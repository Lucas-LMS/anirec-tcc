"""Metricas tie-aware, verificacao independente de nDCG e bootstrap por intencao."""
import collections
import csv
import hashlib
import json
import math
import pathlib

import numpy as np
from sklearn.metrics import ndcg_score

ROOT = pathlib.Path(__file__).resolve().parents[1]
MAIN = ['tfidf','glove','fasttext','w2v-cbow','w2v-sg','minilm']
NAMES = {'tfidf':'TF-IDF', 'glove':'GloVe text8 50d', 'fasttext':'fastText fil9 100d',
         'w2v-cbow':'Word2Vec CBOW text8', 'w2v-sg':'Word2Vec Skip-gram text8',
         'minilm':'MiniLM multilíngue', 'w2v-lee-cbow':'Word2Vec CBOW Lee (diagnóstico)',
         'w2v-lee-sg':'Word2Vec Skip-gram Lee (diagnóstico)'}


def groups(scores):
    order = np.argsort(-scores, kind='stable')
    start = 0
    while start < len(order):
        end = start+1
        while end < len(order) and scores[order[end]] == scores[order[start]]:
            end += 1
        yield start, order[start:end]
        start = end


def metrics(grades, scores):
    gains = 2.0**grades-1
    ideal = np.sort(gains)[::-1][:5]
    idcg = np.sum(ideal/np.log2(np.arange(len(ideal))+2))
    dcg, recovered, rr, hit, precision = 0., 0., 0., 0., 0.
    rr_found = False
    for start, positions in groups(scores):
        n = len(positions)
        positives = int((grades[positions] >= 1).sum())
        strong = int((grades[positions] == 2).sum())
        if start == 0:
            hit = strong/n
        amount = max(0, min(n, 5-start))
        if amount:
            dcg += gains[positions].mean()*sum(1/math.log2(i+2) for i in range(start,start+amount))
            recovered += amount*positives/n
        amount3 = max(0, min(n, 3-start))
        precision += amount3*positives/n/min(3,len(scores))
        if strong and not rr_found and start < 10:
            probability_no_previous = 1.0
            for j in range(1,min(n,10-start)+1):
                probability_first = probability_no_previous*strong/(n-j+1)
                rr += probability_first/(start+j)
                probability_no_previous *= max(0,(n-strong-j+1))/(n-j+1)
            rr_found = True
    return {'ndcg5': float(dcg/idcg), 'hit1': float(hit), 'mrr10': float(rr),
            'recall5': float(recovered/int((grades >= 1).sum())), 'precision3': float(precision)}


def resource(path):
    text = path.read_text()
    rss = None
    for line in text.splitlines():
        if 'Maximum resident set size' in line:
            rss = int(line.rsplit(':',1)[1].strip())
    return {'max_rss_kib': rss}


