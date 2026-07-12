#!/usr/bin/env python3
"""Build validated benefit/product crosswalks from official legal text.

This module is intentionally conservative. It publishes only records that can
be tied to a local legal text captured from an official source and that contain
an operational hook such as NCM, CEST, cBenef, CST, cClassTrib or a literal
product/operation description in the same legal excerpt.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import unicodedata
import urllib.request
from datetime import date
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from state_legal_pages import (  # noqa: E402
    BENEFIT_SECTOR_DEFS,
    STATE_NAMES,
    collect_state_documents,
)


BD_FEDERAL = Path(r"C:\Users\kris2\OneDrive\COWORK\BD_LEGISLACAO\#FEDERAIS-COMPILADO-ONLINE\legislacao_txt_completa")
TODAY = date.today().isoformat()

BENEFIT_NEEDLES = [
    "isenção",
    "isencao",
    "isentas",
    "isento",
    "redução de base",
    "reducao de base",
    "base de cálculo é reduzida",
    "base de calculo e reduzida",
    "crédito presumido",
    "credito presumido",
    "crédito outorgado",
    "credito outorgado",
    "diferimento",
    "diferido",
    "suspensão",
    "suspensao",
    "alíquota zero",
    "aliquota zero",
    "alíquota 0",
    "aliquota 0",
    "monofásic",
    "monofasic",
    "não incidência",
    "nao incidencia",
    "imunidade",
    "substituição tributária",
    "substituicao tributaria",
    "antecipação",
    "antecipacao",
    "cbenef",
    "cst",
    "cclasstrib",
    "ccredpres",
]

STALE_NEEDLES = [
    "revogado",
    "revogada",
    "redação anterior",
    "redacao anterior",
    "vigência encerrada",
    "vigencia encerrada",
    "sem eficácia",
    "sem eficacia",
]

FEDERAL_FILES = [
    {
        "jurisdiction": "Federal",
        "name": "PIS/Cofins",
        "tax": "PIS/Cofins",
        "file": "IN_RFB_2121_2022_PIS_COFINS_Parte1.txt",
        "title": "Instrução Normativa RFB nº 2.121/2022 - PIS/Pasep e Cofins",
        "official_url": "https://normas.receita.fazenda.gov.br/sijut2consulta/link.action?visao=anotado&idAto=127905",
        "captured_on": "2026-04-26",
    },
    {
        "jurisdiction": "Federal",
        "name": "PIS/Cofins",
        "tax": "PIS/Cofins",
        "file": "IN_RFB_2121_2022_PIS_COFINS_Parte2.txt",
        "title": "Instrução Normativa RFB nº 2.121/2022 - PIS/Pasep e Cofins",
        "official_url": "https://normas.receita.fazenda.gov.br/sijut2consulta/link.action?visao=anotado&idAto=127905",
        "captured_on": "2026-04-26",
    },
    {
        "jurisdiction": "Federal",
        "name": "PIS/Cofins",
        "tax": "PIS/Cofins",
        "file": "IN_RFB_2121_2022_PIS_COFINS_Parte3.txt",
        "title": "Instrução Normativa RFB nº 2.121/2022 - PIS/Pasep e Cofins",
        "official_url": "https://normas.receita.fazenda.gov.br/sijut2consulta/link.action?visao=anotado&idAto=127905",
        "captured_on": "2026-04-26",
    },
    {
        "jurisdiction": "Federal",
        "name": "PIS/Cofins-Importação",
        "tax": "PIS/Cofins-Importação",
        "file": "Lei_10865_2004_PIS_COFINS_Importacao.txt",
        "title": "Lei nº 10.865/2004 - PIS/Cofins-Importação",
        "official_url": "https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2004/lei/l10.865.htm",
        "captured_on": "2026-04-26",
    },
    {
        "jurisdiction": "Federal",
        "name": "PIS/Cofins",
        "tax": "PIS/Cofins",
        "file": "Lei_13097_2015_Reducao_Zero_PIS_COFINS.txt",
        "title": "Lei nº 13.097/2015 - Alíquota zero e regimes de PIS/Cofins",
        "official_url": "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13097.htm",
        "captured_on": "2026-04-26",
    },
    {
        "jurisdiction": "Federal",
        "name": "IPI",
        "tax": "IPI",
        "file": "Decreto_11158_2022_TIPI.txt",
        "title": "Decreto nº 11.158/2022 - TIPI",
        "official_url": "https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2022/decreto/d11158.htm",
        "captured_on": "2026-04-26",
    },
    {
        "jurisdiction": "Federal",
        "name": "IPI",
        "tax": "IPI",
        "repo_file": "data/legal_sources/federal/IN_RFB_2324_2026_IPI_Suspensao.txt",
        "file": "IN_RFB_2324_2026_IPI_Suspensao.txt",
        "title": "Instrucao Normativa RFB n. 2.324/2026 - suspensao do IPI",
        "official_url": "https://normas.receita.fazenda.gov.br/sijut2consulta/link.action?antigo=1&idAto=150886",
        "captured_on": "2026-05-25",
    },
    {
        "jurisdiction": "Federal",
        "name": "Reforma Tributária",
        "tax": "IBS/CBS",
        "file": "LC_214_2025_Compilada_IBS_CBS_IS.txt",
        "title": "Lei Complementar nº 214/2025 - IBS, CBS e Imposto Seletivo",
        "official_url": "https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214.htm",
        "captured_on": "2026-04-26",
    },
    {
        "jurisdiction": "Federal",
        "name": "Reforma Tributária",
        "tax": "CBS",
        "repo_file": "data/legal_sources/reforma_tributaria/Decreto_12955_2026_Regulamento_CBS.txt",
        "file": "Decreto_12955_2026_Regulamento_CBS.txt",
        "title": "Decreto nº 12.955/2026 - Regulamento da CBS",
        "official_url": "https://www.in.gov.br/en/web/dou/-/decreto-n-12.955-de-29-de-abril-de-2026-702415229",
        "captured_on": "2026-04-30",
    },
    {
        "jurisdiction": "Federal",
        "name": "Reforma Tributária",
        "tax": "IBS",
        "repo_file": "data/legal_sources/reforma_tributaria/Resolucao_CGIBS_6_2026_Regulamento_IBS.txt",
        "file": "Resolucao_CGIBS_6_2026_Regulamento_IBS.txt",
        "title": "Resolução CGIBS nº 6/2026 - Regulamento do IBS",
        "official_url": "https://www.cgibs.gov.br/upload/arquivos/202604/30084927-res-cgibs-n-6-30-abr-2026-regulamenta-o-ibs.pdf",
        "captured_on": "2026-04-30",
    },
    {
        "jurisdiction": "Federal",
        "name": "Reforma Tributária",
        "tax": "IBS/CBS",
        "repo_file": "data/legal_sources/reforma_tributaria/Tabela_CST_cClassTrib_IBS_CBS_2026_04_15.txt",
        "file": "Tabela_CST_cClassTrib_IBS_CBS_2026_04_15.txt",
        "title": "Tabela CST e cClassTrib do IBS e da CBS - 15/04/2026",
        "official_url": "https://dfe-portal.svrs.rs.gov.br/CFF/ClassificacaoTributaria",
        "captured_on": "2026-04-15",
    },
    {
        "jurisdiction": "Federal",
        "name": "Reforma Tributária",
        "tax": "IBS/CBS",
        "repo_file": "data/legal_sources/reforma_tributaria/Tabela_cCredPres_IBS_CBS_2025_12_12.txt",
        "file": "Tabela_cCredPres_IBS_CBS_2025_12_12.txt",
        "title": "Tabela de códigos de crédito presumido do IBS e da CBS - 12/12/2025",
        "official_url": "https://dfe-portal.svrs.rs.gov.br/CFF/TabelaCreditoPresumido",
        "captured_on": "2025-12-12",
    },
]


class PlainTextHTMLParser(HTMLParser):
    skip_tags = {"script", "style", "head"}

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.skip_stack: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in self.skip_tags:
            self.skip_stack.append(tag)
        if tag in {"p", "div", "br", "tr", "td", "li", "h1", "h2", "h3", "h4"} and not self.skip_stack:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in self.skip_stack:
            while self.skip_stack:
                current = self.skip_stack.pop()
                if current == tag:
                    break
        if tag in {"p", "div", "tr", "li", "h1", "h2", "h3", "h4"} and not self.skip_stack:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self.skip_stack:
            return
        if data.strip():
            self.parts.append(data)

    def text(self) -> str:
        return "\n".join(line.strip() for line in "".join(self.parts).splitlines() if line.strip())


def normalize(value: str) -> str:
    text = unicodedata.normalize("NFKD", value or "")
    text = text.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", text)).strip()


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


PAGE_MARKER_RE = re.compile(
    r"(?:=+\s*)?(?:PÁGINA|PAGINA|PÃ.?GINA)\s+\d+(?:\s*=+)?(?:\s+[A-Za-z0-9_.\\/-]+){0,10}",
    re.I,
)
GENERIC_SCOPE_PREFIX = normalize("Produto ou operação descrito literalmente no trecho legal")
BENEFIT_EFFECT_NEEDLES = [
    "isencao",
    "reducao de base",
    "credito presumido",
    "credito outorgado",
    "diferimento",
    "suspensao",
    "aliquota zero",
    "nao incidencia",
    "imunidade",
    "substituicao tributaria",
    "antecipacao",
    "monofasico",
    "ccredpres",
]
OPERATION_CONTEXT_NEEDLES = [
    "produto",
    "mercadoria",
    "operacao",
    "saida",
    "entrada",
    "venda",
    "importacao",
    "exportacao",
    "prestacao",
    "revenda",
    "fabricante",
    "produtor",
    "destinatario",
    "industrializacao",
]
NON_BENEFIT_NOISE_NEEDLES = [
    "auto de infracao",
    "penalidade",
    "multa",
    "obrigacao acessoria",
    "cadastro fiscal",
    "suspensao de inscricao",
    "cancelamento de inscricao",
    "gia st",
    "declaracao de conteudo eletronica",
    "nfcom",
    "livro fiscal",
    "escrituracao fiscal",
]
SCOPE_DOCUMENT_NOISE_NEEDLES = [
    "nota fiscal",
    "nota fiscal avulsa",
    "documento de arrecadacao",
    "declaracao da movimentacao",
    "dmd",
    "efd",
    "registro e110",
    "registro e111",
    "cod_aj_apur",
    "vl_tot_aj",
    "livros fiscais",
    "devera emitir",
    "devera ser emitida",
    "deverao apresentar",
    "informar mensalmente",
    "campo 02",
    "campo 08",
]


def sanitize_text(value: str) -> str:
    clean = unescape(value or "")
    clean = PAGE_MARKER_RE.sub(" ", clean)
    clean = re.sub(r"\[\s*\]", " ", clean)
    clean = clean.replace("\u00a0", " ")
    clean = re.sub(r"\s+", " ", clean)
    return clean.strip()


def compact(value: str, limit: int = 900) -> str:
    clean = sanitize_text(value)
    clean = " ".join(clean.split())
    if len(clean) <= limit:
        return clean
    return clean[: limit - 3].rsplit(" ", 1)[0] + "..."


def load_json(path: Path, fallback: object) -> object:
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def official_state_sources() -> dict[str, dict[str, dict]]:
    manifests: dict[str, dict[str, dict]] = {}
    for manifest in sorted((ROOT / "data" / "fontes-estaduais-curadas").rglob("manifest.json")):
        payload = load_json(manifest, {})
        uf = str(payload.get("uf", "")).upper()
        if not uf:
            continue
        manifests.setdefault(uf, {})
        for source in payload.get("fontes", []):
            if source.get("arquivo"):
                manifests[uf][source["arquivo"]] = source
            if source.get("id"):
                manifests[uf][source["id"]] = source
    return manifests


def state_statuses() -> dict:
    payload = load_json(ROOT / "data" / "state_curadoria.json", {})
    return payload.get("statuses", {}) if isinstance(payload, dict) else {}


def extract_header_meta(text: str) -> dict[str, str]:
    meta: dict[str, str] = {}
    for line in text.splitlines()[:20]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key_norm = normalize(key)
        value = value.strip()
        if key_norm.startswith("titulo"):
            meta["title"] = value
        elif key_norm.startswith("fonte publica") or key_norm.startswith("fonte"):
            meta["official_url"] = value
        elif key_norm.startswith("data da captura") or key_norm.startswith("captura"):
            meta["captured_on"] = value
        elif key_norm.startswith("tema"):
            meta["theme"] = value
        elif key_norm.startswith("status curadoria"):
            meta["curation_status"] = value
        elif key_norm.startswith("motivo quarentena"):
            meta["quarantine_reason"] = value
    return meta


def source_meta_from_doc(uf: str, doc: dict, manifest: dict[str, dict]) -> dict:
    path = Path(doc["path"])
    text = path.read_text(encoding="utf-8", errors="ignore")
    header = extract_header_meta(text)
    manifest_source = manifest.get(doc.get("file", ""), {}) or manifest.get(doc.get("source_id", ""), {})
    return {
        "jurisdiction": uf,
        "name": STATE_NAMES.get(uf, uf),
        "tax": "ICMS",
        "title": header.get("title") or manifest_source.get("titulo") or doc.get("title", ""),
        "official_url": header.get("official_url") or manifest_source.get("url") or doc.get("official_url", ""),
        "captured_on": header.get("captured_on") or manifest_source.get("data_captura") or manifest_source.get("capturado_em") or "2026-04-26",
        "curation_status": header.get("curation_status") or manifest_source.get("status_curadoria") or "",
        "quarantine_reason": header.get("quarantine_reason") or manifest_source.get("motivo_quarentena") or "",
        "source_file": doc.get("file", path.name),
        "source_path": path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path),
        "sha256": doc.get("sha256") or hashlib.sha256(path.read_bytes()).hexdigest(),
        "text": text,
    }


def federal_source_meta(config: dict) -> dict | None:
    if config.get("repo_file"):
        path = ROOT / config["repo_file"]
    else:
        path = BD_FEDERAL / config["file"]
    if not path.exists():
        return None
    return {
        **config,
        "source_file": config.get("file", path.name),
        "source_path": path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "text": path.read_text(encoding="utf-8", errors="ignore"),
    }


def goias_source_meta() -> dict | None:
    registry = load_json(ROOT / "data" / "legal_sources_registry.json", {})
    sources = registry.get("sources", []) if isinstance(registry, dict) else []
    anexo = next((item for item in sources if item.get("source_id") == "anexo-ix-go"), None)
    if not anexo:
        return None
    url = anexo.get("official_url", "")
    raw = b""
    text = ""
    fallback = ROOT / "estados" / "goias" / "legislacao" / "atos" / "anexo-ix-go.html"
    if fallback.exists():
        raw = fallback.read_bytes()
        parser = PlainTextHTMLParser()
        parser.feed(raw.decode("utf-8", errors="ignore"))
        text = parser.text()
    else:
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "RJC-Conhecimento/2.0"})
            with urllib.request.urlopen(request, timeout=45) as response:
                raw = response.read()
            html = raw.decode("latin-1", errors="ignore")
            parser = PlainTextHTMLParser()
            parser.feed(html)
            text = parser.text()
        except Exception:
            text = ""
    if not text:
        return None
    return {
        "jurisdiction": "GO",
        "name": "Goiás",
        "tax": "ICMS",
        "title": anexo.get("title", "Anexo IX do RCTE/GO - Benefícios fiscais"),
        "official_url": url,
        "captured_on": TODAY,
        "source_file": "ANEXO_09_Beneficio_Fiscal.htm",
        "source_path": url,
        "sha256": sha256_bytes(raw or text.encode("utf-8")),
        "text": text,
    }


def source_candidates() -> list[dict]:
    manifests = official_state_sources()
    statuses = state_statuses()
    sources: list[dict] = []
    goias = goias_source_meta()
    if goias:
        sources.append(goias)
    for uf in sorted(STATE_NAMES):
        status = statuses.get(uf, {})
        if uf == "GO" or not status.get("publish_deep"):
            continue
        for doc in collect_state_documents(uf):
            category = doc.get("category", "")
            if category not in {"ICMS_BENEFICIOS", "ICMS_ANEXOS", "ICMS_ST", "RICMS", "INSTRUCOES_NORMATIVAS", "OUTROS", "ICMS_LEIS"}:
                continue
            try:
                meta = source_meta_from_doc(uf, doc, manifests.get(uf, {}))
            except Exception:
                continue
            if meta.get("official_url") and meta.get("text"):
                sources.append(meta)
    for config in FEDERAL_FILES:
        meta = federal_source_meta(config)
        if meta:
            sources.append(meta)
    return sources


_BENEFIT_NEEDLES_NORM: list[str] | None = None
_STALE_NEEDLES_NORM: list[str] | None = None


def benefit_needles_norm() -> list[str]:
    global _BENEFIT_NEEDLES_NORM
    if _BENEFIT_NEEDLES_NORM is None:
        _BENEFIT_NEEDLES_NORM = [normalize(needle) for needle in BENEFIT_NEEDLES]
    return _BENEFIT_NEEDLES_NORM


def stale_needles_norm() -> list[str]:
    global _STALE_NEEDLES_NORM
    if _STALE_NEEDLES_NORM is None:
        _STALE_NEEDLES_NORM = [normalize(needle) for needle in STALE_NEEDLES]
    return _STALE_NEEDLES_NORM


def has_benefit_text(value: str) -> bool:
    low = normalize(value)
    return any(needle in low for needle in benefit_needles_norm())


def is_stale(value: str) -> bool:
    low = normalize(value)
    return any(needle in low for needle in stale_needles_norm())


def extract_ncm(value: str) -> list[str]:
    if not re.search(r"\b(NCM|TIPI|NBM|Nomenclatura|posição|posições|Capítulo|Capítulos|código|códigos)\b", value, re.I):
        return []
    codes = re.findall(r"(?<!\d)(?:\d{4}\.\d{2}\.\d{2}|\d{4}\.\d{2}|\d{2}\.\d{2}|\d{8}|\d{4}\.\d|\d{4}|Cap[ií]tulos?\s+\d{1,2}|posi[cç][aã]o\s+\d{2}\.\d{2})(?!\d)", value, re.I)
    cleaned: list[str] = []
    for code in codes:
        code = " ".join(code.split())
        digits = re.sub(r"\D", "", code)
        if len(digits) == 4 and digits.startswith(("19", "20")):
            continue
        if code not in cleaned:
            cleaned.append(code)
    return cleaned[:24]


def extract_cest(value: str) -> list[str]:
    return sorted(set(re.findall(r"\b\d{2}\.\d{3}\.\d{2}\b", value)))[:24]


def extract_cbenef(value: str) -> list[str]:
    return sorted(set(re.findall(r"\b(?:AC|AL|AP|AM|BA|CE|DF|ES|GO|MA|MT|MS|MG|PA|PB|PR|PE|PI|RJ|RN|RS|RO|RR|SC|SP|SE|TO)\d{6}\b", value, flags=re.I)))[:24]


def extract_cst(value: str) -> list[str]:
    direct = re.findall(r"\bCST\s*(00|10|20|30|40|41|50|51|60|70|90)\b", value, flags=re.I)
    return sorted({f"CST {item}" for item in direct})[:12]


def extract_cclasstrib(value: str) -> list[str]:
    return sorted(set(re.findall(r"\b\d{6}\b", value)))[:24] if "cClassTrib" in value or "cclasstrib" in normalize(value) else []


def split_sentences(value: str) -> list[str]:
    text = " ".join(value.split())
    pieces = re.split(r"(?<=[.;:])\s+", text)
    return [piece.strip() for piece in pieces if len(piece.strip()) > 18]


def is_transport_cfop_noise(excerpt: str, identifiers: list[str]) -> bool:
    if identifiers:
        return False
    low = normalize(excerpt)
    if "declaracao de conteudo eletronica" in low or "nfcom" in low:
        return True
    if "transportador autonomo" not in low and "onde iniciado o servico" not in low:
        return False
    cfops = re.findall(r"\b[1-7]\.\d{3}\b", excerpt)
    return len(cfops) >= 2


def sentences_matching(value: str, needles: list[str], default: str) -> str:
    low_needles = [normalize(needle) for needle in needles]
    hits = []
    for sentence in split_sentences(value):
        sentence_norm = normalize(sentence)
        if any(needle in sentence_norm for needle in low_needles):
            hits.append(sentence)
    return compact(" ".join(hits[:3]), 500) if hits else default


def infer_benefit_type(value: str) -> str:
    low = normalize(value)
    mapping = [
        ("crédito outorgado/presumido", ["credito outorgado", "credito presumido", "ccredpres"]),
        ("redução de base de cálculo", ["reducao de base", "base de calculo e reduzida"]),
        ("isenção", ["isencao", "isentas", "isento"]),
        ("diferimento", ["diferimento", "diferido"]),
        ("suspensão", ["suspensao", "suspenso"]),
        ("alíquota zero", ["aliquota zero", "aliquota 0"]),
        ("monofásico", ["monofasic"]),
        ("não incidência/imunidade", ["nao incidencia", "imunidade"]),
        ("substituição tributária/antecipação", ["substituicao tributaria", "antecipacao", "cest"]),
        ("código de benefício/documento fiscal", ["cbenef", "cst", "cclasstrib"]),
    ]
    for label, needles in mapping:
        if any(needle in low for needle in needles):
            return label
    return "tratamento tributário específico"


def classify_group(value: str) -> tuple[str, str]:
    group_id, group_title, _evidence = classify_group_details(value)
    return group_id, group_title


def keyword_in_normalized_text(keyword: str, normalized_text: str) -> bool:
    normalized_keyword = normalize(keyword)
    if not normalized_keyword:
        return False
    if " " in normalized_keyword:
        return normalized_keyword in normalized_text
    return bool(re.search(rf"(?<![a-z0-9]){re.escape(normalized_keyword)}(?![a-z0-9])", normalized_text))


def classify_group_details(value: str) -> tuple[str, str, list[str]]:
    low = normalize(value)
    best = (0, "geral", "Geral e operação tributária", [])
    for sector in BENEFIT_SECTOR_DEFS:
        evidence = [keyword for keyword in sector["keywords"] if keyword_in_normalized_text(keyword, low)]
        score = len(evidence)
        if score > best[0]:
            best = (score, sector["id"], sector["title"], evidence[:8])
    return best[1], best[2], best[3]


def has_benefit_effect(value: str) -> bool:
    low = normalize(value)
    return any(needle in low for needle in BENEFIT_EFFECT_NEEDLES)


def has_noise_profile(value: str) -> bool:
    low = normalize(value)
    return any(needle in low for needle in NON_BENEFIT_NOISE_NEEDLES)


def has_scope_document_noise(value: str) -> bool:
    low = normalize(value)
    return any(needle in low for needle in SCOPE_DOCUMENT_NOISE_NEEDLES)


def is_table_of_contents_noise(value: str) -> bool:
    low = normalize(value)
    if "modelos de documentos fiscaisdisciplinados" in low or "parte 3 dos modelos de documentos" in low:
        return True
    return low.count("capitulo") >= 5 and low.count(" art ") < 2


def is_generic_scope(value: str) -> bool:
    low = normalize(value)
    if not low:
        return True
    if low.startswith(GENERIC_SCOPE_PREFIX):
        return True
    generic = {
        "aplicacao definida pela operacao descrita no dispositivo transcrito",
        "produto ou operacao descrito literalmente no trecho legal",
    }
    return low in generic


def clean_scope_value(value: str) -> str:
    clean = sanitize_text(value)
    clean = re.sub(
        r"^(?:\d{1,4}(?:,\s*[A-ZXLVI]+)?\s+)?(?:\d{2}/\d{2}/\d{4}\s+){1,3}(?:RICMS/\d+\s+)?(?:\d+(?:\.\d+)?\s+)?(?:Decreto\s+[\d./-]+\s*)?",
        "",
        clean,
    )
    clean = re.sub(r"^\d{1,4},\s*[A-ZXLVI]+\s+", "", clean)
    clean = re.sub(r"^(?:\d+(?:\.\d+)?\s+)?Decreto\s+[\d./-]+\s+", "", clean)
    return clean.strip(" ;,")


def is_incomplete_scope(value: str) -> bool:
    low = normalize(value)
    if not low:
        return True
    if low.endswith((" e", " ou", " de", " da", " do", " a", " o", " para", " com")):
        return True
    return low in {"produtor rural", "cooperativas", "associacoes", "fabricantes", "contribuintes"}


def scope_has_operational_detail(value: str, identifiers: list[str]) -> bool:
    if identifiers:
        return True
    value = clean_scope_value(value)
    low = normalize(value)
    if is_generic_scope(value):
        return False
    if is_incomplete_scope(value):
        return False
    if len(low.split()) < 5:
        return False
    if low.startswith(("considerando que", "para fruicao do beneficio", "contribuintes que")) and "produto" not in low and "mercadoria" not in low:
        return False
    return any(normalize(needle) in low for needle in OPERATION_CONTEXT_NEEDLES)


def validity_status(source: dict, excerpt: str) -> str:
    raw_end = str(source.get("validity_end", "") or "").strip()
    if raw_end:
        return f"vigencia ate {raw_end}"
    low = normalize(excerpt)
    if "ate 31 12" in low or "ate 30 11" in low or "efeitos ate" in low:
        return "vigencia exige conferencia do periodo citado no trecho"
    if "ibs" in low or "cbs" in low or "reforma tributaria" in low:
        return "transicao IBS/CBS"
    return "vigente conforme ato capturado"


def iso_date(value: object) -> str:
    text = str(value or "").strip()
    candidate = text if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text) else ""
    if not candidate:
        match = re.search(r"\b(\d{4})[-/](\d{2})[-/](\d{2})\b", text)
        candidate = "-".join(match.groups()) if match else ""
    if candidate:
        try:
            return date.fromisoformat(candidate).isoformat()
        except ValueError:
            pass
    return ""


def is_material_sha256(value: object) -> bool:
    return bool(re.fullmatch(r"[0-9a-fA-F]{64}", str(value or "").strip()))


def official_url_identity(value: object) -> tuple[str, str] | None:
    text = str(value or "").strip()
    try:
        parsed = urlparse(text)
    except ValueError:
        return None
    host = (parsed.hostname or "").casefold().rstrip(".")
    if parsed.scheme != "https" or not host:
        return None
    if not host.endswith((".gov.br", ".leg.br", ".jus.br")):
        return None
    if (parsed.path or "/") == "/" and not parsed.query:
        return None
    return host, text


def material_text(value: object, minimum: int = 12) -> bool:
    text = compact(str(value or ""), 4000).strip()
    if len(text) < minimum:
        return False
    return normalize(text) not in {"none", "nenhum", "na", "n a", "nao aplicavel", "indeterminado"}


def source_reference_date(source: dict) -> str:
    """Return only a proven legal publication date.

    Capture/build/editorial dates are metadata and must never become legal dates.
    """
    return iso_date(source.get("publication_date"))


def material_publication_blockers(source: dict) -> list[str]:
    """List missing material evidence; publication is fail-closed."""
    blockers: list[str] = []
    if source.get("publishable") is not True:
        blockers.append("fonte sem autorização material publishable=true")
    publication_date = iso_date(source.get("publication_date"))
    validity_start = iso_date(source.get("validity_start"))
    effectiveness_start = iso_date(source.get("effectiveness_start"))
    if not publication_date:
        blockers.append("publicação AUSENTE ou sem prova")
    if not validity_start:
        blockers.append("início de vigência AUSENTE ou sem prova")
    if not effectiveness_start:
        blockers.append("início de eficácia AUSENTE ou sem prova")
    if publication_date and validity_start and publication_date > validity_start:
        blockers.append("início de vigência anterior à publicação sem prova específica")
    if publication_date and effectiveness_start and publication_date > effectiveness_start:
        blockers.append("início de eficácia anterior à publicação sem prova específica")
    source_url = official_url_identity(source.get("official_url"))
    if not source_url:
        blockers.append("URL oficial material inválida ou sem localizador")
    if not is_material_sha256(source.get("sha256")):
        blockers.append("hash SHA-256 material da fonte inválido")
    provenance = source.get("field_provenance")
    if not isinstance(provenance, dict):
        blockers.append("field_provenance ausente")
    else:
        for field in ("publication_date", "validity_start", "effectiveness_start"):
            item = provenance.get(field)
            if not isinstance(item, dict):
                blockers.append(f"proveniência ausente para {field}")
                continue
            required = {
                "card_id", "field", "value", "final_url", "official_domain",
                "redirects", "http_status", "mime", "body_sha256",
                "literal_excerpt", "locator", "normalization_rule",
            }
            if required - set(item):
                blockers.append(f"proveniência incompleta para {field}")
                continue
            if not material_text(item.get("card_id"), 8):
                blockers.append(f"card_id material inválido para {field}")
            if item.get("field") != field:
                blockers.append(f"campo de proveniência divergente para {field}")
            if iso_date(item.get("value")) != iso_date(source.get(field)):
                blockers.append(f"valor de proveniência divergente para {field}")
            final_identity = official_url_identity(item.get("final_url"))
            official_domain = str(item.get("official_domain", "")).casefold().rstrip(".")
            if not final_identity or official_domain != (final_identity[0] if final_identity else ""):
                blockers.append(f"identidade oficial inválida para {field}")
            redirects = item.get("redirects")
            if not isinstance(redirects, list) or any(not isinstance(value, str) for value in redirects):
                blockers.append(f"cadeia de redirects inválida para {field}")
            if item.get("http_status") != 200:
                blockers.append(f"HTTP material inválido para {field}")
            mime = str(item.get("mime", "")).casefold().split(";", 1)[0].strip()
            if mime not in {"text/html", "text/plain", "application/pdf", "application/xml", "text/xml"}:
                blockers.append(f"MIME material inválido para {field}")
            if not is_material_sha256(item.get("body_sha256")):
                blockers.append(f"hash material inválido para {field}")
            if not material_text(item.get("literal_excerpt"), 20):
                blockers.append(f"trecho literal material inválido para {field}")
            if not material_text(item.get("locator"), 4):
                blockers.append(f"localizador material inválido para {field}")
            if not material_text(item.get("normalization_rule"), 8):
                blockers.append(f"regra de normalização material inválida para {field}")
    receipt_ids = source.get("independent_http_receipt_ids")
    material_receipts = {
        str(value).strip() for value in receipt_ids or [] if material_text(value, 8)
    } if isinstance(receipt_ids, list) else set()
    if len(material_receipts) < 2:
        blockers.append("duas capturas HTTP nativas independentes ausentes")
    if not material_text(source.get("verification_receipt_id"), 8):
        blockers.append("recibo material de verificação ausente")
    if not iso_date(source.get("verified_on")):
        blockers.append("verificado_em sem revalidação material")
    jurisdiction = str(source.get("jurisdiction", ""))
    if len(jurisdiction) == 2 and source.get("tax") == "ICMS":
        status = source.get("internalization_status")
        if status not in {"COMPROVADA", "DISPENSADA_COM_FUNDAMENTO"}:
            blockers.append("internalização NÃO_COMPROVADA")
        if not isinstance(source.get("internalization_evidence"), dict):
            blockers.append("prova específica de internalização ausente")
    return blockers


def normalized_card_status(source: dict, excerpt: str) -> str:
    status_text = normalize(validity_status(source, excerpt))
    raw_end = iso_date(source.get("validity_end"))
    if raw_end and raw_end < TODAY:
        return "historico"
    if "exige conferencia" in status_text:
        return "a_revalidar"
    if material_publication_blockers(source):
        return "a_revalidar"
    return "vigente"


def confidence_score(label: str) -> float:
    return {
        "alta": 0.95,
        "media": 0.82,
        "baixa": 0.40,
    }.get(normalize(label), 0.40)


def infer_act_type(title: str) -> str:
    low = normalize(title)
    if "lei complementar" in low:
        return "Lei Complementar"
    if "lei" in low:
        return "Lei"
    if "decreto" in low:
        return "Decreto"
    if "instrucao normativa" in low:
        return "Instrução Normativa"
    if "resolucao" in low:
        return "Resolução"
    if "portaria" in low:
        return "Portaria"
    if "convenio" in low:
        return "Convênio"
    if "ajuste" in low:
        return "Ajuste"
    if "protocolo" in low:
        return "Protocolo"
    if "tabela" in low:
        return "Tabela oficial"
    return "Ato oficial"


def infer_act_number(title: str) -> str:
    patterns = [
        r"(?:n[ºo.]|n\.)\s*([\d.]+(?:/\d{4})?)",
        r"\b(?:lei|decreto|resolu[cç][aã]o|portaria|conv[eê]nio|ajuste|protocolo)\s+([\d.]+(?:/\d{4})?)",
    ]
    for pattern in patterns:
        match = re.search(pattern, title, flags=re.I)
        if match:
            return match.group(1)
    return ""


def transition_rt_label(tax: str, excerpt: str) -> str:
    low_tax = normalize(tax)
    low = normalize(f"{tax} {excerpt}")
    if "ibs" in low_tax or "cbs" in low_tax:
        return "n/a - tributo da Reforma Tributaria; conferir regime proprio de IBS/CBS."
    if "icms" in low_tax or "iss" in low_tax:
        return "coexiste; ICMS/ISS permanecem no regime antigo durante a transicao e serao extintos ate 2033."
    if "pis" in low_tax or "cofins" in low_tax:
        return "coexiste; PIS/Cofins convivem com teste CBS/IBS em 2026 e CBS plena a partir de 2027."
    if "ipi" in low_tax:
        return "coexiste; IPI deve ser lido com a transicao RT-2026 e regras especificas de manutencao/reducao."
    if "reforma tributaria" in low:
        return "n/a - regra vinculada a IBS/CBS/IS."
    return "n/a"


def benefit_contract_fields(
    source: dict,
    excerpt: str,
    benefit_type: str,
    product: str,
    scope_summary: str,
    conditions: str,
    risk: str,
) -> dict:
    publication = source_reference_date(source)
    start = iso_date(source.get("validity_start"))
    effectiveness = iso_date(source.get("effectiveness_start"))
    end = iso_date(source.get("validity_end"))
    status = normalized_card_status(source, excerpt)
    act = {
        "tipo": infer_act_type(source.get("title", "")),
        "num": infer_act_number(source.get("title", "")),
        "titulo": source.get("title", ""),
        "url": source.get("official_url", ""),
        "resolve": bool(source.get("act_identity_proven") is True),
    }
    validity = {
        "publicacao": publication,
        "inicio_vigencia": start,
        "inicio_eficacia": effectiveness,
        "fim_vigencia": end or None,
        "status": status,
    }
    proof = {
        "url": source.get("official_url", ""),
        "internalizacao_status": source.get("internalization_status", "NÃO_COMPROVADA"),
        "internalizacao_evidencia": source.get("internalization_evidence"),
        "descricao": proof_for(benefit_type, excerpt),
    }
    return {
        "beneficio": benefit_type,
        "mercadoria_servico": product if not is_generic_scope(product) else scope_summary,
        "ente_uf": source.get("jurisdiction", ""),
        "ato": act,
        "ato_oficial": act,
        "publicacao": publication,
        "inicio_vigencia": start,
        "inicio_eficacia": effectiveness,
        "fim_vigencia": end or None,
        "vigencia": validity,
        "condicao": conditions,
        "prova_documental": proof,
        "transicao_rt": transition_rt_label(source.get("tax", ""), excerpt),
        "risco": risk,
        "status": status,
        "verificado_em": iso_date(source.get("verified_on")),
        "field_provenance": source.get("field_provenance", {}),
        "verification_receipt_id": source.get("verification_receipt_id", ""),
        "provenance": "ato_oficial",
    }


def build_scope_summary(
    product: str,
    operation: str,
    identifiers: list[str],
    ncm: list[str],
    cest: list[str],
    cbenef: list[str],
    cst: list[str],
    cclasstrib: list[str],
) -> str:
    parts: list[str] = []
    product = clean_scope_value(product)
    operation = clean_scope_value(operation)
    if product and not is_generic_scope(product):
        parts.append(product)
    elif operation and not is_generic_scope(operation):
        parts.append(operation)
    code_bits = []
    if ncm:
        code_bits.append("NCM/TIPI " + ", ".join(ncm[:8]))
    if cest:
        code_bits.append("CEST " + ", ".join(cest[:8]))
    if cbenef:
        code_bits.append("cBenef " + ", ".join(cbenef[:8]))
    if cst:
        code_bits.append("CST " + ", ".join(cst[:8]))
    if cclasstrib:
        code_bits.append("cClassTrib " + ", ".join(cclasstrib[:8]))
    if code_bits:
        parts.append("; ".join(code_bits))
    if not parts and identifiers:
        parts.append(", ".join(identifiers[:12]))
    return compact(" | ".join(parts), 650)


def classification_confidence(
    excerpt: str,
    product: str,
    operation: str,
    identifiers: list[str],
    group_evidence: list[str],
) -> str:
    if identifiers and scope_has_operational_detail(product, identifiers):
        return "alta"
    if identifiers:
        return "media"
    if scope_has_operational_detail(product, identifiers) and (group_evidence or scope_has_operational_detail(operation, identifiers)):
        return "media"
    if has_benefit_effect(excerpt) and scope_has_operational_detail(product, identifiers):
        return "media"
    return "baixa"


def rejection_reasons(
    excerpt: str,
    legal_excerpt: str,
    product: str,
    operation: str,
    identifiers: list[str],
    confidence: str,
) -> list[str]:
    reasons: list[str] = []
    if len(legal_excerpt) < 80:
        reasons.append("trecho legal curto demais para publicacao")
    if is_table_of_contents_noise(excerpt):
        reasons.append("trecho parece indice/sumario de anexo, nao dispositivo operacional")
    if not has_benefit_effect(excerpt):
        reasons.append("sem efeito tributario favorecido claro")
    if not scope_has_operational_detail(product, identifiers) and not scope_has_operational_detail(operation, identifiers):
        reasons.append("sem produto, mercadoria, operacao ou codigo fiscal suficientemente explicito")
    if has_noise_profile(excerpt) and not identifiers:
        reasons.append("perfil de obrigacao acessoria, cadastro, penalidade ou documento sem codigo de beneficio")
    if has_scope_document_noise(product) and not re.search(r"\b(sa[ií]das?|entradas?|vendas?|importa[cç][aã]o|exporta[cç][aã]o)\b", product, re.I):
        reasons.append("escopo extraido descreve obrigacao documental, nao mercadoria ou operacao beneficiada")
    if has_scope_document_noise(product) and not has_benefit_effect(product):
        reasons.append("escopo documental sem efeito favorecido no proprio campo publicado")
    if confidence == "baixa":
        reasons.append("confianca baixa na classificacao automatica")
    return reasons


def extract_operation(value: str) -> str:
    return sentences_matching(
        value,
        ["operação", "operações", "saída", "saídas", "venda", "importação", "exportação", "prestação", "revenda", "entrada"],
        "Aplicação definida pela operação descrita no dispositivo transcrito.",
    )


def extract_legal_basis(value: str, title: str) -> str:
    patterns = [
        r"\bArt(?:igo)?\.?\s*\d+[ºo]?(?:-[A-Z])?",
        r"\bCl[áa]usula\s+\w+",
        r"\bItem\s+\d+",
        r"\bAnexo\s+[IVXLCDM\d]+",
    ]
    for pattern in patterns:
        match = re.search(pattern, value, flags=re.I)
        if match:
            return f"{title} - {match.group(0)}"
    return title


def legal_windows(text: str) -> list[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    indexes = []
    for index, line in enumerate(lines):
        window = " ".join(lines[max(0, index - 3): min(len(lines), index + 5)])
        if has_benefit_text(window) and (
            extract_ncm(window)
            or extract_cest(window)
            or extract_cbenef(window)
            or extract_cst(window)
            or extract_cclasstrib(window)
            or re.search(r"\b(produtos?|mercadorias?|opera[cç][oõ]es?|sa[ií]das?|vendas?|importa[cç][aã]o|exporta[cç][aã]o)\b", window, re.I)
        ):
            indexes.append(index)
    windows = []
    seen = set()
    for index in indexes:
        start = index
        for pos in range(index, max(-1, index - 28), -1):
            if re.match(r"^(Art(?:igo)?\.?\s*\d+|CAP[ÍI]TULO|SE[ÇC][ÃA]O|SUBSE[ÇC][ÃA]O|ANEXO|ITEM\s+\d+)", lines[pos], flags=re.I):
                start = pos
                break
        end = min(len(lines), index + 18)
        for pos in range(index + 1, min(len(lines), index + 60)):
            if re.match(r"^Art(?:igo)?\.?\s*\d+", lines[pos], flags=re.I):
                end = pos
                break
        excerpt = " ".join(lines[start:end])
        key = normalize(excerpt[:700])
        if key and key not in seen and not is_stale(excerpt):
            seen.add(key)
            windows.append(excerpt)
    return windows


def legal_windows(text: str) -> list[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    norm_lines = [normalize(line) for line in lines]
    benefit_needles = benefit_needles_norm()
    context_needles = [normalize(needle) for needle in OPERATION_CONTEXT_NEEDLES]

    def is_header(line: str) -> bool:
        low = normalize(line)
        return bool(re.match(r"^(art(?:igo)? \d+|capitulo|secao|subsecao|anexo|item \d+)", low))

    def is_next_article(line: str) -> bool:
        return bool(re.match(r"^art(?:igo)? \d+", normalize(line)))

    indexes = []
    for index in range(len(lines)):
        start_window = max(0, index - 3)
        end_window = min(len(lines), index + 5)
        norm_window = " ".join(norm_lines[start_window:end_window])
        if not any(needle in norm_window for needle in benefit_needles):
            continue
        raw_window = " ".join(lines[start_window:end_window])
        if (
            extract_ncm(raw_window)
            or extract_cest(raw_window)
            or extract_cbenef(raw_window)
            or extract_cst(raw_window)
            or extract_cclasstrib(raw_window)
            or any(needle in norm_window for needle in context_needles)
        ):
            indexes.append(index)

    windows = []
    seen = set()
    for index in indexes:
        start = index
        for pos in range(index, max(-1, index - 28), -1):
            if is_header(lines[pos]):
                start = pos
                break
        end = min(len(lines), index + 18)
        for pos in range(index + 1, min(len(lines), index + 60)):
            if is_next_article(lines[pos]):
                end = pos
                break
        excerpt = sanitize_text(" ".join(lines[start:end]))
        key = normalize(excerpt[:700])
        if key and key not in seen and not is_stale(excerpt):
            seen.add(key)
            windows.append(excerpt)
    return windows


def table_line_windows(text: str) -> list[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    windows = []
    seen = set()
    for index, line in enumerate(lines):
        if not (extract_cbenef(line) or extract_cst(line) or extract_cclasstrib(line)):
            continue
        window = " ".join(lines[max(0, index - 1): min(len(lines), index + 3)])
        if has_benefit_text(window) and not is_stale(window):
            window = sanitize_text(window)
            key = normalize(window[:700])
            if key not in seen:
                seen.add(key)
                windows.append(window)
    return windows


def source_quarantine_reasons(source: dict) -> list[str]:
    status = normalize(str(source.get("curation_status", "")))
    if not status:
        return []
    quarantine_markers = ("a validar", "quarentena", "link 404", "404", "bloqueado")
    if not any(marker in status for marker in quarantine_markers):
        return []
    reason = str(source.get("quarantine_reason") or "").strip()
    if not reason:
        reason = f"fonte marcada como {source.get('curation_status')}; nao publicar ate revalidacao oficial."
    return [reason]


def evaluate_entry(source: dict, excerpt: str, seq: int) -> tuple[dict | None, list[str]]:
    excerpt = sanitize_text(excerpt)
    source_reasons = source_quarantine_reasons(source)
    if source_reasons:
        return None, source_reasons
    ncm = extract_ncm(excerpt)
    cest = extract_cest(excerpt)
    cbenef = extract_cbenef(excerpt)
    cst = extract_cst(excerpt)
    cclasstrib = extract_cclasstrib(excerpt)
    identifiers = [*ncm, *cest, *cbenef, *cst, *cclasstrib]
    if is_transport_cfop_noise(excerpt, identifiers):
        return None, ["perfil de CFOP/transporte sem codigo de beneficio"]
    if not (ncm or cest or cbenef or cst or cclasstrib or re.search(r"\bprodutos?|mercadorias?|opera[cç][oõ]es?|sa[ií]das?|vendas?|importa[cç][aã]o|exporta[cç][aã]o\b", excerpt, re.I)):
        return None, ["sem codigo fiscal ou contexto operacional no trecho"]
    benefit_type = infer_benefit_type(excerpt)
    legal_basis = extract_legal_basis(excerpt, source["title"])
    product = sentences_matching(
        excerpt,
        ["produto", "produtos", "mercadoria", "mercadorias", "classificados", "código", "códigos", "NCM", "CEST", "TIPI"],
        "Produto ou operação descrito literalmente no trecho legal.",
    )
    product = clean_scope_value(product)
    operation = clean_scope_value(extract_operation(excerpt))
    scope_summary = build_scope_summary(product, operation, identifiers, ncm, cest, cbenef, cst, cclasstrib)
    group_id, group_name, group_evidence = classify_group_details(scope_summary)
    legal_excerpt = compact(excerpt, 1600)
    conditions = sentences_matching(
        excerpt,
        ["desde que", "condicion", "somente", "quando", "destinad", "habilita", "credenci", "mediante", "termo", "declara"],
        "Aplicar somente dentro do produto, operação, sujeito, período e documento descritos no trecho legal.",
    )
    prohibitions = sentences_matching(
        excerpt,
        ["vedad", "não se aplica", "nao se aplica", "exceto", "exclu", "salvo", "não alcança", "nao alcanca"],
        "Não ampliar por analogia para produto, destinatário ou operação fora do texto legal.",
    )
    confidence_label = classification_confidence(excerpt, product, operation, identifiers, group_evidence)
    confidence = confidence_score(confidence_label)
    reasons = rejection_reasons(excerpt, legal_excerpt, product, operation, identifiers, confidence_label)
    reasons.extend(material_publication_blockers(source))
    if reasons:
        return None, reasons
    entry_id = f"{source['jurisdiction'].lower()}-{hashlib.sha1((source['source_file'] + excerpt).encode('utf-8')).hexdigest()[:12]}"
    risk = risk_for(benefit_type)
    contract = benefit_contract_fields(
        source=source,
        excerpt=excerpt,
        benefit_type=benefit_type,
        product=product,
        scope_summary=scope_summary,
        conditions=conditions,
        risk=risk,
    )
    return {
        "id": entry_id,
        "jurisdiction": source["jurisdiction"],
        "name": source["name"],
        "tax": source["tax"],
        "benefit_group_id": group_id,
        "benefit_group": group_name,
        "benefit_group_evidence": group_evidence,
        "benefit_group_confidence": "alta" if len(group_evidence) >= 2 else ("media" if group_evidence else "baixa"),
        "benefit_type": benefit_type,
        "scope_summary": scope_summary,
        "goods_or_services": product if not is_generic_scope(product) else scope_summary,
        "product_or_operation": product,
        "ncm": ncm,
        "cest": cest,
        "cbenef": cbenef,
        "cst": cst,
        "cclasstrib": cclasstrib,
        "operation": operation,
        "conditions": conditions,
        "prohibitions": prohibitions,
        "validity_start": source.get("validity_start", ""),
        "validity_end": source.get("validity_end", ""),
        "validity_status": validity_status(source, excerpt),
        "modifying_act": source.get("modifying_act", ""),
        "transition_status": infer_transition_status(source, excerpt),
        "legal_nature": infer_legal_nature(benefit_type, excerpt),
        "source_kind": source.get("source_kind", "ato normativo"),
        "legal_basis": legal_basis,
        "legal_description": compact(excerpt, 700),
        "legal_excerpt": legal_excerpt,
        "source_title": source["title"],
        "source_file": source["source_file"],
        "source_path": source["source_path"],
        "official_url": source["official_url"],
        "captured_on": source.get("captured_on", ""),
        "sha256": source["sha256"],
        "validation_status": "validado",
        "validation_basis": [
            "texto legal local capturado de fonte oficial",
            "trecho contém tratamento tributário favorecido e campo operacional",
            "escopo publicado foi extraído do próprio trecho legal",
            "registro publicado sem pendência pública",
        ],
        "classification_confidence": confidence,
        "classification_confidence_label": confidence_label,
        "audience_status": "humano e IA",
        "publishable": not material_publication_blockers(source),
        "proof_required": proof_for(benefit_type, excerpt),
        "risk": risk,
        "seq": seq,
        **contract,
    }, []


def build_entry(source: dict, excerpt: str, seq: int) -> dict | None:
    entry, _reasons = evaluate_entry(source, excerpt, seq)
    return entry


def quarantine_entry(source: dict, excerpt: str, seq: int, reasons: list[str]) -> dict | None:
    excerpt = sanitize_text(excerpt)
    if len(excerpt) < 60:
        return None
    entry_id = f"q-{source['jurisdiction'].lower()}-{hashlib.sha1((source['source_file'] + excerpt).encode('utf-8')).hexdigest()[:12]}"
    return {
        "id": entry_id,
        # Internal-only fields used for deterministic deduplication. The writer
        # deliberately serializes no quarantine entries into the public tree.
        "jurisdiction": source.get("jurisdiction", ""),
        "source_file": source.get("source_file", ""),
        "legal_excerpt": compact(excerpt, 900),
        "source_fingerprint": hashlib.sha256(str(source.get("sha256", "")).encode("utf-8")).hexdigest(),
        "quarantine_reasons": sorted(set(reasons)),
        "validation_status": "a_validar",
        "audience_status": "interno-nao-publicar",
        "public_impact": "tombstone sem conteúdo material",
        "seq": seq,
    }


def infer_transition_status(source: dict, excerpt: str) -> str:
    low = normalize(source.get("tax", "") + " " + source.get("title", "") + " " + excerpt)
    if "ibs" in low or "cbs" in low or "imposto seletivo" in low or "reforma tributaria" in low:
        if "2026" in low or "transicao" in low or "transitorio" in low:
            return "regra de reforma/transicao"
        return "regra de IBS/CBS"
    return "regra vigente atual"


def infer_legal_nature(benefit_type: str, excerpt: str) -> str:
    low = normalize(benefit_type + " " + excerpt)
    if "imunidade" in low or "nao incidencia" in low:
        return "fora do campo de incidencia ou imunidade"
    if "aliquota zero" in low:
        return "aliquota zero"
    if "isencao" in low:
        return "isencao"
    if "reducao" in low:
        return "reducao de carga"
    if "credito" in low:
        return "credito fiscal"
    if "diferimento" in low or "suspensao" in low:
        return "adiamento ou suspensao da exigencia"
    if "regime" in low:
        return "regime especifico ou diferenciado"
    return "tratamento tributario especifico"


def proof_for(benefit_type: str, excerpt: str) -> str:
    base = "XML/NF-e, cadastro fiscal do produto, memória de enquadramento, escrituração e dispositivo legal transcrito."
    low = normalize(benefit_type + " " + excerpt)
    if "cbenef" in low or "cst" in low:
        return "XML/NF-e com CST/cBenef compatível, cadastro de benefício, tabela da UF, dispositivo legal e EFD."
    if "substituicao" in low or "cest" in low:
        return "XML/NF-e, NCM, CEST, MVA/pauta quando houver, guia de recolhimento, EFD e memória de ST."
    if "export" in low or "drawback" in low:
        return "NF-e, DU-E/DI/DUIMP quando aplicável, contrato, invoice, ato concessório e comprovação de destino."
    if "credito" in low:
        return "XML/NF-e, EFD, ajuste de apuração, memória de crédito, termo/credenciamento quando exigido e prova da condição."
    return base


def risk_for(benefit_type: str) -> str:
    low = normalize(benefit_type)
    if "credito" in low:
        return "Apropriar crédito sem cumprir condição, vedação, termo ou segregação exigida pela norma."
    if "reducao" in low:
        return "Transformar redução de base em alíquota menor sem demonstrar carga efetiva e fundamento."
    if "isencao" in low:
        return "Ampliar isenção por semelhança comercial para produto, sujeito ou operação não alcançados."
    if "diferimento" in low:
        return "Perder o evento que encerra o diferimento e deixar imposto sem recolhimento ou sem prova."
    if "substituicao" in low:
        return "Aplicar ST por descrição aproximada sem conferir NCM/CEST, operação, destinatário e protocolo vigente."
    if "aliquota zero" in low or "monofasico" in low:
        return "Classificar pelo nome comercial sem validar NCM, etapa da cadeia e CST aplicável."
    return "Aplicar o tratamento fora do recorte literal do dispositivo legal."


def build_validated_benefits() -> dict:
    entries: list[dict] = []
    quarantine: list[dict] = []
    seen: set[str] = set()
    seen_quarantine: set[str] = set()
    for source in source_candidates():
        seq = 0
        excerpts = legal_windows(source["text"]) + table_line_windows(source["text"])
        for excerpt in excerpts:
            seq += 1
            entry, reasons = evaluate_entry(source, excerpt, seq)
            if not entry:
                quarantined = quarantine_entry(source, excerpt, seq, reasons)
                if quarantined:
                    q_key = "|".join([
                        quarantined["jurisdiction"],
                        quarantined["source_file"],
                        normalize(quarantined["legal_excerpt"])[:180],
                    ])
                    if q_key not in seen_quarantine:
                        seen_quarantine.add(q_key)
                        quarantine.append(quarantined)
                continue
            fingerprint = "|".join([
                entry["jurisdiction"],
                entry["source_file"],
                entry["benefit_type"],
                normalize(entry["scope_summary"])[:160],
                ",".join(entry["ncm"]),
                ",".join(entry["cest"]),
                ",".join(entry["cbenef"]),
                ",".join(entry["cst"]),
            ])
            if fingerprint in seen:
                continue
            seen.add(fingerprint)
            entries.append(entry)
    entries.sort(key=lambda item: (item["jurisdiction"], item["benefit_group"], item["benefit_type"], item["source_file"], item["seq"]))
    quarantine.sort(key=lambda item: (item["jurisdiction"], item["source_file"], item["seq"]))
    return {
        "schema": "rjc-validated-benefits-crosswalk-v3",
        "generated_on": TODAY,
        "editorial_status": "matriz publica composta somente por itens com escopo operacional extraido do proprio texto legal",
        "validation_rule": "publicar somente quando houver fonte oficial, trecho legal em tela, tratamento tributario favorecido, campo operacional extraido e confianca media ou alta",
        "summary": {
            "entries": len(entries),
            "quarantined_entries": len(quarantine),
            "jurisdictions": len({item["jurisdiction"] for item in entries}),
            "with_ncm": sum(1 for item in entries if item["ncm"]),
            "with_cest": sum(1 for item in entries if item["cest"]),
            "with_cbenef": sum(1 for item in entries if item["cbenef"]),
            "with_cst": sum(1 for item in entries if item["cst"]),
            "high_confidence": sum(1 for item in entries if float(item.get("classification_confidence", 0)) >= 0.90),
            "medium_confidence": sum(1 for item in entries if 0.80 <= float(item.get("classification_confidence", 0)) < 0.90),
            "oldest_verified_on": min((item.get("verificado_em") for item in entries if item.get("verificado_em")), default=None),
            "editorial_date": min((item.get("verificado_em") for item in entries if item.get("verificado_em")), default=None),
            "editorial_date_source": "min_verificado_em",
        },
        "entries": entries,
        "quarantine": quarantine,
    }


if __name__ == "__main__":
    payload = build_validated_benefits()
    print(json.dumps(payload["summary"], ensure_ascii=False, indent=2))
