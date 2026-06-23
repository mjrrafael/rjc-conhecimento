#!/usr/bin/env python3
"""Shared helpers for the Portal RJC v2 hard-gate audits."""

from __future__ import annotations

import json
import re
import hashlib
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BENEFITS = ROOT / "data" / "benefits_crosswalk.json"
QUARANTINE = ROOT / "data" / "benefits_quarantine.json"
SEARCH_JS = ROOT / "assets" / "portal-search.js"
SEARCH_FULL = ROOT / "assets" / "portal-search-full.json"
BUILD_FRESHNESS = ROOT / "assets" / "build-freshness.json"
LLM_MANIFEST = ROOT / "assets" / "llm-manifest.json"
LLMS_TXT = ROOT / "llms.txt"
SITEMAP_TXT = ROOT / "sitemap.txt"
SITEMAP_XML = ROOT / "sitemap.xml"
BENEFIT_INDEX = ROOT / "beneficios" / "index.html"
TEXTUAL_HASH_SUFFIXES = {".html", ".txt", ".json", ".js", ".xml", ".ndjson", ".md"}
STALE_DATE_MARKERS = (
    "/".join(["25", "04", "2026"]),
    f"Atualizacao editorial: {'/'.join(['25', '04', '2026'])}",
    f"Atualizada em {'/'.join(['25', '04', '2026'])}",
    f"Conteúdo atualizado em {'/'.join(['25', '04', '2026'])}",
    f"Conteudo atualizado em {'/'.join(['25', '04', '2026'])}",
    f"organização editorial V3 atualizada em {'/'.join(['25', '04', '2026'])}",
    f"organizacao editorial V3 atualizada em {'/'.join(['25', '04', '2026'])}",
)


def is_workspace_duplicate(path: Path) -> bool:
    return bool(re.search(r" \(\d+\)$", path.stem))


def iter_public_html_files(base: Path = ROOT) -> list[Path]:
    return sorted(
        path
        for path in base.rglob("*.html")
        if ".git" not in path.parts and not is_workspace_duplicate(path)
    )


BENEFIT_PAGES = [path for path in iter_public_html_files(ROOT / "beneficios") if path.parent == ROOT / "beneficios"]


def load_json(path: Path, fallback: object) -> object:
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def canonical_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    if path.suffix.lower() in TEXTUAL_HASH_SUFFIXES:
        data = read_text(path).replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
        digest.update(data)
        return digest.hexdigest()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def benefit_payload() -> dict:
    payload = load_json(BENEFITS, {})
    return payload if isinstance(payload, dict) else {}


def benefit_entries() -> list[dict]:
    payload = benefit_payload()
    entries = payload.get("entries", [])
    return entries if isinstance(entries, list) else []


def quarantine_entries() -> list[dict]:
    payload = load_json(QUARANTINE, {})
    entries = payload.get("entries", []) if isinstance(payload, dict) else []
    return entries if isinstance(entries, list) else []


def search_full_entries() -> list[dict]:
    payload = load_json(SEARCH_FULL, [])
    return payload if isinstance(payload, list) else []


def search_js_entries() -> list[dict]:
    raw = read_text(SEARCH_JS).strip()
    prefix = "window.RJC_SEARCH = "
    if not raw.startswith(prefix):
        return []
    try:
        payload = json.loads(raw[len(prefix):].rstrip(";"))
    except json.JSONDecodeError:
        return []
    return payload if isinstance(payload, list) else []


def confidence_score(value: object) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value or "").strip().lower()
    if not text:
        return None
    aliases = {
        "alta": 0.95,
        "high": 0.95,
        "media": 0.70,
        "medium": 0.70,
        "baixa": 0.40,
        "low": 0.40,
    }
    if text in aliases:
        return aliases[text]
    try:
        return float(text.replace(",", "."))
    except ValueError:
        return None


def tax_requires_transition(value: str) -> bool:
    low = str(value or "").strip().lower()
    return low in {"icms", "iss", "pis", "cofins", "ipi", "pis/cofins", "pis/cofins-importação", "pis/cofins-importacao"}


def visible_text(html: str) -> str:
    class _Parser(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self.parts: list[str] = []
            self.skip = 0

        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            if tag.lower() in {"script", "style"}:
                self.skip += 1

        def handle_endtag(self, tag: str) -> None:
            if tag.lower() in {"script", "style"} and self.skip:
                self.skip -= 1

        def handle_data(self, data: str) -> None:
            if not self.skip:
                text = " ".join(data.split())
                if text:
                    self.parts.append(text)

    parser = _Parser()
    parser.feed(html)
    return " ".join(parser.parts)


def benefit_article_blocks(path: Path | None = None) -> list[tuple[str, str]]:
    target = path or BENEFIT_INDEX
    html = read_text(target)
    return re.findall(
        r'(<article\b(?:(?!</article>).)*?\bid="([^"]+)"(?:(?!</article>).)*?</article>)',
        html,
        flags=re.I | re.S,
    )


def benefit_articles_by_id(path: Path | None = None) -> dict[str, str]:
    return {entry_id: block for block, entry_id in benefit_article_blocks(path)}


def raw_benefit_articles(path: Path) -> list[str]:
    html = read_text(path)
    return re.findall(r"<article\b(?:(?!</article>).)*?benefit-cross-card(?:(?!</article>).)*?</article>", html, flags=re.I | re.S)


def stale_date_hits() -> list[str]:
    hits: list[str] = []
    for path in iter_public_html_files():
        text = read_text(path)
        for marker in STALE_DATE_MARKERS:
            if marker in text:
                hits.append(f"{path.relative_to(ROOT)} -> {marker}")
                break
    for path in (SEARCH_FULL, LLMS_TXT):
        text = read_text(path)
        for marker in STALE_DATE_MARKERS:
            if marker in text:
                hits.append(f"{path.relative_to(ROOT)} -> {marker}")
                break
    return hits
