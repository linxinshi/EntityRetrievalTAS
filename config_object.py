# -*- coding: utf-8 -*-
from config import *
import os

class Config_Object(object):

      system_flag=None    
      mongo_port=58903
      
      def __init__(self):
          self.system_flag=SYSTEM_FLAG
          self.LUCENE_INDEX_DIR=os.path.join('mmapDirectory','dbpedia_v3_FSDM3')
          self.LUCENE_INDEX_WIKI_DIR=os.path.join('mmapDirectory','index_wikipedia_2015')
          self.LUCENE_INDEX_CATEGORY_CORPUS=os.path.join('mmapDirectory','category_corpus_dbpedia201510_top5_fsdm3')

          self.QUERY_FILEPATH=os.path.join('query','simple_cluster','INEX_LD_v2.txt')
          self.PATH_GROUNDTRUTH=os.path.join('qrels-v2.txt')
          self.PATH_CATEGORY_DAG='category_dag_dbpedia_top10.pkl.gz'
          
          if self.system_flag=='Windows':
             self.LUCENE_INDEX_DIR=os.path.join('E:\\',self.LUCENE_INDEX_DIR)
             self.LUCENE_INDEX_WIKI_DIR=os.path.join('E:\\',self.LUCENE_INDEX_WIKI_DIR)
             self.LUCENE_INDEX_CATEGORY_CORPUS=os.path.join('E:\\',self.LUCENE_INDEX_CATEGORY_CORPUS)
             self.QUERY_FILEPATH=os.path.join('E:\\','Entity_Retrieval',self.QUERY_FILEPATH)
             self.PATH_GROUNDTRUTH=os.path.join('E:\\','Entity_Retrieval','Balog_SIGIR13',self.PATH_GROUNDTRUTH)
             self.PATH_CATEGORY_DAG='F:\\研究数据\\Wikipedia_DBpedia_data\\DBpedia_data\\2015-10\\category_structure_processing\\category_dag_dbpedia_top10.pkl.gz'
             self.mongo_port=27017
