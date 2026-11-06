"""Aquisição gratuita e verificável de runtime Windows, GGUF e dataset Kaggle.

Somente HTTP público. Não usa APIs de inferência, chaves ou cobrança.
Revisões fixadas; pesos fora do OneDrive. Hash esperado vem do LFS do publicador
da conversão: não é prova de igualdade com pesos originais em outra precisão.
"""
import concurrent.futures
import hashlib
import json
import pathlib
import time
import urllib.request
import zipfile

ROOT=pathlib.Path(__file__).resolve().parents[1]
DEST=pathlib.Path('C:/tcc-lab/LLMs')
for p in [DEST/'downloads',DEST/'models',ROOT/'fontes',ROOT/'logs',ROOT/'dados/brutos',ROOT/'resultados']:
    p.mkdir(parents=True,exist_ok=True)
MODELS=[
 {'key':'llama','repo':'bartowski/Llama-3.2-1B-Instruct-GGUF','revision':'067b946cf014b7c697f3654f621d577a3e3afd1c','file':'Llama-3.2-1B-Instruct-Q4_K_M.gguf','original':'meta-llama/Llama-3.2-1B-Instruct','provenance':'Conversão comunitária Bartowski; licença Llama 3.2'},
 {'key':'deepseek','repo':'bartowski/DeepSeek-R1-Distill-Qwen-1.5B-GGUF','revision':'9cc28b17e86fa2415fcb070f8ee5ec27c965aa61','file':'DeepSeek-R1-Distill-Qwen-1.5B-Q4_K_M.gguf','original':'deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B','provenance':'Conversão comunitária Bartowski; modelo destilado baseado em Qwen'},
 {'key':'qwen','repo':'Qwen/Qwen3-0.6B-GGUF','revision':'23749fefcc72300e3a2ad315e1317431b06b590a','file':'Qwen3-0.6B-Q8_0.gguf','original':'Qwen/Qwen3-0.6B','provenance':'GGUF publicado pela organização Qwen; Apache 2.0'},
]

def get(url):
    request=urllib.request.Request(url,headers={'User-Agent':'AniRec-TCC-documentation/1.0'})
    return urllib.request.urlopen(request,timeout=120)

def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def fetch(url,path,expected=None):
    if path.exists() and (expected is None or sha(path)==expected):
        print('Preservado:',path.name,flush=True);return
    part=path.with_suffix(path.suffix+'.part')
    for attempt in range(3):
        try:
            with get(url) as response,part.open('wb') as output:
                size=0;reported=time.monotonic()
                while block:=response.read(1024*1024):
                    output.write(block);size+=len(block)
                    if time.monotonic()-reported>12:
                        print(f'{path.name}: {size/1024/1024:.0f} MiB recebidos',flush=True);reported=time.monotonic()
            if expected and sha(part)!=expected:raise ValueError(f'Hash divergente: {path.name}')
            part.replace(path)
            print('Concluído:',path.name,path.stat().st_size,flush=True);return
        except Exception as error:
            print(f'Tentativa {attempt+1} falhou para {path.name}: {type(error).__name__}: {error}',flush=True)
            if attempt==2:raise

def acquire_model(entry):
    info=json.load(get(f"https://huggingface.co/api/models/{entry['repo']}/revision/{entry['revision']}?blobs=true"))
    (ROOT/'fontes'/f"{entry['key']}-metadata.json").write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
    file=next(x for x in info['siblings'] if x['rfilename']==entry['file'])
    expected=file['lfs']['sha256']
    target=DEST/'models'/entry['file']
    url=f"https://huggingface.co/{entry['repo']}/resolve/{entry['revision']}/{entry['file']}"
    fetch(url,target,expected)
    for item in ['README.md','LICENSE']:
        if any(x['rfilename']==item for x in info['siblings']):
            fetch(f"https://huggingface.co/{entry['repo']}/resolve/{entry['revision']}/{item}",ROOT/'fontes'/f"{entry['key']}-{item}")
    entry.update(path=str(target),bytes=target.stat().st_size,sha256=expected,url=url)
    return entry

def main():
    runtime_url='https://github.com/ggml-org/llama.cpp/releases/download/b12110/llama-b12110-bin-win-cpu-x64.zip'
    runtime_sha='98901e327c252875accaf2d1bf364e10e868843b0b63468baad1aa945cdc5da2'
    archive=DEST/'downloads/llama-b12110-bin-win-cpu-x64.zip'
    fetch(runtime_url,archive,runtime_sha)
    runtime=DEST/'runtime-b12110';runtime.mkdir(exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for n in z.namelist():
            resolved=(runtime/n).resolve()
            assert resolved.is_relative_to(runtime.resolve()),n
        z.extractall(runtime)
    (ROOT/'fontes/runtime-release.json').write_text(json.dumps(json.load(get('https://api.github.com/repos/ggml-org/llama.cpp/releases/tags/b12110')),indent=2),encoding='utf-8')
    fetch('https://raw.githubusercontent.com/ggml-org/llama.cpp/cd959bae99ff4bed22bef2604f45241c09bbb8c8/LICENSE',ROOT/'fontes/llama-cpp-LICENSE.txt')
    kg_url='https://www.kaggle.com/api/v1/datasets/download/uciml/sms-spam-collection-dataset'
    kg=ROOT/'dados/brutos/sms-spam-collection-kaggle.zip'
    fetch(kg_url,kg)
    with zipfile.ZipFile(kg) as z:
        assert z.testzip() is None
        assert 'spam.csv' in z.namelist()
        with (ROOT/'dados/brutos/spam.csv').open('wb') as f:f.write(z.read('spam.csv'))
    (ROOT/'fontes/kaggle-listagem.json').write_text(json.dumps(json.load(get('https://www.kaggle.com/api/v1/datasets/list?search=sms-spam-collection-dataset')),indent=2),encoding='utf-8')
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        entries=list(pool.map(acquire_model,MODELS))
    manifest={'date':'2026-11-05','cost':'Sem cobrança de API; execução local consome recursos e energia da máquina.',
              'runtime':{'tag':'b12110','commit':'cd959bae99ff4bed22bef2604f45241c09bbb8c8','url':runtime_url,'sha256':runtime_sha,'path':str(runtime)},
              'models':entries,'dataset':{'source':kg_url,'zip_sha256':sha(kg),'csv_sha256':sha(ROOT/'dados/brutos/spam.csv'),'zip_bytes':kg.stat().st_size}}
    (ROOT/'resultados/instalacao.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Manifesto de instalação salvo.',flush=True)

if __name__=='__main__':main()
