"""Cliente didático para a API loopback. Não pode chamar provedor externo."""
import argparse
import json
import urllib.request

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--text',required=True)
parser.add_argument('--port',type=int,default=8088)
parser.add_argument('--max-tokens',type=int,default=512)
args=parser.parse_args()
assert 1<=args.port<=65535
payload={'messages':[{'role':'user','content':args.text}],
         'max_tokens':args.max_tokens,'temperature':.6,'top_p':.95,'stream':False}
request=urllib.request.Request(f'http://127.0.0.1:{args.port}/v1/chat/completions',
                               data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
with urllib.request.urlopen(request,timeout=180) as response:result=json.load(response)
print(json.dumps(result,ensure_ascii=False,indent=2))
