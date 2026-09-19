#!/usr/bin/env python3
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import json, os, shutil, time, uuid, urllib.parse
ROOT=Path(os.environ.get('ASTRA_CONVERT_HOME', str(Path.home() / 'astra-convert'))).expanduser(); JOBS=ROOT/'jobs'; JOBS.mkdir(parents=True,exist_ok=True)
ALLOWED=ROOT.resolve()

def inside(p):
    p=Path(p).resolve(); return p if p==ALLOWED or ALLOWED in p.parents else None
class H(BaseHTTPRequestHandler):
 def sendj(self,code,obj):
  b=json.dumps(obj,ensure_ascii=False).encode(); self.send_response(code); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Access-Control-Allow-Origin','*'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b)
 def do_OPTIONS(self): self.send_response(204); self.send_header('Access-Control-Allow-Origin','*'); self.send_header('Access-Control-Allow-Headers','Content-Type'); self.send_header('Access-Control-Allow-Methods','GET,POST,OPTIONS'); self.end_headers()
 def do_GET(self):
  u=urllib.parse.urlparse(self.path); q=urllib.parse.parse_qs(u.query)
  if u.path=='/converter/status':
   self.sendj(200,{'available':(ROOT/'v1_converter.py').is_file() and (ROOT/'templates').is_dir(),'root':str(ROOT)}); return
  if u.path=='/converter/job':
   jid=q.get('id',[''])[0]; job=JOBS/jid
   if not job.is_dir(): self.sendj(404,{'error':'job not found'}); return
   try: status=json.loads((job/'status.json').read_text())
   except: status={'status':'unknown'}
   events=[]
   if (job/'events.ndjson').is_file():
    for x in (job/'events.ndjson').read_text(errors='replace').splitlines()[-200:]:
     try: events.append(json.loads(x))
     except: pass
   self.sendj(200,dict(status,events=events)); return
  self.sendj(404,{'error':'not found'})
 def do_POST(self):
  n=int(self.headers.get('Content-Length','0')); data=json.loads(self.rfile.read(n) or b'{}')
  if self.path=='/converter/jobs':
   ck=inside(data.get('ckpt','')); pt=inside(data.get('pth','')); avatar=str(data.get('avatarId','')).strip()
   if not ck or not pt or not ck.is_file() or not pt.is_file() or not avatar or not avatar.replace('-','').replace('_','').isalnum(): self.sendj(400,{'error':'invalid input; files must be under ASTRA_CONVERT_HOME/inbox'}); return
   jid=time.strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:8]; job=JOBS/jid; job.mkdir()
   req={'ckpt':str(ck),'pth':str(pt),'avatarId':avatar,'simplify':bool(data.get('simplify')),'quantize':bool(data.get('quantize'))}
   (job/'request.json').write_text(json.dumps(req,ensure_ascii=False,indent=2)); (job/'status.json').write_text(json.dumps({'status':'queued','jobId':jid}))
   self.sendj(202,{'jobId':jid,'status':'queued'}); return
  if self.path=='/converter/import':
   jid=str(data.get('jobId','')); job=JOBS/jid; status=json.loads((job/'status.json').read_text()) if (job/'status.json').is_file() else {}
   if status.get('status')!='success': self.sendj(409,{'error':'job not successful'}); return
   req=json.loads((job/'request.json').read_text()); dst=Path(os.environ.get('ASTRA_TTS_HOME', str(Path.home() / 'tts-arm64'))) / 'resources' / 'models_v1' / req['avatarId']; dst.mkdir(parents=True,exist_ok=True)
   files=[]
   for p in (job/'result').glob('*.onnx'): shutil.copy2(p,dst/p.name); files.append(p.name)
   if len(files)<5: self.sendj(500,{'error':'incomplete result'}); return
   self.sendj(200,{'success':True,'target':str(dst),'files':files}); return
  self.sendj(404,{'error':'not found'})
 def log_message(self,*a): pass
ThreadingHTTPServer(('0.0.0.0',5126),H).serve_forever()
