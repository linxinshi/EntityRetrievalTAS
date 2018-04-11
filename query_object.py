# coding=utf-8
import sys
import string
from lib_process import cleanSentence, remove_stopwords, convStr2Vec,stemSentence
from list_term_object import List_Term_Object
from config import *
from document_object import Document_Object
from nltk.util import ngrams

class Query_Object(Document_Object):
      contents_obj=None
      subqueries=None
      bigrams=None
      
      def __init__(self,query,structure,lucene_handler,debug_mode=False):
          mongoObj,w2vmodel=structure.mongoObj,structure.w2vmodel
          self.dict_attr={}
          # query: query_id, clusterd query, raw query
          self.setAttr('id',query[0].strip())
          self.setAttr('clustered_query',query[1].strip().lower())
          if IS_STOPWORD_REMOVED:
             qstr=remove_stopwords(cleanSentence(query[2].strip(),True,' '),' ')
          self.setAttr('raw_query',qstr)
             
          self.setAttr('stemmed_raw_query',stemSentence(self.raw_query,None,True))
          self.setAttr('querystr',self.dict_attr[USED_QUERY_VERSION])
          self.setAttr('queryID',self.id)
          
          self.contents_obj=List_Term_Object(self.querystr,True,' ',mongoObj,w2vmodel)
          self.update_bigrams()

      def update_bigrams(self):
          self.bigrams = list(set(ngrams(self.querystr.split(),2)))
          #print (str(self.bigrams))
                        
        