#!/usr/bin/env python3
"""Audit state ICMS source quality before publication."""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from state_legal_pages import (  # noqa: E402
    STATE_NAMES,
    collect_state_documents,
    normalize,
)


CURATION = ROOT / "data" / "state_curadoria.json"
OUT_JSON = ROOT / "data" / "state_source_audit.json"
OUT_MD = ROOT / "docs" / "state-source-audit.md"

NOISE_TERMS = {
    "ipva": "IPVA",
    "itcmd": "ITCMD/ITCD",
    "itcd": "ITCMD/ITCD",
    "taxa": "Taxas",
    "taxas": "Taxas",
    "emolumento": "Emolumentos",
}

MOJIBAKE_MARKS = (
    "Ã§", "Ã£", "Ã¡", "Ã©", "Ã­", "Ã³", "Ãº",
    "Ã‡", "Ãƒ", "Ã‰", "Ã", "Ã“", "Ãš",
    "Âº", "Â§", "â€", "ï\x81", "\ufffd",
)


def load_curation() -> dict:
    if not CURATION.exists():
        return {"statuses": {}}
    return json.loads(CURATION.read_text(encoding="utf-8"))


def quality_flags(doc: dict) -> list[str]:
    text = doc.get("text", "")
    low = normalize(text)
    path = doc.get("path")
    curated_state_doc = False
    if isinstance(path, Path):
        curated_state_doc = path.is_relative_to(ROOT / "data" / "fontes-estaduais-curadas")
    flags: list[str] = list(doc.get("scope_flags", []))
    if doc.get("scope_blocked"):
        flags.append("escopo material incompatível com ICMS")
    if doc.get("fallback_icms"):
        flags.append("fallback amplo")
    if not doc.get("named_icms"):
        flags.append("categoria não específica de ICMS")
    if "documentos fonte" in low and not re.search(r"https?://", text):
        flags.append("fonte local sem URL oficial no cabeçalho")
    if any(mark in text for mark in MOJIBAKE_MARKS):
        flags.append("ruído de extração/encoding")
    if len(text) < 20_000 and not curated_state_doc:
        flags.append("texto curto para RICMS/benefícios")
    if not curated_state_doc:
        for term, label in NOISE_TERMS.items():
            if re.search(rf"\b{re.escape(term)}\b", low):
                flags.append(f"contém {label}")
    return sorted(set(flags))


def audit() -> dict:
    curation = load_curation()
    status_map = curation.get("statuses", {})
    report = {
        "generated_on": "2026-04-26",
        "summary": {},
        "states": {},
    }
    totals = Counter()
    for uf in sorted(STATE_NAMES):
        docs = list(collect_state_documents(uf)) if uf != "GO" else []
        status = status_map.get(uf, {})
        categories = Counter(doc.get("category", "") for doc in docs)
        flags_by_doc = {doc["file"]: quality_flags(doc) for doc in docs}
        all_flags = sorted({flag for flags in flags_by_doc.values() for flag in flags})
        duplicate_hashes = [
            digest for digest, count in Counter(doc.get("sha256", "") for doc in docs).items()
            if digest and count > 1
        ]
        scope_blocked = [doc for doc in docs if doc.get("scope_blocked")]
        publishable_docs = [doc for doc in docs if not doc.get("scope_blocked")]
        if duplicate_hashes:
            all_flags.append("possível duplicidade de fonte")
        curated_pack = any(
            isinstance(doc.get("path"), Path)
            and doc["path"].is_relative_to(ROOT / "data" / "fontes-estaduais-curadas")
            for doc in docs
        )
        recommendation = "manter_publicado" if uf == "GO" else "bloquear_publicacao_ate_curadoria"
        if uf != "GO" and status.get("publish_deep") and curated_pack and not scope_blocked:
            recommendation = "manter_publicado"
        if uf != "GO" and scope_blocked:
            recommendation = "bloquear_publicacao_ate_reclassificar_escopo"
        if uf != "GO" and not docs:
            recommendation = "pesquisar_fontes_oficiais_do_zero"
        report["states"][uf] = {
            "estado": STATE_NAMES[uf],
            "region": status.get("region", ""),
            "curadoria": status.get("status", "sem_status"),
            "publish_deep": bool(status.get("publish_deep")),
            "document_count": len(docs),
            "publishable_document_count": len(publishable_docs),
            "scope_blocked_document_count": len(scope_blocked),
            "total_chars": sum(int(doc.get("chars", 0)) for doc in docs),
            "categories": dict(sorted(categories.items())),
            "flags": all_flags,
            "recommendation": recommendation,
            "next_step": status.get("next_step", ""),
            "documents": [
                {
                    "file": doc["file"],
                    "category": doc["category"],
                    "chars": doc["chars"],
                    "named_icms": bool(doc.get("named_icms")),
                    "fallback_icms": bool(doc.get("fallback_icms")),
                    "dominant_scope": doc.get("dominant_scope", ""),
                    "source_scopes": doc.get("source_scopes", []),
                    "scope_blocked": bool(doc.get("scope_blocked")),
                    "scope_flags": doc.get("scope_flags", []),
                    "source_documents": doc.get("source_documents", [])[:8],
                    "flags": flags_by_doc[doc["file"]],
                }
                for doc in docs
            ],
        }
        totals["states"] += 1
        totals["docs"] += len(docs)
        totals["publishable_docs"] += len(publishable_docs)
        totals["scope_blocked_docs"] += len(scope_blocked)
        if status.get("publish_deep") and scope_blocked:
            totals["published_scope_errors"] += 1
        totals["blocked"] += 1 if recommendation.startswith("bloquear") else 0
    report["summary"] = dict(totals)
    return report


