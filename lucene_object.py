import os
import lucene
from java.io import File
from java.nio.file import Paths
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.document import Document, Field, StringField, TextField, StoredField
from org.apache.lucene.index import IndexWriter, IndexWriterConfig, DirectoryReader, Term
from org.apache.lucene.store import MMapDirectory
from org.apache.lucene.util import Version
from org.apache.lucene.queryparser.classic import ParseException, QueryParser
from org.apache.lucene.search import IndexSearcher, ScoreDoc, TopScoreDocCollector
from org.apache.lucene.search.similarities import BM25Similarity
from org.apache.lucene.search import PhraseQuery, BooleanQuery, TermQuery, BooleanClause
from org.apache.lucene.util import BytesRef, BytesRefIterator

from org.apache.lucene.search.spans import SpanQuery, SpanTermQuery, SpanNearQuery, NearSpansOrdered, NearSpansUnordered
from org.apache.lucene.search.spans import SpanScorer, SpanWeight, Spans
from org.apache.lucene.search import DocIdSetIterator
from config import LIST_F

class Lucene_Object(object):
      lucene_vm_init=None
      index_name=None
      index_dir=None
      index_mm=None
      analyzer=None
      config=None
      reader=None
      searcher=None
      searcher2=None

      dict_term_freq=None
      dict_doc=None
      total_field_freq=None
      
      def __init__(self,LUCENE_INDEX_DIR,similarity='BM25',lucene_vm_flag=False):
          if lucene_vm_flag==False:
             lucene.initVM(vmargs=['-Djava.awt.headless=true'])
          self.lucene_vm_init=True
          self.index_dir=LUCENE_INDEX_DIR
          self.index_mm = MMapDirectory(Paths.get(LUCENE_INDEX_DIR))
          self.analyzer = StandardAnalyzer()
          self.config = IndexWriterConfig(self.analyzer)
          self.reader = DirectoryReader.open(self.index_mm)
          self.searcher = IndexSearcher(self.reader)
          self.dict_term_freq={}
          self.dict_doc_field_title={}
          if similarity=='BM25':
            (self.searcher).setSimilarity(BM25Similarity())
            
      def getSecondarySearcher(self):
          if self.searcher2 is None:
             self.searcher2=IndexSearcher(self.reader)
          return self.searcher2
      

      def retrieve(self,query,field,hitsPerPage,boostList):
          querystr=query
          
          # build query
          q_lucene = QueryParser(field, self.analyzer).parse(querystr)
          # build searcher              
          collector = TopScoreDocCollector.create(hitsPerPage)
          (self.searcher).search(q_lucene, collector);
          hits = collector.topDocs().scoreDocs;
          
          len_hits=len(hits)
          single_query_result=[(self.searcher.doc(hits[j].doc),hits[j].doc) for j in range(len_hits)]
          return single_query_result
          
      def findDoc(self,title,field,is_docid_required=False):
          searcher=self.getSecondarySearcher()
          t=Term(field,title)
          query=TermQuery(t)
          docs=searcher.search(query,1)
          if docs.totalHits==0:
             if is_docid_required==True:
                 return None,None
             else:
                 return None
          docID=(docs.scoreDocs)[0].doc
          d=searcher.doc(docID)
          if is_docid_required==False:
             return d
          else:
             return d,docID
             
      def get_terms(self,docid,field):
          terms=self.reader.getTermVector(docid,field)
          te_itr=terms.iterator()
          return [brf.utf8ToString() for brf in BytesRefIterator.cast_(te_itr)]
      
      def clearCache(self):
          self.dict_term_freq.clear()
          
      def get_term_freq(self,docid,field,is_cached=False):
          if is_cached==True and (field,docid) in self.dict_term_freq:
             return self.dict_term_freq[(field,docid)]

          if len(self.dict_term_freq)>2000:
             self.dict_term_freq.clear()
             
          terms=self.reader.getTermVector(docid,field)
          term_freq={}
          if terms is not None:
             te_itr=terms.iterator()
             for bytesref in BytesRefIterator.cast_(te_itr):
                 t=bytesref.utf8ToString()
                 freq=te_itr.totalTermFreq()
                 term_freq[t]=freq
          
          self.dict_term_freq[(field,docid)]=term_freq
          return self.dict_term_freq[(field,docid)]
          
      def get_coll_termfreq(self, term, field):
          """ 
          Returns collection term frequency for the given field.

          :param term: string
          :param field: string, document field
          :return: int
          """
          return self.reader.totalTermFreq(Term(field, term))

      def get_doc_freq(self, term, field):
          """
          Returns document frequency for the given term and field.

          :param term: string, term
          :param field: string, document field
          :return: int
          """
          return self.reader.docFreq(Term(field, term))

      def get_doc_count(self, field):
          """
          Returns number of documents with at least one term for the given field.

          :param field: string, field name
          :return: int
          """
          return self.reader.getDocCount(field)

      def get_coll_length(self, field):
          """ 
          Returns length of field in the collection.

          :param field: string, field name
          :return: int
          """
          return self.reader.getSumTotalTermFreq(field)

      def get_avg_len(self, field):
          """ 
          Returns average length of a field in the collection.

          :param field: string, field name
          """
          
          n = self.reader.getDocCount(field)  # number of documents with at least one term for this field
          len_all = self.reader.getSumTotalTermFreq(field)
          if n == 0:
             return 0
          else:
             return len_all / float(n)
             
      def get_total_field_freq(self,fields):
          """Returns total occurrences of all fields"""
          if self.total_field_freq is None:
             total_field_freq = 0
             for f in fields:
                 total_field_freq += self.get_doc_count(f)
                 self.total_field_freq = total_field_freq
          return self.total_field_freq    
                     
      def get_coll_bigram_freq(self,bigram,field,ordered,slop,title,field_cache='title'):   
          searcher=self.getSecondarySearcher()
          SpanClauses=[]
          for term in bigram.split(' '):
              SpanClauses.append(SpanTermQuery(Term(field,term)))

          builder=SpanNearQuery.Builder(field,ordered)
          for i in range(len(SpanClauses)):
              clause=SpanClauses[i]
              builder.addClause(clause)
          builder.setSlop(slop) 
          q_lucene=builder.build()
          
          sw=q_lucene.createWeight(searcher,False)
          list_leaves=self.reader.getContext().leaves()
          frequency=0
          doc_phrase_freq={}
          for leave in list_leaves:
              spans = sw.getSpans(leave, SpanWeight.Postings.POSITIONS)
              if spans is None:
                 continue
              while spans.nextDoc()!=DocIdSetIterator.NO_MORE_DOCS:
                    id=leave.reader().document(spans.docID()).get(field_cache)
                    #id=leave.reader().document(spans.docID()).get('wiki_id')
                    
                    if id not in doc_phrase_freq:
                       doc_phrase_freq[id]=0
                    while spans.nextStartPosition()!=Spans.NO_MORE_POSITIONS:
                          doc_phrase_freq[id]+=1
                          frequency+=1     
          cf=sum(doc_phrase_freq.values())
          tf=doc_phrase_freq.get(title,0)
          return tf,cf
          #return doc_phrase_freq