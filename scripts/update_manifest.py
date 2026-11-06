"""Hash the exact staged Git blobs; excludes this self-referential manifest."""
import hashlib,json,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
paths=subprocess.check_output(['git','ls-files','-z'],cwd=root).decode().split('\0');paths=[p for p in paths if p and p!='docs/distribution-manifest.json']
raw=subprocess.check_output(['git','cat-file','--batch'],cwd=root,input=('\n'.join(':'+p for p in paths)+'\n').encode());position=0;files=[]
for path in paths:
    end=raw.index(b'\n',position);fields=raw[position:end].split();assert fields[1]==b'blob';size=int(fields[2]);body=raw[end+1:end+1+size];position=end+size+2
    files.append({'path':path,'bytes':size,'sha256':hashlib.sha256(body).hexdigest()})
(root/'docs/distribution-manifest.json').write_text(json.dumps({'format':'git-index-blob-sha256-v1','scope':'Exact staged source and public data files; self excluded. No private profile, API credentials, hardware inventory or runtime logs.','files':files},ensure_ascii=False,indent=2),encoding='utf-8')
print('Manifest updated:',len(files),'Git blobs')
