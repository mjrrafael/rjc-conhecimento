#!/usr/bin/env python3
"""Capture official state tax sources as local text packages."""

from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from datetime import date
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


def fetch_pdf(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "RJC-Conhecimento/1.0"})
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


def pdf_to_text(pdf_bytes: bytes) -> tuple[str, int]:
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        pages: list[str] = []
        for page_number, page in enumerate(doc, start=1):
            text = page.get_text("text").strip()
            pages.append(f"===== PAGINA {page_number} =====\n{text}\n")
        return "\n".join(pages).strip() + "\n", len(doc)


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


def capture_state(uf: str) -> None:
    uf = uf.upper()
    if uf not in STATE_PACKS:
        raise SystemExit(f"UF ainda sem pacote configurado: {uf}")

    pack = STATE_PACKS[uf]
    capture_date = today_iso()
    output_dir = OUTPUT_ROOT / pack["path_region"] / uf
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest_sources = []
    sha_by_file: dict[str, str] = {}
    for source in pack["sources"]:
        print(f"Capturando {source['id']}...")
        pdf_bytes = fetch_pdf(source["url"])
        extracted_text, page_count = pdf_to_text(pdf_bytes)
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
    parser.add_argument("--uf", required=True, help="UF a capturar, por exemplo BA")
    args = parser.parse_args()
    capture_state(args.uf)


if __name__ == "__main__":
    main()
