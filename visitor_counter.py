#!/usr/bin/env python3
"""Contador agregado de sessões do Observatório, sem guardar IP ou user-agent."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
import hashlib
import json
import os
import re
import sqlite3
import time
from threading import Lock

DB = Path('/var/lib/observatorio-monitor/site-counter.sqlite3')
HOST, PORT = '127.0.0.1', 8767
ACTIVE_TTL = 60
ORIGINS = {'https://observatorio.leaomc.com', 'https://observatorio.lula.com.vc'}
TOKEN_RE = re.compile(r'^[a-f0-9-]{36}$')
DB_LOCK = Lock()


def db_conn():
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB, timeout=10)
    con.execute('PRAGMA busy_timeout=10000')
    return con


def init_db():
    con = db_conn()
    con.execute('PRAGMA journal_mode=WAL')
    con.execute('CREATE TABLE IF NOT EXISTS totals (key TEXT PRIMARY KEY, value INTEGER NOT NULL)')
    con.execute("INSERT OR IGNORE INTO totals VALUES ('visits', 0)")
    con.execute("INSERT OR IGNORE INTO totals VALUES ('peak', 0)")
    con.execute('CREATE TABLE IF NOT EXISTS seen_sessions (token_hash TEXT PRIMARY KEY)')
    con.execute('CREATE TABLE IF NOT EXISTS active_sessions (token_hash TEXT PRIMARY KEY, last_seen INTEGER NOT NULL)')
    con.commit()
    con.close()


class Handler(BaseHTTPRequestHandler):
    server_version = 'SiteCounter'

    def log_message(self, *_args):
        # Não registrar endereços IP nem tokens de sessão nos logs.
        pass

    def reply(self, status, payload):
        body = json.dumps(payload, separators=(',', ':')).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def totals(self):
        now = int(time.time())
        con = db_conn()
        con.execute('DELETE FROM active_sessions WHERE last_seen < ?', (now - ACTIVE_TTL,))
        visits = con.execute("SELECT value FROM totals WHERE key='visits'").fetchone()[0]
        active = con.execute('SELECT COUNT(*) FROM active_sessions').fetchone()[0]
        peak = con.execute("SELECT value FROM totals WHERE key='peak'").fetchone()[0]
        con.commit()
        con.close()
        return {'visits': visits, 'active': active, 'peak': peak, 'updated_at': now}

    def do_GET(self):
        if urlparse(self.path).path != '/api/site-counter':
            return self.reply(404, {'error': 'not_found'})
        with DB_LOCK:
            return self.reply(200, self.totals())

    def do_POST(self):
        if urlparse(self.path).path != '/api/site-counter':
            return self.reply(404, {'error': 'not_found'})
        if self.headers.get('Origin') not in ORIGINS:
            return self.reply(403, {'error': 'origin_not_allowed'})
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if size < 1 or size > 256:
                return self.reply(400, {'error': 'invalid_request'})
            data = json.loads(self.rfile.read(size))
            token = str(data.get('session', ''))
            if not TOKEN_RE.fullmatch(token):
                return self.reply(400, {'error': 'invalid_session'})
            with DB_LOCK:
                token_hash = hashlib.sha256(token.encode()).hexdigest()
                now = int(time.time())
                con = db_conn()
                con.execute('BEGIN IMMEDIATE')
                inserted = con.execute('INSERT OR IGNORE INTO seen_sessions(token_hash) VALUES (?)', (token_hash,)).rowcount
                if inserted:
                    con.execute("UPDATE totals SET value=value+1 WHERE key='visits'")
                con.execute('INSERT INTO active_sessions(token_hash,last_seen) VALUES(?,?) ON CONFLICT(token_hash) DO UPDATE SET last_seen=excluded.last_seen', (token_hash, now))
                con.execute('DELETE FROM active_sessions WHERE last_seen < ?', (now - ACTIVE_TTL,))
                visits = con.execute("SELECT value FROM totals WHERE key='visits'").fetchone()[0]
                active = con.execute('SELECT COUNT(*) FROM active_sessions').fetchone()[0]
                con.execute("UPDATE totals SET value=MAX(value, ?) WHERE key='peak'", (active,))
                peak = con.execute("SELECT value FROM totals WHERE key='peak'").fetchone()[0]
                con.commit()
                con.close()
            return self.reply(200, {'visits': visits, 'active': active, 'peak': peak, 'updated_at': now})
        except (ValueError, TypeError, json.JSONDecodeError):
            return self.reply(400, {'error': 'invalid_request'})
        except Exception:
            return self.reply(503, {'error': 'temporarily_unavailable'})


if __name__ == '__main__':
    init_db()
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
