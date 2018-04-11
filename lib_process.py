# -*- coding: utf-8 -*- 
import string, re, gzip
import pickle
import nltk, numpy
from nltk.stem.snowball import SnowballStemmer
from nltk.corpus import stopwords

import lucene
from org.apache.lucene.index import Term
from org.apache.lucene.search import TermQuery
    
    
def findOneDBEntry(conn,condition_field,value,result_field):
    item=conn.find_one({condition_field:value})
    if item is None:
       return None
    return item[result_field]
    
def findAllDBEntry(conn,condition_field,value):
    list_doc=conn.find({condition_field:value})
    if list_doc is None:
       return None
    return list_doc  
    
def save_zipped_pickle(obj, filename, protocol=-1):
    with gzip.open(filename, 'wb') as f:
         pickle.dump(obj, f, protocol)
         
def load_zipped_pickle(filename):
    with gzip.open(filename, 'rb') as f:
         loaded_object = pickle.load(f)
         return loaded_object
         
def save_obj(obj,filename):
    with open(filename,'wb') as f:
         pickle.dump(obj,f,pickle.HIGHEST_PROTOCOL)

def load_obj(filename):
    with open(filename, 'rb') as f:
         return pickle.load(f)

def remove_stopwords(line,SEPERATE_CHAR=' '):
    line=line.strip()
    if len(line)==0:
       return ''
    list=line.split(SEPERATE_CHAR)
    res_list=[]
    whitelist=set(['win','won','most','biggest','largest','fastest'])
    blacklist=set(['give','also',' ','and','of','in','list'])
    stop = set(stopwords.words('english'))
    
    filter_list=(stop|blacklist)-whitelist
    res_list=[word for word in list if word not in filter_list]
    return SEPERATE_CHAR.join(res_list)


def cleanSentence(line,isLower=True,SEPERATE_CHAR=' '):
    if len(line)==0:
       return ''
    
    tabin=[ord(ch) for ch in string.punctuation]
    tabout=[' ' for i in range(len(tabin))]
    trantab=dict(zip(tabin,tabout))
    
    for ch in "–—。，、）（·！】【`":
        trantab[ord(ch)]=' '
    
    line = line.translate(trantab)
    if isLower==True:
       line=line.lower()
    line=SEPERATE_CHAR.join(line.split())
    return line

def stemSentence(line,stemmer=SnowballStemmer('english'),isCleanNeeded=True):
    if isCleanNeeded==True:
       line=cleanSentence(line,True)
    if stemmer is None:
       stemmer=SnowballStemmer('english')
    list=line.split(' ')
    stemlist=[stemmer.stem(word) for word in list]
    res=' '.join(stemlist)
    return res
    
def cleanSentence2(line,isLower=True,SEPERATE_CHAR=' '):
    if len(line)==0:
       return ''

    replace_punctuation = str.maketrans(string.punctuation, ' '*len(string.punctuation))
    line = line.translate(replace_punctuation)
    if isLower==True:
       line=line.lower()
    line=SEPERATE_CHAR.join(line.split())
    return line

def cleanRelation(line):
    # http:
    l=re.findall('[a-zA-Z][^A-Z]*',line)
    return ' '.join(l)
    
def cleanValue(line):
    # value or http:
    if line.find('http')!=-1:
       pos_head = line.find("resource/")+9
       return line[pos_head:]
    else:
       return line
    
def cleanDBpediaValue(line):
    # relation%%%%value$$$$relation%%%%value
    if len(line)==0:
       return ''
    l=line.split('$$$$')
    res=''
    for item in l:
        pair=item.split('%%%%') # relation value
        relation=pair[0]
        value=pair[1]
        res=res+'%s %s '%(cleanRelation(relation),cleanValue(value))
    return cleanSentence(res,True)



#def remove_duplicate(line):
    #l=list(set(line.split(' ')))
    #return ' '.join(l)
def remove_duplicate(line,SEPERATE_CHAR=' '):
    ltmp=line.split(SEPERATE_CHAR)
    l=list(set(ltmp))
    l.sort(key=ltmp.index)
    res=' '.join(l)
    return res

