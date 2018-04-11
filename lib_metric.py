import math
from config import *

def get_dirichlet_prob(tf_t_d, len_d, tf_t_C, len_C, mu):
    """
    Computes Dirichlet-smoothed probability
    P(t|theta_d) = [tf(t, d) + mu P(t|C)] / [|d| + mu]

    :param tf_t_d: tf(t,d)
    :param len_d: |d|
    :param tf_t_C: tf(t,C)
    :param len_C: |C| = \sum_{d \in C} |d|
    :param mu: \mu
    :return:
    """
    if mu == 0:  # i.e. field does not have any content in the collection
       return 0
    else:
       p_t_C = tf_t_C / len_C if len_C > 0.0 else 0.0
       return (tf_t_d + mu * p_t_C) / (len_d + mu)

       
def lmSim(lt_obj1,entityObj,field,w2vmodel,mode,lucene_obj):
    # subquery x et[0..n-1] 
    totalSim=0.0
    if mode=='mul':
       totalSim=1.0
       
    term_freq=entityObj.term_freq
    len_C_f = lucene_obj.get_coll_length(field)
    mu=lucene_obj.get_avg_len(field)
    cnt=0
    
    # iterate each t in term_freq and compare similarity
    for i in range(lt_obj1.length):
        qt=lt_obj1.term[i]
        # compute p(t|De)
        localSim=term_freq.get(qt,0)
           
        if localSim>0.0:
           cnt+=1
           
        len_d_f = entityObj.length
        tf_t_d_f = localSim
        tf_t_C_f = lucene_obj.get_coll_termfreq(qt, field)
        
        p_t_d=get_dirichlet_prob(tf_t_d_f, float(len_d_f), float(tf_t_C_f), float(len_C_f), mu)
        # compute f(p(t1|De),p(t2|De)...) 
        if mode=='sum':
           totalSim+=p_t_d
        elif mode=='max':
           totalSim=max(p_t_d,totalSim)
        elif mode=='mul':
           if p_t_d>0.0:
              totalSim*=p_t_d
        elif mode=='log_sum' or mode=='log_sum_avg':
           if p_t_d>0.0:
              totalSim+=math.log(p_t_d)
    if mode=='log_sum_avg' and cnt>0:
       totalSim/=float(cnt)
    return totalSim
    
    
def mlmSim(lt_obj1,entityObj,lucene_obj):
    # need every field representation instead of single lt_obj for entity
    # subquery x et[0..n-1] 
    
    len_C_f={}
    mu={}
    mlm_weights={}
    for f in LIST_F:
        len_C_f[f]=lucene_obj.get_coll_length(f)
        mu[f]=lucene_obj.get_avg_len(f)
        mlm_weights[f]=1.0/len(LIST_F)
        
    if MODEL_NAME=='mlm-tc':
       mlm_weights={'stemmed_names':0.2,'stemmed_catchall':0.8} if USED_QUERY_VERSION=='stemmed_raw_query' else {'names':0.2,'catchall':0.8} 
        
    totalSim=0.0
    for i in range(lt_obj1.length):
        qt=lt_obj1.term[i]
        localSim=0.0
        # compute p(t|Df)
        for f in LIST_F:
            len_d_f = entityObj.lengths[f]
            tf_t_d_f = entityObj.term_freqs[f].get(qt,0)
            tf_t_C_f = lucene_obj.get_coll_termfreq(qt, f)
            
            tempSim=get_dirichlet_prob(tf_t_d_f, len_d_f, tf_t_C_f, len_C_f[f], mu[f])
            # compute f(p(t1|De),p(t2|De)...) 
            localSim+=mlm_weights[f]*tempSim
            
        if localSim>0.0:
           totalSim+=math.log(localSim)
    return totalSim


def sdmSim(queryObj,entityObj,field,lucene_obj):
    ft=fo=fu=0.0
    len_C_f = lucene_obj.get_coll_length(field)
    mu=lucene_obj.get_avg_len(field)
    
    ft=lmSim(queryObj.contents_obj,entityObj,field,None,'log_sum',lucene_obj)
    if LAMBDA_O>0:
       for bigram_pair in queryObj.bigrams:
           bigram=bigram_pair[0]+' '+bigram_pair[1]
           tf,cf=lucene_obj.get_coll_bigram_freq(bigram,field,True,0,entityObj.title)
           ptd=get_dirichlet_prob(tf,entityObj.length,cf,len_C_f,mu)
           if ptd>0:
              fo+=math.log(ptd)
    if LAMBDA_U>0:
       for bigram_pair in queryObj.bigrams:
           bigram=bigram_pair[0]+' '+bigram_pair[1]
           tf,cf=lucene_obj.get_coll_bigram_freq(bigram,field,False,6,entityObj.title)
           ptd=get_dirichlet_prob(tf,entityObj.length,cf,len_C_f,mu)
           if ptd>0:
              fu+=math.log(ptd)
    score=LAMBDA_T*ft+LAMBDA_O*fo+LAMBDA_U*fu
    return score
    
