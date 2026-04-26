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
import unicodedata
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
BD_ROOT = Path(os.environ.get("RJC_BD_LEGISLACAO", r"C:\Users\kris2\OneDrive\COWORK\BD_LEGISLACAO"))
FEDERAL_ROOT = BD_ROOT / "#FEDERAIS-COMPILADO-ONLINE" / "legislacao_txt_completa"
UPDATED_ON = "25/04/2026"


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
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 RJC-Conhecimento/1.0"})
    with urlopen(request, timeout=120) as response:
        raw = response.read()
        content_type = response.headers.get("Content-Type", "")
    return html_to_text(raw, content_type)


def read_local_text(files: list[str]) -> str:
    chunks = []
    for file_name in files:
        path = FEDERAL_ROOT / file_name
        if not path.exists():
            raise FileNotFoundError(f"Arquivo de pesquisa nao encontrado: {path}")
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
        "sources": ["ripi-2010", "tipi-2022", "lei-7798-1989-ipi", "lei-8387-1991-zfm-ipi", "decretos-tipi-2025"],
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
                "refs": [{"source": "ripi-2010", "ranges": [(43, 55)]}, {"source": "lei-8387-1991-zfm-ipi", "ranges": None}],
                "analysis": [
                    "Suspensao e isencao nao sao sinonimos. Uma posterga a exigencia sob condicao; outra afasta a tributacao dentro do recorte legal.",
                    "O risco comum e aplicar beneficio pelo destino comercial sem provar habilitacao, finalidade, produto e documento fiscal.",
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
        "sources": ["in-rfb-2121-2022-pis-cofins", "lei-9715-1998-pis", "lei-9718-1998-pis-cofins", "lei-10637-2002-pis", "lei-10865-2004-pis-cofins-importacao", "lei-13097-2015-pis-cofins"],
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
                "refs": [{"source": "lei-10637-2002-pis", "ranges": [(1, 3), (15, 17)]}, {"source": "in-rfb-2121-2022-pis-cofins", "ranges": [(150, 206)]}],
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
                "refs": [{"source": "in-rfb-2121-2022-pis-cofins", "ranges": [(398, 500)]}, {"source": "lei-13097-2015-pis-cofins", "ranges": None}],
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
        "sources": ["lc-70-1991-cofins", "lei-9718-1998-pis-cofins", "lei-10833-2003-cofins", "lei-10865-2004-pis-cofins-importacao", "in-rfb-2121-2022-pis-cofins", "lei-13097-2015-pis-cofins"],
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
                "refs": [{"source": "lei-10833-2003-cofins", "ranges": [(1, 3), (10, 16)]}, {"source": "in-rfb-2121-2022-pis-cofins", "ranges": [(150, 206)]}],
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
                "refs": [{"source": "in-rfb-2121-2022-pis-cofins", "ranges": [(398, 500)]}, {"source": "lei-13097-2015-pis-cofins", "ranges": None}],
                "analysis": [
                    "Beneficio de Cofins se prova por texto legal, produto, NCM, etapa, CST e documento. A cadeia importa.",
                    "O erro mais caro e vender como aliquota zero aquilo que a lei reservou a outra etapa ou a outro produto.",
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
        "title": "Reforma Tributaria: legislacao em tela",
        "summary": "EC 132/2023, LC 214/2025 e LC 227/2026 organizadas por IBS, CBS, Imposto Seletivo, transicao, creditos, split payment, beneficios e governanca.",
        "legacy": "federal/reforma-tributaria.html",
        "sources": ["ec-132-2023-reforma", "lc-214-2025-reforma", "lc-227-2026-cgibs"],
        "chapters": [
            {
                "id": "matriz-ibs-cbs",
                "title": "Regra matriz do IBS e da CBS",
                "summary": "Competencia, neutralidade, incidencia ampla sobre bens e servicos, sujeito passivo, definicoes e local da operacao.",
                "refs": [
                    {"source": "ec-132-2023-reforma", "ranges": [(156, 156), (195, 195)]},
                    {"source": "lc-214-2025-reforma", "ranges": [(1, 18)]},
                ],
                "analysis": [
                    "A Reforma muda a leitura de consumo: sai a logica fragmentada de tributos sobre mercadoria, servico e faturamento, e entra uma matriz ampla sobre operacoes com bens e servicos. O primeiro cuidado e separar competencia constitucional, lei complementar e regra operacional.",
                    "Na pratica, compras, fiscal, cadastro e tecnologia precisam falar a mesma lingua: local da operacao, destinatario, documento fiscal, natureza do bem ou servico e tratamento da contraprestacao passam a ser pontos centrais de apuracao.",
                ],
            },
            {
                "id": "base-aliquotas-transicao",
                "title": "Base de calculo, aliquotas e transicao",
                "summary": "Como a lei constroi a base, fixa aliquotas de referencia e disciplina a convivencia de tributos antigos e novos.",
                "refs": [
                    {"source": "ec-132-2023-reforma", "ranges": [(21, 23)]},
                    {"source": "lc-214-2025-reforma", "ranges": [(12, 18), (345, 365)]},
                ],
                "analysis": [
                    "A aliquota da Reforma nao deve ser lida como um numero isolado. Ela depende da referencia definida em lei, do periodo de transicao, do ente competente e de eventuais reducoes ou regimes diferenciados.",
                    "O impacto real aparece em preco, contrato, ERP, pedido, NF-e, contas a receber, contas a pagar e fluxo de caixa. A transicao exige memoria de calculo para demonstrar por que uma operacao ficou em determinado periodo, aliquota e tratamento.",
                ],
            },
            {
                "id": "creditos-recolhimento-split-payment",
                "title": "Creditos, recolhimento e split payment",
                "summary": "Extincao do debito, recolhimento, nao cumulatividade operacional e segregacao automatica do imposto no pagamento.",
                "refs": [
                    {"source": "lc-214-2025-reforma", "ranges": [(27, 68)]},
                ],
                "analysis": [
                    "O credito deixa de ser apenas uma rotina contabil posterior. Com split payment e mecanismos de extincao do debito, o documento, o pagamento e a validacao do sistema se aproximam.",
                    "A empresa precisa provar tres coisas: que a operacao ocorreu, que o tributo foi destacado ou tratado corretamente e que o credito ou recolhimento dialoga com o fluxo financeiro. Sem essa amarracao, o risco migra do imposto para a prova.",
                ],
            },
            {
                "id": "regimes-diferenciados-beneficios",
                "title": "Regimes diferenciados, reducoes e beneficios",
                "summary": "Cesta basica, devolucoes, reducoes de aliquota, regimes especificos e tratamentos favorecidos previstos em lei.",
                "refs": [
                    {"source": "ec-132-2023-reforma", "ranges": [(8, 10), (12, 12), (19, 19)]},
                    {"source": "lc-214-2025-reforma", "ranges": [(101, 188), (234, 260)]},
                ],
                "analysis": [
                    "Beneficio na Reforma continua sendo excecao legal, nao atalho comercial. A pergunta correta e: a operacao esta expressamente dentro da hipotese, no periodo e nas condicoes previstas?",
                    "Para aplicar reducao, aliquota zero, regime especifico ou tratamento diferenciado, documente produto, servico, destinatario, finalidade, enquadramento legal, vigencia, reflexo no documento e memoria de calculo.",
                ],
            },
            {
                "id": "imposto-seletivo",
                "title": "Imposto Seletivo",
                "summary": "Incidencia, nao incidencia, base, aliquotas, contribuinte, responsabilidade, apuracao e pagamento do IS.",
                "refs": [
                    {"source": "lc-214-2025-reforma", "ranges": [(409, 433)]},
                ],
                "analysis": [
                    "O Imposto Seletivo nao substitui a leitura do IBS e da CBS; ele adiciona uma camada sobre bens e servicos escolhidos pela lei. A materialidade, a base, a incidencia unica e as exclusoes precisam ser lidas antes de qualquer parametrizacao.",
                    "No dia a dia, o risco nasce em NCM, enquadramento do produto, cadeia de fornecimento, exportacao, responsabilidade e centralizacao do pagamento. O cadastro fiscal deve registrar por que o item entra ou sai do campo do IS.",
                ],
            },
            {
                "id": "comite-gestor-fiscalizacao",
                "title": "Comite Gestor, administracao e fiscalizacao",
                "summary": "Governanca do IBS, competencias administrativas, fiscalizacao integrada, cobranca e financiamento do CGIBS.",
                "refs": [
                    {"source": "ec-132-2023-reforma", "ranges": [(156, 156)]},
                    {"source": "lc-227-2026-cgibs", "ranges": [(1, 12), (47, 51)]},
                ],
                "analysis": [
                    "O CGIBS e a peca de governanca do IBS. Para o contribuinte, isso significa que a operacao pode continuar local, mas a administracao, a uniformizacao e parte relevante da fiscalizacao passam a ter desenho integrado.",
                    "Departamentos fiscal e juridico devem acompanhar regulamento unico, procedimentos de fiscalizacao, cobranca e contencioso. A prova precisa estar pronta para uma leitura coordenada entre entes.",
                ],
            },
            {
                "id": "transicao-icms-iss-beneficios-saldos",
                "title": "Transicao, beneficios antigos e saldos de ICMS",
                "summary": "Extincao gradual de tributos, fundos de compensacao, beneficios onerosos, distribuicao da arrecadacao e saldos credores.",
                "refs": [
                    {"source": "ec-132-2023-reforma", "ranges": [(12, 23)]},
                    {"source": "lc-214-2025-reforma", "ranges": [(542, 544)]},
                    {"source": "lc-227-2026-cgibs", "ranges": [(109, 117), (132, 134), (180, 182)]},
                ],
                "analysis": [
                    "A transicao e o ponto em que a Reforma conversa diretamente com ICMS, ISS, PIS, Cofins e beneficios fiscais existentes. Nao basta saber quando o tributo novo entra; e preciso provar o que acontece com contratos, creditos, incentivos e saldos.",
                    "Empresas com beneficio estadual, saldo credor relevante, operacoes incentivadas ou contratos longos devem construir dossie por periodo: norma antiga, norma nova, condicao cumprida, efeito financeiro e reflexo documental.",
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
        "sources": ["rcte-go", "anexo-ix-go", "in-1518-2022-cbenef-go"],
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
}

THEME_TO_MODULES = {
    "iof": ["iof"],
    "ipi": ["ipi"],
    "pis_cofins": ["pis", "cofins"],
    "irpj_csll": ["irpj", "csll"],
    "regimes": ["irpj", "csll"],
    "beneficios": ["pis", "cofins", "irpj", "csll", "reforma-tributaria"],
    "previdencia_folha": ["folha-clt"],
    "reforma": ["reforma-tributaria"],
    "goias": ["goias"],
}


SIGNAL_CHAPTER_MAP = {
    "goias": {
        "aliquota": ["base-aliquota-apuracao", "reducao-base"],
        "reducao de base": ["reducao-base"],
        "isencao": ["isencoes"],
        "credito outorgado": ["credito-outorgado"],
        "diferimento": ["diferimento-st"],
        "substituicao tributaria": ["diferimento-st"],
        "regime especial": ["beneficios-regra-maior", "credito-outorgado"],
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
        "aliquota": ["custeio-previdenciario"],
        "regime especial": ["esocial-obrigacoes-digitais"],
        "efd/sped": ["esocial-obrigacoes-digitais"],
        "isencao": ["custeio-previdenciario"],
        "suspensao": ["beneficios-previdenciarios-prova"],
        "protege/fundo": ["fgts-deposito-rescisao"],
    },
    "reforma-tributaria": {
        "aliquota": ["base-aliquotas-transicao", "regimes-diferenciados-beneficios"],
        "isencao": ["regimes-diferenciados-beneficios"],
        "suspensao": ["regimes-diferenciados-beneficios"],
        "exportacao": ["imposto-seletivo", "regimes-diferenciados-beneficios"],
        "nao incidencia": ["matriz-ibs-cbs", "imposto-seletivo"],
        "credito outorgado": ["transicao-icms-iss-beneficios-saldos"],
        "credito": ["creditos-recolhimento-split-payment", "transicao-icms-iss-beneficios-saldos"],
        "regime especial": ["regimes-diferenciados-beneficios"],
        "efd/sped": ["creditos-recolhimento-split-payment", "comite-gestor-fiscalizacao"],
        "fundo/contrapartida": ["transicao-icms-iss-beneficios-saldos"],
        "protege/fundo": ["transicao-icms-iss-beneficios-saldos"],
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


def render_analysis(chapter: dict) -> str:
    points = "".join(f"<p>{escape(item)}</p>" for item in chapter.get("analysis", []))
    return f"""
<section class="analysis-panel" id="analise">
  <span class="eyebrow">Depois da lei</span>
  <h2>Leitura didatica e aplicacao</h2>
  <p>Os comentarios abaixo partem do texto legal exibido acima. A aplicacao concreta deve voltar ao artigo citado e ao link oficial do ato antes de entrar no ERP, no fechamento ou em parecer.</p>
  {points}
  <div class="department-grid compact">
    <article><strong>Fiscal</strong><span>Transforma o artigo em CST, CFOP, base, aliquota, beneficio e documento.</span></article>
    <article><strong>Contabil</strong><span>Leva a regra para receita, custo, credito, provisao, conta e conciliacao.</span></article>
    <article><strong>Financeiro</strong><span>Confere vencimento, DARF/guia, retencao, caixa, comprovante e contrato.</span></article>
    <article><strong>Auditoria</strong><span>Fecha o dossie: lei, XML, declaracao, memoria, contrato e evidencia.</span></article>
  </div>
</section>
"""


def render_chapter_page(module: dict, chapter: dict, sources: dict, layout_func) -> str:
    path = module_chapter_path(module, chapter)
    sibling_links = "".join(
        f'<a href="{escape(rel_href(path, module_chapter_path(module, item)))}" class="{ "active" if item["id"] == chapter["id"] else "" }">{escape(item["title"])}</a>'
        for item in module["chapters"]
    )
    source_blocks = []
    chapter_nav = []
    for ref in chapter.get("refs", []):
        source_id = ref["source"]
        source = sources[source_id]["def"]
        source_anchor = f"lei-{slug(source_id)}"
        chapter_nav.append(f'<a href="#{escape(source_anchor)}">Lei: {escape(source["short"])}</a>')
        if ref.get("full_text") or source.get("render") == "full_text":
            body = render_text_chunks(sources[source_id]["text"], source_id)
            count = f"{fmt_num(len(sources[source_id]['text']))} caracteres"
        else:
            articles = selected_articles(sources[source_id], ref.get("ranges"), False)
            body = render_article_blocks(articles, source_id, path)
            count = f"{fmt_num(len(articles))} artigos"
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
  </div>
</section>
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
    {render_analysis(chapter)}
  </div>
</section>
"""
    return layout_func(path, f"{chapter['title']} | {module['title']}", chapter["summary"], body, "estados" if module["jurisdiction"] == "GO" else "federal")


def render_source_page(source_id: str, source_data: dict, layout_func) -> str:
    source = source_data["def"]
    path = source_page_path(source_id)
    source_ranges = source.get("source_ranges")
    if source.get("render") == "full_text":
        law_body = render_text_chunks(source_data["text"], source_id)
        count = f"{fmt_num(len(source_data['text']))} caracteres"
    else:
        articles = selected_articles(source_data, source_ranges, False)
        law_body = render_article_blocks(articles, source_id, path)
        count = f"{fmt_num(len(articles))} artigos"
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
    <p>IRPJ, CSLL, IOF, IPI, PIS, Cofins, Reforma Tributaria, Folha e CLT organizados por capitulo, com texto legal antes da analise e link oficial do Planalto ou da Receita Federal em cada ato.</p>
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
    return layout_func(path, "Legislacao federal em tela", "IRPJ, CSLL, IOF, IPI, PIS, Cofins, Reforma Tributaria, Folha e CLT.", body, "federal")


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
   data-search="IRPJ CSLL IOF IPI PIS Cofins Reforma Tributaria IBS CBS Imposto Seletivo Folha CLT previdencia legislacao integral lei em tela">
  <span class="card-kicker">Lei em tela</span>
  <h3>Federal: legislacao integral</h3>
  <p>IRPJ, CSLL, IOF, IPI, PIS, Cofins, Reforma Tributaria, Folha e CLT em capitulos: primeiro a lei em tela, com link oficial, depois a analise.</p>
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
            "summary": "IRPJ, CSLL, IOF, IPI, PIS, Cofins, Reforma Tributaria, Folha e CLT por capitulos, com lei antes da analise.",
            "tags": "IRPJ CSLL IOF IPI PIS Cofins Reforma Tributaria IBS CBS Imposto Seletivo Folha CLT previdencia legislacao integral",
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
