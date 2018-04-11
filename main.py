# -*- coding: utf-8 -*-

from multiprocessing import Process,Manager
import os, sys, argparse, time, datetime, gzip
import math, numpy, networkx
#from franges import drange

from query_object import Query_Object
from entity_object import Entity_Object
from mongo_object import Mongo_Object
from structure_object import Structure_Object
from lucene_object import Lucene_Object
from list_term_object import List_Term_Object
from lib_process import *
from lib_metric import *
from config import *
from config_object import *

import lucene
from java.io import File
from java.nio.file import Paths
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.document import Document
from org.apache.lucene.index import IndexWriter, IndexWriterConfig, DirectoryReader, Term
from org.apache.lucene.store import MMapDirectory
from org.apache.lucene.queryparser.classic import QueryParserBase, ParseException, QueryParser, MultiFieldQueryParser
from org.apache.lucene.search import IndexSearcher, Query, ScoreDoc, TopScoreDocCollector, TermQuery, TermRangeQuery
from org.apache.lucene.search.similarities import BM25Similarity

from queue import Queue
import heapq

def add2Report(title,line,structure):
    entityReport=structure.entityReport
    if title in entityReport:
       entityReport[title].append(line+'\n')
    else:
       entityReport[title]=[line+'\n']
       
def read_query(queries,conf_paras):
    src = open(conf_paras.QUERY_FILEPATH,'r')
    for line in src.readlines():
        list = line.strip().split('\t')
        #queries.append((list[0],list[1],list[2],list[3])) # raw_ID,querystr(for w2v mark ngram),raw merge query, original query
        queries.append((list[0],list[1],list[2])) # query_id, clusterd query, raw query

def computeScore(queryObj,entityObj,structure,lucene_handler,conf_paras):
    mongoObj,w2vmodel,entityScore=structure.mongoObj,structure.w2vmodel,structure.entityScore
    lucene_obj=lucene_handler['first_pass']
    title=entityObj.title
    if title in entityScore:
       return entityScore[title]
  
    add2Report(title,'compare document '+title,structure)
    add2Report(title,'queryID='+queryObj.queryID,structure)
    
    # compute text_sim    
    text_sim=0.0
    if IS_SAS_USED==True and entityObj.categories is not None:
       # need to check if there is at least one category in the collection
       if MODEL_NAME=='lm':
          text_sim=lm_sas(queryObj,entityObj,structure,lucene_handler,mongoObj,USED_CONTENT_FIELD)
          if text_sim==0.0 or text_sim==NEGATIVE_INFINITY:
             text_sim=lmSim(queryObj.contents_obj,entityObj,USED_CONTENT_FIELD,w2vmodel,'log_sum',lucene_obj)
       elif MODEL_NAME in ['mlm','mlm-tc']:
          text_sim=mlm_sas(queryObj,entityObj,structure,lucene_handler)
          if text_sim==0.0 or text_sim==NEGATIVE_INFINITY:
             text_sim=mlmSim(queryObj.contents_obj,entityObj,lucene_obj)
       if text_sim==0.0 or text_sim==NEGATIVE_INFINITY:  
          print ('BAD_ENTITY\t%s\t%s'%(entityObj.title,str(entityObj.categories)))    
          text_sim=NEGATIVE_INFINITY
    else:
       if MODEL_NAME=='lm': 
          text_sim=lmSim(queryObj.contents_obj,entityObj,USED_CONTENT_FIELD,w2vmodel,'log_sum',lucene_obj) 
       elif MODEL_NAME in ['mlm','mlm-tc']:
            text_sim=mlmSim(queryObj.contents_obj,entityObj,lucene_obj)
       elif MODEL_NAME=='sdm':
            text_sim=sdmSim(queryObj,entityObj,USED_CONTENT_FIELD,lucene_obj)
       elif MODEL_NAME=='fsdm':
            text_sim=fsdmSim(queryObj,entityObj,lucene_obj)
    
    # end computing text_sim
    score=text_sim

    add2Report(title,'final score=%f'%(score),structure)
    add2Report(title,'-----------------------------------------------\n',structure)
    return score
    

