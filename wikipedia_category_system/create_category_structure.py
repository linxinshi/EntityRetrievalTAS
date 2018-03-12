import sys, gzip, pickle
import networkx

def load_zipped_pickle(filename):
    with gzip.open(filename, 'rb') as f:
         loaded_object = pickle.load(f)
         return loaded_object
          
def getDistSize(list_g):
    dist_size={}
    for c in list_g:
        lc=len(c)
        if lc not in dist_size:
           dist_size[lc]=0
        dist_size[lc]+=1
    return dist_size        
    
def extractCategoryLabel(line):
    pos=line.find('Category:')
    assert pos>-1
    return line[pos+9:-1]

def getCycleEdges(g):
    # input a list of vertex in the cycle g
    
    # modify: g[i] -> g.nodes[i] for networkx 2.0. 2017/12/28
    
    edges=[]
    len_g=len(g)
    for i in range(len_g-1):
        edges.append((g[i],g[i+1]))
    edges.append((g[len_g-1],g[0]))
    
    return edges
    
def main():
    profile=load_zipped_pickle('category_profiles_dbpedia_201510.gz')
    
    # choose top-k parent categories, therefore children for each category should be updated
    # parent field contains all parents for each category instead of top-k parent
    NUMBER_TOP_K_PARENT=10
    if len(sys.argv)>2:
       print ('usage: python create_category_structure.py [NUMBER_TOP_K_PARENT]')
       return
    try:
       NUMBER_TOP_K_PARENT=int(sys.argv[1])
       print ('NUMBER_TOP_K_PARENT=%d'%(NUMBER_TOP_K_PARENT))
    except:
       print ('NON-INTEGER INPUT')
       print ('usage: python create_category_structure.py [NUMBER_TOP_K_PARENT]')
       return
    
    D=networkx.DiGraph()
    for id in profile:
        D.add_node(extractCategoryLabel(id),label=profile[id].label)
    
    # update children
    for id in profile:
        for i in range(min(NUMBER_TOP_K_PARENT,len(profile[id].parent))):
            id_parent=profile[id].parent[i]
            if id_parent==id:
               continue
            if id_parent not in profile:
               continue
            D.add_edge(extractCategoryLabel(id_parent),extractCategoryLabel(id))
    
    list_scc=sorted(networkx.strongly_connected_component_subgraphs(D),key=len, reverse=True)
    #print (str(getDistSize(list_scc)))
    #print (len(list_scc))
    # remove edges in D instead of scc when generating cleaned DiGraph
    cnt=0
    for scc in list_scc:
        if networkx.is_directed_acyclic_graph(scc)==True:
           continue
        if len(scc)==1:
           continue
        print ('processing scc  size=%d'%(len(scc)))
        
        if len(scc)<500:
           # find circuit system, decompose it into elementary cycles
           lec=list(networkx.simple_cycles(scc))
           print ('number of elementary circuits:%d'%(len(lec)))
           set_edges_removed=set()
           set_cycle_edges=[set(getCycleEdges(cycle)) for cycle in lec]
           is_cycle_no_intersection=[True for i in range(len(lec))]
           for i in range(len(lec)-1):
               for j in range(i+1,len(lec)):
                   temp=set_cycle_edges[i] & set_cycle_edges[j]
                   if len(temp)>0:
                      set_edges_removed=set_edges_removed|(temp)
                      is_cycle_no_intersection[i]=False
                      is_cycle_no_intersection[j]=False
           
           D.remove_edges_from(set_edges_removed)
           for i in range(len(lec)):
               if is_cycle_no_intersection[i]==True:
                  #print ('find no intersection idx=%d'%(i))
                  cycle=lec[i]
                  u,v=cycle[0],cycle[-1]
                  try:
                      D.remove_edge(v,u)
                  except:
                      pass    
        else:
           print ('remove all edges from this scc since it is too big')
           print ('size=%d'%(len(scc.nodes())))
           D.remove_edges_from(scc.edges())
           # find a heuristic way
           pass
    
    print (str(networkx.is_directed_acyclic_graph(D)))
    print ('number of vertex:%d'%(len(D.nodes())))
    print ('number of edges:%d'%(len(D.edges())))
    print ('saving Digraph to disk')
    print ('begin reverse test')
    H=D.reverse()
    networkx.write_gpickle(D,'category_dag_dbpedia_top%d_debug.pkl.gz'%(NUMBER_TOP_K_PARENT))
        
if __name__ == '__main__':
   main()
