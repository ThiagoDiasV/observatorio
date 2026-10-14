#!/usr/bin/env python3
"""Impede que a fila de pesquisa seja confundida com conteúdo publicável."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main(path: str) -> int:
    report = json.loads(Path(path).read_text(encoding="utf-8"))
    errors = []
    for item in report.get("candidates", []):
        if item.get("publication_allowed") is not False:
            errors.append(f"{item.get('id')}: candidatos nunca podem autorizar publicação")
        if item.get("status") != "needs_review":
            errors.append(f"{item.get('id')}: status inicial deve ser needs_review")
        source = item.get("source", {})
        if source.get("kind") not in {"primary", "journalism"} or not source.get("url", "").startswith("https://"):
            errors.append(f"{item.get('id')}: fonte inválida")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"OK: {len(report.get('candidates', []))} candidatos aguardando revisão.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
