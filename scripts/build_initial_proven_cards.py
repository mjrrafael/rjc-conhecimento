#!/usr/bin/env python3
"""Build the first human/AI-readable legal cards from independently recaptured acts.

The card data is intentionally small and exact. It demonstrates the publishing
contract before any legacy bulk corpus is reintroduced.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "auditoria" / "execucoes" / "reconstrucao-provas-2026-07-16"
OUT = ROOT / "data" / "prova_material" / "cards_em_reconstrucao.json"


def load_receipts(path: Path) -> dict[str, dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"Recibos inválidos: {path}")
    return {str(item["source_id"]): item for item in payload}


def evidence(source_id: str, first: dict[str, dict[str, Any]], second: dict[str, dict[str, Any]]) -> dict[str, Any]:
    one, two = first[source_id], second[source_id]
    if one.get("result") != "CAPTURADA_PENDENTE_DE_REFETCH" or two.get("result") != "CAPTURADA_PENDENTE_DE_REFETCH":
        raise ValueError(f"Fonte {source_id} não foi capturada duas vezes.")
    one_body, two_body = one.get("body", {}), two.get("body", {})
    if one_body.get("sha256") != two_body.get("sha256"):
        raise ValueError(f"Divergência de corpo entre capturas: {source_id}")
    one_response, two_response = one.get("response", {}), two.get("response", {})
    if one_response.get("status") != 200 or two_response.get("status") != 200:
        raise ValueError(f"Resposta não 200: {source_id}")
    return {
        "source_id": source_id,
        "url_final": one_response["url_final"],
        "dominio_oficial": urlparse(one_response["url_final"]).hostname,
        "http_status": 200,
        "mime": one_response.get("mime", ""),
        "sha256_corpo_bruto": one_body["sha256"],
        "capturas_locais_independentes": [one["receipt_id"], two["receipt_id"]],
        "web_tool_references": [],
        "nota": "Capturas locais coincidentes; ainda depende de recibo nativo de plataforma e revisão cega para autorizar publicação.",
    }


def provenance(ev: dict[str, Any], field: str, value: Any, literal: str, locator: str, rule: str, tool_refs: list[str]) -> dict[str, Any]:
    return {
        "card_id": "",
        "campo": field,
        "valor": value,
        "url_final": ev["url_final"],
        "dominio_oficial": ev["dominio_oficial"],
        "http_status": ev["http_status"],
        "mime": ev["mime"],
        "sha256_corpo_bruto": ev["sha256_corpo_bruto"],
        "trecho_literal": literal,
        "localizador": locator,
        "regra_normalizacao": rule,
        "recibos": ev["capturas_locais_independentes"],
        "web_tool_references": tool_refs,
    }


def with_additional(primary: dict[str, Any], *additional: dict[str, Any]) -> dict[str, Any]:
    primary["fundamentos_adicionais"] = list(additional)
    return primary


def finalize(card: dict[str, Any]) -> dict[str, Any]:
    for source in card["field_provenance"].values():
        source["card_id"] = card["id"]
        for additional in source.get("fundamentos_adicionais", []):
            additional["card_id"] = card["id"]
    canonical = json.dumps(card, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    card["sha256_registro"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return card


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--first", type=Path, default=RUN / "act_capture_receipts_tentativa_3.json")
    parser.add_argument("--second", type=Path, default=RUN / "act_capture_receipts_tentativa_4.json")
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    first, second = load_receipts(args.first), load_receipts(args.second)
    ctn = evidence("BR-CTN-TEXTO-COMPILED", first, second)
    ctn_registro = evidence("BR-CTN-SENADO-REGISTRO", first, second)
    ctn_camara = evidence("BR-CTN-CAMARA-HISTORICO", first, second)
    lc214 = evidence("BR-LC214-TEXTO-ATUAL", first, second)
    lc214_dou = evidence("BR-LC214-DOU-ORIGINAL", first, second)
    ctn["web_tool_references"] = ["turn56view2", "turn60view2", "turn60view1", "turn61view0"]
    ctn_registro["web_tool_references"] = ["turn87view0"]
    ctn_camara["web_tool_references"] = ["turn61view0"]
    lc214["web_tool_references"] = ["turn56view0", "turn57view0", "turn59view0"]
    lc214_dou["web_tool_references"] = ["turn73search1"]
    ctn.update({"identificacao_humana": "Texto consolidado do CTN — Senado Federal", "papel": "texto normativo consolidado e vigência"})
    ctn_registro.update({"identificacao_humana": "Registro da Lei nº 5.172/1966 — Senado Federal", "papel": "publicação original"})
    ctn_camara.update({"identificacao_humana": "Ficha histórica da Lei nº 5.172/1966 — Câmara dos Deputados", "papel": "origem e histórico legislativo"})
    lc214_dou.update({"identificacao_humana": "Publicação original da LC nº 214/2025 — Diário Oficial da União", "papel": "ato e publicação original"})
    lc214.update({"identificacao_humana": "Texto atual da LC nº 214/2025 — Senado Federal", "papel": "vigência e eficácia do texto vigente"})

    cards = [
        finalize({
            "id": "br-ctn-legislacao-tributaria-art96",
            "tipo": "NORMA_GERAL",
            "jurisdicao": "BR",
            "titulo_humano": "O que conta como legislação tributária",
            "resumo_humano": "O art. 96 do CTN inclui leis, tratados e convenções internacionais, decretos e normas complementares que tratem, total ou parcialmente, de tributos e de relações jurídicas a eles ligadas.",
            "regra_estruturada": {
                "regra": "A expressão abrange leis, tratados e convenções internacionais, decretos e normas complementares sobre tributos e relações jurídicas pertinentes.",
            },
            "orientacao_editorial": "Este card define fontes normativas; não calcula tributo e não substitui a leitura do ato aplicável ao caso.",
            "ato": {"tipo": "Lei", "numero": "5.172", "data": "1966-10-25", "autoridade_emissora": "Presidente da República / Congresso Nacional"},
            "temporal": {
                "publicacao": {"valor": "1966-10-27", "status": "COMPROVADA"},
                "inicio_vigencia": {"valor": "1967-01-01", "status": "COMPROVADA"},
                "inicio_eficacia": {"valor": None, "status": "INDETERMINADO", "justificativa": "O dispositivo de vigência lido não separa uma data autônoma de eficácia para o art. 96."},
                "fim_vigencia": {"valor": None, "status": "INDETERMINADO", "justificativa": "A consulta não encontrou termo final expresso para o art. 96; isso não prova inexistência de alteração ou revogação futura."},
            },
            "fontes": [ctn, ctn_registro, ctn_camara],
            "field_provenance": {
                "titulo_humano": provenance(ctn, "titulo_humano", "O que conta como legislação tributária", "LEGISLAÇÃO TRIBUTÁRIA", "Título I, Livro Segundo", "rótulo editorial fiel ao título legal", ["turn60view2"]),
                "resumo_humano": provenance(ctn, "resumo_humano", "O art. 96 do CTN inclui leis, tratados e convenções internacionais, decretos e normas complementares que tratem, total ou parcialmente, de tributos e de relações jurídicas a eles ligadas.", "Art. 96. A expressão \"legislação tributária\" compreende as leis, os tratados e as convenções internacionais, os decretos e as normas complementares que versem, no todo ou em parte, sobre tributos e relações jurídicas a eles pertinentes.", "Art. 96", "paráfrase conservadora; sem ampliar o alcance", ["turn60view2"]),
                "regra_estruturada.regra": provenance(ctn, "regra_estruturada.regra", "A expressão abrange leis, tratados e convenções internacionais, decretos e normas complementares sobre tributos e relações jurídicas pertinentes.", "Art. 96. A expressão \"legislação tributária\" compreende as leis, os tratados e as convenções internacionais, os decretos e as normas complementares que versem, no todo ou em parte, sobre tributos e relações jurídicas a eles pertinentes.", "Art. 96", "paráfrase conservadora; sem ampliar o alcance", ["turn60view2"]),
                "ato.tipo": provenance(ctn, "ato.tipo", "Lei", "LEI Nº 5.172, DE 25 DE OUTUBRO DE 1966", "cabeçalho do texto", "tipo normalizado", ["turn61view0"]),
                "ato.numero": provenance(ctn, "ato.numero", "5.172", "LEI Nº 5.172, DE 25 DE OUTUBRO DE 1966", "cabeçalho do texto", "número sem pontuação adicional", ["turn61view0"]),
                "ato.data": provenance(ctn, "ato.data", "1966-10-25", "LEI Nº 5.172, DE 25 DE OUTUBRO DE 1966", "cabeçalho do texto", "DD de mês por extenso de AAAA para ISO-8601", ["turn61view0"]),
                "ato.autoridade_emissora": provenance(ctn, "ato.autoridade_emissora", "Presidente da República / Congresso Nacional", "O PRESIDENTE DA REPÚBLICA: Faço saber que o Congresso Nacional decreta e eu sanciono a seguinte Lei:", "preâmbulo da Lei nº 5.172/1966 no texto consolidado", "autoridades literais normalizadas em ordem de promulgação e decreto", ["turn61view0"]),
                "jurisdicao": provenance(ctn_camara, "jurisdicao", "BR", "normas gerais de direito tributário aplicáveis à União, Estados e Municípios", "ementa da Lei nº 5.172/1966 na ficha histórica da Câmara", "alcance federativo normalizado como jurisdição BR", ["turn61view0"]),
                "temporal.publicacao": provenance(ctn_registro, "temporal.publicacao", "1966-10-27", "[Diário Oficial da União de 27/10/1966] (p. 12451, col. 1)", "registro do Senado, Publicação do Texto Principal", "DD/MM/AAAA para ISO-8601", ["turn87view0"]),
                "temporal.inicio_vigencia": provenance(ctn, "temporal.inicio_vigencia", "1967-01-01", "Esta Lei entrará em vigor, em todo o território nacional, no dia 1º de janeiro de 1967", "Art. 218", "data literal para ISO-8601", ["turn60view1"]),
            },
            "estado_publicacao": "NAO_PUBLICAR_SEM_RECIBO_NATIVO_E_REVISAO_CEGA",
        }),
        finalize({
            "id": "br-lc214-ibs-cbs-incidencia-geral",
            "tipo": "NORMA_GERAL",
            "jurisdicao": "BR",
            "titulo_humano": "IBS e CBS: instituição e regra geral de incidência",
            "resumo_humano": "A Lei Complementar nº 214/2025 institui o IBS e a CBS. O art. 4º estabelece que, como regra geral, os dois tributos incidem sobre operações onerosas com bens ou serviços.",
            "regra_estruturada": {
                "tributos": ["IBS", "CBS"],
                "instituicao": "O IBS é de competência compartilhada entre Estados, Municípios e Distrito Federal; a CBS é de competência da União.",
                "incidencia_geral": "IBS e CBS incidem sobre operações onerosas com bens ou serviços.",
                "transicao_rt": "Para os dispositivos deste card, a LC 214 fixa produção de efeitos a partir de 1º de janeiro de 2026, salvo regra específica do art. 544.",
            },
            "orientacao_editorial": "Não use este card para calcular alíquota, crédito, benefício ou obrigação acessória sem o dispositivo específico aplicável.",
            "ato": {"tipo": "Lei Complementar", "numero": "214", "data": "2025-01-16", "autoridade_emissora": "Presidente da República / Congresso Nacional"},
            "temporal": {
                "publicacao": {"valor": "2025-01-16", "status": "COMPROVADA"},
                "inicio_vigencia": {"valor": "2025-01-16", "status": "COMPROVADA"},
                "inicio_eficacia": {"valor": "2026-01-01", "status": "COMPROVADA"},
                "fim_vigencia": {"valor": None, "status": "INDETERMINADO", "justificativa": "A consulta não encontrou termo final expresso para os arts. 1º e 4º; isso não prova inexistência de alteração ou revogação futura."},
            },
            "fontes": [lc214_dou, lc214],
            "field_provenance": {
                "titulo_humano": provenance(lc214_dou, "titulo_humano", "IBS e CBS: instituição e regra geral de incidência", "Institui o Imposto sobre Bens e Serviços (IBS), a Contribuição Social sobre Bens e Serviços (CBS) e o Imposto Seletivo (IS)", "ementa no DOU, edição extra 11-B, p. 1", "rótulo editorial restrito à ementa e aos arts. 1º e 4º", ["turn73search1"]),
                "resumo_humano": provenance(lc214_dou, "resumo_humano", "A Lei Complementar nº 214/2025 institui o IBS e a CBS. O art. 4º estabelece que, como regra geral, os dois tributos incidem sobre operações onerosas com bens ou serviços.", "Art. 1º Ficam instituídos:\nI - o Imposto sobre Bens e Serviços (IBS), de competência compartilhada entre Estados, Municípios e Distrito Federal, de que trata o art. 156-A da Constituição Federal; e\nII - a Contribuição Social sobre Bens e Serviços (CBS), de competência da União, de que trata o inciso V do caput do art. 195 da Constituição Federal.\n\nArt. 4º O IBS e a CBS incidem sobre operações onerosas com bens ou com serviços.", "DOU edição extra 11-B, p. 1, arts. 1º, I e II, e 4º, caput", "paráfrase conservadora; excertos literais identificados por artigo", ["turn73search1"]),
                "regra_estruturada.tributos": provenance(lc214_dou, "regra_estruturada.tributos", ["IBS", "CBS"], "Art. 1º Ficam instituídos:\nI - o Imposto sobre Bens e Serviços (IBS), de competência compartilhada entre Estados, Municípios e Distrito Federal, de que trata o art. 156-A da Constituição Federal; e\nII - a Contribuição Social sobre Bens e Serviços (CBS), de competência da União, de que trata o inciso V do caput do art. 195 da Constituição Federal.", "DOU edição extra 11-B, p. 1, art. 1º, I e II", "siglas e nomes literais convertidos em lista", ["turn73search1"]),
                "regra_estruturada.instituicao": provenance(lc214_dou, "regra_estruturada.instituicao", "O IBS é de competência compartilhada entre Estados, Municípios e Distrito Federal; a CBS é de competência da União.", "Art. 1º Ficam instituídos:\nI - o Imposto sobre Bens e Serviços (IBS), de competência compartilhada entre Estados, Municípios e Distrito Federal, de que trata o art. 156-A da Constituição Federal; e\nII - a Contribuição Social sobre Bens e Serviços (CBS), de competência da União, de que trata o inciso V do caput do art. 195 da Constituição Federal.", "DOU edição extra 11-B, p. 1, art. 1º, I e II", "paráfrase conservadora", ["turn73search1"]),
                "regra_estruturada.incidencia_geral": provenance(lc214_dou, "regra_estruturada.incidencia_geral", "IBS e CBS incidem sobre operações onerosas com bens ou serviços.", "Art. 4º O IBS e a CBS incidem sobre operações onerosas com bens ou com serviços.", "DOU edição extra 11-B, p. 1, art. 4º, caput", "reprodução sem ampliação", ["turn73search1"]),
                "ato.tipo": provenance(lc214_dou, "ato.tipo", "Lei Complementar", "LEI COMPLEMENTAR Nº 214, DE 16 DE JANEIRO DE 2025", "cabeçalho no DOU, edição extra 11-B, p. 1", "tipo normalizado", ["turn73search1"]),
                "ato.numero": provenance(lc214_dou, "ato.numero", "214", "LEI COMPLEMENTAR Nº 214, DE 16 DE JANEIRO DE 2025", "cabeçalho no DOU, edição extra 11-B, p. 1", "número sem pontuação adicional", ["turn73search1"]),
                "ato.data": provenance(lc214_dou, "ato.data", "2025-01-16", "LEI COMPLEMENTAR Nº 214, DE 16 DE JANEIRO DE 2025", "cabeçalho no DOU, edição extra 11-B, p. 1", "DD de mês por extenso de AAAA para ISO-8601", ["turn73search1"]),
                "ato.autoridade_emissora": provenance(lc214_dou, "ato.autoridade_emissora", "Presidente da República / Congresso Nacional", "O P R E S I D E N T E D A R E P Ú B L I C A\nFaço saber que o Congresso Nacional decreta e eu sanciono a seguinte Lei Complementar:", "DOU, edição extra 11-B, p. 1, preâmbulo da LC nº 214/2025", "autoridades literais normalizadas em ordem de promulgação e decreto", ["turn73search1"]),
                "jurisdicao": provenance(lc214_dou, "jurisdicao", "BR", "I - o Imposto sobre Bens e Serviços (IBS), de competência compartilhada entre Estados, Municípios e Distrito Federal, de que trata o art. 156-A da Constituição Federal; e\nII - a Contribuição Social sobre Bens e Serviços (CBS), de competência da União, de que trata o inciso V do caput do art. 195 da Constituição Federal.", "DOU edição extra 11-B, p. 1, art. 1º, I e II", "competências federativas brasileiras normalizadas como jurisdição BR", ["turn73search1"]),
                "temporal.publicacao": provenance(lc214_dou, "temporal.publicacao", "2025-01-16", "Brasília - DF, quinta-feira, 16 de janeiro de 2025", "DOU, edição extra 11-B, p. 1, cabeçalho", "data da edição oficial para ISO-8601", ["turn73search1"]),
                "temporal.inicio_vigencia": with_additional(
                    provenance(lc214, "temporal.inicio_vigencia", "2025-01-16", "Esta Lei Complementar entra em vigor na data de sua publicação", "Art. 544, caput", "data de publicação comprovada aplicada somente porque o ato a incorpora literalmente", ["turn59view0"]),
                    provenance(lc214_dou, "temporal.inicio_vigencia.publicacao", "2025-01-16", "Brasília - DF, quinta-feira, 16 de janeiro de 2025", "DOU, edição extra 11-B, p. 1, cabeçalho", "data da edição oficial para ISO-8601; fundamento da expressão 'data de sua publicação'", ["turn73search1"]),
                ),
                "temporal.inicio_eficacia": provenance(lc214, "temporal.inicio_eficacia", "2026-01-01", "a partir de 1º de janeiro de 2026, em relação aos demais dispositivos", "Art. 544, VI; arts. 1º e 4º não constam dos incisos I a V", "data literal para ISO-8601; exclusão verificada no elenco do art. 544", ["turn59view0"]),
                "regra_estruturada.transicao_rt": provenance(lc214, "regra_estruturada.transicao_rt", "Para os dispositivos deste card, a LC 214 fixa produção de efeitos a partir de 1º de janeiro de 2026, salvo regra específica do art. 544.", "VI – a partir de 1º de janeiro de 2026, em relação aos demais dispositivos.", "Art. 544, VI", "paráfrase conservadora vinculada aos arts. 1º e 4º", ["turn59view0"]),
            },
            "estado_publicacao": "NAO_PUBLICAR_SEM_RECIBO_NATIVO_E_REVISAO_CEGA",
        }),
    ]
    payload = {
        "schema": "rjc-prova-material-cards-v1",
        "gerado_por": "scripts/build_initial_proven_cards.py",
        "cards": cards,
        "nota": "O arquivo é uma fila de publicação: dupla captura local coincidiu, mas o estado bloqueia a superfície pública até haver recibo nativo de plataforma e revisão cega.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Gerados {len(cards)} cards com proveniência por campo: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
