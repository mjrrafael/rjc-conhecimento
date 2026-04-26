#!/usr/bin/env python3
"""Audit static pages, legal modules and navigation for the RJC portal."""

from __future__ import annotations

import os
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from build_portal import STATE_REGIONS  # noqa: E402
from legal_modules import (  # noqa: E402
    FEDERAL_ROOT,
    LEGAL_MODULES,
    SOURCE_DEFS,
    THEME_TO_MODULES,
    TOPIC_TO_MODULES,
    module_chapter_path,
    module_index_path,
)
from state_legal_pages import (  # noqa: E402
    GROUP_DEFS,
    STATE_NAMES,
    benefit_sector_results,
    collect_state_documents,
    group_docs,
    group_path,
    group_by_id,
    index_path as state_index_path,
    sector_anchor,
    source_path,
)


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self.ids: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_map = {name.lower(): value or "" for name, value in attrs}
        if "id" in attrs_map and attrs_map["id"]:
            self.ids.add(attrs_map["id"])
        for attr in ("href", "src"):
            value = attrs_map.get(attr)
            if value:
                self.links.append((attr, value))


def clean_target(value: str) -> tuple[str, str]:
    no_query = value.split("?", 1)[0]
    path, _hash, fragment = no_query.partition("#")
    return path, fragment


def is_external(value: str) -> bool:
    low = value.lower()
    return low.startswith(("http://", "https://", "mailto:", "tel:", "javascript:", "data:"))


def html_files() -> list[Path]:
    return sorted(path for path in ROOT.rglob("*.html") if ".git" not in path.parts)


def parse_pages() -> dict[Path, PageParser]:
    parsed: dict[Path, PageParser] = {}
    for path in html_files():
        parser = PageParser()
        parser.feed(path.read_text(encoding="utf-8", errors="ignore"))
        parsed[path.resolve()] = parser
    return parsed


def resolve_local(base: Path, raw_path: str) -> Path:
    if not raw_path:
        return base
    target = (base.parent / raw_path).resolve()
    if target.is_dir():
        target = target / "index.html"
    return target


def audit_links(parsed: dict[Path, PageParser]) -> list[str]:
    errors: list[str] = []
    known = set(parsed)
    existing = {path.resolve() for path in ROOT.rglob("*") if path.is_file()}
    for path, parser in parsed.items():
        for attr, value in parser.links:
            if is_external(value) or value.startswith("//"):
                continue
            raw_path, fragment = clean_target(value)
            if raw_path.startswith("#"):
                raw_path = ""
                fragment = value[1:]
            target = resolve_local(path, raw_path)
            if target not in existing and target not in known:
                errors.append(f"{path.relative_to(ROOT)}: {attr} quebrado -> {value}")
                continue
            if fragment:
                target_parser = parsed.get(target)
                if target_parser and fragment not in target_parser.ids:
                    errors.append(f"{path.relative_to(ROOT)}: ancora sem destino -> {value}")
    return errors


def audit_search_entries(parsed: dict[Path, PageParser]) -> list[str]:
    errors: list[str] = []
    search_path = ROOT / "assets" / "portal-search.js"
    if not search_path.exists():
        return ["indice de busca ausente: assets/portal-search.js"]
    raw = search_path.read_text(encoding="utf-8", errors="ignore").strip()
    prefix = "window.RJC_SEARCH = "
    if not raw.startswith(prefix):
        return ["indice de busca em formato inesperado"]
    try:
        entries = json.loads(raw[len(prefix):].rstrip(";"))
    except json.JSONDecodeError as exc:
        return [f"indice de busca invalido: {exc}"]
    known = set(parsed)
    for index, entry in enumerate(entries):
        title = entry.get("title", "")
        url = entry.get("url", "")
        if not title or not url:
            errors.append(f"busca item {index}: titulo ou url ausente")
            continue
        if is_external(url):
            continue
        raw_path, fragment = clean_target(url)
        target = (ROOT / raw_path).resolve()
        if target.is_dir():
            target = target / "index.html"
        if target not in known:
            errors.append(f"busca item quebrado: {title} -> {url}")
            continue
        if fragment and fragment not in parsed[target].ids:
            errors.append(f"busca ancora sem destino: {title} -> {url}")
    return errors


def source_has_file(source: dict) -> bool:
    if source.get("fetch_url"):
        return True
    files = source.get("files") or []
    if not files:
        return False
    if source.get("jurisdiction") == "Federal":
        return all((FEDERAL_ROOT / file_name).exists() for file_name in files)
    return True


def audit_legal_registry() -> list[str]:
    errors: list[str] = []
    module_ids = {module["id"] for module in LEGAL_MODULES}
    source_ids = set(SOURCE_DEFS)

    for source_id, source in SOURCE_DEFS.items():
        if not source.get("url"):
            errors.append(f"fonte sem URL oficial: {source_id}")
        if not source_has_file(source):
            errors.append(f"fonte sem texto local/fetch configurado: {source_id}")

    for module in LEGAL_MODULES:
        if not module.get("sources"):
            errors.append(f"modulo sem fontes: {module['id']}")
        if not module.get("chapters"):
            errors.append(f"modulo sem capitulos: {module['id']}")
        for source_id in module.get("sources", []):
            if source_id not in source_ids:
                errors.append(f"{module['id']}: fonte inexistente {source_id}")
        for chapter in module.get("chapters", []):
            if not chapter.get("refs"):
                errors.append(f"{module['id']}/{chapter.get('id')}: capitulo sem referencias legais")
            for ref in chapter.get("refs", []):
                if ref.get("source") not in source_ids:
                    errors.append(f"{module['id']}/{chapter.get('id')}: referencia inexistente {ref.get('source')}")

    for theme in ("iof", "ipi", "pis_cofins", "irpj_csll", "regimes", "previdencia_folha", "reforma", "beneficios"):
        missing = [module_id for module_id in THEME_TO_MODULES.get(theme, []) if module_id not in module_ids]
        if theme not in THEME_TO_MODULES:
            errors.append(f"tema sem modulo legal: {theme}")
        for module_id in missing:
            errors.append(f"tema {theme}: modulo inexistente {module_id}")

    for topic_id, modules in TOPIC_TO_MODULES.items():
        for module_id in modules:
            if module_id not in module_ids:
                errors.append(f"topico {topic_id}: modulo inexistente {module_id}")
    return errors