def createGraph(queryObj,lucene_handler,structure,conf_paras):
    lucene_obj=lucene_handler['first_pass']
    mongoObj,w2vmodel=structure.mongoObj,structure.w2vmodel
    entityScore,entityObjects=structure.entityScore,structure.entityObjects
    
    candidates=[]
    cnt=0
    for entity in structure.currentEntity:
        entityScore[entity] = computeScore(queryObj,entityObjects[entity],structure,lucene_handler,conf_paras)
        candidates.append((entityScore[entity],cnt,entity))
        cnt+=1
    return candidates

def createEntityObject(d_pair,structure,lucene_obj):
    #d_pair:(document,docid)
    d=d_pair[0]
    title=d.get('title')

    entityObjects=structure.entityObjects
    if title not in entityObjects:
       entityObj=Entity_Object()
       entityObj.updateFromIndex(d_pair,structure.mongoObj,structure.w2vmodel,lucene_obj)
       entityObjects[title]=entityObj
    structure.currentEntity.add(title)
    return entityObjects[title]
             
def handle_process(id_process,queries,RES_STORE_PATH,conf_paras):
    starttime=datetime.datetime.now()
    
    structure=Structure_Object(conf_paras,id_process)
    lucene_handler={}
    lucene_handler['first_pass']=Lucene_Object(conf_paras.LUCENE_INDEX_DIR,'BM25',False)
    lucene_handler['category_corpus']=Lucene_Object(conf_paras.LUCENE_INDEX_CATEGORY_CORPUS,'BM25',True)
    
    # prepare report_category_%d
    RESULT_FILENAME=os.path.join(RES_STORE_PATH,'pylucene_%d.runs'%(id_process))
    REPORT_FILENAME=os.path.join(RES_STORE_PATH,'report_lucene_%d.txt'%(id_process))
    rec_result=open(RESULT_FILENAME,'w',encoding='utf-8')
    rec_report=open(REPORT_FILENAME,'w',encoding='utf-8')
    
    # search
    candidates=[]    
    
    for i in range(len(queries)):
        lucene_obj=lucene_handler['first_pass']
        # build query object for computeScore
        queryObj=Query_Object(queries[i],structure,lucene_handler,False)
        querystr=queryObj.querystr   # no stemming may encourter zero candidates if field contents has stemming
        docs=lucene_obj.retrieve(querystr,USED_CONTENT_FIELD,hitsPerPage,None)
        
        # initialize duplicate remover and score record
        structure.clear()
        del candidates[:]
        
        # find candidate results after 1st round filter
        # d_pair:(document,docid)
        for d_pair in docs:
            d=d_pair[0]
            if d is None:
               continue
            uri,title=d['uri'],d['title']
            if title in structure.currentEntity:
               continue    
            obj=createEntityObject(d_pair,structure,lucene_obj)  
        
        candidates=createGraph(queryObj,lucene_handler,structure,conf_paras)
        print ('id_process=%d\t %d/%d\t query=%s  len_docs=%d'%(id_process,i+1,len(queries),queryObj.querystr,len(docs)))
        
        # output and clean entityReport for each query
        rec_report.write('processing query '+str(i)+':'+queryObj.queryID+'\n')
        for key in structure.entityReport:
            rec_report.writelines(structure.entityReport[key])
        rec_report.write('=========================================================\n')
            
        # output results from priority queue larger score first
        candidates.sort(key=lambda pair:pair[0],reverse=True)
        print ('id_process=%d      candidate number=%d' %(id_process,len(candidates)))
        
        for rank in range(min(1000,len(candidates))):
            item=candidates[rank]
            title='<dbpedia:%s>' %(item[2])
            res_line="%s\t%s\t%s\t%d\t%f\t%s\n" %(queryObj.queryID,'Q0',title,rank+1,item[0],'mazda6')
            rec_result.writelines(res_line)
    
    interval=(datetime.datetime.now() - starttime).seconds
    print ('id_process=%d   running time=%s' %(id_process,str(interval)))
    
    rec_report.write('hitsPerPage=%d'%(hitsPerPage))
    rec_report.write('running time=%s seconds\n'% (str(interval)) )
    rec_report.close()
    rec_result.close()
       
