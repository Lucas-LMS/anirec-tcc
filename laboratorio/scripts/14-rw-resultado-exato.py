"""Executa o avaliador oficial sem edita-lo e registra suas variaveis numericas."""
import hashlib
import json
import pathlib
import runpy
import sys

repo, run = map(pathlib.Path, sys.argv[1:])
sys.argv = ['eval.py', '-m', str(run/'vectors.txt'), '-d', str(repo/'data/rw/rw.txt')]
state = runpy.run_path(str(repo/'eval.py'), run_name='__main__')
result = {
    'spearman_rho': float(state['corr'][0]),
    'p_value': float(state['corr'][1]),
    'rho_times_100': float(state['corr'][0]*100),
    'total_pairs': int(state['nwords']), 'dropped_pairs': int(state['drop']),
    'official_evaluator_sha256': hashlib.sha256((repo/'eval.py').read_bytes()).hexdigest(),
    'dataset_origin': 'AWS mirror corroborated against academic copy; see manifests/rw/auditoria.json',
}
(run/'resultado-exato.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
