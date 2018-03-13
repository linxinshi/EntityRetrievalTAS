# Entity Retrieval via Type Taxonomy Aware Smoothing
(in progress)

This repository contains resources developed within the following paper:

Xinshi Lin and Wai Lam. “Entity Retrieval via Type Taxonomy Aware Smoothing”, ECIR 2018

# usage
build index (see folder "build_index")

build graph representation of the Wikipedia Category System (see folder "wikipedia_category_system")

edit config.py and config_object.py to specify parameters for retrieval models and index path etc.

execute command "python main.py"


# comments
1. The TAS approach is implemented in a backtracking way that greatly speed up the retrieval. (see function get_sas_prob() and mlmSas() in lib_metric.py) 

2. From our own experimence, the TAS approach is more effective in helping retrieval models scroing against the single catchall field. Replacing the normalized weights (1-alpha)/(1-alpha^{k}) by a small weight between 0 and 1 may obtain more consistently stable performance

3. We believe this method is still "underresearched". Currently we are trying some varities that have more stable performance. Our design has a focus on structuralism. Welcome to join the disscusion.

# contact
Xinshi Lin (xslin@se.cuhk.edu.hk)

# license
MIT License