def main(conf_paras):
    system_flag=conf_paras.system_flag
    
    starttime_total=datetime.datetime.now()
    parser = argparse.ArgumentParser()
    parser.add_argument("-comment", help="comment for configuration", default='')
    args = parser.parse_args()
    
    # generate folder to store results
    if (len(args.comment.strip()))>0:
       comment='-'.join(args.comment.split(' '))
       RES_STORE_PATH=os.path.join(str(datetime.datetime.now()).replace(':','-').replace(' ','-')[:-7]+'-'+comment)
    else:
       RES_STORE_PATH=str(datetime.datetime.now()).replace(':','-').replace(' ','-')[:-7]   
    
    RES_STORE_PATH=os.path.join('Retrieval_result',RES_STORE_PATH)

    print ('store_path=%s'%(RES_STORE_PATH))
    os.makedirs(RES_STORE_PATH)
  
    print ('begin backup code files')
    if system_flag=='Windows':
       cmd='robocopy %s %s\\code_files *.py'%(r'%cd%',RES_STORE_PATH)
    else:
       cmd='cp -f py3/*.py %s/code_files'%(RES_STORE_PATH)
    os.system(cmd)
    # read queries
    queries=[]
    read_query(queries,conf_paras)
    cnt_query=len(queries)
   
   # begin multiprocessing
    process_list=[]
    num_workers=NUM_PROCESS
    delta=cnt_query//num_workers  
    if cnt_query%num_workers!=0:  # +1 important
       delta=delta+1
    
    for i in range(num_workers):
        left=i*delta
        right=(i+1)*delta
        if right>cnt_query:
           right=cnt_query
         
        p = Process(target=handle_process, args=(i,queries[left:right],RES_STORE_PATH,conf_paras))
        p.daemon = True
        process_list.append(p)

    if IS_SAS_USED==True:
       delay=40
    else:
       delay=3
    for i in range(len(process_list)):
        process_list[i].start()
        print ("sleep %d seconds to enable next process"%(delay))
        time.sleep(delay)

    for i in range(len(process_list)):
        process_list[i].join()
    
    print ('begin to merge results')
    dict_merged={}
    list_allResult={}
    list_name=['pylucene','report_lucene']
       
    list_ext=['runs','txt']
    for name in list_name:
        list_allResult[name]=[]
    
    for i in range(num_workers):
        for j in range(len(list_name)):
            name=list_name[j]
            filename=os.path.join(RES_STORE_PATH,name)+'_%s.%s'%(str(i),list_ext[j])
            with open(filename,'r',encoding='utf-8') as f_tmp:
                 list_allResult[name].extend(f_tmp.readlines())
            os.remove(filename)    

    list_allResult['pylucene'].sort(key=lambda item:item.split('\t')[0],reverse=False)
    for j in range(len(list_name)):
        name=list_name[j]
        filename=os.path.join(RES_STORE_PATH,name)+'_all_mp.'+list_ext[j]
        if name!='report_lucene':
           with open(filename,'w',encoding='utf-8') as f:
                f.writelines(list_allResult[name])
        else:
           with gzip.open(filename+'.gz','wb') as f:
                f.writelines([line.encode('utf-8') for line in list_allResult[name]])           
             
    res_mp_filepath=os.path.join(RES_STORE_PATH,'pylucene_all_mp.runs')
    PATH_GROUNDTRUTH=conf_paras.PATH_GROUNDTRUTH
    cmp_mp_filepath=os.path.join(RES_STORE_PATH,'result_mp.txt')
    cmd='trec_eval -q -m num_q -m num_ret -m num_rel -m num_rel_ret -m P.5,10,15,20,30,100 -m map_cut.100 -m ndcg_cut.10 %s %s > %s'%(PATH_GROUNDTRUTH,res_mp_filepath,cmp_mp_filepath)
    os.system(cmd)
        
    print ('total running time='+str((datetime.datetime.now() - starttime_total).seconds))
    
if __name__ == '__main__':
   conf_paras=Config_Object()
   main(conf_paras)
