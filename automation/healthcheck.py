#!/usr/bin/env python3
"""Registra a saúde da coleta e do release sem modificar conteúdo editorial."""
from __future__ import annotations

import argparse
import json
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path


def read(path: Path, fallback):
    try: return json.loads(path.read_text(encoding="utf-8")) if path.exists() else fallback
    except json.JSONDecodeError: return fallback


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--root", type=Path, default=Path("/opt/observatorio")); parser.add_argument("--site", default="https://observatorio.leaomc.com/")
    args = parser.parse_args(); now = datetime.now(timezone.utc)
    health = read(args.root / "automation" / "state" / "source-health.json", {"sources": []})
    checks, alerts = [], []
    sources = health.get("sources", [])
    failures = [source for source in sources if not source.get("ok")]
    checks.append({"name": "fontes", "ok": bool(sources) and len(failures) < len(sources), "sources": len(sources), "failed": len(failures)})
    if not sources: alerts.append("Nenhuma fonte foi verificada pelo coletor.")
    elif failures: alerts.append(f"{len(failures)} fonte(s) falharam na última coleta.")
    if sources and len(failures) == len(sources): alerts.append("Todas as fontes falharam na última coleta.")
    generated = health.get("updated_at")
    try:
        stale = now - datetime.fromisoformat(generated.replace("Z", "+00:00")) > timedelta(hours=30)
    except (AttributeError, ValueError): stale = True
    checks.append({"name": "coleta_recente", "ok": not stale, "updated_at": generated})
    if stale: alerts.append("A coleta está sem atualização há mais de 30 horas.")
    try:
        request = urllib.request.Request(args.site, headers={"User-Agent": "ObservatorioHealth/1.0"})
        with urllib.request.urlopen(request, timeout=20) as response: code = response.status
        checks.append({"name": "site_https", "ok": code == 200, "status": code})
        if code != 200: alerts.append(f"O site respondeu HTTP {code}.")
    except Exception as exc:
        checks.append({"name": "site_https", "ok": False, "error": str(exc)}); alerts.append("Não foi possível consultar o site HTTPS.")
    report = {"checked_at": now.isoformat(), "ok": not alerts, "checks": checks, "alerts": alerts}
    destination = args.root / "automation" / "monitoring" / "latest.json"; destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".tmp"); temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"); temporary.replace(destination)
    print(json.dumps(report, ensure_ascii=False))
    # Alertas descrevem o estado editorial a ser visto no painel; uma coleta
    # parcial não deve fazer o timer parecer quebrado. Falhas de execução
    # (permissão, JSON inválido etc.) continuam encerrando o processo em erro.
    return 0


if __name__ == "__main__": raise SystemExit(main())
