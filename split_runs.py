import string
import sys,os

filter={}
results={}
all_data_name=[]
for filename in ['INEX_LD_v2.txt','ListSearch_v2.txt','QALD2_v2.txt','SemSearch_ES_v2.txt']:
    with open('E:\\Entity_Retrieval\\query\\simple_cluster\\%s'%(filename),'r',encoding='utf-8') as src:
         data_name=filename.replace('.txt','')
         results[data_name]=[]
         all_data_name.append(data_name)
         for line in src:
             item=line.strip().split('\t')
             qid=item[0]
             filter[qid]=data_name

run_name=sys.argv[1]
with open(run_name,'r',encoding='utf-8') as dest:
     for line in dest:
         qid=line.strip().split('\t')[0]
         data_name=filter[qid]
         results[data_name].append(line)

for data_name in all_data_name:
    with open('%s.runs'%(data_name),'w',encoding='utf-8') as dest:
         dest.writelines(results[data_name])
    cmd='trec_eval -q -m num_q -m num_ret -m num_rel -m num_rel_ret -m P.5,10,15,20,30,100 -m map_cut.100 -m ndcg_cut.10 %s %s > %s_results.txt'%('E:\\qrels-v2.txt','%s.runs'%(data_name),data_name)
    os.system(cmd)