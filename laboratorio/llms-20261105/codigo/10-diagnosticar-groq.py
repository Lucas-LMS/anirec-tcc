"""Diagnóstico de transporte sem expor chave. Uma frase sintética, fora do teste."""
import json
import pathlib
import httpx
from benchmark_suporte import ROOT,OUT

secret=pathlib.Path('/mnt/c/tcc-lab/secrets/groq-api-key.txt').read_text(encoding='utf-8-sig').strip()
payload={'model':'openai/gpt-oss-20b','messages':[{'role':'user','content':'Reply with one word: ready'}],
         'max_completion_tokens':128,'reasoning_effort':'low'}
with httpx.Client(timeout=90) as client:
    response=client.post('https://api.groq.com/openai/v1/chat/completions',
                         headers={'Authorization':'Bearer '+secret,'User-Agent':'AniRec-TCC/1.0'},json=payload)
safe=response.text.replace(secret,'[REMOVIDO]')
print('HTTP',response.status_code)
if response.status_code==200:
    data=response.json();print('Resposta válida; tokens:',data.get('usage',{}).get('total_tokens'))
else:print(safe[:1500])
target=OUT/'gptoss/diagnostico-transporte.json';target.parent.mkdir(parents=True,exist_ok=True)
target.write_text(json.dumps({'status':response.status_code,'response':json.loads(safe) if safe.startswith('{') else safe[:1500]},ensure_ascii=False,indent=2),encoding='utf-8')
