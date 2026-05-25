#!/usr/bin/env python3
"""Render the deep legal modules for the RJC tax portal.

This module keeps the implementation static and reproducible: research files
guide the federal text extraction, while Goias material that needs live HTML
is read from public Secretaria da Economia pages during generation. Public
pages always cite the competent official link.
"""

from __future__ import annotations

import os
import re
import time
import unicodedata
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
BD_ROOT = Path(os.environ.get("RJC_BD_LEGISLACAO", r"C:\Users\kris2\OneDrive\COWORK\BD_LEGISLACAO"))
FEDERAL_ROOT = BD_ROOT / "#FEDERAIS-COMPILADO-ONLINE" / "legislacao_txt_completa"
REPO_SOURCE_ROOT = ROOT / "data" / "legal_sources"
UPDATED_ON = "25/05/2026"


def slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_text = ascii_text.lower()
    ascii_text = re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")
    return ascii_text or "item"


def fmt_num(value: int | float | str) -> str:
    try:
        return f"{int(value):,}".replace(",", ".")
    except (TypeError, ValueError):
        return str(value)


def rel_href(from_path: str, target: str) -> str:
    if target.startswith(("http://", "https://", "#")):
        return target
    start = (ROOT / from_path).parent
    return os.path.relpath(ROOT / target, start=start).replace("\\", "/")


class VisibleTextParser(HTMLParser):
    block_tags = {"p", "div", "br", "tr", "td", "th", "li", "h1", "h2", "h3", "h4", "h5", "h6"}
    skip_tags = {"style", "script", "head", "title"}

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.skip_stack: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in self.skip_tags:
            self.skip_stack.append(tag)
        if tag in self.block_tags and not self.skip_stack:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in self.skip_stack:
            while self.skip_stack:
                current = self.skip_stack.pop()
                if current == tag:
                    break
        if tag in self.block_tags and not self.skip_stack:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.skip_stack and data.strip():
            self.parts.append(data)


def html_to_text(raw: bytes, content_type: str = "") -> str:
    charset_match = re.search(r"charset=([^;\s]+)", content_type or "", flags=re.I)
    encodings = [charset_match.group(1)] if charset_match else []
    encodings.extend(["utf-8", "windows-1252", "latin-1"])
    html = ""
    for encoding in encodings:
        if not encoding:
            continue
        try:
            html = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    if not html:
        html = raw.decode("latin-1", errors="ignore")
    parser = VisibleTextParser()
    parser.feed(html)
    text = "".join(parser.parts)
    text = re.sub(r"[\t\r\f\v]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def fetch_public_text(url: str) -> str:
    last_error: Exception | None = None
    for attempt in range(1, 4):
        request = Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 RJC-Conhecimento/1.0",
                "Accept-Language": "pt-BR,pt;q=0.9",
                "Connection": "close",
            },
        )
        try:
            with urlopen(request, timeout=240) as response:
                raw = response.read()
                content_type = response.headers.get("Content-Type", "")
            return html_to_text(raw, content_type)
        except Exception as error:
            last_error = error
            time.sleep(attempt * 2)
    raise RuntimeError(f"Falha ao buscar fonte publica: {url}") from last_error


def read_local_text(files: list[str]) -> str:
    chunks = []
    for file_name in files:
        path = FEDERAL_ROOT / file_name
        if not path.exists():
            raise FileNotFoundError(f"Arquivo de pesquisa nao encontrado: {path}")
        chunks.append(strip_local_header(path.read_text(encoding="utf-8", errors="ignore")))
    return "\n\n".join(chunks)


def read_repo_text(files: list[str]) -> str:
    chunks = []
    for file_name in files:
        path = (ROOT / file_name) if ("/" in file_name or "\\" in file_name) else (REPO_SOURCE_ROOT / file_name)
        if not path.exists():
            raise FileNotFoundError(f"Arquivo versionado nao encontrado: {path}")
        chunks.append(strip_local_header(path.read_text(encoding="utf-8", errors="ignore")))
    return "\n\n".join(chunks)


def strip_local_header(text: str) -> str:
    text = re.sub(r"(?s)^={20,}.*?={20,}\s*", "", text, count=1)
    return text.strip()


