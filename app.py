"""Servidor Python local. Execute: python3 app.py --port 8000"""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
import argparse
from build import build

ROOT = Path(__file__).resolve().parent
class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / 'dist'), **kwargs)
    def do_GET(self):
        if urlsplit(self.path).path == '/api/cases':
            self.path = '/cases.json'
        elif urlsplit(self.path).path == '/api/statements':
            self.path = '/statements.json'
        super().do_GET()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    build()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'Local: http://127.0.0.1:{args.port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
