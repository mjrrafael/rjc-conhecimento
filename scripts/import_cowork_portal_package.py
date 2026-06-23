#!/usr/bin/env python3
"""Import the Cowork/Bruno portal package into controlled public datasets."""

from __future__ import annotations

import hashlib
import json
import re
import urllib.request
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = Path(r"G:\Outros computadores\LOCALHOST\Departamento Financeiro MTJ\#administração\#codex")
MEMORY_ROOT = SOURCE_ROOT / "BD_LEGISLACAO" / "Memória_profunda"

INGESTION_JSON = MEMORY_ROOT / "INGESTAO_PORTAL_TRIBUTARIO_2026-06-22.json"
STATE_REGISTRY_JSON = MEMORY_ROOT / "memória_profunda_estadual" / "_indices" / "legal_sources_registry.json"
PROJECT_DOCS_JSONL = MEMORY_ROOT / "memoria_parceira" / "05_projetos" / "portal_tributario" / "projeto_portal_tributario_ingestao_docs_2026-06-22.jsonl"
REFORMA_RESELO_JSONL = MEMORY_ROOT / "memória_profunda_federal" / "banco_llm" / "reforma_tributaria_lc214_lc224_lc227_reselo_sofia_2026-06-22.jsonl"
ARROZ_RESELO_JSONL = MEMORY_ROOT / "memória_profunda_federal" / "banco_llm" / "produtos_arroz_reselo_sofia_2026-06-22.jsonl"

OUT_CORPUS = ROOT / "data" / "corpus-local" / "legal_sources_registry.json"
OUT_UF_PLAN = ROOT / "data" / "corpus-local" / "uf-sealing-plan.json"
OUT_PROJECT_MANIFEST = ROOT / "data" / "cowork" / "portal-package-manifest.json"
OUT_REFORMA = ROOT / "data" / "reforma-tributaria" / "reselo-lc214-lc224-lc227.ndjson"
OUT_PRODUTOS_INDEX = ROOT / "data" / "produtos-ncm" / "index.json"
OUT_PRODUTOS_CAP10 = ROOT / "data" / "produtos-ncm" / "cap-10.json"

PLANALTO_SOURCES = {
    "lc214_2025": {
        "tipo": "Lei Complementar",
        "numero": "214/2025",
        "titulo": "LC 214/2025 - IBS, CBS e Imposto Seletivo",
        "url": "https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214.htm",
    },
    "lc224_2025": {
        "tipo": "Lei Complementar",
        "numero": "224/2025",
        "titulo": "LC 224/2025 - reducao gradual de beneficios federais",
        "url": "https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp224.htm",
    },
    "lc227_2026": {
        "tipo": "Lei Complementar",
        "numero": "227/2026",
        "titulo": "LC 227/2026 - CGIBS e administracao do IBS",
        "url": "https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp227.htm",
    },
    "lei_10925_2004": {
        "tipo": "Lei",
        "numero": "10.925/2004",
        "titulo": "Lei 10.925/2004 - aliquota zero PIS/Cofins",
        "url": "https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2004/lei/l10.925.htm",
    },
}

UF_CODES = [
    "AC",
    "AL",
    "AP",
    "AM",
    "BA",
    "CE",
    "DF",
    "ES",
    "GO",
    "MA",
    "MT",
    "MS",
    "MG",
    "PA",
    "PB",
    "PR",
    "PE",
    "PI",
    "RJ",
    "RN",
    "RS",
    "RO",
    "RR",
    "SC",
    "SP",
    "SE",
    "TO",
]


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_ndjson(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows)
    path.write_text(text, encoding="utf-8", newline="\n")


def rel_from_source(path: str) -> str:
    normalized = str(path or "").replace("\\", "/")
    marker = "BD_LEGISLACAO/"
    idx = normalized.find(marker)
    if idx >= 0:
        return normalized[idx:]
    marker = "#codex/"
    idx = normalized.find(marker)
    if idx >= 0:
        return normalized[idx + len(marker) :]
    return normalized


def strip_absolute_paths(entry: dict) -> dict:
    clean = json.loads(json.dumps(entry, ensure_ascii=False))
    storage = clean.get("storage")
    if isinstance(storage, dict):
        absolute = storage.pop("path", "")
        if absolute:
            storage["source_relative_path"] = rel_from_source(str(absolute))
    return clean


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch_source_health(url: str) -> dict:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=45) as response:
            raw = response.read()
            return {
                "http_status": int(getattr(response, "status", 0) or 0),
                "live_sha256": sha256_bytes(raw),
                "live_bytes": len(raw),
                "error": None,
            }
    except Exception as exc:  # pragma: no cover - network variance is recorded in data.
        return {
            "http_status": None,
            "live_sha256": None,
            "live_bytes": None,
            "error": str(exc),
        }


