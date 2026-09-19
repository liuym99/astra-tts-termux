from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
import urllib.request,urllib.parse,json,time,threading,os
UPSTREAM='http://127.0.0.1:5123'
MAX_INFLIGHT=int(os.environ.get('ASTRA_API_CONCURRENCY','1'))
QUEUE=threading.BoundedSemaphore(MAX_INFLIGHT)
HTTP=urllib.request.build_opener()
DEFAULT_SPEED=float(os.environ.get('ASTRA_DEFAULT_SPEED','1.4'))
class H(BaseHTTPRequestHandler):
 protocol_version='HTTP/1.1'
 def cors(self):
  self.send_header('Access-Control-Allow-Origin','*'); self.send_header('Access-Control-Allow-Headers','Content-Type'); self.send_header('Access-Control-Allow-Methods','POST,OPTIONS')
 def do_OPTIONS(self):
  self.send_response(204); self.cors(); self.send_header('Content-Length','0'); self.end_headers()
 def do_GET(self):
  if self.path!='/healthz': self.send_error(404); return
  b=json.dumps({'status':'ok','service':'astra-api','concurrency':MAX_INFLIGHT,'defaultSpeed':DEFAULT_SPEED}).encode()
  self.send_response(200); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(b))); self.cors(); self.end_headers(); self.wfile.write(b)
 def do_POST(self):
  if self.path!='/v1/speech': self.send_error(404); return
  started=time.monotonic()
  try:
   n=int(self.headers.get('Content-Length','0'))
   if n<=0 or n>1024*1024: raise ValueError('invalid body size')
   p=json.loads(self.rfile.read(n)); text=p.pop('text',None); stream=bool(p.pop('stream',False))
   if not isinstance(text,str) or not text.strip() or len(text)>10000: raise ValueError('text must be 1..10000 chars')
  except Exception as e:
   b=json.dumps({'error':str(e)}).encode(); self.send_response(400); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(b))); self.cors(); self.end_headers(); self.wfile.write(b); return
  p.setdefault('avatarId','cyrene'); p.setdefault('referenceId','default'); p.setdefault('speed',DEFAULT_SPEED); p.setdefault('languages',['zh','en'])
  if not QUEUE.acquire(timeout=5):
   b=b'{"error":"busy","message":"synthesis queue is full"}'; self.send_response(429); self.send_header('Content-Type','application/json'); self.send_header('Retry-After','3'); self.send_header('Content-Length',str(len(b))); self.cors(); self.end_headers(); self.wfile.write(b); return
  try:
   if stream:
    q=[('text',text)]
    for k,v in p.items(): q.extend((k,x) for x in v) if isinstance(v,list) else q.append((k,str(v)))
    req=urllib.request.Request(UPSTREAM+'/api/tts/predict-stream?'+urllib.parse.urlencode(q),method='GET')
   else:
    req=urllib.request.Request(UPSTREAM+'/api/tts/predict',data=json.dumps(dict(text=text,**p),ensure_ascii=False).encode(),headers={'Content-Type':'application/json'},method='POST')
   with HTTP.open(req,timeout=600) as up:
    self.send_response(up.status); self.send_header('Content-Type','audio/pcm' if stream else up.headers.get('Content-Type','audio/wav')); self.send_header('X-Audio-Sample-Rate',up.headers.get('X-Audio-Sample-Rate','32000')); self.send_header('X-Request-Elapsed-Ms',str(int((time.monotonic()-started)*1000)))
    if not stream and up.headers.get('Content-Length'): self.send_header('Content-Length',up.headers['Content-Length'])
    self.send_header('Connection','close'); self.cors(); self.end_headers()
    while True:
     block=up.read(65536)
     if not block: break
     self.wfile.write(block)
     if stream: self.wfile.flush()
  except (BrokenPipeError,ConnectionResetError): pass
  except Exception as e:
   try:
    b=json.dumps({'error':'upstream_failed','message':str(e)}).encode(); self.send_response(502); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(b))); self.cors(); self.end_headers(); self.wfile.write(b)
   except Exception: pass
  finally: QUEUE.release()
 def log_message(self,*args): pass
ThreadingHTTPServer(('0.0.0.0',5125),H).serve_forever()
