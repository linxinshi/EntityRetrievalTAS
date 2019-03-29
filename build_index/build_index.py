import os, sys, argparse, string, re, pymongo, platform
from nltk.stem.snowball import SnowballStemmer
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords

import lucene
from java.io import File
from java.nio.file import Paths
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.analysis.core import SimpleAnalyzer
from org.apache.lucene.document import Document, Field, StringField, TextField, StoredField
from org.apache.lucene.index import IndexWriter, IndexWriterConfig, DirectoryReader, Term
from org.apache.lucene.store import MMapDirectory
from org.apache.lucene.util import Version
from org.apache.lucene.queryparser.classic import ParseException, QueryParser
from org.apache.lucene.search import IndexSearcher, Query, ScoreDoc, TopScoreDocCollector
from org.apache.lucene.search.similarities import BM25Similarity
from org.apache.lucene.search import PhraseQuery, BooleanQuery, TermQuery, BooleanClause

from lucene_field import *
from org.apache.lucene.document import FieldType

# has java VM for Lucene been initialized
lucene_vm_init = False

# global data structure
queries = []

# global parameter
LUCENE_INDEX_DIR='mmapDirectory/dbpedia_v2_FSDM3'

def cleanSentence(line,isLower=True,SEPERATE_CHAR=' '):
    if len(line)==0:
       return ''

    replace_punctuation = str.maketrans(string.punctuation, ' '*len(string.punctuation))
    line = line.translate(replace_punctuation)
    if isLower==True:
       line=line.lower()
    line=SEPERATE_CHAR.join(line.split())
    return line

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
    

def stemSentence(line,stemmer=SnowballStemmer('english'),isCleanNeeded=True):
    if isCleanNeeded==True:
       line=cleanSentence(line,True)
    if stemmer is None:
       stemmer=SnowballStemmer('english')
    list=line.split(' ')
    stemlist=[stemmer.stem(word) for word in list]
    res=' '.join(stemlist)
    return res    
    
def cleanRelation(line):
    # http:
    pos1=line.rfind('/')
    pos2=line.rfind('#')
    
    if pos2>pos1:
       pos=pos2
    else:
       pos=pos1
    
    if pos!=-1:
       line=line[pos+1:-1]
    l=re.findall('[a-zA-Z][^A-Z]*',line)
    return ' '.join(l)
    
def cleanValue(line):
    # value or http:
    if line.find('http')!=-1:
       pos_head = line.find("resource/")+9
       return line[pos_head:]
    else:
       return line
       
def findTitle(line):
    pos=line.find('resource/')
    assert pos!=-1
    return line[pos+9:-1]
     
def findOneEntry(conn,condition_field,value,result_field):
    item=conn.find_one({condition_field:value})
    if item is None:
       return None
    return item[result_field]
    
def findAllEntry(conn,condition_field,value):
    iter_list_doc=conn.find({condition_field:value})
    if iter_list_doc is None:
       return None
    return list(iter_list_doc)  
    
