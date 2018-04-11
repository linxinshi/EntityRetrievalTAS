# coding=utf-8
import math, networkx, gensim, pymongo
from mongo_object import Mongo_Object
from lib_process import load_zipped_pickle, stemSentence
from config import *


class Structure_Object(object):
      entityScore=None
      entity2ID=None
      ID2entity=None
      entityObjects=None
      entityReport=None
      currentEntity=None
      idx_entity=None

      w2vmodel=None
      mongoObj=None
      cat_dag=None
      # LCA(x, y) = val[RMQ(depth, first[x], first[y])]
      
      def __init__(self,conf_paras,id_process=0):
          self.entityScore={}
          self.entity2ID={}
          self.ID2entity={}
          self.entityObjects={}
          self.entityReport={}
          self.idx_entity=0
          self.currentEntity=set()

          # initialize mongodb client
          self.mongoObj=Mongo_Object('localhost',conf_paras.mongo_port)
          
          # initialize category graph
          if IS_SAS_USED==True:
             print ('id=%d  load category structure'%(id_process))
             if SAS_MODE=='TOPDOWN':
                self.cat_dag=load_zipped_pickle(conf_paras.PATH_CATEGORY_DAG).reverse()
             else:
                self.cat_dag=load_zipped_pickle(conf_paras.PATH_CATEGORY_DAG)
             print ('id=%d  finish loading category structure'%(id_process))
          self.paths={}
          
      def clear(self):
          #self.entityObjects.clear()
          self.entityScore.clear()
          self.entityReport.clear()
          self.entity2ID.clear()
          self.ID2entity.clear()
          self.idx_entity=0
          self.currentEntity.clear()
          self.paths.clear()
                
      def getEntityID(self,entity):
          result=-1
          # entity: title, result: index of entity 
          
          if entity in self.entity2ID:
             result=self.entity2ID[entity]
          else:
             result=self.idx_entity
             self.entity2ID[entity]=result
             self.ID2entity[result]=entity
             self.idx_entity+=1
          return result
      
