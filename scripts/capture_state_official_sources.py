#!/usr/bin/env python3
"""Capture official state tax sources as local text packages."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.request
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / "data" / "fontes-estaduais-curadas"


STATE_PACKS = {
    "BA": {
        "uf": "BA",
        "estado": "Bahia",
        "regiao": "Nordeste",
        "path_region": "nordeste",
        "portal": "https://www.sefaz.ba.gov.br/legislacao/textos-legais/",
        "sources": [
            {
                "id": "BA_LEI_7014_1996_ICMS",
                "title": "Lei nº 7.014/1996 - Lei básica do ICMS da Bahia",
                "theme": "ICMS - lei material",
                "type": "lei estadual",
                "url": "https://mbusca.sefaz.ba.gov.br/DITRI/leis/leis_estaduais/legest_1996_7014_icmscomnotas.pdf",
                "filename": "BA_LEI_7014_1996_ICMS_{date}.txt",
            },
            {
                "id": "BA_DEC_13780_2012_RICMS",
                "title": "Decreto nº 13.780/2012 - Regulamento do ICMS da Bahia",
                "theme": "ICMS - regulamento",
                "type": "decreto estadual",
                "url": "https://mbusca.sefaz.ba.gov.br/DITRI/normas_complementares/decretos/decreto_2012_13780_ricms_texto_2021.pdf",
                "filename": "BA_DEC_13780_2012_RICMS_{date}.txt",
            },
            {
                "id": "BA_RICMS_ANEXO_1_ST_2026",
                "title": "Anexo 1 do RICMS/BA - Substituição tributária vigente 2026",
                "theme": "ICMS - substituição tributária",
                "type": "anexo regulamentar",
                "url": "https://mbusca.sefaz.ba.gov.br/DITRI/normas_complementares/decretos/decreto_2012_13780_ricms_anexo_1_vigente_2026.pdf",
                "filename": "BA_RICMS_ANEXO_1_ST_{date}.txt",
            },
            {
                "id": "BA_RICMS_ANEXO_2_RURAL",
                "title": "Anexo 2 do RICMS/BA - Crédito fiscal nas atividades rurais",
                "theme": "ICMS - crédito fiscal rural",
                "type": "anexo regulamentar",
                "url": "https://mbusca.sefaz.ba.gov.br/DITRI/normas_complementares/decretos/decreto_2012_13780_ricms_anexo_2.pdf",
                "filename": "BA_RICMS_ANEXO_2_RURAL_{date}.txt",
            },
            {
                "id": "BA_LEI_7980_2001_DESENVOLVE",
                "title": "Lei nº 7.980/2001 - Programa DESENVOLVE",
                "theme": "ICMS - benefício fiscal e desenvolvimento industrial",
                "type": "lei estadual",
                "url": "https://mbusca.sefaz.ba.gov.br/DITRI/leis/leis_estaduais/legest_2001_7980.pdf",
                "filename": "BA_LEI_7980_2001_DESENVOLVE_{date}.txt",
            },
            {
                "id": "BA_DEC_8205_2002_DESENVOLVE",
                "title": "Decreto nº 8.205/2002 - Regulamento do Programa DESENVOLVE",
                "theme": "ICMS - benefício fiscal e desenvolvimento industrial",
                "type": "decreto estadual",
                "url": "https://mbusca.sefaz.ba.gov.br/DITRI/normas_complementares/decretos/decreto_2002_8205_desenvolve.pdf",
                "filename": "BA_DEC_8205_2002_DESENVOLVE_{date}.txt",
            },
            {
                "id": "BA_DEC_18802_2018_PROIND",
                "title": "Decreto nº 18.802/2018 - Programa de Estímulo à Indústria da Bahia",
                "theme": "ICMS - benefício fiscal industrial",
                "type": "decreto estadual",
                "url": "https://mbusca.sefaz.ba.gov.br/DITRI/normas_complementares/decretos/decreto_2018_18802.pdf",
                "filename": "BA_DEC_18802_2018_PROIND_{date}.txt",
            },
            {
                "id": "BA_LEI_9829_2005_PRONAVAL",
                "title": "Lei nº 9.829/2005 - PRONAVAL",
                "theme": "ICMS - benefício fiscal setorial",
                "type": "lei estadual",
                "url": "https://mbusca.sefaz.ba.gov.br/DITRI/leis/leis_estaduais/legest_2005_9829.pdf",
                "filename": "BA_LEI_9829_2005_PRONAVAL_{date}.txt",
            },
            {
                "id": "BA_DEC_11015_2008_PRONAVAL",
                "title": "Decreto nº 11.015/2008 - Regulamento do PRONAVAL",
                "theme": "ICMS - benefício fiscal setorial",
                "type": "decreto estadual",
                "url": "https://mbusca.sefaz.ba.gov.br/DITRI/normas_complementares/decretos/decreto_2008_11015.pdf",
                "filename": "BA_DEC_11015_2008_PRONAVAL_{date}.txt",
            },
            {
                "id": "BA_LEI_7025_1997_CREDITO_PRESUMIDO",
                "title": "Lei nº 7.025/1997 - Crédito presumido do ICMS",
                "theme": "ICMS - crédito presumido",
                "type": "lei estadual",
                "url": "https://mbusca.sefaz.ba.gov.br/DITRI/leis/leis_estaduais/legest_1997_7025.pdf",
                "filename": "BA_LEI_7025_1997_CREDITO_PRESUMIDO_{date}.txt",
            },
            {
                "id": "BA_DEC_6734_1997_CREDITO_PRESUMIDO",
                "title": "Decreto nº 6.734/1997 - Crédito presumido do ICMS",
                "theme": "ICMS - crédito presumido",
                "type": "decreto estadual",
                "url": "https://mbusca.sefaz.ba.gov.br/DITRI/normas_complementares/decretos/decreto_1997_6734.pdf",
                "filename": "BA_DEC_6734_1997_CREDITO_PRESUMIDO_{date}.txt",
            },
            {
                "id": "BA_DEC_4316_1995_INFORMATICA_ELETRONICA",
                "title": "Decreto nº 4.316/1995 - Informática, eletrônica e telecomunicações",
                "theme": "ICMS - benefício fiscal setorial",
                "type": "decreto estadual",
                "url": "https://mbusca.sefaz.ba.gov.br/DITRI/normas_complementares/decretos/decreto_1995_4316.pdf",
                "filename": "BA_DEC_4316_1995_INFORMATICA_ELETRONICA_{date}.txt",
            },
            {
                "id": "BA_DEC_18270_2018_BENEFICIOS_LC160",
                "title": "Decreto nº 18.270/2018 - Relação de atos de benefícios fiscais",
                "theme": "ICMS - benefícios fiscais e Convênio ICMS 190/2017",
                "type": "decreto estadual",
                "url": "https://mbusca.sefaz.ba.gov.br/DITRI/normas_complementares/decretos/decreto_2018_18270.pdf",
                "filename": "BA_DEC_18270_2018_BENEFICIOS_LC160_{date}.txt",
            },
            {
                "id": "BA_DEC_18288_2018_BENEFICIOS_LC160",
                "title": "Decreto nº 18.288/2018 - Alteração da relação de atos de benefícios fiscais",
                "theme": "ICMS - benefícios fiscais e Convênio ICMS 190/2017",
                "type": "decreto estadual",
                "url": "https://mbusca.sefaz.ba.gov.br/DITRI/normas_complementares/decretos/decreto_2018_18288.pdf",
                "filename": "BA_DEC_18288_2018_BENEFICIOS_LC160_{date}.txt",
            },
            {
                "id": "BA_PORT_273_2014_EFD_INCENTIVOS",
                "title": "Portaria nº 273/2014 - EFD dos incentivos fiscais",
                "theme": "ICMS - obrigações acessórias e benefícios fiscais",
                "type": "portaria estadual",
                "url": "https://www.sefaz.ba.gov.br/docs/inspetoria-eletronica/icms/incentivos_fiscais_orientacoes_lancamento.pdf",
                "filename": "BA_PORT_273_2014_EFD_INCENTIVOS_{date}.txt",
            },
        ],
    },
}


def today_iso() -> str:
    return date.today().isoformat()


class VisibleTextParser(HTMLParser):
    skip_tags = {"script", "style", "svg", "noscript"}
    block_tags = {"p", "div", "section", "article", "li", "tr", "td", "th", "h1", "h2", "h3", "h4", "br"}

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
        if self.skip_stack or not data.strip():
            return
        self.parts.append(data)

    def text(self) -> str:
        lines = []
        for line in "".join(self.parts).splitlines():
            clean = re.sub(r"\s+", " ", line).strip()
            if clean:
                lines.append(clean)
        return "\n".join(lines).strip() + "\n"


def fetch_url(url: str) -> tuple[bytes, str]:
    request = urllib.request.Request(url, headers={"User-Agent": "RJC-Conhecimento/1.0"})
    with urllib.request.urlopen(request, timeout=120) as response:
        content_type = response.headers.get("Content-Type", "")
        return response.read(), content_type


def pdf_to_text(pdf_bytes: bytes) -> tuple[str, int]:
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        pages: list[str] = []
        for page_number, page in enumerate(doc, start=1):
            text = page.get_text("text").strip()
            pages.append(f"===== PAGINA {page_number} =====\n{text}\n")
        return "\n".join(pages).strip() + "\n", len(doc)


def html_to_text(html_bytes: bytes) -> tuple[str, int]:
    raw = html_bytes.decode("utf-8", errors="ignore")
    parser = VisibleTextParser()
    parser.feed(raw)
    return parser.text(), 1


def bytes_to_text(payload: bytes) -> tuple[str, int]:
    for encoding in ("utf-8", "windows-1252", "latin-1"):
        try:
            return payload.decode(encoding), 1
        except UnicodeDecodeError:
            continue
    return payload.decode("utf-8", errors="ignore"), 1


def source_to_text(source: dict[str, str]) -> tuple[str, int]:
    payload, content_type = fetch_url(source["url"])
    declared = (source.get("format") or "").lower()
    url_lower = source["url"].lower().split("?", 1)[0]
    if declared == "pdf" or "application/pdf" in content_type.lower() or url_lower.endswith(".pdf"):
        return pdf_to_text(payload)
    if declared in {"html", "htm"} or "html" in content_type.lower() or url_lower.endswith((".html", ".htm", ".aspx")):
        return html_to_text(payload)
    return bytes_to_text(payload)


def write_source_text(target: Path, source: dict[str, str], capture_date: str, text: str) -> None:
    header = "\n".join(
        [
            f"TITULO: {source['title']}",
            f"TEMA: {source['theme']}",
            f"TIPO: {source['type']}",
            f"FONTE PUBLICA: {source['url']}",
            f"DATA DA CAPTURA: {capture_date}",
            "",
            "TEXTO EXTRAIDO",
            "",
        ]
    )
    target.write_text(header + text, encoding="utf-8", newline="\n")


def load_packs(pack_file: str | None) -> dict:
    if not pack_file:
        return STATE_PACKS
    data = json.loads(Path(pack_file).read_text(encoding="utf-8"))
    return data.get("packs", data)


def capture_state(uf: str, packs: dict | None = None, capture_date: str | None = None) -> None:
    uf = uf.upper()
    packs = packs or STATE_PACKS
    if uf not in packs:
        raise SystemExit(f"UF ainda sem pacote configurado: {uf}")

    pack = packs[uf]
    capture_date = capture_date or today_iso()
    output_dir = OUTPUT_ROOT / pack["path_region"] / uf
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest_sources = []
    sha_by_file: dict[str, str] = {}
    for source in pack["sources"]:
        print(f"Capturando {source['id']}...")
        extracted_text, page_count = source_to_text(source)
        filename = source["filename"].format(date=capture_date)
        target = output_dir / filename
        write_source_text(target, source, capture_date, extracted_text)
        file_bytes = target.read_bytes()
        sha_by_file[filename] = hashlib.sha256(file_bytes).hexdigest()
        manifest_sources.append(
            {
                "id": source["id"],
                "titulo": source["title"],
                "tema": source["theme"],
                "tipo": source["type"],
                "url": source["url"],
                "arquivo": filename,
                "paginas_pdf": page_count,
                "caracteres_extraidos": len(extracted_text),
                "sha256": sha_by_file[filename],
            }
        )

    manifest = {
        "uf": pack["uf"],
        "estado": pack["estado"],
        "regiao": pack["regiao"],
        "status_curadoria": "em_segmentacao",
        "data_captura": capture_date,
        "portal_legislacao": pack["portal"],
        "fontes": manifest_sources,
        "arquivos": [source["arquivo"] for source in manifest_sources],
        "sha256": sha_by_file,
        "observacoes": (
            "Pacote inicial capturado a partir do portal da Secretaria da Fazenda. "
            "A publicação profunda depende de segmentação por capítulos, revisão de vigência, "
            "benefícios fiscais, regimes especiais e prova documental."
        ),
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"Pacote salvo em {output_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--uf", help="UF a capturar, por exemplo BA")
    parser.add_argument("--pack-file", help="JSON externo com pacotes por UF.")
    parser.add_argument("--date", help="Data de captura a usar no nome dos arquivos, em YYYY-MM-DD.")
    parser.add_argument("--list", action="store_true", help="Lista UFs configuradas e sai.")
    args = parser.parse_args()
    packs = load_packs(args.pack_file)
    if args.list:
        for uf in sorted(packs):
            print(f"{uf}: {packs[uf].get('estado', uf)}")
        return
    if not args.uf:
        raise SystemExit("Informe --uf ou use --list.")
    capture_state(args.uf, packs=packs, capture_date=args.date)


if __name__ == "__main__":
    main()
