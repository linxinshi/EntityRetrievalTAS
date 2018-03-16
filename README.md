# Entity Retrieval via Type Taxonomy Aware Smoothing
(in progress)

This repository contains resources developed within the following paper:

Xinshi Lin and Wai Lam. “Entity Retrieval via Type Taxonomy Aware Smoothing”, ECIR 2018

## usage
1. build index (see folder "build_index")

2. build graph representation of the Wikipedia Category System (see folder "wikipedia_category_system")

3. edit config.py and config_object.py to specify parameters for retrieval models and index path etc.

4. execute command "python main.py"

5. check results in folder Retrieval_results (created by program and name it after the time executed)

## requirement
Python 3.4+

NLTK, Gensim

NetworkX <= 1.11

PyLucene 6.x 

(if you have PyLucene install issues on Windows, please refer to http://lxsay.com/archives/365)

## comments
1. The TAS approach is implemented in a backtracking way to speed up the retrieval. (see function get_sas_prob() and mlmSas() in lib_metric.py) 

2. From our own experience, the TAS approach is more effective in helping retrieval models scroing against the single catchall field. Replacing the normalized weights (1-alpha)/(1-alpha^{k}) by a small weight between 0 and 1 may obtain more consistently stable performance on non-keyword based queries.

3. Currently we are trying some varities that have better performance. 

## contact
Xinshi Lin (xslin@se.cuhk.edu.hk)

## license
MIT License
