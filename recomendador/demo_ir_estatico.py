"""Offline IR demo using frozen static document vectors, not a trained ranker.

This is a mechanism demonstration, not the final UI or a personalization
benchmark. It uses the 1,000-item English catalog, which is not AniList live.
"""
import argparse,json,unicodedata,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]/'laboratorio/anime-en-20261105'
def normalize_title(s):return unicodedata.normalize('NFKC',s).casefold().strip()
def main():
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser()
    parser.add_argument('--anime',help='Exact title or MAL ID present in the demo catalog')
    parser.add_argument('--favorite',action='append',default=[],help='Favorite title or MAL ID; repeat for more')
    parser.add_argument('--alpha',type=float,default=.7,help='Anchor weight when favorites exist; 0.4 to 1, engineering setting')
    parser.add_argument('--model',choices=['glove','fasttext','w2v-cbow','w2v-sg'],default='w2v-sg')
    parser.add_argument('--topk',type=int,default=5)
    parser.add_argument('--list',action='store_true',help='Show catalog titles; no network or inference')
    args=parser.parse_args()
    catalog=json.loads((ROOT/'data/catalog.json').read_text(encoding='utf-8'))
    if args.list:
        print(json.dumps([dict(id=r['id'],title=r['title']) for r in catalog[:30]],ensure_ascii=False,indent=2));return
    if not args.anime:parser.error('Choose --anime or use --list to see examples.')
    if not .4<=args.alpha<=1 or not 1<=args.topk<=20:parser.error('alpha must be 0.4..1 and topk 1..20.')
    def lookup(value):
        found=[i for i,r in enumerate(catalog) if r['id']==value or normalize_title(r['title'])==normalize_title(value)]
        if len(found)!=1:raise ValueError('Title/ID not uniquely found in the 1,000-item demo; use --list. No silent AniList replacement.')
        return found[0]
    seed=lookup(args.anime);favorites=sorted(set(lookup(x) for x in args.favorite))
    matrix=np.load(ROOT/f'results/retrieval/{args.model}/document-index.npy')
    assert matrix.shape[0]==len(catalog)
    anchor=matrix[seed]
    if np.linalg.norm(anchor)==0:raise ValueError('Anchor has no usable vector for this model.')
    anchor_scores=matrix@anchor
    profile_scores=np.zeros(len(catalog));alpha=1.
    if favorites:
        # Explicit arithmetic aggregation; no fit, labels or weight optimization.
        profile=matrix[favorites].mean(axis=0);norm=np.linalg.norm(profile)
        if norm==0:raise ValueError('Favorites have no usable profile vector.')
        profile=profile/norm;profile_scores=matrix@profile;alpha=args.alpha
    # Each document vector is L2-normalized; dot products are cosine similarities.
    scores=alpha*anchor_scores+(1-alpha)*profile_scores
    excluded={seed,*favorites}
    ranking=sorted((i for i in range(len(catalog)) if i not in excluded),key=lambda i:(-float(scores[i]),int(catalog[i]['id'])))[:args.topk]
    result=dict(demo_not_benchmark=True,model=args.model,anchor=catalog[seed]['title'],favorites=[catalog[i]['title'] for i in favorites],anchor_weight=round(alpha,6),profile_weight=round(1-alpha,6),score_is_probability=False,
        results=[dict(id=catalog[i]['id'],title=catalog[i]['title'],score=float(scores[i]),anchor_similarity=float(anchor_scores[i]),profile_similarity=float(profile_scores[i]) if favorites else None,genres=catalog[i]['genres']) for i in ranking])
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
