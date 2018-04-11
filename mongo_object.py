import pymongo

class Mongo_Object(object):
      client = None
      db = None
      conn_acs = None # article category sentence
      conn_page_id = None
      
      def __init__(self,hostname,port):
          self.client = pymongo.MongoClient(hostname,port)
          self.db = (self.client).wiki2015
          self.conn_page_id=self.db['page_id']
          self.conn_acs=self.db['article_categories']
          
      def __del__(self):
          (self.client).close()