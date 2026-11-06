"""Run the authorized anime experiment only after SMS inference/report finishes.

This supervisor waits in short intervals and saves a recoverable stage log.
No paid provider fallback. One local model at a time.
"""
import datetime,json,subprocess,sys,time,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];WORK=ROOT.parents[1];CODE=ROOT/'codigo';OUT=ROOT/'results';OUT.mkdir(exist_ok=True)
def stamp(stage):
    print(datetime.datetime.now().isoformat(timespec='seconds'),stage,flush=True)
    (OUT/'run-state.json').write_text(json.dumps(dict(stage=stage,timestamp=datetime.datetime.now().isoformat()),indent=2),encoding='utf-8')
def linux(path):return '/mnt/'+path.drive[0].lower()+'/'+path.as_posix().split(':/',1)[1]
def wsl(python,script,*args):return ['wsl','-d','Ubuntu','--',python,linux(CODE/script),*args]
try:
    stamp('waiting_for_SMS_completion')
    state=WORK/'output/comparacao-sms/estado-atualizacao.json'
    while True:
        if state.exists() and json.loads(state.read_text(encoding='utf-8')).get('completed')==13:break
        time.sleep(50)
    stamp('indexing_and_retrieval')
    subprocess.run(['wsl','-d','Ubuntu','--','bash',linux(CODE/'04-retrievers.sh')],check=True)
    stamp('freezing_shared_shortlists')
    if not (ROOT/'data/shortlists.json').exists():subprocess.run(wsl('/home/lucas/tcc-lab/.venv-sentences/bin/python','05-freeze-shortlists.py'),check=True)
    stamp('listwise_reranking')
    # Remote I/O runs concurrently with only one local model, as in SMS.
    remote_log=(OUT/'groq-console.log').open('w',encoding='utf-8')
    remote=subprocess.Popen(wsl('/home/lucas/tcc-lab/.venv-groq/bin/python','06-rerank.py','--model','gptoss'),stdout=remote_log,stderr=subprocess.STDOUT)
    try:subprocess.run(['wsl','-d','Ubuntu','--','bash',linux(CODE/'07-local-rerankers.sh')],check=True)
    finally:
        remote.wait();remote_log.close()
    if remote.returncode:raise RuntimeError('Remote inference stopped; inspect groq-console.log; no paid fallback.')
    stamp('evaluating')
    subprocess.run(wsl('/home/lucas/tcc-lab/.venv-sentences/bin/python','08-evaluate.py'),check=True)
    stamp('ready_for_report_review')
except Exception:
    traceback.print_exc();stamp('error_checkpoint_preserved');raise
