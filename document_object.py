
class Document_Object(object):
      dict_attr=None
      term_freq=None
      length=None
      
      def __init__(self):
          pass
          
      def __getattr__(self,attrName):
          return self.dict_attr[attrName]
      
      def setAttr(self,attrName,value):
          self.dict_attr[attrName]=value