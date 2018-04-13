# Entity Retrieval via Type Taxonomy Aware Smoothing

This repository contains resources developed within the following paper:

    Xinshi Lin and Wai Lam. “Entity Retrieval via Type Taxonomy Aware Smoothing”, ECIR 2018

## usage
0. collect data from DBpedia and store them into a MongoDB database (see https://github.com/linxinshi/DBpedia-Wikipedia-Toolkit)

1. build graph representation of the Wikipedia Category System (see folder "wikipedia_category_system")

2. build index (see folder "build_index")

3. edit config.py, config_object.py  and mongo_object.py to specify parameters for retrieval models and index path etc.

4. execute command "python main.py"

5. check results in folder Retrieval_results (created by program and name it after the time executed)

*this implementation supports multi-processing, specify NUM_PROCESS in config.py

## requirements
Python 3.4+

NLTK, Gensim

NetworkX <= 1.11

PyLucene 6.x 

(if you have PyLucene install issues on Windows, please refer to http://lxsay.com/archives/365)

## comments
1. The TAS approach is implemented in a recursive and backtracking way to speed up. (see function lm_sas() and mlmSas() in lib_metric.py) 

2. From our own experience, the TAS approach is more effective in helping retrieval models scroing against the single catchall field. Replacing the normalizing weights (1-alpha)/(1-alpha^{k}) by a small weight between 0 and 1 (e.g. 1/300) may obtain more consistently stable performance on verbose queries such as natural language questions.

3. The quality of index will greatly affect the performance. After this the parameter alpha and the normalizing weight may affect the performance a bit (-/+ 10%). 

4. If you want to improve its practical performance or reproduce the exact results brought by TAS reported in the paper, the following small tricks might be helpful: 

    1. only TAS for entites that has positive term frequencies given a query term. 
    
    2. for entites that have no categories, use the original version of the model (i.e. no TAS) to score them. (already implemented)
    
    Results reported in the paper relies little on these tricks.

5. Currently we are trying some varities that have better performance. 

6. This framework works well with other type taxonomies (DBpedia ontology, YAGO etc.) too, it is not a "dataset specific" method.

## relevant projects
FSDM:  https://github.com/teanalab/FieldedSDM

PFSDM:  https://github.com/teanalab/pfsdm

FSDM+ELR:  https://github.com/hasibi/EntityLinkingRetrieval-ELR

DBpedia-Entity Test Collection:  https://iai-group.github.io/DBpedia-Entity/

## contact
Xinshi Lin (xslin@se.cuhk.edu.hk)

## license
Creative Commons