def makeIndex(w):
   # initialize mongodb
    client = pymongo.MongoClient('localhost',27017)
    db = client.wiki2015
    conn_label = db['label']
    conn_abstract = db['long_abstracts']
    conn_id = db['page_id']
    conn_dbpedia_literal=db['mapping_based_properties_literal']
    conn_dbpedia_object=db['mapping_based_properties_object']
    conn_disam=db['disambiguations']
    conn_redirect=db['redirects']
    conn_category=db['article_categories']

    # begin construction
    cnt_debug=0
    data={}
    addedEntity=set()
    
    # names field: entity label, properties in namelist
    namelist=['<http://xmlns.com/foaf/0.1/name>','<http://dbpedia.org/ontology/title>','<http://dbpedia.org/ontology/name>']
    
    for doc in conn_abstract.find({},no_cursor_timeout=True):
        #cnt_debug+=1
        #if cnt_debug>10:
           #break
           
        uri=doc['uri'] 
        abstract=doc['abstract'].strip()
        title=findTitle(uri)
        
        if len(abstract)==0:
           continue
        if uri in addedEntity:
           continue    
        
        # get label and page_id
        label=findOneEntry(conn_label,'uri',uri,'label')
        wiki_id=findOneEntry(conn_id,'uri',uri,'wiki_id')

        if label is None:
           continue
        if len(label.strip())==0:
           continue
        if wiki_id is None:
           continue
        label=label.strip().lower()

        list_literal=findAllEntry(conn_dbpedia_literal,'uri',uri)
        list_object=findAllEntry(conn_dbpedia_object,'uri',uri)

        
        #list_value_literal=[cleanRelation(doc['property']).lower()+' '+cleanSentence(doc['value'],True,' ') for doc in list_literal]
        list_value_object=[cleanRelation(doc['property']).lower()+' '+cleanSentence(findOneEntry(conn_label,'uri',doc['value'],'label'),True,' ') for doc in list_object if findOneEntry(conn_label,'uri',doc['value'],'label') is not None]      
        #str_literal=' '.join(list_value_literal).strip()
        str_object=' '.join(list_value_object).strip()
        
        item_disam=findAllEntry(conn_disam,'uri',uri)
        list_disam=item_disam if item_disam is not None else []
        value_disam=' '.join([findTitle(doc['disambiguated_uri']) for doc in list_disam])
        
        item_redirect=findAllEntry(conn_redirect,'uri',uri)
        list_redirect=item_redirect if item_redirect is not None else []
        value_redirect=' '.join([findTitle(doc['redirect_uri']) for doc in list_redirect])
        
        item_category=findOneEntry(conn_category,'uri',uri,'categories')
        list_category=item_category.split('|') if item_category is not None else []
        
        # need to extract name,label etc. from mapping_based_properties_literal
        names=label+' '+' '.join([doc['value'] for doc in list_literal if doc['property'] in namelist])
        str_attributes=' '.join([cleanRelation(doc['property']).lower()+' '+cleanSentence(doc['value'],True,' ') for doc in list_literal if doc['property'] not in namelist])
        attributes=abstract+' '+str_attributes
        categories=' '.join(list_category)
        similar_entities=value_disam+' '+value_redirect
        related_entities=str_object

        
        names=remove_stopwords(cleanSentence(names,True,' '),' ')
        attributes=remove_stopwords(cleanSentence(attributes,True,' '),' ')
        categories=remove_stopwords(cleanSentence(categories,True,' '),' ')
        similar_entities=remove_stopwords(cleanSentence(similar_entities,True,' '),' ')
        related_entities=remove_stopwords(cleanSentence(related_entities,True,' '),' ')
        
        catchall=names+' '+attributes+' '+categories+' '+similar_entities+' '+related_entities
        
        addedEntity.add(uri)
        
        # store field into dictionary
        data.clear()
        data['names']=(names,'CUSTOM_FIELD_TEXT') 
        data['attributes']=(attributes,'CUSTOM_FIELD_TEXT')
        data['categories']=(categories,'CUSTOM_FIELD_TEXT')
        data['similar_entities']=(similar_entities,'CUSTOM_FIELD_TEXT')
        data['related_entities']=(related_entities,'CUSTOM_FIELD_TEXT')
        data['catchall']=(catchall,'CUSTOM_FIELD_TEXT')
        
        for field in ['names','attributes','categories','similar_entities','related_entities','catchall']:
            data['stemmed_'+field]=(stemSentence(data[field][0],None,False),'CUSTOM_FIELD_TEXT')
        
        data['uri']=(uri,'StringField')
        data['title']=(title,'StringField')
        data['wiki_id']=(wiki_id,'StringField')
        data['label']=(label,'CUSTOM_FIELD_TEXT')
        
        addDoc(w,data)
    
    client.close()
    
def addDoc(w,data):
    doc = Document()
    #print ('----------------------------')
    for field in data:
        value,type=data[field][0],data[field][1]
        #print ('field:%s  type:%s'%(field,type))
        #print (value+'\n')
        
        if type=='StringField':
           doc.add(StringField(field,value,Field.Store.YES))
        elif type=='TextField':
           doc.add(TextField(field,value,Field.Store.YES))
        elif type=='CUSTOM_FIELD_TEXT':
           doc.add(Field(field,value,CUSTOM_FIELD_TEXT))
        elif type=='INTEGER_STORED':
           doc.add(StoredField(field,value))
        else:
           print ('UNKNOWN FIELD')
           
    w.addDocument(doc)

def main():
    try:
       lucene.initVM(vmargs=['-Djava.awt.headless=true'])
       lucene_vm_init = True
    except:
       print ('JavaVM already running')
       
       
    is_index_Exist = os.path.exists(LUCENE_INDEX_DIR)
    # specify index path 
    index_mm = MMapDirectory(Paths.get(LUCENE_INDEX_DIR))
    
    # configure search engine
    analyzer = SimpleAnalyzer()
    config = IndexWriterConfig(analyzer)
    config=config.setRAMBufferSizeMB(1024.0)
    # write data to index
    
    if not is_index_Exist:
       print ('begin backup code files')
       system_flag=platform.system()
       cmd='robocopy %s %s\code_files *.py'%(r'%cd%',LUCENE_INDEX_DIR) if system_flag=='Windows' else 'cp -f *.py %s\code_files'%(LUCENE_INDEX_DIR)
       os.system(cmd)
        
       w = IndexWriter(index_mm,config)
       makeIndex(w)
       w.close()
    else:
       print ('index already exists, stop indexing')

if __name__ == '__main__':
   main()
