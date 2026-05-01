#!/usr/bin/env python3
"""Capture official IBS/CBS regulation texts into versioned local sources."""

from __future__ import annotations

import hashlib
import re
import time
import urllib.request
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "legal_sources" / "reforma_tributaria"
ORIG_DIR = OUT_DIR / "originais"
TODAY = date.today().isoformat()


HTML_SOURCES = [
    {
        "file": "Decreto_12955_2026_Regulamento_CBS.txt",
        "title": "Decreto nº 12.955/2026 - Regulamento da CBS",
        "url": "https://www.in.gov.br/en/web/dou/-/decreto-n-12.955-de-29-de-abril-de-2026-702415229",
        "start": "DECRETO Nº 12.955, DE 29 DE ABRIL DE 2026",
        "kind": "decreto",
    },
    {
        "file": "Ato_Conjunto_RFB_CGIBS_1_2025_Obrigacoes_2026.txt",
        "title": "Ato Conjunto RFB/CGIBS nº 1/2025 - obrigações acessórias de IBS/CBS em 2026",
        "url": "https://www.in.gov.br/en/web/dou/-/ato-conjunto-rfb/cgibs-n-1-de-22-de-dezembro-de-2025-677624586",
        "start": "ATO CONJUNTO RFB/CGIBS Nº 1, DE 22 DE DEZEMBRO DE 2025",
        "kind": "ato conjunto",
    },
    {
        "file": "Receita_Orientacoes_Reforma_2026.txt",
        "title": "Receita Federal - Orientações da Reforma Tributária para 2026",
        "url": "https://www.gov.br/receitafederal/pt-br/acesso-a-informacao/acoes-e-programas/programas-e-atividades/reforma-consumo/orientacoes-2026",
        "start": "Orientações da Reforma Tributária para 2026",
        "kind": "orientacao administrativa",
    },
    {
        "file": "Receita_Marcos_Regulatorios_Reforma.txt",
        "title": "Receita Federal - Principais marcos regulatórios da Reforma Tributária",
        "url": "https://www.gov.br/receitafederal/pt-br/acesso-a-informacao/acoes-e-programas/programas-e-atividades/reforma-consumo/marcos",
        "start": "Principais Marcos Regulatórios",
        "kind": "orientacao administrativa",
    },
]

PDF_SOURCES = [
    {
        "file": "Resolucao_CGIBS_6_2026_Regulamento_IBS.txt",
        "pdf": "Resolucao_CGIBS_6_2026_Regulamento_IBS.pdf",
        "title": "Resolução CGIBS nº 6/2026 - Regulamento do IBS",
        "url": "https://www.cgibs.gov.br/upload/arquivos/202604/30084927-res-cgibs-n-6-30-abr-2026-regulamenta-o-ibs.pdf",
        "kind": "resolucao",
    },
    {
        "file": "Portaria_Conjunta_MF_CGIBS_7_2026.txt",
        "pdf": "Portaria_Conjunta_MF_CGIBS_7_2026.pdf",
        "title": "Portaria Conjunta MF/CGIBS nº 7/2026",
        "url": "https://www.cgibs.gov.br/upload/arquivos/202604/30094136-sei-mgi-60959979-portaria-conjunta.pdf",
        "kind": "portaria conjunta",
    },
]


class VisibleTextParser(HTMLParser):
    skip_tags = {"script", "style", "head", "noscript"}
    block_tags = {"p", "div", "br", "tr", "td", "th", "li", "h1", "h2", "h3", "h4", "section", "article"}

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

    def text(self) -> str:
        text = "".join(self.parts)
        text = re.sub(r"[\t\r\f\v]+", " ", text)
        text = re.sub(r" *\n *", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


def clean_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def request_bytes(url: str, accept: str) -> bytes:
    last_error: Exception | None = None
    for attempt in range(1, 5):
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) RJC-Conhecimento/2.0",
                "Accept": accept,
                "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
                "Referer": "https://www.cgibs.gov.br/regulamentos" if "cgibs.gov.br" in url else "https://www.gov.br/",
                "Connection": "close",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                return response.read()
        except Exception as error:  # network resets are common on official PDF hosts
            last_error = error
            time.sleep(attempt * 1.5)
    assert last_error is not None
    raise last_error


def trim_from_marker(text: str, marker: str) -> str:
    index = text.find(marker)
    if index < 0:
        return text
    text = text[index:]
    # DOU pages repeat title/navigation before the certified content.
    published = text.find("Publicado em:")
    if published > 0:
        title_again = text.find(marker, published)
        if title_again > 0:
            text = text[title_again:]
    return text


def html_to_text(raw: bytes, marker: str) -> str:
    html = raw.decode("utf-8", errors="ignore")
    parser = VisibleTextParser()
    parser.feed(html)
    text = parser.text()
    return clean_text(trim_from_marker(text, marker))


def pdf_to_text(path: Path) -> str:
    reader = PdfReader(str(path))
    pages: list[str] = []
    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = clean_text(text)
        if text:
            pages.append(f"## Página {index}\n{text}")
    return "\n\n".join(pages)


def header(source: dict, raw: bytes) -> str:
    digest = hashlib.sha256(raw).hexdigest()
    return "\n".join(
        [
            f"# {source['title']}",
            "",
            f"Tipo: {source['kind']}",
            f"Fonte oficial: {source['url']}",
            f"Data de captura: {TODAY}",
            f"SHA256 do arquivo capturado: {digest}",
            "",
            "## Texto em tela",
            "",
        ]
    )


def capture_html(source: dict) -> None:
    raw = request_bytes(source["url"], "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
    text = html_to_text(raw, source["start"])
    (OUT_DIR / source["file"]).write_text(header(source, raw) + text + "\n", encoding="utf-8", newline="\n")


def capture_pdf(source: dict) -> None:
    raw = request_bytes(source["url"], "application/pdf,*/*")
    pdf_path = ORIG_DIR / source["pdf"]
    pdf_path.write_bytes(raw)
    text = pdf_to_text(pdf_path)
    (OUT_DIR / source["file"]).write_text(header(source, raw) + text + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ORIG_DIR.mkdir(parents=True, exist_ok=True)
    for source in HTML_SOURCES:
        capture_html(source)
        print(f"capturado: {source['file']}")
    for source in PDF_SOURCES:
        capture_pdf(source)
        print(f"capturado: {source['file']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
