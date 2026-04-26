#!/usr/bin/env python3
"""Export the versionable legal-source registry used by the portal."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from legal_modules import FEDERAL_ROOT, LEGAL_MODULES, SOURCE_DEFS, UPDATED_ON  # noqa: E402
from state_legal_pages import state_source_records  # noqa: E402


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def modules_for_source(source_id: str) -> list[dict]:
    items: list[dict] = []
    for module in LEGAL_MODULES:
        chapters = [
            chapter["id"]
            for chapter in module.get("chapters", [])
            for ref in chapter.get("refs", [])
            if ref.get("source") == source_id
        ]
        if source_id in module.get("sources", []) or chapters:
            items.append(
                {
                    "module_id": module["id"],
                    "module_title": module["title"],
                    "chapters": sorted(set(chapters)),
                }
            )
    return items


def source_record(source_id: str, source: dict) -> dict:
    files = source.get("files") or []
    hashes: dict[str, str] = {}
    for file_name in files:
        path = FEDERAL_ROOT / file_name
        if path.exists():
            hashes[file_name] = sha256_file(path)
    return {
        "source_id": source_id,
        "jurisdiction": source.get("jurisdiction"),
        "title": source.get("title"),
        "short": source.get("short"),
        "official_url": source.get("url"),
        "storage": {
            "type": "local_text" if files else "official_fetch",
            "files": files,
            "sha256": hashes,
            "fetch_url": source.get("fetch_url", ""),
        },
        "note": source.get("note", ""),
        "render": source.get("render", "articles"),
        "source_ranges": source.get("source_ranges", []),
        "modified_by": [],
        "used_by": modules_for_source(source_id),
    }


def main() -> int:
    registry = {
        "schema": "rjc-legal-sources-v1",
        "updated_on": UPDATED_ON,
        "editorial_rule": "Cada tese publicada deve apontar o ato oficial, manter o texto em tela e registrar o caminho de continuidade por tema.",
        "change_workflow": [
            "adicionar ou atualizar a fonte em scripts/legal_modules.py",
            "vincular a fonte a modulo e capitulo",
            "executar scripts/build_portal.py",
            "executar scripts/export_legal_registry.py",
            "executar scripts/audit_portal.py",
        ],
        "sources": [source_record(source_id, SOURCE_DEFS[source_id]) for source_id in sorted(SOURCE_DEFS)] + state_source_records(),
    }
    target = ROOT / "data" / "legal_sources_registry.json"
    target.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Registro exportado: {target.relative_to(ROOT)} ({len(registry['sources'])} fontes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
