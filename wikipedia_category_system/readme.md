## Introduction

Input: DBpedia Skos Categories dataset (skos_categories_en.ttl)

Intermedia Output: A collection of profile that records category name, parent categories, related categories for each category

Final Output: A directed acyclic graph representation of the Wikipedia Category System

## Requirement

Python 2.7.x or Python 3.4+

NetworkX <= 1.11 (current networkx 2.0 is very slow in finding strongly connected components, probably due to incomplete development)

## Usage

(put source code files and skos_categories_en.ttl into the same folder)

STEP 1: python create_skos_categories_profile.py

STEP 2: python create_category_structure.py NUMBER_TOP_K_PARENT

(NUMBER_TOP_K_PARENT is the parameter for considering top k parent categories for each category, set to 10 by default)