def audit_regions() -> list[str]:
    errors: list[str] = []
    expected = {
        "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA",
        "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN",
        "RS", "RO", "RR", "SC", "SP", "SE", "TO",
    }
    seen: list[str] = []
    for _region_id, _label, ufs in STATE_REGIONS:
        seen.extend(ufs)
    if set(seen) != expected:
        errors.append(f"regioes nao cobrem exatamente as 27 UFs: {sorted(set(seen) ^ expected)}")
    duplicates = sorted({uf for uf in seen if seen.count(uf) > 1})
    if duplicates:
        errors.append(f"UF duplicada em regioes: {duplicates}")
    for uf in expected:
        flag = ROOT / "assets" / "flags" / f"{uf.lower()}.svg"
        if not flag.exists():
            errors.append(f"bandeira ausente: {flag.relative_to(ROOT)}")
    return errors


def read_page(path: str) -> str:
    file_path = ROOT / path
    if not file_path.exists():
        return ""
    return file_path.read_text(encoding="utf-8", errors="ignore")


def audit_content_pages() -> list[str]:
    errors: list[str] = []
    public_pages = [
        "federal/reforma-tributaria.html",
        "federal/lucro-real.html",
        "federal/lucro-presumido.html",
        "federal/pis-cofins.html",
        "federal/ipi.html",
        "federal/iof.html",
        "federal/irpj-csll.html",
        "folha-clt/index.html",
        "estados/goias.html",
    ]
    for page in public_pages:
        html = read_page(page)
        if not html:
            errors.append(f"pagina critica ausente: {page}")
            continue
        if "legislacao/" not in html and "Lei em tela" not in html and "Legislacao em tela" not in html:
            errors.append(f"pagina critica sem caminho claro para lei em tela: {page}")

    for module in LEGAL_MODULES:
        index_path = module_index_path(module)
        if not read_page(index_path):
            errors.append(f"indice legal ausente: {index_path}")
        for chapter in module["chapters"]:
            chapter_path = module_chapter_path(module, chapter)
            html = read_page(chapter_path)
            if not html:
                errors.append(f"capitulo legal ausente: {chapter_path}")
                continue
            if "legal-document" not in html or ("article-block" not in html and "law-pre" not in html):
                errors.append(f"capitulo sem texto legal em tela: {chapter_path}")
            if "Analise, aplicacao e prova" not in html and "Análise, aplicação e prova" not in html:
                errors.append(f"capitulo sem bloco de analise: {chapter_path}")

    reforma = read_page("federal/legislacao/reforma-tributaria/index.html")
    if reforma and not re.search(r"EC 132/2023|LC 214/2025|LC 227/2026", reforma):
        errors.append("indice da Reforma nao cita os atos centrais")
    for uf in STATE_NAMES:
        if uf == "GO":
            continue
        docs = collect_state_documents(uf)
        if not docs:
            continue
        index_html = read_page(state_index_path(uf))
        if not index_html or "legislação de ICMS em tela" not in index_html:
            errors.append(f"{uf}: indice estadual de ICMS ausente")
        for group in GROUP_DEFS:
            group_html = read_page(group_path(uf, group["id"]))
            if not group_html or "Texto integral" not in group_html:
                errors.append(f"{uf}: grupo estadual sem texto integral: {group['id']}")
        beneficios_html = read_page(group_path(uf, "beneficios"))
        sector_results = benefit_sector_results(group_docs(docs, group_by_id("beneficios")))
        # Reuse the benefits classifier only to confirm that visible sector links exist when the corpus supports them.
        if sector_results and "benefit-sector" not in beneficios_html:
            errors.append(f"{uf}: beneficios fiscais sem secoes setoriais")
        for result in sector_results:
            anchor = sector_anchor(result["sector"])
            if f'id="{anchor}"' not in beneficios_html:
                errors.append(f"{uf}: ancora setorial ausente em beneficios: {anchor}")
        for doc in list(docs)[:3]:
            source_html = read_page(source_path(uf, doc))
            if not source_html or "law-pre" not in source_html:
                errors.append(f"{uf}: fonte estadual sem texto em tela: {doc['file']}")
    return errors


def main() -> int:
    parsed = parse_pages()
    checks = [
        ("links e ancoras", audit_links(parsed)),
        ("indice de busca", audit_search_entries(parsed)),
        ("fontes e modulos legais", audit_legal_registry()),
        ("regioes e bandeiras", audit_regions()),
        ("conteudo critico", audit_content_pages()),
    ]
    errors = [f"[{name}] {error}" for name, group in checks for error in group]
    print(f"Paginas HTML auditadas: {len(parsed)}")
    if errors:
        print("Falhas encontradas:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Auditoria concluida sem falhas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
