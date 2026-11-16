"""Loopback-only UI; no uploads to third parties, no filesystem discovery."""
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from .core import analyze, bundle, compare, verify_bundle, InputError, MAX_BYTES, strict_loads
ROOT=Path(__file__).resolve().parent.parent

class LocalServer(ThreadingHTTPServer):
    daemon_threads=True
    request_queue_size=8
    def __init__(self,*args):
        self.slots=threading.BoundedSemaphore(4)
        super().__init__(*args)
    def process_request(self,request,address):
        if not self.slots.acquire(blocking=False):
            try: request.sendall(b'HTTP/1.1 503 Service Unavailable\r\nContent-Length: 0\r\nConnection: close\r\n\r\n')
            except OSError: pass
            self.shutdown_request(request)
            return
        try: super().process_request(request,address)
        except Exception:
            self.slots.release();raise
    def process_request_thread(self,request,address):
        try: super().process_request_thread(request,address)
        finally: self.slots.release()

class Handler(BaseHTTPRequestHandler):
    def setup(self):
        super().setup()
        self.connection.settimeout(15)

    def log_message(self,*args): pass # Never log transcript bodies, URLs, or local filenames.
    def authorized(self):
        allowed={f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'}
        host=self.headers.get('Host','')
        origin=self.headers.get('Origin')
        return host in allowed and (not origin or origin in {'http://'+h for h in allowed}) and self.headers.get('Sec-Fetch-Site','same-origin') not in {'cross-site'}
    def send(self,status,body,ctype='application/json; charset=utf-8'):
        if not isinstance(body,bytes): body=json.dumps(body).encode()
        self.send_response(status)
        self.send_header('Content-Type',ctype);self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; object-src 'none'; frame-ancestors 'none'; base-uri 'none'")
        try:
            self.end_headers();self.wfile.write(body)
        except (BrokenPipeError,ConnectionResetError):
            pass # A local browser/navigation may cancel an in-flight response.
    def do_GET(self):
        if not self.authorized(): return self.send(403,{'error':'Only this loopback origin is allowed.'})
        path=urlsplit(self.path).path
        if path=='/api/demo':
            data=ROOT/'examples'/'claude-structural.jsonl'
            if not data.exists(): return self.send(404,{'error':'Demo is not installed.'})
            return self.send(200,dict(text=data.read_text(),format='claude',label='Real-session structure · Entire MIT fixture',provenance='Allowlist-projected from Entire’s upstream real Claude session. All prose and arguments removed; 349 records, 92 tools, 5 explicit tool failures. See docs/PROVENANCE.md.'))
        paths={'/':'index.html','/index.html':'index.html','/app.js':'app.js','/style.css':'style.css','/styles.css':'styles.css'}
        if path not in paths: return self.send(404,{'error':'Not found.'})
        file=ROOT/'web'/paths[path]
        if not file.is_file(): return self.send(404,{'error':'Asset unavailable.'})
        ctype={'html':'text/html; charset=utf-8','js':'text/javascript; charset=utf-8','css':'text/css; charset=utf-8'}[file.suffix[1:]]
        self.send(200,file.read_bytes(),ctype)
    def do_POST(self):
        if not self.authorized(): return self.send(403,{'error':'Only this loopback origin is allowed.'})
        if self.headers.get('Content-Type','').split(';')[0]!='application/json': return self.send(415,{'error':'Use application/json.'})
        try:
            size=int(self.headers.get('Content-Length','0'))
            if size<1 or size>MAX_BYTES: return self.send(413,{'error':'Request must be 1 byte to 16 MiB.'})
            self.connection.settimeout(15)
            data=strict_loads(self.rfile.read(size).decode('utf-8'))
            if not isinstance(data,dict): raise InputError('Expected a JSON object.')
            path=urlsplit(self.path).path
            if path=='/api/analyze': result=analyze(data.get('text'),data.get('format','auto'))
            elif path=='/api/bundle': result=bundle(data.get('text'),data.get('format','auto'),data.get('focus'))
            elif path=='/api/compare': result=compare(data.get('before'),data.get('after'))
            elif path=='/api/verify': result=verify_bundle(data)
            else: return self.send(404,{'error':'Unknown endpoint.'})
            self.send(200,result)
        except (ValueError,UnicodeError,TypeError,KeyError,RecursionError): self.send(400,{'error':'Invalid input. Use valid JSONL in a supported format, within the size limit.'})
        except (TimeoutError,ConnectionError,OSError): return

def serve(port=8765):
    if not 1<=port<=65535: raise InputError('Port must be between 1 and 65535.')
    server=LocalServer(('127.0.0.1',port),Handler)
    print(f'Agent Incident Lab: http://127.0.0.1:{port} · local only · Ctrl+C to stop',flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