def official_sources(ingestion: dict, generated_at: str) -> list[dict]:
    raw_snapshots = ingestion.get("planalto_snapshots", {})
    if isinstance(raw_snapshots, list):
        snapshots = {str(item.get("id", "")): item for item in raw_snapshots if isinstance(item, dict)}
    elif isinstance(raw_snapshots, dict):
        snapshots = raw_snapshots
    else:
        snapshots = {}
    sources = []
    for source_id, meta in PLANALTO_SOURCES.items():
        snapshot = snapshots.get(source_id, {})
        health = fetch_source_health(meta["url"])
        sources.append(
            {
                "id": source_id,
                **meta,
                "url_resolve": health.get("http_status") == 200,
                "http_status": health.get("http_status"),
                "live_sha256": health.get("live_sha256"),
                "live_bytes": health.get("live_bytes"),
                "live_error": health.get("error"),
                "snapshot_sha256": snapshot.get("sha256"),
                "snapshot_source_path": rel_from_source(snapshot.get("snapshot_path") or snapshot.get("path", "")),
                "snapshot_status": snapshot.get("status"),
                "verified_at": generated_at,
                "source_role": "fonte_oficial_primaria",
            }
        )
    return sources


def project_manifest(generated_at: str) -> dict:
    docs = read_jsonl(PROJECT_DOCS_JSONL)
    return {
        "schema": "rjc-cowork-package-manifest-v1",
        "generated_at": generated_at,
        "source_root": rel_from_source(str(SOURCE_ROOT)),
        "rule_zero": "Nada suposto; sem fonte oficial lida, vigencia e hash, o item fica A_VALIDAR.",
        "summary": {
            "documents_ingested": len(docs),
            "bytes": sum(int(row.get("bytes", 0) or 0) for row in docs),
            "chars": sum(int(row.get("chars", 0) or 0) for row in docs),
        },
        "documents": [
            {
                "relative_path": row.get("relative_path"),
                "sha256": row.get("sha256"),
                "bytes": row.get("bytes"),
                "chars": row.get("chars"),
                "ingested_at": row.get("ingested_at"),
            }
            for row in docs
        ],
    }


def corpus_registry(generated_at: str) -> dict:
    source = read_json(STATE_REGISTRY_JSON)
    entries = [strip_absolute_paths(entry) for entry in source.get("entries", [])]
    by_uf: dict[str, int] = {}
    for entry in entries:
        uf = str(entry.get("uf", "")).upper()
        if uf:
            by_uf[uf] = by_uf.get(uf, 0) + 1
    return {
        "schema": "rjc-corpus-local-registry-v1",
        "generated_at": generated_at,
        "source_generated_at": source.get("generated_at"),
        "rule_zero": source.get("rule_zero", "Corpus local nao vira verde sem URL oficial viva, vigencia e sha256."),
        "selo_maximo_atual": "AMARELO_CORPUS_LOCAL",
        "public_policy": "Este arquivo registra corpus local consolidado. Ele nao autoriza beneficio publicado nem substitui SEFAZ/CONFAZ/Planalto vivos.",
        "summary": {
            "entries": len(entries),
            "ufs": len(by_uf),
            "by_uf": dict(sorted(by_uf.items())),
            "go_cbenef_local_entries": sum(1 for entry in entries if entry.get("tipo") == "cbenef_oficial_local_goias"),
        },
        "entries": entries,
    }


def uf_sealing_plan(generated_at: str, corpus: dict) -> dict:
    by_uf = corpus.get("summary", {}).get("by_uf", {})
    ufs = []
    for uf in UF_CODES:
        is_go = uf == "GO"
        ufs.append(
            {
                "uf": uf,
                "corpus_entries": int(by_uf.get(uf, 0) or 0),
                "corpus_selo": "AMARELO_CORPUS_LOCAL",
                "cbenef_status": "AMARELO_COM_SNAPSHOT_LOCAL_REVALIDAR_SEFAZ" if is_go else "A_VALIDAR_SEFAZ_VIVA",
                "publicavel_verde": False,
                "green_requirements": [
                    "URL oficial da SEFAZ/UF resolvendo HTTP 200",
                    "vigencia/eficacia/fim extraidos da fonte oficial",
                    "sha256 do artefato oficial lido",
                    "internalizacao/ratificacao quando depender de CONFAZ",
                ],
                "note": "GO tem snapshot local de cBenef; ainda requer revalidacao das URLs SEFAZ para verde."
                if is_go
                else "cBenef e grades por NCM permanecem A_VALIDAR ate captura oficial viva da SEFAZ.",
            }
        )
    return {
        "schema": "rjc-uf-sealing-plan-v1",
        "generated_at": generated_at,
        "rule_zero": "UF/cBenef nao-GO nunca vira verde por corpus local ou keyword.",
        "ufs": ufs,
    }


