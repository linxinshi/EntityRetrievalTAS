'''
This file defines object for each category in skos_categories dataset
'''

class Category_Profile_Object(object):
      id=None
      label=None
      rdf_type=None
      related=None
      parent=None
      children=None
      
      def __init__(self):
          # use list instead of set because it show priority by editor
          self.related=[]
          self.parent=[]
          self.children=[]