def fsdmSim(queryObj,entityObj,lucene_obj):
    fields=LIST_F
    
    len_C_f={}
    mu={}
    for f in LIST_F:
        len_C_f[f]=lucene_obj.get_coll_length(f)
        mu[f]=lucene_obj.get_avg_len(f)
        
    ft=fo=fu=0.0
    # w is a dict of weights for each field
    # compute ft
    for t in queryObj.contents_obj.term:
        w=get_mapping_prob(t,lucene_obj)
        ft_temp=0.0
        for field in w:
            tf=entityObj.term_freqs[field].get(t,0)
            cf=lucene_obj.get_coll_termfreq(t, field)            
            ptd=get_dirichlet_prob(tf,entityObj.lengths[field],cf,len_C_f[field],mu[field])
            if ptd>0:
               ft_temp+=ptd*w[field]
        if ft_temp>0:
           ft+=math.log(ft_temp)
    # compute fo
    if LAMBDA_O>0:
       for bigram_pair in queryObj.bigrams:
           bigram=bigram_pair[0]+' '+bigram_pair[1]
           w=get_mapping_prob(bigram,lucene_obj,ordered=True,slop=0)
           fo_temp=0.0
           for field in w:
               tf,cf=lucene_obj.get_coll_bigram_freq(bigram,field,True,0,entityObj.title)
               ptd=get_dirichlet_prob(tf,entityObj.lengths[field],cf,len_C_f[field],mu[field])
               if ptd>0:
                  fo_temp+=ptd*w[field]
           if fo_temp>0:
              fo+=math.log(fo_temp)
    # compute fu
    if LAMBDA_U>0:
       for bigram_pair in queryObj.bigrams:
           bigram=bigram_pair[0]+' '+bigram_pair[1]
           w=get_mapping_prob(bigram,lucene_obj,ordered=False,slop=6)
           fu_temp=0.0
           for field in w:
               tf,cf=lucene_obj.get_coll_bigram_freq(bigram,field,False,6,entityObj.title)
               ptd=get_dirichlet_prob(tf,entityObj.lengths[field],cf,len_C_f[field],mu[field])
               if ptd>0:
                  fu_temp+=ptd*w[field]
           if fu_temp>0:
              fu+=math.log(fu_temp)
    '''
    if queryObj.contents_obj.length>1:
       ft/=queryObj.contents_obj.length
       fo/=(queryObj.contents_obj.length-1)
       fu/=(queryObj.contents_obj.length-1)
    '''
    score=LAMBDA_T*ft+LAMBDA_O*fo+LAMBDA_U*fu
    return score
    
def get_mapping_prob(t,lucene_obj,ordered=True,slop=0):
    """
    Computes PRMS field mapping probability.
        p(f|t) = P(t|f)P(f) / sum_f'(P(t|C_{f'_c})P(f'))

    :param t: str
    :param coll_termfreq_fields: {field: freq, ...}
    :return Dictionary {field: prms_prob, ...}
    """
    fields=LIST_F
    
    if len(fields)==1:
       # for sdm and lm
       return {fields[0]:1.0}
    
    is_bigram=True if t.find(' ')>-1 else False     
    #find cache
          
    coll_termfreq_fields={}
    
    for f in fields:
        if is_bigram==False:
           coll_termfreq_fields[f]=lucene_obj.get_coll_termfreq(t, f)
        else:
           coll_termfreq_fields[f]=lucene_obj.get_coll_bigram_freq(t,f,ordered,slop,'NONE')[1]

    total_field_freq=lucene_obj.get_total_field_freq(fields)
    # calculates numerators for all fields: P(t|f)P(f)
    numerators = {}
    for f in fields:
        p_t_f = coll_termfreq_fields[f] / lucene_obj.get_coll_length(f)
        p_f = lucene_obj.get_doc_count(f) / total_field_freq
        p_f_t = p_t_f * p_f
        if p_f_t > 0:
           numerators[f] = p_f_t
        else:
           numerators[f]=0

    # calculates denominator: sum_f'(P(t|C_{f'_c})P(f'))
    denominator = sum(numerators.values())

    mapping_probs = {}
    if denominator > 0:  # if the term is present in the collection
       for f in numerators:
           mapping_probs[f] = numerators[f] / denominator
           
    return mapping_probs
    
