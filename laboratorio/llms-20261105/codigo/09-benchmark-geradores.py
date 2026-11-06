"""Classificação zero-shot de SMS em LLM local ou GPT-OSS Groq Free.

Chave lida fora do projeto e nunca salva no log. Sem fallback de provedor.
Checkpoint por ID; não altera prompt ou parâmetros após as previsões.
"""
import argparse
import collections
import datetime
import json
import os
import pathlib
import re
import resource
import socket
import subprocess
import time
import urllib.error
import urllib.request

from benchmark_suporte import ROOT,OUT,SEED,read_data,prompt,label,write_json

FILES={'llama':'Llama-3.2-1B-Instruct-Q4_K_M.gguf','deepseek':'DeepSeek-R1-Distill-Qwen-1.5B-Q4_K_M.gguf',
       'qwen':'Qwen3-0.6B-Q8_0.gguf'}

def read_peak(pid):
    try:
        text=pathlib.Path(f'/proc/{pid}/status').read_text()
        return int(re.search(r'^VmHWM:\s+(\d+)',text,re.M)[1])
    except Exception:return None

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--model',choices=[*FILES,'gptoss'],required=True)
    args=parser.parse_args();target=OUT/args.model;target.mkdir(parents=True,exist_ok=True)
    if (target/'resultado.json').exists():print('Preservado:',args.model);return
    train,validation,test,common,freeze=read_data()
    remote=args.model=='gptoss';process=None;log=None;httpclient=None
    secret=None;api_model='openai/gpt-oss-20b' if remote else args.model
    request_times=collections.deque();total_tokens=0;call_count=0;headers_seen=[]
    if remote:
        import httpx
        httpclient=httpx.Client(timeout=180)
        secret_path=pathlib.Path('/mnt/c/tcc-lab/secrets/groq-api-key.txt')
        secret=os.environ.get('GROQ_API_KEY') or secret_path.read_text(encoding='utf-8-sig').strip()
        assert len(secret)>15,'Chave ausente ou arquivo vazio'
        url='https://api.groq.com/openai/v1/chat/completions'
        load_seconds=None;command=None
    else:
        with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
        url=f'http://127.0.0.1:{port}/v1/chat/completions'
        executable=pathlib.Path.home()/'tcc-lab/LLMs/runtime-b12110/llama-b12110/llama-server'
        weights=pathlib.Path('/mnt/c/tcc-lab/LLMs/models')/FILES[args.model]
        command=[str(executable),'-m',str(weights),'-c','2048','-t','4','-tb','4','-ngl','0','-np','1',
                 '--host','127.0.0.1','--port',str(port),'--reasoning','off' if args.model=='llama' else 'on']
        log=(target/'server.log').open('wb');started=time.perf_counter()
        process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
        while time.perf_counter()-started<180:
            if process.poll() is not None:raise RuntimeError('Servidor encerrou; consultar server.log')
            try:
                with urllib.request.urlopen(f'http://127.0.0.1:{port}/health',timeout=2) as response:
                    if json.load(response).get('status')=='ok':break
            except Exception:time.sleep(.3)
        else:raise TimeoutError('Servidor não ficou pronto')
        load_seconds=time.perf_counter()-started

    def invoke(text,index):
        nonlocal total_tokens,call_count
        payload={'model':api_model,'messages':[{'role':'user','content':prompt(text)}],
                 'temperature':.6,'top_p':.95,'seed':SEED+index,'stream':False}
        if remote:payload.update(max_completion_tokens=512,reasoning_effort='low')
        else:payload['max_tokens']=512
        if args.model=='qwen':payload.update(top_k=20,min_p=0,presence_penalty=1.5,chat_template_kwargs={'enable_thinking':True})
        reserve=len(prompt(text).encode())//2+512
        throttle=0.
        if remote:
            if call_count>=205 or total_tokens+reserve>150000:raise RuntimeError('Orçamento gratuito local esgotado; interrompido sem fallback.')
            now=time.monotonic()
            while request_times and now-request_times[0][0]>=60:request_times.popleft()
            # RPM e reserva conservadora de tokens; não confundir com latência de inferência.
            if request_times:
                throttle=max(0.,2.2-(now-request_times[-1][0]))
            if sum(x[1] for x in request_times)+reserve>7500:
                throttle=max(throttle,60.2-(now-request_times[0][0]))
            if throttle>0:time.sleep(throttle)
        req_headers={'Content-Type':'application/json'}
        if remote:req_headers['Authorization']='Bearer '+secret
        data=json.dumps(payload).encode();start=time.perf_counter();retry_wait=0.
        for attempt in range(3):
            try:
                if remote:
                    response=httpclient.post(url,json=payload,headers={**req_headers,'User-Agent':'AniRec-TCC/1.0'})
                    if response.status_code>=400:
                        raise urllib.error.HTTPError(url,response.status_code,'Erro remoto',response.headers,None)
                    result=response.json()
                    headers_seen.append({k:v for k,v in response.headers.items() if k.lower().startswith(('x-ratelimit','retry-after'))})
                else:
                    req=urllib.request.Request(url,data=data,headers=req_headers)
                    with urllib.request.urlopen(req,timeout=180) as response:result=json.load(response)
                break
            except urllib.error.HTTPError as error:
                if error.code==429 and attempt<2:
                    delay=float(error.headers.get('retry-after','20'))
                    if delay>60:raise RuntimeError('Limite remoto exige espera longa; estado preservado, sem fallback pago.')
                    time.sleep(delay);retry_wait+=delay
                else:raise RuntimeError(f'API HTTP {error.code}; execução interrompida sem exibir credenciais.') from None
        else:raise RuntimeError('API não retornou resposta')
        elapsed=time.perf_counter()-start
        usage=result.get('usage',{});used=int(usage.get('total_tokens',0));total_tokens+=used;call_count+=1
        if remote:request_times.append((time.monotonic(),used))
        choice=result['choices'][0];content=choice['message'].get('content') or ''
        return {'prediction':label(content),'content':content,'response':result,'request':payload,
                'wall_seconds':elapsed,'throttle_seconds':throttle,'retry_wait_seconds':retry_wait,
                'finish_reason':choice.get('finish_reason'),'usage':usage,
                'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}

    status={'model':args.model,'environment':'Groq Free remoto' if remote else 'Ubuntu/WSL2 CPU',
            'api_model':api_model,'load_seconds':load_seconds,'command':command,'threads':None if remote else 4,
            'max_completion_tokens':512,'dataset_sha256':freeze['files_sha256'],
            'inference_timing':'Uma chamada por SMS; inclui resposta completa e raciocínio. Espera preventiva por cota registrada separadamente.',
            'comparison_note':'Serviço remoto tem hardware/RAM desconhecidos; não comparar latência como efeito causal só da arquitetura.' if remote else 'GGUF quantizado, contexto 2048, quatro threads.'}
    start_total=time.perf_counter();records=[];raw=target/'requests.jsonl'
    if raw.exists():records=[json.loads(line) for line in raw.read_text(encoding='utf-8').splitlines()]
    done={x['id'] for x in records}
    # Recuperar orçamento já gasto caso haja retomada nesta mesma versão.
    if remote:total_tokens=sum(int(x.get('usage',{}).get('total_tokens',0)) for x in records);call_count=len(records)
    try:
        if not done:
            warm=invoke('Hello, I will see you at the library this afternoon.',-1)
            write_json(target/'warmup.json',warm)
        with raw.open('a',encoding='utf-8',buffering=1) as output:
            for index,row in enumerate(common):
                if row['id'] in done:continue
                result=invoke(row['text'],index);result['id']=row['id']
                output.write(json.dumps(result,ensure_ascii=False)+'\n');records.append(result)
                if len(records)%10==0:print(f'{args.model}: {len(records)}/{len(common)}; decorrido {time.perf_counter()-start_total:.1f} s',flush=True)
        assert len(records)==len(common) and len({x['id'] for x in records})==len(common)
        predictions=[{k:x[k] for k in ['id','prediction','wall_seconds','throttle_seconds','finish_reason','usage']} for x in records]
        status.update({'common_count':len(records),'total_stage_wall_seconds':time.perf_counter()-start_total,
                      'total_tokens_this_process':total_tokens,'api_calls_this_process':call_count,
                      'peak_rss_kib_server':None if remote else read_peak(process.pid),
                      'peak_rss_kib_client':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                      'remote_memory':None,'cost_policy':'Sem API paga; Groq Free conforme configuração do usuário.' if remote else 'Local sem cobrança por token.'})
        write_json(target/'predictions.json',predictions);write_json(target/'resultado.json',status)
        if remote:write_json(target/'rate-limit-headers.json',headers_seen)
        print(args.model,'concluído.',flush=True)
    finally:
        if process and process.poll() is None:
            process.terminate()
            try:process.wait(timeout=15)
            except subprocess.TimeoutExpired:process.kill();process.wait()
        if log:log.close()
        if httpclient:httpclient.close()

if __name__=='__main__':main()
