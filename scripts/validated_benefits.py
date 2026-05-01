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
from html.parser import HTMLParser
from pathlib import Path


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


def compact(value: str, limit: int = 900) -> str:
    clean = " ".join((value or "").split())
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
    low = normalize(value)
    best = (0, "geral", "Geral e operação tributária")
    for sector in BENEFIT_SECTOR_DEFS:
        score = sum(1 for keyword in sector["keywords"] if normalize(keyword) in low)
        if score > best[0]:
            best = (score, sector["id"], sector["title"])
    return best[1], best[2]


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
    code_or_operation = re.compile(
        r"\b(NCM|TIPI|NBM|CEST|cBenef|CST|cClassTrib|produtos?|mercadorias?|opera[cÃ§][oÃµ]es?|sa[iÃ­]das?|vendas?|importa[cÃ§][aÃ£]o|exporta[cÃ§][aÃ£]o)\b",
        re.I,
    )
    header = re.compile(
        r"^(Art(?:igo)?\.?\s*\d+|CAP[ÃI]TULO|SE[Ã‡C][ÃƒA]O|SUBSE[Ã‡C][ÃƒA]O|ANEXO|ITEM\s+\d+)",
        re.I,
    )
    next_article = re.compile(r"^Art(?:igo)?\.?\s*\d+", re.I)
    indexes = []
    for index in range(len(lines)):
        start_window = max(0, index - 3)
        end_window = min(len(lines), index + 5)
        norm_window = " ".join(norm_lines[start_window:end_window])
        if not any(needle in norm_window for needle in benefit_needles):
            continue
        raw_window = " ".join(lines[start_window:end_window])
        if code_or_operation.search(raw_window):
            indexes.append(index)

    windows = []
    seen = set()
    for index in indexes:
        start = index
        for pos in range(index, max(-1, index - 28), -1):
            if header.match(lines[pos]):
                start = pos
                break
        end = min(len(lines), index + 18)
        for pos in range(index + 1, min(len(lines), index + 60)):
            if next_article.match(lines[pos]):
                end = pos
                break
        excerpt = " ".join(lines[start:end])
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
            key = normalize(window[:700])
            if key not in seen:
                seen.add(key)
                windows.append(window)
    return windows


def build_entry(source: dict, excerpt: str, seq: int) -> dict | None:
    ncm = extract_ncm(excerpt)
    cest = extract_cest(excerpt)
    cbenef = extract_cbenef(excerpt)
    cst = extract_cst(excerpt)
    cclasstrib = extract_cclasstrib(excerpt)
    if not (ncm or cest or cbenef or cst or cclasstrib or re.search(r"\bprodutos?|mercadorias?|opera[cç][oõ]es?|sa[ií]das?|vendas?|importa[cç][aã]o|exporta[cç][aã]o\b", excerpt, re.I)):
        return None
    group_id, group_name = classify_group(excerpt)
    benefit_type = infer_benefit_type(excerpt)
    legal_basis = extract_legal_basis(excerpt, source["title"])
    product = sentences_matching(
        excerpt,
        ["produto", "produtos", "mercadoria", "mercadorias", "classificados", "código", "códigos", "NCM", "CEST", "TIPI"],
        "Produto ou operação descrito literalmente no trecho legal.",
    )
    if not (ncm or cest or cbenef or cst or cclasstrib) and normalize(product).startswith("produto ou opera"):
        return None
    legal_excerpt = compact(excerpt, 1600)
    if len(legal_excerpt) < 80:
        return None
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
    entry_id = f"{source['jurisdiction'].lower()}-{hashlib.sha1((source['source_file'] + excerpt).encode('utf-8')).hexdigest()[:12]}"
    return {
        "id": entry_id,
        "jurisdiction": source["jurisdiction"],
        "name": source["name"],
        "tax": source["tax"],
        "benefit_group_id": group_id,
        "benefit_group": group_name,
        "benefit_type": benefit_type,
        "product_or_operation": product,
        "ncm": ncm,
        "cest": cest,
        "cbenef": cbenef,
        "cst": cst,
        "cclasstrib": cclasstrib,
        "operation": extract_operation(excerpt),
        "conditions": conditions,
        "prohibitions": prohibitions,
        "validity_start": source.get("validity_start", source.get("captured_on", "")),
        "validity_end": source.get("validity_end", ""),
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
            "trecho contém tratamento tributário e campo operacional",
            "registro publicado sem pendência pública",
        ],
        "proof_required": proof_for(benefit_type, excerpt),
        "risk": risk_for(benefit_type),
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
    seen: set[str] = set()
    for source in source_candidates():
        seq = 0
        excerpts = legal_windows(source["text"]) + table_line_windows(source["text"])
        for excerpt in excerpts:
            seq += 1
            entry = build_entry(source, excerpt, seq)
            if not entry:
                continue
            fingerprint = "|".join([
                entry["jurisdiction"],
                entry["source_file"],
                entry["benefit_type"],
                normalize(entry["product_or_operation"])[:120],
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
    return {
        "schema": "rjc-validated-benefits-crosswalk-v3",
        "generated_on": TODAY,
        "editorial_status": "matriz publica composta somente por itens validados em texto legal de fonte oficial",
        "validation_rule": "publicar somente quando houver fonte oficial, trecho legal em tela, tratamento tributario e campo operacional extraido",
        "summary": {
            "entries": len(entries),
            "jurisdictions": len({item["jurisdiction"] for item in entries}),
            "with_ncm": sum(1 for item in entries if item["ncm"]),
            "with_cest": sum(1 for item in entries if item["cest"]),
            "with_cbenef": sum(1 for item in entries if item["cbenef"]),
            "with_cst": sum(1 for item in entries if item["cst"]),
        },
        "entries": entries,
    }


if __name__ == "__main__":
    payload = build_validated_benefits()
    print(json.dumps(payload["summary"], ensure_ascii=False, indent=2))