# ============================    
def mlm_sas(queryObj,entityObj,structure,lucene_handler):
    if len(entityObj.categories)==0:
       return NEGATIVE_INFINITY
    D=structure.cat_dag
    lucene_cat=lucene_handler['category_corpus']
    lucene_doc=lucene_handler['first_pass']
    
    len_d_f=entityObj.lengths
    
    sum_score=0.0
    max_score=NEGATIVE_INFINITY
    len_C_f={}
    mlm_weights={}
    sum_ptc={}
    mu={}
    for field in LIST_F:
        len_C_f[field]=lucene_doc.get_coll_length(field)
        mu[field]=lucene_doc.get_avg_len(field)
        mlm_weights[field]=1.0/len(LIST_F)
        sum_ptc[field]=[0.0 for i in range(queryObj.contents_obj.length)]
        
    if MODEL_NAME=='mlm-tc':
       mlm_weights={'stemmed_names':0.2,'stemmed_catchall':0.8} if USED_QUERY_VERSION=='stemmed_raw_query' else {'names':0.2,'attributes':0.8} 

    curPath=[]

    def smooth_path(cat,path_len,alpha_t,sum_nominator):
        nonlocal D,curPath,sum_ptc,cnt_path
        nonlocal max_score_p_cat,max_score
        nonlocal lucene_cat,lucene_doc
        
        if cnt_path>TOP_PATH_NUM_PER_CAT:
           return
        # the following is end condition
        if path_len==LIMIT_SAS_PATH_LENGTH or len(D[cat])==0:
           # compute score
           cnt_path+=1
           if alpha_t==ALPHA_SAS:
              return      
           cof=(1-ALPHA_SAS)/(ALPHA_SAS-alpha_t)
           #cof=0.003
           score_p=0.0
           for j in range(queryObj.contents_obj.length):
               term=queryObj.contents_obj.term[j]
               ptd=0.0
               for f in LIST_F:
                   tf_d_f=entityObj.term_freqs[f].get(term,0.0)
                   cf_f = lucene_doc.get_coll_termfreq(term, f)
                   ptc_doc=cf_f/len_C_f[f] if len_C_f[f]>0 else 0.0
                   ptd_f=(tf_d_f+mu[f]*ptc_doc+cof*sum_ptc[f][j])/(len_d_f[f]+mu[f]+cof*sum_nominator[f]) if (len_d_f[f]+mu[f]+cof*sum_nominator[f])>0 else 0.0             
                   '''
                   if tf_d_f>0:
                      ptd_f=(tf_d_f+mu[f]*ptc_doc+cof*sum_ptc[f][j])/(len_d_f[f]+mu[f]+cof*sum_nominator[f]) if len_d_f[f]+mu[f]+cof*sum_nominator[f]>0 else 0.0
                   else:
                      ptd_f=(tf_d_f+mu[f]*ptc_doc)/(len_d_f[f]+mu[f]) if len_d_f[f]+mu[f]>0 else 0.0
                   '''

                   ptd+=mlm_weights[f]*ptd_f
               if ptd>0:
                  score_p+=math.log(ptd)
           if score_p>max_score_p_cat:
              max_score_p_cat=score_p
           return
           
        # maintain useful temporary variables
        d,docID=lucene_cat.findDoc(cat,'category',True)
        bak_sum_ptc=sum_ptc.copy()
        if d is not None:
           # maintain
           cnt_doc_corpus=int(d['num_articles'])
           for f in LIST_F:
               # get category corpus
               term_freq=lucene_cat.get_term_freq(docID,f,True)
               len_c=sum(term_freq.values())
               mu_c=len_c/cnt_doc_corpus if cnt_doc_corpus>0 else 0.0
               sum_nominator[f]+=alpha_t*mu_c             

               for j in range(queryObj.contents_obj.length):
                   term=queryObj.contents_obj.term[j]
                   tf_c=term_freq.get(term,0.0)     
                   ptc=tf_c/len_c if len_c>0 else -1    
                   if ptc>-1:  
                      sum_ptc[f][j]+=(alpha_t*mu_c*ptc) 
                                     
        cnt=0
        for child in iter(D[cat]):
            if child in D:
               curPath.append(child)
               smooth_path(child,path_len+1,alpha_t*ALPHA_SAS,sum_nominator)
               curPath.pop()
               sum_ptc=bak_sum_ptc.copy()
            cnt+=1
            if cnt>TOP_CATEGORY_NUM:
               break
    # end of function smooth_path
    
    for cat in entityObj.categories[:TOP_CATEGORY_NUM]:
        if cat not in D:
           continue
        max_score_p_cat=NEGATIVE_INFINITY     
        cnt_path=0
        smooth_path(cat,1,ALPHA_SAS,{f:0.0 for f in LIST_F})
        
        if max_score_p_cat>NEGATIVE_INFINITY:
           sum_score+=max_score_p_cat
        if max_score_p_cat>max_score:
           max_score=max_score_p_cat
               
    return max_score    
