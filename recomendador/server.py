"""Local-only HTTP interface for the deterministic static IR prototype."""
import argparse,json,traceback,threading,os
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse,parse_qs
from engine import Engine,PARAMS
ROOT=Path(__file__).resolve().parent
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--port',type=int,default=8765);args=ap.parse_args()
    print('Carregando vetores estáticos e índice...',flush=True);engine=Engine()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,format,*args):pass  # Do not log profile payloads or search terms.
        def send(self,obj,status=200):
            body=json.dumps(obj,ensure_ascii=False,allow_nan=False).encode('utf-8')
            self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(body)
        def allowed(self):
            hosts={f'127.0.0.1:{args.port}',f'localhost:{args.port}'}
            origin=self.headers.get('Origin')
            return self.headers.get('Host') in hosts and (not origin or origin in {'http://'+h for h in hosts})
        def do_GET(self):
            if not self.allowed():self.send(dict(error='Acesso somente local.'),403);return
            path=urlparse(self.path)
            try:
                if path.path in {'/laboratorio.html','/dataset.html'} or path.path.startswith('/lab/') or path.path=='/catalog.json':
                    rel=Path(path.path.lstrip('/'));target=(ROOT/'online'/rel).resolve()
                    if not target.is_relative_to((ROOT/'online').resolve()) or not target.is_file():self.send(dict(error='Não encontrado.'),404);return
                    body=target.read_bytes();self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8' if target.suffix=='.html' else 'application/json' if target.suffix=='.json' else 'text/javascript' if target.suffix=='.js' else 'text/css' if target.suffix=='.css' else 'application/octet-stream');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body);return
                if path.path=='/api/health':self.send(dict(ok=True,version=PARAMS['version']));return
                if path.path=='/api/config':self.send(dict(profile=engine.summary(),params=PARAMS,catalog_size=len(engine.base_keys)));return
                if path.path=='/api/import-status':self.send(engine.import_status);return
                if path.path=='/api/database':self.send(engine.repository.stats());return
                if path.path=='/api/dataset':self.send(engine.repository.dataset_report());return
                if path.path=='/api/popular':
                    seeds=json.loads((ROOT/'data/anilist-seed.json').read_text(encoding='utf-8'))
                    from engine import public
                    self.send([public(engine.media.get(engine.key_for(row),engine.materialize(row))) for row in seeds[:24]]);return
                if path.path=='/api/profile/export':self.send(dict(format='anirec-local-profile-v1',profile=engine.profile));return
                if path.path=='/api/tags':self.send(engine.client.taxonomy());return
                if path.path=='/api/search':
                    query=parse_qs(path.query);self.send(engine.search(query.get('q',[''])[0],query.get('online',['true'])[0]=='true'));return
                if path.path.startswith('/assets/'):
                    name=path.path.removeprefix('/assets/')
                    allowed={'ir-core.js','onboarding.js','app.js','app.css','local-adapter.js'}
                    if name not in allowed:self.send(dict(error='Asset não encontrado.'),404);return
                    content=(ROOT/'shared'/name).read_bytes();self.send_response(200);self.send_header('Content-Type','text/css; charset=utf-8' if name.endswith('.css') else 'text/javascript; charset=utf-8');self.send_header('Content-Length',str(len(content)));self.send_header('Cache-Control','no-cache');self.end_headers();self.wfile.write(content);return
                if path.path not in ['/','/index.html']:self.send(dict(error='Não encontrado.'),404);return
                content=(ROOT/'web/index.html').read_bytes();self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(content)));self.send_header('X-Content-Type-Options','nosniff');self.send_header('Referrer-Policy','no-referrer');self.end_headers();self.wfile.write(content)
            except (ValueError,RuntimeError,OSError) as error:self.send(dict(error=str(error)),400)
            except Exception:traceback.print_exc();self.send(dict(error='Erro interno. Consulte o log local, sem dados de perfil.'),500)
        def do_POST(self):
            if not self.allowed():self.send(dict(error='Origem não permitida.'),403);return
            if self.headers.get('Content-Type','').split(';')[0]!='application/json':self.send(dict(error='Use JSON.'),415);return
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 0<length<=65536:raise ValueError('Requisição fora do limite.')
                data=json.loads(self.rfile.read(length));path=urlparse(self.path).path
                if not isinstance(data,dict):raise ValueError('Objeto JSON esperado.')
                if path=='/api/discover-more':
                    with engine.lock:
                        anchor=engine.media.get(str(data.get('key','')))
                        if not anchor:raise ValueError('Pesquise a referência novamente.')
                        seen=engine.profile_signals()[2];count=0;added=[]
                        for genre in anchor.get('genres',[])[:2]:
                            excluded={m['anilist_id'] for m in engine.media.values() if m.get('anilist_id')}|{(entry.get('media') or {}).get('id') or entry.get('mediaId') for entry in engine.profile.get('entries',[]) if entry.get('status') in {'COMPLETED','CURRENT','REPEATING','PAUSED','DROPPED'}}
                            excluded.discard(None)
                            for row in engine.client.discover(genre,excluded):added.append(engine.add_anilist(row)['key']);count+=1
                        engine.discovery_extra[anchor['key']]=list(set(engine.discovery_extra.get(anchor['key'],[]))|set(added))
                        result=dict(added=count)
                elif path=='/api/profile/import':result=engine.import_profile(str(data.get('username','')).strip())
                elif path=='/api/profile/onboarding':result=engine.onboarding(data.get('preferred',[]),data.get('avoided',[]),data.get('favorite_keys',[]))
                elif path=='/api/profile/preferences':result=engine.preferences(data.get('preferred',[]),data.get('avoided',[]))
                elif path=='/api/profile/favorite':result=engine.favorite(str(data.get('key','')),data.get('add',True) is True)
                elif path=='/api/profile/reject':result=engine.reject(str(data.get('key','')),data.get('add',True) is True)
                elif path=='/api/profile/clear-import':result=engine.clear_import()
                elif path=='/api/recommend':result=engine.recommend(str(data.get('key','')),float(data.get('personalization',.35)),data.get('exclude_seen',False) is True,data.get('online',True) is True,data.get('require_genre',False) is True,data.get('exclude_upcoming',True) is True,data.get('require_tag_metadata',False) is True,float(data.get('personal_min_topics',.25)),pure=data.get('pure',False) is True)
                elif path=='/api/shutdown':
                    self.send(dict(ok=True));threading.Thread(target=server.shutdown,daemon=True).start();return
                else:self.send(dict(error='Não encontrado.'),404);return
                self.send(result)
            except (ValueError,RuntimeError,OSError,TypeError) as error:self.send(dict(error=str(error)),400)
            except Exception:traceback.print_exc();self.send(dict(error='Erro interno. Consulte o log local.'),500)
    server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    pid_file=engine.dir/'server.pid';pid_file.write_text(str(os.getpid()),encoding='ascii')
    print(f'Pronto: http://127.0.0.1:{args.port} | motor estático, sem treinamento ou LLM',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:
        server.server_close()
        if pid_file.exists() and pid_file.read_text().strip()==str(os.getpid()):pid_file.unlink()
if __name__=='__main__':main()
