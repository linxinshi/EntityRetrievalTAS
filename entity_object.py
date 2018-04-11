import sys 
from nltk.stem.snowball import SnowballStemmer
from lib_process import *
from list_term_object import List_Term_Object
from config import *

from document_object import Document_Object
from nltk.util import ngrams

class Entity_Object(Document_Object):
      categories=None
      dict_obj=None
      term_freq=None
      term_freqs=None
      lengths=None
      
      def __init__(self):
          self.dict_obj={}
          self.dict_attr={}
          
      def updateFromIndex(self,d_pair,mongoObj,w2vmodel,lucene_obj):
          # d_pair:(document,docid) entity: dict   
          entity,docid=d_pair[0],d_pair[1]
          for idf in entity.iterator():
              self.setAttr(idf.name(),idf.stringValue())
              #print ('%s\t%s'%(idf.name(),idf.stringValue()))
          self.setAttr('name',self.label)    
          
          if IS_SAS_USED==True:
             self.update_categories(mongoObj)
          self.update_term_freq(docid,USED_CONTENT_FIELD,lucene_obj)
          self.length=sum(self.term_freq.values())
          self.update_term_freqs(docid,lucene_obj)

      
      def update_term_freq(self,docid,field,lucene_obj):
          self.term_freq=lucene_obj.get_term_freq(docid,field,False)
          
      def update_term_freqs(self,docid,lucene_obj):
          self.term_freqs={}
          self.lengths={}
          for f in LIST_F:
              try:
                self.term_freqs[f]=lucene_obj.get_term_freq(docid,f,False)
                self.lengths[f]=sum(self.term_freqs[f].values())
              except:
                self.term_freqs[f]={}
                self.lengths[f]=0
          if LIST_F[0].find('stemmed')>-1:
             self.term_freqs['stemmed_catchall']=lucene_obj.get_term_freq(docid,'stemmed_catchall',False)
             self.lengths['stemmed_catchall']=sum(self.term_freqs['stemmed_catchall'].values()) 
          else:
             self.term_freqs['catchall']=lucene_obj.get_term_freq(docid,'catchall',False)
             self.lengths['catchall']=sum(self.term_freqs['catchall'].values())              
          
      def update_categories(self,mongoObj):
          if mongoObj.conn_acs==None:
             return
          item=mongoObj.conn_acs.find_one({'uri':self.uri})
          if item is None:
             self.categories=[]
             return
          self.categories=item['categories'].strip().split('|')

