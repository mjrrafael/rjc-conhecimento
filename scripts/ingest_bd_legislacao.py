#!/usr/bin/env python3
"""Create a compact legal inventory from the local BD_LEGISLACAO corpus.

The portal should teach the law, not dump raw files. This inventory keeps the
full corpus represented: file, category, source trail, legal signals and an
editorial reading path for each state and federal theme.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BD = Path(r"C:\Users\kris2\OneDrive\COWORK\BD_LEGISLACAO")
OUT = ROOT / "data" / "legal_inventory.json"

STATE_NAMES = {
    "AC": "Acre",
    "AL": "Alagoas",
    "AP": "Amapa",
    "AM": "Amazonas",
    "BA": "Bahia",
    "CE": "Ceara",
    "DF": "Distrito Federal",
    "ES": "Espirito Santo",
    "GO": "Goias",
    "MA": "Maranhao",
    "MT": "Mato Grosso",
    "MS": "Mato Grosso do Sul",
    "MG": "Minas Gerais",
    "PA": "Para",
    "PB": "Paraiba",
    "PR": "Parana",
    "PE": "Pernambuco",
    "PI": "Piaui",
    "RJ": "Rio de Janeiro",
    "RN": "Rio Grande do Norte",
    "RS": "Rio Grande do Sul",
    "RO": "Rondonia",
    "RR": "Roraima",
    "SC": "Santa Catarina",
    "SP": "Sao Paulo",
    "SE": "Sergipe",
    "TO": "Tocantins",
}

SIGNALS = {
    "isencao": ["isencao", "isento", "isenta"],
    "reducao de base": ["reducao de base", "base de calculo reduzida"],
    "credito outorgado": ["credito outorgado", "credito presumido"],
    "diferimento": ["diferimento", "diferido"],
    "substituicao tributaria": ["substituicao tributaria", "icms st", "substituto tributario"],
    "aliquota": ["aliquota"],
    "nao incidencia": ["nao incidencia", "nao-incidencia"],
    "suspensao": ["suspensao"],
    "regime especial": ["regime especial", "tare", "termo de acordo"],
    "protege/fundo": ["protege", "fundo"],
    "exportacao": ["exportacao", "exterior"],
    "monofasico": ["monofasico"],
    "cBenef": ["cbenef", "codigo de beneficio"],
    "efd/sped": ["efd", "sped", "escrituracao fiscal"],
}

FEDERAL_THEMES = {
    "pis_cofins": ["PIS", "COFINS", "PASEP", "CONTRIBUICOES"],
    "ipi": ["IPI", "TIPI", "RIPI"],
    "iof": ["IOF"],
    "irpj_csll": ["IRPJ", "CSLL", "RENDA", "LUCRO"],
    "regimes": ["SIMPLES", "PRESUMIDO", "REAL", "MEI"],
    "previdencia_folha": ["CLT", "PREVIDENCIA", "CUSTEIO", "BENEFICIOS_PREVIDENCIA", "CPRB"],
    "reforma": ["IBS", "CBS", "IS_", "REFORMA", "CGIBS"],
    "beneficios": ["DIRBI", "BENEFICIOS", "INCENTIVOS", "ZFM", "SUFRAMA", "REINTEGRA", "PERSE"],
    "aduaneiro": ["ADUANEIRO", "IMPORTACAO", "EXPORTACAO", "SISCOMEX"],
}

CATEGORY_LABELS = {
    "RICMS": "Regulamento do ICMS",
    "ICMS_LEIS": "Leis de ICMS",
    "ICMS_DECRETOS": "Decretos de ICMS",
    "ICMS_BENEFICIOS": "Beneficios fiscais de ICMS",
    "ICMS_ST": "Substituicao tributaria",
    "ICMS_ALIQUOTAS": "Aliquotas de ICMS",
    "ICMS_ANEXOS": "Anexos e tabelas",
    "DECRETOS": "Decretos",
    "LEIS": "Leis",
    "INSTRUCOES_NORMATIVAS": "Instrucoes normativas",
    "PORTARIAS": "Portarias",
    "RESOLUCOES": "Resolucoes",
    "IPVA": "IPVA",
    "ITCD": "ITCD",
    "TAXAS": "Taxas",
    "OUTROS": "Outros atos",
}

OFFICIAL_SOURCE_OVERRIDES = {
    "IN_RFB_2121_2022": "https://normas.receita.fazenda.gov.br/sijut2consulta/consulta.action?tipoData=2&siglaOrgaoFacet=RFB&termoBusca=2121&tiposAtosSelecionados=42",
    "IN_RFB_2305_2025": "https://normas.receita.fazenda.gov.br/sijut2consulta/consulta.action?tipoData=2&siglaOrgaoFacet=RFB&termoBusca=2305&tiposAtosSelecionados=42",
    "IN_RFB_2306_2026": "https://normas.receita.fazenda.gov.br/sijut2consulta/consulta.action?tipoData=2&siglaOrgaoFacet=RFB&termoBusca=2306&tiposAtosSelecionados=42",
}

LEGAL_CHAPTERS = [
    {
        "id": "regra-maior",
        "title": "Regra maior",
        "needles": ["fato gerador", "incide", "incidencia", "contribuinte", "responsavel", "base de calculo", "aliquota"],
    },
    {
        "id": "beneficios-isencoes",
        "title": "Beneficios, isencoes e reducoes",
        "needles": ["beneficio", "isencao", "isento", "reducao de base", "credito outorgado", "credito presumido", "aliquota zero"],
    },
    {
        "id": "excecoes-condicoes",
        "title": "Excecoes, condicoes e vedacoes",
        "needles": ["exceto", "vedado", "nao se aplica", "condicao", "desde que", "fica condicionado", "perde o direito"],
    },
    {
        "id": "documento-prova",
        "title": "Documento fiscal, declaracao e prova",
        "needles": ["documento fiscal", "nota fiscal", "escrituracao", "efd", "sped", "declaracao", "informacoes complementares", "xml"],
    },
    {
        "id": "apuracao-recolhimento",
        "title": "Apuracao, recolhimento e controle",
        "needles": ["apuracao", "recolhimento", "compensacao", "credito", "debito", "periodo de apuracao", "ajuste"],
    },
]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1", errors="ignore")


def normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    ascii_text = decomposed.encode("ascii", "ignore").decode("ascii")
    return ascii_text.lower()


def count_signals(text: str) -> dict[str, int]:
    low = normalize(text)
    counts = {}
    for label, needles in SIGNALS.items():
        total = 0
        for needle in needles:
            total += low.count(normalize(needle))
        if total:
            counts[label] = total
    return counts


def clean_excerpt(value: str, limit: int = 900) -> str:
    value = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    value = re.sub(r"^(Art\.?\s*\d+[^\w]*)", r"\1", value, flags=re.I)
    if len(value) <= limit:
        return value
    cut = value[:limit].rsplit(" ", 1)[0]
    return cut.rstrip(".,;") + "..."


def looks_like_law(value: str) -> bool:
    normalized = normalize(value)
    bad_needles = [
        "clique aqui",
        "requerimento padrao",
        "nome ou razao social",
        "codigo do evento",
        "pagina ",
        "apresentacao ",
        "sumario",
        "indice",
        "item cest",
        "ncm/sh descricao",
        "informativo de equipamento",
        "informativo das obrigacoes",
        "documentos a serem apresentados",
        "superintendencia da receita",
        "av. ",
        "avenida ",
        "cep:",
        "conferida nova redacao",
    ]
    if any(needle in normalized[:250] for needle in bad_needles):
        return False
    if re.search(r"\.{6,}", value):
        return False
    letters = [char for char in value if char.isalpha()]
    if len(letters) > 120:
        upper_ratio = sum(1 for char in letters if char.isupper()) / len(letters)
        if upper_ratio > 0.75:
            return False
    law_markers = ["art.", "artigo", "§", "paragrafo", "inciso", "fica", "sao", "sera", "aplica", "contribuinte", "isencao", "aliquota"]
    return any(marker in normalized for marker in law_markers)


def passage_score(value: str, chapter: dict) -> int:
    normalized = normalize(value)
    score = 0
    if re.search(r"\bArt\.?\s*\d+", value, flags=re.I):
        score += 8
    if "§" in value or "paragrafo" in normalized:
        score += 4
    if "inciso" in normalized:
        score += 2
    if "fica" in normalized:
        score += 2
    if chapter["id"] == "beneficios-isencoes" and any(term in normalized for term in ["isencao", "beneficio", "credito presumido", "credito outorgado"]):
        score += 4
    if chapter["id"] == "excecoes-condicoes" and any(term in normalized for term in ["desde que", "vedado", "nao se aplica"]):
        score += 4
    if normalized.startswith("anexo"):
        score -= 3
    return score


def paragraphs(text: str) -> list[str]:
    raw = re.split(r"\n\s*\n|\r\n\s*\r\n", text)
    chunks = []
    for chunk in raw:
        clean = re.sub(r"\s+", " ", chunk).strip()
        if len(clean) < 120:
            continue
        lowered = normalize(clean)
        if lowered.startswith(("documentos fonte", "observacao", "fonte:", "data de extracao")):
            continue
        if not looks_like_law(clean):
            continue
        chunks.append(clean)
    return chunks


def extract_legal_passages(text: str, source_label: str, limit: int = 5) -> list[dict[str, str]]:
    chunks = paragraphs(text)
    passages: list[dict[str, str]] = []
    used: set[int] = set()
    for chapter in LEGAL_CHAPTERS:
        candidates = []
        for idx, chunk in enumerate(chunks):
            normalized = normalize(chunk)
            if any(needle in normalized for needle in chapter["needles"]):
                candidates.append((passage_score(chunk, chapter), idx, chunk))
        for _score, idx, chunk in sorted(candidates, key=lambda item: item[0], reverse=True):
            if idx in used:
                continue
            passages.append({
                "chapter_id": chapter["id"],
                "chapter_title": chapter["title"],
                "source": source_label,
                "text": clean_excerpt(chunk),
            })
            used.add(idx)
            break
        if len(passages) >= limit:
            break
    return passages


def category_from_state_file(uf: str, path: Path) -> str:
    name = path.stem
    if name.startswith(f"{uf}_"):
        name = name[len(uf) + 1 :]
    name = re.sub(r"_parte\d+$|_pt\d+$", "", name, flags=re.I)
    return name.upper()


def parse_state_sources(text: str) -> list[str]:
    sources = []
    in_sources = False
    for line in text.splitlines()[:80]:
        stripped = line.strip()
        normalized = normalize(stripped)
        if normalized.startswith("documentos fonte"):
            in_sources = True
            continue
        if in_sources and (stripped.startswith("•") or stripped.startswith("-") or stripped.startswith("*")):
            sources.append(stripped.lstrip("•-* ").strip())
        elif in_sources and normalized.startswith("observacao"):
            break
    return sources[:20]


def parse_federal_header(text: str, path: Path) -> dict[str, str]:
    header = {"title": path.stem.replace("_", " "), "source": "", "extracted_on": ""}
    for line in text.splitlines()[:35]:
        normalized = normalize(line)
        if normalized.startswith("titulo:"):
            header["title"] = line.split(":", 1)[1].strip()
        elif normalized.startswith("fonte:"):
            header["source"] = line.split(":", 1)[1].strip()
        elif normalized.startswith("data de extracao:"):
            header["extracted_on"] = line.split(":", 1)[1].strip()
    return header


def theme_for_federal(name: str) -> str:
    normalized = name.upper().replace("-", "_").replace(" ", "_")
    for theme, needles in FEDERAL_THEMES.items():
        if any(needle in normalized for needle in needles):
            return theme
    return "geral"


def official_source_for(path: Path, source: str) -> str:
    for prefix, official in OFFICIAL_SOURCE_OVERRIDES.items():
        if path.stem.startswith(prefix):
            return official
    return source


def state_commentary(uf: str, docs: list[dict], signals: dict[str, int]) -> dict[str, str]:
    name = STATE_NAMES.get(uf, uf)
    categories = {doc["category"] for doc in docs}
    if not docs:
        return {
            "diagnostico": f"O acervo compilado para {name} ainda nao trouxe base estadual util nesta rodada. A pagina fica preservada para receber o RICMS e atos oficiais quando a base local for completada.",
            "primeiro_estudo": "Antes de publicar tese estadual, o caminho correto e localizar o regulamento do ICMS, lei do imposto, anexos de beneficios, atos de ST e tabela de aliquotas em fonte oficial.",
            "auditoria": "Sem acervo material, qualquer conclusao estadual deve ficar suspensa. O auditor so deve avancar com fonte oficial aberta e data de conferencia."
        }
    has_benefits = any("BENEF" in c or signals.get("isencao") or signals.get("credito outorgado") for c in categories)
    has_st = any("ST" in c for c in categories) or bool(signals.get("substituicao tributaria"))
    has_ricms = any("RICMS" in c for c in categories)
    diagnostico = (
        f"O acervo de {name} permite uma leitura de ICMS em camadas. "
        f"Ha {len(docs)} consolidados estaduais, com destaque para "
        f"{', '.join(sorted(CATEGORY_LABELS.get(c, c.title()) for c in list(categories)[:6]))}. "
        "A pagina nao trata esse material como simples arquivo: ela organiza a lei para decisao fiscal, emissao documental e prova."
    )
    primeiro = (
        "Comece pelo regulamento do ICMS e pela lei material do imposto; depois avance para anexos, beneficios, ST, aliquotas e atos infralegais. "
        "Essa ordem evita o erro classico de aplicar um beneficio sem antes confirmar incidencia, sujeito passivo, produto, operacao e vigencia."
    )
    if has_benefits:
        primeiro += " Nos beneficios, a pergunta decisiva e sempre a mesma: a empresa cumpre todas as condicoes ou apenas encontrou um texto favoravel?"
    if has_st:
        primeiro += " Em ST, separe responsabilidade, MVA/pauta, protocolo/convenio e documento fiscal antes de calcular."
    auditoria = (
        "Na revisao, trabalhe como fiscal: peca XML, EFD, memoria de calculo, cadastro de produto, NCM, contrato e dispositivo legal. "
        "Se uma dessas pecas nao conversa com a outra, o risco nao esta na lei; esta na prova."
    )
    if has_ricms:
        auditoria += " O RICMS deve ser a espinha dorsal da analise, mas anexos e atos recentes costumam alterar a operacao concreta."
    return {"diagnostico": diagnostico, "primeiro_estudo": primeiro, "auditoria": auditoria}


def build_legal_chapters_from_docs(docs: list[dict], limit_per_chapter: int = 3) -> list[dict]:
    chapters = []
    for chapter in LEGAL_CHAPTERS:
        passages = []
        for doc in docs:
            for passage in doc.get("passages", []):
                if passage.get("chapter_id") == chapter["id"]:
                    passages.append(passage)
                    break
            if len(passages) >= limit_per_chapter:
                break
        if passages:
            chapters.append({
                "id": chapter["id"],
                "title": chapter["title"],
                "passages": passages,
            })
    return chapters


def ingest_states(bd: Path) -> list[dict]:
    base = bd / "#ESTADUAIS-COMPILADO-NOTEBOOKLM"
    states = []
    for uf, name in STATE_NAMES.items():
        folder = base / uf
        docs = []
        total_signals: Counter[str] = Counter()
        total_chars = 0
        if folder.exists():
            for path in sorted(folder.glob("*.txt")):
                if path.name.startswith("00_"):
                    continue
                text = read_text(path)
                signals = count_signals(text)
                total_signals.update(signals)
                category = category_from_state_file(uf, path)
                total_chars += len(text)
                docs.append({
                    "file": path.name,
                    "category": category,
                    "category_label": CATEGORY_LABELS.get(category, category.replace("_", " ").title()),
                    "chars": len(text),
                    "source_documents": parse_state_sources(text),
                    "signals": signals,
                    "passages": extract_legal_passages(text, path.name, limit=4),
                })
        signal_dict = dict(total_signals.most_common())
        states.append({
            "uf": uf,
            "name": name,
            "file_count": len(docs),
            "total_chars": total_chars,
            "categories": sorted({doc["category"] for doc in docs}),
            "signals": signal_dict,
            "commentary": state_commentary(uf, docs, signal_dict),
            "legal_chapters": build_legal_chapters_from_docs(docs),
            "documents": docs,
            "compiled_on": "11/04/2026",
        })
    return states


def ingest_federal(bd: Path) -> dict:
    folders = [
        bd / "#FEDERAIS-COMPILADO-ONLINE" / "legislacao_txt_completa",
        bd / "#FEDERAIS-COMPILADO-ONLINE" / "notebooklm_txt",
    ]
    by_name: dict[str, Path] = {}
    for folder in folders:
        if not folder.exists():
            continue
        for path in folder.glob("*.txt"):
            by_name.setdefault(path.name, path)
    documents = []
    themes: dict[str, dict] = {}
    for path in sorted(by_name.values(), key=lambda p: p.name):
        text = read_text(path)
        header = parse_federal_header(text, path)
        theme = theme_for_federal(path.stem)
        signals = count_signals(text)
        doc = {
            "file": path.name,
            "theme": theme,
            "title": header["title"],
            "source": official_source_for(path, header["source"]),
            "extracted_on": header["extracted_on"] or "11/04/2026",
            "chars": len(text),
            "signals": signals,
            "passages": extract_legal_passages(text, header["title"] or path.name, limit=4),
        }
        documents.append(doc)
        bucket = themes.setdefault(theme, {"theme": theme, "file_count": 0, "total_chars": 0, "signals": Counter(), "documents": []})
        bucket["file_count"] += 1
        bucket["total_chars"] += len(text)
        bucket["signals"].update(signals)
        bucket["documents"].append(doc)
    for bucket in themes.values():
        bucket["signals"] = dict(bucket["signals"].most_common())
        bucket["legal_chapters"] = build_legal_chapters_from_docs(bucket["documents"])
    return {"documents": documents, "themes": themes}


def main() -> None:
    bd = DEFAULT_BD
    if not bd.exists():
        raise SystemExit(f"BD_LEGISLACAO not found at {bd}")
    data = {
        "generated_on": date.today().isoformat(),
        "bd_root": str(bd),
        "states": ingest_states(bd),
        "federal": ingest_federal(bd),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    print(f"Wrote {OUT.relative_to(ROOT)}")
    print(f"States: {len(data['states'])}; federal docs: {len(data['federal']['documents'])}")


if __name__ == "__main__":
    main()
