#!/usr/bin/env python3
"""Build master audit indexes for the RJC open tax portal.

The files produced here are not conclusions by themselves. They are the
versioned operating layer that tells the portal what is already published,
what is only available as source material, and what still needs curatorship
before the site can teach it as a reliable tax position.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import unicodedata
import urllib.request
from collections import Counter, defaultdict
from datetime import date
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from state_legal_pages import (  # noqa: E402
    BENEFIT_SECTOR_DEFS,
    STATE_NAMES,
    benefit_sector_results,
    collect_state_documents,
)
from validated_benefits import build_validated_benefits  # noqa: E402


TODAY = date.today().isoformat()


def resolve_bd_federal() -> Path:
    configured = os.environ.get("RJC_BD_LEGISLACAO")
    candidates = []
    if configured:
        candidates.append(Path(configured))
    candidates.extend([
        Path.home() / "OneDrive" / "COWORK" / "BD_LEGISLACAO",
        Path(r"C:\Users\kris2\OneDrive\COWORK\BD_LEGISLACAO"),
    ])
    for candidate in candidates:
        federal = candidate / "#FEDERAIS-COMPILADO-ONLINE" / "legislacao_txt_completa"
        if federal.exists():
            return federal
    return candidates[0] / "#FEDERAIS-COMPILADO-ONLINE" / "legislacao_txt_completa"


BD_FEDERAL = resolve_bd_federal()

OUT_TAXONOMY = ROOT / "data" / "master_taxonomy.json"
OUT_COVERAGE = ROOT / "data" / "master_source_coverage.json"
OUT_BENEFITS = ROOT / "data" / "benefits_crosswalk.json"
OUT_BENEFITS_QUARANTINE = ROOT / "data" / "benefits_quarantine.json"
OUT_CONFAZ = ROOT / "data" / "confaz_ultimos_5_anos.json"
OUT_DOC = ROOT / "docs" / "master-audit.md"


FEDERAL_REQUIREMENTS = [
    {
        "id": "irpj",
        "title": "IRPJ",
        "terms": ["IRPJ", "RIR", "Lei 9.430", "Lei 9.249"],
        "expected_files": ["Decreto_9580_2018_Regulamento_IRPJ.txt", "Lei_9430_1996_Compilada_IRPJ.txt"],
        "minimum": "regra matriz, contribuinte, lucro real, presumido, arbitrado, adicionais, pagamentos, ECF e prova",
    },
    {
        "id": "csll",
        "title": "CSLL",
        "terms": ["CSLL", "Lei 7.689", "Lei 15.079"],
        "expected_files": ["Lei_7689_1988_CSLL_Original.txt", "Lei_15079_2024_Adicional_CSLL.txt"],
        "minimum": "base, aliquotas, adicional, compensacao, base negativa, ECF e prova",
    },
    {
        "id": "pis",
        "title": "PIS/Pasep",
        "terms": ["PIS", "Pasep", "Lei 10.637", "IN RFB 2.121"],
        "expected_files": ["Lei_10637_2002_PIS_Nao_Cumulativo.txt", "IN_RFB_2121_2022_PIS_COFINS_Parte1.txt"],
        "minimum": "cumulativo, nao cumulativo, importacao, monofasico, aliquota zero, creditos e EFD",
    },
    {
        "id": "cofins",
        "title": "Cofins",
        "terms": ["COFINS", "Lei 10.833", "LC 70", "IN RFB 2.121"],
        "expected_files": ["Lei_10833_2003_Compilada_COFINS.txt", "LC_70_1991_COFINS_Original.txt"],
        "minimum": "cumulativo, nao cumulativo, importacao, retencoes, monofasico, creditos e EFD",
    },
    {
        "id": "ipi",
        "title": "IPI",
        "terms": ["IPI", "TIPI", "RIPI"],
        "expected_files": ["Decreto_7212_2010_RIPI.txt", "TIPI_Vigente_2022_Parte1.txt"],
        "minimum": "industrializacao, equiparados, fato gerador, TIPI, suspensoes, isencoes, ZFM e prova",
    },
    {
        "id": "iof",
        "title": "IOF",
        "terms": ["IOF", "Decreto 6.306", "Lei 5.143"],
        "expected_files": ["Decreto_6306_2007_Regulamento_IOF.txt", "Decreto_12499_2025_IOF_Alteracoes2.txt"],
        "minimum": "credito, cambio, seguro, titulos, valores mobiliarios, aliquotas e alteracoes vigentes",
    },
    {
        "id": "irpf_pf",
        "title": "IRPF e pessoa fisica",
        "terms": ["IRPF", "pessoa fisica", "Lei 9.250"],
        "expected_files": ["Lei_9250_1995_IRPF.txt", "Lei_15191_2025_IRPF_Tabela_Progressiva.txt"],
        "minimum": "rendimentos, deducoes, ganho de capital, tabela progressiva, declaracao e prova",
    },
    {
        "id": "simples_mei",
        "title": "Simples Nacional e MEI",
        "terms": ["Simples Nacional", "MEI", "LC 123"],
        "expected_files": ["LC_123_2006_Simples_Nacional.txt", "LC_128_2008_MEI.txt"],
        "minimum": "enquadramento, anexos, sublimites, segregacao de receita, monofasico/ST/retencoes e PGDAS-D",
    },
    {
        "id": "lucro_real",
        "title": "Lucro Real",
        "terms": ["Lucro Real", "Lalur", "Lacs"],
        "expected_files": ["Decreto_9580_2018_Regulamento_IRPJ.txt", "Lei_9430_1996_Compilada_IRPJ.txt"],
        "minimum": "adicoes, exclusoes, compensacoes, estimativa, trimestral/anual, ECD, ECF e prova contabil",
    },
    {
        "id": "lucro_presumido",
        "title": "Lucro Presumido",
        "terms": ["Lucro Presumido", "presuncao", "Lei 8.981"],
        "expected_files": ["Lei_8981_1995_Lucro_Real_Presumido.txt", "Decreto_12808_2026_Lucro_Presumido.txt"],
        "minimum": "percentuais, segregacao de receita, limite, retencoes, PIS/Cofins cumulativo e ECF",
    },
    {
        "id": "lucro_arbitrado",
        "title": "Lucro Arbitrado",
        "terms": ["Lucro Arbitrado", "arbitramento"],
        "expected_files": ["Lei_8981_1995_Lucro_Real_Presumido.txt", "Decreto_9580_2018_Regulamento_IRPJ.txt"],
        "minimum": "hipoteses de arbitramento, base, percentuais, provas e riscos",
    },
    {
        "id": "comercio_exterior",
        "title": "Importacao, exportacao e regimes aduaneiros",
        "terms": ["importacao", "exportacao", "aduaneiro", "drawback", "Siscomex"],
        "expected_files": ["Decreto_6759_2009_Regulamento_Aduaneiro.txt", "Lei_10865_2004_PIS_COFINS_Importacao.txt"],
        "minimum": "II, IPI importacao, PIS/Cofins-Importacao, despacho, regimes especiais, drawback, REINTEGRA e prova",
    },
    {
        "id": "beneficios_federais",
        "title": "Beneficios federais, DIRBI e reducao de beneficios",
        "terms": ["DIRBI", "beneficios fiscais", "renuncias", "Lei 14.973"],
        "expected_files": ["Lei_14973_2024_DIRBI.txt", "Lei_15321_2025_DIRBI_Obrigatoriedade.txt", "Decreto_12861_2026_Regulamento_Beneficios.txt"],
        "minimum": "habilitacao, fruicao, declaracao, DIRBI, reducao de beneficios, prova e controles",
    },
    {
        "id": "reforma",
        "title": "Reforma Tributaria",
        "terms": ["IBS", "CBS", "Imposto Seletivo", "cClassTrib", "cCredPres"],
        "expected_files": [
            "EC_132_2023_Reforma_Tributaria.txt",
            "LC_214_2025_Compilada_IBS_CBS_IS.txt",
            "LC_227_2026_Comite_Gestor_IBS.txt",
            "data/legal_sources/reforma_tributaria/Decreto_12955_2026_Regulamento_CBS.txt",
            "data/legal_sources/reforma_tributaria/Resolucao_CGIBS_6_2026_Regulamento_IBS.txt",
            "data/legal_sources/reforma_tributaria/Portaria_Conjunta_MF_CGIBS_7_2026.txt",
            "data/legal_sources/reforma_tributaria/Ato_Conjunto_RFB_CGIBS_1_2025_Obrigacoes_2026.txt",
        ],
        "minimum": "EC 132, LC 214, LC 227, Decreto CBS, Resolucao IBS, Portaria comum, Ato Conjunto 2026, CST, cClassTrib, cCredPres, transicao e documentos fiscais",
    },
    {
        "id": "folha_clt",
        "title": "Folha, CLT e previdenciario",
        "terms": ["CLT", "previdencia", "eSocial", "DCTFWeb", "FGTS"],
        "expected_files": ["Lei_8212_1991_Custeio_Previdencia.txt", "Lei_8213_1991_Beneficios_Previdencia.txt"],
        "minimum": "contrato, jornada, salario, encargos, seguridade, eSocial, DCTFWeb, Reinf, FGTS e prova",
    },
]


BENEFIT_TYPES = [
    "isencao",
    "reducao_base",
    "credito_presumido_outorgado",
    "diferimento",
    "suspensao",
    "nao_incidencia_imunidade",
    "monofasico",
    "aliquota_zero",
    "regime_especial",
    "fundo_contrapartida",
    "st_antecipacao",
    "exportacao_creditos",
    "importacao_regime",
]


CONFaz_FAMILIES = {
    "convenios": {
        "title": "Convenios ICMS",
        "base_url": "https://www.confaz.fazenda.gov.br/legislacao/convenios",
        "pattern": r"/legislacao/convenios/(?P<year>20\d{2})/CV\d+_\d+",
    },
    "ajustes": {
        "title": "Ajustes SINIEF",
        "base_url": "https://www.confaz.fazenda.gov.br/legislacao/ajustes",
        "pattern": r"/legislacao/ajustes/(?P<year>20\d{2})/AJ\d+_\d+",
    },
    "protocolos": {
        "title": "Protocolos ICMS",
        "base_url": "https://www.confaz.fazenda.gov.br/legislacao/protocolos",
        "pattern": r"/legislacao/protocolos/(?:20\d{2})/(?:PT|pt)\d+_\d+|/legislacao/protocolos/(?:20\d{2})/protocolo-icms-\d+-\d+(?:-[a-z0-9-]+)?",
    },
}


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[dict[str, str]] = []
        self._href = ""
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        attrs_map = {name.lower(): value or "" for name, value in attrs}
        self._href = attrs_map.get("href", "")
        self._text = []

    def handle_data(self, data: str) -> None:
        if self._href:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._href:
            self.links.append({"href": self._href, "text": " ".join(" ".join(self._text).split())})
            self._href = ""
            self._text = []


class TextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style"}:
            self._skip += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style"} and self._skip:
            self._skip -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip:
            text = " ".join(data.split())
            if text:
                self.parts.append(text)


def normalize(value: str) -> str:
    text = unicodedata.normalize("NFKD", value or "")
    text = text.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", text)).strip()


def read_json(path: Path, fallback: object) -> object:
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def file_digest(path: Path) -> str:
    if not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def federal_files() -> dict[str, dict[str, object]]:
    files: dict[str, dict[str, object]] = {}
    if BD_FEDERAL.exists():
        for path in sorted(BD_FEDERAL.glob("*.txt")):
            files[path.name] = {
                "name": path.name,
                "size": path.stat().st_size,
                "sha256": file_digest(path),
            }
    for path in sorted((ROOT / "data" / "legal_sources" / "reforma_tributaria").glob("*.txt")):
        key = path.relative_to(ROOT).as_posix()
        files[key] = {
            "name": key,
            "size": path.stat().st_size,
            "sha256": file_digest(path),
        }
    return files


def registry_sources() -> list[dict]:
    registry = read_json(ROOT / "data" / "legal_sources_registry.json", {})
    if isinstance(registry, dict):
        return list(registry.get("sources", []))
    return []


def build_taxonomy() -> dict:
    return {
        "schema": "rjc-master-taxonomy-v2",
        "generated_on": TODAY,
        "editorial_rule": "Lei em tela antes da analise; conclusao apenas com fonte oficial e prova documental.",
        "benefit_types": BENEFIT_TYPES,
        "benefit_groups": [
            {
                "id": sector["id"],
                "title": sector["title"],
                "summary": sector["summary"],
                "keywords": sector["keywords"],
            }
            for sector in BENEFIT_SECTOR_DEFS
        ],
        "federal_requirements": FEDERAL_REQUIREMENTS,
        "confaz_families": {
            key: {"title": item["title"], "base_url": item["base_url"]}
            for key, item in CONFaz_FAMILIES.items()
        },
        "validation_triple": [
            "texto legal direto em tela",
            "fonte oficial e vigencia identificadas",
            "leitura contraditoria: escopo, revogacao, condicao, documento e risco",
        ],
    }


def build_coverage() -> dict:
    sources = registry_sources()
    federal_available = federal_files()
    source_text = normalize(" ".join((item.get("title", "") + " " + item.get("short", "") + " " + item.get("note", "")) for item in sources))
    pages = {
        path.relative_to(ROOT).as_posix()
        for path in ROOT.rglob("*.html")
        if ".git" not in path.parts and not re.search(r" \(\d+\)$", path.stem)
    }
    federal = []
    for req in FEDERAL_REQUIREMENTS:
        expected = []
        for file_name in req["expected_files"]:
            expected.append({
                "file": file_name,
                "available": file_name in federal_available,
                "size": federal_available.get(file_name, {}).get("size", 0),
                "sha256": federal_available.get(file_name, {}).get("sha256", ""),
            })
        term_hit = any(normalize(term) in source_text for term in req["terms"])
        page_hit = any(req["id"].replace("_", "-") in page or req["id"].split("_", 1)[0] in page for page in pages)
        available_count = sum(1 for item in expected if item["available"])
        if term_hit and page_hit:
            status = "publicado_v1"
        elif available_count:
            status = "fonte_local_disponivel"
        else:
            status = "a_estruturar"
        federal.append({
            **req,
            "status": status,
            "expected_files": expected,
            "registry_match": term_hit,
            "page_match": page_hit,
        })

    curation = read_json(ROOT / "data" / "state_curadoria.json", {})
    statuses = curation.get("statuses", {}) if isinstance(curation, dict) else {}
    audit = read_json(ROOT / "data" / "state_source_audit.json", {})
    audit_states = audit.get("states", {}) if isinstance(audit, dict) else {}
    states = []
    for uf, name in sorted(STATE_NAMES.items()):
        status = statuses.get(uf, {})
        item = audit_states.get(uf, {})
        states.append({
            "uf": uf,
            "name": name,
            "region": status.get("region", item.get("region", "")),
            "status": status.get("status", item.get("curadoria", "sem_status")),
            "publish_deep": bool(status.get("publish_deep")),
            "document_count": item.get("document_count", 0),
            "publishable_document_count": item.get("publishable_document_count", 0),
            "flags": item.get("flags", []),
            "next_step": status.get("next_step", item.get("next_step", "")),
        })

    return {
        "schema": "rjc-master-source-coverage-v2",
        "generated_on": TODAY,
        "summary": {
            "federal_requirements": len(federal),
            "federal_published": sum(1 for item in federal if item["status"] == "publicado_v1"),
            "federal_source_available": sum(1 for item in federal if item["status"] == "fonte_local_disponivel"),
            "states": len(states),
            "states_deep": sum(1 for item in states if item["publish_deep"]),
            "states_waiting_review": sum(1 for item in states if item["status"] == "aguardando_revisao"),
            "states_reviewed_with_pendencies": sum(1 for item in states if str(item["status"]).startswith("revisado")),
            "registered_sources": len(sources),
        },
        "federal": federal,
        "states": states,
    }


def build_benefits_crosswalk() -> dict:
    return build_validated_benefits()


def fetch_links(url: str) -> list[dict[str, str]]:
    request = urllib.request.Request(url, headers={"User-Agent": "RJC-Conhecimento/2.0"})
    with urllib.request.urlopen(request, timeout=45) as response:
        raw = response.read().decode("utf-8", errors="ignore")
    parser = LinkParser()
    parser.feed(raw)
    return parser.links


def fetch_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "RJC-Conhecimento/2.0"})
    with urllib.request.urlopen(request, timeout=45) as response:
        raw = response.read().decode("utf-8", errors="ignore")
    parser = TextParser()
    parser.feed(raw)
    return "\n".join(parser.parts)


def absolute_url(base: str, href: str) -> str:
    if href.startswith("http://") or href.startswith("https://"):
        return href
    if href.startswith("/"):
        return "https://www.confaz.fazenda.gov.br" + href
    return base.rstrip("/") + "/" + href.lstrip("/")


def classify_confaz_theme(text: str) -> list[str]:
    low = normalize(text)
    themes = []
    mapping = [
        ("substituicao_tributaria", ["substituicao", "st", "mva"]),
        ("beneficio_fiscal", ["beneficio", "isencao", "reducao", "credito presumido", "lc 160"]),
        ("documento_fiscal", ["nota fiscal", "nf e", "ct e", "mdf e", "nfc e", "sinief", "efd"]),
        ("reforma_tributaria", ["ibs", "cbs", "imposto seletivo", "reforma tributaria"]),
        ("combustiveis", ["combustivel", "diesel", "gasolina", "etanol", "glp"]),
        ("importacao_exportacao", ["importacao", "exportacao", "exterior"]),
    ]
    for theme, needles in mapping:
        if any(needle in low for needle in needles):
            themes.append(theme)
    return themes or ["a_classificar"]


def fallback_confaz_acts(family_id: str, year_url: str, year: int) -> list[dict[str, object]]:
    if family_id != "ajustes":
        return []
    text = fetch_text(year_url)
    suffix = str(year)[-2:]
    found: set[str] = set()
    acts: list[dict[str, object]] = []
    for match in re.finditer(r"AJUSTE\s+SINIEF\s+0*(\d{1,3})\s*/\s*(\d{2})", text, flags=re.I):
        number, act_suffix = match.groups()
        if act_suffix != suffix:
            continue
        padded = f"{int(number):03d}"
        title = f"AJUSTE SINIEF {int(number):02d}/{suffix}"
        url = f"{year_url.rstrip('/')}/AJ{padded}_{suffix}"
        if url in found:
            continue
        found.add(url)
        acts.append({
            "title": title,
            "url": url,
            "themes": classify_confaz_theme(title),
        })
    if acts:
        return acts
    misses = 0
    for number in range(1, 100):
        padded = f"{number:03d}"
        url = f"{year_url.rstrip('/')}/AJ{padded}_{suffix}"
        try:
            fetch_text(url)
        except Exception:
            misses += 1
            if acts and misses >= 8:
                break
            continue
        misses = 0
        acts.append({
            "title": f"AJUSTE SINIEF {number:02d}/{suffix}",
            "url": url,
            "themes": classify_confaz_theme(f"AJUSTE SINIEF {number:02d}/{suffix}"),
        })
    return acts


def build_confaz_index() -> dict:
    current = date.today().year
    years = list(range(current - 4, current + 1))
    payload = {
        "schema": "rjc-confaz-5y-index-v2",
        "generated_on": TODAY,
        "years": years,
        "source_policy": "Indice oficial do CONFAZ; cada ato relevante ainda precisa ser lido em tela antes de virar conclusao.",
        "families": {},
    }
    for family_id, family in CONFaz_FAMILIES.items():
        family_rows = []
        for year in years:
            year_url = f"{family['base_url']}/{year}"
            links: list[dict[str, str]] = []
            fetch_error = ""
            try:
                candidates = fetch_links(year_url)
                matcher = re.compile(family["pattern"], flags=re.I)
                seen = set()
                for link in candidates:
                    url = absolute_url(family["base_url"], link.get("href", ""))
                    match = matcher.search(url)
                    if not match or url in seen:
                        continue
                    seen.add(url)
                    label = link.get("text") or url.rsplit("/", 1)[-1]
                    links.append({
                        "title": label,
                        "url": url,
                        "themes": classify_confaz_theme(label + " " + url),
                    })
                if not links:
                    links = fallback_confaz_acts(family_id, year_url, year)
            except Exception as exc:  # network source should not break local publishing
                fetch_error = str(exc)
            family_rows.append({
                "year": year,
                "index_url": year_url,
                "count": len(links),
                "fetch_error": fetch_error,
                "acts": links,
            })
        payload["families"][family_id] = {
            "title": family["title"],
            "base_url": family["base_url"],
            "years": family_rows,
            "total": sum(item["count"] for item in family_rows),
        }
    return payload


def write_markdown(coverage: dict, benefits: dict, confaz: dict) -> None:
    lines = [
        "# Auditoria Mestre v2",
        "",
        f"Gerado em {TODAY}.",
        "",
        "Este arquivo resume cobertura e cruzamentos do Portal RJC Tributario Aberto. Ele e uma trilha de auditoria, nao um parecer tributario.",
        "",
        "## Cobertura",
        "",
        f"- Fontes registradas: {coverage['summary']['registered_sources']}",
        f"- Requisitos federais mapeados: {coverage['summary']['federal_requirements']}",
        f"- Requisitos federais publicados: {coverage['summary']['federal_published']}",
        f"- Requisitos federais com fonte local disponivel: {coverage['summary']['federal_source_available']}",
        f"- Estados profundos: {coverage['summary']['states_deep']}",
        f"- Estados aguardando revisao: {coverage['summary']['states_waiting_review']}",
        f"- Estados revisados sem aprovacao profunda: {coverage['summary']['states_reviewed_with_pendencies']}",
        f"- Entradas validadas na matriz de beneficios: {benefits['summary']['entries']}",
        f"- Entradas em quarentena editorial: {benefits['summary'].get('quarantined_entries', 0)}",
        f"- Entradas com NCM/TIPI: {benefits['summary'].get('with_ncm', 0)}",
        f"- Entradas com CEST: {benefits['summary'].get('with_cest', 0)}",
        f"- Entradas com cBenef: {benefits['summary'].get('with_cbenef', 0)}",
        "",
        "## Lacunas Federais",
        "",
        "| Tema | Status | Minimo editorial | Fontes locais |",
        "| --- | --- | --- | --- |",
    ]
    for item in coverage["federal"]:
        files = ", ".join(file["file"] for file in item["expected_files"] if file["available"]) or "sem fonte local mapeada"
        lines.append(f"| {item['title']} | {item['status']} | {item['minimum']} | {files} |")
    lines.extend([
        "",
        "## Estados",
        "",
        "| UF | Status | Docs | Alertas principais | Proximo passo |",
        "| --- | --- | ---: | --- | --- |",
    ])
    for item in coverage["states"]:
        flags = ", ".join(item["flags"][:4]) if item["flags"] else "sem alerta automatizado"
        lines.append(f"| {item['uf']} | {item['status']} | {item['document_count']} | {flags} | {item['next_step']} |")
    lines.extend([
        "",
        "## CONFAZ 5 anos",
        "",
        "| Familia | Total indexado | Fonte oficial |",
        "| --- | ---: | --- |",
    ])
    for item in confaz["families"].values():
        lines.append(f"| {item['title']} | {item['total']} | {item['base_url']} |")
    OUT_DOC.parent.mkdir(parents=True, exist_ok=True)
    OUT_DOC.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    taxonomy = build_taxonomy()
    coverage = build_coverage()
    benefits = build_benefits_crosswalk()
    confaz = build_confaz_index()
    benefits_quarantine = {
        "schema": "rjc-benefits-quarantine-v1",
        "generated_on": benefits.get("generated_on", TODAY),
        "source": "data/benefits_crosswalk.json",
        "summary": {
            "entries": len(benefits.get("quarantine", [])),
            "rule": "itens extraidos de fonte oficial, mas nao publicados por escopo ambíguo, baixa confiança ou ruido editorial",
        },
        "entries": benefits.get("quarantine", []),
    }
    public_benefits = {key: value for key, value in benefits.items() if key != "quarantine"}
    write_json(OUT_TAXONOMY, taxonomy)
    write_json(OUT_COVERAGE, coverage)
    write_json(OUT_BENEFITS, public_benefits)
    write_json(OUT_BENEFITS_QUARANTINE, benefits_quarantine)
    write_json(OUT_CONFAZ, confaz)
    write_markdown(coverage, benefits, confaz)
    print(f"Taxonomia mestre: {OUT_TAXONOMY.relative_to(ROOT)}")
    print(f"Cobertura mestre: {OUT_COVERAGE.relative_to(ROOT)}")
    print(f"Matriz de beneficios: {OUT_BENEFITS.relative_to(ROOT)}")
    print(f"Quarentena de beneficios: {OUT_BENEFITS_QUARANTINE.relative_to(ROOT)}")
    print(f"CONFAZ 5 anos: {OUT_CONFAZ.relative_to(ROOT)}")
    print(f"Relatorio: {OUT_DOC.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
