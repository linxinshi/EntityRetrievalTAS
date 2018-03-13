# -*- coding: utf-8 -*-
import sys, os, platform
import pickle, gzip, string
import networkx, pymongo, nltk
from nltk.stem.snowball import SnowballStemmer
from nltk.corpus import stopwords

import lucene
from java.io import File
from java.nio.file import Paths
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.document import Document, Field, StringField, TextField, StoredField, IntPoint
from org.apache.lucene.index import IndexWriter, IndexWriterConfig, DirectoryReader, Term
from org.apache.lucene.store import MMapDirectory
from org.apache.lucene.util import Version
from org.apache.lucene.queryparser.classic import ParseException, QueryParser
from org.apache.lucene.search import IndexSearcher, Query, ScoreDoc, TopScoreDocCollector
from org.apache.lucene.search.similarities import BM25Similarity
from org.apache.lucene.search import PhraseQuery, BooleanQuery, TermQuery, BooleanClause

# for customized field
from org.apache.lucene.document import Field
from org.apache.lucene.document import FieldType
from lucene_field import *
from lucene_object import Lucene_Object

def findTitle(line):
    pos=line.find('resource/')
    assert pos!=-1
    return line[pos+9:-1]

def stemSentence(line,stemmer,isCleanNeeded=True):
    if isCleanNeeded==True:
       line=cleanSentence(line,True)
    if stemmer is None:
       stemmer=SnowballStemmer('english')
    list=line.split(' ')
    stemlist=[stemmer.stem(word) for word in list]
    res=' '.join(stemlist)
    return res
    
def cleanSentence(line,isLower=True,SEPERATE_CHAR=' '):
    if len(line)==0:
       return ''
    
    tabin=[ord(ch) for ch in string.punctuation]
    tabout=[' ' for i in range(len(tabin))]
    trantab=dict(zip(tabin,tabout))
    
    for ch in "–—。，、）（·！】【`￥&：？》《":
        trantab[ord(ch)]=' '
    
    line = line.translate(trantab)
    line=SEPERATE_CHAR.join(line.split())
    if isLower==True:
       line=line.lower()
    return line
    
def load_zipped_pickle(filename):
    with gzip.open(filename, 'rb') as f:
         loaded_object = pickle.load(f)
         return loaded_object

def save_zipped_pickle(obj, filename, protocol=-1):
    with gzip.open(filename, 'wb') as f:
         pickle.dump(obj, f, protocol)

def findOneDBEntry(conn,condition_field,value,result_field):
    item=conn.find_one({condition_field:value})
    if item is None:
       return None
    return item[result_field]

def addDoc(w,data):
    doc = Document()
    for field in data:
        value,type=data[field][0],data[field][1]
        
        '''
        if type!='INTEGER_STORED':
           #print ('field=%s  len=%d'%(field,len(value)))
           print ('field=%s  value=%s'%(field,value))
        else:
           print ('field=%s  value=%d'%(field,value))
        '''
        
        if type=='StringField':
           doc.add(StringField(field,value,Field.Store.YES))
        elif type=='TextField':
           doc.add(TextField(field,value,Field.Store.YES))
        elif type=='CUSTOM_FIELD_TEXT':
           doc.add(Field(field,value,CUSTOM_FIELD_TEXT))
        elif type=='CUSTOM_FIELD_TEXT_NOT_STORED':
           doc.add(Field(field,value,CUSTOM_FIELD_TEXT_NOT_STORED))
        elif type=='INTEGER_STORED':
           doc.add(StoredField(field,value))
        else:
           print ('UNKNOWN FIELD')
           
    try:
       w.addDocument(doc)
    except:
       #print ('error cat=%s'%(data['category'][0]))
       print ('-----------------------------------')
       for field in data:
           value,type=data[field][0],data[field][1]
           print ('field=%s\nvalue=%s'%(field,str(value)))
    
    
    
