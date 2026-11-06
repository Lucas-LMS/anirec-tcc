"""Listwise English reranking. Checkpoints, context audit and Free-only guard."""
import argparse,collections,datetime,hashlib,json,os,re,resource,socket,subprocess,time,urllib.request,urllib.error
from pathlib import Path
from support import DATA,OUT,SEED,read,load,save,parse,prompt
FILES={'llama':'Llama-3.2-1B-Instruct-Q4_K_M.gguf','deepseek':'DeepSeek-R1-Distill-Qwen-1.5B-Q4_K_M.gguf','qwen':'Qwen3-0.6B-Q8_0.gguf','qwen-nothink':'Qwen3-0.6B-Q8_0.gguf'}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--model',required=True,choices=[*FILES,'gptoss']);args=ap.parse_args()
    target=OUT/'reranking'/args.model;target.mkdir(parents=True,exist_ok=True)
    if (target/'result.json').exists():print('Preserved:',args.model);return
    catalog,queries,freeze=read();shortlists=load(DATA/'shortlists.json')
    assert hashlib.sha256((DATA/'shortlists.json').read_bytes()).hexdigest()==load(DATA/'shortlists-freeze.json')['sha256']
    remote=args.model=='gptoss';process=None;log=None;client=None;command=None;load_seconds=None
    api_model='openai/gpt-oss-20b' if remote else args.model
    raw=target/'requests.jsonl';records=[json.loads(l) for l in raw.read_text(encoding='utf-8').splitlines()] if raw.exists() else []
    done={r['id'] for r in records};used=sum(r.get('usage',{}).get('total_tokens',0) for r in records);calls=len(records);window=collections.deque()
    known_sms=0
    if remote:
        import httpx
        client=httpx.Client(timeout=180)
        key=os.environ.get('GROQ_API_KEY') or Path('/mnt/c/tcc-lab/secrets/groq-api-key.txt').read_text(encoding='utf-8-sig').strip()
        url='https://api.groq.com/openai/v1/chat/completions'
        sms=Path(__file__).resolve().parents[2]/'llms-20261105/resultados/benchmark-v1/gptoss/resultado.json'
        known_sms=load(sms).get('total_tokens_this_process',0)
    else:
        with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
        url=f'http://127.0.0.1:{port}/v1/chat/completions'
        command=[str(Path.home()/'tcc-lab/LLMs/runtime-b12110/llama-b12110/llama-server'),'-m',str(Path('/mnt/c/tcc-lab/LLMs/models')/FILES[args.model]),'-c','2048','-t','4','-tb','4','-ngl','0','-np','1','--host','127.0.0.1','--port',str(port),'--reasoning','off' if args.model in ['llama','qwen-nothink'] else 'on']
        log=(target/'server.log').open('wb');started=time.perf_counter();process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
        while time.perf_counter()-started<180:
            if process.poll() is not None:raise RuntimeError('Server stopped; inspect log.')
            try:
                with urllib.request.urlopen(f'http://127.0.0.1:{port}/health',timeout=2) as r:
                    if json.load(r).get('status')=='ok':break
            except Exception:time.sleep(.3)
        else:process.terminate();raise TimeoutError('Server startup timeout.')
        load_seconds=time.perf_counter()-started
    def localpost(endpoint,payload):
        req=urllib.request.Request(f'http://127.0.0.1:{port}'+endpoint,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(req,timeout=180) as response:return json.load(response)
    def invoke(text,index):
        nonlocal calls,used
        payload=dict(model=api_model,messages=[dict(role='user',content=text)],temperature=.7 if args.model=='qwen-nothink' else .6,top_p=.8 if args.model=='qwen-nothink' else .95,seed=SEED+index,stream=False)
        if remote:payload.update(max_completion_tokens=512,reasoning_effort='low')
        else:payload['max_tokens']=512
        if args.model.startswith('qwen'):payload.update(top_k=20,min_p=0,presence_penalty=1.5,chat_template_kwargs=dict(enable_thinking=args.model=='qwen'))
        throttle=0.;reserve=len(text.encode())//2+512
        if remote:
            if calls>=30 or used+reserve>80000 or known_sms+used+reserve>180000:raise RuntimeError('Known Free budget guard reached; no paid fallback.')
            now=time.monotonic()
            while window and now-window[0][0]>=60:window.popleft()
            if window:throttle=max(0,2.2-(now-window[-1][0]))
            if sum(x[1] for x in window)+reserve>7500:throttle=max(throttle,60.2-(now-window[0][0]))
            if throttle>0:time.sleep(throttle)
        start=time.perf_counter();retry_wait=0
        for attempt in range(3):
            if remote:
                response=client.post(url,json=payload,headers={'Authorization':'Bearer '+key,'User-Agent':'AniRec-TCC/1.0'})
                if response.status_code==429 and attempt<2:
                    delay=float(response.headers.get('retry-after','20'))
                    if delay>60:raise RuntimeError('Long quota wait; checkpoint preserved.')
                    time.sleep(delay);retry_wait+=delay;continue
                if response.status_code>=400:raise RuntimeError(f'Groq HTTP {response.status_code}; no paid fallback.')
                result=response.json()
            else:result=localpost('/v1/chat/completions',payload)
            break
        else:raise RuntimeError('Quota retries exhausted.')
        elapsed=time.perf_counter()-start;usage=result.get('usage',{});used+=usage.get('total_tokens',0);calls+=1
        if remote:window.append((time.monotonic(),usage.get('total_tokens',0)))
        choice=result['choices'][0];content=choice['message'].get('content') or ''
        return dict(prediction=parse(content),content=content,response=result,request=payload,wall_seconds=elapsed,throttle_seconds=throttle,retry_wait_seconds=retry_wait,usage=usage,finish_reason=choice.get('finish_reason'),timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    stage=time.perf_counter()
    try:
        # Audit the rendered local chat templates BEFORE test predictions.
        if not remote:
            counts=[]
            for row in shortlists:
                rendered=localpost('/apply-template',dict(messages=[dict(role='user',content=row['prompt'])],chat_template_kwargs=dict(enable_thinking=args.model=='qwen')))['prompt']
                n=len(localpost('/tokenize',dict(content=rendered,add_special=False,parse_special=True))['tokens']);counts.append(dict(id=row['id'],prompt_tokens=n))
            save(target/'context-audit.json',dict(context=2048,output_budget=512,extra_margin=32,counts=counts))
            assert max(x['prompt_tokens'] for x in counts)+512+32<=2048,'Prompt exceeds fixed context: stop before predictions.'
        if not records:
            warm=prompt('Recommend a funny story.',[dict(id=c,synopsis='A humorous adventure with friends.' if c=='A' else 'A serious historical investigation.') for c in 'ABCDE'])
            save(target/'warmup.json',invoke(warm,-1))
        with raw.open('a',encoding='utf-8',buffering=1) as f:
            for index,row in enumerate(shortlists):
                if row['id'] in done:continue
                answer=invoke(row['prompt'],index);answer['id']=row['id'];f.write(json.dumps(answer,ensure_ascii=False)+'\n');records.append(answer)
                print(args.model,len(records),'/',len(shortlists),flush=True)
        assert len(records)==24 and len({r['id'] for r in records})==24
        rss=None
        if process:
            match=re.search(r'^VmHWM:\s+(\d+)',Path(f'/proc/{process.pid}/status').read_text(),re.M);rss=int(match[1]) if match else None
        save(target/'predictions.json',[{k:r[k] for k in ['id','prediction','wall_seconds','throttle_seconds','finish_reason','usage']} for r in records])
        save(target/'result.json',dict(model=args.model,environment='Groq Free remote' if remote else 'Ubuntu WSL2 CPU',command=command,load_seconds=load_seconds,total_stage_wall_seconds=time.perf_counter()-stage,total_tokens_this_process=used,api_calls_this_process=calls,known_sms_tokens=known_sms,peak_rss_kib_server=rss,remote_memory=None,shortlist_sha256=load(DATA/'shortlists-freeze.json')['sha256'],dataset_sha256=freeze['files_sha256'],context=2048 if not remote else None,max_output_tokens=512,threads=4 if not remote else None,ttft_measured=False))
        print(args.model,'completed.',flush=True)
    finally:
        if process and process.poll() is None:
            process.terminate()
            try:process.wait(timeout=15)
            except subprocess.TimeoutExpired:process.kill();process.wait()
        if log:log.close()
        if client:client.close()
if __name__=='__main__':main()
