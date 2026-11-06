"""Acompanha a execução já iniciada e atualiza arquivos; não faz inferência.

Não inicia nova API, não modifica os modelos e não altera respostas. Mantém
histórico dos relatórios anteriores. Pode continuar com o computador ligado.
"""
import datetime,json,shutil,subprocess,sys,time,traceback
from pathlib import Path
BASE=Path(__file__).resolve().parents[1];WORK=BASE.parents[1]
OUT=WORK/'output/comparacao-sms';ROOT=BASE/'resultados/benchmark-v1'
CODE=BASE/'codigo';state=OUT/'estado-atualizacao.json'
last=json.loads(state.read_text(encoding='utf-8')).get('completed',11) if state.exists() else 11
def now():return datetime.datetime.now().isoformat(timespec='seconds')
def run_analysis():
    # Executa o avaliador com sklearn no ambiente já usado para a análise.
    windows=CODE/'12-avaliar-comparacao.py'
    linux='/mnt/'+windows.drive[0].lower()+'/'+windows.as_posix().split(':/',1)[1]
    subprocess.run(['wsl','-d','Ubuntu','--','/home/lucas/tcc-lab/.venv-sentences/bin/python',linux],check=True)
def archive(count):
    dest=OUT/'historico'/f'{count}-modelos';dest.mkdir(parents=True,exist_ok=True)
    for p in OUT.iterdir():
        if p.is_file():shutil.copy2(p,dest/p.name)
    for name in ['comparacao.json','comparacao.csv']:
        src=BASE/'resultados/comparacao'/name
        if src.exists():shutil.copy2(src,dest/name)
try:
    print(now(),f'Acompanhamento iniciado; relatório de {last} modelos preservado.',flush=True)
    while True:
        count=sum((d/'resultado.json').exists() for d in ROOT.iterdir() if d.is_dir())
        if count>last:
            archive(last);print(now(),f'{count}/13 concluídos: atualizando relatório.',flush=True)
            run_analysis()
            args=[sys.executable,str(CODE/'13-gerar-relatorio.py')]
            if count<13:args.append('--preliminary')
            subprocess.run(args,check=True)
            # Snapshot numérico ao lado da apresentação para consulta simples.
            for name in ['comparacao.json','comparacao.csv']:shutil.copy2(BASE/'resultados/comparacao'/name,OUT/name)
            (OUT/'estado-atualizacao.json').write_text(json.dumps(dict(updated_at=now(),completed=count,total=13,status='completo' if count==13 else 'preliminar'),indent=2),encoding='utf-8')
            last=count;print(now(),'Arquivos atualizados.',flush=True)
        if count==13:break
        time.sleep(50)
    print(now(),'Acompanhamento concluído, sem novas chamadas de inferência.',flush=True)
except Exception:
    traceback.print_exc()
    (OUT/'erro-atualizacao.txt').write_text(traceback.format_exc(),encoding='utf-8')
    raise