def main():
    if len(sys.argv)<2:
       print ('error: too few arguments')
       print ('command:  python create_corpus.py NUMBER_TOP_CATEGORY')
       quit()
    
    NUMBER_TOP_CATEGORY=int(sys.argv[1])
    print ('NUMBER_TOP_CATEGORY=%d'%(NUMBER_TOP_CATEGORY))
    
    print ('loading category profiles')
    profile=load_zipped_pickle('category_profiles_dbpedia_201510.gz')
    print ('finish loading category profiles')
    
    system_flag=platform.system()
    cwd=os.getcwd()
    
    # initialize mongo client
    if system_flag=='Windows':
       client = pymongo.MongoClient("localhost",27017)
    else:
       client = pymongo.MongoClient("localhost",58903)
       
    db = client.wiki2015  
    wiki_article_categories=db['article_categories']
    
    category_corpus={}
    
    pkl_filename='category_dbpedia_corpus_top%d_fsdm3.pkl.gz'%(NUMBER_TOP_CATEGORY)
    if system_flag=='Windows':
       lucene_dbpedia_fsdm=Lucene_Object('mmapDirectory\\dbpedia_v2_FSDM3','BM25',True)
    else:
       lucene_dbpedia_fsdm=Lucene_Object('%s/mmapDirectory/dbpedia_v2_FSDM3'%(cwd),'BM25',True)
    
    cnt=0
    if os.path.exists(pkl_filename)==True:
    #if False==True:
       print ('loading category corpus')
       category_corpus=load_zipped_pickle(pkl_filename)
    else:

       for item in wiki_article_categories.find():
           list_category=item['categories'].strip().split('|')
           uri_article=item['uri']
           title=findTitle(uri_article)
           
           entity_content_dict={}
           doc_entity=lucene_dbpedia_fsdm.findEntityDocFromIndex(title,'title',False)
           if doc_entity is None:
              continue
           
           for f in ['names','attributes','categories','similar_entities','related_entities','catchall']:
               entity_content_dict[f]=doc_entity[f]
               entity_content_dict['stemmed_'+f]=doc_entity['stemmed_'+f]

           if len(entity_content_dict['catchall'].strip())==0:
              continue
                
           for cat in list_category[:NUMBER_TOP_CATEGORY]:
               if ('<http://dbpedia.org/resource/Category:'+cat+'>') not in profile:
                  continue
               if cat not in category_corpus:
                  category_corpus[cat]=[]
               if len(category_corpus[cat])<300:
                  category_corpus[cat].append(entity_content_dict)

           #cnt+=1
           #if cnt>20:
              #break
           
       print ('saving corpus to pkl.gz')
       save_zipped_pickle(category_corpus,pkl_filename)    
    client.close()


    
    # begin write the data into index
    print ('begin write into index')
    if system_flag=='Windows':
       LUCENE_INDEX_DIR='mmapDirectory\\category_corpus_dbpedia201510_top'+str(NUMBER_TOP_CATEGORY)+'_fsdm3'
    else:
       LUCENE_INDEX_DIR='%s/mmapDirectory/category_corpus_dbpedia201510_top'%(cwd)+str(NUMBER_TOP_CATEGORY)+'_fsdm3'
    
    # backup code files
    cmd='robocopy %s %s\code_files *.py'%(r'%cd%',LUCENE_INDEX_DIR) if system_flag=='Windows' else 'cp *.py %s/code_files'%(LUCENE_INDEX_DIR)
    os.system(cmd)
    
    # specify index path 
    index_mm = MMapDirectory(Paths.get(LUCENE_INDEX_DIR))
    
    # configure search engine
    analyzer = StandardAnalyzer()
    config = IndexWriterConfig(analyzer)
    
    # write data to index
    w = IndexWriter(index_mm,config)
    
    cnt=0
    data={}
    max_article_num=0
    stemmer=SnowballStemmer('english')
    for cat,list_entity_dict in category_corpus.items():
        cat_label=cleanSentence(cat,True)
        data.clear()
        data['category']=(cat,'StringField')
        data['label']=(cat_label,'CUSTOM_FIELD_TEXT')
        data['stemmed_label']=(stemSentence(cat_label,stemmer,True),'CUSTOM_FIELD_TEXT')
        data['num_articles']=(len(list_entity_dict),'INTEGER_STORED')
        
        if data['num_articles'][0]>max_article_num:
           max_article_num=data['num_articles'][0]
        
        for f in ['names','attributes','categories','similar_entities','related_entities','catchall']:
            contents=cleanSentence(' '.join([dic[f] for dic in list_entity_dict]),True,' ')
            data[f]=(contents,'CUSTOM_FIELD_TEXT_NOT_STORED')
            data['stemmed_'+f]=(stemSentence(contents,stemmer,False),'CUSTOM_FIELD_TEXT_NOT_STORED')
        #print ('--------------------')
        # need to calculate corpus average length
        addDoc(w,data)
        
        #cnt+=1
        #if cnt>20:
           #break
           
    w.close()    
    print ('max article num=%d'%(max_article_num))

    
if __name__ == '__main__':
   main()
