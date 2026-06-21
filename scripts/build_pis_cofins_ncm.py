#!/usr/bin/env python3
"""Build the PIS/Cofins by NCM dataset from official primary sources.

The script has two outputs:
- Deep evidence files under G:/Meu Drive/RJC/BD_LEGISLACAO/PIS_COFINS_NCM.
- Public, validated NDJSON/JSON files under data/pis-cofins.

Rows are intentionally conservative. A public row must contain an official URL,
HTTP 200, explicit NCM/TIPI context, a treatment term and a validity envelope.
Uncertain rows go to quarantine.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from collections import Counter
from dataclasses import dataclass
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable

import requests


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DIR = ROOT / "data" / "pis-cofins"
TODAY = os.environ.get("RJC_VERIFICADO_EM", date.today().isoformat())
DEFAULT_DEEP_ROOT = Path(r"G:\Meu Drive\RJC\BD_LEGISLACAO\PIS_COFINS_NCM")
DEEP_ROOT = Path(os.environ.get("RJC_PIS_COFINS_NCM_DB", str(DEFAULT_DEEP_ROOT)))

RAW_DIR = DEEP_ROOT / "fontes-brutas"
NORM_DIR = DEEP_ROOT / "fontes-normalizadas"
LOG_DIR = DEEP_ROOT / "logs"

PUBLIC_NDJSON = PUBLIC_DIR / "ncm.ndjson"
PUBLIC_INDEX = PUBLIC_DIR / "ncm-index.json"
QUARANTINE_NDJSON = PUBLIC_DIR / "quarentena.ndjson"
DEEP_INVENTORY = DEEP_ROOT / "inventario-fontes.ndjson"
DEEP_CANDIDATES = DEEP_ROOT / "extracoes-candidatas.ndjson"

USER_AGENT = "Mozilla/5.0 (RJC-Conhecimento/2.0; contato: portal aberto)"


class TextHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style", "noscript"}:
            self.skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript"} and self.skip_depth:
            self.skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self.skip_depth and data.strip():
            self.parts.append(data.strip())

    def text(self) -> str:
        return "\n".join(self.parts)


@dataclass(frozen=True)
class SourceSpec:
    source_id: str
    tipo: str
    numero: str
    titulo: str
    url: str
    publicacao: str
    inicio_vigencia: str
    inicio_eficacia: str
    fim_vigencia: str | None
    papel: str
    setores: tuple[str, ...]
    allow_public: bool = True


SOURCES: tuple[SourceSpec, ...] = (
    SourceSpec(
        "lei-10147-2000",
        "Lei",
        "10.147/2000",
        "Lei 10.147/2000 - PIS/Cofins monofasico para produtos especificos",
        "https://www.planalto.gov.br/ccivil_03/leis/l10147.htm",
        "2000-12-22",
        "2000-12-22",
        "2001-05-01",
        None,
        "dispositiva",
        ("farmaceutico", "perfumaria", "higiene"),
    ),
    SourceSpec(
        "lei-10485-2002",
        "Lei",
        "10.485/2002",
        "Lei 10.485/2002 - PIS/Cofins setor automotivo e autopecas",
        "https://www.planalto.gov.br/ccivil_03/leis/2002/l10485.htm",
        "2002-07-04",
        "2002-07-04",
        "2002-11-01",
        None,
        "dispositiva",
        ("automotivo", "autopecas", "maquinas"),
    ),
    SourceSpec(
        "lei-10865-2004",
        "Lei",
        "10.865/2004",
        "Lei 10.865/2004 - PIS/Cofins-Importacao e reducoes a zero",
        "https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2004/lei/l10.865.htm",
        "2004-04-30",
        "2004-04-30",
        "2004-05-01",
        None,
        "dispositiva",
        ("importacao", "aeronautico", "saude", "acessibilidade", "agro"),
    ),
    SourceSpec(
        "lei-10925-2004",
        "Lei",
        "10.925/2004",
        "Lei 10.925/2004 - reducao a zero de PIS/Cofins para produtos agropecuarios e correlatos",
        "https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2004/lei/l10.925.htm",
        "2004-07-26",
        "2004-07-26",
        "2004-08-01",
        None,
        "dispositiva",
        ("agro", "alimentos", "insumos agropecuarios"),
    ),
    SourceSpec(
        "lei-12839-2013",
        "Lei",
        "12.839/2013",
        "Lei 12.839/2013 - reducao a zero para azeites e alteracoes correlatas",
        "https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2013/Lei/L12839.htm",
        "2013-07-10",
        "2013-07-10",
        "2013-07-10",
        None,
        "dispositiva_alteradora",
        ("alimentos",),
    ),
    SourceSpec(
        "lei-13097-2015",
        "Lei",
        "13.097/2015",
        "Lei 13.097/2015 - aliquota zero e regimes especificos de PIS/Cofins",
        "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/L13097.htm",
        "2015-01-20",
        "2015-01-20",
        "2015-01-20",
        None,
        "dispositiva_alteradora",
        ("bebidas", "saude", "acessibilidade", "outros"),
    ),
    SourceSpec(
        "decreto-5195-2004",
        "Decreto",
        "5.195/2004",
        "Decreto 5.195/2004 - reducao a zero vinculada a Lei 10.925/2004",
        "https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2004/decreto/d5195.htm",
        "2004-08-27",
        "2004-08-27",
        "2004-08-27",
        None,
        "regulamentar",
        ("agro", "insumos agropecuarios"),
    ),
    SourceSpec(
        "decreto-5630-2005",
        "Decreto",
        "5.630/2005",
        "Decreto 5.630/2005 - reducao a zero vinculada a Lei 10.925/2004",
        "https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2005/decreto/d5630.htm",
        "2005-12-23",
        "2005-12-23",
        "2005-12-23",
        None,
        "regulamentar",
        ("agro", "insumos agropecuarios"),
    ),
    SourceSpec(
        "decreto-6426-2008",
        "Decreto",
        "6.426/2008",
        "Decreto 6.426/2008 - aliquota zero PIS/Cofins para produtos quimicos, farmaceuticos e saude",
        "https://www.planalto.gov.br/ccivil_03/_ato2007-2010/2008/decreto/d6426.htm",
        "2008-04-08",
        "2008-04-08",
        "2008-04-08",
        None,
        "regulamentar",
        ("saude", "farmaceutico", "quimicos"),
    ),
    SourceSpec(
        "decreto-6707-2008",
        "Decreto",
        "6.707/2008",
        "Decreto 6.707/2008 - regime de bebidas",
        "https://www.planalto.gov.br/ccivil_03/_ato2007-2010/2008/Decreto/D6707.htm",
        "2008-12-24",
        "2008-12-24",
        "2009-01-01",
        "2015-05-01",
        "historica_regulamentar",
        ("bebidas",),
        allow_public=False,
    ),
    SourceSpec(
        "decreto-8442-2015",
        "Decreto",
        "8.442/2015",
        "Decreto 8.442/2015 - regime de bebidas e revogacao do Decreto 6.707/2008",
        "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/decreto/D8442.htm",
        "2015-04-30",
        "2015-05-01",
        "2015-05-01",
        None,
        "regulamentar",
        ("bebidas",),
    ),
    SourceSpec(
        "decreto-12991-2026",
        "Decreto",
        "12.991/2026",
        "Decreto 12.991/2026 - reducao de PIS/Cofins sobre querosene de aviacao e biodiesel",
        "https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2026/decreto/d12991.htm",
        "2026-06-18",
        "2026-06-18",
        "2026-06-18",
        None,
        "regulamentar",
        ("combustiveis", "aviacao", "biodiesel"),
    ),
    SourceSpec(
        "lei-15394-2026",
        "Lei",
        "15.394/2026",
        "Lei 15.394/2026 - creditos e isencao de PIS/Cofins para residuos e aparas",
        "https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2026/lei/L15394.htm",
        "2026-06-16",
        "2026-06-16",
        "2026-06-16",
        None,
        "dispositiva",
        ("residuos", "reciclagem"),
    ),
    SourceSpec(
        "portaria-rfb-688-2026",
        "Portaria",
        "RFB 688/2026",
        "Portaria RFB 688/2026 - transparencia ativa de beneficios tributarios",
        "https://normas.receita.fazenda.gov.br/sijut2consulta/link.action?idAto=151652",
        "2026-05-29",
        "2026-05-29",
        "2026-05-29",
        None,
        "inventario_controle",
        ("dirbi", "transparencia"),
        allow_public=False,
    ),
)

BENEFIT_RE = re.compile(
    r"(reduzid[ao]s?\s+a\s+zero|al[ií]quota\s+0|al[ií]quota\s+zero|ficam?\s+sujeit[ao]s?|"
    r"monof[aá]sic|incid[eê]ncia\s+concentrada|suspens[aoã]|isen[cç][aã]o|isenta|cr[eé]dito\s+presumido)",
    re.I,
)
NCM_CONTEXT_RE = re.compile(
    r"(NCM|TIPI|Nomenclatura\s+Comum|classificad[oa]s?|posi[cç][aã]o|posi[cç][oõ]es|c[oó]digo(?:s)?|Cap[ií]tulo)",
    re.I,
)
CODE_RE = re.compile(
    r"(?<![\d/])(\d{4}\.\d{2}\.\d{2}|\d{4}\.\d{2}\.\d|\d{4}\.\d{2}|\d{2}\.\d{2}|\d{8}|\d{6}|\d{4})(?![\d/])"
)
ARTICLE_RE = re.compile(r"(?=Art\.?\s*\d+[ºo]?)", re.I)
STALE_RE = re.compile(r"(Revogado|Revogada|sem efic[aá]cia|vig[eê]ncia encerrada)", re.I)


def ensure_dirs() -> None:
    for path in (PUBLIC_DIR, RAW_DIR, NORM_DIR, LOG_DIR):
        path.mkdir(parents=True, exist_ok=True)


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def decode_response(raw: bytes, encoding: str | None) -> str:
    candidates = [encoding or "", "utf-8", "latin-1", "cp1252"]
    best = ""
    for enc in candidates:
        if not enc:
            continue
        try:
            text = raw.decode(enc, errors="ignore")
        except Exception:
            continue
        if not best or text.count("\ufffd") < best.count("\ufffd"):
            best = text
    return best


def html_to_text(html: str) -> str:
    parser = TextHTMLParser()
    parser.feed(html)
    lines = []
    for line in parser.text().splitlines():
        cleaned = " ".join(line.split())
        if cleaned:
            lines.append(cleaned)
    text = "\n".join(lines)
    # Drop common WAF/client-side fragments that Planalto occasionally appends.
    return re.sub(r"\*?\s*\(function\(\)\{var f5_cspm=.*$", "", text, flags=re.S)


def fetch_source(spec: SourceSpec) -> tuple[int | str, bytes, str]:
    last_error = ""
    for attempt in range(1, 4):
        try:
            response = requests.get(
                spec.url,
                headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml,*/*"},
                timeout=45,
            )
            status = response.status_code
            raw = response.content
            html = decode_response(raw, response.encoding)
            return status, raw, html_to_text(html)
        except Exception as exc:  # network flakiness must not publish rows
            last_error = str(exc)
            time.sleep(1.5 * attempt)
    return "ERR", b"", last_error


def clean(value: object) -> str:
    return " ".join(str(value or "").split())


TREATMENT_LABELS = {
    "aliquota_zero": "aliquota zero",
    "monofasico": "monofasico",
    "credito_presumido": "credito presumido",
    "suspensao": "suspensao",
    "isencao": "isencao",
    "coeficiente_reducao": "coeficiente/reducao",
    "tratamento_especifico": "tratamento especifico",
}


def display(value: object) -> str:
    return clean(str(value or "nao especificado").replace("_", " "))


def treatment_label_for(treatment: str) -> str:
    return TREATMENT_LABELS.get(treatment, display(treatment))


def compact(value: str, limit: int = 900) -> str:
    text = clean(value)
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def ncm_digits(code: str) -> str:
    return re.sub(r"\D", "", code or "")


def ncm_level(code: str) -> str:
    digits = ncm_digits(code)
    if len(digits) == 8:
        return "subitem"
    if len(digits) == 7:
        return "item_tipi"
    if len(digits) == 6:
        return "subposicao"
    if len(digits) == 4:
        return "posicao"
    if len(digits) == 2:
        return "capitulo"
    return "codigo_tipi_ncm"


def valid_code(code: str, surrounding: str, before: str, after: str) -> bool:
    digits = ncm_digits(code)
    if len(digits) not in {4, 6, 7, 8}:
        return False
    if set(digits) == {"0"}:
        return False
    if code.isdigit() and (before.endswith(",") or before.endswith(".")):
        return False
    if re.search(r"R\$\s*0[,\.]?$", before, re.I):
        return False
    if code.isdigit() and re.search(r"(mil[eé]simo|cent[eé]simo|d[eé]cimo|grama|litro|R\$)", surrounding, re.I):
        return False
    # Avoid dates, law numbers and article numbers.
    if len(digits) == 4 and 1900 <= int(digits) <= 2099 and "." not in code:
        return False
    low = surrounding.lower()
    if "lei n" in low and code in surrounding:
        return False
    return bool(NCM_CONTEXT_RE.search(surrounding))


def extract_codes(excerpt: str) -> list[str]:
    text = clean(excerpt)
    codes: list[str] = []
    seen: set[str] = set()
    for match in CODE_RE.finditer(text):
        code = match.group(1)
        start = max(0, match.start() - 140)
        end = min(len(text), match.end() + 140)
        surrounding = text[start:end]
        before = text[max(0, match.start() - 8):match.start()]
        after = text[match.end():match.end() + 8]
        if not valid_code(code, surrounding, before, after):
            continue
        key = ncm_digits(code)
        if key not in seen:
            seen.add(key)
            codes.append(code)
    return codes


def article_windows(text: str) -> list[str]:
    compacted = clean(text)
    starts = [m.start() for m in ARTICLE_RE.finditer(compacted)]
    windows: list[str] = []
    if not starts:
        return [compacted]
    starts.append(len(compacted))
    for pos, start in enumerate(starts[:-1]):
        end = starts[pos + 1]
        chunk = compacted[start:end]
        if len(chunk) >= 120:
            windows.append(chunk)
    return windows


def treatment_for(excerpt: str, source: SourceSpec) -> str:
    low = excerpt.lower()
    if "crédito presumido" in low or "credito presumido" in low:
        return "credito_presumido"
    if "suspens" in low:
        return "suspensao"
    if "isenta" in low or "isencao" in low or "isenção" in low:
        return "isencao"
    if "reduzid" in low and ("zero" in low or "0" in low):
        return "aliquota_zero"
    if "alíquota zero" in low or "aliquota zero" in low or "alíquota 0" in low or "aliquota 0" in low:
        return "aliquota_zero"
    if source.source_id in {"lei-10147-2000", "lei-10485-2002"} or "monof" in low:
        return "monofasico"
    if "coeficiente" in low and "redu" in low:
        return "coeficiente_reducao"
    return "tratamento_especifico"


def operation_for(excerpt: str) -> str:
    low = excerpt.lower()
    has_import = "importa" in low or "cofins-importa" in low or "pis/pasep-importa" in low
    has_sale = "venda" in low or "mercado interno" in low or "receita bruta" in low
    if has_import and has_sale:
        return "mercado_interno_e_importacao"
    if has_import:
        return "importacao"
    if has_sale:
        return "mercado_interno"
    return "nao_especificado"


def chain_stage_for(excerpt: str) -> str:
    low = excerpt.lower()
    stages = []
    if "fabricante" in low or "industrializa" in low or "industrial" in low:
        stages.append("fabricante_industrial")
    if "importador" in low or "importa" in low:
        stages.append("importador")
    if "atacadista" in low:
        stages.append("atacadista")
    if "varejista" in low:
        stages.append("varejista")
    if "pessoa jurídica industrial" in low or "pessoa juridica industrial" in low:
        stages.append("adquirente_industrial")
    return "_e_".join(dict.fromkeys(stages)) if stages else "nao_especificado"


def sector_for(source: SourceSpec, excerpt: str) -> str:
    low = excerpt.lower()
    if "aeronave" in low or "querosene de avia" in low:
        return "aviacao"
    if "biodiesel" in low or "combust" in low:
        return "combustiveis"
    if "farmac" in low or "medicament" in low:
        return "farmaceutico"
    if "hospital" in low or "saude" in low or "saúde" in low or "clinica" in low or "clínica" in low:
        return "saude"
    if "fertiliz" in low or "defensiv" in low or "agro" in low:
        return "insumos_agropecuarios"
    if "veiculo" in low or "autopec" in low or "maquinas" in low or "máquinas" in low:
        return "automotivo_maquinas"
    if "bebida" in low or "cerveja" in low:
        return "bebidas"
    return source.setores[0] if source.setores else "federal"


def sentence_for_code(excerpt: str, code: str) -> str:
    text = clean(excerpt)
    idx = text.find(code)
    if idx < 0:
        return compact(text, 220)
    start = max(0, text.rfind(".", 0, idx))
    semi = text.rfind(";", 0, idx)
    start = max(start, semi)
    end_candidates = [p for p in (text.find(".", idx), text.find(";", idx)) if p > idx]
    end = min(end_candidates) if end_candidates else min(len(text), idx + 260)
    fragment = compact(text[start + 1:end + 1], 320)
    if len(fragment) < 45:
        fragment = compact(text[max(0, idx - 180):min(len(text), idx + 360)], 420)
    return fragment


def confidence_for(excerpt: str, source: SourceSpec, code: str) -> float:
    score = 0.74
    if source.allow_public:
        score += 0.08
    if BENEFIT_RE.search(excerpt):
        score += 0.08
    if NCM_CONTEXT_RE.search(excerpt):
        score += 0.05
    if len(ncm_digits(code)) >= 6:
        score += 0.03
    if STALE_RE.search(excerpt):
        score -= 0.20
    return round(min(score, 0.97), 2)


def status_for(source: SourceSpec, excerpt: str) -> str:
    if source.fim_vigencia and source.fim_vigencia < TODAY:
        return "historico"
    if STALE_RE.search(excerpt):
        return "a_validar"
    if source.inicio_eficacia > TODAY:
        return "a_validar"
    return "vigente"


def reason_for_quarantine(row: dict) -> str:
    reasons = []
    if row["ato_oficial"]["http_status"] != 200:
        reasons.append("link_primario_nao_200")
    if row["classification_confidence"] < 0.80:
        reasons.append("classification_confidence_baixa")
    if row["status"] == "a_validar":
        reasons.append("vigencia_ou_redacao_a_validar")
    if not row["ncm"]["codigo"]:
        reasons.append("ncm_ausente")
    if "portaria-rfb" in row["source_id"]:
        reasons.append("fonte_de_inventario_nao_dispositiva")
    if not reasons:
        reasons.append("revisao_humana_pendente")
    return ";".join(reasons)


def build_rows_for_source(spec: SourceSpec, status: int | str, text: str, raw_hash: str, norm_hash: str) -> tuple[list[dict], list[dict]]:
    public_rows: list[dict] = []
    quarantine: list[dict] = []
    windows = article_windows(text)
    for seq, excerpt in enumerate(windows, start=1):
        if not BENEFIT_RE.search(excerpt):
            continue
        codes = extract_codes(excerpt)
        if not codes:
            # Keep source/article candidates with benefit terms but no NCM out of public indices.
            candidate_id = hashlib.sha1(f"{spec.source_id}|{seq}|sem-ncm".encode("utf-8")).hexdigest()[:16]
            quarantine.append({
                "id": f"q-pcncm-{candidate_id}",
                "source_id": spec.source_id,
                "motivo": "descricao_sem_ncm_ou_ncm_nao_extraido",
                "ato": f"{spec.tipo} {spec.numero}",
                "official_url": spec.url,
                "trecho_legal": compact(excerpt, 1000),
                "publishable": False,
                "verificado_em": TODAY,
            })
            continue
        for code in codes:
            treatment = treatment_for(excerpt, spec)
            sector = sector_for(spec, excerpt)
            operation = operation_for(excerpt)
            chain_stage = chain_stage_for(excerpt)
            status_label = status_for(spec, excerpt)
            confidence = confidence_for(excerpt, spec, code)
            row_hash = hashlib.sha1(
                "|".join([spec.source_id, str(seq), ncm_digits(code), treatment, excerpt[:220]]).encode("utf-8")
            ).hexdigest()[:16]
            source_line = sentence_for_code(excerpt, code)
            resumo_operacional = compact(
                " ".join([
                    f"NCM {code} ({ncm_level(code)}) com {treatment_label_for(treatment)} de PIS/Cofins.",
                    f"Setor {display(sector)}; operacao {display(operation)}; etapa da cadeia {display(chain_stage)}.",
                    f"Fonte primaria {spec.tipo} {spec.numero}.",
                    "Aplicar somente se produto, sujeito, etapa, operacao e documento fiscal coincidirem com o dispositivo legal.",
                    f"Recorte legal: {source_line}",
                ]),
                900,
            )
            leitura_humana = {
                "pergunta_de_uso": "Este NCM tem tratamento de PIS/Cofins diferente da regra habitual?",
                "resposta_curta": resumo_operacional,
                "como_validar": [
                    "Conferir o NCM/TIPI no cadastro do produto e no documento fiscal.",
                    "Ler o trecho legal, o artigo e o ato oficial primario antes de aplicar.",
                    "Conferir sujeito, etapa da cadeia, operacao, CST e EFD-Contribuicoes.",
                    "Nao aplicar se houver divergencia de produto, destinatario, finalidade ou periodo.",
                ],
                "nao_usar_sem": [
                    "fonte oficial primaria HTTP 200",
                    "envelope de vigencia e eficacia",
                    "documento fiscal/XML ou documento de importacao quando aplicavel",
                    "memoria de enquadramento por produto",
                ],
            }
            pesquisa_texto = compact(
                " ".join([
                    code,
                    ncm_digits(code),
                    ncm_level(code),
                    resumo_operacional,
                    spec.tipo,
                    spec.numero,
                    spec.titulo,
                    spec.source_id,
                    sector,
                    operation,
                    chain_stage,
                    treatment,
                    status_label,
                    source_line,
                    excerpt,
                ]),
                2600,
            )
            row = {
                "schema": "rjc-pis-cofins-ncm-v1",
                "id": f"pcncm-{row_hash}",
                "source_id": spec.source_id,
                "lote_id": f"pis-cofins-ncm-{TODAY[:7]}",
                "ncm": {
                    "codigo": code,
                    "digitos": ncm_digits(code),
                    "nivel": ncm_level(code),
                    "descricao_tipi": "",
                    "status": "confirmado_no_trecho_legal",
                    "tipi_versao": "a_validar",
                    "ex": "Ex" if re.search(rf"{re.escape(code)}\s+Ex", excerpt, re.I) else None,
                },
                "mercadoria_servico": source_line,
                "resumo_operacional": resumo_operacional,
                "pesquisa_texto": pesquisa_texto,
                "leitura_humana": leitura_humana,
                "setor": sector,
                "aplicacao": operation,
                "tratamento": treatment,
                "tributos": ["PIS/Pasep", "Cofins"],
                "operacao": operation,
                "etapa_cadeia": chain_stage,
                "regime_sujeito": "conforme_dispositivo_legal",
                "aliquota": {
                    "tipo": "zero" if treatment == "aliquota_zero" else treatment,
                    "pis": 0 if treatment == "aliquota_zero" else None,
                    "cofins": 0 if treatment == "aliquota_zero" else None,
                    "formula": "conforme trecho legal e ato oficial",
                },
                "ato_oficial": {
                    "tipo": spec.tipo,
                    "numero": spec.numero,
                    "titulo": spec.titulo,
                    "artigo": f"janela_artigo_{seq}",
                    "inciso": None,
                    "anexo": None,
                    "url": spec.url,
                    "http_status": status,
                    "resolve": status == 200,
                },
                "fundamento_primario": {
                    "tipo": "lei_decreto" if spec.tipo in {"Lei", "Decreto"} else "ato_rfb",
                    "id": spec.source_id,
                    "url": spec.url,
                },
                "fonte_consolidada": {
                    "tipo": "IN RFB 2.121/2022",
                    "uso": "apoio_nao_autonomo",
                },
                "trecho_legal": compact(excerpt, 1600),
                "trecho_hash": f"sha256:{sha256_text(excerpt)}",
                "publicacao": spec.publicacao,
                "inicio_vigencia": spec.inicio_vigencia,
                "inicio_eficacia": spec.inicio_eficacia,
                "fim_vigencia": spec.fim_vigencia,
                "vigencia": {
                    "publicacao": spec.publicacao,
                    "inicio_vigencia": spec.inicio_vigencia,
                    "inicio_eficacia": spec.inicio_eficacia,
                    "fim_vigencia": spec.fim_vigencia,
                    "status": status_label,
                },
                "validity_status": status_label,
                "status": status_label,
                "condicoes": [
                    "Aplicar somente ao produto/codigo, operacao, sujeito e etapa descritos no trecho legal.",
                    "Conferir cadastro de produto, NCM/TIPI, documento fiscal e EFD-Contribuicoes antes de aplicar.",
                ],
                "vedacoes": [
                    "Nao ampliar por analogia para NCM, produto, etapa da cadeia ou destinatario fora do texto legal.",
                ],
                "prova_documental": [
                    "link oficial primario",
                    "trecho legal capturado",
                    "cadastro do produto/NCM",
                    "XML/NF-e ou DI/DUIMP quando aplicavel",
                    "EFD-Contribuicoes e memoria de enquadramento",
                ],
                "cst_entrada_saida": {
                    "pis_entrada": None,
                    "pis_saida": None,
                    "cofins_entrada": None,
                    "cofins_saida": None,
                    "fonte": "a_validar_em_tabela_sped",
                },
                "transicao_cbs": {
                    "status": "coexiste",
                    "referencia": "LC 214/2025; PIS/Cofins coexistem com teste CBS/IBS em 2026 e CBS plena a partir de 2027.",
                },
                "risco": "Alto se usado apenas por semelhanca de NCM; a etapa da cadeia e as condicoes do dispositivo governam o tratamento.",
                "provenance": {
                    "origem": "ato_oficial",
                    "metodo_extracao": "crawler_oficial_artigo_ncm",
                    "raw_sha256": raw_hash,
                    "normalized_sha256": norm_hash,
                    "capturado_em": TODAY,
                    "verificado_em": TODAY,
                },
                "classification_confidence": confidence,
                "validation_status": "validado" if confidence >= 0.80 and status_label in {"vigente", "historico"} and spec.allow_public else "a_validar",
                "publishable": confidence >= 0.80 and status == 200 and status_label in {"vigente", "historico"} and spec.allow_public,
                "verificado_em": TODAY,
            }
            if row["publishable"]:
                public_rows.append(row)
            else:
                qrow = {**row, "id": "q-" + row["id"], "motivo": reason_for_quarantine(row), "publishable": False}
                quarantine.append(qrow)
    return public_rows, quarantine


def write_ndjson(path: Path, rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def build_index(rows: list[dict], quarantine: list[dict], inventory: list[dict]) -> dict:
    by_treatment = Counter(row["tratamento"] for row in rows)
    by_sector = Counter(row["setor"] for row in rows)
    by_source = Counter(row["source_id"] for row in rows)
    return {
        "schema": "rjc-pis-cofins-ncm-index-v1",
        "generated_on": TODAY,
        "source_rule": "Somente registros publishable=true entram no indice publico; quarentena fica fora da busca e do llms.txt.",
        "summary": {
            "published_rows": len(rows),
            "unique_ncm": len({row["ncm"]["digitos"] for row in rows}),
            "sources_checked": len(inventory),
            "quarantine_rows": len(quarantine),
            "by_treatment": dict(sorted(by_treatment.items())),
            "by_sector": dict(sorted(by_sector.items())),
            "by_source": dict(sorted(by_source.items())),
            "oldest_verificado_em": min((row["verificado_em"] for row in rows), default=None),
        },
        "records": [
            {
                "id": row["id"],
                "ncm": row["ncm"]["codigo"],
                "ncm_digits": row["ncm"]["digitos"],
                "descricao": row["mercadoria_servico"],
                "resumo_operacional": row["resumo_operacional"],
                "pesquisa_texto": row["pesquisa_texto"],
                "setor": row["setor"],
                "tratamento": row["tratamento"],
                "operacao": row["operacao"],
                "status": row["status"],
                "validity_status": row["validity_status"],
                "ato": f"{row['ato_oficial']['tipo']} {row['ato_oficial']['numero']}",
                "url": row["ato_oficial"]["url"],
                "verificado_em": row["verificado_em"],
            }
            for row in rows
        ],
    }


def main() -> int:
    ensure_dirs()
    inventory: list[dict] = []
    public_rows: list[dict] = []
    quarantine_rows: list[dict] = []
    candidates: list[dict] = []

    for spec in SOURCES:
        status, raw, text = fetch_source(spec)
        raw_hash = sha256_bytes(raw) if raw else ""
        norm_hash = sha256_text(text) if text else ""
        raw_path = RAW_DIR / f"{spec.source_id}.html"
        norm_path = NORM_DIR / f"{spec.source_id}.txt"
        if raw:
            raw_path.write_bytes(raw)
        norm_path.write_text(text, encoding="utf-8", newline="\n")
        inv = {
            "source_id": spec.source_id,
            "tipo": spec.tipo,
            "numero": spec.numero,
            "titulo": spec.titulo,
            "url": spec.url,
            "http_status": status,
            "papel": spec.papel,
            "publicacao": spec.publicacao,
            "inicio_vigencia": spec.inicio_vigencia,
            "inicio_eficacia": spec.inicio_eficacia,
            "fim_vigencia": spec.fim_vigencia,
            "raw_path": str(raw_path),
            "normalized_path": str(norm_path),
            "raw_sha256": raw_hash,
            "normalized_sha256": norm_hash,
            "capturado_em": TODAY,
        }
        inventory.append(inv)
        rows, qrows = build_rows_for_source(spec, status, text, raw_hash, norm_hash)
        public_rows.extend(rows)
        quarantine_rows.extend(qrows)
        candidates.extend(rows)
        candidates.extend(qrows)

    public_rows.sort(key=lambda row: (row["ncm"]["digitos"], row["tratamento"], row["source_id"], row["id"]))
    quarantine_rows.sort(key=lambda row: row["id"])
    write_ndjson(DEEP_INVENTORY, inventory)
    write_ndjson(DEEP_CANDIDATES, candidates)
    write_ndjson(PUBLIC_NDJSON, public_rows)
    write_ndjson(QUARANTINE_NDJSON, quarantine_rows)
    PUBLIC_INDEX.write_text(
        json.dumps(build_index(public_rows, quarantine_rows, inventory), ensure_ascii=False, indent=2),
        encoding="utf-8",
        newline="\n",
    )
    summary = {
        "sources": len(inventory),
        "published_rows": len(public_rows),
        "quarantine_rows": len(quarantine_rows),
        "public_ndjson": str(PUBLIC_NDJSON),
        "deep_root": str(DEEP_ROOT),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