def convStr2Vec(str,SEPERATE_CHAR='|'):
    x=numpy.array(str.split(SEPERATE_CHAR))
    return x.astype(numpy.float)

def getEntitySim(dict_en_v1,dict_en_v2,dict_rel1,dict_rel2,en1,en2,NEGATIVE_RESULT):
    if (en1 not in dict_en_v1.has_key(en1)) or (en2 not in dict_en_v2):
       return NEGATIVE_RESULT
    ev1=dict_en_v1[en1]
    ev2=dict_en_v2[en2]
    maxSim=-1.0
    
    maxSim=numpy.dot(ev1,ev2)/(numpy.linalg.norm(ev1)*numpy.linalg.norm(ev2))
    '''
    for rel in dict_rel1:
        ev1_new=ev1+dict_rel1[rel]
        temp_sim=numpy.dot(ev1_new,ev2)/(numpy.linalg.norm(ev1_new)*numpy.linalg.norm(ev2))
        if temp_sim>maxSim:
           maxSim=temp_sim

    for rel in dict_rel2:
        ev2_new=ev2+dict_rel2[rel]
        temp_sim=numpy.dot(ev1,ev2_new)/(numpy.linalg.norm(ev1)*numpy.linalg.norm(ev2_new))
        if temp_sim>maxSim:
           maxSim=temp_sim
    '''
    return (1+maxSim)/2.0
    
def categorySim(en_obj1,en_obj2,w2vmodel):
    maxSim=0.0
    if len(en_obj1.list_category_term)==0 or len(en_obj2.list_category_term)==0:
       return 0.0
    for term_list1 in en_obj1.list_category_term:
        len_term_list1=float(len(term_list1))
        for term_list2 in en_obj2.list_category_term:
            temp_sim=0.0
            for term1 in term_list1:
                for term2 in term_list2:
                    temp_sim+=w2vmodel.similarity(term1,term2)
            temp_sim/=len_term_list1*float(len(term_list2))
            if temp_sim>maxSim:
               maxSim=temp_sim
    return maxSim

def readDictionary(path,d,dimension=300):
    src=open(path,'r')
    
    for line in src.readlines():
        l=line.split(" ")
        if len(l)<dimension:
           continue
        word=l[0]
        str=" ".join(l[1:]).strip()
        vector=convStr2Vec(str,' ')
        d[word]=vector
        
    src.close()
    
    
def fillBooleanArray(i,n,isTermUsed):
    for offset in range(n):
        isTermUsed[i+offset]=True
        
def findNgram(qts,n,model):
    if qts is None:
       #print 'qts is none'
       return []
    #print 'qts='+str(qts)
    if len(qts)<n:
       return qts
    isTermUsed=[False for i in range(len(qts))]
    queryTerms=[]
    seperateList=['_','']
    
    singularList=[]
    pluralList=[]
    for i in range(len(qts)):
        singularList.append(singularize(qts[i]))
        pluralList.append(pluralize(qts[i]))
        
    for i in range(len(qts)-n+1):
        if isTermUsed[i]==True:
           continue
           
        for sepChar in seperateList:
            line=sepChar.join(qts[i:i+n-1])
            lastWord=qts[i+n-1]
            choices=[lastWord,lastWord[:-1],singularList[i+n-1]]
            for j in range(len(choices)):
                tempLine=line+sepChar+choices[j]
                if tempLine in model.vocab:
                   queryTerms.append(tempLine)
                   fillBooleanArray(i,n,isTermUsed)
                   break
            if isTermUsed[i]==True:
               break
        if isTermUsed[i]==True:
           continue        

        for sepChar in seperateList:
            line=sepChar.join(qts[i:i+n-1])
            tempLine=line+sepChar+pluralList[i+n-1]
            if tempLine in model.vocab:
               queryTerms.append(tempLine)
               fillBooleanArray(i,n,isTermUsed)
               break
        if isTermUsed[i]==True:
           continue 
        
        # remaining unigram           
        queryTerms.append(qts[i])
    # remaining unused unigram      
    queryTerms+=qts[len(qts)-n+1:]
    #for i in range(len(qts)-n+1,len(qts)):
        #queryTerms.append(qts[i])
    return queryTerms   