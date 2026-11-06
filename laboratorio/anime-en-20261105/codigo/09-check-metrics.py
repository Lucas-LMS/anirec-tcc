"""Check tied ranking metrics against exhaustive small permutations."""
import importlib.util,itertools
from pathlib import Path
import numpy as np
from sklearn.metrics import ndcg_score
spec=importlib.util.spec_from_file_location('evaluation',Path(__file__).with_name('08-evaluate.py'));ev=importlib.util.module_from_spec(spec);spec.loader.exec_module(ev)
scores=[1,1,0,0,0];grades=np.array([2,1,0,0,2]);forbidden=np.array([False,False,True,False,False]);ideal=sorted(2.**grades-1,reverse=True);den=sum(g/np.log2(i+2) for i,g in enumerate(ideal))
concrete=[]
for first in itertools.permutations([0,1]):
    for last in itertools.permutations([2,3,4]):
        order=list(first+last);gs=grades[order];strict=gs==2;first_relevant=next(i+1 for i,g in enumerate(strict) if g)
        concrete.append([sum((2.**g-1)/np.log2(i+2) for i,g in enumerate(gs))/den,float(strict[0]),sum(strict[:3])/3,1/first_relevant,float(forbidden[order[0]])])
actual=ev.quality(scores,grades,2,grades,forbidden)
assert np.allclose([actual[k] for k in ['ndcg5','hit1','precision3','mrr5','violation1']],np.mean(concrete,axis=0))
# sklearn treats y_true as gains directly; supply our exponential gains.
assert np.isclose(actual['ndcg5'],ndcg_score([2.**grades-1],[scores],k=5,ignore_ties=False))
zero=ev.quality([0]*5,[0]*5,0,[0]*5,[False]*5);assert zero['ndcg5']==0 and zero['mrr5']==0 and zero['zero_ideal_gain']
perfect=ev.quality([5,4,3,2,1],[2,2,1,0,0],2,[2,2,1,0,0],[False]*5);assert np.isclose(perfect['ndcg5'],1) and perfect['mrr5']==1 and perfect['recall10']==1
print('Expected ties match exhaustive permutations and sklearn; zero/perfect cases passed.')