def product_seed(generated_at: str, sources: list[dict], reforma_rows: list[dict], arroz_rows: list[dict]) -> tuple[dict, dict]:
    source_ids = {source["id"]: source for source in sources}
    rice_source_ids = ["lei_10925_2004", "lc224_2025", "lc214_2025"]
    source_refs = [
        {
            "id": source_id,
            "url": source_ids[source_id]["url"],
            "http_status": source_ids[source_id]["http_status"],
            "snapshot_sha256": source_ids[source_id]["snapshot_sha256"],
            "live_sha256": source_ids[source_id]["live_sha256"],
        }
        for source_id in rice_source_ids
        if source_id in source_ids
    ]
    produtos = [
        {
            "id": "produto-arroz-ncm-1006",
            "produto": "Arroz",
            "chapter": "10",
            "chapter_title": "Cereais",
            "status": "A_VALIDAR_ENVELOPE_TEMPORAL",
            "public_status": "visible_research_seed",
            "publishable": False,
            "verificado_em": generated_at[:10],
            "why_not_green": [
                "campo publicacao/inicio_vigencia/inicio_eficacia/fim_vigencia nao foi extraido integralmente para card de beneficio",
                "TIPI/NCM oficial da posicao 1006 ainda nao foi capturada nesta rodada",
                "CST/cClassTrib operacional da Reforma Tributaria permanece A_VALIDAR",
            ],
            "ncm": [
                {
                    "codigo": "1006.20",
                    "digitos": "100620",
                    "descricao": "Arroz descascado (cargo ou castanho)",
                    "pis_cofins": "Lei 10.925/2004 art. 1, V cobre 1006.20 conforme re-selo Planalto.",
                    "ibs_cbs": "LC 214/2025 art. 125 + Anexo I cobre 1006.20 conforme re-selo Planalto.",
                    "status": "A_VALIDAR_ENVELOPE_TEMPORAL",
                },
                {
                    "codigo": "1006.30",
                    "digitos": "100630",
                    "descricao": "Arroz semibranqueado ou branqueado, mesmo polido ou brunido",
                    "pis_cofins": "Lei 10.925/2004 art. 1, V cobre 1006.30 conforme re-selo Planalto.",
                    "ibs_cbs": "LC 214/2025 art. 125 + Anexo I cobre 1006.30 conforme re-selo Planalto.",
                    "status": "A_VALIDAR_ENVELOPE_TEMPORAL",
                },
                {
                    "codigo": "1006.40.00",
                    "digitos": "10064000",
                    "descricao": "Arroz quebrado",
                    "pis_cofins": "A_VALIDAR: nao consta no re-selo da Lei 10.925/2004 art. 1, V.",
                    "ibs_cbs": "LC 214/2025 art. 125 + Anexo I cobre 1006.40.00 conforme re-selo Planalto.",
                    "status": "A_VALIDAR_ENVELOPE_TEMPORAL",
                },
            ],
            "reselos": [
                {
                    "id": "arroz-pis-cofins-lei10925-lc224",
                    "tributos": ["PIS", "COFINS"],
                    "beneficio": "aliquota_zero",
                    "ente_uf": "Uniao",
                    "assertion": "Lei 10.925/2004 art. 1, V cobre 1006.20 e 1006.30; LC 224/2025 art. 4, par. 8, III preserva a excecao da Cesta Basica Nacional.",
                    "official_source_ids": ["lei_10925_2004", "lc224_2025"],
                    "publicacao": "A_VALIDAR",
                    "inicio_vigencia": "A_VALIDAR",
                    "inicio_eficacia": "A_VALIDAR",
                    "fim_vigencia": "A_VALIDAR",
                    "transicao_rt": "coexiste; PIS/Cofins antigo em transicao com CBS/IBS; conferir LC 214/2025 e LC 224/2025",
                    "status": "A_VALIDAR_ENVELOPE_TEMPORAL",
                    "publishable": False,
                },
                {
                    "id": "arroz-ibs-cbs-lc214",
                    "tributos": ["IBS", "CBS"],
                    "beneficio": "aliquota_zero",
                    "ente_uf": "Uniao",
                    "assertion": "LC 214/2025 art. 125 + Anexo I cobre arroz NCM 1006.20, 1006.30 e 1006.40.00.",
                    "official_source_ids": ["lc214_2025"],
                    "publicacao": "A_VALIDAR",
                    "inicio_vigencia": "A_VALIDAR",
                    "inicio_eficacia": "A_VALIDAR",
                    "fim_vigencia": "A_VALIDAR",
                    "transicao_rt": "IBS/CBS em implantacao; teste 2026 e plena CBS 2027 devem ser conferidos no card operacional",
                    "status": "A_VALIDAR_ENVELOPE_TEMPORAL",
                    "publishable": False,
                },
                {
                    "id": "lc227-nao-fonte-10pct",
                    "tributos": ["IBS"],
                    "beneficio": "nao_e_beneficio",
                    "ente_uf": "Uniao",
                    "assertion": "LC 227/2026 institui CGIBS/administracao do IBS e nao e fonte da mecanica de 10% dos beneficios federais.",
                    "official_source_ids": ["lc227_2026"],
                    "publicacao": "A_VALIDAR",
                    "inicio_vigencia": "A_VALIDAR",
                    "inicio_eficacia": "A_VALIDAR",
                    "fim_vigencia": "A_VALIDAR",
                    "transicao_rt": "n/a; registro negativo de enquadramento",
                    "status": "VERIFICADO_FONTE_SEM_CARD_BENEFICIO",
                    "publishable": False,
                },
            ],
            "official_sources": source_refs,
            "source_records": {
                "reforma_reselo_ids": [row.get("id") for row in reforma_rows],
                "arroz_reselo_ids": [row.get("id") for row in arroz_rows],
            },
            "search_text": "arroz 1006 100620 100630 10064000 pis cofins aliquota zero lei 10925 lc224 lc214 ibs cbs cesta basica nacional",
        }
    ]
    cap10 = {
        "schema": "rjc-produto-ncm-chapter-v1",
        "generated_at": generated_at,
        "chapter": "10",
        "chapter_title": "Cereais",
        "source": "Cowork/Bruno + re-selo Planalto Sofia 2026-06-22",
        "products": produtos,
    }
    index = {
        "schema": "rjc-produto-ncm-v1",
        "generated_at": generated_at,
        "rule_zero": "Produto/NCM nao publica beneficio verde sem fonte oficial viva, vigencia completa e sha256.",
        "summary": {
            "products": len(produtos),
            "ncm_codes": sum(len(product["ncm"]) for product in produtos),
            "official_sources": len(sources),
            "plantalto_sources_http_200": sum(1 for source in sources if source.get("http_status") == 200),
            "a_validar_products": sum(1 for product in produtos if str(product.get("status", "")).startswith("A_VALIDAR")),
        },
        "official_sources": sources,
        "chapters": [
            {
                "chapter": "10",
                "title": "Cereais",
                "path": "data/produtos-ncm/cap-10.json",
                "products": len(produtos),
                "ncm_codes": sum(len(product["ncm"]) for product in produtos),
                "status": "A_VALIDAR_ENVELOPE_TEMPORAL",
            }
        ],
    }
    return index, cap10


def main() -> int:
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    ingestion = read_json(INGESTION_JSON)
    reforma_rows = read_jsonl(REFORMA_RESELO_JSONL)
    arroz_rows = read_jsonl(ARROZ_RESELO_JSONL)
    sources = official_sources(ingestion, generated_at)
    corpus = corpus_registry(generated_at)
    index, cap10 = product_seed(generated_at, sources, reforma_rows, arroz_rows)

    write_json(OUT_PROJECT_MANIFEST, project_manifest(generated_at))
    write_json(OUT_CORPUS, corpus)
    write_json(OUT_UF_PLAN, uf_sealing_plan(generated_at, corpus))
    write_ndjson(OUT_REFORMA, reforma_rows)
    write_json(OUT_PRODUTOS_INDEX, index)
    write_json(OUT_PRODUTOS_CAP10, cap10)

    print(
        json.dumps(
            {
                "status": "OK",
                "generated_at": generated_at,
                "corpus_entries": corpus["summary"]["entries"],
                "product_index": str(OUT_PRODUTOS_INDEX.relative_to(ROOT)),
                "plantalto_http_200": index["summary"]["plantalto_sources_http_200"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
