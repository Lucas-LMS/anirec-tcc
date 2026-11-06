"""Testes funcionais locais de carregamento e API HTTP, sem avaliação Kaggle.

Um processo por vez, somente loopback, sem provedor externo. Raciocínio desligado
neste smoke test curto; isso não fixa a condição final do benchmark DeepSeek.
"""
import argparse
import ctypes
import ctypes.wintypes
import json
import pathlib
import socket
import subprocess
import time
import urllib.request

ROOT=pathlib.Path(__file__).resolve().parents[1]
LAB=pathlib.Path('C:/tcc-lab/LLMs')
MODELS={'qwen':'Qwen3-0.6B-Q8_0.gguf','llama':'Llama-3.2-1B-Instruct-Q4_K_M.gguf',
        'deepseek':'DeepSeek-R1-Distill-Qwen-1.5B-Q4_K_M.gguf'}

class Memory(ctypes.Structure):
    _fields_=[('cb',ctypes.wintypes.DWORD),('PageFaultCount',ctypes.wintypes.DWORD),
              ('PeakWorkingSetSize',ctypes.c_size_t),('WorkingSetSize',ctypes.c_size_t),
              ('QuotaPeakPagedPoolUsage',ctypes.c_size_t),('QuotaPagedPoolUsage',ctypes.c_size_t),
              ('QuotaPeakNonPagedPoolUsage',ctypes.c_size_t),('QuotaNonPagedPoolUsage',ctypes.c_size_t),
              ('PagefileUsage',ctypes.c_size_t),('PeakPagefileUsage',ctypes.c_size_t)]

def memory(process):
    value=Memory();value.cb=ctypes.sizeof(value)
    func=ctypes.windll.psapi.GetProcessMemoryInfo
    func.argtypes=[ctypes.wintypes.HANDLE,ctypes.POINTER(Memory),ctypes.wintypes.DWORD]
    if not func(ctypes.wintypes.HANDLE(int(process._handle)),ctypes.byref(value),value.cb):
        raise ctypes.WinError()
    return value.PeakWorkingSetSize

def request(url,payload=None):
    data=json.dumps(payload).encode() if payload is not None else None
    req=urllib.request.Request(url,data=data,headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=180) as response:return json.load(response)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--model',choices=list(MODELS),required=True)
    parser.add_argument('--official-qwen-sampling',action='store_true',help='Diagnóstico separado usando amostragem do README Qwen para modo sem thinking.')
    parser.add_argument('--reasoning-mode',choices=['off','on'],default='off')
    parser.add_argument('--max-tokens',type=int,default=64)
    args=parser.parse_args()
    if args.official_qwen_sampling and args.model!='qwen':raise ValueError('Opção específica do Qwen.')
    model=LAB/'models'/MODELS[args.model]
    assert model.exists(),f'Download ainda não concluído: {model}'
    variant='-official-sampling' if args.official_qwen_sampling else ''
    if args.reasoning_mode=='on':variant+='-thinking'
    target=ROOT/'resultados'/f'smoke-{args.model}{variant}.json'
    if target.exists():raise FileExistsError('Teste já registrado; preservar antes de repetir.')
    with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
    command=[str(LAB/'runtime-b12110/llama-server.exe'),'-m',str(model),'-c','2048','-t','4','-tb','4',
             '-ngl','0','-np','1','--host','127.0.0.1','--port',str(port),'--reasoning',args.reasoning_mode]
    log=ROOT/'logs'/f'server-{args.model}{variant}.log'
    started=time.perf_counter();output=log.open('wb')
    process=subprocess.Popen(command,stdout=output,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    result={'model':args.model,'command':command,'pid':process.pid,'purpose':'Verificação funcional, não avaliação comparativa.',
            'external_api_cost':0,'reasoning_mode':args.reasoning_mode,'max_tokens':args.max_tokens,
            'reasoning':'Condição funcional registrada; não é avaliação de classificação.'}
    try:
        while time.perf_counter()-started<180:
            if process.poll() is not None:raise RuntimeError(f'Servidor encerrou com {process.returncode}; consultar {log}')
            try:
                health=request(f'http://127.0.0.1:{port}/health')
                if health.get('status')=='ok':break
            except Exception:time.sleep(.3)
        else:raise TimeoutError('Servidor não ficou pronto em 180 s')
        result['load_seconds']=time.perf_counter()-started
        result['health']=health;result['requests']=[]
        for language,prompt in [('en','What is two plus two? Reply with just the number.'),('pt','Quanto é dois mais dois? Responda apenas o número.')]:
            payload={'model':args.model,'messages':[{'role':'user','content':prompt}],'max_tokens':args.max_tokens,
                     'temperature':.6,'top_p':.95,'seed':20261105,'stream':False}
            if args.official_qwen_sampling:
                thinking=args.reasoning_mode=='on'
                payload.update(temperature=.6 if thinking else .7,top_p=.95 if thinking else .8,
                               top_k=20,min_p=0,presence_penalty=1.5,
                               chat_template_kwargs={'enable_thinking':thinking})
            t=time.perf_counter();response=request(f'http://127.0.0.1:{port}/v1/chat/completions',payload)
            elapsed=time.perf_counter()-t
            content=response['choices'][0]['message'].get('content','')
            result['requests'].append({'language':language,'request':payload,'response':response,'wall_seconds':elapsed,
                                       'expected_number_present':'4' in content})
            assert isinstance(content,str) and content.strip(),'Resposta final vazia; verificar reasoning_content e finish_reason.'
            print(f'{args.model}/{language}: {content!r}; {elapsed:.2f} s',flush=True)
        result['peak_working_set_bytes']=memory(process)
        result['success']=True
    except Exception as error:
        result['success']=False;result['error']=f'{type(error).__name__}: {error}';raise
    finally:
        if process.poll() is None:
            process.terminate()
            try:process.wait(timeout=15)
            except subprocess.TimeoutExpired:process.kill();process.wait()
        output.close()
        target.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'{args.model}: testes funcionais concluídos; servidor encerrado.',flush=True)

if __name__=='__main__':main()
