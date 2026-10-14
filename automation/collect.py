#!/usr/bin/env python3
"""Coleta diária auditável. Cria candidatos privados; nunca publica conteúdo."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parent
USER_AGENT = "ObservatorioResearchBot/2.0 (+https://observatorio.leaomc.com)"
THEMES = {
    "STF e Justiça": ("stf", "supremo", "judiciário", "justiça", "tribunal", "acórdão", "decisão"),
    "Eleições e democracia": ("tse", "eleição", "eleitoral", "urna", "democracia", "partido"),
    "Administração pública": ("cgu", "licitação", "contrato", "emenda", "governo", "ministério"),
    "Investigações e processos": ("inquérito", "denúncia", "investiga", "indicia", "prisão", "processo", "polícia", "mpf"),
    "Falas públicas": ("disse", "afirmou", "declaração", "entrevista", "discurso", "fala"),
}


def clean(value: str | None) -> str:
    text = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", unescape(text)).strip()


def child_text(node: ET.Element, names: tuple[str, ...]) -> str:
    for element in node.iter():
        if element.tag.rsplit("}", 1)[-1] in names and clean(element.text):
            return clean(element.text)
    return ""


def parse_feed(payload: bytes, source: dict) -> list[dict]:
    # Alguns feeds públicos publicam entidades HTML fora do subconjunto XML.
    # Escapá-las preserva texto e evita perder toda a fonte por um caractere.
    text = payload.decode("utf-8", errors="replace")
    text = re.sub(r"&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9a-fA-F]+;)", "&amp;", text)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    root = ET.fromstring(text)
    items = [node for node in root.iter() if node.tag.rsplit("}", 1)[-1] in {"item", "entry"}]
    records = []
    for item in items:
        link = child_text(item, ("link",))
        if not link:
            for node in item.iter():
                if node.tag.rsplit("}", 1)[-1] == "link" and node.attrib.get("href"):
                    link = node.attrib["href"]
                    break
        title = child_text(item, ("title",))
        summary = child_text(item, ("description", "summary", "content"))
        published = child_text(item, ("pubDate", "published", "updated", "date"))
        if link and title:
            records.append({"url": link, "title": title, "summary": summary, "published_raw": published, "source": source})
    return records


def normalize_date(raw: str) -> str | None:
    raw = raw.strip()
    if not raw:
        return None
    try:
        return parsedate_to_datetime(raw).astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError, IndexError):
        pass
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(timezone.utc).isoformat()
    except ValueError:
        return None


def relevant(record: dict, terms: list[str]) -> list[str]:
    haystack = (record["title"] + " " + record["summary"]).casefold()
    return [term for term in terms if term.casefold() in haystack]


def classify(record: dict, matches: list[str]) -> tuple[list[str], list[str]]:
    text = (record["title"] + " " + record["summary"]).casefold()
    themes = [name for name, keywords in THEMES.items() if any(word in text for word in keywords)]
    return (themes or ["A classificar"], sorted({term for term in matches if len(term) > 2}))


def risk_level(record: dict) -> str:
    wording = (record["title"] + " " + record["summary"]).casefold()
    sensitive = ("investiga", "denúncia", "conden", "indicia", "prisão", "crime", "corrup")
    return "high" if any(word in wording for word in sensitive) else "normal"


def signature(record: dict) -> str:
    title = re.sub(r"[^a-z0-9 ]", "", record["title"].casefold())
    return re.sub(r"\s+", " ", title).strip()[:180]


def load_json(path: Path, fallback):
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else fallback
    except json.JSONDecodeError:
        return fallback


def atomic_json(path: Path, value) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT / "sources.json")
    parser.add_argument("--output", type=Path, default=ROOT / "inbox")
    parser.add_argument("--state", type=Path, default=ROOT / "state" / "seen.json")
    parser.add_argument("--health", type=Path, default=ROOT / "state" / "source-health.json")
    args = parser.parse_args()
    config = load_json(args.config, {})
    args.output.mkdir(parents=True, exist_ok=True)
    args.state.parent.mkdir(parents=True, exist_ok=True)
    seen_state = load_json(args.state, {"urls": [], "signatures": []})
    seen_urls, seen_signatures = set(seen_state.get("urls", [])), set(seen_state.get("signatures", []))
    failures, candidates, source_status = [], [], []
    fetched_at = datetime.now(timezone.utc).isoformat()
    for source in config.get("sources", []):
        if not source.get("enabled", True):
            continue
        try:
            request = urllib.request.Request(source["feed"], headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/atom+xml, application/xml;q=0.9"})
            with urllib.request.urlopen(request, timeout=25) as response:
                records = parse_feed(response.read(), source)
            source_status.append({"id": source["id"], "name": source["name"], "checked_at": fetched_at, "ok": True, "records": len(records)})
        except Exception as exc:
            failures.append({"source": source["id"], "feed": source["feed"], "error": str(exc)})
            source_status.append({"id": source["id"], "name": source["name"], "checked_at": fetched_at, "ok": False, "error": str(exc)})
            continue
        for record in records:
            matches = relevant(record, config.get("watch_terms", []))
            normalized_signature = signature(record)
            if not matches or record["url"] in seen_urls or normalized_signature in seen_signatures:
                continue
            fingerprint = hashlib.sha256(record["url"].encode()).hexdigest()[:16]
            themes, people = classify(record, matches)
            candidates.append({
                "id": f"candidate-{fingerprint}", "discovered_at": fetched_at,
                "status": "needs_review", "publication_allowed": False,
                "risk": risk_level(record), "matched_terms": matches, "entities": people,
                "themes": themes, "title": record["title"], "summary": record["summary"],
                "published_raw": record["published_raw"], "published_at": normalize_date(record["published_raw"]),
                "dedupe_signature": normalized_signature,
                "source": {"id": source["id"], "name": source["name"], "kind": source["kind"], "authority": source.get("authority", "unknown"), "feed": source["feed"], "url": record["url"]},
                "provenance": {"fetched_at": fetched_at, "collector_version": 2, "review_required": True}
            })
            seen_urls.add(record["url"]); seen_signatures.add(normalized_signature)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    report_path = args.output / f"{stamp}.json"
    # Reexecuções no mesmo dia atualizam a saúde das fontes sem apagar a fila
    # já apresentada ao editor naquela data.
    existing = load_json(report_path, {})
    preserved = {item.get("id"): item for item in existing.get("candidates", []) if item.get("id")}
    preserved.update({item["id"]: item for item in candidates})
    report = {"generated_at": fetched_at, "collector_version": 2, "candidates": list(preserved.values()), "failures": failures, "source_status": source_status}
    atomic_json(report_path, report)
    atomic_json(args.state, {"urls": sorted(seen_urls), "signatures": sorted(seen_signatures)})
    atomic_json(args.health, {"updated_at": fetched_at, "sources": source_status, "failures": failures})
    print(json.dumps({"new_candidates": len(candidates), "queued_candidates": len(preserved), "sources_checked": len(source_status), "sources_failed": len(failures), "report": str(report_path)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
