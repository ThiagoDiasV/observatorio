#!/usr/bin/env python3
"""Painel local para revisão, rascunhos e preparação editorial sem publicação."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from editorial_pipeline import validate

HTML = r'''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Revisão editorial · Lula Presidente</title>
<style>body{margin:0;background:#080e17;color:#e7f1f4;font:15px system-ui,sans-serif}main{max-width:1080px;margin:auto;padding:38px 22px}h1,h2{margin:0}header,p{color:#aebfc7}.meta,.actions{display:flex;gap:9px;flex-wrap:wrap;margin:18px 0}.chip{border:1px solid #365061;border-radius:20px;padding:6px 10px;font-size:12px}.card{background:#111c29;border:1px solid #273d4a;border-radius:12px;padding:20px;margin:14px 0}.card h2{font-size:19px;margin:8px 0}.high{color:#ffb4bd}.normal{color:#7bf5c8}.source{color:#83d7ff}button{border:0;border-radius:7px;padding:9px 12px;font-weight:700;cursor:pointer}.approve{background:#7bf5c8;color:#06231b}.reject{background:#f08495;color:#2a080d}.review{background:#37495d;color:#fff}.ready{background:#f5cf75;color:#342300}textarea,input,select{width:100%;min-height:36px;margin:7px 0;background:#0a111b;color:#e7f1f4;border:1px solid #365061;border-radius:7px;padding:8px;box-sizing:border-box}textarea{min-height:76px}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.decision{color:#f5cf75;font-size:13px}.editor{margin-top:18px;padding-top:14px;border-top:1px solid #273d4a}.notice{border-left:3px solid #f5cf75;padding-left:12px}</style>
<main><header><h1>Revisão editorial</h1><p>Pesquisa, decisão, rascunho e preparação ficam separados. Esta tela nunca altera o site público.</p></header><div id="meta" class="meta"></div><section id="items"></section></main>
<script>
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const value=(id)=>document.querySelector('#'+CSS.escape(id)).value.trim();
function editor(i,d){d=d||{};const r=d.record||{};return `<div class="editor"><h2>Rascunho editorial</h2><p class="notice">Complete e confira cada campo na fonte. “Pronto” somente prepara um changeset privado; ainda não publica.</p><div class="grid"><label>Tipo<select id="kind-${i.id}"><option value="case" ${r.kind==='case'?'selected':''}>Caso/processo</option><option value="speech" ${r.kind==='speech'?'selected':''}>Fala pública</option></select></label><label>Data<input id="date-${i.id}" value="${esc(r.date||'')}"></label><label>Pessoas, separadas por vírgula<input id="people-${i.id}" value="${esc((r.people||[]).join(', '))}"></label><label>Tema<input id="theme-${i.id}" value="${esc(r.theme||'')}"></label><label>Status processual/registro<input id="status-${i.id}" value="${esc(r.status||'')}"></label><label>Grupo<input id="group-${i.id}" value="${esc(r.group||'Registro em apuração')}"></label></div><label>Título<input id="title-${i.id}" value="${esc(r.title||i.title)}"></label><label>Resumo<textarea id="summary-${i.id}">${esc(r.summary||i.summary||'')}</textarea></label><label>Desfecho / situação atual<textarea id="outcome-${i.id}">${esc(r.outcome||'')}</textarea></label><label>Resposta / posição documentada<textarea id="response-${i.id}">${esc(r.response||'')}</textarea></label><div class="grid"><label>Rótulo da fonte<input id="label-${i.id}" value="${esc((r.source||{}).label||i.source.name)}"></label><label>URL HTTPS da fonte<input id="url-${i.id}" value="${esc((r.source||{}).url||i.source.url)}"></label></div><div class="actions"><button class="review" onclick="saveDraft('${i.id}')">Salvar rascunho</button><button class="ready" onclick="readyDraft('${i.id}')">Marcar pronto para preparação</button></div>${d.validation?`<p class="decision">${esc(d.validation.join(' · '))}</p>`:''}</div>`}
async function decide(id,action){const note=prompt(action==='approved'?'Justificativa editorial para aprovar:':action==='rejected'?'Justificativa editorial para rejeitar:':'Observação (opcional):')||'';if((action==='approved'||action==='rejected')&&!note.trim())return;const res=await fetch('/api/decision',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id,action,note})});if(!res.ok)alert('Não foi possível registrar a decisão.');load()}
function record(id){return {kind:value('kind-'+id),title:value('title-'+id),people:value('people-'+id).split(',').map(x=>x.trim()).filter(Boolean),theme:value('theme-'+id),date:value('date-'+id),status:value('status-'+id),group:value('group-'+id),summary:value('summary-'+id),outcome:value('outcome-'+id),response:value('response-'+id),source:{label:value('label-'+id),url:value('url-'+id)}}}
async function saveDraft(id){const res=await fetch('/api/draft',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id,record:record(id)})});if(!res.ok)alert('Não foi possível salvar o rascunho.');load()}
async function readyDraft(id){await saveDraft(id);const res=await fetch('/api/draft/ready',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});const data=await res.json();if(!res.ok)alert((data.error||'Rascunho incompleto.'));load()}
async function load(){const data=await fetch('/api/items',{cache:'no-store'}).then(r=>r.json());document.querySelector('#meta').innerHTML=`<span class="chip">${data.count} candidatos</span><span class="chip">${data.pending} aguardando revisão</span><span class="chip">${data.ready} prontos para preparação</span><span class="chip">Falhas de fonte: ${data.failures}</span><span class="chip">Alertas: ${data.alerts.length}</span>`;const el=document.querySelector('#items');el.innerHTML=data.items.length?data.items.map(i=>{const d=data.drafts[i.id];return `<article class="card"><div class="${i.risk}">PRIORIDADE ${esc(i.risk).toUpperCase()} · ${esc(i.status)}</div><h2>${esc(i.title)}</h2><p>${esc(i.summary||'Sem resumo no feed.')}</p><p><a class="source" href="${esc(i.source.url)}" target="_blank" rel="noopener">${esc(i.source.name)} ↗</a> · temas: ${esc((i.themes||[]).join(', '))}</p>${i.decision?`<p class="decision">Decisão: ${esc(i.decision.action)} · ${esc(i.decision.note||'sem observação')}</p>`:''}<div class="actions"><button class="approve" onclick="decide('${i.id}','approved')">Aprovar para rascunho</button><button class="reject" onclick="decide('${i.id}','rejected')">Rejeitar</button><button class="review" onclick="decide('${i.id}','needs_review')">Manter em revisão</button></div>${i.status==='approved'||d?editor(i,d):''}</article>`}).join(''):'<p>Nenhum candidato encontrado.</p>'}
load();</script>'''


class ReviewStore:
    def __init__(self, root: Path):
        self.root, self.inbox = root, root / "automation" / "inbox"
        self.review = root / "automation" / "review"
        self.decisions, self.drafts = self.review / "decisions.json", self.review / "drafts"
        self.review.mkdir(parents=True, exist_ok=True); self.drafts.mkdir(exist_ok=True)

    @staticmethod
    def read(path: Path, fallback):
        try: return json.loads(path.read_text(encoding="utf-8")) if path.exists() else fallback
        except json.JSONDecodeError: return fallback

    @staticmethod
    def write(path: Path, value):
        temp = path.with_suffix(path.suffix + ".tmp"); temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8"); temp.replace(path)

    def read_decisions(self): return self.read(self.decisions, {})
    def get_draft(self, item_id): return self.read(self.drafts / f"{item_id}.json", None)

    def items(self):
        decisions, result, failures = self.read_decisions(), [], 0
        known = set()
        for report_file in sorted(self.inbox.glob("*.json"), reverse=True):
            report = self.read(report_file, {})
            failures += len(report.get("failures", []))
            for item in report.get("candidates", []):
                if item["id"] in known: continue
                known.add(item["id"]); item["decision"] = decisions.get(item["id"])
                item["status"] = item["decision"]["action"] if item["decision"] else item["status"]; result.append(item)
        return result, failures

    def ensure_item(self, item_id):
        items, _ = self.items()
        item = next((item for item in items if item["id"] == item_id), None)
        if not item: raise ValueError("item não encontrado")
        return item

    def decide(self, item_id, action, note):
        if action not in {"approved", "rejected", "needs_review"}: raise ValueError("ação inválida")
        if action in {"approved", "rejected"} and not note: raise ValueError("justificativa obrigatória")
        self.ensure_item(item_id); decisions = self.read_decisions()
        decisions[item_id] = {"action": action, "note": note, "at": datetime.now(timezone.utc).isoformat(), "publication_allowed": False, "notice": "A decisão não publica conteúdo."}
        self.write(self.decisions, decisions)

    def save_draft(self, item_id, record):
        item = self.ensure_item(item_id)
        if not item.get("decision") or item["decision"]["action"] != "approved": raise ValueError("aprove o item antes de criar um rascunho")
        draft = {"id": item_id, "updated_at": datetime.now(timezone.utc).isoformat(), "status": "draft", "publication_allowed": False, "record": record, "validation": validate(record)}
        self.write(self.drafts / f"{item_id}.json", draft); return draft

    def ready_draft(self, item_id):
        draft = self.get_draft(item_id)
        if not draft: raise ValueError("salve o rascunho antes de prepará-lo")
        errors = validate(draft.get("record", {})); draft["validation"] = errors
        if errors: self.write(self.drafts / f"{item_id}.json", draft); raise ValueError("; ".join(errors))
        draft.update({"status": "ready_for_build", "ready_at": datetime.now(timezone.utc).isoformat(), "publication_allowed": False, "validation": []})
        self.write(self.drafts / f"{item_id}.json", draft)


def handler(store: ReviewStore):
    class Handler(BaseHTTPRequestHandler):
        def send_json(self, payload, status=HTTPStatus.OK):
            body = json.dumps(payload, ensure_ascii=False).encode(); self.send_response(status); self.send_header("Content-Type", "application/json; charset=utf-8"); self.send_header("Cache-Control", "no-store"); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
        def do_GET(self):
            if self.path in {"/", "/index.html"}:
                body = HTML.encode(); self.send_response(HTTPStatus.OK); self.send_header("Content-Type", "text/html; charset=utf-8"); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body); return
            if self.path == "/api/items":
                items, failures = store.items(); drafts = {item["id"]: store.get_draft(item["id"]) for item in items}; ready = sum(1 for draft in drafts.values() if draft and draft.get("status") == "ready_for_build"); pending = sum(1 for item in items if item["status"] == "needs_review"); health = store.read(store.root / "automation" / "monitoring" / "latest.json", {}); self.send_json({"items": items, "drafts": drafts, "count": len(items), "pending": pending, "ready": ready, "failures": failures, "alerts": health.get("alerts", [])}); return
            if self.path == "/api/health": self.send_json({"ok": True}); return
            self.send_error(HTTPStatus.NOT_FOUND)
        def do_POST(self):
            if self.path not in {"/api/decision", "/api/draft", "/api/draft/ready"}: self.send_error(HTTPStatus.NOT_FOUND); return
            try:
                size = int(self.headers.get("Content-Length", "0"));
                if not 0 < size <= 50000: raise ValueError("corpo de pedido inválido")
                payload = json.loads(self.rfile.read(size))
                if self.path == "/api/decision": store.decide(str(payload["id"]), str(payload["action"]), str(payload.get("note", "")).strip())
                elif self.path == "/api/draft": store.save_draft(str(payload["id"]), payload.get("record", {}))
                else: store.ready_draft(str(payload["id"]))
                self.send_json({"ok": True})
            except (KeyError, ValueError, json.JSONDecodeError) as exc: self.send_json({"ok": False, "error": str(exc)}, HTTPStatus.BAD_REQUEST)
        def log_message(self, fmt, *args): pass
    return Handler


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--root", type=Path, default=Path("/opt/observatorio")); parser.add_argument("--port", type=int, default=8787); args = parser.parse_args()
    ThreadingHTTPServer(("127.0.0.1", args.port), handler(ReviewStore(args.root))).serve_forever()