#===========================================
def lm_sas(queryObj,entityObj,structure,lucene_handler,mongoObj,field):
    if len(entityObj.categories)==0:
       return NEGATIVE_INFINITY
    D=structure.cat_dag
    lucene_cat=lucene_handler['category_corpus']
    lucene_doc=lucene_handler['first_pass']
    
    termList=entityObj.term_freq
    len_d=entityObj.length
    
    sum_score=0.0
    max_score=NEGATIVE_INFINITY
    len_C_f = lucene_doc.get_coll_length(field)
    mu_d=lucene_doc.get_avg_len(field)

    curPath=[]
    sum_ptc=[0.0 for i in range(queryObj.contents_obj.length)]
    
    def smooth_path(cat,path_len,alpha_t,sum_nominator):
        nonlocal D,curPath,sum_ptc,cnt_path
        nonlocal max_score_p_cat,max_score
        nonlocal lucene_cat,lucene_doc
        
        if cnt_path>TOP_PATH_NUM_PER_CAT:
           return
        if path_len==LIMIT_SAS_PATH_LENGTH or len(D[cat])==0:
           # compute score
           cnt_path+=1
           if alpha_t==ALPHA_SAS:
              return       
           cof=(1-ALPHA_SAS)/(ALPHA_SAS-alpha_t)
           #cof=0.003
           score_p=0.0
           for j in range(queryObj.contents_obj.length):
                term=queryObj.contents_obj.term[j]
                tf_d=entityObj.term_freq.get(term,0.0)
                tf_t_C_f = lucene_doc.get_coll_termfreq(term, field)
                ptc_doc=tf_t_C_f/len_C_f if len_C_f>0 else 0.0
                ptd=(tf_d+mu_d*ptc_doc+cof*sum_ptc[j])/(len_d+mu_d+cof*sum_nominator) if len_d+mu_d+cof*sum_nominator>0 else 0.0
                '''
                if tf_d==0:
                   ptd=(tf_d+mu_d*ptc_doc+cof*sum_ptc[j])/(len_d+mu_d+cof*sum_nominator) if len_d+mu_d+cof*sum_nominator>0 else 0.0
                else:
                   ptd=(tf_d+mu_d*ptc_doc)/(len_d+mu_d) if len_d+mu_d>0 else 0.0
                '''
                if ptd>0:
                   score_p+=math.log(ptd)
           if score_p>max_score_p_cat:
              max_score_p_cat=score_p
           return
           
        # maintain useful temporary variables
        d,docID=lucene_cat.findDoc(cat,'category',True)
        bak_sum_ptc=sum_ptc[:]
        if d is not None:
           # maintain
           term_freq=lucene_cat.get_term_freq(docID,field,True)
           len_c=sum(term_freq.values())
           cnt_doc_corpus=int(d['num_articles'])
           mu_c=len_c/cnt_doc_corpus if cnt_doc_corpus>0 else 0.0
           sum_nominator+=alpha_t*mu_c         

           for j in range(queryObj.contents_obj.length):
               term=queryObj.contents_obj.term[j]
               tf_c=term_freq.get(term,0.0)     
               ptc=tf_c/len_c if len_c>0 else -1    
               if ptc>-1:  
                  sum_ptc[j]+=(alpha_t*ptc*mu_c)                     
        
        cnt=0
        for child in iter(D[cat]):
            cnt+=1
            if cnt>TOP_CATEGORY_NUM:
               break
            if child in D:
               curPath.append(child)
               smooth_path(child,path_len+1,alpha_t*ALPHA_SAS,sum_nominator)
               curPath.pop()
               sum_ptc=bak_sum_ptc[:]
    # end of function smooth_path
    
    for cat in entityObj.categories[:TOP_CATEGORY_NUM]:
        if cat not in D:
           continue
        
        max_score_p_cat=NEGATIVE_INFINITY     
        cnt_path=0
        smooth_path(cat,1,ALPHA_SAS,0.0)
        if max_score_p_cat>NEGATIVE_INFINITY:
           sum_score+=max_score_p_cat
        if max_score_p_cat>max_score:
           max_score=max_score_p_cat
               
    return max_score

# ============================