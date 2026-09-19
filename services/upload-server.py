#!/usr/bin/env python3
import json, os, re, shutil, tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

ROOT = os.path.dirname(os.path.abspath(__file__))
MAX_FILE = 2 * 1024 * 1024 * 1024
MODEL_FILES = {
    'prompt_encoder.onnx', 't2s_encoder.onnx',
    't2s_first_stage_decoder.onnx', 't2s_stage_decoder.onnx', 'vits.onnx'
}

def safe_id(value):
    return bool(re.fullmatch(r'[A-Za-z0-9_-]{1,80}', value or ''))

def send_json(handler, code, payload):
    data = json.dumps(payload, ensure_ascii=False).encode()
    handler.send_response(code)
    handler.send_header('Content-Type', 'application/json; charset=utf-8')
    handler.send_header('Access-Control-Allow-Origin', '*')
    handler.send_header('Content-Length', str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)

class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != '/upload/v1':
            send_json(self, 404, {'error': 'not found'})
            return
        query = parse_qs(parsed.query)
        avatar = query.get('avatarId', [''])[0]
        filename = os.path.basename(query.get('filename', [''])[0])
        kind = query.get('kind', ['model'])[0]
        if not safe_id(avatar):
            send_json(self, 400, {'error': 'invalid avatarId'})
            return
        if kind == 'model':
            if filename not in MODEL_FILES or not filename.endswith('.onnx'):
                send_json(self, 400, {'error': 'invalid model filename'})
            target_dir = os.path.join(ROOT, 'resources', 'models_v1', avatar)
        elif kind == 'reference':
            if not re.fullmatch(r'[A-Za-z0-9_.-]{1,160}', filename) or not filename.lower().endswith('.wav'):
                send_json(self, 400, {'error': 'invalid wav filename'})
            target_dir = os.path.join(ROOT, 'resources', 'avatars', avatar, 'references')
        else:
            send_json(self, 400, {'error': 'invalid kind'})
            return
        try:
            length = int(self.headers.get('Content-Length', '-1'))
        except ValueError:
            length = -1
        if length < 1 or length > MAX_FILE:
            send_json(self, 413, {'error': 'file too large or missing length'})
            return
        os.makedirs(target_dir, exist_ok=True)
        target = os.path.join(target_dir, filename)
        fd, temp = tempfile.mkstemp(prefix='.upload-', dir=target_dir)
        try:
            remaining = length
            with os.fdopen(fd, 'wb') as out:
                while remaining:
                    chunk = self.rfile.read(min(1024 * 1024, remaining))
                    if not chunk:
                        raise RuntimeError('incomplete upload')
                    out.write(chunk)
                    remaining -= len(chunk)
            os.replace(temp, target)
            send_json(self, 200, {'ok': True, 'filename': filename, 'path': target})
        except Exception as exc:
            try: os.unlink(temp)
            except OSError: pass
            send_json(self, 400, {'error': str(exc)})

    def log_message(self, fmt, *args):
        print('[upload]', fmt % args, flush=True)

if __name__ == '__main__':
    print('V1 upload server listening on 0.0.0.0:5124', flush=True)
    ThreadingHTTPServer(('0.0.0.0', 5124), Handler).serve_forever()
