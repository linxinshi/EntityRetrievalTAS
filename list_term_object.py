# coding=utf-8
from nltk.stem.snowball import SnowballStemmer
from lib_process import *
from nltk.stem import WordNetLemmatizer
from nltk.util import ngrams
from config import *

class List_Term_Object(object):
      str=None
      term=None
      final=None
      stem=None
      length=None
      term_freq=None
      bigram_freq=None
      
      def __init__(self,line,raw_mode,SEPERATE_CHAR,mongoObj,w2vmodel):
          self.str=line.strip()
          self.get_term(raw_mode,SEPERATE_CHAR)
          #self.update_term(mongoObj,w2vmodel)
          self.update_term_freq()
          #self.update_bigram_freq()
      
      def get_term(self,raw_mode,SEPERATE_CHAR):
          # first mark ngram before stemming
          if raw_mode==False:
             stmp=remove_stopwords(cleanSentence(self.str,True,SEPERATE_CHAR),SEPERATE_CHAR)
             qts=stmp.split(SEPERATE_CHAR)
          else:
             qts=self.str.split(SEPERATE_CHAR)
          self.term=qts   
          self.length=len(self.term)          

      def get_term_lucene(self,docid,field,lucene_obj):
          self.term=lucene_obj.get_terms(docid,field)
          self.length=len(self.term)
      
      def update_term_freq(self):
          self.term_freq={}
          for t in self.term:
              if t not in self.term_freq:
                 self.term_freq[t]=0
              self.term_freq[t]+=1
              
      def update_bigram_freq(self):
          bigrams = ngrams(self.term,2)
          #if self.bigram_freq==None:
             #self.bigram_freq={}
          for bigram_pair in bigrams:
              bigram=bigram_pair[0]+' '+bigram_pair[1]
              if bigram not in self.term_freq:
                 self.term_freq[bigram]=0
              self.term_freq[bigram]+=1
          
      def update_term(self,mongoObj,w2vmodel):
          stemmer=SnowballStemmer('english')
          self.final=[]
          self.stem=[]
          wordnet_lemmatizer = WordNetLemmatizer()
          
          # update word root
          len_t=len(self.term)
          for i in range(len_t):
              t=self.term[i]
              t_stem=stemmer.stem(t)
              t_final_tmp=''
              (self.stem).append(t_stem)
              t_lemma=wordnet_lemmatizer.lemmatize(t)
              # find root term in w2vmodel
              if WORD_EMBEDDING_TYPE!='NONE':
                 if t in w2vmodel.vocab:
                    t_final_tmp=t
                 elif t_lemma in w2vmodel.vocab:
                      t_final_tmp=t_lemma                 

              (self.final).append(t_final_tmp)
              