def md_escape(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def write_bahia_example(lines: list[str], report: dict) -> None:
    ba = report["states"].get("BA", {})
    blocked_docs = [doc for doc in ba.get("documents", []) if doc.get("scope_blocked")]
    if not blocked_docs:
        return
    lines.extend([
        "",
        "## Caso Bahia: erro de escopo material",
        "",
        "A Bahia mostrou o risco central: arquivo com rótulo de ICMS não pode ser aceito quando o próprio texto ou os documentos-fonte indicam Taxas, IPVA, ITCMD ou outro tributo. Categoria, nome do arquivo e ocorrência da palavra ICMS não bastam.",
        "",
        "| Arquivo | Categoria | Escopo dominante | Documentos-fonte | Alerta |",
        "| --- | --- | --- | --- | --- |",
    ])
    for doc in blocked_docs[:8]:
        sources = ", ".join(doc.get("source_documents", [])[:3]) or "sem fonte interna"
        alert = "; ".join(doc.get("scope_flags", [])) or "escopo incompatível"
        lines.append(
            f"| {md_escape(doc['file'])} | {md_escape(doc['category'])} | {md_escape(doc.get('dominant_scope', ''))} | {md_escape(sources)} | {md_escape(alert)} |"
        )


def write_markdown(report: dict) -> None:
    lines = [
        "# Auditoria Da Base Estadual",
        "",
        "Gerado em 26/04/2026.",
        "",
        "Esta auditoria mede qualidade editorial do acervo estadual antes de publicação profunda. Ela não aprova tese tributária; aponta risco de fonte, ruído, escopo e contaminação por tributo diferente de ICMS.",
        "",
        "## Resumo",
        "",
        f"- Estados avaliados: {report['summary'].get('states', 0)}",
        f"- Documentos estaduais candidatos a ICMS: {report['summary'].get('docs', 0)}",
        f"- Documentos úteis após teste de escopo: {report['summary'].get('publishable_docs', 0)}",
        f"- Documentos bloqueados por escopo material: {report['summary'].get('scope_blocked_docs', 0)}",
        f"- Estados bloqueados para publicação profunda: {report['summary'].get('blocked', 0)}",
        "",
        "## Estados",
        "",
        "| UF | Região | Status | Docs | Úteis | Escopo bloqueado | Recomendação | Principais alertas |",
        "| --- | --- | --- | ---: | ---: | ---: | --- | --- |",
    ]
    for uf, item in report["states"].items():
        flags = ", ".join(item["flags"][:5]) if item["flags"] else "sem alerta automatizado"
        lines.append(
            f"| {uf} | {md_escape(item['region'])} | {md_escape(item['curadoria'])} | {item['document_count']} | {item['publishable_document_count']} | {item['scope_blocked_document_count']} | {md_escape(item['recommendation'])} | {md_escape(flags)} |"
        )
    write_bahia_example(lines, report)
    lines.extend([
        "",
        "## Regra De Leitura Do Resultado",
        "",
        "- `escopo material incompatível com ICMS` indica que o texto foi rotulado ou capturado como ICMS, mas os documentos-fonte ou a dominância do conteúdo apontam para Taxas, IPVA, ITCMD/ITCD ou outro escopo.",
        "- `fallback amplo` indica que o portal encontrou a palavra ICMS em categoria genérica, mas não necessariamente um RICMS ou anexo de benefício.",
        "- `ruído de extração/encoding` indica texto vindo de PDF ou HTML com caracteres corrompidos; não deve alimentar explicação didática sem limpeza.",
        "- `contém IPVA/ITCMD/Taxas` indica que o arquivo pode misturar tributos estaduais fora do escopo de ICMS.",
        "- `fonte local sem URL oficial no cabeçalho` indica que o texto pode ser aproveitado como acervo, mas precisa ser amarrado a link oficial antes de publicar.",
        "",
        "## Regra Editorial Nova",
        "",
        "Nenhum Estado pode sair de `revisao_fonte` apenas porque existe arquivo chamado RICMS ou ICMS. A curadoria precisa ler o cabeçalho, os documentos-fonte, o índice interno e amostras do texto. Se um bloco de ICMS estiver falando de Taxas, ele deve ser reclassificado, excluído da trilha de ICMS e substituído por fonte limpa antes de qualquer explicação didática.",
    ])
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    report = audit()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    write_markdown(report)
    print(f"Auditoria estadual gravada: {OUT_JSON.relative_to(ROOT)}")
    print(f"Relatorio gravado: {OUT_MD.relative_to(ROOT)}")
    if report["summary"].get("published_scope_errors", 0):
        raise SystemExit("Há Estado publicado com documento de escopo material incompatível com ICMS.")


if __name__ == "__main__":
    main()
