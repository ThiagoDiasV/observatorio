#!/usr/bin/env python3
"""Prepara changesets revisados sem tocar no release público.

O comando publish é deliberadamente ausente: a troca de release continua sendo
uma operação privilegiada e explícita em deploy_release.sh.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

REQUIRED = ("kind", "title", "people", "theme", "date", "status", "summary", "outcome", "response", "source")


def load(path: Path, fallback=None):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else fallback


def write(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


def validate(record: dict) -> list[str]:
    errors = [f"campo obrigatório ausente: {key}" for key in REQUIRED if not record.get(key)]
    if record.get("kind") not in {"case", "speech"}:
        errors.append("kind deve ser case ou speech")
    if not isinstance(record.get("people", []), list) or not all(isinstance(p, str) and p.strip() for p in record.get("people", [])):
        errors.append("people deve ser lista de nomes")
    if not isinstance(record.get("source"), dict) or not str(record.get("source", {}).get("url", "")).startswith("https://"):
        errors.append("source.url deve usar HTTPS")
    if not str(record.get("date", "")).startswith(tuple(str(y) for y in range(1900, 2101))):
        errors.append("date deve começar com ano no formato ISO")
    for key in ("summary", "outcome", "response"):
        if len(str(record.get(key, "")).strip()) < 30:
            errors.append(f"{key} precisa de contexto editorial mínimo")
    return errors


def next_id(records: list[dict], prefix: str) -> str:
    used = {str(record.get("id", "")) for record in records}
    n = 1
    while f"{prefix}{n:03d}" in used:
        n += 1
    return f"{prefix}{n:03d}"


def normalize_for_site(record: dict, all_records: list[dict]) -> dict:
    source = record["source"]
    common = {
        "id": next_id(all_records, "A" if record["kind"] == "case" else "M"),
        "title": record["title"].strip(), "people": record["people"], "theme": record["theme"].strip(),
        "year": int(record["date"][:4]), "date": record["date"][:10], "status": record["status"].strip(),
        "group": record.get("group", "Registro em apuração"), "summary": record["summary"].strip(),
        "outcome": record["outcome"].strip(), "response": record["response"].strip(),
        "sources": [{"label": source.get("label", source["url"]), "url": source["url"]}],
        "analysis": {"title": "Contexto editorial", "text": record.get("analysis", "Ficha criada após revisão humana; consulte a fonte primária indicada.")},
        "documentIds": record.get("documentIds", []), "slug": record.get("slug", ""),
    }
    if record["kind"] == "speech":
        common.update({"kind": "speech", "eventDate": record.get("eventDate", common["date"]), "dateBasis": "Data confirmada pelo editor", "quote": record.get("quote", ""), "medium": record.get("medium", "Registro documental"), "affiliation": record.get("affiliation", "")})
    else:
        common["stf"] = bool(record.get("stf", False))
    return common


def create_changeset(drafts_dir: Path, out_dir: Path) -> Path:
    drafts = [load(path) for path in sorted(drafts_dir.glob("*.json"))]
    selected = [draft for draft in drafts if draft.get("status") == "ready_for_build"]
    if not selected:
        raise SystemExit("Nenhum rascunho marcado como pronto para preparação.")
    errors = {draft.get("id", "sem-id"): validate(draft.get("record", {})) for draft in selected}
    errors = {key: value for key, value in errors.items() if value}
    if errors:
        raise SystemExit(json.dumps({"drafts_invalidos": errors}, ensure_ascii=False))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    digest = hashlib.sha256("".join(sorted(draft["id"] for draft in selected)).encode()).hexdigest()[:12]
    destination = out_dir / f"changeset-{stamp}-{digest}"
    destination.mkdir(parents=True, exist_ok=False)
    write(destination / "drafts.json", selected)
    write(destination / "manifest.json", {"created_at": datetime.now(timezone.utc).isoformat(), "state": "prepared", "draft_count": len(selected), "draft_ids": [draft["id"] for draft in selected], "public_release_changed": False})
    print(destination)
    return destination


def stage(changeset: Path, source: Path, work_root: Path) -> Path:
    manifest = load(changeset / "manifest.json")
    if manifest.get("state") != "prepared":
        raise SystemExit("Changeset não está pronto para staging.")
    if not (source / "build.py").exists() or not (source / "cases.json").exists():
        raise SystemExit("Fonte editorial inválida; o staging não foi iniciado.")
    target = work_root / changeset.name
    if target.exists():
        raise SystemExit("Staging já existe; revise ou remova manualmente após auditoria.")
    # Os PDFs originais precisam acompanhar o build para que verify.py possa
    # conferir hashes e links; somente artefatos regeneráveis são omitidos.
    shutil.copytree(source, target, ignore=shutil.ignore_patterns("dist", ".git"))
    # O gerador sobrescreve HTML/JSON, mas os recursos estáticos e PDFs do
    # acervo são preservados a partir do último build validado.
    shutil.copytree(source / "dist", target / "dist")
    cases, statements = load(target / "cases.json"), load(target / "statements.json")
    extra = load(target / "lula_records.json", {"cases": [], "statements": []})
    all_records = cases + statements + extra.get("cases", []) + extra.get("statements", [])
    for draft in load(changeset / "drafts.json"):
        record = normalize_for_site(draft["record"], all_records)
        (statements if record.get("kind") == "speech" else cases).append(record)
        all_records.append(record)
    write(target / "cases.json", cases); write(target / "statements.json", statements)
    subprocess.run(("python3", "build.py"), cwd=target, check=True)
    subprocess.run(("python3", "verify.py"), cwd=target, check=True)
    manifest.update({"state": "staged", "staged_at": datetime.now(timezone.utc).isoformat(), "staging_path": str(target), "public_release_changed": False})
    write(changeset / "manifest.json", manifest)
    print(target)
    return target


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("validate"); check.add_argument("draft", type=Path)
    create = sub.add_parser("create-changeset"); create.add_argument("--drafts", type=Path, required=True); create.add_argument("--out", type=Path, required=True)
    staged = sub.add_parser("stage"); staged.add_argument("--changeset", type=Path, required=True); staged.add_argument("--source", type=Path, required=True); staged.add_argument("--work-root", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "validate":
        errors = validate(load(args.draft).get("record", {})); print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=False)); return int(bool(errors))
    if args.command == "create-changeset": create_changeset(args.drafts, args.out)
    if args.command == "stage": stage(args.changeset, args.source, args.work_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
