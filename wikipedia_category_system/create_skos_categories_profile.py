'''
This program create profile for each category in skos_categories dataset

'''

import pickle, gzip
from category_profile_object import Category_Profile_Object

def save_zipped_pickle(obj, filename, protocol=-1):
    with gzip.open(filename, 'wb') as f:
         pickle.dump(obj, f, protocol)
         
def load_zipped_pickle(filename):
    with gzip.open(filename, 'rb') as f:
         loaded_object = pickle.load(f)
         return loaded_object

         
def extractLabel(line):
    #print ('line:'+line)
    pos1=line.find('"')
    pos2=line.rfind('"')
    assert (pos1>-1)
    return line[pos1+1:pos2]
    
def main():
    profile={}
    with open('skos_categories_en.ttl','r',encoding='utf-8') as f:
         cnt=0
         for line in f.readlines():
             if line.startswith('#')==True:
                continue
             
             cnt+=1
             #if cnt>100:
                #break
             
             # since label contains blank space, line cannot be split into items by blank space
             list_item=line.strip().split('>')
             id=list_item[0].strip()+'>'
             pred=list_item[1].strip()+'>'
             
             # <...Category:Alphabet_Inc.>
             obj=list_item[2].strip()
             if len(list_item)==4:
                obj=obj+'>'
             else:
                obj=obj.strip('. ')
                
             #print ('%s %s %s'%(id,pred,obj))
             
             
             if id not in profile:
                profile[id]=Category_Profile_Object()
                profile[id].id=id
             
             # act depending on pred
             if pred.find('22-rdf-syntax-ns#type')>-1:
                profile[id].rdf_type=obj
             elif pred.find('core#prefLabel')>-1:
                  profile[id].label=extractLabel(obj)
             elif pred.find('core#broader>')>-1:
                  profile[id].parent.append(obj)
             elif pred.find('core#related')>-1:
                  profile[id].related.append(obj)
             else:
                  print ('UNKNOWN PREDICATE!')
             
    # update children field for each category
    
    with open('error_category_id.txt','w',encoding='utf-8') as f:
         for id in profile:
             if profile[id].label==None or profile[id].rdf_type==None:
                print ('ERROR id:%s'%(id))
             for id_parent in profile[id].parent:
                 if id_parent not in profile:
                    f.write('ERROR id_parent:%s\tid:%s\n'%(id_parent,id))
                 else:
                    profile[id_parent].children.append(id)
    
    # output
    
    print ('save category profiles to dump file')
    save_zipped_pickle(profile,'category_profiles_dbpedia_201510.gz')
    
    '''
    for id in profile:
        print ('-----------------------------')
        print ('%s %s %s'%(profile[id].id,profile[id].label,profile[id].rdf_type)) 
        print (str(profile[id].related)+'\n')
        print (str(profile[id].parent)+'\n')
    '''
         
if __name__ == '__main__':
   main()