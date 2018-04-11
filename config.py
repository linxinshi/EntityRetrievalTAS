# coding=utf-8
# global parameter
import platform

SYSTEM_FLAG=platform.system()
DATA_VERSION = 2015
hitsPerPage = 1000
NUM_PROCESS= 4

NEGATIVE_INFINITY=-99999999
MODEL_NAME='lm'   # lm,mlm-tc,mlm-all,sdm,fsdm

DEBUG_MODE=False

# for MLM-tc model
MLMtc_FIELD_WEIGHTS={'stemmed_names':0.2,'stemmed_catchall':0.8}

# for FSDM model
LAMBDA_T=0.8
LAMBDA_O=0.1
LAMBDA_U=0.1

# for structure-aware smoothing
IS_SAS_USED=False   
# if it is True, then enable TAS

SAS_MAX_ARTICLE_PER_CAT=100
SAS_MODE='TOPDOWN' 
# SAS_MODE can be TOPDOWN or BOTTOM-UP, it determines the path goes to parental types or descant types in the graph

LIMIT_SAS_PATH_LENGTH=3
# 10,20
TOP_CATEGORY_NUM=10
# 30
TOP_PATH_NUM_PER_CAT=500
ALPHA_SAS=0.75

# for Query_Object
USED_QUERY_VERSION='stemmed_raw_query'  
# raw_query or stemmed_raw_query, 'stemmed' means query terms are filtered by a stemmer

IS_STOPWORD_REMOVED=True
   
if USED_QUERY_VERSION=='raw_query':
   USED_CONTENT_FIELD='catchall'
   LIST_F=['names','attributes','categories','similar_entities','related_entities']
   if MODEL_NAME=='mlm-tc':
      LIST_F=['names','catchall']
   elif MODEL_NAME=='sdm':
      LIST_F=['catchall']
elif USED_QUERY_VERSION=='stemmed_raw_query':
     USED_CONTENT_FIELD='stemmed_catchall' 
     LIST_F=['stemmed_names','stemmed_attributes','stemmed_categories','stemmed_similar_entities','stemmed_related_entities']
     if MODEL_NAME=='mlm-tc':
        LIST_F=['stemmed_names','stemmed_catchall']
     elif MODEL_NAME=='sdm':
        LIST_F=['stemmed_catchall']
else:
     print ('Wrong query version !')
     USED_QUERY_VERSION='raw_query'
     USED_CONTENT_FIELD='catchall'