def normalize_law_text(text: str, start_marker: str = "") -> str:
    text = text.replace("\xa0", " ")
    text = text.translate({
        0x0091: ord("'"),
        0x0092: ord("'"),
        0x0093: ord('"'),
        0x0094: ord('"'),
        0x0096: ord("-"),
        0x0097: ord("-"),
    })
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", text)
    if start_marker:
        marker_index = text.upper().find(start_marker.upper())
        if marker_index >= 0:
            text = text[marker_index:]
    text = re.sub(r"(?m)^(\s*)Art\.\s*(\d+(?:\.\d+)?(?:-[A-Z])?)\s*(?:º|°|o)?\s*\.?", r"\1Art. \2º", text)
    text = re.sub(r"(Art\. \d+(?:\.\d+)?(?:-[A-Z])?º)(?=\S)", r"\1 ", text)
    text = re.sub(r"(?m)^(\s*)§\s*(\d+)\s*(?:º|°|o)?", r"\1§ \2º", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def read_source_text(source: dict) -> str:
    if source.get("fetch_url"):
        raw = fetch_public_text(source["fetch_url"])
    elif source.get("repo_files"):
        raw = read_repo_text(source.get("repo_files", []))
    else:
        raw = read_local_text(source.get("files", []))
    return normalize_law_text(raw, source.get("start_marker", ""))


ARTICLE_RE = re.compile(r"(?m)^\s*Art\.\s*(\d+(?:\.\d+)?(?:-[A-Za-z])?)\s*(?:º|°|o)?\.?")


ROMAN_ONLY_RE = re.compile(r"^[IVXLCDM]{1,12}[A-Z]?$", re.I)
INCISO_DASH_RE = re.compile(r"^(?P<marker>[IVXLCDM]{1,12}[A-Z]?)\s*[-–]\s*(?P<rest>.*)$", re.I)
ALINEA_RE = re.compile(r"^(?P<marker>[a-z])\)\s*(?P<rest>.*)$")
ITEM_RE = re.compile(r"^(?P<marker>\d+(?:\.\d+)*)\s*(?:[-–.)])\s*(?P<rest>.*)$")
PARAGRAPH_RE = re.compile(
    r"^(?P<marker>(?:Â§|§)\s*\d+\s*(?:Âº|º|°|o)?[A-Za-z]?|Par[aá]grafo\s+u[nú]nico|Paragrafo\s+unico)\s*(?P<rest>.*)$",
    re.I,
)

SUBUNIT_LABELS = {
    "inciso": "Inciso",
    "paragrafo": "Paragrafo",
    "alinea": "Alinea",
    "item": "Item",
}


def article_base_number(number: str) -> int:
    base = number.split("-", 1)[0].replace(".", "")
    try:
        return int(base)
    except ValueError:
        return -1


def parse_articles(text: str) -> list[dict]:
    matches = list(ARTICLE_RE.finditer(text))
    articles = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        number = match.group(1)
        block = text[match.start():end].strip()
        if len(block) < 12:
            continue
        articles.append({
            "number": number,
            "base": article_base_number(number),
            "anchor": f"art-{slug(number)}-{index + 1}",
            "text": block,
        })
    return articles


def ascii_upper(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return normalized.encode("ascii", "ignore").decode("ascii").upper()


def canonical_marker(kind: str, marker: str) -> str:
    clean = ascii_upper(marker)
    clean = clean.replace("PARAGRAFO UNICO", "UNICO")
    clean = re.sub(r"[^A-Z0-9]+", "", clean)
    return f"{kind}:{clean}"


def is_source_index_instruction(line: str) -> bool:
    clean = ascii_upper(line)
    return "PARA ACESSAR" in clean or "CLICAR EM SEU NUMERO" in clean


def index_marker(line: str) -> dict | None:
    clean = line.strip()
    if not clean:
        return None
    if ROMAN_ONLY_RE.match(clean):
        return {"kind": "inciso", "marker": clean}
    paragraph = PARAGRAPH_RE.match(clean)
    if paragraph:
        return {"kind": "paragrafo", "marker": paragraph.group("marker").strip()}
    return None


def strip_source_index(text: str) -> tuple[str, list[dict]]:
    """Remove source-site click instructions and keep them as a real index."""
    lines = text.splitlines()
    cleaned: list[str] = []
    markers: list[dict] = []
    in_index = False
    for line in lines:
        if is_source_index_instruction(line):
            in_index = True
            continue
        if in_index:
            marker = index_marker(line)
            if marker:
                markers.append(marker)
                continue
            if not line.strip():
                continue
            in_index = False
        cleaned.append(line)
    return "\n".join(cleaned).strip(), markers


def next_nonempty_line(lines: list[str], start: int) -> str:
    for line in lines[start + 1:]:
        if line.strip():
            return line.strip()
    return ""


def detect_subunit_start(lines: list[str], index: int) -> dict | None:
    line = lines[index].strip()
    if not line:
        return None
    paragraph = PARAGRAPH_RE.match(line)
    if paragraph:
        return {"kind": "paragrafo", "marker": paragraph.group("marker").strip(), "line": index}
    inciso = INCISO_DASH_RE.match(line)
    if inciso:
        return {"kind": "inciso", "marker": inciso.group("marker").strip(), "line": index}
    if ROMAN_ONLY_RE.match(line) and next_nonempty_line(lines, index).startswith(("-", "–")):
        return {"kind": "inciso", "marker": line, "line": index}
    alinea = ALINEA_RE.match(line)
    if alinea:
        return {"kind": "alinea", "marker": alinea.group("marker").strip(), "line": index}
    item = ITEM_RE.match(line)
    if item and not re.match(r"^Art\.", line, flags=re.I):
        marker = item.group("marker").strip()
        if re.match(r"^\d{1,2}\.\d{1,2}\.\d{2,4}$", marker):
            return None
        return {"kind": "item", "marker": marker, "line": index}
    return None


def parse_article_structure(text: str, article_id: str) -> dict:
    cleaned_text, source_index = strip_source_index(text)
    lines = cleaned_text.splitlines()
    starts: list[dict] = []
    for index, _line in enumerate(lines):
        start = detect_subunit_start(lines, index)
        if start:
            starts.append(start)
    if not starts:
        return {
            "text": cleaned_text,
            "intro": cleaned_text,
            "source_index": source_index,
            "subunits": [],
            "targets": {},
        }
    intro = "\n".join(lines[:starts[0]["line"]]).strip()
    seen: dict[str, int] = {}
    targets: dict[str, str] = {}
    subunits: list[dict] = []
    for position, start in enumerate(starts):
        end_line = starts[position + 1]["line"] if position + 1 < len(starts) else len(lines)
        body = "\n".join(lines[start["line"]:end_line]).strip()
        key = canonical_marker(start["kind"], start["marker"])
        seen[key] = seen.get(key, 0) + 1
        base_anchor = f"{article_id}-{start['kind']}-{slug(start['marker'])}"
        anchor = base_anchor if seen[key] == 1 else f"{base_anchor}-{seen[key]}"
        targets.setdefault(key, anchor)
        subunits.append({
            "kind": start["kind"],
            "marker": start["marker"],
            "anchor": anchor,
            "text": body,
            "key": key,
        })
    return {
        "text": cleaned_text,
        "intro": intro,
        "source_index": source_index,
        "subunits": subunits,
        "targets": targets,
    }


def subunit_summary(text: str, limit: int = 108) -> str:
    clean = re.sub(r"\s+", " ", text).strip()
    return clean[:limit].rstrip() + ("..." if len(clean) > limit else "")


SUBUNIT_PLURALS = {
    "alinea": "alíneas",
    "inciso": "incisos",
    "item": "itens",
    "paragrafo": "parágrafos",
}


def render_article_index(structure: dict) -> str:
    index_items = structure.get("source_index") or [
        {"kind": item["kind"], "marker": item["marker"]} for item in structure.get("subunits", [])
    ]
    if not index_items or (not structure.get("source_index") and len(index_items) < 4):
        return ""
    subunit_by_key = {item["key"]: item for item in structure.get("subunits", [])}
    compact = len(index_items) > 24
    links = []
    missing = 0
    seen_index_keys: set[str] = set()
    for item in index_items:
        key = canonical_marker(item["kind"], item["marker"])
        if key in seen_index_keys:
            continue
        seen_index_keys.add(key)
        target = structure.get("targets", {}).get(key)
        label = f"{SUBUNIT_LABELS.get(item['kind'], 'Parte')} {item['marker']}"
        if not target:
            missing += 1
            continue
        detail = ""
        if not compact and key in subunit_by_key:
            detail = f"<small>{escape(subunit_summary(subunit_by_key[key]['text']))}</small>"
        links.append(f'<a href="#{escape(target)}"><span>{escape(label)}</span>{detail}</a>')
    if not links:
        return ""
    note = ""
    if missing:
        note = f'<p class="article-index-note">Os atalhos aparecem apenas quando o texto do inciso ou parágrafo está em tela. As demais remissões internas devem ser lidas no ato integral.</p>'
    return f"""
<nav class="article-index" aria-label="Índice interno do artigo">
  <strong>Índice do artigo</strong>
  <p>Use este mapa para sair do caput e chegar diretamente aos incisos, parágrafos, alíneas ou itens que estruturam a regra.</p>
  <div class="article-index-links {'compact' if compact else ''}">{''.join(links)}</div>
  {note}
</nav>
"""


def render_article_guidance(structure: dict) -> str:
    subunits = structure.get("subunits", [])
    if not subunits:
        return ""
    counts: dict[str, int] = {}
    for item in subunits:
        counts[item["kind"]] = counts.get(item["kind"], 0) + 1
    parts = []
    for kind, count in counts.items():
        singular = SUBUNIT_LABELS.get(kind, kind).lower()
        label = singular if count == 1 else SUBUNIT_PLURALS.get(kind, f"{singular}s")
        parts.append(f"{count} {label}")
    return f"""
<div class="article-context-note">
  <strong>Como ler este artigo</strong>
  <span>Comece pelo caput, depois avance pelas unidades normativas: {escape(', '.join(parts))}. Em beneficios e excecoes, confira sempre condicao, vigencia, documento e eventual nota de revogacao.</span>
</div>
"""


def render_article_body(article: dict, source_id: str) -> str:
    article_id = source_id + "-" + article["anchor"]
    structure = parse_article_structure(article["text"], article_id)
    if not structure.get("subunits"):
        return f'<div class="article-text">{escape(structure["text"])}</div>'
    intro = f'<div class="article-text article-caput">{escape(structure["intro"])}</div>' if structure.get("intro") else ""
    subunits = "".join(
        f"""
<section class="article-subunit" id="{escape(item['anchor'])}">
  <div class="article-subunit-marker">{escape(SUBUNIT_LABELS.get(item['kind'], 'Parte'))} {escape(item['marker'])}</div>
  <div class="article-text">{escape(item['text'])}</div>
</section>
"""
        for item in structure["subunits"]
    )
    return render_article_guidance(structure) + render_article_index(structure) + intro + f'<div class="article-subunits">{subunits}</div>'


def in_ranges(article: dict, ranges: list[tuple[int, int]] | None) -> bool:
    if not ranges:
        return True
    base = article.get("base", -1)
    return any(start <= base <= end for start, end in ranges)


def source_page_path(source_id: str) -> str:
    source = SOURCE_DEFS[source_id]
    base = "federal/legislacao/atos" if source["jurisdiction"] == "Federal" else "estados/goias/legislacao/atos"
    return f"{base}/{source_id}.html"


SOURCE_DEFS: dict[str, dict] = {
    "rir-2018-pj": {
        "jurisdiction": "Federal",
        "title": "Decreto 9.580/2018 - Regulamento do Imposto sobre a Renda",
        "short": "RIR/2018",
        "url": "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/decreto/d9580.htm",
        "files": ["Decreto_9580_2018_Regulamento_IRPJ.txt"],
        "source_ranges": [(158, 204), (217, 386), (500, 540), (578, 610), (919, 925), (1010, 1010)],
        "note": "Livro II e dispositivos de pessoa juridica, regimes, pagamento e Lalur.",
    },
    "lei-7689-1988-csll": {
        "jurisdiction": "Federal",
        "title": "Lei 7.689/1988 - Contribuicao Social sobre o Lucro Liquido",
        "short": "Lei da CSLL",
        "url": "https://www.planalto.gov.br/ccivil_03/leis/l7689.htm",
        "files": ["Lei_7689_1988_CSLL_Original.txt"],
        "note": "Instituicao, base e regras centrais da CSLL.",
    },
    "lei-9249-1995-irpj-csll": {
        "jurisdiction": "Federal",
        "title": "Lei 9.249/1995 - IRPJ, CSLL, juros sobre capital proprio e ajustes",
        "short": "Lei 9.249/1995",
        "url": "https://www.planalto.gov.br/ccivil_03/leis/l9249.htm",
        "files": ["Lei_9249_1995_IRPJ_CSLL.txt"],
        "note": "Base de IRPJ/CSLL, JCP, deducoes, dividendos e regras correlatas.",
    },
    "lei-9430-1996-irpj": {
        "jurisdiction": "Federal",
        "title": "Lei 9.430/1996 - Administracao tributaria, IRPJ e CSLL",
        "short": "Lei 9.430/1996",
        "url": "https://www.planalto.gov.br/ccivil_03/leis/l9430.htm",
        "files": ["Lei_9430_1996_Compilada_IRPJ.txt"],
        "note": "Apuracao, estimativas, compensacao, multa, juros e controles.",
    },
    "lei-8981-1995-regimes": {
        "jurisdiction": "Federal",
        "title": "Lei 8.981/1995 - Lucro real, presumido, arbitrado e receitas",
        "short": "Lei 8.981/1995",
        "url": "https://www.planalto.gov.br/ccivil_03/leis/l8981.htm",
        "files": ["Lei_8981_1995_Lucro_Real_Presumido.txt"],
        "note": "Regimes e bases de apuracao usados na leitura de IRPJ e CSLL.",
    },
    "lei-9065-1995-irpj": {
        "jurisdiction": "Federal",
        "title": "Lei 9.065/1995 - IRPJ, compensacao e limites",
        "short": "Lei 9.065/1995",
        "url": "https://www.planalto.gov.br/ccivil_03/leis/l9065.htm",
        "files": ["Lei_9065_1995_IRPJ_Aliquotas.txt"],
        "note": "Aliquotas, compensacoes e limites relevantes a fechamento.",
    },
    "lei-15079-2024-csll": {
        "jurisdiction": "Federal",
        "title": "Lei 15.079/2024 - Adicional da CSLL",
        "short": "Lei 15.079/2024",
        "url": "https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2024/lei/l15079.htm",
        "files": ["Lei_15079_2024_Adicional_CSLL.txt"],
        "note": "Adicional da CSLL e controles especificos.",
    },
    "decreto-6306-2007-iof": {
        "jurisdiction": "Federal",
        "title": "Decreto 6.306/2007 - Regulamento do IOF",
        "short": "Regulamento do IOF",
        "url": "https://www.planalto.gov.br/ccivil_03/_ato2007-2010/2007/Decreto/D6306.htm",
        "files": ["Decreto_6306_2007_Regulamento_IOF.txt"],
        "note": "Credito, cambio, seguro, titulos, responsaveis, cobranca e fiscalizacao.",
    },
    "lei-5143-1966-iof": {
        "jurisdiction": "Federal",
        "title": "Lei 5.143/1966 - Instituicao do IOF",
        "short": "Lei do IOF",
        "url": "https://www.planalto.gov.br/ccivil_03/leis/l5143.htm",
        "files": ["Lei_5143_1966_IOF_Original.txt"],
        "note": "Norma matriz do IOF.",
    },
    "lei-8894-1994-iof": {
        "jurisdiction": "Federal",
        "title": "Lei 8.894/1994 - Aliquotas do IOF",
        "short": "Lei 8.894/1994",
        "url": "https://www.planalto.gov.br/ccivil_03/leis/l8894.htm",
        "files": ["Lei_8894_1994_IOF_Aliquotas.txt"],
        "note": "Competencia para alteracao de aliquotas e limites.",
    },
    "decretos-iof-2025": {
        "jurisdiction": "Federal",
        "title": "Decretos de 2025 - Alteracoes recentes do IOF",
        "short": "Alteracoes IOF 2025",
        "url": "https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2025/decreto/indice.htm",
        "files": ["Decreto_12466_2025_IOF_Aliquotas.txt", "Decreto_12467_2025_IOF_Alteracoes.txt", "Decreto_12499_2025_IOF_Alteracoes2.txt"],
        "note": "Atos recentes de aliquota e vigencia.",
    },
    "ripi-2010": {
        "jurisdiction": "Federal",
        "title": "Decreto 7.212/2010 - Regulamento do IPI",
        "short": "RIPI/2010",
        "url": "https://www.planalto.gov.br/ccivil_03/_ato2007-2010/2010/decreto/d7212.htm",
        "fetch_url": "https://www.planalto.gov.br/ccivil_03/_ato2007-2010/2010/decreto/d7212.htm",
        "note": "Regulamento vigente da cobranca, fiscalizacao, arrecadacao e administracao do IPI.",
    },
    "tipi-2022": {
        "jurisdiction": "Federal",
        "title": "TIPI vigente - Tabela de Incidencia do IPI",
        "short": "TIPI",
        "url": "https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2022/decreto/d11158.htm",
        "files": ["TIPI_Vigente_2022_Parte1.txt", "TIPI_Vigente_2022_Parte2.txt", "TIPI_Vigente_2022_Parte3.txt"],
        "render": "full_text",
        "note": "Tabela de classificacao e aliquotas do IPI.",
    },
    "lei-7798-1989-ipi": {
        "jurisdiction": "Federal",
        "title": "Lei 7.798/1989 - IPI e classificacao de produtos",
        "short": "Lei 7.798/1989",
        "url": "https://www.planalto.gov.br/ccivil_03/leis/l7798.htm",
        "files": ["Lei_7798_1989_IPI_Alteracoes.txt"],
        "note": "Regras legais de IPI ligadas a produtos e tributacao.",
    },
    "lei-8387-1991-zfm-ipi": {
        "jurisdiction": "Federal",
        "title": "Lei 8.387/1991 - Zona Franca de Manaus e IPI",
        "short": "ZFM e IPI",
        "url": "https://www.planalto.gov.br/ccivil_03/leis/l8387.htm",
        "files": ["Lei_8387_1991_ZFM_IPI_Isento.txt"],
        "note": "Beneficios e condicionantes de IPI em area incentivada.",
    },
    "decretos-tipi-2025": {
        "jurisdiction": "Federal",
        "title": "Decretos de 2025 - Atualizacoes da TIPI",
        "short": "Atualizacoes TIPI 2025",
        "url": "https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2025/decreto/indice.htm",
        "files": ["Decreto_12549_2025_TIPI_Atualizada.txt"],
        "note": "Ajustes recentes de classificacao e aliquota.",
    },
    "in-rfb-2324-2026-ipi-suspensao": {
        "jurisdiction": "Federal",
        "title": "IN RFB 2.324/2026 - suspensao do IPI",
        "short": "IN RFB 2.324/2026",
        "url": "https://normas.receita.fazenda.gov.br/sijut2consulta/link.action?antigo=1&idAto=150886",
        "repo_files": ["data/legal_sources/federal/IN_RFB_2324_2026_IPI_Suspensao.txt"],
        "start_marker": "Art. 1",
        "note": "Disciplina hipoteses de suspensao do IPI previstas nas Leis 9.826/1999 e 10.637/2002, com condicoes, declaracoes, registro e informacao em nota fiscal.",
    },
    "in-rfb-2121-2022-pis-cofins": {
        "jurisdiction": "Federal",
        "title": "IN RFB 2.121/2022 - PIS/Pasep, Cofins e importacao",
        "short": "IN RFB 2.121/2022",
        "url": "https://normasinternet2.receita.fazenda.gov.br/#/consulta/externa/127905",
        "files": ["IN_RFB_2121_2022_PIS_COFINS_Parte1.txt", "IN_RFB_2121_2022_PIS_COFINS_Parte2.txt", "IN_RFB_2121_2022_PIS_COFINS_Parte3.txt"],
        "start_marker": "RESOLVE:",
        "note": "Consolidacao normativa de PIS/Pasep, Cofins, importacao, regimes e obrigacoes.",
    },
    "lei-10637-2002-pis": {
        "jurisdiction": "Federal",
        "title": "Lei 10.637/2002 - PIS/Pasep nao cumulativo",
        "short": "Lei 10.637/2002",
        "url": "https://www.planalto.gov.br/ccivil_03/leis/2002/l10637.htm",
        "files": ["Lei_10637_2002_PIS_Nao_Cumulativo.txt"],
        "note": "Nao cumulatividade do PIS/Pasep, creditos e regras correlatas.",
    },
    "lei-10833-2003-cofins": {
        "jurisdiction": "Federal",
        "title": "Lei 10.833/2003 - Cofins nao cumulativa",
        "short": "Lei 10.833/2003",
        "url": "https://www.planalto.gov.br/ccivil_03/leis/2003/l10.833.htm",
        "files": ["Lei_10833_2003_Compilada_COFINS.txt"],
        "note": "Nao cumulatividade da Cofins, creditos, retencoes e regras correlatas.",
    },
    "lei-10865-2004-pis-cofins-importacao": {
        "jurisdiction": "Federal",
        "title": "Lei 10.865/2004 - PIS/Cofins-Importacao",
        "short": "Lei 10.865/2004",
        "url": "https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2004/lei/l10.865.htm",
        "files": ["Lei_10865_2004_PIS_COFINS_Importacao.txt"],
        "note": "Importacao de bens e servicos, base, aliquota, contribuinte e creditos.",
    },
    "mpv-1357-2026-remessas-postais": {
        "jurisdiction": "Federal",
        "title": "Medida Provisoria 1.357/2026 - remessas postais internacionais",
        "short": "MP 1.357/2026",
        "url": "https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2026/mpv/mpv1357.htm",
        "repo_files": ["data/legal_sources/federal/MP_1357_2026_Remessas_Postais.txt"],
        "note": "Altera o Decreto-Lei 1.804/1980 para tratar da tributacao simplificada de remessas postais internacionais.",
    },
    "lei-9715-1998-pis": {
        "jurisdiction": "Federal",
        "title": "Lei 9.715/1998 - PIS/Pasep",
        "short": "Lei 9.715/1998",
        "url": "https://www.planalto.gov.br/ccivil_03/leis/l9715.htm",
        "files": ["Lei_9715_1998_PIS_Base_Contributiva.txt"],
        "note": "Base legal geral do PIS/Pasep.",
    },
    "lei-9718-1998-pis-cofins": {
        "jurisdiction": "Federal",
        "title": "Lei 9.718/1998 - PIS/Cofins no regime cumulativo",
        "short": "Lei 9.718/1998",
        "url": "https://www.planalto.gov.br/ccivil_03/leis/l9718.htm",
        "files": ["Lei_9718_1998_COFINS_Compilada.txt"],
        "note": "Receita bruta, cumulatividade e regras de PIS/Cofins.",
    },
    "lc-70-1991-cofins": {
        "jurisdiction": "Federal",
        "title": "Lei Complementar 70/1991 - Cofins",
        "short": "LC 70/1991",
        "url": "https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp70.htm",
        "files": ["LC_70_1991_COFINS_Original.txt"],
        "note": "Instituicao da Cofins.",
    },
    "lei-13097-2015-pis-cofins": {
        "jurisdiction": "Federal",
        "title": "Lei 13.097/2015 - Reducoes a zero e regimes setoriais",
        "short": "Lei 13.097/2015",
        "url": "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13097.htm",
        "files": ["Lei_13097_2015_Reducao_Zero_PIS_COFINS.txt"],
        "note": "Tratamentos setoriais, aliquota zero e beneficios.",
    },
    "lei-15394-2026-pis-cofins-residuos": {
        "jurisdiction": "Federal",
        "title": "Lei 15.394/2026 - creditos e isencao de PIS/Cofins para residuos e aparas",
        "short": "Lei 15.394/2026",
        "url": "https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2026/lei/l15394.htm",
        "repo_files": ["data/legal_sources/federal/Lei_15394_2026_PIS_COFINS_Residuos.txt"],
        "start_marker": "LEI Nº 15.394, DE 22 DE ABRIL DE 2026",
        "note": "Altera a Lei 11.196/2005 para autorizar creditamento de PIS/Cofins em aquisicoes de determinados residuos e aparas e isentar vendas especificadas.",
    },
    "ec-132-2023-reforma": {
        "jurisdiction": "Federal",
        "title": "Emenda Constitucional 132/2023 - Reforma Tributaria",
        "short": "EC 132/2023",
        "url": "https://www.planalto.gov.br/ccivil_03/constituicao/emendas/emc/emc132.htm",
        "files": ["EC_132_2023_Reforma_Tributaria.txt"],
        "note": "Altera o Sistema Tributario Nacional, cria a arquitetura constitucional do IBS, CBS e Imposto Seletivo e disciplina a transicao.",
    },
    "lc-214-2025-reforma": {
        "jurisdiction": "Federal",
        "title": "Lei Complementar 214/2025 - IBS, CBS e Imposto Seletivo",
        "short": "LC 214/2025",
        "url": "https://www.planalto.gov.br/ccivil_03/leis/lcp/Lcp214compilado.htm",
        "files": ["LC_214_2025_Compilada_IBS_CBS_IS.txt"],
        "note": "Institui IBS, CBS e Imposto Seletivo, organiza fato gerador, base, creditos, recolhimento, split payment, regimes diferenciados e transicao.",
    },
    "lc-227-2026-cgibs": {
        "jurisdiction": "Federal",
        "title": "Lei Complementar 227/2026 - Comite Gestor do IBS",
        "short": "LC 227/2026",
        "url": "https://www.planalto.gov.br/ccivil_03/leis/lcp/Lcp227.htm",
        "files": ["LC_227_2026_Comite_Gestor_IBS.txt"],
        "note": "Institui o Comite Gestor do IBS, disciplina administracao integrada, fiscalizacao, distribuicao da arrecadacao e saldos credores de ICMS.",
    },
    "decreto-12955-2026-cbs": {
        "jurisdiction": "Federal",
        "title": "Decreto 12.955/2026 - Regulamento da CBS",
        "short": "Decreto 12.955/2026",
        "url": "https://www.in.gov.br/en/web/dou/-/decreto-n-12.955-de-29-de-abril-de-2026-702415229",
        "repo_files": ["data/legal_sources/reforma_tributaria/Decreto_12955_2026_Regulamento_CBS.txt"],
        "note": "Regulamenta a Contribuicao Social sobre Bens e Servicos - CBS, com normas comuns espelhadas ao IBS, documento fiscal, apuracao, creditos, split payment, regimes e transicao.",
    },
    "resolucao-cgibs-6-2026-ibs": {
        "jurisdiction": "Federal",
        "title": "Resolucao CGIBS 6/2026 - Regulamento do IBS",
        "short": "Resolucao CGIBS 6/2026",
        "url": "https://www.cgibs.gov.br/upload/arquivos/202604/30084927-res-cgibs-n-6-30-abr-2026-regulamenta-o-ibs.pdf",
        "repo_files": ["data/legal_sources/reforma_tributaria/Resolucao_CGIBS_6_2026_Regulamento_IBS.txt"],
        "note": "Regulamenta o Imposto sobre Bens e Servicos - IBS, com normas comuns a CBS, documento fiscal, apuracao, creditos, split payment, regimes e transicao.",
    },
    "portaria-mf-cgibs-7-2026": {
        "jurisdiction": "Federal",
        "title": "Portaria Conjunta MF/CGIBS 7/2026 - disposicoes comuns IBS/CBS",
        "short": "Portaria MF/CGIBS 7/2026",
        "url": "https://www.cgibs.gov.br/upload/arquivos/202604/30094136-sei-mgi-60959979-portaria-conjunta.pdf",
        "repo_files": ["data/legal_sources/reforma_tributaria/Portaria_Conjunta_MF_CGIBS_7_2026.txt"],
        "note": "Formaliza o reconhecimento das disposicoes comuns ao IBS e a CBS nos respectivos regulamentos.",
    },
    "ato-conjunto-rfb-cgibs-1-2025": {
        "jurisdiction": "Federal",
        "title": "Ato Conjunto RFB/CGIBS 1/2025 - obrigacoes acessorias IBS/CBS em 2026",
        "short": "Ato Conjunto 1/2025",
        "url": "https://www.in.gov.br/en/web/dou/-/ato-conjunto-rfb/cgibs-n-1-de-22-de-dezembro-de-2025-677624586",
        "repo_files": ["data/legal_sources/reforma_tributaria/Ato_Conjunto_RFB_CGIBS_1_2025_Obrigacoes_2026.txt"],
        "note": "Define documentos fiscais recepcionados e prazos de observancia para informacoes destinadas a apuracao do IBS e da CBS em 2026.",
    },
    "rfb-orientacoes-reforma-2026": {
        "jurisdiction": "Federal",
        "title": "Receita Federal - orientacoes da Reforma Tributaria para 2026",
        "short": "Orientacoes RFB 2026",
        "url": "https://www.gov.br/receitafederal/pt-br/acesso-a-informacao/acoes-e-programas/programas-e-atividades/reforma-tributaria-do-consumo/orientacoes-2026",
        "repo_files": ["data/legal_sources/reforma_tributaria/Receita_Orientacoes_Reforma_2026.txt"],
        "render": "structured_text",
        "note": "Orientacao administrativa da Receita Federal para preparacao operacional de 2026.",
    },
    "rfb-marcos-reforma": {
        "jurisdiction": "Federal",
        "title": "Receita Federal - principais marcos regulatorios da Reforma Tributaria",
        "short": "Marcos RFB Reforma",
        "url": "https://www.gov.br/receitafederal/pt-br/acesso-a-informacao/acoes-e-programas/programas-e-atividades/reforma-tributaria-do-consumo/marcos",
        "repo_files": ["data/legal_sources/reforma_tributaria/Receita_Marcos_Regulatorios_Reforma.txt"],
        "render": "structured_text",
        "note": "Pagina oficial de marcos regulatorios para acompanhamento de normas da Reforma Tributaria do Consumo.",
    },
    "tabela-cst-cclasstrib-ibs-cbs": {
        "jurisdiction": "Federal",
        "title": "Tabela CST e cClassTrib do IBS e da CBS - 15/04/2026",
        "short": "CST/cClassTrib IBS-CBS",
        "url": "https://dfe-portal.svrs.rs.gov.br/CFF/ClassificacaoTributaria",
        "repo_files": ["data/legal_sources/reforma_tributaria/Tabela_CST_cClassTrib_IBS_CBS_2026_04_15.txt"],
        "render": "structured_text",
        "note": "Tabela operacional do Portal Nacional de Documentos Fiscais Eletrônicos que relaciona CST-IBS/CBS, cClassTrib, base legal, reduções, indicadores e aplicabilidade por documento fiscal.",
    },
    "tabela-ccredpres-ibs-cbs": {
        "jurisdiction": "Federal",
        "title": "Tabela de códigos de crédito presumido do IBS e da CBS - 12/12/2025",
        "short": "cCredPres IBS-CBS",
        "url": "https://dfe-portal.svrs.rs.gov.br/CFF/TabelaCreditoPresumido",
        "repo_files": ["data/legal_sources/reforma_tributaria/Tabela_cCredPres_IBS_CBS_2025_12_12.txt"],
        "render": "structured_text",
        "note": "Tabela operacional de crédito presumido: código, hipótese legal, forma de apropriação, grupos XML, alíquotas, vigência e referência de cClassTrib.",
    },
    "it-2025-002-tabelas-reforma": {
        "jurisdiction": "Federal",
        "title": "Informe Técnico 2025.002 v1.50 - tabelas de classificação do IBS e da CBS",
        "short": "IT 2025.002 v1.50",
        "url": "https://dfe-portal.svrs.rs.gov.br/Nfe/Documentos",
        "repo_files": ["data/legal_sources/reforma_tributaria/IT_2025_002_v1_50_Tabelas_Classificacao_IBS_CBS.txt"],
        "render": "structured_text",
        "note": "Informe técnico com conceitos de CST, cClassTrib, cCredPres, alíquotas padrão e links operacionais das tabelas da Reforma Tributária do Consumo.",
    },
    "nt-2025-002-rtc-nfe": {
        "jurisdiction": "Federal",
        "title": "Nota Técnica 2025.002 v1.35 - adequações NF-e/NFC-e para IBS, CBS e IS",
        "short": "NT 2025.002 v1.35",
        "url": "https://dfe-portal.svrs.rs.gov.br/Nfe/Documentos",
        "repo_files": ["data/legal_sources/reforma_tributaria/NT_2025_002_v1_35_RTC_NFe_IBS_CBS_IS.txt"],
        "render": "structured_text",
        "note": "Nota técnica de leiaute, campos e regras de validação da NF-e e NFC-e para a Reforma Tributária do Consumo.",
    },
    "rcte-go": {
        "jurisdiction": "GO",
        "title": "Decreto GO 4.852/1997 - RCTE",
        "short": "RCTE/GO",
        "url": "https://appasp.economia.go.gov.br/legislacao/arquivos/RCTE/RCTE.htm",
        "fetch_url": "https://appasp.economia.go.gov.br/legislacao/arquivos/RCTE/RCTE.htm",
        "source_ranges": [(1, 107), (167, 167), (167, 168), (520, 540)],
        "note": "Regulamento do Codigo Tributario de Goias, com ICMS, beneficios e documento fiscal.",
    },
    "anexo-ix-go": {
        "jurisdiction": "GO",
        "title": "Anexo IX do RCTE/GO - Beneficios fiscais",
        "short": "Anexo IX",
        "url": "https://appasp.economia.go.gov.br/legislacao/arquivos/Rcte/Anexos/ANEXO_09_Beneficio_Fiscal.htm",
        "fetch_url": "https://appasp.economia.go.gov.br/legislacao/arquivos/Rcte/Anexos/ANEXO_09_Beneficio_Fiscal.htm",
        "note": "Isencoes, reducoes, creditos outorgados, condicionantes e beneficios goianos.",
    },
    "decreto-go-10904-2026-anexo-ix-transmissao-energia": {
        "jurisdiction": "GO",
        "title": "Decreto GO 10.904/2026 - Anexo IX do RCTE/GO - linhas de transmissao",
        "short": "Decreto GO 10.904/2026",
        "url": "https://goias.gov.br/economia/wp-content/uploads/sites/45/2026/05/D_10904.doc",
        "repo_files": ["data/legal_sources/goias/Decreto_GO_10904_2026_Anexo_IX_Transmissao_Energia.txt"],
        "render": "full_text",
        "note": "Altera o Anexo IX do RCTE/GO para tratar de beneficio em entradas de mercadorias e bens destinados a obras de linhas de transmissao de energia eletrica, nos termos do Convenio ICMS 30/2025.",
    },
    "decreto-go-10905-2026-anexo-ix-biogas-biometano": {
        "jurisdiction": "GO",
        "title": "Decreto GO 10.905/2026 - Anexo IX do RCTE/GO - biogas e biometano",
        "short": "Decreto GO 10.905/2026",
        "url": "https://goias.gov.br/economia/wp-content/uploads/sites/45/2026/05/D_10905.doc",
        "repo_files": ["data/legal_sources/goias/Decreto_GO_10905_2026_Anexo_IX_Biogas_Biometano.txt"],
        "render": "full_text",
        "note": "Altera o Anexo IX do RCTE/GO com regras de credito especial de investimento para unidades industriais de biogas e biometano e termo de acordo de regime especial.",
    },
    "in-1518-2022-cbenef-go": {
        "jurisdiction": "GO",
        "title": "IN 1.518/2022-GSE - Codigo de Beneficio Fiscal em Goias",
        "short": "IN cBenef/GO",
        "url": "https://appasp.economia.go.gov.br/Legislacao/arquivos/Secretario/IN/IN_1518_2022.htm",
        "fetch_url": "https://appasp.economia.go.gov.br/Legislacao/arquivos/Secretario/IN/IN_1518_2022.htm",
        "render": "full_text",
        "note": "Tabela e uso do codigo de beneficio fiscal na NF-e e NFC-e.",
    },
    "clt-1943": {
        "jurisdiction": "Federal",
        "title": "Decreto-Lei 5.452/1943 - Consolidacao das Leis do Trabalho",
        "short": "CLT",
        "url": "https://www.planalto.gov.br/ccivil_03/Decreto-lei/Del5452.htm",
        "fetch_url": "https://www.planalto.gov.br/ccivil_03/Decreto-lei/Del5452.htm",
        "note": "Texto compilado da CLT: relacao de emprego, contrato, jornada, salario, ferias, rescisao, seguranca e normas trabalhistas.",
    },
    "lei-8212-1991-custeio": {
        "jurisdiction": "Federal",
        "title": "Lei 8.212/1991 - Custeio da Seguridade Social",
        "short": "Lei 8.212/1991",
        "url": "https://www.planalto.gov.br/ccivil_03/leis/L8212cons.htm",
        "files": ["Lei_8212_1991_Custeio_Previdencia.txt"],
        "note": "Custeio previdenciario, segurados, empresa, contribuicoes sobre folha, obrigacoes, arrecadacao e prova.",
    },
    "lei-12546-2011-cprb": {
        "jurisdiction": "Federal",
        "title": "Lei 12.546/2011 - CPRB e desoneracao da folha",
        "short": "Lei 12.546/2011",
        "url": "https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2011/lei/l12546.htm",
        "files": ["Lei_12546_2011_CPRB.txt"],
        "note": "Contribuicao previdenciaria sobre a receita bruta, substituicao de contribuicoes sobre folha, setores, bases, aliquotas e controles.",
    },
    "lei-8213-1991-beneficios": {
        "jurisdiction": "Federal",
        "title": "Lei 8.213/1991 - Planos de Beneficios da Previdencia Social",
        "short": "Lei 8.213/1991",
        "url": "https://www.planalto.gov.br/ccivil_03/LEIS/L8213cons.htm",
        "files": ["Lei_8213_1991_Beneficios_Previdencia.txt"],
        "note": "Beneficios previdenciarios, incapacidade, acidente do trabalho, estabilidade e deveres informacionais.",
    },
    "decreto-3048-1999-rps": {
        "jurisdiction": "Federal",
        "title": "Decreto 3.048/1999 - Regulamento da Previdencia Social",
        "short": "RPS/1999",
        "url": "https://www.planalto.gov.br/ccivil_03/decreto/D3048.htm",
        "fetch_url": "https://www.planalto.gov.br/ccivil_03/decreto/D3048.htm",
        "note": "Regulamento do RGPS: segurados, beneficios, salario-de-contribuicao, arrecadacao e obrigações previdenciarias.",
    },
    "lei-8036-1990-fgts": {
        "jurisdiction": "Federal",
        "title": "Lei 8.036/1990 - Fundo de Garantia do Tempo de Servico",
        "short": "Lei 8.036/1990",
        "url": "https://www.planalto.gov.br/ccivil_03/leis/L8036consol.htm",
        "fetch_url": "https://www.planalto.gov.br/ccivil_03/leis/L8036consol.htm",
        "note": "Regime legal do FGTS: contas vinculadas, depositos, movimentacao, rescisao, fiscalizacao e penalidades.",
    },
    "decreto-8373-2014-esocial": {
        "jurisdiction": "Federal",
        "title": "Decreto 8.373/2014 - eSocial",
        "short": "Decreto do eSocial",
        "url": "https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2014/decreto/d8373.htm",
        "fetch_url": "https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2014/decreto/d8373.htm",
        "note": "Institui o Sistema de Escrituracao Digital das Obrigacoes Fiscais, Previdenciarias e Trabalhistas.",
    },
}


LEGAL_MODULES: list[dict] = [
    {
        "id": "irpj",
        "jurisdiction": "Federal",
        "title": "IRPJ: legislacao em tela",
        "summary": "Regra matriz, regimes, lucro real, presumido, JCP, beneficios e prova do imposto de renda da pessoa juridica.",
        "legacy": "federal/irpj-csll.html",
        "sources": ["rir-2018-pj", "lei-9249-1995-irpj-csll", "lei-9430-1996-irpj", "lei-8981-1995-regimes", "lei-9065-1995-irpj"],
        "chapters": [
            {
                "id": "contribuintes-regra-matriz",
                "title": "Contribuintes, equiparacoes e regra matriz",
                "summary": "Quem entra na tributacao como pessoa juridica e onde a relacao fiscal comeca.",
                "refs": [{"source": "rir-2018-pj", "ranges": [(158, 170)]}],
                "analysis": [
                    "O IRPJ comeca pela identificacao do contribuinte. Antes de falar em lucro real ou presumido, confirme se a entidade, SCP, empresa individual, filial ou equiparacao esta dentro do campo de tributacao.",
                    "A aplicacao pratica esta no cadastro fiscal e societario: CNPJ, matriz/filial, contrato social, atividade, regime escolhido e demonstracao de quem assume o resultado tributavel.",
                ],
            },
            {
                "id": "apuracao-regimes",
                "title": "Periodo de apuracao e regimes de lucro",
                "summary": "Lucro real, presumido e arbitrado como portas de entrada do calculo.",
                "refs": [{"source": "rir-2018-pj", "ranges": [(217, 236)]}, {"source": "lei-8981-1995-regimes", "ranges": [(25, 37)]}],
                "analysis": [
                    "O regime nao e uma etiqueta; ele define a forma de provar a base. No real, a contabilidade conversa com Lalur e ECF. No presumido, a receita precisa estar segregada por atividade e natureza.",
                    "A pergunta de auditoria e se a base usada no DARF aparece com a mesma logica na ECD, ECF, balancete, notas fiscais e demonstrativos internos.",
                ],
            },
            {
                "id": "lucro-real",
                "title": "Lucro Real, adicoes, exclusoes e compensacoes",
                "summary": "Base fiscal nasce do lucro liquido e recebe ajustes controlados.",
                "refs": [{"source": "rir-2018-pj", "ranges": [(258, 386)]}, {"source": "lei-9430-1996-irpj", "ranges": [(1, 15)]}],
                "analysis": [
                    "Lucro Real e uma ponte entre contabilidade e lei. A tese fiscal so se sustenta quando cada adicao, exclusao, compensacao e incentivo tem memoria, conta contabil e fundamento legal.",
                    "Na rotina, isso vira conciliacao: resultado societario, parte A, parte B, base negativa, prejuizo fiscal, ECF, DCTF e PER/DCOMP devem contar a mesma historia.",
                ],
            },
            {
                "id": "lucro-presumido",
                "title": "Lucro Presumido e segregacao de receitas",
                "summary": "Percentuais de presuncao, receitas e limites do regime simplificado.",
                "refs": [{"source": "rir-2018-pj", "ranges": [(587, 610)]}, {"source": "lei-9249-1995-irpj-csll", "ranges": [(15, 25)]}],
                "analysis": [
                    "Presumido nao dispensa prova. Ele troca a prova do lucro efetivo pela prova da receita correta, da atividade correta e do percentual correto.",
                    "A maior falha aparece quando a empresa mistura receitas de naturezas diferentes e aplica um percentual unico sem demonstrar a classificacao legal.",
                ],
            },
            {
                "id": "beneficios-jcp-prova",
                "title": "Beneficios, JCP, pagamento e prova",
                "summary": "Tratamentos que reduzem, diferem ou controlam a base e o recolhimento.",
                "refs": [{"source": "lei-9249-1995-irpj-csll", "ranges": [(9, 10)]}, {"source": "rir-2018-pj", "ranges": [(919, 925), (1010, 1010)]}],
                "analysis": [
                    "Beneficio e deducao nao sao desconto livre. Cada vantagem exige requisito, limite, demonstracao e documento que suporte a decisao.",
                    "Para JCP, pagamento e Lalur, o controle forte e documental: deliberacao societaria, calculo, retencao quando aplicavel, escrituração e cruzamento na ECF.",
                ],
            },
        ],
    },
    {
        "id": "csll",
        "jurisdiction": "Federal",
        "title": "CSLL: legislacao em tela",
        "summary": "Instituicao, base de calculo, aliquotas, ajustes, adicional e prova da contribuicao social.",
        "legacy": "federal/irpj-csll.html",
        "sources": ["lei-7689-1988-csll", "lei-9249-1995-irpj-csll", "lei-9430-1996-irpj", "lei-9065-1995-irpj", "lei-15079-2024-csll"],
        "chapters": [
            {
                "id": "instituicao-base",
                "title": "Instituicao, contribuintes e base",
                "summary": "A regra que cria a CSLL e amarra a contribuicao ao resultado da pessoa juridica.",
                "refs": [{"source": "lei-7689-1988-csll", "ranges": [(1, 4)]}],
                "analysis": [
                    "A CSLL acompanha a logica do resultado, mas nao e copia automatica do IRPJ. Ela tem base, aliquota e ajustes proprios.",
                    "No fechamento, trate IRPJ e CSLL como tributos irmaos: partem da mesma contabilidade, mas cada um exige memoria especifica.",
                ],
            },
            {
                "id": "aliquotas-ajustes",
                "title": "Aliquotas, ajustes e limites",
                "summary": "Dispositivos que alteram carga, dedutibilidade, compensacao e tratamento da base.",
                "refs": [{"source": "lei-7689-1988-csll", "ranges": [(3, 9)]}, {"source": "lei-9249-1995-irpj-csll", "ranges": [(13, 20)]}],
                "analysis": [
                    "A aliquota so fecha depois de confirmar setor, periodo e regra especial. Bancos, seguradoras e outras atividades podem ter tratamento distinto.",
                    "A memoria de calculo deve separar resultado contabil, exclusoes, adicoes, compensacao de base negativa e fundamento de cada ajuste.",
                ],
            },
            {
                "id": "compensacao-controles",
                "title": "Compensacao, pagamentos e controles",
                "summary": "Leis que conectam CSLL, pagamento mensal, declaracoes e auditoria.",
                "refs": [{"source": "lei-9430-1996-irpj", "ranges": [(1, 15), (44, 74)]}, {"source": "lei-9065-1995-irpj", "ranges": [(15, 20)]}],
                "analysis": [
                    "Compensar base ou credito sem lastro e um risco direto de glosa. A origem do valor precisa aparecer no controle fiscal e na declaracao.",
                    "Na auditoria, a CSLL deve ser reconciliada com balancete, ECF, DCTF, pagamentos e eventuais compensacoes.",
                ],
            },
            {
                "id": "adicional-csll",
                "title": "Adicional da CSLL e regimes especificos",
                "summary": "Normas recentes que exigem leitura separada por tipo de contribuinte.",
                "refs": [{"source": "lei-15079-2024-csll", "ranges": None}],
                "analysis": [
                    "O adicional nao deve ser tratado como mero aumento percentual. Ele exige verificar se a pessoa juridica esta no grupo legal alcancado e em qual periodo.",
                    "A decisao deve ficar registrada em nota tecnica interna, porque a fiscalizacao tende a olhar enquadramento, grupo economico, base e demonstrativo.",
                ],
            },
        ],
    },
    {
        "id": "iof",
        "jurisdiction": "Federal",
        "title": "IOF: legislacao em tela",
        "summary": "Credito, cambio, seguro, titulos e valores mobiliarios com regra, excecoes, aliquotas e prova.",
        "legacy": "federal/iof.html",
        "sources": ["lei-5143-1966-iof", "lei-8894-1994-iof", "decreto-6306-2007-iof", "decretos-iof-2025"],
        "chapters": [
            {
                "id": "matriz-aliquotas",
                "title": "Matriz legal e aliquotas",
                "summary": "Instituicao do imposto e competencia para modular aliquotas.",
                "refs": [{"source": "lei-5143-1966-iof", "ranges": None}, {"source": "lei-8894-1994-iof", "ranges": None}],
                "analysis": [
                    "IOF nao e um unico imposto operacional. A sigla cobre materialidades diferentes e cada uma pede contrato, base e responsavel proprios.",
                    "O primeiro controle e classificar a operacao: credito, cambio, seguro ou titulo. Sem isso, a aliquota certa pode estar no capitulo errado.",
                ],
            },
            {
                "id": "credito",
                "title": "Operacoes de credito",
                "summary": "Fato gerador, contribuinte, responsavel, base e cobranca no credito.",
                "refs": [{"source": "decreto-6306-2007-iof", "ranges": [(2, 10)]}],
                "analysis": [
                    "No credito, o IOF aparece no contrato e no fluxo financeiro. Prazo, principal, parcelas, renovacao, prorrogacao e liquidacao mudam a leitura.",
                    "A prova boa junta contrato, demonstrativo bancario, memoria de calculo, recolhimento e contabilizacao do custo financeiro.",
                ],
            },
            {
                "id": "cambio-seguro",
                "title": "Cambio e seguro",
                "summary": "Operacoes em moeda estrangeira e contratos de seguro.",
                "refs": [{"source": "decreto-6306-2007-iof", "ranges": [(11, 22)]}],
                "analysis": [
                    "Cambio e seguro costumam ser tratados como detalhe bancario, mas a lei exige fato gerador e base propria.",
                    "Em importacao, exportacao, remessa, premio ou indenizacao, mantenha contrato, comprovante, fechamento de cambio e documento financeiro no mesmo dossie.",
                ],
            },
            {
                "id": "titulos-valores",
                "title": "Titulos e valores mobiliarios",
                "summary": "Aplicacoes financeiras, resgates e mercados sujeitos ao IOF.",
                "refs": [{"source": "decreto-6306-2007-iof", "ranges": [(25, 34)]}],
                "analysis": [
                    "Nos titulos, a data de aplicacao e resgate muda a carga. A conferencia precisa olhar prazo, produto financeiro e demonstrativo da instituicao.",
                    "Para auditoria, extrato sintetico nao basta: a memoria deve permitir reconstruir o calculo por operacao.",
                ],
            },
            {
                "id": "atualizacoes-risco",
                "title": "Atualizacoes de aliquota e risco de vigencia",
                "summary": "Atos recentes e cuidados para aplicar a regra no periodo correto.",
                "refs": [{"source": "decretos-iof-2025", "ranges": None}, {"source": "decreto-6306-2007-iof", "ranges": [(44, 55)]}],
                "analysis": [
                    "IOF e sensivel a decreto e vigencia. Nao basta saber a regra atual: a operacao deve ser cruzada com a data do fato gerador.",
                    "Quando houver alteracao de aliquota, guarde a tabela aplicada no dia, o ato de referencia e a memoria do sistema financeiro.",
                ],
            },
        ],
    },
    {
        "id": "ipi",
        "jurisdiction": "Federal",
        "title": "IPI: legislacao em tela",
        "summary": "Industrializacao, contribuinte, TIPI, suspensoes, isencoes, creditos, obrigacoes e prova.",
        "legacy": "federal/ipi.html",
        "sources": ["ripi-2010", "tipi-2022", "lei-7798-1989-ipi", "lei-8387-1991-zfm-ipi", "decretos-tipi-2025", "in-rfb-2324-2026-ipi-suspensao"],
        "chapters": [
            {
                "id": "materialidade-industrializacao",
                "title": "Materialidade e industrializacao",
                "summary": "Quando o IPI nasce e o que a lei chama de produto industrializado.",
                "refs": [{"source": "ripi-2010", "ranges": [(1, 9)]}],
                "analysis": [
                    "IPI comeca pelo processo, nao pela aliquota. Transformacao, beneficiamento, montagem, acondicionamento e renovacao podem mudar a natureza fiscal da saida.",
                    "Antes da TIPI, confirme operacao, estabelecimento, produto, NCM e se a saida e fato gerador.",
                ],
            },
            {
                "id": "contribuintes-equiparados",
                "title": "Contribuintes e equiparados a industrial",
                "summary": "Quem responde pelo IPI mesmo sem ser fabrica classica.",
                "refs": [{"source": "ripi-2010", "ranges": [(24, 35)]}],
                "analysis": [
                    "A equiparacao a industrial e uma armadilha recorrente. Importador, comerciante e estabelecimento com operacoes especificas podem assumir obrigacoes de IPI.",
                    "A rotina segura exige cadastro de estabelecimento e fluxo de mercadoria, nao apenas CNAE.",
                ],
            },
            {
                "id": "tipi-aliquota",
                "title": "TIPI, NCM e aliquota",
                "summary": "Tabela, classificacao fiscal e atualizacoes de aliquota.",
                "refs": [{"source": "tipi-2022", "full_text": True}, {"source": "decretos-tipi-2025", "ranges": None}],
                "analysis": [
                    "TIPI e consequencia da classificacao fiscal. Uma NCM errada contamina aliquota, beneficio, documento e custo.",
                    "A boa prova junta laudo ou descricao tecnica, NCM, TIPI aplicavel na data, XML e memoria do cadastro do produto.",
                ],
            },
            {
                "id": "suspensoes-isencoes",
                "title": "Suspensoes, isencoes e areas incentivadas",
                "summary": "Tratamentos que afastam ou suspendem a cobranca quando a condicao legal existe.",
                "refs": [
                    {"source": "ripi-2010", "ranges": [(43, 55)]},
                    {"source": "lei-8387-1991-zfm-ipi", "ranges": None},
                    {"source": "in-rfb-2324-2026-ipi-suspensao", "ranges": [(1, 28)]},
                ],
                "analysis": [
                    "Suspensao e isencao nao sao sinonimos. Uma posterga a exigencia sob condicao; outra afasta a tributacao dentro do recorte legal.",
                    "A IN RFB 2.324/2026 reforca que a suspensao de IPI depende do produto, da finalidade industrial, da declaracao do adquirente, do registro quando exigido e da informacao expressa na nota fiscal.",
                ],
            },
            {
                "id": "creditos-obrigacoes",
                "title": "Creditos, livros, documento e fiscalizacao",
                "summary": "Como o imposto aparece em apuracao, escrita fiscal e auditoria.",
                "refs": [{"source": "ripi-2010", "ranges": [(225, 260), (407, 520)]}],
                "analysis": [
                    "IPI depende de trilha documental. Credito, debito, estorno e saldo credor devem conversar com entrada, saida, livro e classificacao.",
                    "A auditoria deve conseguir sair da nota fiscal, chegar no item, passar pela TIPI e fechar na apuracao.",
                ],
            },
        ],
    },
    {
        "id": "pis",
        "jurisdiction": "Federal",
        "title": "PIS/Pasep: legislacao em tela",
        "summary": "Regimes cumulativo e nao cumulativo, creditos, importacao, monofasico, aliquota zero e prova.",
        "legacy": "federal/pis-cofins.html",
        "sources": ["in-rfb-2121-2022-pis-cofins", "lei-9715-1998-pis", "lei-9718-1998-pis-cofins", "lei-10637-2002-pis", "lei-10865-2004-pis-cofins-importacao", "lei-13097-2015-pis-cofins", "lei-15394-2026-pis-cofins-residuos"],
        "chapters": [
            {
                "id": "regra-geral",
                "title": "Regra geral, contribuinte e receita",
                "summary": "O ponto de partida da contribuicao sobre receita ou faturamento.",
                "refs": [{"source": "in-rfb-2121-2022-pis-cofins", "ranges": [(1, 20)]}, {"source": "lei-9715-1998-pis", "ranges": None}],
                "analysis": [
                    "PIS/Pasep comeca pela receita e pelo regime da pessoa juridica. O erro comum e olhar produto antes de saber se a receita esta no regime certo.",
                    "A leitura pratica cruza faturamento, CST, EFD-Contribuicoes, natureza da receita e tratamento legal aplicado.",
                ],
            },
            {
                "id": "cumulativo",
                "title": "Regime cumulativo",
                "summary": "Base e tributacao sem creditamento amplo.",
                "refs": [{"source": "lei-9718-1998-pis-cofins", "ranges": [(2, 9)]}, {"source": "in-rfb-2121-2022-pis-cofins", "ranges": [(122, 149)]}],
                "analysis": [
                    "No cumulativo, a principal prova e a receita. Deducoes, exclusoes e receitas fora do campo precisam estar previstas e demonstradas.",
                    "A empresa deve manter mapa de receitas por natureza, porque o mesmo faturamento pode ter tratamentos diferentes.",
                ],
            },
            {
                "id": "nao-cumulativo-creditos",
                "title": "Nao cumulatividade e creditos",
                "summary": "Debito sobre receita e credito admitido em lei.",
                "refs": [{"source": "lei-10637-2002-pis", "ranges": [(1, 3), (15, 17)]}, {"source": "in-rfb-2121-2022-pis-cofins", "ranges": [(150, 206)]}, {"source": "lei-15394-2026-pis-cofins-residuos", "ranges": [(1, 1)]}],
                "analysis": [
                    "Credito de PIS nao nasce de despesa contabil; nasce de permissao legal, documento idoneo e vinculacao com receita tributada.",
                    "A revisao deve separar insumo, ativo, energia, frete, aluguel, monofasico, aliquota zero e vedacoes.",
                ],
            },
            {
                "id": "importacao",
                "title": "PIS/Pasep-Importacao",
                "summary": "Entrada de bens e servicos do exterior.",
                "refs": [{"source": "lei-10865-2004-pis-cofins-importacao", "ranges": [(1, 17)]}, {"source": "in-rfb-2121-2022-pis-cofins", "ranges": [(253, 354)]}],
                "analysis": [
                    "Importacao exige separar bem, servico, responsavel, base aduaneira, cambio, documento e credito possivel.",
                    "O dossie precisa juntar DI/DUIMP, invoice, contrato, conhecimento, NF-e de entrada e apuracao das contribuicoes.",
                ],
            },
            {
                "id": "beneficios-monofasico",
                "title": "Monofasico, aliquota zero, suspensao e beneficios",
                "summary": "Tratamentos especiais por produto, cadeia ou politica fiscal.",
                "refs": [{"source": "in-rfb-2121-2022-pis-cofins", "ranges": [(398, 500)]}, {"source": "lei-13097-2015-pis-cofins", "ranges": None}, {"source": "lei-15394-2026-pis-cofins-residuos", "ranges": [(1, 2)]}],
                "analysis": [
                    "Beneficio de PIS depende de produto, NCM, etapa da cadeia, destinatario e vigencia. Parecido nao basta.",
                    "Quando a empresa aplica aliquota zero, suspensao ou monofasico, o XML e a EFD-Contribuicoes precisam apontar a mesma justificativa.",
                ],
            },
        ],
    },
    {
        "id": "cofins",
        "jurisdiction": "Federal",
        "title": "Cofins: legislacao em tela",
        "summary": "Cumulatividade, nao cumulatividade, creditos, importacao, retencoes, beneficios e prova.",
        "legacy": "federal/pis-cofins.html",
        "sources": ["lc-70-1991-cofins", "lei-9718-1998-pis-cofins", "lei-10833-2003-cofins", "lei-10865-2004-pis-cofins-importacao", "in-rfb-2121-2022-pis-cofins", "lei-13097-2015-pis-cofins", "lei-15394-2026-pis-cofins-residuos"],
        "chapters": [
            {
                "id": "instituicao-receita",
                "title": "Instituicao, receita e sujeito passivo",
                "summary": "A base juridica da Cofins antes dos regimes de apuracao.",
                "refs": [{"source": "lc-70-1991-cofins", "ranges": None}, {"source": "in-rfb-2121-2022-pis-cofins", "ranges": [(1, 20)]}],
                "analysis": [
                    "Cofins deve ser lida por receita, regime e excecao. O nome da atividade nao resolve sozinho a tributacao.",
                    "No fechamento, a receita contabil precisa reconciliar com notas, EFD-Contribuicoes, exclusoes e base declarada.",
                ],
            },
            {
                "id": "cumulativo",
                "title": "Regime cumulativo",
                "summary": "Receita bruta, exclusoes e apuracao sem credito amplo.",
                "refs": [{"source": "lei-9718-1998-pis-cofins", "ranges": [(2, 9)]}, {"source": "in-rfb-2121-2022-pis-cofins", "ranges": [(122, 149)]}],
                "analysis": [
                    "A Cofins cumulativa costuma ser simples na aliquota e complexa na segregacao da receita.",
                    "A boa memoria mostra o que entrou na base, o que saiu, por qual dispositivo e em qual documento isso aparece.",
                ],
            },
            {
                "id": "nao-cumulativo-creditos",
                "title": "Nao cumulatividade e creditos",
                "summary": "Regra de debito e credito da Cofins.",
                "refs": [{"source": "lei-10833-2003-cofins", "ranges": [(1, 3), (10, 16)]}, {"source": "in-rfb-2121-2022-pis-cofins", "ranges": [(150, 206)]}, {"source": "lei-15394-2026-pis-cofins-residuos", "ranges": [(1, 1)]}],
                "analysis": [
                    "Credito de Cofins exige fundamento legal e rastreabilidade. Sem documento idoneo e vinculacao, a tese fragiliza.",
                    "A analise deve distinguir insumo, ativo, servico, frete, energia, aluguel, mercadoria monofasica e receita nao tributada.",
                ],
            },
            {
                "id": "importacao-retencoes",
                "title": "Importacao, retencoes e responsaveis",
                "summary": "Operacoes em que a cobranca aparece fora da venda comum.",
                "refs": [{"source": "lei-10865-2004-pis-cofins-importacao", "ranges": [(1, 17)]}, {"source": "lei-10833-2003-cofins", "ranges": [(30, 36)]}],
                "analysis": [
                    "Importacao e retencao deslocam a responsabilidade operacional. O financeiro precisa entrar na leitura tributaria.",
                    "Contrato, nota, DARF, comprovante, EFD e conta contabil devem fechar por prestador, tomador ou operacao de comercio exterior.",
                ],
            },
            {
                "id": "beneficios-monofasico",
                "title": "Monofasico, aliquota zero, suspensao e beneficios",
                "summary": "Tratamentos especiais por setor, produto e etapa da cadeia.",
                "refs": [{"source": "in-rfb-2121-2022-pis-cofins", "ranges": [(398, 500)]}, {"source": "lei-13097-2015-pis-cofins", "ranges": None}, {"source": "lei-15394-2026-pis-cofins-residuos", "ranges": [(1, 2)]}],
                "analysis": [
                    "Beneficio de Cofins se prova por texto legal, produto, NCM, etapa, CST e documento. A cadeia importa.",
                    "O erro mais caro e vender como aliquota zero aquilo que a lei reservou a outra etapa ou a outro produto.",
                ],
            },
        ],
    },
    {
        "id": "aduaneiro",
        "jurisdiction": "Federal",
        "title": "Aduaneiro e remessas internacionais: legislacao em tela",
        "summary": "Importacao, exportacao, remessas postais internacionais, PIS/Cofins-Importacao, documentos e prova aduaneira.",
        "legacy": "federal/aduaneiro.html",
        "sources": ["mpv-1357-2026-remessas-postais", "lei-10865-2004-pis-cofins-importacao", "in-rfb-2121-2022-pis-cofins"],
        "chapters": [
            {
                "id": "remessas-postais-tributacao-simplificada",
                "title": "Remessas postais internacionais e tributacao simplificada",
                "summary": "MP 1.357/2026 e a moldura legal para faixas e aliquotas de remessas postais internacionais.",
                "refs": [{"source": "mpv-1357-2026-remessas-postais", "ranges": [(1, 2)]}],
                "analysis": [
                    "A MP 1.357/2026 deve ser lida como alteracao expressa do Decreto-Lei 1.804/1980. Ela autoriza classificacao generica dos bens em grupos, com aliquotas constantes ou progressivas em funcao do valor das remessas, dentro dos limites indicados no texto.",
                    "Para aplicar no cadastro ou na conferencia, ainda e necessario verificar o ato do Ministro da Fazenda que efetivamente fixar ou alterar as aliquotas por faixa, produto ou programa de conformidade.",
                ],
            },
            {
                "id": "pis-cofins-importacao-prova",
                "title": "PIS/Cofins-Importacao e prova documental",
                "summary": "Entrada de bens e servicos do exterior com base, contribuinte, documento e credito possivel.",
                "refs": [{"source": "lei-10865-2004-pis-cofins-importacao", "ranges": [(1, 17)]}, {"source": "in-rfb-2121-2022-pis-cofins", "ranges": [(253, 354)]}],
                "analysis": [
                    "PIS/Cofins-Importacao nao se resolve pela etiqueta de compra internacional. A leitura exige bem ou servico, responsavel, base aduaneira, documento, pagamento, credito possivel e relacao com a EFD-Contribuicoes.",
                    "O dossie minimo deve preservar DI ou DUIMP quando houver, invoice, contrato, conhecimento de transporte, NF-e de entrada, comprovante de recolhimento e memoria de apuracao das contribuicoes.",
                ],
            },
        ],
    },
    {
        "id": "folha-clt",
        "jurisdiction": "Federal",
        "title": "Folha e CLT: legislacao em tela",
        "summary": "CLT, contrato, jornada, salario, ferias, rescisao, custeio previdenciario, FGTS, afastamentos e eSocial.",
        "legacy": "folha-clt/index.html",
        "sources": [
            "clt-1943",
            "lei-8212-1991-custeio",
            "lei-12546-2011-cprb",
            "lei-8213-1991-beneficios",
            "decreto-3048-1999-rps",
            "lei-8036-1990-fgts",
            "decreto-8373-2014-esocial",
        ],
        "chapters": [
            {
                "id": "contrato-emprego-registro",
                "title": "Contrato de trabalho, empregado e registro",
                "summary": "A relacao de emprego, o contrato individual e o registro como ponto de partida da folha.",
                "refs": [{"source": "clt-1943", "ranges": [(2, 13), (29, 41), (442, 456)]}],
                "analysis": [
                    "Folha nasce no vinculo. Antes da rubrica, confirme se existe relacao de emprego, quem e o empregador, qual contrato foi firmado e como o registro foi escriturado.",
                    "Na pratica, admissao, alteracao salarial, funcao, jornada, local de trabalho e eventos nao periodicos do eSocial precisam contar a mesma historia do contrato e da CTPS.",
                ],
            },
            {
                "id": "jornada-descanso-ferias",
                "title": "Jornada, descanso, horas extras e ferias",
                "summary": "Tempo de trabalho, descansos, remuneracao variavel e ferias como base de calculo da folha.",
                "refs": [{"source": "clt-1943", "ranges": [(57, 75), (129, 153)]}],
                "analysis": [
                    "Jornada e prova, nao apenas escala. Ponto, acordo, banco de horas, intervalo, adicional noturno, horas extras e ferias precisam fechar com a remuneracao paga.",
                    "O risco aparece quando o recibo paga uma verba correta, mas o controle de jornada ou o evento transmitido nao sustenta a quantidade, o periodo ou o adicional.",
                ],
            },
            {
                "id": "salario-remuneracao-rescisao",
                "title": "Salario, remuneracao, verbas e rescisao",
                "summary": "O que compoe remuneracao, como classificar verbas e como provar a rescisao.",
                "refs": [{"source": "clt-1943", "ranges": [(457, 467), (477, 486)]}],
                "analysis": [
                    "A natureza da verba decide reflexos trabalhistas, previdenciarios, FGTS e IRRF. Nome comercial de rubrica nao resolve incidencia.",
                    "Rescisao exige cronologia: aviso, motivo, saldo salarial, ferias, decimo terceiro quando devido, FGTS, guias, comprovantes e evento de desligamento precisam ser coerentes.",
                ],
            },
            {
                "id": "verbas-indenizatorias-remuneratorias",
                "title": "Verbas indenizatorias x remuneratorias",
                "summary": "Natureza da verba, salario-de-contribuicao, reflexos de FGTS, IRRF, eSocial e prova da rubrica.",
                "refs": [{"source": "clt-1943", "ranges": [(457, 458)]}, {"source": "lei-8212-1991-custeio", "ranges": [(28, 28)]}],
                "analysis": [
                    "A pergunta nao e o nome da rubrica; e a natureza juridica do pagamento. Verba remuneratoria, indenizatoria, ajuda de custo, premio, diaria, abono e ressarcimento mudam reflexos trabalhistas, previdenciarios, FGTS, IRRF e eSocial.",
                    "O dossie minimo deve mostrar contrato, politica interna, fato gerador da rubrica, criterio de calculo, incidencia parametrizada, evento transmitido e conciliacao com DCTFWeb, FGTS Digital e contabilidade.",
                ],
            },
            {
                "id": "seguranca-saude-afastamentos",
                "title": "Seguranca, saude, acidente e afastamentos",
                "summary": "Normas de protecao, acidente do trabalho, CAT, estabilidade e reflexos na folha.",
                "refs": [{"source": "clt-1943", "ranges": [(154, 201)]}, {"source": "lei-8213-1991-beneficios", "ranges": [(19, 23), (118, 120)]}],
                "analysis": [
                    "SST nao e anexo do DP; ela altera risco, afastamento, beneficio, estabilidade e custo previdenciario. A folha precisa conversar com laudos, exames, CAT e eventos de SST.",
                    "Quando ha afastamento, a auditoria deve reconstruir data, causa, remuneracao, beneficio, retorno, estabilidade e reflexos em FGTS e encargos.",
                ],
            },
            {
                "id": "custeio-previdenciario",
                "title": "Custeio previdenciario e salario-de-contribuicao",
                "summary": "Quem contribui, sobre qual base, com quais responsabilidades e controles.",
                "refs": [{"source": "lei-8212-1991-custeio", "ranges": [(10, 31)]}, {"source": "decreto-3048-1999-rps", "ranges": [(195, 216)]}],
                "analysis": [
                    "A contribuicao previdenciaria nasce da remuneracao paga, devida ou creditada, mas a base depende da natureza juridica da verba. Por isso rubrica e incidencia precisam ser governadas juntas.",
                    "O fechamento forte concilia folha, eSocial, DCTFWeb, DARF, contabilidade, retenções e demonstrativo por estabelecimento, lotacao e categoria.",
                ],
            },
            {
                "id": "fap-rat-sat",
                "title": "FAP, RAT/SAT e risco ambiental do trabalho",
                "summary": "Enquadramento de risco, adicional por atividade, FAP, nexo acidentario e efeito no custo previdenciario.",
                "refs": [{"source": "lei-8212-1991-custeio", "ranges": [(22, 22)]}, {"source": "decreto-3048-1999-rps", "ranges": [(202, 203)]}],
                "analysis": [
                    "FAP e RAT nao sao detalhe da guia: eles ligam atividade economica, ambiente de trabalho, historico acidentario e custeio previdenciario. A folha precisa conversar com CNAE, laudos, eventos de SST, CAT, afastamentos e contestacoes.",
                    "A auditoria deve reconstruir periodo, estabelecimento, alíquota RAT, multiplicador FAP, base da folha, eventos de SST e memoria que levou o valor para DCTFWeb.",
                ],
            },
            {
                "id": "retencao-11-cessao-mao-obra",
                "title": "Retencao de 11% na cessao de mao de obra",
                "summary": "Retencao previdenciaria em nota fiscal/fatura, cessao de mao de obra, empreitada, responsavel e compensacao.",
                "refs": [{"source": "lei-8212-1991-custeio", "ranges": [(31, 33)]}, {"source": "decreto-3048-1999-rps", "ranges": [(219, 220)]}],
                "analysis": [
                    "A retencao de 11% nasce fora da folha mensal comum, mas fecha dentro do mesmo ecossistema: contrato, nota, servico, cessao de mao de obra ou empreitada, tomador, prestador, EFD-Reinf, DCTFWeb e compensacao.",
                    "O erro comum e tratar toda prestacao de servico como retencao automatica, ou deixar de reter quando o contrato colocou trabalhadores a disposicao do tomador. A prova deve separar objeto contratual, local, supervisao, nota, base e recolhimento.",
                ],
            },
            {
                "id": "desoneracao-folha-cprb",
                "title": "Desoneracao da folha e CPRB",
                "summary": "Contribuicao sobre receita bruta, substituicao das contribuicoes patronais, setores, base, aliquota e controle por periodo.",
                "refs": [{"source": "lei-12546-2011-cprb", "ranges": [(7, 9)]}],
                "analysis": [
                    "CPRB nao e reducao generica de encargo. Ela substitui contribuicoes previdenciarias patronais em hipoteses legais delimitadas por setor, receita, periodo, regras de exclusao da base e convivencia com atividades nao abrangidas.",
                    "A revisao precisa bater CNAE/atividade real, receita bruta, exclusoes, aliquota aplicavel, periodo, memoria de segregacao, DCTFWeb/EFD-Reinf quando aplicavel e conciliacao contabil.",
                ],
            },
            {
                "id": "fgts-deposito-rescisao",
                "title": "FGTS, deposito, movimentacao e prova",
                "summary": "Conta vinculada, depositos mensais, rescisao e fiscalizacao do FGTS.",
                "refs": [{"source": "lei-8036-1990-fgts", "ranges": [(1, 23)]}],
                "analysis": [
                    "FGTS deve ser lido como obrigacao documental mensal. O deposito precisa bater com remuneracao, categoria, afastamento, rescisao e comprovante.",
                    "No controle, nao basta emitir guia: a empresa precisa provar base, empregado, competencia, pagamento, eventuais diferencas e reflexos da rescisao.",
                ],
            },
            {
                "id": "esocial-obrigacoes-digitais",
                "title": "eSocial, eventos e obrigacoes digitais",
                "summary": "A unificacao das informacoes trabalhistas, previdenciarias e fiscais em ambiente nacional.",
                "refs": [{"source": "decreto-8373-2014-esocial", "ranges": None}, {"source": "lei-8212-1991-custeio", "ranges": [(32, 33), (47, 47)]}],
                "analysis": [
                    "eSocial nao cria o direito trabalhista, mas torna a prova cronologica. Admissao, afastamento, remuneracao, pagamento, desligamento e SST ficam datados e cruzaveis.",
                    "A leitura pratica e sequencial: evento nao periodico correto, rubrica correta, evento periodico fechado, DCTFWeb coerente, FGTS Digital conciliado e contabilizacao sem sobra.",
                ],
            },
            {
                "id": "beneficios-previdenciarios-prova",
                "title": "Beneficios previdenciarios, incapacidades e prova",
                "summary": "Beneficios, segurados, incapacidade, acidente e documentos que impactam a folha.",
                "refs": [{"source": "lei-8213-1991-beneficios", "ranges": [(9, 18), (42, 63), (71, 80)]}, {"source": "decreto-3048-1999-rps", "ranges": [(18, 75)]}],
                "analysis": [
                    "Beneficio previdenciario impacta folha porque altera pagamento, afastamento, estabilidade, FGTS e retorno ao trabalho. A empresa precisa saber o que paga e o que sai da folha.",
                    "O dossie seguro junta comunicado, atestado, CAT quando aplicavel, protocolo, decisao previdenciaria, evento eSocial, calculo da folha, guia e retorno.",
                ],
            },
        ],
    },
    {
        "id": "reforma-tributaria",
        "jurisdiction": "Federal",
        "title": "Reforma Tributária: legislação em tela",
        "summary": "EC 132/2023, LC 214/2025, LC 227/2026, tabelas CST/cClassTrib/cCredPres, alíquotas, documentos fiscais, transição, créditos, split payment, benefícios e governança.",
        "legacy": "federal/reforma-tributaria.html",
        "sources": [
            "ec-132-2023-reforma",
            "lc-214-2025-reforma",
            "lc-227-2026-cgibs",
            "decreto-12955-2026-cbs",
            "resolucao-cgibs-6-2026-ibs",
            "portaria-mf-cgibs-7-2026",
            "ato-conjunto-rfb-cgibs-1-2025",
            "rfb-orientacoes-reforma-2026",
            "rfb-marcos-reforma",
            "it-2025-002-tabelas-reforma",
            "tabela-cst-cclasstrib-ibs-cbs",
            "tabela-ccredpres-ibs-cbs",
            "nt-2025-002-rtc-nfe",
        ],
        "chapters": [
            {
                "id": "matriz-ibs-cbs",
                "title": "Regra matriz do IBS e da CBS",
                "summary": "Competência, neutralidade, incidência ampla sobre bens e serviços, sujeito passivo, definições e local da operação.",
                "refs": [
                    {"source": "ec-132-2023-reforma", "ranges": [(156, 156), (195, 195)]},
                    {"source": "lc-214-2025-reforma", "ranges": [(1, 18)]},
                ],
                "analysis": [
                    "A Reforma muda a leitura de consumo: sai a lógica fragmentada de tributos sobre mercadoria, serviço e faturamento, e entra uma matriz ampla sobre operações com bens e serviços. O primeiro cuidado é separar competência constitucional, lei complementar e regra operacional.",
                    "Na prática, compras, fiscal, cadastro e tecnologia precisam falar a mesma língua: local da operação, destinatário, documento fiscal, natureza do bem ou serviço e tratamento da contraprestação passam a ser pontos centrais de apuração.",
                ],
            },
            {
                "id": "regulamentos-publicados-ibs-cbs",
                "title": "Regulamentos publicados: CBS, IBS e disposições comuns",
                "summary": "Decreto 12.955/2026, Resolução CGIBS 6/2026 e Portaria Conjunta MF/CGIBS 7/2026 em leitura coordenada.",
                "refs": [
                    {"source": "portaria-mf-cgibs-7-2026", "ranges": [(1, 2)]},
                    {"source": "decreto-12955-2026-cbs", "ranges": [(1, 2), (617, 620)]},
                    {"source": "resolucao-cgibs-6-2026-ibs", "ranges": [(1, 2), (614, 617)]},
                ],
                "analysis": [
                    "A Portaria Conjunta amarra a leitura dos dois regulamentos: o Livro I do Decreto da CBS e o Livro I da Resolução do IBS foram reconhecidos como disposições comuns. Isso evita tratar CBS e IBS como mundos separados quando a regra operacional foi desenhada de forma espelhada.",
                    "A leitura didática deve seguir esta ordem: primeiro a EC 132/2023 e a LC 214/2025; depois o decreto da CBS e a resolução do IBS; por fim, documentos fiscais, tabelas técnicas e orientações administrativas. A lei cria a matriz; o regulamento mostra como a rotina vai funcionar.",
                    "Para o escritório, este capítulo vira a porta de entrada de qualquer estudo da Reforma: se a dúvida for documento, crédito, split payment, base, alíquota, importação, exportação, regime diferenciado ou transição, ela deve voltar a esta arquitetura comum antes de virar parametrização.",
                ],
            },
            {
                "id": "cbs-regulamento-integral-decreto-12955-2026",
                "title": "CBS: Decreto 12.955/2026 em tela",
                "summary": "Regulamento integral da Contribuição Social sobre Bens e Serviços, com normas comuns, apuração, créditos, documentos, regimes e transição.",
                "refs": [
                    {"source": "decreto-12955-2026-cbs", "full_text": True},
                ],
                "analysis": [
                    "Este é o texto-base infralegal da CBS. A leitura não deve começar pela exceção: antes de falar em benefício, redução, crédito ou regime específico, confirme definições, fornecimento, adquirente, destinatário, fato gerador, base, alíquota, sujeito passivo e forma de extinção do débito.",
                    "O fiscal deve transformar o regulamento em roteiro de ERP: cadastro de operações, documento fiscal, CST, cClassTrib, base de cálculo, alíquota, crédito, recolhimento e prova. A contabilidade deve preservar memória por período para que a transição não apague a regra vigente no fato gerador.",
                ],
            },
            {
                "id": "ibs-regulamento-integral-resolucao-cgibs-6-2026",
                "title": "IBS: Resolução CGIBS 6/2026 em tela",
                "summary": "Regulamento integral do Imposto sobre Bens e Serviços, com documento fiscal, regimes, administração, créditos e regras operacionais.",
                "refs": [
                    {"source": "resolucao-cgibs-6-2026-ibs", "full_text": True},
                ],
                "analysis": [
                    "O IBS nasce com competência compartilhada, mas precisa ser operado como tributo nacionalmente padronizado. O regulamento do CGIBS deve ser lido junto da LC 214/2025 e da LC 227/2026, principalmente quando a pergunta envolve administração integrada, fiscalização, ressarcimento, créditos e distribuição da arrecadação.",
                    "Na prática, a empresa deve guardar prova de local da operação, destinatário, documento, classificação, alíquota, crédito e pagamento. A transição não autoriza apagar a memória do ICMS; ela exige conviver com ICMS, ISS, CBS e IBS durante anos.",
                ],
            },
            {
                "id": "incidencia-imunidades-fato-gerador-regulamento",
                "title": "Incidência, imunidades, fato gerador e local da operação",
                "summary": "Como os regulamentos detalham o que entra no campo de IBS/CBS, quando o fato gerador ocorre e onde a operação se localiza.",
                "refs": [
                    {"source": "decreto-12955-2026-cbs", "ranges": [(2, 25)]},
                    {"source": "resolucao-cgibs-6-2026-ibs", "ranges": [(2, 25)]},
                    {"source": "lc-214-2025-reforma", "ranges": [(1, 18)]},
                ],
                "analysis": [
                    "O erro mais caro na Reforma será pular direto para código de XML. Código é consequência. Antes dele, o analista precisa responder: houve operação com bem ou serviço? Quem forneceu? Quem adquiriu? Qual o destinatário? Onde está o local da operação? O fato gerador ocorreu em qual momento?",
                    "Imunidade e não incidência não são sinônimos de benefício. Elas ficam antes da discussão de redução ou crédito. Quando a operação estiver fora do campo tributável, a prova deve demonstrar a natureza jurídica da operação e não apenas preencher um código fiscal favorável.",
                ],
            },
            {
                "id": "base-creditos-recolhimento-split-regulamento",
                "title": "Base, créditos, ressarcimento e split payment nos regulamentos",
                "summary": "Leitura operacional da base de cálculo, não cumulatividade, extinção do débito, ressarcimento e recolhimento na liquidação financeira.",
                "refs": [
                    {"source": "decreto-12955-2026-cbs", "ranges": [(17, 52), (58, 68)]},
                    {"source": "resolucao-cgibs-6-2026-ibs", "ranges": [(17, 52), (58, 68)]},
                    {"source": "lc-214-2025-reforma", "ranges": [(27, 68)]},
                ],
                "analysis": [
                    "A Reforma aproxima três mundos que antes podiam ficar separados: documento fiscal, financeiro e crédito. Com split payment e apuração assistida, o XML deixa de ser apenas documento de venda; ele passa a conversar com extinção de débito, crédito do adquirente, pagamento e ressarcimento.",
                    "O controle interno precisa nascer por evento: emissão, cancelamento, devolução, pagamento, estorno, crédito, compensação e ressarcimento. Se a empresa não amarrar XML, recebimento, pagamento e apuração, a divergência aparecerá no cruzamento digital.",
                ],
            },
            {
                "id": "documentos-obrigacoes-2026-ato-conjunto",
                "title": "Documentos fiscais e obrigações acessórias em 2026",
                "summary": "Ato Conjunto RFB/CGIBS 1/2025 e regulamentos mostram quais documentos alimentam a apuração de IBS/CBS em 2026.",
                "refs": [
                    {"source": "ato-conjunto-rfb-cgibs-1-2025", "full_text": True},
                    {"source": "decreto-12955-2026-cbs", "ranges": [(69, 84)]},
                    {"source": "resolucao-cgibs-6-2026-ibs", "ranges": [(69, 84)]},
                    {"source": "nt-2025-002-rtc-nfe", "full_text": True},
                ],
                "analysis": [
                    "Em 2026, a Reforma entra pelo documento fiscal. O Ato Conjunto lista os documentos recepcionados e fixa o dever de emitir documento fiscal eletrônico nas operações com bens e serviços, inclusive importação e exportação.",
                    "A leitura para o departamento fiscal é direta: NF-e, NFC-e, NFS-e, CT-e, CT-e OS, BP-e, MDF-e, GTV-e e demais documentos reconhecidos precisam conversar com CST, cClassTrib, base, alíquota e campos técnicos. O ERP deve ser testado por cenário real, não apenas por exemplo genérico.",
                ],
            },
            {
                "id": "importacao-exportacao-regulamento-ibs-cbs",
                "title": "Importação, exportação e regimes aduaneiros na Reforma",
                "summary": "Tratamento de IBS/CBS sobre importações, exportações, combustível internacional, regimes aduaneiros especiais, ZPE e bens de capital.",
                "refs": [
                    {"source": "decreto-12955-2026-cbs", "ranges": [(85, 139)]},
                    {"source": "resolucao-cgibs-6-2026-ibs", "ranges": [(85, 139)]},
                    {"source": "lc-214-2025-reforma", "ranges": [(69, 100)]},
                ],
                "analysis": [
                    "Comércio exterior exige prova mais forte que a venda interna. Importação pede DI/DUIMP, documento fiscal, base, local, responsável, pagamento e crédito. Exportação pede demonstração de destino ao exterior, documento correto e coerência entre fiscal, aduaneiro e financeiro.",
                    "Regime aduaneiro especial não é benefício automático. A empresa precisa comprovar enquadramento no regime, cumprimento de prazo, destinação, baixa documental e reflexo correto no documento fiscal e na apuração.",
                ],
            },
            {
                "id": "beneficios-futuros-regimes-diferenciados-reforma",
                "title": "Benefícios futuros, cesta básica e regimes diferenciados de IBS/CBS",
                "summary": "Grupos favorecidos da Reforma: reduções, alíquota zero, regimes diferenciados, produtor rural, transportador autônomo, reciclagem e bens usados.",
                "refs": [
                    {"source": "decreto-12955-2026-cbs", "ranges": [(140, 260)]},
                    {"source": "resolucao-cgibs-6-2026-ibs", "ranges": [(140, 260)]},
                    {"source": "lc-214-2025-reforma", "ranges": [(101, 188), (234, 260)]},
                ],
                "analysis": [
                    "Benefício futuro não pode ser tratado como promessa comercial. Ele só vira matriz do portal quando o texto legal trouxer grupo, produto, serviço, sujeito, condição, redução, crédito ou alíquota zero com vigência e documento de prova.",
                    "A classificação por setor deve separar alimentos, medicamentos, saúde, educação, acessibilidade, agro, cultura, esporte, transporte, reciclagem, bens usados e regimes específicos. Cada grupo precisa indicar se o efeito é redução de alíquota, alíquota zero, crédito presumido, regime próprio ou tratamento documental.",
                ],
            },
            {
                "id": "orientacoes-operacionais-reforma-2026",
                "title": "Orientações operacionais da Receita Federal para 2026",
                "summary": "Leitura administrativa para preparar cadastro, documento fiscal, apuração assistida, teste e governança da Reforma.",
                "refs": [
                    {"source": "rfb-orientacoes-reforma-2026", "full_text": True},
                    {"source": "rfb-marcos-reforma", "full_text": True},
                ],
                "analysis": [
                    "Orientação administrativa não substitui lei, mas ajuda a transformar a lei em agenda de implementação. A leitura deve ser usada para preparar cronograma, testes, responsabilidades internas e trilha de acompanhamento de novos atos.",
                    "O escritório deve converter estas orientações em tarefas: saneamento cadastral, CST/cClassTrib, testes de XML, revisão de contratos, conciliação de documentos, acompanhamento de novos regulamentos e revisão de benefícios atuais com impacto na transição.",
                ],
            },
            {
                "id": "base-aliquotas-transicao",
                "title": "Base de cálculo, alíquotas e transição",
                "summary": "Como a lei constrói a base, fixa alíquotas de referência e disciplina a convivência de tributos antigos e novos.",
                "refs": [
                    {"source": "ec-132-2023-reforma", "ranges": [(21, 23)]},
                    {"source": "lc-214-2025-reforma", "ranges": [(12, 18), (345, 365)]},
                ],
                "analysis": [
                    "A alíquota da Reforma não deve ser lida como um número isolado. Ela depende da referência definida em lei, do período de transição, do ente competente e de eventuais reduções ou regimes diferenciados.",
                    "O impacto real aparece em preço, contrato, ERP, pedido, NF-e, contas a receber, contas a pagar e fluxo de caixa. A transição exige memória de cálculo para demonstrar por que uma operação ficou em determinado período, alíquota e tratamento.",
                ],
            },
            {
                "id": "aliquotas-padrao-documentos-fiscais",
                "title": "Alíquotas padrão, teste e referência nos documentos fiscais",
                "summary": "Percentuais de teste de 2026, regra de alíquota própria ou de referência e leitura operacional do pIBSUF, pIBSMun e pCBS.",
                "refs": [
                    {"source": "lc-214-2025-reforma", "ranges": [(12, 18), (343, 365)]},
                    {"source": "it-2025-002-tabelas-reforma", "full_text": True},
                ],
                "analysis": [
                    "A alíquota da Reforma precisa ser lida em três camadas: a lei complementar define a arquitetura, cada ente fixará suas alíquotas quando for o caso, e o documento fiscal precisa receber campos técnicos coerentes com o período.",
                    "Para 2026, o ponto prático é parametrização e teste: pIBSUF, pIBSMun e pCBS devem existir no XML quando a regra técnica exigir. A empresa ainda não pode tratar o número como carga definitiva de 2033.",
                    "O departamento fiscal deve manter tabela de vigência por ano, UF, município, tributo, CST, cClassTrib e regime. Tecnologia deve versionar regra, não sobrescrever histórico.",
                ],
            },
            {
                "id": "cst-cclasstrib-ibs-cbs",
                "title": "CST-IBS/CBS e cClassTrib: como classificar a operação",
                "summary": "Tabela completa de CST e cClassTrib, com base legal, reduções, indicadores e documentos fiscais permitidos.",
                "refs": [
                    {"source": "tabela-cst-cclasstrib-ibs-cbs", "full_text": True},
                    {"source": "lc-214-2025-reforma", "ranges": [(1, 18), (101, 188)]},
                ],
                "analysis": [
                    "O CST-IBS/CBS indica a família jurídica do tratamento: tributação integral, alíquota uniforme, redução, isenção, suspensão, não incidência, monofasia, transferência de crédito ou outra situação prevista.",
                    "O cClassTrib refina a resposta. Ele não é enfeite do XML; é o código que aponta a hipótese concreta, o artigo legal, o tipo de alíquota, a redução e os campos que o documento fiscal pode ou deve receber.",
                    "O bom cadastro nasce assim: produto ou serviço, natureza da operação, destinatário, finalidade, artigo da LC 214/2025, CST, cClassTrib, documento fiscal aplicável e evidência que sustenta a escolha.",
                ],
            },
            {
                "id": "creditos-recolhimento-split-payment",
                "title": "Créditos, recolhimento e split payment",
                "summary": "Extinção do débito, recolhimento, não cumulatividade operacional e segregação automática do imposto no pagamento.",
                "refs": [
                    {"source": "lc-214-2025-reforma", "ranges": [(27, 68)]},
                ],
                "analysis": [
                    "O crédito deixa de ser apenas uma rotina contábil posterior. Com split payment e mecanismos de extinção do débito, o documento, o pagamento e a validação do sistema se aproximam.",
                    "A empresa precisa provar três coisas: que a operação ocorreu, que o tributo foi destacado ou tratado corretamente e que o crédito ou recolhimento dialoga com o fluxo financeiro. Sem essa amarração, o risco migra do imposto para a prova.",
                ],
            },
            {
                "id": "credito-presumido-codigos-ibs-cbs",
                "title": "Créditos presumidos: cCredPres, apropriação e prova",
                "summary": "Tabela completa de cCredPres, hipóteses legais, forma de apropriação, grupos XML, alíquotas e vigência.",
                "refs": [
                    {"source": "lc-214-2025-reforma", "ranges": [(168, 171), (309, 312), (442, 450)]},
                    {"source": "tabela-ccredpres-ibs-cbs", "full_text": True},
                ],
                "analysis": [
                    "Crédito presumido na Reforma é benefício com código próprio e prova própria. A tabela cCredPres mostra se o crédito nasce no documento fiscal, por evento, ou por regra de apropriação posterior.",
                    "A leitura segura exige amarrar quatro pontos: artigo da LC 214/2025, código cCredPres, base de cálculo do crédito e impedimentos. Sem essa amarração, o crédito vira risco de glosa.",
                    "Compras e fiscal precisam identificar se o fornecedor ou a aquisição é a hipótese protegida pela lei: produtor rural não contribuinte, transportador autônomo, reciclagem, bem usado, regime automotivo ou Zona Franca de Manaus, conforme a tabela aplicável.",
                ],
            },
            {
                "id": "regimes-diferenciados-beneficios",
                "title": "Regimes diferenciados, reduções e benefícios",
                "summary": "Cesta básica, devoluções, reduções de alíquota, regimes específicos e tratamentos favorecidos previstos em lei.",
                "refs": [
                    {"source": "ec-132-2023-reforma", "ranges": [(8, 10), (12, 12), (19, 19)]},
                    {"source": "lc-214-2025-reforma", "ranges": [(101, 188), (234, 260)]},
                ],
                "analysis": [
                    "Benefício na Reforma continua sendo exceção legal, não atalho comercial. A pergunta correta é: a operação está expressamente dentro da hipótese, no período e nas condições previstas?",
                    "Para aplicar redução, alíquota zero, regime específico ou tratamento diferenciado, documente produto, serviço, destinatário, finalidade, enquadramento legal, vigência, reflexo no documento e memória de cálculo.",
                ],
            },
            {
                "id": "cbenef-icms-convivencia-reforma",
                "title": "cBenef de ICMS e Reforma: convivência sem confundir códigos",
                "summary": "Como o código de benefício estadual do ICMS convive com CST, cClassTrib e cCredPres de IBS/CBS durante a transição.",
                "refs": [
                    {"source": "ec-132-2023-reforma", "ranges": [(12, 23)]},
                    {"source": "lc-214-2025-reforma", "ranges": [(542, 544)]},
                    {"source": "lc-227-2026-cgibs", "ranges": [(109, 117), (132, 134)]},
                ],
                "analysis": [
                    "cBenef continua sendo linguagem documental ligada a benefícios de ICMS definidos pela unidade federada. A Reforma não transforma cBenef em código federal de IBS/CBS.",
                    "Para IBS e CBS, a classificação operacional passa por CST-IBS/CBS, cClassTrib e, quando houver crédito presumido, cCredPres. Durante a transição, a mesma operação pode exigir leitura do benefício de ICMS e leitura do tratamento de IBS/CBS.",
                    "O ERP deve guardar as duas histórias: a história estadual do ICMS, com cBenef e fundamento local, e a história nacional da Reforma, com LC 214/2025, CST, cClassTrib, cCredPres, alíquotas e regras técnicas do documento fiscal.",
                ],
            },
            {
                "id": "imposto-seletivo",
                "title": "Imposto Seletivo",
                "summary": "Incidência, não incidência, base, alíquotas, contribuinte, responsabilidade, apuração e pagamento do IS.",
                "refs": [
                    {"source": "lc-214-2025-reforma", "ranges": [(409, 433)]},
                ],
                "analysis": [
                    "O Imposto Seletivo não substitui a leitura do IBS e da CBS; ele adiciona uma camada sobre bens e serviços escolhidos pela lei. A materialidade, a base, a incidência única e as exclusões precisam ser lidas antes de qualquer parametrização.",
                    "No dia a dia, o risco nasce em NCM, enquadramento do produto, cadeia de fornecimento, exportação, responsabilidade e centralização do pagamento. O cadastro fiscal deve registrar por que o item entra ou sai do campo do IS.",
                ],
            },
            {
                "id": "documentos-fiscais-nfe-nfce-rtc",
                "title": "NF-e e NFC-e na Reforma: campos, validações e ERP",
                "summary": "Nota Técnica 2025.002 v1.35 em tela para entender leiaute, grupos de IBS, CBS, IS e regras de validação.",
                "refs": [
                    {"source": "nt-2025-002-rtc-nfe", "full_text": True},
                    {"source": "it-2025-002-tabelas-reforma", "full_text": True},
                ],
                "analysis": [
                    "A Reforma não chega ao contribuinte apenas por uma lei nova; ela chega pelo XML. Se o ERP não conhece grupos, campos, CST, cClassTrib, cCredPres, alíquotas e validações, a tese jurídica correta não se transforma em documento fiscal válido.",
                    "A leitura da NT deve ser feita por perfil: fiscal define enquadramento; tecnologia parametriza campos; compras e vendas testam cenários; auditoria verifica XML autorizado, rejeições, memória de cálculo e consistência com contrato e cadastro.",
                    "A rotina recomendada é criar massa de teste por operação: tributação integral, redução, isenção, suspensão, não incidência, crédito presumido, monofasia, imposto seletivo, devolução e operação com benefício de ICMS em convivência.",
                ],
            },
            {
                "id": "comite-gestor-fiscalizacao",
                "title": "Comitê Gestor, administração e fiscalização",
                "summary": "Governança do IBS, competências administrativas, fiscalização integrada, cobrança e financiamento do CGIBS.",
                "refs": [
                    {"source": "ec-132-2023-reforma", "ranges": [(156, 156)]},
                    {"source": "lc-227-2026-cgibs", "ranges": [(1, 12), (47, 51)]},
                ],
                "analysis": [
                    "O CGIBS é a peça de governança do IBS. Para o contribuinte, isso significa que a operação pode continuar local, mas a administração, a uniformização e parte relevante da fiscalização passam a ter desenho integrado.",
                    "Departamentos fiscal e jurídico devem acompanhar regulamento único, procedimentos de fiscalização, cobrança e contencioso. A prova precisa estar pronta para uma leitura coordenada entre entes.",
                ],
            },
            {
                "id": "transicao-icms-iss-beneficios-saldos",
                "title": "Transição, benefícios antigos e saldos de ICMS",
                "summary": "Extinção gradual de tributos, fundos de compensação, benefícios onerosos, distribuição da arrecadação e saldos credores.",
                "refs": [
                    {"source": "ec-132-2023-reforma", "ranges": [(12, 23)]},
                    {"source": "lc-214-2025-reforma", "ranges": [(542, 544)]},
                    {"source": "lc-227-2026-cgibs", "ranges": [(109, 117), (132, 134), (180, 182)]},
                ],
                "analysis": [
                    "A transição é o ponto em que a Reforma conversa diretamente com ICMS, ISS, PIS, Cofins e benefícios fiscais existentes. Não basta saber quando o tributo novo entra; é preciso provar o que acontece com contratos, créditos, incentivos e saldos.",
                    "Empresas com benefício estadual, saldo credor relevante, operações incentivadas ou contratos longos devem construir dossiê por período: norma antiga, norma nova, condição cumprida, efeito financeiro e reflexo documental.",
                ],
            },
        ],
    },
    {
        "id": "goias",
        "jurisdiction": "GO",
        "title": "Goias: ICMS e beneficios fiscais em tela",
        "summary": "RCTE, Anexo IX, cBenef, isencoes, reducoes, creditos outorgados, PROTEGE, ST e prova documental.",
        "legacy": "estados/goias.html",
        "sources": [
            "rcte-go",
            "anexo-ix-go",
            "decreto-go-10904-2026-anexo-ix-transmissao-energia",
            "decreto-go-10905-2026-anexo-ix-biogas-biometano",
            "in-1518-2022-cbenef-go",
        ],
        "chapters": [
            {
                "id": "icms-regra-geral",
                "title": "ICMS: incidencia, fato gerador e contribuinte",
                "summary": "A regra maior antes de qualquer beneficio.",
                "refs": [{"source": "rcte-go", "ranges": [(1, 35)]}],
                "analysis": [
                    "Em Goias, beneficio fiscal so faz sentido depois da pergunta maior: a operacao esta no campo do ICMS e quem e o contribuinte responsavel?",
                    "O departamento fiscal deve sair deste capitulo com CFOP, CST/CSOSN, base, aliquota, destinatario e documento definidos.",
                ],
            },
            {
                "id": "base-aliquota-apuracao",
                "title": "Base de calculo, aliquota e apuracao",
                "summary": "Como a operacao tributada vira valor devido ou saldo.",
                "refs": [{"source": "rcte-go", "ranges": [(36, 79)]}],
                "analysis": [
                    "Base, aliquota e apuracao sao a espinha dorsal. Beneficio que mexe na base precisa explicar se altera credito, estorno e carga final.",
                    "A memoria deve bater XML, EFD, livro, guia, conta contabil e demonstrativo interno.",
                ],
            },
            {
                "id": "beneficios-regra-maior",
                "title": "Beneficios fiscais: regra maior e condicionantes",
                "summary": "A porta de entrada do Anexo IX e das condicoes de fruicao.",
                "refs": [{"source": "rcte-go", "ranges": [(80, 87)]}, {"source": "anexo-ix-go", "ranges": [(1, 5)]}],
                "analysis": [
                    "Beneficio goiano nao e permissao generica. Ele nasce no RCTE, ganha detalhe no Anexo IX e pode exigir regularidade, recolhimento, fundo, termo ou prova especifica.",
                    "Antes de aplicar, transforme cada condicao em checklist: produto, NCM, operacao, destinatario, periodo, adimplencia, documento e cBenef.",
                ],
            },
            {
                "id": "isencoes",
                "title": "Isencoes do Anexo IX",
                "summary": "Hipoteses em que a lei afasta a exigencia do ICMS dentro de recorte fechado.",
                "refs": [{"source": "anexo-ix-go", "ranges": [(6, 7)]}],
                "analysis": [
                    "Isencao deve ser lida literalmente. Se produto, destinatario, finalidade ou prazo nao cabem no inciso, a operacao volta para a tributacao normal.",
                    "A prova da isencao deve aparecer no XML, no cadastro do produto, na EFD e no dossie da operacao.",
                ],
            },
            {
                "id": "reducao-base",
                "title": "Reducao de base de calculo",
                "summary": "Carga menor sem transformar a operacao em isenta.",
                "refs": [{"source": "anexo-ix-go", "ranges": [(8, 10)]}],
                "analysis": [
                    "Reducao de base exige calcular a carga efetiva. Ela nao autoriza simplesmente trocar aliquota no cadastro.",
                    "O ponto sensivel e credito: confira se a norma permite manutencao, exige estorno ou condiciona a fruicao.",
                ],
            },
            {
                "id": "credito-outorgado",
                "title": "Credito outorgado, programas e PROTEGE",
                "summary": "Creditos presumidos/outorgados e contrapartidas.",
                "refs": [{"source": "anexo-ix-go", "ranges": [(11, 12)]}],
                "analysis": [
                    "Credito outorgado e tecnica de apuracao, nao credito livre. O valor nasce da lei e precisa obedecer limite, condicao e eventual fundo.",
                    "Guarde ato concessivo, memoria, comprovantes, EFD, recolhimentos e demonstracao de que o beneficio nao foi acumulado indevidamente.",
                ],
            },
            {
                "id": "transmissao-energia-anexo-ix-2026",
                "title": "Linhas de transmissao de energia: Decreto 10.904/2026",
                "summary": "Reducao de base em entradas destinadas a obras de instalacao e construcao de linhas de transmissao.",
                "refs": [{"source": "decreto-go-10904-2026-anexo-ix-transmissao-energia", "full_text": True}],
                "analysis": [
                    "O Decreto 10.904/2026 altera expressamente o Anexo IX do RCTE/GO para operacoes de entrada de mercadorias e bens destinados a obras de linhas de transmissao de energia eletrica.",
                    "A aplicacao exige conferir origem da mercadoria, existencia de similar nacional quando houver importacao, percentuais do inciso, substituicao de creditos e eventual desistencia de discussao administrativa ou judicial.",
                ],
            },
            {
                "id": "biogas-biometano-investimento-2026",
                "title": "Biogas e biometano: credito especial de investimento",
                "summary": "Credito especial de investimento, TARE e limites para unidades industriais de biogas e biometano.",
                "refs": [{"source": "decreto-go-10905-2026-anexo-ix-biogas-biometano", "full_text": True}],
                "analysis": [
                    "O Decreto 10.905/2026 altera o Anexo IX para disciplinar credito especial de investimento vinculado a unidade industrial de biogas e biometano.",
                    "A fruicao depende de regime especial, limites, controles de investimento e memoria que conecte ato concessivo, apuracao, EFD, recolhimentos e eventual interdependencia entre estabelecimentos.",
                ],
            },
            {
                "id": "diferimento-st",
                "title": "Diferimento, substituicao tributaria e regimes",
                "summary": "Deslocamento do momento ou da responsabilidade pelo imposto.",
                "refs": [{"source": "rcte-go", "ranges": [(50, 79)]}, {"source": "anexo-ix-go", "ranges": [(13, 20)]}],
                "analysis": [
                    "Diferimento e ST mudam o responsavel ou o tempo da cobranca. O erro comum e tratar como beneficio sem verificar encerramento, complemento ou ressarcimento.",
                    "A prova precisa mostrar cadeia, substituto, substituido, MVA/pauta quando houver, documento e apuracao.",
                ],
            },
            {
                "id": "cbenef-prova",
                "title": "cBenef, documento fiscal e prova",
                "summary": "Como o beneficio aparece na NF-e, NFC-e, EFD e auditoria.",
                "refs": [{"source": "in-1518-2022-cbenef-go", "full_text": True}, {"source": "rcte-go", "ranges": [(167, 168)]}],
                "analysis": [
                    "cBenef e a ponte entre a tese e o XML. Ele nao cria beneficio; apenas documenta o beneficio que ja cabe na lei.",
                    "O codigo deve conversar com CST, CFOP, NCM, dispositivo do Anexo IX, valor da desoneracao e escrituração.",
                ],
            },
        ],
    },
]


TOPIC_TO_MODULES = {
    "goias-icms-beneficios": ["goias"],
    "federal-pis-cofins": ["pis", "cofins"],
    "federal-ipi": ["ipi"],
    "federal-irpj-csll": ["irpj", "csll"],
    "federal-lucro-real": ["irpj", "csll"],
    "federal-lucro-presumido": ["irpj", "csll"],
    "federal-reforma-tributaria": ["reforma-tributaria"],
    "folha-clt-previdencia": ["folha-clt"],
}

TOPIC_CHAPTER_LINKS = {
    "federal-lucro-real": [
        ("IRPJ: Lucro Real, adicoes, exclusoes e compensacoes", "irpj", "lucro-real"),
        ("IRPJ: periodo de apuracao e regimes", "irpj", "apuracao-regimes"),
        ("CSLL: compensacao, controles e prova", "csll", "compensacao-controles"),
    ],
    "federal-lucro-presumido": [
        ("IRPJ: Lucro Presumido e segregacao de receitas", "irpj", "lucro-presumido"),
        ("IRPJ: periodo de apuracao e regimes", "irpj", "apuracao-regimes"),
        ("CSLL: base, aliquotas e ajustes", "csll", "aliquotas-ajustes"),
    ],
    "federal-irpj-csll": [
        ("IRPJ: contribuintes e regra matriz", "irpj", "contribuintes-regra-matriz"),
        ("IRPJ: Lucro Real", "irpj", "lucro-real"),
        ("IRPJ: Lucro Presumido", "irpj", "lucro-presumido"),
        ("CSLL: instituicao e base", "csll", "instituicao-base"),
    ],
    "federal-pis-cofins": [
        ("PIS: regra geral e receita", "pis", "regra-geral"),
        ("PIS: nao cumulatividade e creditos", "pis", "nao-cumulativo-creditos"),
        ("Cofins: instituicao e receita", "cofins", "instituicao-receita"),
        ("Cofins: nao cumulatividade e creditos", "cofins", "nao-cumulativo-creditos"),
    ],
    "folha-clt-previdencia": [
        ("Folha: verbas indenizatorias x remuneratorias", "folha-clt", "verbas-indenizatorias-remuneratorias"),
        ("Folha: FAP, RAT/SAT e risco", "folha-clt", "fap-rat-sat"),
        ("Folha: retencao de 11% na cessao de mao de obra", "folha-clt", "retencao-11-cessao-mao-obra"),
        ("Folha: desoneracao e CPRB", "folha-clt", "desoneracao-folha-cprb"),
    ],
}

THEME_TO_MODULES = {
    "iof": ["iof"],
    "ipi": ["ipi"],
    "pis_cofins": ["pis", "cofins"],
    "irpj_csll": ["irpj", "csll"],
    "regimes": ["irpj", "csll"],
    "beneficios": ["pis", "cofins", "irpj", "csll", "reforma-tributaria"],
    "aduaneiro": ["aduaneiro", "pis", "cofins", "reforma-tributaria"],
    "previdencia_folha": ["folha-clt"],
    "reforma": ["reforma-tributaria"],
    "goias": ["goias"],
}


SIGNAL_CHAPTER_MAP = {
    "goias": {
        "aliquota": ["base-aliquota-apuracao", "reducao-base"],
        "reducao de base": ["reducao-base", "transmissao-energia-anexo-ix-2026"],
        "isencao": ["isencoes"],
        "credito outorgado": ["credito-outorgado", "biogas-biometano-investimento-2026"],
        "diferimento": ["diferimento-st"],
        "substituicao tributaria": ["diferimento-st"],
        "regime especial": ["beneficios-regra-maior", "credito-outorgado", "biogas-biometano-investimento-2026"],
        "protege/fundo": ["beneficios-regra-maior", "credito-outorgado"],
        "cBenef": ["cbenef-prova"],
        "efd/sped": ["cbenef-prova"],
        "nao incidencia": ["icms-regra-geral"],
        "exportacao": ["icms-regra-geral", "beneficios-regra-maior"],
        "suspensao": ["beneficios-regra-maior"],
    },
    "ipi": {
        "aliquota": ["tipi-aliquota"],
        "isencao": ["suspensoes-isencoes"],
        "suspensao": ["suspensoes-isencoes"],
        "exportacao": ["suspensoes-isencoes", "creditos-obrigacoes"],
        "regime especial": ["suspensoes-isencoes"],
        "credito outorgado": ["creditos-obrigacoes"],
        "efd/sped": ["creditos-obrigacoes"],
        "nao incidencia": ["materialidade-industrializacao"],
    },
    "iof": {
        "aliquota": ["matriz-aliquotas", "atualizacoes-risco"],
        "regime especial": ["atualizacoes-risco"],
        "isencao": ["matriz-aliquotas"],
        "suspensao": ["atualizacoes-risco"],
        "exportacao": ["cambio-seguro"],
    },
    "pis": {
        "aliquota": ["regra-geral", "beneficios-monofasico"],
        "isencao": ["beneficios-monofasico"],
        "suspensao": ["beneficios-monofasico"],
        "monofasico": ["beneficios-monofasico"],
        "exportacao": ["regra-geral", "nao-cumulativo-creditos"],
        "credito outorgado": ["nao-cumulativo-creditos"],
        "efd/sped": ["nao-cumulativo-creditos"],
        "nao incidencia": ["regra-geral"],
    },
    "cofins": {
        "aliquota": ["instituicao-receita", "beneficios-monofasico"],
        "isencao": ["beneficios-monofasico"],
        "suspensao": ["beneficios-monofasico"],
        "monofasico": ["beneficios-monofasico"],
        "exportacao": ["instituicao-receita", "nao-cumulativo-creditos"],
        "credito outorgado": ["nao-cumulativo-creditos"],
        "efd/sped": ["nao-cumulativo-creditos"],
        "nao incidencia": ["instituicao-receita"],
    },
    "aduaneiro": {
        "aliquota": ["remessas-postais-tributacao-simplificada"],
        "regime especial": ["remessas-postais-tributacao-simplificada"],
        "importacao": ["remessas-postais-tributacao-simplificada", "pis-cofins-importacao-prova"],
        "exportacao": ["pis-cofins-importacao-prova"],
        "efd/sped": ["pis-cofins-importacao-prova"],
    },
    "irpj": {
        "aliquota": ["apuracao-regimes"],
        "regime especial": ["apuracao-regimes"],
        "isencao": ["beneficios-jcp-prova"],
        "credito outorgado": ["beneficios-jcp-prova"],
        "efd/sped": ["lucro-real"],
        "suspensao": ["beneficios-jcp-prova"],
    },
    "csll": {
        "aliquota": ["aliquotas-ajustes", "adicional-csll"],
        "regime especial": ["adicional-csll"],
        "isencao": ["compensacao-controles"],
        "credito outorgado": ["compensacao-controles"],
        "efd/sped": ["compensacao-controles"],
    },
    "folha-clt": {
        "aliquota": ["custeio-previdenciario", "fap-rat-sat", "desoneracao-folha-cprb"],
        "regime especial": ["desoneracao-folha-cprb", "esocial-obrigacoes-digitais"],
        "efd/sped": ["esocial-obrigacoes-digitais", "retencao-11-cessao-mao-obra"],
        "isencao": ["verbas-indenizatorias-remuneratorias", "custeio-previdenciario"],
        "suspensao": ["beneficios-previdenciarios-prova"],
        "protege/fundo": ["fgts-deposito-rescisao"],
        "retencao": ["retencao-11-cessao-mao-obra"],
        "cprb": ["desoneracao-folha-cprb"],
        "rat": ["fap-rat-sat"],
        "fap": ["fap-rat-sat"],
    },
    "reforma-tributaria": {
        "aliquota": ["base-aliquotas-transicao", "aliquotas-padrao-documentos-fiscais", "base-creditos-recolhimento-split-regulamento", "regimes-diferenciados-beneficios"],
        "isencao": ["beneficios-futuros-regimes-diferenciados-reforma", "regimes-diferenciados-beneficios"],
        "suspensao": ["beneficios-futuros-regimes-diferenciados-reforma", "regimes-diferenciados-beneficios"],
        "exportacao": ["importacao-exportacao-regulamento-ibs-cbs", "imposto-seletivo", "regimes-diferenciados-beneficios"],
        "nao incidencia": ["incidencia-imunidades-fato-gerador-regulamento", "matriz-ibs-cbs", "imposto-seletivo"],
        "credito outorgado": ["credito-presumido-codigos-ibs-cbs", "beneficios-futuros-regimes-diferenciados-reforma", "transicao-icms-iss-beneficios-saldos"],
        "credito": ["base-creditos-recolhimento-split-regulamento", "creditos-recolhimento-split-payment", "credito-presumido-codigos-ibs-cbs", "transicao-icms-iss-beneficios-saldos"],
        "regime especial": ["beneficios-futuros-regimes-diferenciados-reforma", "regimes-diferenciados-beneficios", "importacao-exportacao-regulamento-ibs-cbs"],
        "efd/sped": ["documentos-obrigacoes-2026-ato-conjunto", "documentos-fiscais-nfe-nfce-rtc", "base-creditos-recolhimento-split-regulamento"],
        "fundo/contrapartida": ["transicao-icms-iss-beneficios-saldos"],
        "protege/fundo": ["transicao-icms-iss-beneficios-saldos"],
        "cBenef": ["cbenef-icms-convivencia-reforma", "cst-cclasstrib-ibs-cbs"],
        "cst": ["cst-cclasstrib-ibs-cbs"],
        "cclasstrib": ["cst-cclasstrib-ibs-cbs"],
        "ccredpres": ["credito-presumido-codigos-ibs-cbs"],
    },
}


def module_by_id(module_id: str) -> dict:
    return next(module for module in LEGAL_MODULES if module["id"] == module_id)


def chapter_by_id(module: dict, chapter_id: str) -> dict:
    return next(chapter for chapter in module["chapters"] if chapter["id"] == chapter_id)


def legal_signal_links(theme_id: str, signal_key: str, current_path: str) -> str:
    module_ids = THEME_TO_MODULES.get(theme_id, [])
    if not module_ids:
        return ""
    links = []
    seen: set[str] = set()
    for module_id in module_ids:
        module = module_by_id(module_id)
        chapter_ids = SIGNAL_CHAPTER_MAP.get(module_id, {}).get(signal_key, [])
        chapters = [chapter for chapter in module["chapters"] if chapter["id"] in chapter_ids]
        if not chapters:
            words = set(re.findall(r"[a-z0-9]+", slug(signal_key)))
            chapters = [
                chapter for chapter in module["chapters"]
                if words and words.intersection(set(re.findall(r"[a-z0-9]+", slug(chapter["id"] + " " + chapter["title"] + " " + chapter["summary"]))))
            ][:2]
        for chapter in chapters:
            href = rel_href(current_path, module_chapter_path(module, chapter))
            if href in seen:
                continue
            seen.add(href)
            links.append(f'<a href="{escape(href)}">{escape(module["title"])}: {escape(chapter["title"])}</a>')
    if not links:
        links = [
            f'<a href="{escape(rel_href(current_path, module_index_path(module_by_id(module_id))))}">'
            f'{escape(module_by_id(module_id)["title"])}</a>'
            for module_id in module_ids
        ]
    return f"""
<div class="signal-law-links">
  <strong>Lei em tela para estudar agora</strong>
  <div>{''.join(links)}</div>
</div>
"""


def module_index_path(module: dict) -> str:
    if module["jurisdiction"] == "GO":
        return "estados/goias/legislacao/index.html"
    return f"federal/legislacao/{module['id']}/index.html"


def module_chapter_path(module: dict, chapter: dict) -> str:
    if module["jurisdiction"] == "GO":
        return f"estados/goias/legislacao/{chapter['id']}.html"
    return f"federal/legislacao/{module['id']}/{chapter['id']}.html"


def load_sources(source_ids: set[str]) -> dict[str, dict]:
    loaded = {}
    for source_id in sorted(source_ids):
        source = SOURCE_DEFS[source_id]
        text = read_source_text(source)
        articles = parse_articles(text)
        loaded[source_id] = {
            "def": source,
            "text": text,
            "articles": articles,
            "chars": len(text),
        }
    return loaded


def selected_articles(source_data: dict, ranges: list[tuple[int, int]] | None, full_text: bool = False) -> list[dict]:
    if full_text:
        return source_data["articles"]
    return [article for article in source_data["articles"] if in_ranges(article, ranges)]


def render_source_link(current_path: str, source_id: str, label: str = "abrir ato integral") -> str:
    return f'<a href="{escape(rel_href(current_path, source_page_path(source_id)))}">{escape(label)}</a>'


def official_link_label(source: dict) -> str:
    url = source.get("url", "").lower()
    if "planalto.gov.br" in url:
        return "link oficial no Planalto"
    if "receita.fazenda.gov.br" in url or "gov.br/receitafederal" in url:
        return "link oficial na Receita Federal"
    if "confaz.fazenda.gov.br" in url:
        return "link oficial no CONFAZ"
    if "cgibs.gov.br" in url:
        return "link oficial no Comite Gestor do IBS"
    if "in.gov.br" in url:
        return "link oficial no Diario Oficial da Uniao"
    if "economia.go.gov.br" in url or "goias.gov.br/economia" in url:
        return "link oficial na Secretaria da Economia de Goias"
    if "sped.rfb.gov.br" in url:
        return "link oficial no SPED"
    return "link oficial da fonte normativa"


def official_anchor(source: dict) -> str:
    return f'<a href="{escape(source["url"])}" target="_blank" rel="noopener">{escape(official_link_label(source))}</a>'


def official_source_links(source_ids: list[str]) -> str:
    links = []
    for source_id in source_ids:
        source = SOURCE_DEFS[source_id]
        links.append(
            f'<a href="{escape(source["url"])}" target="_blank" rel="noopener">'
            f'{escape(source["short"])}: {escape(official_link_label(source))}</a>'
        )
    return "".join(links)


def render_article_blocks(articles: list[dict], source_id: str, current_path: str) -> str:
    if not articles:
        return '<p class="empty-note">Nao foram encontrados artigos numerados para este recorte. Consulte o ato integral nesta mesma trilha.</p>'
    rendered = []
    for article in articles:
        article_id = source_id + "-" + article["anchor"]
        rendered.append(f"""
<article class="article-block" id="{escape(article_id)}">
  <div class="article-number">Art. {escape(article['number'])}</div>
  {render_article_body(article, source_id)}
</article>
""")
    return "".join(rendered)


def render_text_chunks(text: str, source_id: str, chunk_size: int = 28000) -> str:
    chunks = []
    start = 0
    index = 1
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            natural = text.rfind("\n", start, end)
            if natural > start + 8000:
                end = natural
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(f"""
<article class="article-block text-chunk" id="{escape(source_id)}-parte-{index}">
  <div class="article-number">Parte {index}</div>
  <pre class="law-pre">{escape(chunk)}</pre>
</article>
""")
            index += 1
        start = end
    return "".join(chunks)


def split_table_row(line: str) -> list[str]:
    clean = line.strip().strip("|")
    return [cell.strip() for cell in clean.split("|")]


def is_table_separator(line: str) -> bool:
    cells = split_table_row(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in cells if cell.strip())


def row_dict(header: list[str], row: list[str]) -> dict[str, str]:
    row = row[:len(header)] + [""] * max(0, len(header) - len(row))
    return {header[index]: row[index].strip() for index in range(len(header))}


def flag_label(value: str) -> str:
    value = value.strip()
    if value == "1":
        return "Sim"
    if value == "0":
        return "Não"
    return value or "Não indicado na tabela"


def record_field(label: str, value: str, wide: bool = False) -> str:
    clean = (value or "").strip()
    if not clean:
        return ""
    klass = "record-field wide" if wide else "record-field"
    return f"""
<div class="{klass}">
  <strong>{escape(label)}</strong>
  <p>{escape(clean)}</p>
</div>
"""


def item_value(item: dict[str, str], *keys: str) -> str:
    normalized = {slug(key): value for key, value in item.items()}
    for key in keys:
        direct = item.get(key, "")
        if direct.strip():
            return direct.strip()
        value = normalized.get(slug(key), "")
        if value.strip():
            return value.strip()
    return ""


def yes_flag(value: str) -> bool:
    clean = (value or "").strip().lower()
    return clean in {"1", "s", "sim", "x", "true", "exige", "permitido"}


def normalize_legal_cell(value: str) -> str:
    clean = re.sub(r"\s*/\s*", "\n", (value or "").strip())
    clean = re.sub(r"\n{3,}", "\n\n", clean)
    return clean


def format_reduction(item: dict[str, str]) -> str:
    ibs = item_value(item, "pRedIBS")
    cbs = item_value(item, "pRedCBS")
    parts = []
    if ibs:
        parts.append(f"IBS: {ibs}%")
    if cbs:
        parts.append(f"CBS: {cbs}%")
    return "; ".join(parts)


def format_validity(item: dict[str, str]) -> str:
    start = item_value(item, "dIniVig")
    end = item_value(item, "dFimVig") or "sem fim indicado"
    updated = item_value(item, "DataAtualização", "DataAtualizacao")
    parts = []
    if start:
        parts.append(f"início: {start}")
    if start or item_value(item, "dFimVig"):
        parts.append(f"fim: {end}")
    if updated:
        parts.append(f"atualização da tabela: {updated}")
    return "; ".join(parts)


def flag_summary(item: dict[str, str], labels: list[tuple[str, str]], empty: str) -> str:
    active = [label for key, label in labels if yes_flag(item_value(item, key))]
    return "; ".join(active) if active else empty


CST_OPERATIONAL_FLAGS = [
    ("ind_gTribRegular", "grupo de tributação regular"),
    ("ind_gCredPresOper", "crédito presumido da operação"),
    ("ind_gMonoPadrao", "monofasia padrão"),
    ("ind_gMonoReten", "retenção monofásica"),
    ("ind_gMonoRet", "monofasia retida"),
    ("ind_gMonoDif", "diferimento monofásico"),
    ("ind_gEstornoCred", "estorno de crédito"),
    ("ind_gIBSCBS", "grupo IBS/CBS"),
    ("ind_gIBSCBSMono", "grupo IBS/CBS monofásico"),
    ("ind_gRed", "grupo de redução"),
    ("ind_gDif", "grupo de diferimento"),
    ("ind_gTransfCred", "transferência de crédito"),
    ("ind_ gCredPresIBSZFM", "crédito presumido IBS ZFM"),
    ("ind_gAjusteCompet", "ajuste de competência"),
    ("ind_RedutorBC", "redutor da base de cálculo"),
]


CST_DOCUMENT_FLAGS = [
    ("indNFeABI", "NF-e com bem imóvel"),
    ("indNFe", "NF-e"),
    ("indNFCe", "NFC-e"),
    ("indCTe", "CT-e"),
    ("indCTeOS", "CT-e OS"),
    ("indBPe", "BP-e"),
    ("indBPeTA", "BP-e TA"),
    ("indBPeTM", "BP-e TM"),
    ("indNF3e", "NF3-e"),
    ("indNFSe", "NFS-e"),
    ("indNFSe Via", "NFS-e via"),
    ("indNFCom", "NFCom"),
    ("indNFAg", "NF-Ag"),
    ("indNFGas", "NF-Gas"),
    ("indDERE", "DERE"),
]


def render_cst_record_guide(text: str, links: list[tuple[str, str]]) -> str:
    anchors = "".join(
        f'<a href="#{escape(anchor)}">{escape(label)}</a>'
        for anchor, label in links
    )
    links_block = f'<div class="record-guide-links">{anchors}</div>' if anchors else ""
    return f"""
<div class="record-guide">
  <p>{escape(text)}</p>
  {links_block}
</div>
"""


def render_cst_cclasstrib_cards(header: list[str], body_rows: list[list[str]], source_id: str, index: int) -> str:
    has_cclass = any(slug(cell) == "cclasstrib" for cell in header)
    cards = []
    guide_links: list[tuple[str, str]] = []
    seen_groups: set[str] = set()

    for row_index, row in enumerate(body_rows, start=1):
        item = row_dict(header, row)
        cst = item_value(item, "CST-IBS/CBS")
        cst_desc = item_value(item, "Descrição CST-IBS/CBS", "Descricao CST-IBS/CBS")
        if not cst:
            continue

        if has_cclass:
            code = item_value(item, "cClassTrib") or str(row_index)
            anchor = f"{escape(source_id)}-tabela-{index}-cclass-{escape(slug(code))}"
            title = item_value(item, "Nome cClassTrib") or item_value(item, "Descrição cClassTrib", "Descricao cClassTrib") or f"cClassTrib {code}"
            group_key = cst or code
            if group_key not in seen_groups:
                seen_groups.add(group_key)
                guide_links.append((anchor, f"CST {cst} - {subunit_summary(cst_desc, 48)}"))
            subtitle = " · ".join(part for part in [f"CST {cst}" if cst else "", f"cClassTrib {code}", item_value(item, "Tipo de Alíquota", "Tipo de Aliquota")] if part)
            fields = [
                record_field("Família CST", f"{cst} - {cst_desc}".strip(" -")),
                record_field("Hipótese cClassTrib", item_value(item, "Descrição cClassTrib", "Descricao cClassTrib") or title, True),
                record_field("Base legal em tela", normalize_legal_cell(item_value(item, "LC Redação", "LC Redacao")), True),
                record_field("Referência legal", item_value(item, "LC 214/25")),
                record_field("Tipo de alíquota", item_value(item, "Tipo de Alíquota", "Tipo de Aliquota")),
                record_field("Redução informada", format_reduction(item)),
                record_field("Indicadores operacionais", flag_summary(item, CST_OPERATIONAL_FLAGS, "nenhum indicador operacional marcado na tabela"), True),
                record_field("Documentos fiscais admitidos", flag_summary(item, CST_DOCUMENT_FLAGS, "nenhum documento fiscal marcado na tabela"), True),
                record_field("Vigência e atualização", format_validity(item)),
                record_field("Anexo da tabela", item_value(item, "ANEXO")),
                record_field("Link legal específico", item_value(item, "Link"), True),
            ]
        else:
            code = cst or str(row_index)
            anchor = f"{escape(source_id)}-tabela-{index}-cst-{escape(slug(code))}"
            title = f"CST {code} - {cst_desc}" if cst_desc else f"CST {code}"
            guide_links.append((anchor, f"CST {code}"))
            subtitle = "Família CST-IBS/CBS"
            fields = [
                record_field("Como ler", f"Este CST organiza a família operacional '{cst_desc}'. Depois dele, escolha o cClassTrib que aponta a hipótese legal concreta da operação.", True),
                record_field("Grupos exigidos ou permitidos", flag_summary(item, CST_OPERATIONAL_FLAGS, "sem grupo operacional marcado na tabela"), True),
            ]

        cards.append(f"""
<section class="legal-record-card cst-record-card" id="{anchor}">
  <header>
    <span>{escape(subtitle)}</span>
    <h4>{escape(title)}</h4>
  </header>
  <div class="record-fields">
    {''.join(fields)}
  </div>
</section>
""")

    guide_text = (
        "A tabela foi reorganizada em fichas para leitura humana: primeiro localize a família CST, depois confira o cClassTrib, a base legal, o tipo de alíquota, os campos do documento fiscal e a vigência."
        if has_cclass
        else "Este quadro resume as famílias CST. Ele serve como porta de entrada: a classificação completa acontece na ficha do cClassTrib correspondente."
    )
    return f"""
<article class="article-block legal-record-block cst-record-block" id="{escape(source_id)}-tabela-{index}">
  <div class="article-number">Tabela {index} em fichas de leitura</div>
  {render_cst_record_guide(guide_text, guide_links)}
  <div class="legal-record-list cst-record-list">{''.join(cards)}</div>
</article>
"""


def render_ccredpres_cards(header: list[str], body_rows: list[list[str]], source_id: str, index: int) -> str:
    cards = []
    for row_index, row in enumerate(body_rows, start=1):
        item = row_dict(header, row)
        code = item.get("cCredPres", "").strip() or str(row_index)
        desc = item.get("Descrição", "").strip()
        if "LC 214/2025" in item and "Descrição" in item:
            fields = [
                record_field("Base legal em tela", item.get("LC 214/2025", ""), True),
                record_field(
                    "Apropriação",
                    f"Via NF: {flag_label(item.get('Apropria via NF?', ''))}; "
                    f"via evento: {flag_label(item.get('Apropria via evento?', ''))}; "
                    f"deduz no cálculo: {flag_label(item.get('ind_DeduzCredPres', ''))}.",
                ),
                record_field(
                    "Grupos no XML",
                    f"CBS: {flag_label(item.get('ind_gCBSCredPres', ''))}; "
                    f"IBS: {flag_label(item.get('ind_gIBSCredPres', ''))}.",
                ),
                record_field(
                    "Alíquota da CBS",
                    "; ".join(part for part in [item.get("Alíquota CBS", ""), item.get("pAliqCredPresCBS", "")] if part),
                ),
                record_field(
                    "Alíquota do IBS",
                    "; ".join(part for part in [item.get("Alíquota IBS", ""), item.get("pAliqCredPresIBS", "")] if part),
                ),
                record_field("cClass da nota referenciada", item.get("cClass nota referenciada", "")),
                record_field(
                    "Vigência geral",
                    " a ".join(part for part in [item.get("dIniVig", ""), item.get("dFimVig", "") or "sem fim indicado"] if part),
                ),
                record_field(
                    "Vigência por tributo",
                    f"CBS: {item.get('dIniVigCBS', '') or 'não indicada'} a {item.get('dFimVigCBS', '') or 'sem fim indicado'}; "
                    f"IBS: {item.get('dIniVigIBS', '') or 'não indicada'} a {item.get('dFimVigIBS', '') or 'sem fim indicado'}.",
                    True,
                ),
            ]
            title = desc or f"Código {code}"
        else:
            fields = [
                record_field("Base legal em tela", item.get("LC 214/2025", ""), True),
                record_field("Percentual ou regra de alíquota", item.get("pAliq", "")),
                record_field("Base de cálculo do crédito", item.get("vBC_CredPres", "")),
                record_field("Memória de cálculo", item.get("vCred Pres", "")),
                record_field("Impedimentos e vedações", item.get("Impedimento de CredPres", ""), True),
            ]
            title = f"Memória de cálculo do cCredPres {code}"
        cards.append(f"""
<section class="legal-record-card" id="{escape(source_id)}-tabela-{index}-codigo-{escape(slug(code))}">
  <header>
    <span>cCredPres {escape(code)}</span>
    <h4>{escape(title)}</h4>
  </header>
  <div class="record-fields">
    {''.join(fields)}
  </div>
</section>
""")
    return f"""
<article class="article-block legal-record-block" id="{escape(source_id)}-tabela-{index}">
  <div class="article-number">Tabela {index} em fichas de leitura</div>
  <div class="legal-record-list">{''.join(cards)}</div>
</article>
"""


def render_markdown_table(lines: list[str], source_id: str, index: int) -> str:
    rows = [split_table_row(line) for line in lines if line.strip().startswith("|")]
    rows = [row for row in rows if row and not all(not cell for cell in row)]
    if len(rows) >= 2 and is_table_separator(lines[1]):
        header = rows[0]
        body_rows = rows[2:]
    else:
        header = rows[0] if rows else []
        body_rows = rows[1:]
    if source_id == "tabela-ccredpres-ibs-cbs":
        return render_ccredpres_cards(header, body_rows, source_id, index)
    if source_id == "tabela-cst-cclasstrib-ibs-cbs":
        return render_cst_cclasstrib_cards(header, body_rows, source_id, index)
    width = len(header)
    head = "".join(f"<th>{escape(cell)}</th>" for cell in header)
    body = []
    for row in body_rows:
        row = row[:width] + [""] * max(0, width - len(row))
        body.append("<tr>" + "".join(f"<td>{escape(cell)}</td>" for cell in row[:width]) + "</tr>")
    return f"""
<article class="article-block legal-table-block" id="{escape(source_id)}-tabela-{index}">
  <div class="article-number">Tabela {index}</div>
  <div class="law-table-wrap">
    <table class="law-table">
      <thead><tr>{head}</tr></thead>
      <tbody>{''.join(body)}</tbody>
    </table>
  </div>
</article>
"""


def render_structured_text(text: str, source_id: str) -> str:
    rendered: list[str] = []
    text_lines: list[str] = []
    table_lines: list[str] = []
    section_index = 1
    table_index = 1

    def flush_text() -> None:
        nonlocal section_index, text_lines
        block = "\n".join(text_lines).strip()
        text_lines = []
        if not block:
            return
        if block.startswith("# "):
            title = block[2:].strip()
            rendered.append(f'<h2 class="source-heading" id="{escape(source_id)}-secao-{section_index}">{escape(title)}</h2>')
            section_index += 1
            return
        if block.startswith("## "):
            title = block[3:].strip()
            rendered.append(f'<h3 class="source-heading" id="{escape(source_id)}-secao-{section_index}">{escape(title)}</h3>')
            section_index += 1
            return
        rendered.append(f"""
<article class="article-block text-chunk" id="{escape(source_id)}-parte-{section_index}">
  <div class="article-number">Bloco {section_index}</div>
  <pre class="law-pre">{escape(block)}</pre>
</article>
""")
        section_index += 1

    def flush_table() -> None:
        nonlocal table_index, table_lines
        if table_lines:
            rendered.append(render_markdown_table(table_lines, source_id, table_index))
            table_index += 1
            table_lines = []

    for line in text.splitlines():
        if line.strip().startswith("|"):
            flush_text()
            table_lines.append(line)
            continue
        flush_table()
        if line.startswith("#"):
            flush_text()
            text_lines.append(line)
            flush_text()
        else:
            text_lines.append(line)
    flush_table()
    flush_text()
    return "".join(rendered)


def render_source_body_for_ref(source: dict, source_data: dict, source_id: str, ref: dict | None, path: str) -> tuple[str, str]:
    if source.get("render") == "structured_text":
        body = render_structured_text(source_data["text"], source_id)
        count = f"{fmt_num(len(source_data['text']))} caracteres"
    elif (ref and ref.get("full_text")) or source.get("render") == "full_text":
        body = render_text_chunks(source_data["text"], source_id)
        count = f"{fmt_num(len(source_data['text']))} caracteres"
    else:
        ranges = ref.get("ranges") if ref else source.get("source_ranges")
        articles = selected_articles(source_data, ranges, False)
        body = render_article_blocks(articles, source_id, path)
        count = f"{fmt_num(len(articles))} artigos"
    return body, count


def render_analysis(module: dict, chapter: dict) -> str:
    points = "".join(f"<p>{escape(item)}</p>" for item in chapter.get("analysis", []))
    if module.get("id") == "folha-clt":
        department_grid = """
  <div class="department-grid compact">
    <article><strong>DP/RH</strong><span>Confere vinculo, jornada, rubrica, afastamento, rescisao, laudo e evento trabalhista.</span></article>
    <article><strong>Fiscal previdenciario</strong><span>Valida incidencia, salario-de-contribuicao, FAP/RAT, retencao, CPRB, DCTFWeb e EFD-Reinf.</span></article>
    <article><strong>Financeiro</strong><span>Confere DARF, FGTS Digital, retencoes, comprovantes, caixa e conciliacao com a folha.</span></article>
    <article><strong>Auditoria</strong><span>Fecha o dossie: lei, contrato, ponto, rubrica, recibo, evento, guia, memoria e evidencia.</span></article>
  </div>
"""
    else:
        department_grid = """
  <div class="department-grid compact">
    <article><strong>Fiscal</strong><span>Transforma o artigo em CST, CFOP, base, aliquota, beneficio e documento.</span></article>
    <article><strong>Contabil</strong><span>Leva a regra para receita, custo, credito, provisao, conta e conciliacao.</span></article>
    <article><strong>Financeiro</strong><span>Confere vencimento, DARF/guia, retencao, caixa, comprovante e contrato.</span></article>
    <article><strong>Auditoria</strong><span>Fecha o dossie: lei, XML, declaracao, memoria, contrato e evidencia.</span></article>
  </div>
"""
    return f"""
<section class="analysis-panel" id="analise">
  <span class="eyebrow">Depois da lei</span>
  <h2>Leitura didatica e aplicacao</h2>
  <p>Os comentarios abaixo partem do texto legal exibido acima. A aplicacao concreta deve voltar ao artigo citado e ao link oficial do ato antes de entrar no ERP, no fechamento ou em parecer.</p>
  {points}
  {department_grid}
</section>
"""


def render_module_study_path(module: dict, current_path: str) -> str:
    steps = []
    for index, chapter in enumerate(module["chapters"], start=1):
        steps.append(f"""
<a class="study-step" href="{escape(rel_href(current_path, module_chapter_path(module, chapter)))}">
  <span>{index:02d}</span>
  <strong>{escape(chapter['title'])}</strong>
  <small>{escape(chapter['summary'])}</small>
</a>
""")
    intro = (
        "Use esta trilha como auditoria de folha: comece pelo vínculo e pela jornada, classifique rubricas, confira custeio previdenciário, FGTS, eSocial, DCTFWeb, EFD-Reinf, FAP/RAT, retenções e CPRB."
        if module.get("id") == "folha-clt"
        else "Use esta trilha como aula: entenda a regra matriz, passe por base, aliquota e regime, depois feche beneficios, obrigacoes, prova e fiscalizacao."
    )
    return f"""
<section class="study-path" aria-label="Roteiro de estudo">
  <div class="section-heading">
    <span class="eyebrow">Roteiro de estudo</span>
    <h2>Ordem recomendada de leitura</h2>
    <p>{escape(intro)}</p>
  </div>
  <div class="study-step-grid">{''.join(steps)}</div>
</section>
"""


def render_chapter_flow(module: dict, chapter: dict, current_path: str, section_id: str = "") -> str:
    chapters = module["chapters"]
    current_index = next((index for index, item in enumerate(chapters) if item["id"] == chapter["id"]), 0)
    links = []
    if current_index > 0:
        previous = chapters[current_index - 1]
        links.append(("Assunto anterior", previous))
    links.append(("Indice do modulo", None))
    if current_index < len(chapters) - 1:
        next_chapter = chapters[current_index + 1]
        links.append(("Proximo assunto", next_chapter))
    items = []
    for label, target in links:
        if target is None:
            href = rel_href(current_path, module_index_path(module))
            title = module["title"]
            summary = "Volte ao mapa completo para escolher outro tema."
        else:
            href = rel_href(current_path, module_chapter_path(module, target))
            title = target["title"]
            summary = target["summary"]
        items.append(f"""
<a href="{escape(href)}">
  <span>{escape(label)}</span>
  <strong>{escape(title)}</strong>
  <small>{escape(summary)}</small>
</a>
""")
    id_attr = f' id="{escape(section_id)}"' if section_id else ""
    return f"""
<section class="chapter-flow"{id_attr} aria-label="Continuar leitura">
  {''.join(items)}
</section>
"""


def render_chapter_page(module: dict, chapter: dict, sources: dict, layout_func) -> str:
    path = module_chapter_path(module, chapter)
    sibling_links = "".join(
        f'<a href="{escape(rel_href(path, module_chapter_path(module, item)))}" class="{ "active" if item["id"] == chapter["id"] else "" }"><span>{index:02d}</span>{escape(item["title"])}</a>'
        for index, item in enumerate(module["chapters"], start=1)
    )
    source_blocks = []
    chapter_nav = []
    for ref in chapter.get("refs", []):
        source_id = ref["source"]
        source = sources[source_id]["def"]
        source_anchor = f"lei-{slug(source_id)}"
        source_label = "Tabela" if source.get("render") == "structured_text" else "Lei"
        chapter_nav.append(f'<a href="#{escape(source_anchor)}">{escape(source_label)}: {escape(source["short"])}</a>')
        body, count = render_source_body_for_ref(source, sources[source_id], source_id, ref, path)
        source_blocks.append(f"""
<section class="legal-document searchable-card" id="{escape(source_anchor)}" data-search="{escape(source['title'] + ' ' + chapter['title'])}">
  <div class="document-heading">
    <div>
      <span class="eyebrow">Texto legal</span>
      <h2>{escape(source['title'])}</h2>
      <p>{escape(source.get('note', ''))} Abaixo, o conteudo normativo aparece em tela antes da leitura pratica.</p>
    </div>
    <div class="document-actions">
      {official_anchor(source)}
      {render_source_link(path, source_id)}
      <span>{escape(str(count))}</span>
    </div>
  </div>
  {body}
</section>
""")
    body = f"""
<section class="hero-panel legal-hero">
  <div>
    <span class="eyebrow">{escape(module['title'])}</span>
    <h1>{escape(chapter['title'])}</h1>
    <p>{escape(chapter['summary'])}</p>
  </div>
  <aside class="hero-proof">
    <strong>Ordem de leitura</strong>
    <p>Primeiro o texto normativo em tela. Depois a interpretacao, sempre amarrada ao link oficial do ato.</p>
  </aside>
</section>
<section class="chapter-map" aria-label="Mapa do capitulo">
  <strong>Indice do capitulo</strong>
  <div>
    {''.join(chapter_nav)}
    <a href="#analise">Analise, aplicacao e prova</a>
    <a href="#continuar-capitulo">Continuar leitura</a>
    </div>
</section>
{render_chapter_flow(module, chapter, path)}
<section class="law-reader-grid">
  <aside class="law-sidebar">
    <strong>Capitulos</strong>
    {sibling_links}
    <strong>Voltar</strong>
    <a href="{escape(rel_href(path, module_index_path(module)))}">indice do modulo</a>
    <a href="{escape(rel_href(path, module['legacy']))}">pagina principal</a>
  </aside>
  <div class="law-reader-main">
    {''.join(source_blocks)}
    {render_analysis(module, chapter)}
    {render_chapter_flow(module, chapter, path, "continuar-capitulo")}
  </div>
</section>
"""
    return layout_func(path, f"{chapter['title']} | {module['title']}", chapter["summary"], body, "estados" if module["jurisdiction"] == "GO" else "federal")


def render_source_page(source_id: str, source_data: dict, layout_func) -> str:
    source = source_data["def"]
    path = source_page_path(source_id)
    law_body, count = render_source_body_for_ref(source, source_data, source_id, None, path)
    body = f"""
<section class="hero-panel legal-hero">
  <div>
    <span class="eyebrow">{escape(source['short'])}</span>
    <h1>{escape(source['title'])}</h1>
    <p>{escape(source.get('note', 'Texto normativo em tela para leitura por capitulos e assuntos.'))}</p>
  </div>
  <aside class="hero-proof">
    <strong>Texto em tela</strong>
    <p>{escape(count)} nesta pagina, com link oficial do ato normativo.</p>
  </aside>
</section>
<section class="legal-document">
  <div class="document-heading">
    <div>
      <span class="eyebrow">Ato normativo</span>
      <h2>{escape(source['short'])}</h2>
      <p>Use esta pagina como leitura da norma antes de aplicar qualquer conclusao pratica nos capitulos do portal. O fundamento externo e o link oficial indicado ao lado.</p>
    </div>
    <div class="document-actions">
      {official_anchor(source)}
      <span>{escape(UPDATED_ON)}</span>
    </div>
  </div>
  {law_body}
</section>
"""
    active = "estados" if source["jurisdiction"] == "GO" else "federal"
    return layout_func(path, source["title"], source.get("note", ""), body, active)


THEMATIC_GROUPS = [
    {
        "id": "regra-matriz",
        "title": "Regra matriz",
        "summary": "Comece aqui: competencia, materialidade, contribuinte, fato gerador e campo de incidencia.",
        "needles": ["REGRA", "MATRIZ", "MATERIALIDADE", "INSTITUICAO", "CONTRIBUINT", "FATO GERADOR", "RECEITA", "CONTRATO"],
    },
    {
        "id": "base-aliquota",
        "title": "Base de calculo e aliquotas",
        "summary": "Localize como a base nasce, quando muda e qual carga a lei autoriza aplicar.",
        "needles": ["BASE", "ALIQUOT", "CALCULO", "TIPI", "PRESUN", "PERCENTUAL", "REDUCAO"],
    },
    {
        "id": "regimes-apuracao",
        "title": "Regimes, apuracao e creditos",
        "summary": "Separe regime, debito, credito, compensacao, pagamento, livro e fechamento.",
        "needles": ["REGIME", "LUCRO", "CUMULATIVO", "NAO CUMULATIV", "APURACAO", "COMPENSACAO", "PAGAMENTO", "CREDITO", "LALUR"],
    },
    {
        "id": "beneficios-excecoes",
        "title": "Beneficios, isencoes e excecoes",
        "summary": "Estude reducao, isencao, suspensao, diferimento, monofasico, credito outorgado e condicoes.",
        "needles": ["BENEF", "ISENC", "SUSPENS", "DIFER", "MONOFASICO", "OUTORGADO", "ZONA FRANCA", "INCENTIV", "EXCECO"],
    },
    {
        "id": "obrigacoes-prova",
        "title": "Obrigacoes, prova e fiscalizacao",
        "summary": "Feche documento, escrituracao, declaracao, penalidade, dossie e risco de auditoria.",
        "needles": ["OBRIGAC", "DOCUMENT", "LIVRO", "ESOCIAL", "DCTF", "REINF", "FGTS", "FISCALIZ", "PENAL", "PROVA", "CBENEF"],
    },
]


def classify_chapter(chapter: dict) -> dict:
    text = ascii_upper(" ".join([chapter.get("id", ""), chapter.get("title", ""), chapter.get("summary", "")]))
    for group in THEMATIC_GROUPS:
        if any(needle in text for needle in group["needles"]):
            return group
    return THEMATIC_GROUPS[-1]


def render_module_topic_index(module: dict, current_path: str) -> str:
    buckets: dict[str, list[dict]] = {group["id"]: [] for group in THEMATIC_GROUPS}
    for chapter in module["chapters"]:
        group = classify_chapter(chapter)
        buckets[group["id"]].append(chapter)
    groups = []
    for group in THEMATIC_GROUPS:
        chapters = buckets[group["id"]]
        if not chapters:
            continue
        links = "".join(
            f'<a href="{escape(rel_href(current_path, module_chapter_path(module, chapter)))}">'
            f'<strong>{escape(chapter["title"])}</strong><span>{escape(chapter["summary"])}</span></a>'
            for chapter in chapters
        )
        groups.append(f"""
<article class="topic-index-group" id="indice-{escape(group['id'])}">
  <h3>{escape(group['title'])}</h3>
  <p>{escape(group['summary'])}</p>
  <div>{links}</div>
</article>
""")
    return f"""
<section class="topic-index">
  <div class="section-heading">
    <span class="eyebrow">Indice por tema</span>
    <h2>Escolha o assunto antes do artigo</h2>
    <p>A trilha abaixo organiza a lei por materia tributaria. Ela evita que o leitor entre direto em um inciso sem saber se esta diante da regra geral, de excecao, beneficio, apuracao ou prova.</p>
  </div>
  <div class="topic-index-grid">{''.join(groups)}</div>
</section>
"""


def render_module_index(module: dict, sources: dict, layout_func) -> str:
    path = module_index_path(module)
    chapter_cards = []
    for chapter in module["chapters"]:
        chapter_cards.append(f"""
<a class="portal-card searchable-card" href="{escape(rel_href(path, module_chapter_path(module, chapter)))}"
   data-search="{escape(module['title'] + ' ' + chapter['title'] + ' ' + chapter['summary'])}">
  <span class="card-kicker">Capitulo</span>
  <h3>{escape(chapter['title'])}</h3>
  <p>{escape(chapter['summary'])}</p>
  <small>lei em tela + leitura pratica</small>
</a>
""")
    source_cards = []
    for source_id in module["sources"]:
        source = SOURCE_DEFS[source_id]
        chars = sources[source_id]["chars"] if source_id in sources else 0
        source_cards.append(f"""
<a class="source-card searchable-card" href="{escape(rel_href(path, source_page_path(source_id)))}"
   data-search="{escape(source['title'] + ' ' + source.get('note', ''))}">
  <span>{escape(source['short'])}</span>
  <strong>{escape(source['title'])}</strong>
  <small>{fmt_num(chars)} caracteres de texto normativo; {escape(official_link_label(source))}</small>
</a>
""")
    body = f"""
<section class="hero-panel legal-hero">
  <div>
    <span class="eyebrow">Legislacao integral organizada</span>
    <h1>{escape(module['title'])}</h1>
    <p>{escape(module['summary'])}</p>
  </div>
  <aside class="hero-proof">
    <strong>Metodo</strong>
    <p>Capitulo por assunto, texto legal primeiro, link oficial citado e analise logo depois.</p>
  </aside>
</section>
<section class="law-ledger">
  <div>
    <h2>Como estudar</h2>
    <p>Abra um capitulo, leia os artigos em tela e so entao avance para a aplicacao fiscal, contabil, financeira e de auditoria.</p>
  </div>
  <div>
    <h2>Fontes base</h2>
    <p>{fmt_num(len(module['sources']))} atos normativos sustentam esta trilha. Cada ato tem pagina propria com texto em tela e link oficial da fonte competente.</p>
  </div>
  <div>
    <h2>Continuidade</h2>
    <p>Esta pagina complementa a estrutura aprovada e preserva a pagina principal ja publicada.</p>
  </div>
</section>
{render_module_study_path(module, path)}
{render_module_topic_index(module, path)}
<section class="section-wrap">
  <div class="section-heading">
    <span class="eyebrow">Capitulos</span>
    <h2>Leia por assunto</h2>
  </div>
  <div class="card-grid">{''.join(chapter_cards)}</div>
</section>
<section class="section-wrap">
  <div class="section-heading">
    <span class="eyebrow">Atos normativos</span>
    <h2>Legislacao em tela</h2>
  </div>
  <div class="source-grid">{''.join(source_cards)}</div>
</section>
<section class="continuity">
  <h2>Links oficiais dos atos</h2>
  <div>{official_source_links(module['sources'])}</div>
</section>
<section class="continuity">
  <h2>Continuar a leitura</h2>
  <div>
    <a href="{escape(rel_href(path, module['legacy']))}">pagina principal</a>
    <a href="{escape(rel_href(path, 'federal/legislacao/index.html' if module['jurisdiction'] == 'Federal' else 'estados/goias.html'))}">voltar ao portal</a>
  </div>
</section>
"""
    return layout_func(path, module["title"], module["summary"], body, "estados" if module["jurisdiction"] == "GO" else "federal")


def render_federal_hub(sources: dict, layout_func) -> str:
    path = "federal/legislacao/index.html"
    modules = [module for module in LEGAL_MODULES if module["jurisdiction"] == "Federal"]
    cards = []
    for module in modules:
        total_sources = len(module["sources"])
        total_chapters = len(module["chapters"])
        cards.append(f"""
<a class="portal-card searchable-card" href="{escape(rel_href(path, module_index_path(module)))}"
   data-search="{escape(module['title'] + ' ' + module['summary'])}">
  <span class="card-kicker">Federal</span>
  <h3>{escape(module['title'])}</h3>
  <p>{escape(module['summary'])}</p>
  <small>{total_chapters} capitulos, {total_sources} atos em tela</small>
</a>
""")
    body = f"""
<section class="hero-panel legal-hero">
  <div>
    <span class="eyebrow">Federal v1</span>
    <h1>Legislacao federal em tela</h1>
    <p>IRPJ, CSLL, IOF, IPI, PIS, Cofins, Aduaneiro, Reforma Tributaria, Folha e CLT organizados por capitulo, com texto legal antes da analise e link oficial do Planalto ou da Receita Federal em cada ato.</p>
  </div>
  <aside class="hero-proof">
    <strong>Escopo desta fase</strong>
    <p>Os proximos Estados entram somente depois da aprovacao deste conteudo.</p>
  </aside>
</section>
<section class="section-wrap">
  <div class="section-heading">
    <span class="eyebrow">Tributos</span>
    <h2>Escolha o modulo</h2>
  </div>
  <div class="card-grid">{''.join(cards)}</div>
</section>
<section class="continuity">
  <h2>Fontes oficiais federais</h2>
  <div>
    <a href="https://www.planalto.gov.br/ccivil_03/legislacao/legislacao-1.htm" target="_blank" rel="noopener">Legislacao federal no Planalto</a>
    <a href="https://www.gov.br/receitafederal/pt-br/acesso-a-informacao/legislacao" target="_blank" rel="noopener">Legislacao da Receita Federal</a>
  </div>
</section>
"""
    return layout_func(path, "Legislacao federal em tela", "IRPJ, CSLL, IOF, IPI, PIS, Cofins, Aduaneiro, Reforma Tributaria, Folha e CLT.", body, "federal")


def build_legal_pages(layout_func) -> dict[str, str]:
    source_ids: set[str] = set()
    for module in LEGAL_MODULES:
        source_ids.update(module["sources"])
        for chapter in module["chapters"]:
            for ref in chapter.get("refs", []):
                source_ids.add(ref["source"])
    sources = load_sources(source_ids)
    pages: dict[str, str] = {}
    pages["federal/legislacao/index.html"] = render_federal_hub(sources, layout_func)
    for source_id, source_data in sources.items():
        pages[source_page_path(source_id)] = render_source_page(source_id, source_data, layout_func)
    for module in LEGAL_MODULES:
        pages[module_index_path(module)] = render_module_index(module, sources, layout_func)
        for chapter in module["chapters"]:
            pages[module_chapter_path(module, chapter)] = render_chapter_page(module, chapter, sources, layout_func)
    return pages


def topic_has_legal_module(topic_id: str) -> bool:
    return topic_id in TOPIC_TO_MODULES


def legal_topic_teaser(topic_id: str, current_path: str) -> str:
    chapter_links = TOPIC_CHAPTER_LINKS.get(topic_id, [])
    if chapter_links:
        links = []
        for label, module_id, chapter_id in chapter_links:
            module = module_by_id(module_id)
            chapter = chapter_by_id(module, chapter_id)
            links.append(
                f'<a href="{escape(rel_href(current_path, module_chapter_path(module, chapter)))}">{escape(label)}</a>'
            )
        module_links = []
        for module_id in TOPIC_TO_MODULES.get(topic_id, []):
            module = module_by_id(module_id)
            module_links.append(
                f'<a href="{escape(rel_href(current_path, module_index_path(module)))}">{escape(module["title"])}</a>'
            )
        return f"""
<section class="continuity legal-continuity">
  <h2>Lei em tela por capitulo</h2>
  <p>Comece pelo capitulo especifico do tema. Cada link abre texto legal em tela antes da interpretacao e da aplicacao operacional.</p>
  <div>{''.join(links + module_links)}</div>
</section>
"""
    module_ids = TOPIC_TO_MODULES.get(topic_id, [])
    return legal_module_teaser(module_ids, current_path)


def legal_theme_teaser(theme_id: str, current_path: str) -> str:
    return legal_module_teaser(THEME_TO_MODULES.get(theme_id, []), current_path)


def legal_module_teaser(module_ids: list[str], current_path: str) -> str:
    if not module_ids:
        return ""
    links = []
    for module_id in module_ids:
        module = module_by_id(module_id)
        links.append(f'<a href="{escape(rel_href(current_path, module_index_path(module)))}">{escape(module["title"])}</a>')
    return f"""
<section class="continuity legal-continuity">
  <h2>Legislacao em tela</h2>
  <p>Esta trilha agora tem capitulos com texto normativo em tela antes da analise.</p>
  <div>{''.join(links)}</div>
</section>
"""


def federal_legislation_card(current_path: str) -> str:
    return f"""
<a class="portal-card featured searchable-card" href="{escape(rel_href(current_path, 'federal/legislacao/index.html'))}"
   data-search="IRPJ CSLL IOF IPI PIS Cofins Aduaneiro remessas internacionais Reforma Tributaria IBS CBS Imposto Seletivo Folha CLT previdencia legislacao integral lei em tela">
  <span class="card-kicker">Lei em tela</span>
  <h3>Federal: legislacao integral</h3>
  <p>IRPJ, CSLL, IOF, IPI, PIS, Cofins, Aduaneiro, Reforma Tributaria, Folha e CLT em capitulos: primeiro a lei em tela, com link oficial, depois a analise.</p>
  <small>fase federal publicada</small>
</a>
"""


def goias_legislation_card(current_path: str) -> str:
    return f"""
<a class="portal-card featured searchable-card" href="{escape(rel_href(current_path, 'estados/goias/legislacao/index.html'))}"
   data-search="Goias ICMS Anexo IX beneficios fiscais cBenef RCTE lei em tela">
  <span class="card-kicker">Goias</span>
  <h3>ICMS/GO em tela</h3>
  <p>RCTE, Anexo IX, cBenef, beneficios, reducoes, creditos e prova documental com link oficial da Secretaria da Economia.</p>
  <small>modelo estadual v1</small>
</a>
"""


def legal_search_entries() -> list[dict[str, str]]:
    entries = [
        {
            "title": "Legislacao federal em tela",
            "url": "federal/legislacao/index.html",
            "summary": "IRPJ, CSLL, IOF, IPI, PIS, Cofins, Aduaneiro, Reforma Tributaria, Folha e CLT por capitulos, com lei antes da analise.",
            "tags": "IRPJ CSLL IOF IPI PIS Cofins Aduaneiro Remessas Internacionais Reforma Tributaria IBS CBS Imposto Seletivo Folha CLT previdencia legislacao integral",
        }
    ]
    for module in LEGAL_MODULES:
        entries.append({
            "title": module["title"],
            "url": module_index_path(module),
            "summary": module["summary"],
            "tags": " ".join([module["jurisdiction"], module["id"], " ".join(module["sources"])]),
        })
        for chapter in module["chapters"]:
            entries.append({
                "title": f"{module['title']} - {chapter['title']}",
                "url": module_chapter_path(module, chapter),
                "summary": chapter["summary"],
                "tags": " ".join([module["id"], chapter["id"], chapter["title"]]),
            })
    for source_id, source in SOURCE_DEFS.items():
        entries.append({
            "title": source["title"],
            "url": source_page_path(source_id),
            "summary": source.get("note", ""),
            "tags": " ".join([source_id, source["jurisdiction"], source["short"]]),
        })
    return entries