def main():
    # Casos manuais validam o tratamento de empates, nao apenas a formula sem empates.
    test = metrics(np.array([2,0]), np.array([0.,0.]))
    assert np.isclose(test['hit1'], .5) and np.isclose(test['mrr10'], .75)
    assert np.isclose(test['ndcg5'], (1+1/math.log2(3))/2)
    assert np.isclose(metrics(np.array([2,1,0]), np.array([3.,2.,1.]))['ndcg5'], 1)
    data = ROOT/'dados'
    frozen = json.loads((data/'freeze.json').read_text())
    for name, digest in frozen['files_sha256'].items():
        assert hashlib.sha256((data/name).read_bytes()).hexdigest() == digest
    catalog = json.loads((data/'catalogo.json').read_text())
    queries = json.loads((data/'consultas.json').read_text())
    cindex = {row['id']:i for i,row in enumerate(catalog)}
    qindex = {row['id']:i for i,row in enumerate(queries)}
    grades = np.full((len(queries),len(catalog)), -1, dtype=int)
    with (data/'relevancia.csv').open() as source:
        for row in csv.DictReader(source):
            qi, di = qindex[row['query_id']], cindex[row['anime_id']]
            assert grades[qi,di] == -1, 'Par duplicado'
            grades[qi,di] = int(row['grade'])
    assert np.isin(grades,[0,1,2]).all() and (grades == 2).any(axis=1).all()
    assert len({row['title'] for row in catalog}) == len(catalog)
    families = sorted({row['family'] for row in queries})
    family_indices = [[i for i,row in enumerate(queries) if row['family'] == family] for family in families]
    assert all(len(indices) == 2 for indices in family_indices)
    rng = np.random.default_rng(20261029)
    resampling = rng.integers(0,len(families),size=(5000,len(families)))
    rows, rankings, summary, metadata, family_values = [], {}, {}, {}, {}
    qa_errors = []
    models = MAIN+['w2v-lee-cbow','w2v-lee-sg']
    for model in models:
        folder = ROOT/'resultados/v1'/model
        meta = json.loads((folder/'resultado.json').read_text())
        assert meta['catalog_ids'] == [row['id'] for row in catalog]
        assert meta['query_ids'] == [row['id'] for row in queries]
        matrices = np.load(folder/'matrizes.npz')
        metadata[model] = meta | resource(folder/'recursos.txt')
        summary[model], rankings[model], family_values[model] = {}, {}, {}
        for scenario in ['PT_EN','EN_EN','PT_PT']:
            scores = matrices[scenario]
            assert scores.shape == grades.shape and np.isfinite(scores).all()
            values = []
            rankings[model][scenario] = []
            for i, query in enumerate(queries):
                measured = metrics(grades[i], scores[i])
                reference = ndcg_score([(2.0**grades[i]-1)], [scores[i]], k=5, ignore_ties=False)
                qa_errors.append(abs(measured['ndcg5']-reference))
                assert np.isclose(measured['ndcg5'], reference, atol=1e-10)
                assert all(-1e-8 <= value <= 1+1e-8 for value in measured.values())
                row = {'model': model, 'model_name': NAMES[model], 'scenario': scenario,
                       'query_id': query['id'], 'family': query['family'], 'style': query['style'], **measured}
                rows.append(row); values.append(measured)
                order = sorted(range(len(catalog)), key=lambda j: (-float(scores[i,j]),int(catalog[j]['id'])))
                rankings[model][scenario].append([
                    {'id':catalog[j]['id'], 'title':catalog[j]['title'], 'grade':int(grades[i,j]),
                     'score':float(scores[i,j])} for j in order])
            metrics_names = list(values[0])
            aggregate = {metric: float(np.mean([v[metric] for v in values])) for metric in metrics_names}
            fvalues = np.array([np.mean([values[i]['ndcg5'] for i in indices]) for indices in family_indices])
            family_values[model][scenario] = fvalues
            bootstrap = fvalues[resampling].mean(axis=1)
            aggregate['ndcg5_ci95'] = list(map(float,np.quantile(bootstrap,[.025,.975])))
            aggregate['by_style'] = {
                style: {metric:float(np.mean([v[metric] for i,v in enumerate(values) if queries[i]['style']==style]))
                        for metric in metrics_names} for style in ['literal','paraphrase']}
            summary[model][scenario] = aggregate
    winner = max(MAIN, key=lambda name: summary[name]['PT_EN']['ndcg5'])
    deltas = {}
    for other in MAIN:
        if other == winner:
            continue
        difference = family_values[winner]['PT_EN']-family_values[other]['PT_EN']
        distribution = difference[resampling].mean(axis=1)
        deltas[other] = {'mean_difference_ndcg5':float(difference.mean()),
                         'ci95':list(map(float,np.quantile(distribution,[.025,.975])))}
    uninformed = [metrics(grade,np.zeros(len(catalog))) for grade in grades]
    chance = {key:float(np.mean([row[key] for row in uninformed])) for key in uninformed[0]}
    with (ROOT/'resultados/metricas-por-consulta.csv').open('w',newline='',encoding='utf-8') as target:
        writer = csv.DictWriter(target, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    report = {'primary_scenario':'PT_EN', 'confirmed_by_user':True,
              'winner_primary_pilot':winner, 'main_models':MAIN, 'names':NAMES,
              'summary':summary, 'winner_paired_differences':deltas, 'uninformed_tie_baseline':chance,
              'metadata':metadata, 'qa':{'ndcg_crosschecks':len(qa_errors), 'max_abs_difference_sklearn':max(qa_errors),
                                       'full_judgments':int(grades.size), 'query_families':len(families),
                                       'bootstrap_repetitions':5000, 'seed':20261029,
                                       'manual_tie_test_passed':True},
              'limitations':['AI-authored descriptions and qrels, no human validation',
                             'Convenience sample, curated plots and short descriptions',
                             'Different corpora, dimensions and pretraining budgets',
                             'Repeated paraphrases are paired within family',
                             'Diagnostic batch timings; not online latency or generalization evidence']}
    (ROOT/'resultados/resumo.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'resultados/rankings.json').write_text(json.dumps(rankings,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Vencedor operacional provisório PT_EN:', winner)
    for model in MAIN:
        print(NAMES[model], json.dumps(summary[model]['PT_EN']))
    print('QA:', report['qa'])


if __name__ == '__main__':
    main()
