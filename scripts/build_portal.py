#!/usr/bin/env python3
"""Build the static RJC open tax portal from the curated catalog."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import Counter
from datetime import datetime
from html import escape, unescape
from html.parser import HTMLParser
from pathlib import Path

from legal_modules import (
    build_legal_pages,
    federal_legislation_card,
    goias_legislation_card,
    legal_search_entries,
    legal_signal_links,
    legal_theme_teaser,
    legal_topic_teaser,
    topic_has_legal_module,
)
from state_legal_pages import (
    CONFIGURED_STATE_CHAPTERS,
    STATE_OFFICIAL_PORTALS,
    build_state_legal_pages,
    collect_state_documents,
    configured_chapter_path,
    configured_chapters,
    configured_profile,
    index_path,
    rel_href,
    source_path,
    state_curation,
    state_review_label,
    state_review_suffix,
    state_has_legal_pack,
    state_legal_search_entries,
    state_legislation_teaser,
    state_signal_links,
)


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://mjrrafael.github.io/rjc-conhecimento"
CATALOG = ROOT / "data" / "portal_catalog.json"
INVENTORY = ROOT / "data" / "legal_inventory.json"
STATE_SOURCE_AUDIT = ROOT / "data" / "state_source_audit.json"
MASTER_TAXONOMY = ROOT / "data" / "master_taxonomy.json"
MASTER_COVERAGE = ROOT / "data" / "master_source_coverage.json"
BENEFITS_CROSSWALK = ROOT / "data" / "benefits_crosswalk.json"
NCM_BENEFITS_INDEX = ROOT / "data" / "ncm_benefits_index.json"
PIS_COFINS_NCM = ROOT / "data" / "pis-cofins" / "ncm.ndjson"
PIS_COFINS_NCM_INDEX = ROOT / "data" / "pis-cofins" / "ncm-index.json"
PRODUTOS_NCM_INDEX = ROOT / "data" / "produtos-ncm" / "index.json"
CORPUS_LOCAL_REGISTRY = ROOT / "data" / "corpus-local" / "legal_sources_registry.json"
UF_SEALING_PLAN = ROOT / "data" / "corpus-local" / "uf-sealing-plan.json"
REFORMA_RESELO = ROOT / "data" / "reforma-tributaria" / "reselo-lc214-lc224-lc227.ndjson"
CONFAZ_5Y = ROOT / "data" / "confaz_ultimos_5_anos.json"


def derive_editorial_updated_on() -> str:
    try:
        payload = json.loads(BENEFITS_CROSSWALK.read_text(encoding="utf-8"))
    except Exception:
        return "14/06/2026"
    summary = payload.get("summary", {}) if isinstance(payload, dict) else {}
    value = str(summary.get("editorial_date") or summary.get("oldest_verified_on") or "").strip()
    try:
        return datetime.fromisoformat(value).strftime("%d/%m/%Y")
    except ValueError:
        return "14/06/2026"


EDITORIAL_UPDATED_ON = derive_editorial_updated_on()

FULL_SEARCH_STOPWORDS = {
    "a", "o", "as", "os", "um", "uma", "uns", "umas", "de", "da", "do", "das", "dos",
    "e", "ou", "em", "no", "na", "nos", "nas", "por", "para", "com", "sem", "sob",
    "sobre", "ao", "aos", "à", "às", "que", "se", "sua", "seu", "suas", "seus",
    "este", "esta", "estes", "estas", "esse", "essa", "ser", "sera", "serao", "sao",
    "nos", "termos",
}

STATE_DISPLAY_NAMES = {
    "AC": "Acre",
    "AL": "Alagoas",
    "AP": "Amapá",
    "AM": "Amazonas",
    "BA": "Bahia",
    "CE": "Ceará",
    "DF": "Distrito Federal",
    "ES": "Espírito Santo",
    "GO": "Goiás",
    "MA": "Maranhão",
    "MT": "Mato Grosso",
    "MS": "Mato Grosso do Sul",
    "MG": "Minas Gerais",
    "PA": "Pará",
    "PB": "Paraíba",
    "PR": "Paraná",
    "PE": "Pernambuco",
    "PI": "Piauí",
    "RJ": "Rio de Janeiro",
    "RN": "Rio Grande do Norte",
    "RS": "Rio Grande do Sul",
    "RO": "Rondônia",
    "RR": "Roraima",
    "SC": "Santa Catarina",
    "SP": "São Paulo",
    "SE": "Sergipe",
    "TO": "Tocantins",
}

STATE_REGIONS = [
    ("centro-oeste", "Centro-Oeste", ["DF", "GO", "MT", "MS"]),
    ("sudeste", "Sudeste", ["ES", "MG", "RJ", "SP"]),
    ("sul", "Sul", ["PR", "RS", "SC"]),
    ("nordeste", "Nordeste", ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"]),
    ("norte", "Norte", ["AC", "AP", "AM", "PA", "RO", "RR", "TO"]),
]

STATE_REGION_SUMMARIES = {
    "centro-oeste": "Goiás é o modelo profundo da primeira fase. Distrito Federal, Mato Grosso e Mato Grosso do Sul seguem a mesma matriz de RICMS, benefícios, ST, fundos e prova.",
    "sudeste": "Região de grande volume documental: legislação estadual, regimes setoriais, substituição tributária, benefícios industriais, comércio e serviços.",
    "sul": "Leitura por RICMS, incentivos, importação, agroindústria, crédito, diferimento, documento fiscal e obrigações acessórias.",
    "nordeste": "Organização por benefícios fiscais, desenvolvimento regional, fundos, regimes especiais, CONFAZ, indústria, atacado e prova documental.",
    "norte": "Trilha preparada para ICMS, incentivos regionais, Zona Franca, áreas de livre comércio, benefícios estaduais e conexão com atos federais.",
}

SIGNAL_LABELS = {
    "isencao": "Isenção",
    "reducao de base": "Redução de base",
    "credito outorgado": "Crédito outorgado/presumido",
    "diferimento": "Diferimento",
    "substituicao tributaria": "Substituição tributária",
    "aliquota": "Alíquota",
    "nao incidencia": "Não incidência",
    "suspensao": "Suspensão",
    "regime especial": "Regime especial",
    "protege/fundo": "Fundo/contrapartida",
    "exportacao": "Exportação",
    "monofasico": "Monofásico",
    "cBenef": "cBenef",
    "efd/sped": "EFD/SPED",
}

SIGNAL_STUDY = {
    "exportacao": {
        "summary": "Organiza imunidade, nao incidencia, saida com fim especifico de exportacao, manutencao de creditos e prova de embarque.",
        "law": "Leia primeiro a regra constitucional ou legal de nao tributacao; depois confira convenio, regulamento estadual, DU-E, NF-e e CFOP.",
        "proof": "Dossie com pedido, contrato, invoice quando houver, NF-e, comprovante de exportacao, DU-E e conciliacao na EFD.",
        "risk": "Tratar remessa interna como exportacao sem comprovar fim especifico, destinatario, prazo e documento de saida ao exterior.",
    },
    "aliquota": {
        "summary": "Separa aliquota nominal, carga efetiva, reducao de base, adicional, vigencia e excecao por produto ou operacao.",
        "law": "Confirme a regra geral e so depois leia anexos, tabelas, TIPI, RICMS ou ato especifico que altere a carga.",
        "proof": "Cadastro de produto, NCM, CST, memoria de calculo, XML e periodo de vigencia aplicado.",
        "risk": "Aplicar aliquota atual em fato gerador antigo ou confundir reducao de base com mudanca da aliquota.",
    },
    "protege/fundo": {
        "summary": "Mostra beneficios condicionados a fundo, contrapartida, termo, regime especial ou pagamento separado.",
        "law": "Leia a norma do beneficio junto com a norma do fundo; a fruicao costuma depender de recolhimento, adesao ou controle proprio.",
        "proof": "Termo, credenciamento, guia do fundo, demonstrativo de apuracao e vinculacao ao beneficio usado.",
        "risk": "Usar o beneficio e esquecer a contrapartida que mantem a fruicao defensavel.",
    },
    "isencao": {
        "summary": "Localiza hipoteses em que a lei afasta a cobranca dentro de destinatario, produto, operacao e periodo definidos.",
        "law": "Leia a isencao literalmente: sujeito, objeto, condicao, prazo, manutencao ou estorno de credito.",
        "proof": "Documento fiscal com CST correto, fundamento legal, cadastro da operacao e evidencia da condicao.",
        "risk": "Ampliar isencao por analogia para produto ou destinatario que a lei nao incluiu.",
    },
    "regime especial": {
        "summary": "Reune tratamentos que exigem ato concessivo, credenciamento, pedido, autorizacao ou procedimento diferenciado.",
        "law": "Diferencie regra geral de ato individual ou setorial; regime especial precisa ser lido junto com suas condicoes.",
        "proof": "Ato concessivo, vigencia, anexos, relatorios exigidos e rastreio das operacoes abrangidas.",
        "risk": "Continuar aplicando regime vencido, revogado ou fora da operacao autorizada.",
    },
    "suspensao": {
        "summary": "Indica casos em que a exigencia fica parada enquanto a condicao legal for cumprida.",
        "law": "Procure o evento que suspende, o evento que encerra a suspensao e a consequencia do descumprimento.",
        "proof": "Nota fiscal, termo, retorno, industrializacao, exportacao, controle de prazo e baixa documental.",
        "risk": "Tratar suspensao como isencao definitiva e nao controlar prazo ou destino.",
    },
    "diferimento": {
        "summary": "Mapeia transferencia do momento de pagamento para etapa posterior ou responsavel definido pela lei.",
        "law": "Identifique quem deixa de recolher, quem recolhe depois, em qual evento e com qual documento.",
        "proof": "XML, destinatario, evento posterior, memoria do imposto diferido e conciliacao de estoque ou producao.",
        "risk": "Perder o evento de encerramento e deixar o imposto sem recolhimento ou sem prova.",
    },
    "nao incidencia": {
        "summary": "Mostra situacoes fora do campo de incidencia, antes de discutir beneficio fiscal.",
        "law": "Comece pelo fato gerador. Se ele nao ocorre, a conclusao e de nao incidencia, nao de favor fiscal.",
        "proof": "Natureza da operacao, contrato, documento fiscal, livro e demonstracao de que o fato tributavel nao nasceu.",
        "risk": "Usar CST de beneficio quando o correto seria demonstrar ausencia de fato gerador.",
    },
    "credito outorgado": {
        "summary": "Agrupa credito concedido pela lei como tecnica de beneficio, incentivo ou carga efetiva.",
        "law": "Leia percentual, base do credito, condicoes, vedacoes, estornos, acumulacao com outros beneficios e fundo exigido.",
        "proof": "Memoria do credito, EFD, ajuste, XML, termo de opcao quando houver e conciliacao com o imposto devido.",
        "risk": "Somar credito outorgado com outro beneficio que a lei manda excluir.",
    },
    "cBenef": {
        "summary": "Conecta beneficio fiscal ao codigo declarado no documento fiscal eletronico.",
        "law": "Leia a regra material do beneficio antes de preencher o codigo; cBenef e reflexo documental, nao origem da tese.",
        "proof": "XML, cadastro fiscal, tabela da UF, dispositivo legal e rotina de atualizacao.",
        "risk": "Informar codigo de beneficio sem que a operacao cumpra a norma que o sustenta.",
    },
    "efd/sped": {
        "summary": "Leva a leitura legal para escrituracao, declaracao, ajustes, registros e cruzamentos digitais.",
        "law": "Depois da regra material, confira como ela aparece na EFD, EFD-Contribuicoes, ECF, DCTFWeb ou Reinf.",
        "proof": "Arquivo transmitido, recibo, registros, ajustes, memoria e conciliacao com XML, folha ou contabilidade.",
        "risk": "A lei estar correta no parecer, mas incoerente no arquivo digital entregue ao fisco.",
    },
    "monofasico": {
        "summary": "Separa concentracao de tributacao por cadeia, produto, NCM e etapa de circulacao.",
        "law": "Confira se a etapa anterior concentrou a carga e se a etapa atual esta na regra de aliquota zero ou tratamento especifico.",
        "proof": "NCM, fornecedor, XML, CST, EFD-Contribuicoes e memoria por produto.",
        "risk": "Aplicar monofasico por familia comercial sem confirmar NCM e etapa da cadeia.",
    },
    "substituicao tributaria": {
        "summary": "Organiza responsabilidade por recolhimento antecipado ou posterior, MVA, pauta, base presumida e ressarcimento.",
        "law": "Leia protocolo, convenio, RICMS, lista de mercadorias, base, responsavel, encerramento e direito de complemento ou ressarcimento.",
        "proof": "XML, NCM/CEST, pauta ou MVA, GNRE/guia, estoque, EFD e memoria por item.",
        "risk": "Aplicar ST por descricao parecida, sem mercadoria, CEST, destinatario e operacao enquadrados.",
    },
    "reducao de base": {
        "summary": "Mostra quando a lei reduz a base para atingir carga efetiva menor, normalmente com condicoes e vedacoes.",
        "law": "Leia percentual de reducao, carga final, operacoes abrangidas, manutencao de credito e exclusoes.",
        "proof": "Calculo da base reduzida, XML, CST, fundamento legal, NCM e demonstrativo da carga efetiva.",
        "risk": "Informar aliquota menor em vez de demonstrar a base reduzida e sua condicao legal.",
    },
}

FEDERAL_THEME_LABELS = {
    "pis_cofins": "PIS e Cofins",
    "ipi": "IPI",
    "iof": "IOF",
    "irpj_csll": "IRPJ e CSLL",
    "regimes": "Regimes tributarios",
    "previdencia_folha": "Folha e previdencia",
    "reforma": "Reforma tributaria",
    "beneficios": "Beneficios federais e DIRBI",
    "aduaneiro": "Aduaneiro",
    "geral": "Legislacao federal geral",
}

TOPIC_THEME_MAP = {
    "federal-pis-cofins": ["pis_cofins"],
    "federal-ipi": ["ipi"],
    "federal-irpj-csll": ["irpj_csll"],
    "federal-lucro-real": ["irpj_csll"],
    "federal-lucro-presumido": ["irpj_csll", "regimes"],
    "federal-beneficios-dirbi": ["beneficios", "regimes"],
    "folha-clt-previdencia": ["previdencia_folha"],
}

FEDERAL_EXTRA_PAGES = [
    {
        "theme": "pis_cofins",
        "path": "federal/pis-cofins-ncm.html",
        "title": "PIS/Cofins por NCM",
        "summary": "Tabela operacional de NCM, setor, aplicacao, monofasico, aliquota zero e outros tratamentos especificos com fonte primaria.",
        "custom_page": True,
    },
    {
        "theme": "iof",
        "path": "federal/iof.html",
        "title": "IOF: credito, cambio, seguro e titulos",
        "summary": "Leitura do IOF a partir da lei instituidora, regulamento e alteracoes recentes de aliquotas.",
    },
    {
        "theme": "reforma",
        "path": "federal/reforma-tributaria.html",
        "title": "Reforma tributaria: IBS, CBS e Imposto Seletivo",
        "summary": "Transicao da EC 132/2023 para a LC 214/2025, com foco em documento, apuracao, credito e governanca.",
    },
    {
        "theme": "aduaneiro",
        "path": "federal/aduaneiro.html",
        "title": "Aduaneiro e remessas internacionais",
        "summary": "Importacao, exportacao, remessas postais, PIS/Cofins-Importacao e prova documental em comercio exterior.",
    },
]

FEDERAL_ANALYSIS = {
    "pis_cofins": [
        "PIS e Cofins exigem separacao fina entre regime cumulativo, nao cumulativo, importacao, monofasicos, aliquota zero, suspensao e retencoes. O erro comum e olhar apenas a aliquota: a decisao nasce da receita, do produto, do regime da pessoa juridica e da regra de credito.",
        "Na auditoria, a boa pergunta e: a empresa consegue provar por documento e EFD-Contribuicoes por que tributou, excluiu, suspendeu ou creditou? Se a resposta depende de memoria informal, o risco esta aberto."
    ],
    "ipi": [
        "IPI e imposto de produto e industrializacao. A TIPI aponta a classificacao e a aliquota, mas a conclusao juridica depende de industrializacao, equiparacao a industrial, saida do estabelecimento, suspensao, isencao ou imunidade.",
        "O ensino pratico e simples: NCM mal classificada derruba o calculo inteiro. Antes de discutir beneficio, confirme produto, processo, enquadramento, estabelecimento e documento fiscal."
    ],
    "iof": [
        "IOF muda de leitura conforme a operacao: credito, cambio, seguro, titulos ou valores mobiliarios. A mesma sigla cobre fatos geradores diferentes, por isso a matriz correta separa modalidade, base, aliquota, responsavel, prazo e excecao.",
        "Em fechamento e auditoria, IOF nao deve ser tratado como custo bancario invisivel. Contrato, extrato, nota de corretagem, cambio, seguro e demonstrativo financeiro precisam sustentar a apuracao."
    ],
    "irpj_csll": [
        "IRPJ e CSLL pedem uma leitura de regime antes da leitura de imposto. Lucro Real exige ponte entre contabilidade, Lalur/Lacs, adicoes, exclusoes, compensacoes e ECF; Lucro Presumido exige segregacao de receita e percentuais corretos.",
        "A analise madura nao pergunta apenas quanto foi pago. Ela pergunta se o lucro societario, a base fiscal, a receita bruta, as exclusoes e os beneficios contam a mesma historia."
    ],
    "regimes": [
        "Regime tributario e uma decisao de arquitetura. Simples Nacional, Lucro Presumido e Lucro Real mudam base de calculo, obrigacoes, creditos, beneficios, retencoes e forma de provar a operacao.",
        "A escolha anual deve ser documentada. Sem simulacao, memoria e premissas, o regime vira palpite; com prova, vira decisao defensavel."
    ],
    "beneficios": [
        "Beneficio federal nao e desconto generico. Pode ser reducao, isencao, aliquota zero, suspensao, credito presumido, incentivo regional, regime especial ou obrigacao de declarar renuncia como DIRBI.",
        "O ponto de controle e a condicao. Beneficio bom sem requisito cumprido vira passivo, especialmente quando ha reducao linear, prazo de fruicao, habilitacao ou demonstracao em declaracao propria."
    ],
    "previdencia_folha": [
        "Folha combina direito do trabalho, custeio previdenciario, retenções, rubricas, eventos do eSocial, DCTFWeb e EFD-Reinf. A regra nasce no contrato e aparece na rubrica.",
        "A auditoria deve comparar acordo, jornada, folha, evento, incidencia, recolhimento e confissao. Quando a rubrica esta errada, o erro se espalha por encargos e declaracoes."
    ],
    "reforma": [
        "IBS, CBS e Imposto Seletivo reorganizam a tributacao do consumo. A leitura precisa acompanhar transicao, documento fiscal, creditos, split payment quando aplicavel, regimes especificos e convivencia com o modelo anterior.",
        "A postura correta em 2026 e preparar cadastro, contratos, ERP, classificacao de receitas e trilha de credito. A reforma nao e apenas nova aliquota; e uma mudanca de prova."
    ],
    "aduaneiro": [
        "Importacao e exportacao puxam tributos, documentos e regimes para o mesmo processo. A classificacao fiscal, origem, valor aduaneiro, despacho, drawback, Reintegra e tratamento de PIS/Cofins-Importacao precisam conversar.",
        "A prova boa nasce no dossie: DI/DUIMP, invoice, conhecimento, contrato, laudo tecnico, NF-e de entrada e memoria dos tributos."
    ],
    "geral": [
        "A legislacao federal geral serve como mapa de contexto. Ela ajuda a localizar conceitos, responsabilidades, competencias e atos que atravessam varios tributos.",
        "Use essa camada como indice de pesquisa e sempre volte ao ato especifico antes de concluir uma tese."
    ],
}

CHAPTER_READING = {
    "regra-maior": {
        "lead": "Comece aqui: esta e a norma que diz quando o tributo nasce, quem responde e qual e o campo de aplicacao.",
        "application": "No departamento fiscal, vira cadastro, CST/CSOSN, base e aliquota. No financeiro, vira prazo e caixa. Na auditoria, vira pergunta de prova.",
    },
    "beneficios-isencoes": {
        "lead": "Beneficio nao e liberalidade. A lei reduz, isenta, suspende ou concede credito apenas dentro do desenho que ela mesma fixou.",
        "application": "Antes de aplicar, separe produto, NCM, operacao, destinatario, periodo, regime da empresa, documento fiscal e eventual habilitacao.",
    },
    "excecoes-condicoes": {
        "lead": "As excecoes costumam ser o ponto de autuacao. O texto favoravel quase sempre vem acompanhado de condicao, vedacao ou perda do direito.",
        "application": "Transforme cada condicao em checklist: regularidade, prazo, ato concessivo, recolhimento, declaracao, escritura fiscal e memoria de calculo.",
    },
    "documento-prova": {
        "lead": "O imposto pode estar correto e mesmo assim a empresa pode perder a discussao se o documento nao sustentar a historia.",
        "application": "Conecte XML, EFD, EFD-Contribuicoes, ECF, DCTFWeb, eSocial, contrato, laudo, tabela fiscal e demonstrativo de apuracao.",
    },
    "apuracao-recolhimento": {
        "lead": "A apuracao e o lugar em que a tese deixa de ser teoria. Credito, debito, estorno, compensacao e recolhimento precisam fechar.",
        "application": "A revisao deve bater documento, livro, declaracao, guia, contabilidade e conta de resultado ou custo.",
    },
}

CURATED_TOPIC_CHAPTERS = {
    "goias-icms-beneficios": [
        {
            "id": "regra-maior",
            "title": "Regra maior",
            "passages": [
                {
                    "source": "RCTE/GO, Anexo IX, art. 1º",
                    "text": "Art. 1º Os benefícios fiscais, a que se referem os arts. 83 e 84 deste regulamento, são disciplinados pelas normas contidas neste anexo. § 1º A utilização dos benefícios fiscais previstos neste anexo, cuja concessão tenha sido autorizada por lei estadual, fica condicionada a que o sujeito passivo esteja adimplente com o ICMS e não possua crédito tributário inscrito em dívida ativa.",
                }
            ],
        },
        {
            "id": "beneficios-isencoes",
            "title": "Beneficios, isencoes e reducoes",
            "passages": [
                {
                    "source": "RCTE/GO, Anexo IX, art. 2º",
                    "text": "Art. 2º O benefício fiscal da manutenção do crédito, quando concedido, deve constar do mesmo dispositivo do regulamento que dispuser sobre a não-incidência, isenção ou redução da base de cálculo.",
                }
            ],
        },
        {
            "id": "excecoes-condicoes",
            "title": "Excecoes, condicoes e vedacoes",
            "passages": [
                {
                    "source": "RCTE/GO, Anexo IX, art. 1º, § 1º-B",
                    "text": "§ 1º-B Na hipótese prevista no inciso I do § 1º, a falta de pagamento, ainda que parcial, do imposto devido, inclusive o devido por substituição tributária, no prazo previsto na legislação tributária, correspondente a determinado período de apuração, implica perda do direito de o contribuinte utilizar o benefício fiscal, exclusivamente no referido período de apuração.",
                }
            ],
        },
    ],
    "confaz-atos-beneficios": [
        {
            "id": "regra-maior",
            "title": "Regra maior",
            "passages": [
                {
                    "source": "LC 24/1975, art. 1º",
                    "text": "Art. 1º As isenções do imposto sobre operações relativas à circulação de mercadorias serão concedidas ou revogadas nos termos de convênios celebrados e ratificados pelos Estados e pelo Distrito Federal, segundo esta Lei.",
                }
            ],
        },
        {
            "id": "beneficios-isencoes",
            "title": "Beneficios, isencoes e reducoes",
            "passages": [
                {
                    "source": "LC 24/1975, art. 1º, parágrafo único",
                    "text": "O disposto neste artigo também se aplica à redução da base de cálculo, à devolução total ou parcial do tributo, à concessão de créditos presumidos e a quaisquer outros incentivos ou favores fiscais ou financeiro-fiscais concedidos com base no ICMS.",
                }
            ],
        },
        {
            "id": "excecoes-condicoes",
            "title": "Excecoes, condicoes e vedacoes",
            "passages": [
                {
                    "source": "LC 160/2017, arts. 1º a 3º",
                    "text": "A LC 160/2017 permite deliberar sobre remissão e reinstituição de benefícios de ICMS concedidos em desacordo com a LC 24/1975, condicionando o regime à publicação dos atos normativos e ao registro e depósito da documentação no CONFAZ.",
                }
            ],
        },
    ],
    "folha-clt-previdencia": [
        {
            "id": "regra-maior",
            "title": "Regra maior",
            "passages": [
                {
                    "source": "CLT, arts. 2º e 3º",
                    "text": "Art. 2º Considera-se empregador a empresa que, assumindo os riscos da atividade econômica, admite, assalaria e dirige a prestação pessoal de serviço. Art. 3º Considera-se empregado toda pessoa física que prestar serviços de natureza não eventual a empregador, sob dependência deste e mediante salário.",
                }
            ],
        }
    ],
}


def slug(value: str) -> str:
    value = value.lower()
    value = value.replace("ç", "c").replace("ã", "a").replace("á", "a")
    value = value.replace("â", "a").replace("é", "e").replace("ê", "e")
    value = value.replace("í", "i").replace("ó", "o").replace("ô", "o")
    value = value.replace("ú", "u")
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or "item"


def rel_prefix(path: str) -> str:
    depth = len(Path(path).parts) - 1
    return "../" * depth


def site_path(path: str) -> str:
    return path.replace("\\", "/").lstrip("/")


def canonical_url(path: str) -> str:
    normalized = site_path(path)
    if normalized in {"", "index.html"}:
        return f"{BASE_URL}/"
    return f"{BASE_URL}/{normalized}"


def a(href: str, label: str, class_name: str = "") -> str:
    cls = f' class="{escape(class_name)}"' if class_name else ""
    return f'<a href="{escape(href)}"{cls}>{escape(label)}</a>'


def load_inventory() -> dict:
    if not INVENTORY.exists():
        return {"states": [], "federal": {"themes": {}, "documents": []}}
    return json.loads(INVENTORY.read_text(encoding="utf-8"))


def load_json(path: Path, fallback: object) -> object:
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def load_ndjson(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def fmt_num(value: int | float | str) -> str:
    try:
        return f"{int(value):,}".replace(",", ".")
    except (TypeError, ValueError):
        return str(value)


PORTUGUESE_WORDS = {
    "acessorias": "acessórias",
    "acessorio": "acessório",
    "adimplencia": "adimplência",
    "alinea": "alínea",
    "alineas": "alíneas",
    "aliquota": "alíquota",
    "aliquotas": "alíquotas",
    "analise": "análise",
    "aplicacao": "aplicação",
    "aplicavel": "aplicável",
    "aplicaveis": "aplicáveis",
    "apuracao": "apuração",
    "area": "área",
    "areas": "áreas",
    "ausencia": "ausência",
    "autorizacao": "autorização",
    "autorizacoes": "autorizações",
    "automatico": "automático",
    "autonomo": "autônomo",
    "autonomos": "autônomos",
    "beneficio": "benefício",
    "beneficios": "benefícios",
    "calculo": "cálculo",
    "capitulo": "capítulo",
    "capitulos": "capítulos",
    "classificacao": "classificação",
    "cobranca": "cobrança",
    "codigo": "código",
    "competencia": "competência",
    "condicao": "condição",
    "condicoes": "condições",
    "conexao": "conexão",
    "conclusao": "conclusão",
    "conciliacao": "conciliação",
    "consequencia": "consequência",
    "consequencias": "consequências",
    "contabil": "contábil",
    "contabeis": "contábeis",
    "contabilizacao": "contabilização",
    "contribuicao": "contribuição",
    "contribuicoes": "contribuições",
    "conteudo": "conteúdo",
    "convenio": "convênio",
    "convenios": "convênios",
    "credito": "crédito",
    "creditos": "créditos",
    "decisao": "decisão",
    "declaracao": "declaração",
    "declaracoes": "declarações",
    "desoneracao": "desoneração",
    "destinatario": "destinatário",
    "destinatarios": "destinatários",
    "descricao": "descrição",
    "dossie": "dossiê",
    "economica": "econômica",
    "emissao": "emissão",
    "equiparacao": "equiparação",
    "escrituracao": "escrituração",
    "especifica": "específica",
    "especificas": "específicas",
    "especifico": "específico",
    "especificos": "específicos",
    "excecao": "exceção",
    "excecoes": "exceções",
    "exportacao": "exportação",
    "exigencia": "exigência",
    "exigencias": "exigências",
    "fiscalizacao": "fiscalização",
    "fruicao": "fruição",
    "generica": "genérica",
    "genericas": "genéricas",
    "generico": "genérico",
    "genericos": "genéricos",
    "goias": "Goiás",
    "ha": "há",
    "habilitacao": "habilitação",
    "hipotese": "hipótese",
    "hipoteses": "hipóteses",
    "incidencia": "incidência",
    "incidencias": "incidências",
    "indice": "índice",
    "indices": "índices",
    "industrializacao": "industrialização",
    "informacao": "informação",
    "informacoes": "informações",
    "importacao": "importação",
    "instrucao": "instrução",
    "isencao": "isenção",
    "ja": "já",
    "juridica": "jurídica",
    "juridico": "jurídico",
    "legislacao": "legislação",
    "liquido": "líquido",
    "logica": "lógica",
    "lancamento": "lançamento",
    "lancamentos": "lançamentos",
    "manutencao": "manutenção",
    "memoria": "memória",
    "ministerio": "ministério",
    "minimo": "mínimo",
    "minimos": "mínimos",
    "modulo": "módulo",
    "modulos": "módulos",
    "monofasico": "monofásico",
    "movimentacao": "movimentação",
    "mudanca": "mudança",
    "necessaria": "necessária",
    "necessarias": "necessárias",
    "necessario": "necessário",
    "necessarios": "necessários",
    "nao": "não",
    "obrigacao": "obrigação",
    "obrigacoes": "obrigações",
    "operacao": "operação",
    "operacoes": "operações",
    "orgao": "órgão",
    "orgaos": "órgãos",
    "pagina": "página",
    "paragrafo": "parágrafo",
    "paragrafos": "parágrafos",
    "peca": "peça",
    "pecas": "peças",
    "periodo": "período",
    "periodica": "periódica",
    "periodicas": "periódicas",
    "periodico": "periódico",
    "periodicos": "periódicos",
    "permissao": "permissão",
    "previdencia": "previdência",
    "previdenciaria": "previdenciária",
    "previdenciarias": "previdenciárias",
    "previdenciario": "previdenciário",
    "previdenciarios": "previdenciários",
    "producao": "produção",
    "propria": "própria",
    "proprio": "próprio",
    "prova": "prova",
    "publicacao": "publicação",
    "publica": "pública",
    "publicas": "públicas",
    "publico": "público",
    "publicos": "públicos",
    "receita": "receita",
    "reducao": "redução",
    "referencia": "referência",
    "regulamento": "regulamento",
    "relacao": "relação",
    "relatorio": "relatório",
    "relatorios": "relatórios",
    "remissao": "remissão",
    "remissoes": "remissões",
    "responsavel": "responsável",
    "responsaveis": "responsáveis",
    "restricao": "restrição",
    "restricoes": "restrições",
    "retencao": "retenção",
    "retencoes": "retenções",
    "revisao": "revisão",
    "revogacao": "revogação",
    "revogacoes": "revogações",
    "saida": "saída",
    "salario": "salário",
    "salarios": "salários",
    "seguranca": "segurança",
    "sera": "será",
    "situacao": "situação",
    "situacoes": "situações",
    "so": "só",
    "tambem": "também",
    "reune": "reúne",
    "substituicao": "substituição",
    "suspensao": "suspensão",
    "tecnica": "técnica",
    "tecnicas": "técnicas",
    "tecnico": "técnico",
    "tecnicos": "técnicos",
    "transferencia": "transferência",
    "tributacao": "tributação",
    "tributaria": "tributária",
    "tributario": "tributário",
    "tributarios": "tributários",
    "tributavel": "tributável",
    "unico": "único",
    "utilizacao": "utilização",
    "validacao": "validação",
    "vedacoes": "vedações",
    "vigencia": "vigência",
}


def preserve_case(original: str, replacement: str) -> str:
    if original.isupper():
        return replacement.upper()
    if original[:1].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement


PORTUGUESE_PHRASES = {
    "a chave e a coerencia": "a chave é a coerência",
    "folha tambem e": "folha também é",
    "o que e": "o que é",
    "tambem e": "também é",
}

PORTUGUESE_PHRASE_PATTERN = re.compile(
    r"(?<!\w)("
    + "|".join(re.escape(phrase) for phrase in sorted(PORTUGUESE_PHRASES, key=len, reverse=True))
    + r")(?!\w)",
    re.I,
)

PORTUGUESE_PATTERN = re.compile(
    r"(?<!\w)("
    + "|".join(re.escape(word) for word in sorted(PORTUGUESE_WORDS, key=len, reverse=True))
    + r")(?!\w)",
    re.I,
)


def polish_portuguese_text(text: str) -> str:
    text = PORTUGUESE_PHRASE_PATTERN.sub(
        lambda match: preserve_case(match.group(0), PORTUGUESE_PHRASES[match.group(0).lower()]),
        text,
    )
    return PORTUGUESE_PATTERN.sub(
        lambda match: preserve_case(match.group(0), PORTUGUESE_WORDS[match.group(0).lower()]),
        text,
    )


def polish_html_text(content: str) -> str:
    parts = re.split(r"(<[^>]+>)", content)
    for index in range(0, len(parts), 2):
        parts[index] = polish_portuguese_text(parts[index])
    return "".join(parts)


def state_href(uf: str) -> str:
    return "estados/goias.html" if uf == "GO" else f"estados/{uf.lower()}.html"


def local_state_href(uf: str) -> str:
    return "goias.html" if uf == "GO" else f"{uf.lower()}.html"


def state_display_name(state: dict) -> str:
    return STATE_DISPLAY_NAMES.get(state["uf"], state["name"])


def state_flag(path_prefix: str, uf: str, name: str) -> str:
    src = f"{path_prefix}assets/flags/{uf.lower()}.svg"
    return f"""
  <div class="state-symbol">
    <img src="{escape(src)}" alt="{escape(name)} - bandeira estadual" loading="lazy" decoding="async">
    <strong>{escape(uf)}</strong>
  </div>
"""


def state_card_markup(state: dict, data: dict) -> str:
    inv = inventory_state(data, state["uf"])
    display_name = state_display_name(state)
    href = local_state_href(state["uf"])
    klass = "featured" if state["uf"] == "GO" else ""
    if state["uf"] == "GO":
        status = "Capitulo profundo publicado"
    elif state_has_legal_pack(state["uf"]):
        status = "ICMS em tela publicado"
    elif inv.get("file_count", 0):
        status = state_review_label(state["uf"])
    else:
        status = state_review_label(state["uf"])
    coverage = (
        "RICMS, leis, anexos e benefícios em tela"
        if state_has_legal_pack(state["uf"])
        else "Material aberto para leitura e revisão"
        if inv.get("file_count", 0)
        else state["coverage"]
    )
    search_text = state["uf"] + " " + state["name"] + " " + display_name + " ICMS beneficios fiscais " + " ".join(inv.get("categories", []))
    return f"""
<a class="state-card {klass} searchable-card" href="{escape(href)}"
   data-search="{escape(search_text)}">
  {state_flag("../", state["uf"], display_name)}
  <h3>{escape(display_name)}</h3>
  <p>{escape(status)}</p>
  <small>{escape(coverage)}</small>
</a>
"""


def state_queue_card(state: dict, current_path: str) -> str:
    uf = state["uf"]
    display_name = state_display_name(state)
    curation = state_curation(uf)
    status = curation.get("status", "estrutura")
    next_step = curation.get("next_step", "Curadoria fonte-a-fonte pendente.")
    portal = STATE_OFFICIAL_PORTALS.get(uf, "")
    deep = state_has_legal_pack(uf)
    status_label = "Publicado em profundidade" if deep else state_review_label(uf)
    status_class = "is-ready" if deep else ("is-blocked" if status == "revisado_escopo_bloqueado" else "is-pending")
    page_href = local_state_href(uf)
    portal_link = (
        f'<a href="{escape(portal)}" target="_blank" rel="noopener">portal oficial</a>'
        if portal
        else "<span>portal oficial a mapear</span>"
    )
    return f"""
<article class="state-queue-card searchable-card {status_class}"
         data-search="{escape(uf + ' ' + display_name + ' ICMS beneficios fiscais ' + status + ' ' + next_step)}">
  <div class="state-queue-head">
    {state_flag('../', uf, display_name)}
    <div>
      <strong>{escape(display_name)}</strong>
      <span>{escape(status_label)}</span>
    </div>
  </div>
  <p>{escape(next_step)}</p>
  <div class="state-queue-links">
    <a href="{escape(page_href)}">ler na web</a>
    {portal_link}
  </div>
</article>
"""


def state_expansion_queue(data: dict) -> str:
    states_by_uf = {state["uf"]: state for state in data["states"]}
    published = [uf for _region_id, _label, ufs in STATE_REGIONS for uf in ufs if uf in states_by_uf and state_has_legal_pack(uf)]
    pending = [uf for _region_id, _label, ufs in STATE_REGIONS for uf in ufs if uf in states_by_uf and not state_has_legal_pack(uf)]
    reviewed = [uf for uf in pending if state_curation(uf).get("status", "").startswith("revisado")]
    region_blocks = []
    for region_id, label, ufs in STATE_REGIONS:
        cards = [
            state_queue_card(states_by_uf[uf], "estados/index.html")
            for uf in ufs
            if uf in states_by_uf and not state_has_legal_pack(uf)
        ]
        if not cards:
            continue
        region_blocks.append(f"""
<section class="state-queue-region" id="fila-{escape(region_id)}">
  <h3>{escape(label)}</h3>
  <div class="state-queue-grid">{''.join(cards)}</div>
</section>
""")
    if not region_blocks:
        pending_html = "<p>Todos os Estados estão publicados em profundidade.</p>"
    else:
        pending_html = "".join(region_blocks)
    return f"""
<section class="section-wrap state-expansion-queue">
  <div class="section-heading">
    <span class="eyebrow">Esteira editorial</span>
    <h2>O que já está profundo e o que ainda exige curadoria</h2>
    <p>{fmt_num(len(published))} UFs têm legislação em tela por capítulos. {fmt_num(len(reviewed))} UFs foram revisadas criticamente e seguem abertas para leitura, sem aprovação profunda, até que RICMS, benefícios, atos modificadores e fonte oficial limpa sejam conferidos.</p>
  </div>
  <div class="continuity">
    <h2>Estados profundos publicados</h2>
    <div>
      {''.join(f'<a href="{escape(local_state_href(uf))}">{escape(uf)}</a>' for uf in published)}
      <a href="auditoria-fontes.html">auditoria fonte a fonte</a>
    </div>
  </div>
  {pending_html}
</section>
"""


def state_source_audit_page(data: dict) -> str:
    current = "estados/auditoria-fontes.html"
    if not STATE_SOURCE_AUDIT.exists():
        body = """
<section class="hero-panel legal-hero">
  <div>
    <span class="eyebrow">Estados</span>
    <h1>Auditoria fonte a fonte</h1>
    <p>A auditoria estadual ainda não foi gerada neste ambiente.</p>
  </div>
</section>
"""
        return layout(current, "Auditoria fonte a fonte", "Auditoria estadual por UF.", body, "estados")
    report = json.loads(STATE_SOURCE_AUDIT.read_text(encoding="utf-8"))
    summary = report.get("summary", {})
    states_html = []
    for uf, item in report.get("states", {}).items():
        docs = item.get("documents", [])
        local_docs = {doc["file"]: doc for doc in collect_state_documents(uf)} if uf != "GO" else {}
        flags = item.get("flags") or ["sem alerta automatizado"]
        state_status = "publicado" if item.get("publish_deep") or uf == "GO" else state_review_label(uf)
        doc_rows = []
        for doc in docs:
            local_doc = local_docs.get(doc.get("file", ""))
            open_link = ""
            if local_doc:
                open_link = f'<a href="{escape(rel_href(current, source_path(uf, local_doc)))}">abrir fonte em tela</a>'
            source_names = "; ".join(doc.get("source_documents", [])[:3]) or "fonte interna a conferir"
            doc_flags = "; ".join(doc.get("flags", [])[:5]) or "sem alerta automatizado"
            doc_rows.append(f"""
<article class="source-audit-doc searchable-card"
         data-search="{escape(uf + ' ' + doc.get('file', '') + ' ' + doc.get('category', '') + ' ' + doc_flags)}">
  <div>
    <strong>{escape(doc.get('file', 'fonte'))}</strong>
    <span>{escape(doc.get('category', ''))} · {fmt_num(int(doc.get('chars', 0)))} caracteres · escopo dominante: {escape(doc.get('dominant_scope', ''))}</span>
  </div>
  <p>{escape(doc_flags)}</p>
  <small>{escape(source_names)}</small>
  <div class="state-queue-links">{open_link}</div>
</article>
""")
        state_index = index_path(uf) if local_docs else state_href(uf)
        states_html.append(f"""
<details class="source-audit-state searchable-card" {'open' if not (item.get('publish_deep') or uf == 'GO') else ''}>
  <summary>
    <strong>{escape(uf)} · {escape(item.get('estado', uf))}</strong>
    <span>{escape(state_status)} · {fmt_num(int(item.get('document_count', 0)))} documentos · {escape('; '.join(flags[:4]))}</span>
  </summary>
  <div class="source-audit-actions">
    <a href="{escape(rel_href(current, state_href(uf)))}">página estadual</a>
    <a href="{escape(rel_href(current, state_index))}">índice de leitura</a>
    <a href="{escape(STATE_OFFICIAL_PORTALS.get(uf, '#'))}" target="_blank" rel="noopener">portal oficial</a>
  </div>
  <div class="source-audit-docs">{''.join(doc_rows) if doc_rows else '<p>Sem documentos candidatos nesta auditoria.</p>'}</div>
</details>
""")
    body = f"""
<section class="hero-panel legal-hero">
  <div>
    <span class="eyebrow">Estados · revisão crítica</span>
    <h1>Auditoria fonte a fonte</h1>
    <p>Use esta página como bancada de revisão: abra a fonte em tela, compare com o portal oficial e só então aprove a análise estadual profunda.</p>
  </div>
  <aside class="hero-proof">
    <strong>Escopo auditado</strong>
    <p>{fmt_num(int(summary.get('states', 0)))} UFs · {fmt_num(int(summary.get('docs', 0)))} documentos candidatos · {fmt_num(int(summary.get('blocked', 0)))} UFs sem aprovação profunda</p>
  </aside>
</section>
<section class="law-ledger">
  <div><h2>Como usar</h2><p>Estados revisados com pendências podem ser lidos na web, mas ainda não devem ser usados como conclusão operacional.</p></div>
  <div><h2>O que conferir</h2><p>Escopo ICMS, RICMS vigente, anexos de benefícios, atos modificadores, fonte oficial, ruído de extração e contaminação por outros tributos.</p></div>
  <div><h2>Depois da aprovação</h2><p>O Estado sai do selo de revisão com pendências e entra no padrão profundo: lei em tela, análise, aplicação, prova e riscos.</p></div>
</section>
<section class="section-wrap source-audit-list">
  <div class="section-heading">
    <span class="eyebrow">Leitura por UF</span>
    <h2>Abra cada fonte sem sair do portal</h2>
    <p>Os blocos abaixo são deliberadamente explícitos. A ideia é tornar a revisão mais confortável no navegador do que em relatório Markdown.</p>
  </div>
  {''.join(states_html)}
</section>
"""
    return layout(current, "Auditoria fonte a fonte", "Auditoria estadual por UF com fontes em tela.", body, "estados")


def state_curation_panel(uf: str) -> str:
    name = STATE_DISPLAY_NAMES.get(uf, uf)
    curation = state_curation(uf)
    next_step = curation.get("next_step", "Curadoria fonte-a-fonte pendente.")
    label = state_review_label(uf)
    reviewed_on = curation.get("reviewed_on", "")
    reviewed_note = f" Revisão crítica registrada em {reviewed_on}." if reviewed_on else ""
    portal = STATE_OFFICIAL_PORTALS.get(uf, "")
    portal_html = (
        f'<a href="{escape(portal)}" target="_blank" rel="noopener">Abrir portal oficial da Secretaria da Fazenda</a>'
        if portal
        else "<span>Portal oficial ainda não mapeado</span>"
    )
    return f"""
<section class="content-block state-curation-panel searchable-card"
         data-search="{escape(uf + ' ' + name + ' curadoria ICMS RICMS beneficios fiscais fonte oficial')}">
  <span class="eyebrow">{escape(label)}</span>
  <h2>Como continuar a revisão deste Estado</h2>
  <p>{escape(next_step + reviewed_note)}</p>
  <div class="department-grid">
    <article><strong>1. Ler na web</strong><span>Abrir o índice estadual, fontes em tela e capítulos candidatos.</span></article>
    <article><strong>2. Conferir fonte</strong><span>Comparar Lei do ICMS, RICMS, anexos e decretos com o portal oficial.</span></article>
    <article><strong>3. Separar benefício</strong><span>Isenções, reduções, créditos, diferimentos, regimes, fundos, programas e matriz LC 160/CONFAZ.</span></article>
    <article><strong>4. Aprovar depois</strong><span>Só após fonte limpa e escopo ICMS comprovado a página deixa o selo de pendência.</span></article>
  </div>
  <div class="continuity compact">
    <h2>Fonte de partida</h2>
    <div>{portal_html}</div>
  </div>
</section>
"""


def inventory_state(data: dict, uf: str) -> dict:
    for state in data.get("inventory", {}).get("states", []):
        if state.get("uf") == uf:
            return state
    return {"uf": uf, "file_count": 0, "total_chars": 0, "categories": [], "signals": {}, "documents": [], "commentary": {}}


def federal_theme(data: dict, key: str) -> dict:
    return data.get("inventory", {}).get("federal", {}).get("themes", {}).get(
        key,
        {"theme": key, "file_count": 0, "total_chars": 0, "signals": {}, "documents": []},
    )


def official_source_url(url: str) -> str:
    if not url:
        return ""
    clean = url.strip()
    if clean.startswith("http://www.planalto.gov.br"):
        clean = "https://www.planalto.gov.br" + clean[len("http://www.planalto.gov.br") :]
    if clean.startswith("http://planalto.gov.br"):
        clean = "https://www.planalto.gov.br" + clean[len("http://planalto.gov.br") :]
    return clean


def is_official_source(url: str) -> bool:
    clean = official_source_url(url).lower()
    official_domains = (
        "planalto.gov.br",
        "gov.br/receitafederal",
        "normas.receita.fazenda.gov.br",
        "confaz.fazenda.gov.br",
        "sped.rfb.gov.br",
        "cgibs.gov.br",
        "www.gov.br",
    )
    return clean.startswith("https://") and any(domain in clean for domain in official_domains)


def render_doc_source(doc: dict) -> str:
    url = official_source_url(doc.get("source", ""))
    if is_official_source(url):
        return f'<a href="{escape(url)}" target="_blank" rel="noopener">abrir ato</a>'
    return '<span class="source-status">revisar no Planalto, Receita, DOU ou portal do ente antes de citar</span>'


def signal_badges(signals: dict, limit: int = 6) -> str:
    if not signals:
        return '<span class="signal-chip quiet">sem sinal material no indice</span>'
    items = sorted(signals.items(), key=lambda item: item[1], reverse=True)[:limit]
    return "".join(
        f'<span class="signal-chip">{escape(SIGNAL_LABELS.get(key, key))}: {fmt_num(value)}</span>'
        for key, value in items
    )


def signal_detail(key: str) -> dict:
    label = SIGNAL_LABELS.get(key, key)
    default = {
        "summary": "Tema recorrente no texto legal que precisa ser conectado a regra, excecao, documento e prova.",
        "law": "Leia a norma material, depois o regulamento, anexos e obrigacoes acessorias que fazem a regra aparecer na rotina.",
        "proof": "Guarde lei, documento fiscal, memoria de calculo, declaracao e evidencia operacional da condicao aplicada.",
        "risk": "Aplicar a palavra encontrada no acervo sem confirmar se o artigo realmente regula a operacao concreta.",
    }
    detail = dict(default)
    detail.update(SIGNAL_STUDY.get(key, {}))
    detail["label"] = label
    return detail


def signal_anchor(key: str) -> str:
    return f"capitulo-{slug(key)}"


def signal_sections(items: list[tuple[str, int]], current_path: str = "", theme_key: str = "") -> str:
    sections = []
    for key, value in items:
        detail = signal_detail(key)
        if current_path and theme_key and theme_key.startswith("state:"):
            law_links = state_signal_links(theme_key.split(":", 1)[1], key, current_path)
        else:
            law_links = legal_signal_links(theme_key, key, current_path) if current_path and theme_key else ""
        sections.append(f"""
<article class="signal-study searchable-card" id="{escape(signal_anchor(key))}"
         data-search="{escape(detail['label'] + ' ' + detail['summary'] + ' ' + key)}">
  <div>
    <span class="eyebrow">Capítulo de estudo</span>
    <h3>{escape(detail['label'])}</h3>
    <p>{escape(detail['summary'])}</p>
  </div>
  <dl class="signal-study-grid">
    <dt>Como ler a lei</dt><dd>{escape(detail['law'])}</dd>
    <dt>Prova documental</dt><dd>{escape(detail['proof'])}</dd>
    <dt>Risco comum</dt><dd>{escape(detail['risk'])}</dd>
    <dt>Onde aparece</dt><dd>O tema aparece {fmt_num(value)} vezes no texto usado nesta trilha. A contagem orienta a pesquisa, mas a conclusão nasce da leitura do artigo indicado.</dd>
  </dl>
  {law_links}
</article>
""")
    if not sections:
        return ""
    return f"""
<section class="signal-study-list">
  <div class="section-heading">
    <span class="eyebrow">Capítulos por tema</span>
    <h2>Do índice para a aula</h2>
    <p>Cada item abaixo abre uma seção própria: primeiro o conceito, depois a leitura da lei, a prova documental, o risco comum e o caminho para a legislação em tela.</p>
  </div>
  {''.join(sections)}
</section>
"""


def signal_grid(signals: dict, title: str, intro: str, current_path: str = "", theme_key: str = "") -> str:
    items = sorted(signals.items(), key=lambda item: item[1], reverse=True)[:10]
    if not items:
        cards = '<article class="signal-card"><strong>Sem capítulos suficientes</strong><span>Não há material publicado nesta página para abrir um capítulo temático responsável.</span></article>'
    else:
        cards = "".join(
            f'<a class="signal-card" href="#{escape(signal_anchor(key))}"><strong>{escape(signal_detail(key)["label"])}</strong>'
            f'<span>{escape(signal_detail(key)["summary"])}</span>'
            f'<small>Abrir capítulo</small></a>'
            for key, value in items
        )
    return f"""
<section class="signal-panel">
  <div class="section-heading">
    <span class="eyebrow">Índice de estudo</span>
    <h2>{escape(title)}</h2>
    <p>{escape(intro)}</p>
  </div>
  <div class="signal-grid">{cards}</div>
</section>
{signal_sections(items, current_path, theme_key)}
"""


FOLHA_STUDY_CARDS = [
    (
        "Contrato e registro",
        "A relação de emprego, registro, função, salário, admissão e eventos não periódicos.",
        "federal/legislacao/folha-clt/contrato-emprego-registro.html",
    ),
    (
        "Jornada e férias",
        "Ponto, escala, horas extras, intervalo, descanso, férias e reflexo na remuneração.",
        "federal/legislacao/folha-clt/jornada-descanso-ferias.html",
    ),
    (
        "Verbas e incidências",
        "Separação entre verba remuneratória e indenizatória, rubrica, eSocial, FGTS, IRRF e previdência.",
        "federal/legislacao/folha-clt/verbas-indenizatorias-remuneratorias.html",
    ),
    (
        "Custeio previdenciário",
        "Salário-de-contribuição, segurados, empresa, retenções, arrecadação e DCTFWeb.",
        "federal/legislacao/folha-clt/custeio-previdenciario.html",
    ),
    (
        "FAP e RAT/SAT",
        "Risco ambiental do trabalho, FAP, SST, CAT, afastamentos e efeito no custo previdenciário.",
        "federal/legislacao/folha-clt/fap-rat-sat.html",
    ),
    (
        "Retenção de 11%",
        "Cessão de mão de obra, empreitada, nota fiscal, EFD-Reinf, DCTFWeb e compensação.",
        "federal/legislacao/folha-clt/retencao-11-cessao-mao-obra.html",
    ),
    (
        "Desoneração e CPRB",
        "Contribuição sobre receita bruta, setores, base, alíquota, segregação e período de aplicação.",
        "federal/legislacao/folha-clt/desoneracao-folha-cprb.html",
    ),
    (
        "eSocial e FGTS Digital",
        "Eventos, rubricas, fechamento, FGTS, DCTFWeb, EFD-Reinf, recibos e prova mensal.",
        "federal/legislacao/folha-clt/esocial-obrigacoes-digitais.html",
    ),
]


def folha_study_grid(current_path: str) -> str:
    cards = "".join(
        f"""
<a class="signal-card searchable-card" href="{escape(rel_href(current_path, href))}"
   data-search="{escape('Folha CLT previdencia eSocial FGTS DCTFWeb Reinf ' + title + ' ' + summary)}">
  <strong>{escape(title)}</strong>
  <span>{escape(summary)}</span>
  <small>Abrir capítulo</small>
</a>
"""
        for title, summary, href in FOLHA_STUDY_CARDS
    )
    return f"""
<section class="signal-panel">
  <div class="section-heading">
    <span class="eyebrow">Índice de estudo</span>
    <h2>Capítulos trabalhistas-tributários</h2>
    <p>A trilha de Folha/CLT agora fica restrita a vínculo, rubrica, custeio previdenciário, FGTS, eSocial, DCTFWeb, EFD-Reinf, FAP/RAT, retenção e CPRB.</p>
  </div>
  <div class="signal-grid">{cards}</div>
</section>
"""


def render_law_chapters(chapters: list[dict], title: str = "Lei em tela", intro: str = "") -> str:
    if not chapters:
        return ""
    rendered = []
    for chapter in chapters:
        reading = CHAPTER_READING.get(chapter.get("id", ""), {
            "lead": "Leia o texto legal antes de aplicar qualquer conclusao operacional.",
            "application": "Converta a regra em documento, memoria de calculo e prova.",
        })
        passages = []
        for passage in chapter.get("passages", [])[:3]:
            passages.append(
                '<blockquote class="law-quote">'
                f'<p>{escape(passage.get("text", ""))}</p>'
                f'<cite>{escape(passage.get("source", ""))}</cite>'
                '</blockquote>'
            )
        search_text = chapter.get("title", "") + " " + " ".join(p.get("source", "") for p in chapter.get("passages", []))
        rendered.append(f"""
<article class="law-chapter searchable-card" data-search="{escape(search_text)}">
  <h3>{escape(chapter.get("title", "Capitulo legal"))}</h3>
  <p>{escape(reading["lead"])}</p>
  <div class="law-quotes">{''.join(passages)}</div>
  <div class="chapter-application">
    <strong>Leitura pratica</strong>
    <span>{escape(reading["application"])}</span>
  </div>
</article>
""")
    intro_html = f"<p>{escape(intro)}</p>" if intro else ""
    return f"""
<section class="legal-chapters">
  <div class="section-heading">
    <span class="eyebrow">Texto legal</span>
    <h2>{escape(title)}</h2>
    {intro_html}
  </div>
  <div class="law-chapter-list">{''.join(rendered)}</div>
  <div class="department-grid">
    <article><strong>Fiscal</strong><span>Transforma a regra em cadastro, CST/CSOSN, CFOP, base, aliquota, cBenef e documento.</span></article>
    <article><strong>Contabil</strong><span>Leva o efeito para conta, custo, receita, provisao, credito, estorno e conciliacao.</span></article>
    <article><strong>Financeiro</strong><span>Controla vencimento, guia, retencao, caixa, compensacao e comprovante.</span></article>
    <article><strong>Juridico e auditoria</strong><span>Fecha a prova: lei, ato, XML, declaracao, contrato, memoria e risco de autuacao.</span></article>
  </div>
</section>
"""


def category_cards(docs: list[dict]) -> str:
    buckets: dict[str, dict] = {}
    for doc in docs:
        bucket = buckets.setdefault(
            doc.get("category", "OUTROS"),
            {"label": doc.get("category_label", "Outros atos"), "count": 0, "chars": 0, "signals": CounterLike()},
        )
        bucket["count"] += 1
        bucket["chars"] += int(doc.get("chars", 0))
        bucket["signals"].update(doc.get("signals", {}))
    if not buckets:
        return ""
    cards = []
    for category, bucket in sorted(buckets.items(), key=lambda item: item[0]):
        top = dict(bucket["signals"].most_common(4))
        cards.append(
            f'<article class="matrix-card searchable-card" data-search="{escape(category + " " + bucket["label"])}">'
            f'<h3>{escape(bucket["label"])}</h3>'
            f'<p>{fmt_num(bucket["count"])} atos normativos, {fmt_num(bucket["chars"])} caracteres de texto legal tratado.</p>'
            f'<div class="signals-inline">{signal_badges(top, 4)}</div>'
            "</article>"
        )
    return '<section class="matrix-section"><h2>Categorias legais publicadas</h2><div class="matrix-grid">' + "".join(cards) + "</div></section>"


class CounterLike(dict):
    def update(self, other: dict) -> None:  # type: ignore[override]
        for key, value in other.items():
            self[key] = self.get(key, 0) + int(value)

    def most_common(self, limit: int) -> list[tuple[str, int]]:
        return sorted(self.items(), key=lambda item: item[1], reverse=True)[:limit]


def source_list(sources: list[dict[str, str]]) -> str:
    items = []
    for source in sources:
        items.append(
            f'<li><a href="{escape(source["url"])}" target="_blank" rel="noopener">'
            f'{escape(source["label"])}</a></li>'
        )
    return "<ul class=\"source-list\">" + "".join(items) + "</ul>"


def source_badge(topic: dict) -> str:
    return (
        '<div class="source-badge">'
        f'<span>Base normativa desta pagina</span>'
        f'<strong>Atualizada em {escape(topic["data_conferencia"])}</strong>'
        "</div>"
    )


def inventory_badge(label: str, compiled_on: str, verified_on: str) -> str:
    return (
        '<div class="source-badge">'
        f'<span>Texto legal em tela</span>'
        f'<strong>{escape(label)}</strong>'
        "</div>"
    )


def docs_table(docs: list[dict], title: str, intro: str, federal: bool = False) -> str:
    if not docs:
        return f"""
<section class="content-block">
  <h2>{escape(title)}</h2>
  <p>{escape(intro)}</p>
  <p>Esta pagina permanece aberta para receber texto legal publico, vigente e contextualizado antes de qualquer conclusao tributaria.</p>
</section>
"""
    rows = []
    for doc in sorted(docs, key=lambda item: (item.get("category_label") or item.get("theme") or "", item.get("title") or item.get("file") or "")):
        if federal:
            first = escape(doc.get("title") or doc.get("file", ""))
            second = escape(FEDERAL_THEME_LABELS.get(doc.get("theme", ""), doc.get("theme", "")))
            source = render_doc_source(doc)
        else:
            first = escape(doc.get("category_label", doc.get("category", "")))
            sources = doc.get("source_documents", [])[:3]
            second = escape("; ".join(sources) if sources else doc.get("file", ""))
            source = escape(doc.get("file", ""))
        file_hint = "" if federal else f"<span>{escape(doc.get('file', ''))}</span>"
        rows.append(
            "<tr>"
            f"<td><strong>{first}</strong>{file_hint}</td>"
            f"<td>{second}</td>"
            f"<td><div class=\"signals-inline\">{signal_badges(doc.get('signals', {}), 4)}</div></td>"
            f"<td>{fmt_num(doc.get('chars', 0))}</td>"
            f"<td>{source}</td>"
            "</tr>"
        )
    return f"""
<section class="content-block inventory-table">
  <h2>{escape(title)}</h2>
  <p>{escape(intro)}</p>
  <div class="doc-table-wrap">
    <table class="doc-table">
      <thead>
        <tr>
          <th>Documento</th>
          <th>{'Tema' if federal else 'Trilha de fonte'}</th>
          <th>Sinais</th>
          <th>Tamanho</th>
          <th>Fonte publica</th>
        </tr>
      </thead>
      <tbody>{''.join(rows)}</tbody>
    </table>
  </div>
</section>
"""


def layout(path: str, title: str, subtitle: str, body: str, active: str = "") -> str:
    prefix = rel_prefix(path)
    canonical = canonical_url(path)
    social_title = f"{title} | RJC Assessoria"
    nav = [
        ("index.html", "Inicio", "home"),
        ("estados/index.html", "Estados", "estados"),
        ("confaz/index.html", "CONFAZ", "confaz"),
        ("federal/index.html", "Federal", "federal"),
        ("beneficios/index.html", "Beneficios", "beneficios"),
        ("auditoria/index.html", "Auditoria", "auditoria"),
        ("folha-clt/index.html", "Folha e CLT", "folha"),
        ("biblioteca/index.html", "Biblioteca", "biblioteca")
    ]
    nav_html = "".join(
        f'<a href="{prefix}{href}" class="{ "active" if key == active else "" }">{label}</a>'
        for href, label, key in nav
    )
    study_links = [
        ("federal/legislacao/index.html", "Leis federais"),
        ("estados/index.html", "ICMS por Estado"),
        ("beneficios/index.html", "Beneficios/NCM"),
        ("produto.html", "Produto/NCM"),
        ("beneficios/setores.html", "Beneficios por setor"),
        ("beneficios/reforma.html", "Beneficios IBS/CBS"),
        ("auditoria/index.html", "Auditoria"),
        ("federal/legislacao/reforma-tributaria/index.html", "Reforma"),
        ("federal/legislacao/reforma-tributaria/cst-cclasstrib-ibs-cbs.html", "CST/cClassTrib"),
        ("confaz/ultimos-5-anos.html", "CONFAZ 5 anos"),
    ]
    study_html = "".join(
        f'<a href="{prefix}{href}">{label}</a>'
        for href, label in study_links
    )
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escape(social_title)}</title>
  <meta name="description" content="{escape(subtitle)}">
  <meta name="robots" content="index,follow,max-snippet:-1,max-image-preview:large,max-video-preview:-1">
  <link rel="canonical" href="{escape(canonical, quote=True)}">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="Portal RJC Tributario Aberto">
  <meta property="og:title" content="{escape(social_title)}">
  <meta property="og:description" content="{escape(subtitle)}">
  <meta property="og:url" content="{escape(canonical, quote=True)}">
  <link rel="icon" href="{prefix}ico.png">
  <link rel="stylesheet" href="{prefix}assets/portal-tributario.css">
  <script defer src="{prefix}assets/portal-search.js"></script>
  <script defer src="{prefix}assets/portal-tributario.js"></script>
</head>
<body>
  <header class="site-header">
    <div class="topbar">
      <a class="brand" href="{prefix}index.html" aria-label="Portal RJC Tributario Aberto">
        <img src="{prefix}logo.png" alt="RJC Assessoria">
        <span>
          <strong>RJC Tributario Aberto</strong>
          <small>A Arte de Registrar o Patrimonio</small>
        </span>
      </a>
      <nav class="primary-nav" aria-label="Navegacao principal">
        {nav_html}
      </nav>
    </div>
    <div class="searchbar" role="search">
      <label for="globalSearch">Buscar em todo o portal</label>
      <input id="globalSearch" type="search" placeholder="Busca semântica: arroz, benefício fiscal arroz, NCM, cBenef, CST, Estado, regime ou artigo">
      <div id="searchResults" class="search-results" aria-live="polite"></div>
    </div>
    <nav class="study-strip" aria-label="Trilhas rápidas de estudo">
      <strong>Trilhas</strong>
      <div>{study_html}</div>
    </nav>
  </header>
  <main>
    {body}
  </main>
  <footer class="site-footer">
    <div>
      <strong>Portal RJC Tributario Aberto</strong>
      <p>Conteudo educativo pautado em legislacao oficial. Nao substitui parecer individual para operacao concreta.</p>
    </div>
    <div>
      <span>Atualizacao editorial: {EDITORIAL_UPDATED_ON}</span>
      <a href="{prefix}biblioteca/index.html#metodo">Metodo e fontes</a>
    </div>
  </footer>
</body>
</html>
"""


def hero(title: str, subtitle: str, eyebrow: str = "Base legal aberta") -> str:
    return f"""
<section class="hero-panel">
  <div>
    <span class="eyebrow">{escape(eyebrow)}</span>
    <h1>{escape(title)}</h1>
    <p>{escape(subtitle)}</p>
  </div>
  <aside class="hero-proof">
    <strong>Regra editorial</strong>
    <p>Lei em tela. Depois a leitura pratica.</p>
  </aside>
</section>
"""


def card_grid(cards: list[str], class_name: str = "") -> str:
    return f'<div class="card-grid {escape(class_name)}">' + "".join(cards) + "</div>"


def topic_card(topic: dict, prefix: str = "", extra_class: str = "") -> str:
    bases = ", ".join(topic.get("base_legal", [])[:3])
    return f"""
<a class="portal-card {escape(extra_class)} searchable-card" href="{escape(prefix + topic["path"])}"
   data-search="{escape(topic["titulo"] + " " + topic["tema"] + " " + topic["resumo"] + " " + bases)}">
  <span class="card-kicker">{escape(topic["jurisdicao"])} · {escape(topic["tipo"])}</span>
  <h3>{escape(topic["titulo"])}</h3>
  <p>{escape(topic["resumo"])}</p>
  <small>Abrir capitulo</small>
</a>
"""


def render_sections(topic: dict) -> str:
    blocks = []
    for section in topic.get("sections", []):
        paragraphs = "".join(f"<p>{escape(text)}</p>" for text in section.get("body", []))
        blocks.append(f'<section class="content-block"><h2>{escape(section["heading"])}</h2>{paragraphs}</section>')
    return "".join(blocks)


MATRIX_LABELS = [
    ("o_que_e", "O que e"),
    ("base_legal", "Base legal"),
    ("quem_pode_usar", "Quem pode usar"),
    ("condicoes", "Condicoes"),
    ("vedacoes", "Vedacoes"),
    ("como_aparece_no_documento", "Como aparece no documento"),
    ("prova_necessaria", "Prova necessaria"),
    ("risco_comum", "Risco comum"),
    ("fonte_oficial", "Fonte publica")
]


def render_matrix(topic: dict) -> str:
    cards = []
    for item in topic.get("matriz", []):
        rows = []
        for key, label in MATRIX_LABELS:
            rows.append(f"<dt>{label}</dt><dd>{escape(item.get(key, ''))}</dd>")
        cards.append(
            f'<article class="matrix-card searchable-card" data-search="{escape(item["titulo"] + " " + " ".join(item.values()))}">'
            f'<h3>{escape(item["titulo"])}</h3><dl>{"".join(rows)}</dl></article>'
        )
    if not cards:
        return ""
    return '<section class="matrix-section"><h2>Matriz legal de aplicacao</h2><div class="matrix-grid">' + "".join(cards) + "</div></section>"


def related_links(topic: dict) -> str:
    links = topic.get("links_relacionados", [])
    if not links:
        return ""
    html = "".join(f'<a href="{escape(link["href"])}">{escape(link["label"])}</a>' for link in links)
    return f'<section class="continuity"><h2>Continuar a leitura</h2><div>{html}</div></section>'


def master_bundle() -> dict:
    return {
        "taxonomy": load_json(MASTER_TAXONOMY, {"benefit_groups": [], "federal_requirements": []}),
        "coverage": load_json(MASTER_COVERAGE, {"summary": {}, "federal": [], "states": []}),
        "benefits": load_json(BENEFITS_CROSSWALK, {"summary": {}, "entries": []}),
        "confaz": load_json(CONFAZ_5Y, {"years": [], "families": {}}),
    }


def status_badge(status: str) -> str:
    label = (status or "sem_status").replace("_", " ")
    klass = "review-pill"
    if status in {"publicado_v1", "aprovado_v1"}:
        klass += " approved"
    elif status.startswith("revisado"):
        klass += " warning"
    elif status in {"a_estruturar", "sem_status"}:
        klass += " danger"
    return f'<span class="{klass}">{escape(label)}</span>'


def source_audit_index_page(data: dict) -> str:
    master = master_bundle()
    coverage = master["coverage"]
    federal_rows = []
    for item in coverage.get("federal", []):
        files = [f for f in item.get("expected_files", []) if f.get("available")]
        file_text = ", ".join(f["file"] for f in files) or "sem arquivo local"
        federal_rows.append(f"""
<article class="portal-card searchable-card" data-search="{escape(item.get('title', '') + ' ' + item.get('minimum', '') + ' ' + file_text)}">
  <span class="card-kicker">{status_badge(item.get('status', ''))}</span>
  <h3>{escape(item.get('title', ''))}</h3>
  <p>{escape(item.get('minimum', ''))}</p>
  <small>{escape(file_text)}</small>
</article>
""")
    state_rows = []
    for item in coverage.get("states", []):
        state_rows.append(f"""
<tr>
  <td><a href="../{escape(state_href(item.get('uf', '')))}">{escape(item.get('uf', ''))}</a></td>
  <td>{escape(item.get('name', ''))}</td>
  <td>{status_badge(item.get('status', ''))}</td>
  <td>{fmt_num(item.get('document_count', 0))}</td>
  <td>{escape(', '.join(item.get('flags', [])[:3]) or 'sem alerta automatizado')}</td>
</tr>
""")
    summary = coverage.get("summary", {})
    body = f"""
{hero("Auditoria mestre do portal", "Cobertura, lacunas, status editorial e fila de curadoria para transformar o portal em base tributaria nacional confiavel.", "Governanca")}
<section class="method-strip">
  <div><strong>{fmt_num(summary.get('registered_sources', 0))}</strong><span>fontes registradas</span></div>
  <div><strong>{fmt_num(summary.get('federal_requirements', 0))}</strong><span>temas federais essenciais</span></div>
  <div><strong>{fmt_num(summary.get('states_deep', 0))}</strong><span>Estados profundos</span></div>
  <div><strong>{fmt_num(summary.get('states_reviewed_with_pendencies', 0))}</strong><span>Estados revisados sem aprovação profunda</span></div>
</section>
<section class="content-block">
  <h2>Como ler esta auditoria</h2>
  <p>Esta pagina nao e parecer. Ela mostra onde o portal ja possui lei em tela, onde existe fonte local pronta para virar capitulo, e onde o conteudo foi revisado mas ainda deve permanecer sem aprovacao profunda.</p>
  <p>Uma conclusao tributaria so sai do estado de revisao quando o dispositivo legal, a fonte oficial, a vigencia, o documento de prova e a leitura contraditoria estiverem amarrados.</p>
</section>
<section class="section-wrap">
  <div class="section-heading">
    <span class="eyebrow">Federal</span>
    <h2>Cobertura dos temas essenciais</h2>
  </div>
  {card_grid(federal_rows)}
</section>
<section class="content-block inventory-table">
  <h2>Estados e status editorial</h2>
  <div class="doc-table-wrap">
    <table class="doc-table">
      <thead><tr><th>UF</th><th>Estado</th><th>Status</th><th>Docs</th><th>Alertas</th></tr></thead>
      <tbody>{''.join(state_rows)}</tbody>
    </table>
  </div>
</section>
<section class="continuity">
  <h2>Continuar a auditoria</h2>
  <div>
    <a href="../beneficios/index.html">Matriz nacional de beneficios</a>
    <a href="../confaz/ultimos-5-anos.html">CONFAZ dos ultimos 5 anos</a>
    <a href="../estados/auditoria-fontes.html">Auditoria fonte a fonte dos Estados</a>
    <a href="../federal/acervo.html">Acervo federal</a>
  </div>
</section>
"""
    return layout("auditoria/index.html", "Auditoria mestre", "Cobertura, lacunas e status editorial do portal.", body, "auditoria")


def legacy_benefits_crosswalk_page(data: dict) -> str:
    master = master_bundle()
    benefits = master["benefits"]
    entries = benefits.get("entries", [])
    grouped: dict[str, list[dict]] = {}
    for item in entries:
        grouped.setdefault(item.get("benefit_group", "A classificar"), []).append(item)
    groups = []
    for group_name, items in sorted(grouped.items()):
        rows = []
        for item in items[:30]:
            uf = item.get("jurisdiction", "")
            href = f"../estados/{uf.lower()}.html" if len(uf) == 2 else "../federal/index.html"
            rows.append(f"""
<article class="benefit-cross-card searchable-card" data-search="{escape(search_value_text(item))}">
  <span class="card-kicker">{escape(item.get('jurisdiction', ''))} · {escape(item.get('tax', ''))} · {status_badge(item.get('evidence_status', ''))}</span>
  <h3>{escape(item.get('name', item.get('jurisdiction', '')))}</h3>
  <p>{escape(item.get('legal_description', '')[:420])}</p>
  <dl>
    <dt>NCM/CEST</dt><dd>{escape(item.get('ncm_cest', 'nao indicado no trecho'))}</dd>
    <dt>Tipo</dt><dd>{escape(item.get('benefit_type', 'tratamento tributario especifico'))}</dd>
    <dt>Prova</dt><dd>{escape(item.get('proof_required', ''))}</dd>
    <dt>Risco</dt><dd>{escape(item.get('risk', ''))}</dd>
  </dl>
  <a href="{escape(href)}">abrir origem</a>
</article>
""")
        groups.append(f"""
<section class="section-wrap" id="{escape(slug(group_name))}">
  <div class="section-heading">
    <span class="eyebrow">Grupo de beneficio</span>
    <h2>{escape(group_name)}</h2>
    <p>{fmt_num(len(items))} ocorrencias organizadas para cruzamento por UF, tributo, NCM/CEST, documento e prova.</p>
  </div>
  <div class="benefit-cross-grid">{''.join(rows)}</div>
</section>
""")
    summary = benefits.get("summary", {})
    body = f"""
{hero("Matriz nacional de beneficios fiscais", "Cruzamento inicial por UF, tributo, setor, tipo de tratamento, NCM/CEST, documento de prova e status editorial.", "Beneficios e NCM")}
<section class="law-ledger">
  <div>
    <h2>Regra de uso</h2>
    <p>A matriz aponta caminhos de estudo. Ela nao autoriza aplicar beneficio sem ler o artigo, a vigencia, as condicoes, as vedacoes e o documento fiscal exigido.</p>
  </div>
  <div>
    <h2>Validacao tripla</h2>
    <p>Antes de cruzar NCM, beneficio e operacao: confirme texto legal direto, fonte/vigencia oficial e leitura contraditoria de escopo, revogacao, condicao e prova.</p>
  </div>
  <div>
    <h2>Entradas</h2>
    <p>{fmt_num(summary.get('entries', 0))} entradas, {fmt_num(summary.get('published_entries', 0))} em UFs/temas profundos e {fmt_num(summary.get('waiting_review_entries', 0))} aguardando revisao.</p>
  </div>
</section>
{''.join(groups)}
<section class="continuity">
  <h2>Continuar a leitura</h2>
  <div>
    <a href="ncm.html">Lista NCM x beneficios</a>
    <a href="../auditoria/index.html">Auditoria mestre</a>
    <a href="../confaz/ultimos-5-anos.html">CONFAZ 5 anos</a>
    <a href="../federal/pis-cofins.html">PIS/Cofins</a>
    <a href="../painel-fiscal/index.html">Painel fiscal</a>
  </div>
</section>
"""
    return layout("beneficios/index.html", "Matriz nacional de beneficios fiscais", "Beneficios por UF, tributo, setor, NCM e prova.", body, "beneficios")


def ncm_benefits_page(data: dict) -> str:
    payload = load_json(NCM_BENEFITS_INDEX, {"summary": {}, "rows": []})
    summary = payload.get("summary", {})
    rows = payload.get("rows", [])
    table_rows = []
    for item in rows:
        search_text = " ".join(
            search_value_text(item.get(key, ""))
            for key in (
                "ncm",
                "ncm_digits",
                "origin",
                "jurisdiction",
                "tax",
                "benefit_group",
                "benefit_type",
                "scope_summary",
                "goods_or_services",
                "product_or_operation",
                "conditions",
                "prohibitions",
                "legal_basis",
                "source_title",
                "legal_excerpt",
            )
        )
        table_rows.append(f"""
<tr id="{escape(item.get('id', ''))}" class="searchable-card" data-search="{escape(search_text)}">
  <td><strong>{escape(item.get('ncm', ''))}</strong><span>{escape(item.get('ncm_level', 'NCM'))}</span></td>
  <td><strong>{escape(item.get('jurisdiction', ''))}</strong><span>{escape(item.get('origin', ''))} · {escape(item.get('tax', ''))}</span></td>
  <td><strong>{escape(item.get('benefit_type', ''))}</strong><span>{escape(item.get('benefit_group', ''))}</span></td>
  <td>{escape(item.get('scope_summary') or item.get('product_or_operation', ''))}</td>
  <td>{escape(item.get('conditions', ''))}</td>
  <td>{escape(item.get('legal_basis', ''))}<br><a href="{escape(item.get('official_url', ''))}" target="_blank" rel="noopener">fonte legal</a></td>
  <td>{escape(item.get('legal_excerpt', ''))}</td>
</tr>
""")
    origins = summary.get("origins", {})
    origin_text = " · ".join(f"{escape(key)}: {fmt_num(value)}" for key, value in origins.items())
    body = f"""
{hero("Lista NCM x beneficios fiscais", "Relação operacional de NCM/TIPI com benefício, UF/Federal/CONFAZ, condição, base legal, prova e fonte.", "NCM e beneficios")}
<section class="law-ledger">
  <div>
    <h2>Registros</h2>
    <p>{fmt_num(summary.get('rows', 0))} linhas NCM x benefício, {fmt_num(summary.get('unique_ncm', 0))} NCM únicos e {fmt_num(summary.get('jurisdictions', 0))} jurisdições com NCM extraído em texto legal.</p>
  </div>
  <div>
    <h2>Origem</h2>
    <p>{origin_text}</p>
  </div>
  <div>
    <h2>Exportar</h2>
    <p><a href="../data/ncm_benefits_index.csv">CSV</a> · <a href="../data/ncm_benefits_index.json">JSON</a></p>
  </div>
</section>
<section class="content-block">
  <h2>Como usar a lista</h2>
  <p>Esta é a base técnica ampla de NCM x benefícios. Para leitura humana, comece pelos painéis temáticos e use esta página como conferência/exportação: a linha só entra quando o código aparece em trecho legal com tratamento tributário e contexto NCM/TIPI.</p>
  <p><strong>Atalho seguro:</strong> para PIS/Cofins por NCM, use a <a href="../federal/legislacao/pis-cofins/ncm.html#consulta-pis-cofins-ncm">consulta guiada por cards</a>. Ela separa tratamento, setor, vigência, ato oficial, prova e risco antes de mostrar a tabela técnica.</p>
</section>
<section class="content-block inventory-table">
  <h2>Base técnica NCM x benefícios</h2>
  <p>Fechada por padrão para não transformar a leitura humana em uma planilha estreita. Abra somente para auditoria, exportação ou conferência pontual.</p>
  <details class="ncm-audit-table-details">
    <summary>Abrir tabela técnica com {fmt_num(summary.get('rows', 0))} linhas</summary>
    <div class="doc-table-wrap">
    <table class="doc-table ncm-benefits-table">
      <thead><tr><th>NCM</th><th>Origem</th><th>Benefício</th><th>Produto/operação</th><th>Condição</th><th>Base legal</th><th>Trecho</th></tr></thead>
      <tbody>{''.join(table_rows)}</tbody>
    </table>
    </div>
  </details>
</section>
<section class="continuity">
  <h2>Continuar a leitura</h2>
  <div>
    <a href="index.html">Matriz nacional de benefícios</a>
    <a href="../confaz/ultimos-5-anos.html">CONFAZ</a>
    <a href="../federal/index.html">Federal</a>
    <a href="../estados/index.html">Estados</a>
  </div>
</section>
"""
    return layout("beneficios/ncm.html", "Lista NCM x beneficios fiscais", "NCM por beneficio fiscal, UF, Federal e CONFAZ.", body, "beneficios")


PIS_COFINS_TREATMENT_LABELS = {
    "aliquota_zero": "Aliquota zero",
    "monofasico": "Monofasico",
    "credito_presumido": "Credito presumido",
    "suspensao": "Suspensao",
    "isencao": "Isencao",
    "tratamento_especifico": "Tratamento especifico",
    "coeficiente_reducao": "Coeficiente/reducao",
}


def pis_cofins_ncm_public_rows() -> list[dict]:
    return [row for row in load_ndjson(PIS_COFINS_NCM) if row.get("publishable") is True]


def pis_cofins_ncm_summary(rows: list[dict]) -> dict:
    payload = load_json(PIS_COFINS_NCM_INDEX, {"summary": {}})
    summary = payload.get("summary", {}) if isinstance(payload, dict) else {}
    if summary:
        return summary
    return {
        "published_rows": len(rows),
        "unique_ncm": len({str(row.get("ncm", {}).get("digitos", "")) for row in rows}),
        "sources_checked": len({row.get("source_id", "") for row in rows}),
        "quarantine_rows": 0,
        "by_treatment": dict(Counter(row.get("tratamento", "sem_tratamento") for row in rows)),
        "by_sector": dict(Counter(row.get("setor", "sem_setor") for row in rows)),
        "by_source": dict(Counter(row.get("source_id", "sem_fonte") for row in rows)),
        "oldest_verificado_em": min((row.get("verificado_em", "") for row in rows if row.get("verificado_em")), default=""),
    }


def pis_value(value: object, fallback: str = "nao informado") -> str:
    if isinstance(value, list):
        text = "; ".join(str(part) for part in value if str(part).strip())
    elif isinstance(value, dict):
        text = "; ".join(f"{key}: {part}" for key, part in value.items() if str(part).strip())
    else:
        text = str(value or "")
    return text.strip() or fallback


def pis_trim(value: object, limit: int = 520) -> str:
    text = " ".join(pis_value(value, "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def pis_display_label(value: object) -> str:
    return str(value or "nao especificado").replace("_", " ")


def pis_ato_label(row: dict) -> str:
    ato = row.get("ato_oficial", {}) if isinstance(row.get("ato_oficial"), dict) else {}
    return f"{ato.get('tipo', '')} {ato.get('numero', '')}".strip() or "ato nao informado"


def pis_treatment_label(row_or_value: dict | str) -> str:
    treatment = row_or_value.get("tratamento", "") if isinstance(row_or_value, dict) else str(row_or_value or "")
    return PIS_COFINS_TREATMENT_LABELS.get(str(treatment), pis_display_label(treatment))


def pis_validity_label(row: dict) -> str:
    return (
        f"publicacao {row.get('publicacao')}; vigencia {row.get('inicio_vigencia')}; "
        f"eficacia {row.get('inicio_eficacia')}; fim {row.get('fim_vigencia') or 'sem fim indicado'}"
    )


def pis_operational_summary(row: dict) -> str:
    stored = pis_value(row.get("resumo_operacional"), "")
    if stored:
        return stored
    ncm = row.get("ncm", {}) if isinstance(row.get("ncm"), dict) else {}
    code = str(ncm.get("codigo", "")).strip()
    treatment = pis_treatment_label(row)
    setor = pis_display_label(row.get("setor"))
    operacao = pis_display_label(row.get("operacao"))
    ato = pis_ato_label(row)
    descricao = pis_trim(row.get("mercadoria_servico"), 260)
    return f"NCM {code}: {treatment} de PIS/Cofins em {setor}, operacao {operacao}, conforme {ato}. Recorte legal: {descricao}"


def pis_filter_options(rows: list[dict], key: str) -> list[tuple[str, str]]:
    values = sorted({str(row.get(key, "")).strip() for row in rows if str(row.get(key, "")).strip()})
    return [(value, pis_treatment_label(value) if key == "tratamento" else pis_display_label(value)) for value in values]


def pis_select(name: str, label: str, options: list[tuple[str, str]]) -> str:
    option_html = [f'<option value="">{escape(label)}</option>']
    option_html += [f'<option value="{escape(value)}">{escape(display)}</option>' for value, display in options]
    return f'<select aria-label="{escape(label)}" data-pis-filter="{escape(name)}">{"".join(option_html)}</select>'


def pis_ncm_search_text(row: dict) -> str:
    ato = row.get("ato_oficial", {}) if isinstance(row.get("ato_oficial"), dict) else {}
    ncm = row.get("ncm", {}) if isinstance(row.get("ncm"), dict) else {}
    parts = [
        row.get("id", ""),
        ncm.get("codigo", ""),
        ncm.get("digitos", ""),
        ncm.get("descricao_tipi", ""),
        row.get("mercadoria_servico", ""),
        row.get("setor", ""),
        row.get("aplicacao", ""),
        row.get("tratamento", ""),
        row.get("operacao", ""),
        row.get("etapa_cadeia", ""),
        row.get("status", ""),
        row.get("validity_status", ""),
        row.get("publicacao", ""),
        row.get("inicio_vigencia", ""),
        row.get("inicio_eficacia", ""),
        row.get("fim_vigencia", ""),
        row.get("condicoes", []),
        row.get("vedacoes", []),
        row.get("prova_documental", []),
        row.get("risco", ""),
        row.get("resumo_operacional", ""),
        row.get("pesquisa_texto", ""),
        pis_operational_summary(row),
        row.get("trecho_legal", ""),
        ato.get("tipo", ""),
        ato.get("numero", ""),
        ato.get("titulo", ""),
        ato.get("url", ""),
    ]
    return " ".join(pis_value(part, "") for part in parts if pis_value(part, ""))


def pis_cofins_ncm_landing_page(data: dict) -> str:
    rows = pis_cofins_ncm_public_rows()
    summary = pis_cofins_ncm_summary(rows)
    by_treatment = summary.get("by_treatment", {})
    by_sector = summary.get("by_sector", {})
    by_source = summary.get("by_source", {})

    treatment_cards = []
    for treatment, count in sorted(by_treatment.items(), key=lambda item: (-item[1], item[0])):
        label = PIS_COFINS_TREATMENT_LABELS.get(treatment, str(treatment).replace("_", " "))
        examples = sorted({
            row.get("ncm", {}).get("codigo", "")
            for row in rows
            if row.get("tratamento") == treatment and row.get("ncm", {}).get("codigo")
        })[:10]
        treatment_cards.append(f"""
<article class="portal-card searchable-card" data-search="{escape(treatment + ' ' + ' '.join(examples))}">
  <span class="card-kicker">PIS/Cofins</span>
  <h3>{escape(label)}</h3>
  <p>{fmt_num(count)} registros publicados. Exemplos NCM: {escape(', '.join(examples) or 'sem exemplo')}.</p>
  <small>Abra a consulta guiada e filtre por este tratamento</small>
</article>
""")

    sector_cards = []
    for sector, count in sorted(by_sector.items(), key=lambda item: (-item[1], item[0]))[:12]:
        sector_cards.append(f"""
<article class="matrix-card searchable-card" data-search="{escape(str(sector))}">
  <h3>{escape(str(sector).replace('_', ' '))}</h3>
  <p>{fmt_num(count)} linhas por NCM, aplicacao, etapa da cadeia, ato e prova documental.</p>
</article>
""")

    source_rows = []
    for source_id, count in sorted(by_source.items(), key=lambda item: (-item[1], item[0])):
        source_rows.append(f"<tr><td>{escape(str(source_id))}</td><td>{fmt_num(count)}</td></tr>")

    body = f"""
{hero("PIS/Cofins por NCM", "Base operacional de PIS/Pasep e Cofins por NCM, setor, aplicacao e tratamento diferenciado, com fonte primaria e envelope de vigencia.", "Federal")}
<section class="law-ledger">
  <div>
    <h2>Linhas publicadas</h2>
    <p>{fmt_num(summary.get('published_rows', 0))} linhas validadas e {fmt_num(summary.get('unique_ncm', 0))} NCM/codigos TIPI unicos. Verificado por card em {escape(str(summary.get('oldest_verificado_em') or 'a validar'))}.</p>
  </div>
  <div>
    <h2>Fontes conferidas</h2>
    <p>{fmt_num(summary.get('sources_checked', 0))} atos oficiais ou fontes de controle. {fmt_num(summary.get('quarantine_rows', 0))} candidatos ficaram fora do publico por falta de NCM, baixa confianca, historico sem publicacao ou papel nao dispositivo.</p>
  </div>
  <div>
    <h2>Regra de uso</h2>
    <p>NCM aponta caminho, nao decide sozinho. Antes de aplicar, leia artigo, etapa da cadeia, sujeito, vigencia, condicao, CST/EFD e documento fiscal.</p>
  </div>
</section>
<section class="content-block">
  <h2>O que esta seção resolve</h2>
  <p>Ela separa monofasico, aliquota zero, suspensao, isencao, credito presumido e outros tratamentos de PIS/Cofins quando a norma oficial traz NCM, TIPI, posicao, codigo ou capitulo em contexto de aplicacao.</p>
  <p><strong>Status de completude:</strong> base inicial em execucao. Os registros abaixo sao publicados porque passaram pelos gates locais; a cobertura total da legislacao ainda depende do inventario expandido descrito em <a href="../workflow.md">workflow.md</a> e no ledger da rodada.</p>
</section>
<section class="content-block pis-ncm-entry-panel">
  <div>
    <span class="eyebrow">Caminho recomendado</span>
    <h2>Consulta por NCM em cards, não em planilha estreita</h2>
    <p>Use a página operacional para pesquisar por NCM, descrição, setor, tratamento, ato oficial ou trecho legal. Cada resultado mostra primeiro o envelope de aplicação: condição, vigência, prova, risco e transição CBS.</p>
  </div>
  <div class="pis-ncm-entry-actions">
    <a href="legislacao/pis-cofins/ncm.html#consulta-pis-cofins-ncm">Abrir consulta pesquisável por NCM</a>
    <a href="../data/pis-cofins/ncm.ndjson">Baixar NDJSON para LLM</a>
  </div>
</section>
<section class="section-wrap">
  <div class="section-heading">
    <span class="eyebrow">Tratamentos</span>
    <h2>Pesquisar por aplicacao tributaria</h2>
    <p>Cada card mostra a família de tratamento e leva para a consulta pesquisável por NCM, descrição legal, setor, operação, etapa e ato.</p>
  </div>
  {card_grid(treatment_cards)}
</section>
<section class="matrix-section">
  <h2>Setores com registros</h2>
  <div class="matrix-grid">{''.join(sector_cards)}</div>
</section>
<section class="content-block inventory-table">
  <h2>Fontes com linhas publicadas</h2>
  <div class="doc-table-wrap">
    <table class="doc-table">
      <thead><tr><th>Fonte</th><th>Linhas</th></tr></thead>
      <tbody>{''.join(source_rows)}</tbody>
    </table>
  </div>
</section>
<section class="continuity">
  <h2>Abrir base operacional</h2>
  <div>
    <a href="legislacao/pis-cofins/ncm.html#consulta-pis-cofins-ncm">Consulta guiada por NCM</a>
    <a href="../data/pis-cofins/ncm.ndjson">NDJSON publico para LLM</a>
    <a href="../data/pis-cofins/ncm-index.json">Indice compacto JSON</a>
    <a href="pis-cofins.html">Voltar ao guia de PIS/Cofins</a>
  </div>
</section>
"""
    return layout("federal/pis-cofins-ncm.html", "PIS/Cofins por NCM", "NCM, setor e tratamento especifico de PIS/Cofins com fonte primaria.", body, "federal")


def pis_cofins_ncm_table_page(data: dict) -> str:
    rows = sorted(
        pis_cofins_ncm_public_rows(),
        key=lambda row: (
            str(row.get("ncm", {}).get("digitos", "")),
            str(row.get("tratamento", "")),
            str(row.get("source_id", "")),
            str(row.get("id", "")),
        ),
    )
    summary = pis_cofins_ncm_summary(rows)
    treatment_options = pis_filter_options(rows, "tratamento")
    sector_options = pis_filter_options(rows, "setor")
    status_options = pis_filter_options(rows, "status")
    source_options = sorted({(row.get("source_id", ""), pis_ato_label(row)) for row in rows if row.get("source_id")})

    treatment_summary = []
    for treatment, label in treatment_options:
        count = sum(1 for row in rows if row.get("tratamento") == treatment)
        examples = sorted({
            row.get("ncm", {}).get("codigo", "")
            for row in rows
            if row.get("tratamento") == treatment and row.get("ncm", {}).get("codigo")
        })[:7]
        treatment_summary.append(f"""
<button type="button" class="pis-ncm-preset" data-pis-preset="tratamento:{escape(treatment)}">
  <strong>{escape(label)}</strong>
  <span>{fmt_num(count)} registros · {escape(', '.join(examples))}</span>
</button>
""")

    source_summary = []
    for source_id, count in sorted(summary.get("by_source", {}).items(), key=lambda item: (-item[1], item[0])):
        sample = next((row for row in rows if row.get("source_id") == source_id), {})
        source_summary.append(f"""
<article class="matrix-card searchable-card" data-search="{escape(source_id + ' ' + pis_ato_label(sample))}">
  <h3>{escape(pis_ato_label(sample))}</h3>
  <p>{fmt_num(count)} registros publicados. Fonte: {escape(str(source_id))}.</p>
</article>
""")

    record_cards = []
    table_rows = []
    for row in rows:
        ncm = row.get("ncm", {}) if isinstance(row.get("ncm"), dict) else {}
        ato = row.get("ato_oficial", {}) if isinstance(row.get("ato_oficial"), dict) else {}
        vigencia = row.get("vigencia", {}) if isinstance(row.get("vigencia"), dict) else {}
        transition = row.get("transicao_cbs", {}) if isinstance(row.get("transicao_cbs"), dict) else {}
        leitura = row.get("leitura_humana", {}) if isinstance(row.get("leitura_humana"), dict) else {}
        treatment = row.get("tratamento", "")
        treatment_label = pis_treatment_label(row)
        validity = pis_validity_label(row)
        source_label = pis_ato_label(row)
        search_text = pis_ncm_search_text(row)
        operational_summary = pis_operational_summary(row)
        ncm_code = str(ncm.get("codigo", "")).strip()
        goods_summary = pis_trim(row.get("mercadoria_servico") or ncm.get("descricao_tipi") or operational_summary, 260)
        card_heading = f"NCM {ncm_code} - {treatment_label}" if ncm_code else treatment_label
        record_cards.append(f"""
<article id="card-{escape(str(row.get('id', '')))}"
         class="pis-ncm-record searchable-card"
         data-pis-result="card"
         data-search="{escape(search_text)}"
         data-tratamento="{escape(str(treatment))}"
         data-setor="{escape(str(row.get('setor', '')))}"
         data-status="{escape(str(row.get('status', '')))}"
         data-source="{escape(str(row.get('source_id', '')))}">
  <div class="pis-ncm-record-head">
    <div>
      <span class="card-kicker">{escape(pis_display_label(row.get('setor')))} · {escape(pis_display_label(row.get('operacao')))}</span>
      <h3>{escape(card_heading)}</h3>
      <p class="pis-ncm-record-summary">{escape(goods_summary)}</p>
    </div>
    <span class="pis-ncm-record-id">id {escape(str(row.get('id', '')))}</span>
  </div>
  <dl class="pis-ncm-facts">
    <div><dt>Setor/aplicacao</dt><dd>{escape(pis_display_label(row.get('setor')))} · {escape(pis_display_label(row.get('aplicacao')))}</dd></div>
    <div><dt>Operacao/etapa</dt><dd>{escape(pis_display_label(row.get('operacao')))} · {escape(pis_display_label(row.get('etapa_cadeia')))}</dd></div>
    <div><dt>Status/vigencia</dt><dd>{escape(str(row.get('status', '')))} · {escape(validity)}</dd></div>
    <div><dt>Ato oficial</dt><dd><a href="{escape(str(ato.get('url', '')))}" target="_blank" rel="noopener">{escape(source_label)}</a> · HTTP {escape(str(ato.get('http_status', '')))}</dd></div>
    <div><dt>Condicao</dt><dd>{escape(pis_value(row.get('condicoes')))}</dd></div>
    <div><dt>Prova</dt><dd>{escape(pis_value(row.get('prova_documental')))}</dd></div>
  </dl>
  <p class="pis-ncm-guardrail"><strong>Antes de aplicar:</strong> confirme produto/codigo, etapa da cadeia, regime da empresa, documento fiscal e EFD-Contribuicoes. NCM sozinho nao autoriza o tratamento.</p>
  <details class="pis-ncm-details">
    <summary>Ver trecho legal, vedacao, risco e transicao CBS</summary>
    <p><strong>Vedacao:</strong> {escape(pis_value(row.get('vedacoes')))}</p>
    <p><strong>Risco:</strong> {escape(str(row.get('risco', '')))}</p>
    <p><strong>Como validar:</strong> {escape(pis_value(leitura.get('como_validar')))}</p>
    <p><strong>Nao usar sem:</strong> {escape(pis_value(leitura.get('nao_usar_sem')))}</p>
    <p><strong>Transicao CBS:</strong> {escape(str(transition.get('status', '')))} · {escape(str(transition.get('referencia', '')))}</p>
    <p><strong>Trecho legal:</strong> {escape(pis_trim(row.get('trecho_legal'), 900))}</p>
  </details>
</article>
""")
        table_rows.append(f"""
<tr id="{escape(str(row.get('id', '')))}"
    class="searchable-card"
    data-pis-result="row"
    data-search="{escape(search_text)}"
    data-tratamento="{escape(str(treatment))}"
    data-setor="{escape(str(row.get('setor', '')))}"
    data-status="{escape(str(row.get('status', '')))}"
    data-source="{escape(str(row.get('source_id', '')))}">
  <td><strong>{escape(str(ncm.get('codigo', '')))}</strong><span>{escape(str(ncm.get('nivel', 'NCM')))} · {escape(str(ncm.get('status', '')))}</span></td>
  <td><strong>{escape(pis_trim(operational_summary, 260))}</strong><span>TIPI: {escape(str(ncm.get('descricao_tipi') or ncm.get('tipi_versao') or 'a validar'))}</span></td>
  <td><strong>{escape(pis_display_label(row.get('setor')))}</strong><span>{escape(pis_display_label(row.get('aplicacao')))} · etapa {escape(pis_display_label(row.get('etapa_cadeia')))}</span></td>
  <td><strong>{escape(treatment_label)}</strong><span>{escape(', '.join(row.get('tributos', [])))} · {escape(str(row.get('operacao', '')))}</span></td>
  <td><strong>{status_badge(str(row.get('status', '')))}</strong><span>{escape(validity)}</span><span>{escape('vigencia inline: ' + str(vigencia.get('status', '')))}</span></td>
  <td>{escape(pis_value(row.get('condicoes')))}<br><strong>Vedacao:</strong> {escape(pis_value(row.get('vedacoes')))}</td>
  <td>{escape(pis_value(row.get('prova_documental')))}<br><strong>Risco:</strong> {escape(str(row.get('risco', '')))}</td>
  <td><strong>{escape(source_label)}</strong><br><a href="{escape(str(ato.get('url', '')))}" target="_blank" rel="noopener">fonte oficial HTTP {escape(str(ato.get('http_status', '')))}</a><br><span>{escape(str(ato.get('titulo', '')))}</span></td>
  <td><strong>{escape(str(transition.get('status', '')))}</strong><br>{escape(str(transition.get('referencia', '')))}</td>
  <td>{escape(pis_trim(row.get('trecho_legal'), 620))}</td>
</tr>
""")
    body = f"""
{hero("Consulta PIS/Cofins por NCM", "Registros autodescritivos para pesquisa humana e por LLM: NCM, descricao legal, setor, aplicacao, tratamento, vigencia, ato, prova, risco e transicao CBS.", "PIS/Cofins")}
<section class="law-ledger">
  <div>
    <h2>Base publica</h2>
    <p>{fmt_num(summary.get('published_rows', len(rows)))} linhas publicadas e {fmt_num(summary.get('unique_ncm', 0))} NCM/codigos unicos.</p>
  </div>
  <div>
    <h2>Quarentena</h2>
    <p>{fmt_num(summary.get('quarantine_rows', 0))} candidatos ficaram isolados e nao entram em busca, sitemap, llms.txt ou manifest publico.</p>
  </div>
  <div>
    <h2>Advertencia fiscal</h2>
    <p>Use a busca para localizar o item, mas aplique somente apos conferir artigo, sujeito, etapa da cadeia, regime da empresa, documento fiscal e EFD-Contribuicoes.</p>
  </div>
</section>
<section class="content-block pis-ncm-howto">
  <h2>Como ler sem cair em atalho perigoso</h2>
  <div class="pis-ncm-steps">
    <article><strong>1. Comece pelo NCM</strong><span>Use codigo completo, posicao ou descricao. O resultado so aponta o caminho.</span></article>
    <article><strong>2. Leia o tratamento</strong><span>Monofasico, aliquota zero, credito presumido, suspensao e isencao tem efeitos diferentes.</span></article>
    <article><strong>3. Confira etapa e operacao</strong><span>Fabricante, importador, varejo, mercado interno ou importacao mudam a conclusao.</span></article>
    <article><strong>4. Feche com prova</strong><span>Ato oficial, vigencia, documento fiscal e EFD-Contribuicoes sustentam a aplicacao.</span></article>
  </div>
</section>
<section id="consulta-pis-cofins-ncm" class="content-block pis-ncm-explorer" data-pis-ncm-explorer data-total="{fmt_num(len(rows))}">
  <div class="section-heading compact">
    <span class="eyebrow">Consulta guiada</span>
    <h2>Pesquisar por NCM, descricao, setor, tratamento ou ato</h2>
    <p>Este campo filtra os cards operacionais desta pagina. A tabela tecnica fica fechada abaixo, para auditoria. Exemplos: <code>3004</code>, <code>8708</code>, <code>monofasico</code>, <code>farmaceutico</code>, <code>Lei 10.147</code>.</p>
  </div>
  <div class="pis-ncm-query">
    <label for="pisNcmSearch">Busca dentro da base PIS/Cofins por NCM</label>
    <input id="pisNcmSearch" type="search" placeholder="Digite NCM, descricao, tratamento, setor, ato ou trecho legal">
    <button type="button" data-pis-clear>Limpar</button>
  </div>
  <div class="pis-ncm-filters">
    {pis_select('tratamento', 'Todos os tratamentos', treatment_options)}
    {pis_select('setor', 'Todos os setores', sector_options)}
    {pis_select('status', 'Todos os status', status_options)}
    {pis_select('source', 'Todos os atos', source_options)}
  </div>
  <div class="pis-ncm-presets" aria-label="Filtros rapidos por tratamento">
    {''.join(treatment_summary)}
  </div>
  <p class="pis-ncm-count"><strong data-pis-count>{fmt_num(len(rows))}</strong> cards visiveis de {fmt_num(len(rows))} publicados.</p>
  <div class="pis-ncm-card-grid">
    {''.join(record_cards)}
  </div>
</section>
<section class="content-block inventory-table pis-ncm-audit-table">
  <h2>Tabela tecnica fechada para auditoria</h2>
  <p>Esta tabela repete os mesmos registros dos cards, mas em formato largo. Ela permanece fechada por padrao para nao virar a leitura principal do portal humano.</p>
  <details class="pis-ncm-table-details">
    <summary>Abrir tabela tecnica com todos os campos auditaveis</summary>
  <div class="doc-table-wrap">
    <table class="doc-table ncm-benefits-table">
      <thead><tr><th>NCM</th><th>Descricao legal</th><th>Setor/aplicacao</th><th>Tratamento</th><th>Status e vigencia</th><th>Condicoes</th><th>Prova e risco</th><th>Ato oficial</th><th>Transicao CBS</th><th>Trecho legal</th></tr></thead>
      <tbody>{''.join(table_rows)}</tbody>
    </table>
  </div>
  </details>
</section>
<section class="matrix-section">
  <h2>Fontes com linhas publicadas</h2>
  <div class="matrix-grid">{''.join(source_summary)}</div>
</section>
<section class="continuity">
  <h2>Continuar a leitura</h2>
  <div>
    <a href="../../pis-cofins-ncm.html">Voltar ao painel PIS/Cofins por NCM</a>
    <a href="../../../data/pis-cofins/ncm.ndjson">NDJSON publico</a>
    <a href="../../../data/pis-cofins/ncm-index.json">Indice compacto JSON</a>
    <a href="../../pis-cofins.html">Guia PIS/Cofins</a>
  </div>
</section>
"""
    return layout("federal/legislacao/pis-cofins/ncm.html", "Consulta PIS/Cofins por NCM", "Consulta pesquisavel de PIS/Cofins por NCM.", body, "federal")


def produtos_ncm_index() -> dict:
    payload = load_json(PRODUTOS_NCM_INDEX, {"summary": {}, "official_sources": [], "chapters": []})
    return payload if isinstance(payload, dict) else {"summary": {}, "official_sources": [], "chapters": []}


def produtos_ncm_products() -> list[dict]:
    payload = produtos_ncm_index()
    products: list[dict] = []
    for chapter in payload.get("chapters", []):
        chapter_path = ROOT / str(chapter.get("path", ""))
        chapter_payload = load_json(chapter_path, {"products": []})
        if isinstance(chapter_payload, dict):
            products.extend(item for item in chapter_payload.get("products", []) if isinstance(item, dict))
    return products


def produto_source_map() -> dict[str, dict]:
    return {
        str(source.get("id", "")): source
        for source in produtos_ncm_index().get("official_sources", [])
        if isinstance(source, dict)
    }


def produto_source_label(source: dict) -> str:
    return " ".join(part for part in [str(source.get("tipo", "")), str(source.get("numero", ""))] if part).strip() or str(source.get("id", "fonte"))


def produto_source_rows(sources: list[dict]) -> str:
    cards = []
    for source in sources:
        label = produto_source_label(source)
        live_sha = str(source.get("live_sha256") or "")
        snap_sha = str(source.get("snapshot_sha256") or "")
        cards.append(f"""
<article class="matrix-card product-source-card searchable-card" data-search="{escape(label + ' ' + str(source.get('titulo', '')) + ' ' + str(source.get('id', '')))}">
  <h3>{escape(label)}</h3>
  <p>{escape(str(source.get('titulo', '')))}</p>
  <dl>
    <dt>HTTP</dt><dd>{escape(str(source.get('http_status') or 'A_VALIDAR'))}</dd>
    <dt>URL</dt><dd><a href="{escape(str(source.get('url', '')))}" target="_blank" rel="noopener">fonte oficial</a></dd>
    <dt>SHA vivo</dt><dd><code>{escape(live_sha[:16] + '...' if live_sha else 'A_VALIDAR')}</code></dd>
    <dt>SHA snapshot</dt><dd><code>{escape(snap_sha[:16] + '...' if snap_sha else 'A_VALIDAR')}</code></dd>
  </dl>
</article>
""")
    return "".join(cards)


def produto_ncm_card(product: dict, source_map: dict[str, dict]) -> str:
    ncm_rows = []
    for ncm in product.get("ncm", []):
        search = " ".join(str(ncm.get(key, "")) for key in ("codigo", "digitos", "descricao", "pis_cofins", "ibs_cbs", "status"))
        ncm_rows.append(f"""
<article class="product-ncm-chip searchable-card" data-search="{escape(search)}">
  <strong>{escape(str(ncm.get('codigo', '')))}</strong>
  <span>{escape(str(ncm.get('descricao', '')))}</span>
  <small>{escape(str(ncm.get('status', '')))}</small>
  <p><b>PIS/Cofins:</b> {escape(str(ncm.get('pis_cofins', '')))}</p>
  <p><b>IBS/CBS:</b> {escape(str(ncm.get('ibs_cbs', '')))}</p>
</article>
""")
    reselo_rows = []
    for reselo in product.get("reselos", []):
        source_links = []
        for source_id in reselo.get("official_source_ids", []):
            source = source_map.get(str(source_id), {})
            source_links.append(
                f'<a href="{escape(str(source.get("url", "")))}" target="_blank" rel="noopener">{escape(produto_source_label(source) or str(source_id))}</a>'
            )
        reselo_rows.append(f"""
<article class="product-reselo-card searchable-card" data-search="{escape(str(reselo.get('assertion', '')) + ' ' + str(reselo.get('id', '')))}">
  <span class="card-kicker">{escape(', '.join(reselo.get('tributos', [])))} · {escape(str(reselo.get('status', '')))}</span>
  <h4>{escape(str(reselo.get('beneficio', 're-selo normativo')))}</h4>
  <p>{escape(str(reselo.get('assertion', '')))}</p>
  <dl class="product-validity-grid">
    <div><dt>Publicacao</dt><dd>{escape(str(reselo.get('publicacao', 'A_VALIDAR')))}</dd></div>
    <div><dt>Vigencia</dt><dd>{escape(str(reselo.get('inicio_vigencia', 'A_VALIDAR')))}</dd></div>
    <div><dt>Eficacia</dt><dd>{escape(str(reselo.get('inicio_eficacia', 'A_VALIDAR')))}</dd></div>
    <div><dt>Fim</dt><dd>{escape(str(reselo.get('fim_vigencia', 'A_VALIDAR')))}</dd></div>
  </dl>
  <p><strong>Transicao RT:</strong> {escape(str(reselo.get('transicao_rt', 'A_VALIDAR')))}</p>
  <p><strong>Fontes:</strong> {' · '.join(source_links) if source_links else 'A_VALIDAR'}</p>
</article>
""")
    why_not_green = "".join(f"<li>{escape(str(item))}</li>" for item in product.get("why_not_green", []))
    sources_text = " ".join(str(source.get("id", "")) for source in product.get("official_sources", []))
    data_search = " ".join([str(product.get("produto", "")), str(product.get("search_text", "")), sources_text])
    return f"""
<article id="{escape(str(product.get('id', '')))}"
         class="pis-ncm-record product-ncm-record searchable-card"
         data-product-result
         data-search="{escape(data_search)}">
  <div class="pis-ncm-record-head">
    <div>
      <span class="card-kicker">Produto/NCM · {escape(str(product.get('status', '')))}</span>
      <h3>{escape(str(product.get('produto', 'Produto')))} · Capitulo {escape(str(product.get('chapter', '')))}</h3>
      <p class="pis-ncm-record-summary">Seed de pesquisa com fonte oficial primaria e hashes Planalto. Nao e card de beneficio publishable enquanto o envelope temporal completo nao for extraido.</p>
    </div>
    <span class="pis-ncm-record-id">id {escape(str(product.get('id', '')))}</span>
  </div>
  <div class="product-ncm-grid">{''.join(ncm_rows)}</div>
  <div class="product-ncm-warning">
    <strong>Bloqueios para verde</strong>
    <ul>{why_not_green}</ul>
  </div>
  <div class="product-reselo-grid">{''.join(reselo_rows)}</div>
</article>
"""


def produto_ncm_page(data: dict) -> str:
    index = produtos_ncm_index()
    products = produtos_ncm_products()
    source_map = produto_source_map()
    sources = list(source_map.values())
    corpus = load_json(CORPUS_LOCAL_REGISTRY, {"summary": {}})
    uf_plan = load_json(UF_SEALING_PLAN, {"ufs": []})
    summary = index.get("summary", {})
    source_cards = produto_source_rows(sources)
    product_cards = "".join(produto_ncm_card(product, source_map) for product in products)
    uf_rows = []
    for row in uf_plan.get("ufs", []):
        if not isinstance(row, dict):
            continue
        uf_rows.append(f"""
<tr>
  <td><strong>{escape(str(row.get('uf', '')))}</strong></td>
  <td>{escape(str(row.get('corpus_selo', 'AMARELO_CORPUS_LOCAL')))}</td>
  <td>{escape(str(row.get('cbenef_status', 'A_VALIDAR_SEFAZ_VIVA')))}</td>
  <td>{escape('sim' if row.get('publicavel_verde') else 'nao')}</td>
  <td>{escape(str(row.get('note', '')))}</td>
</tr>
""")
    body = f"""
{hero("Consulta Produto/NCM", "Pesquisa operacional por produto e NCM com re-selo federal, hashes de fonte oficial, corpus estadual amarelo e cBenef A_VALIDAR quando faltar SEFAZ viva.", "Produto/NCM")}
<section class="law-ledger">
  <div>
    <h2>Produtos</h2>
    <p>{fmt_num(summary.get('products', len(products)))} produto(s) e {fmt_num(summary.get('ncm_codes', 0))} codigo(s) NCM no seed inicial. A primeira trilha e arroz.</p>
  </div>
  <div>
    <h2>Fontes oficiais</h2>
    <p>{fmt_num(summary.get('official_sources', len(sources)))} fontes Planalto carregadas; {fmt_num(summary.get('plantalto_sources_http_200', 0))} responderam HTTP 200 na importacao.</p>
  </div>
  <div>
    <h2>Regra #0</h2>
    <p>Fonte local ou keyword nunca vira verde. Sem URL oficial viva, vigencia completa e sha256, o item permanece A_VALIDAR.</p>
  </div>
</section>
<section class="content-block pis-ncm-entry-panel product-entry-panel">
  <div>
    <span class="eyebrow">Nova busca estruturada</span>
    <h2>Produto primeiro, beneficio depois</h2>
    <p>Esta tela pesquisa NCM, descricao, tributo e ato oficial. Ela mostra evidencias e pendencias; nao transforma o seed em beneficio vigente.</p>
  </div>
  <div class="pis-ncm-entry-actions">
    <a href="#consulta-produto-ncm">Pesquisar arroz / NCM 1006</a>
    <a href="data/produtos-ncm/index.json">Baixar indice Produto/NCM</a>
    <a href="data/corpus-local/legal_sources_registry.json">Ver corpus local amarelo</a>
  </div>
</section>
<section id="consulta-produto-ncm" class="content-block pis-ncm-explorer product-ncm-explorer" data-product-ncm-explorer>
  <div class="section-heading compact">
    <span class="eyebrow">Consulta guiada</span>
    <h2>Pesquisar por produto, NCM, tributo, ato ou status</h2>
    <p>Exemplos: <code>arroz</code>, <code>1006.20</code>, <code>10064000</code>, <code>LC 224</code>, <code>A_VALIDAR</code>.</p>
  </div>
  <div class="pis-ncm-query">
    <label for="productNcmSearch">Busca dentro da base Produto/NCM</label>
    <input id="productNcmSearch" type="search" placeholder="Digite produto, NCM, tributo, ato, hash ou status">
    <button type="button" data-product-clear>Limpar</button>
  </div>
  <p class="pis-ncm-count"><strong data-product-count>{fmt_num(len(products))}</strong> card(s) visiveis de {fmt_num(len(products))} seed(s).</p>
  <div class="pis-ncm-card-grid product-ncm-card-grid">{product_cards}</div>
</section>
<section class="matrix-section">
  <h2>Fontes federais re-seladas</h2>
  <div class="matrix-grid product-source-grid">{source_cards}</div>
</section>
<section class="content-block inventory-table product-uf-plan">
  <h2>Plano UF/cBenef: corpus local amarelo</h2>
  <p>O registro estadual importado tem {fmt_num(corpus.get('summary', {}).get('entries', 0))} entradas locais. Nenhuma UF nao-GO e publicada como verde para cBenef sem captura oficial SEFAZ viva.</p>
  <details class="pis-ncm-table-details">
    <summary>Abrir plano das 27 UFs</summary>
    <div class="doc-table-wrap">
      <table class="doc-table">
        <thead><tr><th>UF</th><th>Selo corpus</th><th>Status cBenef</th><th>Verde publicavel?</th><th>Nota</th></tr></thead>
        <tbody>{''.join(uf_rows)}</tbody>
      </table>
    </div>
  </details>
</section>
<section class="continuity">
  <h2>Dados para IA/LLM</h2>
  <div>
    <a href="data/produtos-ncm/index.json">Indice Produto/NCM</a>
    <a href="data/produtos-ncm/cap-10.json">Shard capitulo 10</a>
    <a href="data/reforma-tributaria/reselo-lc214-lc224-lc227.ndjson">Re-selo LC 214/224/227</a>
    <a href="data/corpus-local/uf-sealing-plan.json">Plano UF/cBenef</a>
  </div>
</section>
"""
    return layout("produto.html", "Consulta Produto/NCM", "Produto, NCM, re-selo federal, corpus local amarelo e pendencias A_VALIDAR.", body, "home")


def benefits_crosswalk_page(data: dict) -> str:
    master = master_bundle()
    benefits = master["benefits"]
    entries = [item for item in benefits.get("entries", []) if item.get("validation_status") == "validado"]

    def join_list(item: dict, key: str) -> str:
        value = item.get(key)
        if isinstance(value, list):
            return ", ".join(str(part) for part in value if str(part).strip())
        return str(value or "")

    def field(item: dict, key: str, fallback: str = "nao indicado no trecho") -> str:
        value = join_list(item, key)
        return value if value else fallback

    def source_href(item: dict) -> str:
        jurisdiction = str(item.get("jurisdiction", ""))
        if len(jurisdiction) == 2:
            return "../" + state_href(jurisdiction)
        return "../federal/index.html"

    grouped: dict[str, list[dict]] = {}
    for item in entries:
        grouped.setdefault(item.get("benefit_group", "Geral e operacao tributaria"), []).append(item)

    groups = []
    for group_name, items in sorted(grouped.items()):
        rows = []
        for item in items:
            href = source_href(item)
            scope = item.get("scope_summary") or item.get("product_or_operation", "")
            search_text = " ".join(
                search_value_text(item.get(key, ""))
                for key in (
                    "jurisdiction",
                    "tax",
                    "benefit_group",
                    "benefit_group_evidence",
                    "benefit_type",
                    "scope_summary",
                    "goods_or_services",
                    "product_or_operation",
                    "ncm",
                    "cest",
                    "cbenef",
                    "cst",
                    "cclasstrib",
                    "conditions",
                    "prohibitions",
                    "legal_basis",
                    "validity_status",
                )
            )
            rows.append(f"""
<article id="{escape(item.get('id', ''))}" class="benefit-cross-card searchable-card" data-search="{escape(search_text)}">
  <span class="card-kicker">{escape(str(item.get('jurisdiction', '')))} &middot; {escape(str(item.get('tax', '')))} &middot; validado &middot; confiança {escape(str(item.get('classification_confidence', 'media')))}</span>
  <h3>{escape(item.get('benefit_type', 'Tratamento tributario'))}</h3>
  <p><strong>Escopo publicado:</strong> {escape(scope)}</p>
  {benefit_contract_details(item)}
  <a href="{escape(href)}">abrir origem</a>
</article>
""")
        groups.append(f"""
<section class="section-wrap" id="{escape(slug(group_name))}">
  <div class="section-heading">
    <span class="eyebrow">Grupo de beneficio</span>
    <h2>{escape(group_name)}</h2>
    <p>{fmt_num(len(items))} registros com trecho legal, condicao de uso, prova e codigo fiscal quando a norma traz o codigo em tela.</p>
  </div>
  <div class="benefit-cross-grid">{''.join(rows)}</div>
</section>
""")

    summary = benefits.get("summary", {})
    body = f"""
{hero("Matriz nacional de beneficios fiscais", "Lista validada por UF, tributo, tratamento, NCM/TIPI, CEST, cBenef, CST, condicao, prova e trecho legal.", "Beneficios e NCM")}
<section class="law-ledger">
  <div>
    <h2>Regra de uso</h2>
    <p>A matriz leva ao dispositivo legal em tela. O beneficio so deve ser aplicado quando produto, operacao, destinatario, periodo, regime e documento fiscal couberem no texto normativo.</p>
  </div>
  <div>
    <h2>Como ler</h2>
    <p>Comece pelo grupo economico, confira o tipo de tratamento, leia a legislacao transcrita, depois valide codigos, condicoes, vedacoes, prova documental e reflexo no XML/EFD.</p>
  </div>
  <div>
    <h2>Entradas validadas</h2>
    <p>{fmt_num(summary.get('entries', 0))} entradas; {fmt_num(summary.get('with_ncm', 0))} com NCM/TIPI; {fmt_num(summary.get('with_cest', 0))} com CEST; {fmt_num(summary.get('with_cbenef', 0))} com cBenef; {fmt_num(summary.get('with_cst', 0))} com CST.</p>
  </div>
</section>
{''.join(groups)}
<section class="continuity">
  <h2>Continuar a leitura</h2>
  <div>
    <a href="setores.html">Benefícios por setor</a>
    <a href="uf.html">Benefícios por UF</a>
    <a href="reforma.html">Benefícios na Reforma</a>
    <a href="cesta-basica.html">Cesta básica e agro</a>
    <a href="regimes-diferenciados.html">Regimes diferenciados</a>
    <a href="documentos-de-prova.html">Documentos de prova</a>
    <a href="../auditoria/index.html">Auditoria mestre</a>
    <a href="../confaz/ultimos-5-anos.html">CONFAZ 5 anos</a>
    <a href="../federal/pis-cofins.html">PIS/Cofins</a>
    <a href="../painel-fiscal/index.html">Painel fiscal</a>
  </div>
</section>
"""
    return layout("beneficios/index.html", "Matriz nacional de beneficios fiscais", "Beneficios por UF, tributo, setor, NCM e prova.", body, "beneficios")


def benefit_value(item: dict, key: str, fallback: str = "nao indicado no trecho") -> str:
    value = item.get(key)
    if isinstance(value, list):
        text = ", ".join(str(part) for part in value if str(part).strip())
    elif isinstance(value, dict):
        text = " | ".join(str(part) for part in value.values() if str(part).strip())
    else:
        text = str(value or "")
    text = clean_search_fragment(text)
    return text if text else fallback


def benefit_act_label(item: dict) -> str:
    act = item.get("ato_oficial") or item.get("ato") or {}
    if isinstance(act, dict):
        title = str(act.get("titulo") or item.get("source_title") or "").strip()
        number = str(act.get("num") or "").strip()
        act_type = str(act.get("tipo") or "Ato oficial").strip()
        url = str(act.get("url") or item.get("official_url") or "").strip()
        label = " ".join(part for part in [act_type, number] if part).strip() or title or "Ato oficial"
        if title and title not in label:
            label = f"{label} - {title}"
        return f"{label} ({url})" if url else label
    return benefit_value(item, "source_title", "ato oficial indicado na fonte")


def benefit_proof_label(item: dict) -> str:
    proof = item.get("prova_documental")
    if isinstance(proof, dict):
        parts = [
            str(proof.get("descricao") or item.get("proof_required") or "").strip(),
            str(proof.get("url") or item.get("official_url") or "").strip(),
        ]
        return " | ".join(part for part in parts if part) or benefit_value(item, "proof_required")
    return benefit_value(item, "proof_required")


def benefit_contract_details(item: dict, compact: bool = False) -> str:
    status = benefit_value(item, "status", benefit_value(item, "validity_status", "a_revalidar"))
    end = benefit_value(item, "fim_vigencia", "sem fim declarado no registro")
    details = f"""
  <dl>
    <dt>Benefício</dt><dd>{escape(benefit_value(item, 'beneficio', benefit_value(item, 'benefit_type')))}</dd>
    <dt>Mercadoria/operação</dt><dd>{escape(benefit_value(item, 'mercadoria_servico', benefit_value(item, 'goods_or_services')))}</dd>
    <dt>Ente/UF</dt><dd>{escape(benefit_value(item, 'ente_uf', benefit_value(item, 'jurisdiction')))}</dd>
    <dt>Ato oficial</dt><dd>{escape(benefit_act_label(item))}</dd>
    <dt>Publicação</dt><dd>{escape(benefit_value(item, 'publicacao'))}</dd>
    <dt>Início vigência</dt><dd>{escape(benefit_value(item, 'inicio_vigencia'))}</dd>
    <dt>Início eficácia</dt><dd>{escape(benefit_value(item, 'inicio_eficacia'))}</dd>
    <dt>Fim vigência</dt><dd>{escape(end)}</dd>
    <dt>Vigência/status</dt><dd>{escape(benefit_value(item, 'validity_status', status))}</dd>
    <dt>Status</dt><dd>{escape(status)}</dd>
    <dt>Condição</dt><dd>{escape(benefit_value(item, 'condicao', benefit_value(item, 'conditions', 'ver texto legal')))}</dd>
    <dt>Vedação</dt><dd>{escape(benefit_value(item, 'prohibitions', 'ver texto legal'))}</dd>
    <dt>Prova</dt><dd>{escape(benefit_proof_label(item))}</dd>
    <dt>Transição RT-2026</dt><dd>{escape(benefit_value(item, 'transicao_rt', 'n/a'))}</dd>
    <dt>Risco</dt><dd>{escape(benefit_value(item, 'risco', benefit_value(item, 'risk')))}</dd>
    <dt>NCM/TIPI</dt><dd>{escape(benefit_value(item, 'ncm'))}</dd>
    <dt>CEST</dt><dd>{escape(benefit_value(item, 'cest'))}</dd>
    <dt>cBenef</dt><dd>{escape(benefit_value(item, 'cbenef'))}</dd>
    <dt>CST/cClassTrib</dt><dd>{escape(' / '.join(part for part in [benefit_value(item, 'cst', ''), benefit_value(item, 'cclasstrib', '')] if part) or 'nao indicado no trecho')}</dd>
    <dt>Base legal</dt><dd>{escape(benefit_value(item, 'legal_basis'))}</dd>
    <dt>Verificado em</dt><dd>{escape(benefit_value(item, 'verificado_em'))}</dd>
  </dl>
"""
    excerpt = "" if compact else f"""
  <details class="law-excerpt">
    <summary>legislacao em tela</summary>
    <p>{escape(item.get('legal_excerpt', ''))}</p>
    <a href="{escape(item.get('official_url', ''))}" target="_blank" rel="noopener">abrir fonte legal</a>
  </details>
"""
    return details + excerpt


def benefit_card(item: dict, current_path: str, compact: bool = False) -> str:
    source = "../federal/index.html"
    jurisdiction = str(item.get("jurisdiction", ""))
    if len(jurisdiction) == 2:
        source = "../" + state_href(jurisdiction)
    registry = rel_href(current_path, f"beneficios/index.html#{item.get('id', '')}")
    scope = item.get("scope_summary") or item.get("product_or_operation", "")
    details = benefit_contract_details(item, compact=compact)
    search_text = " ".join(str(item.get(key, "")) for key in (
        "jurisdiction", "tax", "benefit_group", "benefit_group_evidence", "benefit_type",
        "scope_summary", "goods_or_services", "product_or_operation",
        "ncm", "cest", "cbenef", "cst", "cclasstrib", "conditions", "legal_basis",
        "transition_status", "validity_status", "legal_nature", "status", "transicao_rt",
        "publicacao", "inicio_vigencia", "inicio_eficacia", "fim_vigencia", "verificado_em",
    ))
    return f"""
<article class="benefit-cross-card searchable-card" data-search="{escape(search_value_text(search_text))}">
  <span class="card-kicker">{escape(jurisdiction)} &middot; {escape(str(item.get('tax', '')))} &middot; {escape(str(item.get('transition_status', 'regra vigente')))} &middot; confiança {escape(str(item.get('classification_confidence', 'media')))}</span>
  <h3>{escape(item.get('benefit_type', 'Tratamento tributario'))}</h3>
  <p><strong>Escopo publicado:</strong> {escape(scope)}</p>
  <p><strong>{escape(item.get('legal_nature', 'tratamento tributario especifico'))}</strong></p>
  <p>{escape(item.get('conditions', ''))}</p>
  {details}
  <div class="mini-link-list">
    <a href="{escape(registry)}">abrir registro completo</a>
    <a href="{escape(source)}">abrir origem no portal</a>
  </div>
</article>
"""


def benefit_entries() -> list[dict]:
    benefits = master_bundle()["benefits"]
    return [item for item in benefits.get("entries", []) if item.get("validation_status") == "validado"]


def benefit_public_topic_text(item: dict, include_group: bool = False) -> str:
    keys = [
        "scope_summary",
        "goods_or_services",
        "product_or_operation",
        "operation",
        "benefit_type",
        "legal_nature",
        "tax",
        "ncm",
        "cest",
        "cbenef",
        "cst",
        "cclasstrib",
        "validity_status",
    ]
    if include_group:
        keys.extend(["benefit_group", "benefit_group_evidence"])
    return search_value_text({key: item.get(key, "") for key in keys})


def benefit_matches_terms(item: dict, needles: tuple[str, ...], include_group: bool = False) -> bool:
    text = normalize_search_text(benefit_public_topic_text(item, include_group=include_group))
    return any(normalize_search_text(needle) in text for needle in needles)


def topic_term_in_text(needle: str, text: str) -> bool:
    term = normalize_search_text(needle)
    if not term:
        return False
    if " " in term:
        return term in text
    return bool(re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", text))


def benefit_matches_cesta_basica(item: dict) -> bool:
    if item.get("benefit_group_id") == "energia-combustiveis-infraestrutura":
        return False
    text = normalize_search_text(benefit_public_topic_text(item, include_group=False))
    guard_text = normalize_search_text(search_value_text({
        "scope_summary": item.get("scope_summary", ""),
        "goods_or_services": item.get("goods_or_services", ""),
        "product_or_operation": item.get("product_or_operation", ""),
        "operation": item.get("operation", ""),
        "conditions": item.get("conditions", ""),
        "prohibitions": item.get("prohibitions", ""),
        "legal_excerpt": item.get("legal_excerpt", ""),
    }))
    food_needles = (
        "cesta",
        "alimento",
        "alimenticio",
        "horticola",
        "fruta",
        "ovo",
        "arroz",
        "feijao",
        "leite",
        "carne",
        "aves",
        "frango",
        "peixe",
        "trigo",
        "farinha",
        "pao",
        "alho",
        "tomate",
        "soja",
        "milho",
    )
    agro_needles = (
        "produtos agropecuarios",
        "produtor rural",
        "agricultor familiar",
        "cooperativa de produtores",
    )
    exclusion_needles = (
        "biodiesel",
        "biocombustivel",
        "diesel",
        "oleo diesel",
        "combustivel",
        "querosene",
        "gas natural",
        "gnv",
        "energia",
        "energia eletrica",
        "energia solar",
        "fotovoltaica",
        "microgeracao",
        "minigeracao",
        "hidreletrica",
        "pch",
        "alcool etilico hidratado combustivel",
        "alcool metilico",
        "metanol",
        "aehc",
        "etanol",
    )
    if any(topic_term_in_text(needle, guard_text) for needle in exclusion_needles):
        return False
    return any(topic_term_in_text(needle, text) for needle in food_needles) or any(topic_term_in_text(needle, text) for needle in agro_needles)


def benefit_special_page(
    path: str,
    title: str,
    subtitle: str,
    eyebrow: str,
    entries: list[dict],
    intro: str,
    group_key: str = "benefit_group",
) -> str:
    grouped: dict[str, list[dict]] = {}
    for item in entries:
        grouped.setdefault(benefit_value(item, group_key, "Geral"), []).append(item)
    sections = []
    for group, items in sorted(grouped.items(), key=lambda pair: (-len(pair[1]), pair[0])):
        cards = "".join(benefit_card(item, path, compact=len(items) > 80) for item in items)
        sections.append(f"""
<section class="section-wrap" id="{escape(slug(group))}">
  <div class="section-heading">
    <span class="eyebrow">{escape(eyebrow)}</span>
    <h2>{escape(group)}</h2>
    <p>{fmt_num(len(items))} registros ligados a este recorte. Abra cada registro para ler a base legal, condicao, prova e risco.</p>
  </div>
  <div class="benefit-cross-grid">{cards}</div>
</section>
""")
    body = f"""
{hero(title, subtitle, eyebrow)}
<section class="content-block">
  <h2>Como estudar esta página</h2>
  <p>{escape(intro)}</p>
</section>
<section class="law-ledger">
  <div><h2>Registros</h2><p>{fmt_num(len(entries))} registros validados neste recorte.</p></div>
  <div><h2>Origem</h2><p>Estados, Federal e CONFAZ entram apenas quando o trecho legal possui fonte oficial, tratamento tributario e campo operacional verificavel.</p></div>
  <div><h2>Prova</h2><p>O uso prático sempre volta ao XML, EFD, cadastro, memória de cálculo, ato legal e documentos da operação.</p></div>
</section>
{''.join(sections) if sections else '<section class="content-block"><h2>Nenhum registro publicado neste recorte</h2><p>O portal não publica conclusão sem trecho legal validado.</p></section>'}
<section class="continuity">
  <h2>Continuar a leitura</h2>
  <div>
    <a href="{escape(rel_href(path, 'beneficios/index.html'))}">matriz completa</a>
    <a href="{escape(rel_href(path, 'beneficios/ncm.html'))}">NCM x beneficios</a>
    <a href="{escape(rel_href(path, 'federal/legislacao/reforma-tributaria/index.html'))}">Reforma tributaria</a>
    <a href="{escape(rel_href(path, 'confaz/ultimos-5-anos.html'))}">CONFAZ</a>
  </div>
</section>
"""
    return layout(path, title, subtitle, body, "beneficios")


def benefits_by_sector_page(data: dict) -> str:
    entries = benefit_entries()
    return benefit_special_page(
        "beneficios/setores.html",
        "Benefícios fiscais por setor",
        "Agro, alimentos, medicamentos, veículos, eletrônicos, informática, energia, combustíveis, indústria, atacado, logística e demais cadeias com tratamento fiscal em tela.",
        "Setores",
        entries,
        "Entre pelo assunto econômico, depois confirme o tipo de tratamento. Setor é porta de leitura; a aplicação depende da mercadoria, NCM, operação, destinatário, vigência e documento.",
    )


def benefits_by_uf_page(data: dict) -> str:
    entries = benefit_entries()
    return benefit_special_page(
        "beneficios/uf.html",
        "Benefícios fiscais por UF e jurisdição",
        "Mapa de registros validados por Estado, Federal e CONFAZ, com retorno ao texto legal e ao módulo de origem.",
        "UF e jurisdição",
        entries,
        "Use esta página para começar pela jurisdição. Depois volte ao registro individual para separar ICMS estadual, regra federal, ato CONFAZ, código documental e prova.",
        group_key="jurisdiction",
    )


def benefits_reforma_page(data: dict) -> str:
    needles = ("IBS", "CBS", "cClassTrib", "cCredPres", "Imposto Seletivo", "Reforma Tribut")
    entries = [item for item in benefit_entries() if benefit_matches_terms(item, needles, include_group=True)]
    return benefit_special_page(
        "beneficios/reforma.html",
        "Benefícios e tratamentos da Reforma Tributária",
        "Tratamentos de IBS/CBS, cClassTrib, cCredPres, regimes diferenciados, alíquota zero, redução, créditos e transição.",
        "Reforma",
        entries,
        "Leia primeiro a natureza jurídica: redução, alíquota zero, crédito presumido, regime específico ou regra de transição. Depois confira CST, cClassTrib, cCredPres e documento fiscal.",
        group_key="legal_nature",
    )


def benefits_compensacao_icms_page(data: dict) -> str:
    needles = ("compensa", "transi", "ICMS", "cBenef", "LC 160", "Convênio ICMS 190", "saldo credor")
    entries = [item for item in benefit_entries() if benefit_matches_terms(item, needles, include_group=True)]
    return benefit_special_page(
        "beneficios/compensacao-icms.html",
        "Compensação, transição e benefícios de ICMS",
        "Leitura de benefícios atuais de ICMS, cBenef, LC 160/2017, Convênio ICMS 190/2017 e reflexos da transição para IBS/CBS.",
        "ICMS e transição",
        entries,
        "Este recorte não transforma benefício de ICMS em benefício de IBS/CBS. Ele mostra onde há regra atual, código estadual, transição, risco de convivência e necessidade de prova.",
        group_key="jurisdiction",
    )


def benefits_cesta_basica_page(data: dict) -> str:
    entries = [item for item in benefit_entries() if benefit_matches_cesta_basica(item)]
    return benefit_special_page(
        "beneficios/cesta-basica.html",
        "Cesta básica, alimentos e agro",
        "Benefícios e tratamentos para alimentos, cesta básica, agropecuária, insumos e produtos essenciais.",
        "Cesta básica",
        entries,
        "A leitura segura começa pelo produto legalmente descrito. Nome comercial não basta: confirme NCM, destinação, etapa da cadeia, manutenção ou estorno de crédito e documento fiscal.",
    )


def benefits_regimes_diferenciados_page(data: dict) -> str:
    needles = ("regime", "diferenciado", "específico", "especifico", "crédito presumido", "credito presumido", "alíquota zero", "aliquota zero", "redução", "reducao", "Zona Franca", "produtor rural")
    entries = [item for item in benefit_entries() if benefit_matches_terms(item, needles, include_group=True)]
    return benefit_special_page(
        "beneficios/regimes-diferenciados.html",
        "Regimes diferenciados, específicos e créditos presumidos",
        "Tratamentos que exigem leitura de condição, opção, credenciamento, código, cálculo e prova documental.",
        "Regimes",
        entries,
        "Regime diferenciado não é sinônimo de economia automática. O uso defensável depende do artigo, do sujeito, da operação, da condição e do documento que prova a fruição.",
        group_key="legal_nature",
    )


def benefits_documents_page(data: dict) -> str:
    entries = benefit_entries()
    return benefit_special_page(
        "beneficios/documentos-de-prova.html",
        "Documentos de prova dos benefícios fiscais",
        "XML, EFD, cadastro, NCM, cBenef, CST, cClassTrib, guias, atos concessivos, memória de cálculo e documentos comerciais por tipo de tratamento.",
        "Prova",
        entries,
        "A tese só fica útil quando vira prova. Esta página agrupa benefícios pelo documento que normalmente sustenta a aplicação e ajuda a montar dossiê por operação.",
        group_key="proof_required",
    )


def confaz_5y_page(data: dict) -> str:
    master = master_bundle()
    confaz = master["confaz"]
    sections = []
    for family_id, family in confaz.get("families", {}).items():
        year_cards = []
        for year in family.get("years", []):
            acts = year.get("acts", [])
            act_links = "".join(
                f'<a href="{escape(act.get("url", ""))}" target="_blank" rel="noopener">{escape(act.get("title", "") or act.get("url", "").rsplit("/", 1)[-1])}</a>'
                for act in acts[:12]
            )
            if not act_links:
                act_links = "<span>Sem atos capturados nesta rodada no indice consultado.</span>"
            error = f'<p class="source-warning">Captura pendente: {escape(year.get("fetch_error", ""))}</p>' if year.get("fetch_error") else ""
            year_cards.append(f"""
<article class="portal-card searchable-card" data-search="{escape(family.get('title', '') + ' ' + str(year.get('year', '')) + ' ' + ' '.join(a.get('url', '') for a in acts))}">
  <span class="card-kicker">{escape(str(year.get('year', '')))} · {fmt_num(year.get('count', 0))} atos</span>
  <h3>{escape(family.get('title', ''))}</h3>
  <p>Indice oficial do CONFAZ para leitura, classificacao e futura captura integral em tela.</p>
  {error}
  <div class="mini-link-list">{act_links}</div>
  <small><a href="{escape(year.get('index_url', ''))}" target="_blank" rel="noopener">abrir indice oficial</a></small>
</article>
""")
        sections.append(f"""
<section class="section-wrap" id="{escape(family_id)}">
  <div class="section-heading">
    <span class="eyebrow">CONFAZ</span>
    <h2>{escape(family.get('title', ''))}</h2>
    <p>{fmt_num(family.get('total', 0))} atos indexados nos ultimos 5 anos para curadoria, internalizacao estadual e cruzamento com beneficios.</p>
  </div>
  {card_grid(year_cards)}
</section>
""")
    body = f"""
{hero("CONFAZ dos ultimos 5 anos", "Indice oficial de Convenios ICMS, Ajustes SINIEF e Protocolos ICMS para sustentar beneficios, ST, documentos fiscais e reforma tributaria.", "CONFAZ")}
<section class="content-block">
  <h2>Como esta pagina entra na curadoria</h2>
  <p>O indice mostra onde buscar os atos oficiais. O proximo passo, para cada ato relevante, e trazer o texto integral em tela, classificar tema, UF, produto, beneficio, documento fiscal e internalizacao estadual.</p>
  <p>Convenio, Ajuste ou Protocolo nao substitui a norma estadual quando a aplicacao depende de internalizacao. O portal deve guardar as duas pontas: ato nacional e ato local.</p>
</section>
{''.join(sections)}
<section class="continuity">
  <h2>Continuar a leitura</h2>
  <div>
    <a href="index.html">CONFAZ: regra maior</a>
    <a href="../beneficios/index.html">Matriz de beneficios</a>
    <a href="../estados/index.html">Estados</a>
    <a href="../auditoria/index.html">Auditoria mestre</a>
  </div>
</section>
"""
    return layout("confaz/ultimos-5-anos.html", "CONFAZ dos ultimos 5 anos", "Convenios, Ajustes e Protocolos ICMS para curadoria.", body, "confaz")


def state_inventory_sections(state_inv: dict, verified_on: str, compact: bool = False, current_path: str = "") -> str:
    docs = state_inv.get("documents", [])
    if not docs:
        return f"""
<section class="law-ledger">
  {inventory_badge('página estadual em estruturação', state_inv.get('compiled_on', '11/04/2026'), verified_on)}
  <div>
    <h2>Leitura juridica</h2>
    <p>A página ainda não possui texto legal estadual suficiente para publicação responsável.</p>
  </div>
  <div>
    <h2>Conduta segura</h2>
    <p>Nao aplique conclusao estadual sem portal publico do ente, norma vigente e prova documental da operacao.</p>
  </div>
</section>
"""
    lead = f"""
<section class="content-block">
  <h2>Leitura da legislação estadual</h2>
  <p>A leitura estadual deve partir da regra-matriz do ICMS, passar pelos anexos e benefícios, e terminar no documento fiscal, na escrituração e na prova.</p>
  <p>Tratamento favorecido nao se presume por semelhanca comercial: produto, NCM, operacao, destinatario, periodo, regime da empresa e condicoes precisam caber no texto legal.</p>
  <p>Antes de configurar ERP, valide o dispositivo aplicavel, a vigencia, a forma de demonstracao no XML/EFD e o documento que sustentara a defesa em fiscalizacao.</p>
</section>
"""
    ledger = f"""
<section class="law-ledger">
  {inventory_badge('legislação estadual organizada', state_inv.get('compiled_on', '11/04/2026'), verified_on)}
  <div>
    <h2>Material coberto</h2>
    <p>{fmt_num(state_inv.get('file_count', 0))} atos normativos, {fmt_num(state_inv.get('total_chars', 0))} caracteres de texto legal e {fmt_num(len(state_inv.get('categories', [])))} categorias.</p>
  </div>
  <div>
    <h2>Como usar</h2>
    <p>Use a tabela como roteiro: norma material, anexos, benefícios, alíquotas, ST, atos infralegais e prova. A tese concreta sempre volta ao portal oficial da UF.</p>
  </div>
</section>
"""
    signals = signal_grid(
        state_inv.get("signals", {}),
        "Capítulos temáticos do Estado",
        "Abra cada tema como aula: regra, exceção, documento, prova e continuidade para a legislação em tela.",
        current_path,
        "goias" if state_inv.get("uf") == "GO" else f"state:{state_inv.get('uf')}" if state_has_legal_pack(state_inv.get("uf", "")) else "",
    )
    legal = "" if compact else render_law_chapters(
        state_inv.get("legal_chapters", []),
        "Lei estadual em tela",
        "Trechos normativos selecionados para orientar a leitura por regra, beneficio, excecao, documento e apuracao.",
    )
    table = ""
    categories = "" if compact else category_cards(docs)
    return ledger + lead + legal + signals + categories + table


def federal_inventory_sections(data: dict, themes: list[str], verified_on: str, compact: bool = False, current_path: str = "") -> str:
    blocks = []
    for key in themes:
        theme = federal_theme(data, key)
        docs = theme.get("documents", [])
        analysis = FEDERAL_ANALYSIS.get(key, FEDERAL_ANALYSIS["geral"])
        law = ""
        study_grid = (
            folha_study_grid(current_path)
            if key == "previdencia_folha"
            else signal_grid(theme.get('signals', {}), 'Capítulos temáticos do tema', 'Abra cada assunto como aula: conceito, lei em tela, interpretação, prova documental e risco de aplicação.', current_path, key)
        )
        blocks.append(f"""
<section class="law-ledger">
  {inventory_badge(FEDERAL_THEME_LABELS.get(key, key), '11/04/2026', verified_on)}
  <div>
    <h2>Material em estudo</h2>
    <p>{fmt_num(theme.get('file_count', 0))} atos normativos, {fmt_num(theme.get('total_chars', 0))} caracteres de legislacao e pesquisa normativa.</p>
  </div>
  <div>
    <h2>Rota de estudo</h2>
    <p>Leia a lei material, depois regulamento, instrucoes normativas, obrigacoes acessorias e efeitos no documento fiscal ou contabil.</p>
  </div>
</section>
<section class="content-block">
  <h2>{escape(FEDERAL_THEME_LABELS.get(key, key))}: analise de especialista</h2>
  <p>{escape(analysis[0])}</p>
  <p>{escape(analysis[1])}</p>
</section>
{law}
{study_grid}
""")
    return "".join(blocks)


def topic_page(topic: dict, active: str, extra_body: str = "") -> str:
    curated_law = "" if topic_has_legal_module(topic.get("id", "")) else render_law_chapters(
        CURATED_TOPIC_CHAPTERS.get(topic.get("id", ""), []),
        "Lei em tela",
        "Dispositivos de abertura para ler a norma antes da conclusao pratica.",
    )
    intro = f"""
{hero(topic["titulo"], topic["resumo"], topic["tema"])}
<section class="law-ledger">
  {source_badge(topic)}
  <div>
    <h2>Base legal principal</h2>
    <p>{escape(", ".join(topic["base_legal"]))}</p>
  </div>
  <div>
    <h2>Fontes oficiais</h2>
    {source_list(topic["fonte_oficial"])}
  </div>
</section>
"""
    body = intro + curated_law + render_sections(topic) + render_matrix(topic) + extra_body + legal_topic_teaser(topic.get("id", ""), topic["path"]) + related_links(topic)
    return layout(topic["path"], topic["titulo"], topic["resumo"], body, active)


def home(data: dict) -> str:
    topics = data["topics"]
    inventory = data.get("inventory", {})
    state_docs = sum(state.get("file_count", 0) for state in inventory.get("states", []))
    federal_docs = len(inventory.get("federal", {}).get("documents", []))
    states_link = "estados/index.html"
    cards = [
        f"""
<a class="portal-card featured searchable-card" href="{states_link}" data-search="ICMS por Estado beneficios fiscais Goias">
  <span class="card-kicker">Estados</span>
  <h3>ICMS por Estado</h3>
  <p>Arquitetura nacional por UF, com ICMS, beneficios fiscais, documentos, riscos, prova e legislação estadual em tela.</p>
  <small>ICMS estadual publicado por UF</small>
</a>
""",
        topic_card(next(t for t in topics if t["id"] == "goias-icms-beneficios")),
        topic_card(next(t for t in topics if t["id"] == "confaz-atos-beneficios")),
        f"""
<a class="portal-card searchable-card" href="federal/index.html" data-search="PIS Cofins IPI IRPJ CSLL Lucro Real Lucro Presumido Federal">
  <span class="card-kicker">Federal</span>
  <h3>Tributos federais</h3>
  <p>PIS, Cofins, IPI, IOF, IRPJ, CSLL, regimes, beneficios federais, DIRBI e reforma tributaria em leitura guiada.</p>
  <small>Lei em tela por tributo</small>
</a>
""",
        f"""
<a class="portal-card featured searchable-card" href="produto.html" data-search="produto NCM arroz 1006 1006.20 1006.30 1006.40 PIS Cofins IBS CBS LC214 LC224 fonte oficial sha256">
  <span class="card-kicker">Produto/NCM</span>
  <h3>Consulta por produto</h3>
  <p>Pesquisa por produto e NCM com re-selo Planalto, hashes oficiais, corpus estadual amarelo e pendencias A_VALIDAR visiveis.</p>
  <small>Abrir busca inteligente por NCM</small>
</a>
""",
        federal_legislation_card("index.html"),
        goias_legislation_card("index.html"),
        f"""
<a class="portal-card searchable-card" href="beneficios/index.html" data-search="matriz nacional beneficios fiscais NCM CEST cBenef CST cClassTrib isencao reducao credito presumido diferimento monofasico">
  <span class="card-kicker">Cruzamentos</span>
  <h3>Matriz de beneficios</h3>
  <p>Beneficios por UF, tributo, grupo economico, NCM/CEST, tipo de tratamento, prova documental e status editorial.</p>
  <small>Auditar por produto e operacao</small>
</a>
""",
        f"""
<a class="portal-card searchable-card" href="auditoria/index.html" data-search="auditoria cobertura lacunas fontes estados federal confaz">
  <span class="card-kicker">Governanca</span>
  <h3>Auditoria mestre</h3>
  <p>Cobertura, lacunas, fontes registradas, Estados em revisao e proximas frentes de curadoria.</p>
  <small>Ver status do portal</small>
</a>
""",
        f"""
<a class="portal-card searchable-card" href="confaz/ultimos-5-anos.html" data-search="CONFAZ ultimos 5 anos convenios ajustes sinief protocolos icms">
  <span class="card-kicker">CONFAZ</span>
  <h3>Ultimos 5 anos</h3>
  <p>Indice oficial de Convenios ICMS, Ajustes SINIEF e Protocolos ICMS para cruzar beneficios, ST e documentos.</p>
  <small>Abrir esteira nacional</small>
</a>
""",
        topic_card(next(t for t in topics if t["id"] == "folha-clt-previdencia")),
        f"""
<a class="portal-card searchable-card" href="biblioteca/index.html" data-search="manual fiscal financeiro DP RH transportadoras painel fiscal biblioteca">
  <span class="card-kicker">Biblioteca viva</span>
  <h3>Manuais e painel</h3>
  <p>Os materiais existentes continuam funcionando e entram como biblioteca avancada do portal.</p>
  <small>URLs preservadas</small>
</a>
"""
    ]
    federal_cards = [topic_card(t) for t in topics if t["path"].startswith("federal/")][:4]
    federal_cards.extend(
        f"""
<a class="portal-card searchable-card" href="{escape(page["path"])}" data-search="{escape(page["title"] + " " + page["summary"])}">
  <span class="card-kicker">Federal</span>
  <h3>{escape(page["title"])}</h3>
  <p>{escape(page["summary"])}</p>
  <small>Leitura estruturada</small>
</a>
"""
        for page in FEDERAL_EXTRA_PAGES
    )
    body = f"""
{hero(data["site"]["title"], data["site"]["subtitle"], "Portal publico de conhecimento")}
<section class="method-strip">
  <div><strong>Fonte oficial primeiro</strong><span>Planalto, Receita, CONFAZ, SPED e UFs.</span></div>
  <div><strong>Lei em tela</strong><span>Texto normativo, contexto e leitura pratica.</span></div>
  <div><strong>Prova documental</strong><span>Cada tema aponta prova e risco comum.</span></div>
</section>
<section class="section-wrap">
  <div class="section-heading">
    <span class="eyebrow">Comece por aqui</span>
    <h2>Portal, painel e fonte de conhecimento tributario</h2>
    <p>Uma estrutura aberta para ensinar a regra, mostrar a lei, apontar o documento fiscal e conectar a operacao ao fechamento.</p>
  </div>
  {card_grid(cards)}
</section>
<section class="guided-reading">
  <span class="eyebrow">Trilha sugerida</span>
  <h2>Da lei ao documento</h2>
  <div class="timeline">
    <a href="estados/goias.html"><strong>1. Estado</strong><span>Identifique ICMS, beneficio, condicionantes e cBenef.</span></a>
    <a href="confaz/index.html"><strong>2. CONFAZ</strong><span>Confira o lastro nacional de convenio, ajuste ou protocolo.</span></a>
    <a href="federal/pis-cofins.html"><strong>3. Federal</strong><span>Segregue PIS/Cofins, IPI, IRPJ, CSLL e regimes.</span></a>
    <a href="biblioteca/index.html"><strong>4. Prova</strong><span>Use manuais, painel fiscal e rotinas de fechamento.</span></a>
  </div>
</section>
<section class="section-wrap">
  <div class="section-heading">
    <span class="eyebrow">Federal v1</span>
    <h2>Guias profundos publicados</h2>
  </div>
  {card_grid(federal_cards)}
</section>
"""
    return layout("index.html", data["site"]["title"], data["site"]["subtitle"], body, "home")


def estados_index(data: dict) -> str:
    total_docs = sum(inventory_state(data, state["uf"]).get("file_count", 0) for state in data["states"])
    total_chars = sum(inventory_state(data, state["uf"]).get("total_chars", 0) for state in data["states"])
    states_by_uf = {state["uf"]: state for state in data["states"]}
    region_nav = "".join(
        f'<a href="#regiao-{escape(region_id)}">{escape(label)}</a>'
        for region_id, label, _ufs in STATE_REGIONS
    )
    region_sections = []
    for region_id, label, ufs in STATE_REGIONS:
        region_cards = [
            state_card_markup(states_by_uf[uf], data)
            for uf in ufs
            if uf in states_by_uf
        ]
        region_sections.append(f"""
<section class="region-block" id="regiao-{escape(region_id)}">
  <div class="region-heading">
    <div>
      <span class="eyebrow">Região</span>
      <h3>{escape(label)}</h3>
      <p>{escape(STATE_REGION_SUMMARIES.get(region_id, 'Estados organizados para expansão por RICMS, benefícios, documentos e prova.'))}</p>
    </div>
    <a href="#topo-estados">voltar ao mapa</a>
  </div>
  {card_grid(region_cards, "states-grid")}
</section>
""")
    body = f"""
{hero("ICMS por Estado", "Arquitetura nacional para organizar RICMS, leis do imposto, benefícios fiscais, cBenef, alíquotas, ST, regimes e prova por UF.", "Estados")}
<section class="law-ledger">
  <div>
  <h2>Modelo estadual</h2>
  <p>O portal organiza a leitura por UF, categoria legal, regra de ICMS, benefício fiscal, documento e prova. Goiás continua como modelo profundo; os demais Estados ficam em curadoria fonte-a-fonte antes de nova publicação profunda.</p>
  </div>
  <div>
    <h2>Como estudar uma UF</h2>
    <p>Comece por RICMS e lei material; depois avance para anexos, benefícios, alíquotas, ST, regimes especiais, atos infralegais e prova documental.</p>
  </div>
  <div>
  <h2>Postura editorial</h2>
  <p>A tese concreta sempre volta ao texto vigente no portal da UF, CONFAZ ou Planalto na data da operacao.</p>
  </div>
</section>
<section class="section-wrap" id="topo-estados">
  <div class="section-heading">
    <span class="eyebrow">Mapa nacional</span>
    <h2>Estados estruturados por região</h2>
    <p>{fmt_num(total_docs)} atos estaduais mapeados e {fmt_num(total_chars)} caracteres de acervo organizados para virar capítulo por UF, com Goiás como modelo editorial aprovado.</p>
  </div>
  <nav class="region-jump" aria-label="Regiões do Brasil">{region_nav}</nav>
  {''.join(region_sections)}
</section>
{state_expansion_queue(data)}
"""
    return layout("estados/index.html", "ICMS por Estado", "Mapa nacional de ICMS e benefícios fiscais por UF.", body, "estados")


def configured_state_overview_cards(uf: str) -> str:
    cards = []
    priority = [
        "mapa-revisado-beneficios",
        "isencoes-reducoes-creditos",
        "fot-feef-contrapartidas",
        "regimes-setoriais-industria-repetro",
        "creditos-presumidos-acumulados",
        "creditos-exportacao-saldo-credor",
        "creditos-exportacao-acumulado",
        "agro-fundersul-diferimento",
        "invest-compete-fundap",
        "importacao-transporte-veiculos-combustiveis",
        "diferimento-regimes-especiais",
        "ms-empreendedor-regimes",
        "st-antecipacao-segmentos",
        "documentos-efd-prova",
        "fiscalizacao-pagamento-restauracao",
        "fiscalizacao-riscos",
    ]
    chapters = {chapter["id"]: chapter for chapter in configured_chapters(uf)}
    ordered = [chapters[item] for item in priority if item in chapters]
    ordered.extend(chapter for chapter in configured_chapters(uf) if chapter["id"] not in priority)
    for chapter in ordered[:8]:
        href = configured_chapter_path(uf, chapter["id"]).replace(f"estados/{uf.lower()}/", f"{uf.lower()}/")
        cards.append(f"""
    <a class="matrix-card searchable-card" href="{escape(href)}" data-search="{escape(uf + ' ICMS beneficios fiscais ' + chapter['title'] + ' ' + chapter['summary'])}">
      <h3>{escape(chapter['title'])}</h3>
      <p>{escape(chapter['summary'])}</p>
    </a>
""")
    return "".join(cards)


def state_page(state: dict, data: dict) -> str:
    inv = inventory_state(data, state["uf"])
    display_name = state_display_name(state)
    verified_on = data["site"]["verified_on"]
    if state["uf"] == "GO":
        topic = next(t for t in data["topics"] if t["id"] == "goias-icms-beneficios")
        extra = state_inventory_sections(inv, verified_on, compact=True, current_path="estados/goias.html")
        return topic_page(topic, "estados", extra)
    path = f'estados/{state["uf"].lower()}.html'
    has_pack = state_has_legal_pack(state["uf"])
    if not inv.get("file_count", 0) and not has_pack:
        body = f"""
{hero(f'{display_name}: ICMS e benefícios fiscais', f'Página estadual {state_review_suffix(state["uf"])}, para leitura pública e conferência fonte a fonte antes da aprovação profunda.', state["uf"])}
{state_legislation_teaser(state["uf"], path)}
{state_curation_panel(state["uf"])}
<section class="continuity">
  <h2>Continuar com seguranca</h2>
  <div>
    <a href="goias.html">Ver modelo publicado de Goiás</a>
    <a href="../confaz/index.html">Entender CONFAZ e benefícios</a>
    <a href="../federal/index.html">Estudar tributos federais</a>
  </div>
</section>
"""
        return layout(path, f'{display_name}: ICMS e benefícios fiscais', "Página estrutural por UF.", body, "estados")
    if has_pack:
        if state["uf"] == "BA":
            body = f"""
{hero(f'{display_name}: ICMS e benefícios fiscais', 'Legislação estadual em tela: ICMS, benefícios fiscais, alíquotas, ST, documentos e prova por assunto.', state["uf"])}
<section class="law-ledger">
  <div>
    <h2>Estado do estudo</h2>
    <p>A Bahia está publicada em capítulos próprios, sem depender do inventário antigo. O caminho correto é abrir o índice estadual, ler a lei em tela e depois avançar para a análise aplicada.</p>
  </div>
  <div>
    <h2>Primeira pergunta</h2>
    <p>A operação está no campo de incidência do ICMS? Só depois disso faz sentido discutir isenção, redução, crédito outorgado, diferimento, incentivo ou substituição tributária.</p>
  </div>
  <div>
    <h2>Prova antes de tese</h2>
    <p>XML, cadastro do item, NCM, EFD, memória de cálculo, ato concessivo e dispositivo legal precisam sustentar a mesma conclusão.</p>
  </div>
</section>
{state_legislation_teaser(state["uf"], path)}
<section class="matrix-section">
  <h2>Benefícios fiscais por grupo</h2>
  <div class="matrix-grid">
    <a class="matrix-card searchable-card" href="ba/legislacao/mapa-revisado-beneficios.html" data-search="Bahia mapa revisado benefícios fiscais ICMS LC 160 Convênio 190 DESENVOLVE PROIND PRONAVAL crédito presumido EFD">
      <h3>Mapa revisado dos benefícios</h3>
      <p>Rotas normativas por espécie: LC 160, programas, crédito presumido, rural, informática, ST, EFD e prova do benefício.</p>
    </a>
    <a class="matrix-card searchable-card" href="ba/legislacao/desenvolve.html" data-search="Bahia DESENVOLVE indústria implantação ampliação diferimento dilação desconto">
      <h3>Indústria, implantação e ampliação</h3>
      <p>DESENVOLVE: diferimento, dilação de prazo, desconto, resolução, investimento, recolhimento e perda do benefício.</p>
    </a>
    <a class="matrix-card searchable-card" href="ba/legislacao/programas-setoriais.html" data-search="Bahia informática eletrônica automação telecomunicações PROIND PRONAVAL naval crédito presumido">
      <h3>Setores incentivados</h3>
      <p>PROIND, PRONAVAL, informática, eletrônica, telecomunicações e crédito presumido lidos por cadeia econômica.</p>
    </a>
    <a class="matrix-card searchable-card" href="ba/legislacao/beneficios-matriz-lc160.html" data-search="Bahia benefícios fiscais LC 160 Convênio 190 isenção redução crédito outorgado crédito presumido">
      <h3>Isenções, reduções e créditos</h3>
      <p>Matriz dos benefícios listados, reinstituídos e documentados na lógica da LC 160/2017 e do Convênio ICMS 190/2017.</p>
    </a>
    <a class="matrix-card searchable-card" href="ba/legislacao/substituicao-tributaria-antecipacao.html" data-search="Bahia substituição tributária ST antecipação Anexo 1 CEST NCM MVA">
      <h3>ST, antecipação e mercadorias</h3>
      <p>Anexo 1 do RICMS/BA: mercadorias, responsabilidade, CEST/NCM, MVA, pauta e recolhimento antecipado.</p>
    </a>
    <a class="matrix-card searchable-card" href="ba/legislacao/rural-cesta-credito.html" data-search="Bahia agro alimentos rural cesta básica crédito fiscal produtor rural">
      <h3>Agro, alimentos e cesta</h3>
      <p>Anexo 2 e cadeias agroalimentares: crédito fiscal, produto, etapa, destinação, manutenção ou estorno.</p>
    </a>
    <a class="matrix-card searchable-card" href="ba/legislacao/documentos-efd-prova.html" data-search="Bahia EFD SPED XML incentivo código ajuste prova documento fiscal">
      <h3>EFD, XML e prova digital</h3>
      <p>Como o benefício aparece nos registros E110, E111, E115 e E116, e como montar prova mensal defensável.</p>
    </a>
  </div>
</section>
<section class="continuity">
  <h2>Continuar a leitura</h2>
  <div>
    <a href="ba/legislacao/index.html">Abrir índice completo da Bahia</a>
    <a href="../confaz/index.html">Entender CONFAZ e benefícios</a>
    <a href="../federal/pis-cofins.html">Conectar com PIS/Cofins</a>
    <a href="../biblioteca/index.html">Consultar manuais e painel</a>
  </div>
</section>
"""
            return layout(path, f'{display_name}: ICMS e benefícios fiscais', "ICMS baiano em tela por capítulos.", body, "estados")
        if state["uf"] == "DF":
            body = f"""
{hero(f'{display_name}: ICMS e benefícios fiscais', 'Legislação estadual em tela: ICMS, benefícios fiscais, alíquotas, ST, documentos e prova por assunto.', state["uf"])}
<section class="law-ledger">
  <div>
    <h2>Estado do estudo</h2>
    <p>O Distrito Federal está publicado em capítulos próprios, com lei material, RICMS, Cadernos, programas e obrigações acessórias em tela. O caminho correto é abrir o índice do DF, ler a lei e depois avançar para a análise aplicada.</p>
  </div>
  <div>
    <h2>Primeira pergunta</h2>
    <p>A operação está no campo de incidência do ICMS? Só depois disso faz sentido discutir isenção, redução, crédito outorgado, diferimento, regime especial ou substituição tributária.</p>
  </div>
  <div>
    <h2>Prova antes de tese</h2>
    <p>XML, cadastro do item, NCM, EFD, memória de cálculo, ato concessivo e dispositivo legal precisam sustentar a mesma conclusão.</p>
  </div>
</section>
{state_legislation_teaser(state["uf"], path)}
<section class="matrix-section">
  <h2>Benefícios fiscais por grupo</h2>
  <div class="matrix-grid">
    <a class="matrix-card searchable-card" href="df/legislacao/mapa-revisado-beneficios.html" data-search="Distrito Federal DF mapa revisado benefícios ICMS Cadernos Anexo I LC 160 EMPREGA-DF PRÓ-DF Desenvolve-DF EFD">
      <h3>Mapa revisado dos benefícios</h3>
      <p>Cadernos do Anexo I, LC 160, regime especial, crédito outorgado, EMPREGA-DF, PRÓ-DF, Desenvolve-DF e EFD.</p>
    </a>
    <a class="matrix-card searchable-card" href="df/legislacao/regime-especial-apuracao.html" data-search="Distrito Federal DF atacado atacadista regime especial apuração crédito outorgado Lei 5005 Decreto 39753">
      <h3>Atacado e crédito outorgado</h3>
      <p>Regime especial de apuração, cálculo favorecido, operações interestaduais, condições de fruição e perda do benefício.</p>
    </a>
    <a class="matrix-card searchable-card" href="df/legislacao/emprega-df-prodf-desenvolve.html" data-search="Distrito Federal DF EMPREGA-DF PRÓ-DF PRODF Desenvolve-DF investimento emprego incentivo desenvolvimento econômico">
      <h3>EMPREGA-DF, PRÓ-DF e Desenvolve-DF</h3>
      <p>Programas de desenvolvimento econômico: projeto, investimento, emprego, crédito presumido, diferimento, habilitação e prova.</p>
    </a>
    <a class="matrix-card searchable-card" href="df/legislacao/beneficios-setoriais-agro-atacado.html" data-search="Distrito Federal DF agro alho insumos agropecuários diferimento crédito outorgado setor produto">
      <h3>Agro, alho e benefícios setoriais</h3>
      <p>Tratamentos por produto e cadeia: crédito outorgado do alho, diferimento de insumos agropecuários, destinação e documentação.</p>
    </a>
    <a class="matrix-card searchable-card" href="df/legislacao/beneficios-matriz-lc160.html" data-search="Distrito Federal DF benefícios fiscais LC 160 Convênio 190 isenção redução crédito presumido suspensão diferimento Cadernos Anexo I">
      <h3>Isenções, reduções e Cadernos</h3>
      <p>Cadernos do Anexo I do RICMS/DF, LC 160/2017, Convênio ICMS 190/2017, remissão, reinstituição e adesão.</p>
    </a>
    <a class="matrix-card searchable-card" href="df/legislacao/substituicao-tributaria-antecipacao.html" data-search="Distrito Federal DF substituição tributária ST antecipação Anexo IV CEST NCM MVA responsabilidade">
      <h3>ST, antecipação e mercadorias</h3>
      <p>Anexo IV do RICMS/DF: responsável, substituto, substituído, mercadorias, MVA/pauta, recolhimento e prova.</p>
    </a>
    <a class="matrix-card searchable-card" href="df/legislacao/documentos-efd-prova.html" data-search="Distrito Federal DF EFD SPED ICMS IPI XML documento fiscal escrituração prova">
      <h3>EFD, XML e prova digital</h3>
      <p>Como a tese aparece no documento fiscal, na EFD ICMS/IPI, nos registros, nos ajustes e no dossiê mensal.</p>
    </a>
  </div>
</section>
<section class="continuity">
  <h2>Continuar a leitura</h2>
  <div>
    <a href="df/legislacao/index.html">Abrir índice completo do DF</a>
    <a href="../confaz/index.html">Entender CONFAZ e benefícios</a>
    <a href="../federal/pis-cofins.html">Conectar com PIS/Cofins</a>
    <a href="../biblioteca/index.html">Consultar manuais e painel</a>
  </div>
</section>
"""
            return layout(path, f'{display_name}: ICMS e benefícios fiscais', "ICMS do Distrito Federal em tela por capítulos.", body, "estados")
        if state["uf"] == "MT":
            body = f"""
{hero(f'{display_name}: ICMS e benefícios fiscais', 'Legislação estadual em tela: ICMS, benefícios fiscais, alíquotas, ST, documentos e prova por assunto.', state["uf"])}
<section class="law-ledger">
  <div>
    <h2>Estado do estudo</h2>
    <p>Mato Grosso está publicado em capítulos próprios, com lei material, RICMS, LC 631/2019, anexos de benefícios e códigos de benefício em tela. O caminho correto é abrir o índice de MT, ler a lei e depois avançar para a análise aplicada.</p>
  </div>
  <div>
    <h2>Primeira pergunta</h2>
    <p>A operação está no campo de incidência do ICMS? Só depois disso faz sentido discutir isenção, redução de base, crédito outorgado, diferimento, PRODEIC, ST ou estimativa simplificada.</p>
  </div>
  <div>
    <h2>Prova antes de tese</h2>
    <p>XML, cadastro do item, NCM, EFD, cBenef, memória de cálculo, ato concessivo e dispositivo legal precisam sustentar a mesma conclusão.</p>
  </div>
</section>
{state_legislation_teaser(state["uf"], path)}
<section class="matrix-section">
  <h2>Benefícios fiscais por grupo</h2>
  <div class="matrix-grid">
    <a class="matrix-card searchable-card" href="mt/legislacao/mapa-revisado-beneficios.html" data-search="Mato Grosso MT mapa revisado benefícios ICMS art 12 RICMS LC 631 PRODEIC cBenef anexos IV V VI VII VIII">
      <h3>Mapa revisado dos benefícios</h3>
      <p>Art. 12 do RICMS/MT, anexos IV a VIII, LC 631/2019, PRODEIC, cBenef, ST, estimativa e prova fiscal.</p>
    </a>
    <a class="matrix-card searchable-card" href="mt/legislacao/prodeic-desenvolvimento.html" data-search="Mato Grosso MT PRODEIC desenvolvimento econômico indústria comércio incentivo programa estadual">
      <h3>PRODEIC e desenvolvimento</h3>
      <p>Programas, módulos, resoluções, condições de fruição, crédito, redução, prazo, metas e prova de cumprimento.</p>
    </a>
    <a class="matrix-card searchable-card" href="mt/legislacao/isencoes-reducoes-creditos.html" data-search="Mato Grosso MT isenção redução base cálculo crédito outorgado crédito presumido Anexo IV V VI cBenef">
      <h3>Isenções, reduções e créditos</h3>
      <p>Anexos IV, V e VI do RICMS/MT: benefício por produto, operação, setor, destinatário e documentos de prova.</p>
    </a>
    <a class="matrix-card searchable-card" href="mt/legislacao/agro-cesta-diferimento.html" data-search="Mato Grosso MT agro alimentos cesta básica vegetal animal biodiesel diferimento Anexo VII">
      <h3>Agro, cesta e diferimento</h3>
      <p>Cadeias agroindustriais, cesta básica, produtos vegetais e animais, biodiesel, diferimento e controle da etapa posterior.</p>
    </a>
    <a class="matrix-card searchable-card" href="mt/legislacao/beneficios-matriz-lc160.html" data-search="Mato Grosso MT benefícios fiscais LC 160 Convênio 190 LC 631 remissão anistia reinstituição">
      <h3>LC 160, reinstituição e matriz</h3>
      <p>LC nº 631/2019, remissão, anistia, reinstituição, regras gerais de fruição, vedações, suspensão e revogações.</p>
    </a>
    <a class="matrix-card searchable-card" href="mt/legislacao/st-estimativa-anexos.html" data-search="Mato Grosso MT substituição tributária ST estimativa simplificada carga média CNAE Anexo X XIII">
      <h3>ST e estimativa simplificada</h3>
      <p>Responsabilidade, substituição tributária, segmentos, carga média por CNAE, recolhimento e prova da cadeia.</p>
    </a>
    <a class="matrix-card searchable-card" href="mt/legislacao/documentos-cbenef-efd-prova.html" data-search="Mato Grosso MT cBenef EFD SPED XML código benefício Portaria 211 documento fiscal">
      <h3>cBenef, EFD e prova digital</h3>
      <p>Como o benefício aparece no XML, no código de benefício, na escrituração e no dossiê mensal de auditoria.</p>
    </a>
  </div>
</section>
<section class="continuity">
  <h2>Continuar a leitura</h2>
  <div>
    <a href="mt/legislacao/index.html">Abrir índice completo de MT</a>
    <a href="../confaz/index.html">Entender CONFAZ e benefícios</a>
    <a href="../federal/pis-cofins.html">Conectar com PIS/Cofins</a>
    <a href="../biblioteca/index.html">Consultar manuais e painel</a>
  </div>
</section>
"""
            return layout(path, f'{display_name}: ICMS e benefícios fiscais', "ICMS de Mato Grosso em tela por capítulos.", body, "estados")
        if state["uf"] == "RN":
            body = f"""
{hero(f'{display_name}: ICMS e benefícios fiscais', 'Legislação estadual em tela: ICMS, benefícios fiscais, alíquotas, FECOP, ST, documentos, PROEDI, FUNDERN e cBenef por assunto.', state["uf"])}
<section class="law-ledger">
  <div>
    <h2>Estado do estudo</h2>
    <p>Rio Grande do Norte está publicado em capítulos próprios, com RICMS, anexos de benefícios, matriz LC 160, PROEDI, FUNDERN, Tax Free, cBenef, ST e documentos fiscais em tela. O caminho correto é abrir o índice do RN, ler a lei e depois avançar para a análise aplicada.</p>
  </div>
  <div>
    <h2>Primeira pergunta</h2>
    <p>A operação está no campo de incidência do ICMS? Só depois disso faz sentido discutir isenção, redução de base, crédito presumido, diferimento, PROEDI, Tax Free, ST ou antecipação.</p>
  </div>
  <div>
    <h2>Prova antes de tese</h2>
    <p>XML, cadastro do item, NCM, EFD, cBenef, memória de cálculo, ato concessivo, guia e dispositivo legal precisam sustentar a mesma conclusão.</p>
  </div>
</section>
{state_legislation_teaser(state["uf"], path)}
<section class="matrix-section">
  <h2>Benefícios fiscais por grupo</h2>
  <div class="matrix-grid">
    <a class="matrix-card searchable-card" href="rn/legislacao/mapa-revisado-beneficios.html" data-search="Rio Grande do Norte RN mapa revisado benefícios ICMS LC 160 Convênio 190 isenção redução crédito presumido diferimento PROEDI Tax Free FUNDERN cBenef">
      <h3>Mapa revisado dos benefícios</h3>
      <p>Roteiro por técnica: isenção, redução, crédito presumido, diferimento, PROEDI, Tax Free, FUNDERN, atacado, ST, cBenef e prova.</p>
    </a>
    <a class="matrix-card searchable-card" href="rn/legislacao/proedi-desenvolvimento.html" data-search="Rio Grande do Norte RN PROEDI desenvolvimento industrial crédito presumido FUNDERN incentivo fiscal">
      <h3>PROEDI e desenvolvimento</h3>
      <p>Lei nº 10.640/2019, Decreto nº 29.420/2019, crédito presumido, enquadramento, requerimento, regularidade, contrapartida e perda do benefício.</p>
    </a>
    <a class="matrix-card searchable-card" href="rn/legislacao/isencoes-reducoes-creditos.html" data-search="Rio Grande do Norte RN isenção redução base crédito presumido Anexo 001 Anexo 003 Anexo 004 cBenef">
      <h3>Isenções, reduções e créditos</h3>
      <p>Anexos 001, 003 e 004 do RICMS/RN: produto, operação, destinatário, carga efetiva, crédito, estorno e cBenef.</p>
    </a>
    <a class="matrix-card searchable-card" href="rn/legislacao/agro-cesta-diferimento.html" data-search="Rio Grande do Norte RN agro alimentos abate gado pesca óleo diesel biodiesel diferimento cesta">
      <h3>Agro, alimentos, pesca e diferimento</h3>
      <p>Cadeias agroalimentares, abate, transporte coletivo, embarcações pesqueiras, óleo diesel/biodiesel e diferimento por etapa.</p>
    </a>
    <a class="matrix-card searchable-card" href="rn/legislacao/beneficios-matriz-lc160.html" data-search="Rio Grande do Norte RN benefícios fiscais LC 160 Convênio 190 Portaria 022 FUNDERN atos normativos">
      <h3>LC 160, matriz e FUNDERN</h3>
      <p>Portaria nº 022/2018-GS/SET, atos de benefícios, reinstituição, contrapartida financeira, depósito e prova mensal.</p>
    </a>
    <a class="matrix-card searchable-card" href="rn/legislacao/atacado-distribuicao-regimes.html" data-search="Rio Grande do Norte RN atacado atacadista distribuição regime especial cosméticos perfumaria higiene pessoal">
      <h3>Atacado, distribuição e regimes</h3>
      <p>Regime especial de atacadistas, percentuais de saídas, atividades reais, vedações, mercadorias e regularidade.</p>
    </a>
    <a class="matrix-card searchable-card" href="rn/legislacao/st-antecipacao-combustiveis.html" data-search="Rio Grande do Norte RN substituição tributária ST antecipação combustíveis lubrificantes trigo farinha veículos">
      <h3>ST, antecipação e segmentos</h3>
      <p>Anexos 005, 007, 008, 009 e 010: antecipação, ST geral, combustíveis, trigo/farinha e veículos autopropulsados.</p>
    </a>
    <a class="matrix-card searchable-card" href="rn/legislacao/documentos-cbenef-efd-prova.html" data-search="Rio Grande do Norte RN cBenef EFD SPED XML NF-e NFC-e documento fiscal prova Portaria 970">
      <h3>cBenef, EFD e prova digital</h3>
      <p>Como o benefício aparece no XML, na NF-e/NFC-e, na EFD, nos livros fiscais e no dossiê mensal de auditoria.</p>
    </a>
  </div>
</section>
<section class="continuity">
  <h2>Continuar a leitura</h2>
  <div>
    <a href="rn/legislacao/index.html">Abrir índice completo do RN</a>
    <a href="../confaz/index.html">Entender CONFAZ e benefícios</a>
    <a href="../federal/pis-cofins.html">Conectar com PIS/Cofins</a>
    <a href="../biblioteca/index.html">Consultar manuais e painel</a>
  </div>
</section>
"""
            return layout(path, f'{display_name}: ICMS e benefícios fiscais', "ICMS do Rio Grande do Norte em tela por capítulos.", body, "estados")
        if state["uf"] in CONFIGURED_STATE_CHAPTERS:
            profile = configured_profile(state["uf"])
            body = f"""
{hero(f'{display_name}: ICMS e benefícios fiscais', profile.get('hero', 'Legislação estadual em tela: ICMS, benefícios fiscais, alíquotas, ST, documentos e prova por assunto.'), state["uf"])}
<section class="law-ledger">
  <div>
    <h2>Estado do estudo</h2>
    <p>{escape(display_name)} está publicado em capítulos próprios, com legislação em tela, benefícios por grupos, regimes especiais, documentos fiscais e prova. O caminho correto é abrir o índice do Estado, ler a lei e depois avançar para a análise aplicada.</p>
  </div>
  <div>
    <h2>Primeira pergunta</h2>
    <p>{escape(profile.get('first_question', 'A operação está no campo de incidência do ICMS? Só depois disso faz sentido discutir benefício, regime, ST ou documento.'))}</p>
  </div>
  <div>
    <h2>Prova antes de tese</h2>
    <p>XML, cadastro do item, NCM, EFD, memória de cálculo, ato concessivo, guia e dispositivo legal precisam sustentar a mesma conclusão.</p>
  </div>
</section>
{state_legislation_teaser(state["uf"], path)}
<section class="matrix-section">
  <h2>Benefícios fiscais por grupo</h2>
  <div class="matrix-grid">
{configured_state_overview_cards(state["uf"])}
  </div>
</section>
<section class="continuity">
  <h2>Continuar a leitura</h2>
  <div>
    <a href="{state["uf"].lower()}/legislacao/index.html">Abrir índice completo de {escape(state["uf"])}</a>
    <a href="../confaz/index.html">Entender CONFAZ e benefícios</a>
    <a href="../federal/pis-cofins.html">Conectar com PIS/Cofins</a>
    <a href="../biblioteca/index.html">Consultar manuais e painel</a>
  </div>
</section>
"""
            return layout(path, f'{display_name}: ICMS e benefícios fiscais', f"ICMS de {display_name} em tela por capítulos.", body, "estados")
        body = f"""
{hero(f'{display_name}: ICMS e benefícios fiscais', 'Legislação estadual em tela: ICMS, benefícios fiscais, alíquotas, ST, documentos e prova por assunto.', state["uf"])}
<section class="law-ledger">
  <div>
    <h2>Estado do estudo</h2>
    <p>A legislação estadual de ICMS já está publicada em tela por temas. Use o índice legal antes de aplicar qualquer conclusão operacional.</p>
  </div>
  <div>
    <h2>Primeira pergunta</h2>
    <p>A operação está no campo de incidência do ICMS? Só depois disso faz sentido discutir isenção, redução, crédito outorgado, diferimento ou ST.</p>
  </div>
  <div>
    <h2>Prova antes de tese</h2>
    <p>XML, cadastro do item, NCM, EFD, memória de cálculo e dispositivo legal precisam sustentar a mesma conclusão.</p>
  </div>
</section>
{state_legislation_teaser(state["uf"], path)}
{state_inventory_sections(inv, verified_on, current_path=path)}
<section class="continuity">
  <h2>Continuar a leitura</h2>
  <div>
    <a href="../confaz/index.html">Entender CONFAZ e benefícios</a>
    <a href="../federal/pis-cofins.html">Conectar com PIS/Cofins</a>
    <a href="../biblioteca/index.html">Consultar manuais e painel</a>
  </div>
</section>
"""
        return layout(path, f'{display_name}: ICMS e benefícios fiscais', "ICMS estadual em tela por UF.", body, "estados")
    body = f"""
{hero(f'{display_name}: ICMS e benefícios fiscais', f'Página estadual {state_review_suffix(state["uf"])}: RICMS, benefícios, alíquotas, ST, atos infralegais e prova podem ser lidos na web antes da aprovação profunda.', state["uf"])}
<section class="law-ledger">
  <div>
    <h2>Estado do estudo</h2>
    <p>Página estadual revisada criticamente, mas ainda sem aprovação profunda. O material disponível deve ser lido como bancada de conferência, não como conclusão tributária aprovada.</p>
  </div>
  <div>
    <h2>Primeira pergunta</h2>
    <p>A operacao esta no campo de incidencia do ICMS? So depois disso faz sentido discutir isencao, reducao, credito outorgado, diferimento ou ST.</p>
  </div>
  <div>
    <h2>Prova antes de tese</h2>
    <p>XML, cadastro do item, NCM, EFD, memoria de calculo e dispositivo legal precisam sustentar a mesma conclusao.</p>
  </div>
</section>
{state_curation_panel(state["uf"])}
<section class="matrix-section">
  <h2>Matriz estadual de trabalho</h2>
  <div class="matrix-grid">
    <article class="matrix-card"><h3>ICMS material</h3><p>Localize fato gerador, contribuinte, responsavel, base, aliquota, diferimento, ST e obrigacoes acessorias.</p></article>
    <article class="matrix-card"><h3>Benefícios fiscais</h3><p>Classifique o favor fiscal: isenção, redução de base, crédito outorgado, suspensão, regime especial ou incentivo condicionado.</p></article>
    <article class="matrix-card"><h3>Documento e SPED</h3><p>Confira NF-e, CT-e, MDF-e, cBenef quando houver, EFD, ajustes e memoria de calculo.</p></article>
    <article class="matrix-card"><h3>Risco comum</h3><p>Nao aplique beneficio por semelhanca comercial. Produto, operacao, destinatario, vigencia e condicao precisam caber no texto legal.</p></article>
  </div>
</section>
{state_legislation_teaser(state["uf"], path)}
<section class="continuity">
  <h2>Continuar a leitura</h2>
  <div>
    <a href="goias.html">Ver modelo publicado de Goiás</a>
    <a href="../confaz/index.html">Entender CONFAZ e benefícios</a>
    <a href="../federal/pis-cofins.html">Conectar com PIS/Cofins</a>
    <a href="../biblioteca/index.html">Consultar manuais e painel</a>
  </div>
</section>
"""
    return layout(path, f'{display_name}: ICMS e benefícios fiscais', "Página estrutural por UF.", body, "estados")


def federal_index(data: dict) -> str:
    topics = [t for t in data["topics"] if t["path"].startswith("federal/")]
    cards = [federal_legislation_card("federal/index.html")]
    for topic in topics:
        local_topic = dict(topic)
        local_topic["path"] = Path(topic["path"]).name
        cards.append(topic_card(local_topic))
    for page in FEDERAL_EXTRA_PAGES:
        theme = federal_theme(data, page["theme"])
        cards.append(f"""
<a class="portal-card searchable-card" href="{escape(Path(page["path"]).name)}"
   data-search="{escape(page["title"] + " " + page["summary"] + " " + page["theme"])}">
  <span class="card-kicker">Federal</span>
  <h3>{escape(page["title"])}</h3>
  <p>{escape(page["summary"])}</p>
  <small>Texto legal e analise</small>
</a>
""")
    cards.append(f"""
<a class="portal-card featured searchable-card" href="acervo.html"
   data-search="fontes federais legislacao Receita Planalto DOU PIS COFINS IPI IOF IRPJ CSLL reforma">
  <span class="card-kicker">Fontes</span>
  <h3>Fontes federais por tema</h3>
  <p>Mapa de estudo por tributo, com texto legal, fonte publica e continuidade para os capitulos profundos.</p>
  <small>Planalto, Receita, DOU e SPED</small>
</a>
""")
    fed_themes = data.get("inventory", {}).get("federal", {}).get("themes", {})
    body = f"""
{hero("Tributos federais", "PIS, Cofins, IPI, IRPJ, CSLL, regimes tributarios, beneficios federais e DIRBI com fonte oficial.", "Federal")}
<section class="law-ledger">
  <div>
    <h2>Como navegar</h2>
    <p>Comece pelo tributo, depois confirme o regime da empresa, o tratamento especial, a obrigacao acessoria e a prova documental.</p>
  </div>
  <div>
    <h2>Legislacao federal</h2>
    <p>Os tributos federais foram organizados por tema de estudo: regra material, beneficios, obrigacoes acessorias, riscos e prova.</p>
  </div>
  <div>
    <h2>Fontes base</h2>
    <p>Planalto, Receita Federal, SPED, DOU, CONFAZ quando cruzar ICMS e atos vigentes em fonte aberta.</p>
  </div>
</section>
<section class="section-wrap">
  <div class="section-heading">
    <span class="eyebrow">Guias publicados</span>
    <h2>Federal em profundidade</h2>
  </div>
  {card_grid(cards)}
</section>
"""
    return layout("federal/index.html", "Tributos federais", "Guias federais profundos.", body, "federal")


def federal_theme_page(data: dict, page: dict) -> str:
    theme = federal_theme(data, page["theme"])
    body = f"""
{hero(page["title"], page["summary"], "Federal")}
{federal_inventory_sections(data, [page["theme"]], data["site"]["verified_on"], current_path=page["path"])}
{legal_theme_teaser(page["theme"], page["path"])}
<section class="continuity">
  <h2>Continuar a leitura</h2>
  <div>
    <a href="index.html">Voltar aos tributos federais</a>
    <a href="acervo.html">Ver fontes federais por tema</a>
    <a href="../biblioteca/index.html">Consultar biblioteca e manuais</a>
  </div>
</section>
"""
    return layout(page["path"], page["title"], page["summary"], body, "federal")


def federal_acervo_page(data: dict) -> str:
    themes = data.get("inventory", {}).get("federal", {}).get("themes", {})
    cards = []
    for key, theme in sorted(themes.items(), key=lambda item: FEDERAL_THEME_LABELS.get(item[0], item[0])):
        page = next((item for item in FEDERAL_EXTRA_PAGES if item["theme"] == key), None)
        href = Path(page["path"]).name if page else "index.html"
        cards.append(f"""
<article class="portal-card searchable-card" data-search="{escape(key + ' ' + FEDERAL_THEME_LABELS.get(key, key))}">
  <span class="card-kicker">Federal</span>
  <h3>{escape(FEDERAL_THEME_LABELS.get(key, key))}</h3>
  <p>Trilha de leitura com norma, regulamento, obrigacao acessoria, prova e conexao com os capitulos profundos.</p>
  <small>{a(href, 'abrir trilha') if page else 'trilha integrada aos guias'}</small>
</article>
""")
    docs = data.get("inventory", {}).get("federal", {}).get("documents", [])
    body = f"""
{hero("Fontes federais por tema", "Mapa de atos federais estruturados por tributo, fonte, sinais de auditoria e continuidade de estudo.", "Federal")}
<section class="law-ledger">
  {inventory_badge('legislacao federal organizada', '11/04/2026', data["site"]["verified_on"])}
  <div>
    <h2>Escopo</h2>
    <p>PIS/Cofins, IPI, IOF, IRPJ/CSLL, regimes, beneficios, folha, reforma e aduaneiro em trilhas de leitura por assunto.</p>
  </div>
  <div>
    <h2>Regra de publicacao</h2>
    <p>Conclusao tributaria so entra no portal quando puder ser sustentada por texto legal, fonte publica e prova operacional.</p>
  </div>
</section>
<section class="section-wrap">
  <div class="section-heading">
    <span class="eyebrow">Mapa federal</span>
    <h2>Temas federais</h2>
  </div>
  {card_grid(cards)}
</section>
<section class="continuity">
  <h2>Continuar a leitura</h2>
  <div>
    <a href="legislacao/index.html">Legislacao federal em tela</a>
    <a href="pis-cofins.html">PIS e Cofins</a>
    <a href="ipi.html">IPI</a>
    <a href="iof.html">IOF</a>
    <a href="irpj-csll.html">IRPJ e CSLL</a>
    <a href="reforma-tributaria.html">Reforma tributaria</a>
  </div>
</section>
"""
    return layout("federal/acervo.html", "Fontes federais por tema", "Mapa federal por fonte publica e trilha legal.", body, "federal")


def biblioteca(data: dict) -> str:
    cards = []
    for item in data["library"]:
        cards.append(f"""
<a class="portal-card searchable-card" href="../{escape(item["href"])}"
   data-search="{escape(item["title"] + " " + item["summary"] + " " + item["type"])}">
  <span class="card-kicker">{escape(item["type"])}</span>
  <h3>{escape(item["title"])}</h3>
  <p>{escape(item["summary"])}</p>
  <small>URL preservada</small>
</a>
""")
    inventory = data.get("inventory", {})
    state_docs = sum(state.get("file_count", 0) for state in inventory.get("states", []))
    federal_docs = len(inventory.get("federal", {}).get("documents", []))
    body = f"""
{hero("Biblioteca viva", "Manuais, painel e materiais avancados preservados como camada de aprofundamento do portal.", "Biblioteca")}
<section id="metodo" class="law-ledger">
  <div>
    <h2>Metodo editorial</h2>
    <p>{escape(data["site"]["source_policy"])}</p>
  </div>
  <div>
    <h2>Data editorial</h2>
    <p>Conteudos profundos v1 atualizados em {escape(data["site"]["verified_on"])}. Paginas estruturais indicam quando ainda aguardam texto legal completo para publicacao.</p>
  </div>
  <div>
    <h2>Lei e prova</h2>
    <p>A leitura combina texto normativo, fonte publica, documento fiscal, memoria de calculo e risco de autuacao.</p>
  </div>
</section>
<section class="content-block">
  <h2>Como a legislacao entra no portal</h2>
  <p>O portal organiza leis, decretos, regulamentos, instrucoes normativas, anexos, beneficios e atos federais em leitura de consultoria: o que a regra faz, que prova pede, onde costuma haver risco e qual caminho seguir antes de aplicar no ERP ou no fechamento.</p>
  <p>Quando houver conclusao tributaria, a pagina apresenta texto legal em tela, link publico da fonte normativa e leitura pratica para o departamento fiscal, contabil, financeiro, juridico e de auditoria.</p>
</section>
<section class="section-wrap">
  <div class="section-heading">
    <span class="eyebrow">Biblioteca RJC</span>
    <h2>Manuais e painel preservados</h2>
  </div>
  {card_grid(cards)}
</section>
<section class="continuity">
  <h2>Entrar na legislacao</h2>
  <div>
    <a href="../estados/index.html">ICMS por Estado</a>
    <a href="../federal/acervo.html">Fontes federais por tema</a>
    <a href="../confaz/index.html">CONFAZ e beneficios</a>
  </div>
</section>
"""
    return layout("biblioteca/index.html", "Biblioteca viva", "Manuais e painel preservados.", body, "biblioteca")


class FullSearchTextParser(HTMLParser):
    skip_tags = {"script", "style", "head", "svg", "header", "footer", "nav"}
    block_tags = {"p", "div", "section", "article", "li", "tr", "td", "th", "h1", "h2", "h3", "h4", "br"}

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.skip_stack: list[str] = []
        self.h1_parts: list[str] = []
        self.in_h1 = False
        self.meta_description = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attrs_map = {name.lower(): value or "" for name, value in attrs}
        if tag in self.skip_tags:
            self.skip_stack.append(tag)
        if tag == "meta" and attrs_map.get("name", "").lower() == "description":
            self.meta_description = attrs_map.get("content", "")
        if tag == "h1" and not self.skip_stack:
            self.in_h1 = True
        if tag in self.block_tags and not self.skip_stack:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "h1":
            self.in_h1 = False
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
        if self.in_h1:
            self.h1_parts.append(data)

    def visible_text(self) -> str:
        text = " ".join("".join(self.parts).split())
        return text.strip()

    def title(self, fallback: str) -> str:
        h1 = " ".join(" ".join(self.h1_parts).split()).strip()
        return h1 or fallback


def normalize_search_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_text = ascii_text.lower()
    ascii_text = re.sub(r"[^a-z0-9]+", " ", ascii_text)
    return re.sub(r"\s+", " ", ascii_text).strip()


def compact_search_terms(text: str) -> str:
    seen: set[str] = set()
    terms: list[str] = []
    for token in normalize_search_text(clean_search_fragment(text)).split():
        if len(token) < 2 or token in FULL_SEARCH_STOPWORDS or token in seen:
            continue
        seen.add(token)
        terms.append(token)
    return " ".join(terms)


def clean_search_fragment(value: object) -> str:
    text = unescape(str(value or ""))
    text = re.sub(
        r"(?:=+\s*)?(?:PÁGINA|PAGINA|PÃ.?GINA)\s+\d+(?:\s*=+)?(?:\s+[A-Za-z0-9_.\\/-]+){0,10}",
        " ",
        text,
        flags=re.I,
    )
    text = text.replace("[]", " ")
    text = text.replace("[", " ").replace("]", " ")
    text = text.replace("{", " ").replace("}", " ")
    text = text.replace("'", " ").replace('"', " ")
    return " ".join(text.split())


def search_value_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return " ".join(part for item in value if (part := search_value_text(item)))
    if isinstance(value, dict):
        return " ".join(part for item in value.values() if (part := search_value_text(item)))
    return clean_search_fragment(value)


def search_summary(text: str, meta: str) -> str:
    base = clean_search_fragment(meta or text)
    if len(base) <= 230:
        return base
    return base[:227].rsplit(" ", 1)[0] + "..."


def search_body(text: str, limit: int = 1400) -> str:
    base = clean_search_fragment(text)
    if len(base) <= limit:
        return base
    return base[:limit].rsplit(" ", 1)[0]


def search_scope(rel: str) -> dict[str, str]:
    parts = rel.split("/")
    scope = {"jurisdiction": "", "tax": "", "theme": ""}
    if rel.startswith("estados/"):
        scope["jurisdiction"] = parts[1].upper() if len(parts) > 1 else "Estados"
        scope["tax"] = "ICMS"
        scope["theme"] = "estadual beneficios fiscais"
    elif rel.startswith("federal/"):
        scope["jurisdiction"] = "Federal"
        scope["theme"] = "federal"
        for token in ("irpj", "csll", "iof", "ipi", "pis", "cofins", "reforma", "lucro-real", "lucro-presumido"):
            if token in rel:
                scope["tax"] = token.replace("-", " ").upper()
                break
    elif rel.startswith("folha-clt/"):
        scope["jurisdiction"] = "Federal"
        scope["tax"] = "Folha CLT Previdenciario"
        scope["theme"] = "trabalhista"
    elif rel.startswith("confaz/"):
        scope["jurisdiction"] = "Nacional"
        scope["tax"] = "ICMS"
        scope["theme"] = "CONFAZ"
    elif rel.startswith("beneficios/"):
        scope["jurisdiction"] = "Nacional"
        scope["theme"] = "beneficios fiscais"
    return scope


def benefit_index_text(value: object) -> str:
    if isinstance(value, list):
        return " ".join(clean_search_fragment(part) for part in value if clean_search_fragment(part))
    if isinstance(value, dict):
        return " ".join(clean_search_fragment(part) for part in value.values() if clean_search_fragment(part))
    return clean_search_fragment(value)


def benefit_full_search_entries() -> list[dict[str, str]]:
    payload = load_json(BENEFITS_CROSSWALK, {"entries": []})
    entries: list[dict[str, str]] = []
    for item in payload.get("entries", []):
        if item.get("validation_status") != "validado":
            continue
        parts = [
            item.get("jurisdiction", ""),
            item.get("name", ""),
            item.get("tax", ""),
            item.get("benefit_group", ""),
            benefit_index_text(item.get("benefit_group_evidence")),
            item.get("benefit_type", ""),
            item.get("scope_summary", ""),
            item.get("goods_or_services", ""),
            item.get("product_or_operation", ""),
            benefit_index_text(item.get("ncm")),
            benefit_index_text(item.get("cest")),
            benefit_index_text(item.get("cbenef")),
            benefit_index_text(item.get("cst")),
            benefit_index_text(item.get("cclasstrib")),
            item.get("transition_status", ""),
            item.get("validity_status", ""),
            item.get("legal_nature", ""),
            item.get("beneficio", ""),
            item.get("mercadoria_servico", ""),
            item.get("ente_uf", ""),
            benefit_index_text(item.get("ato_oficial")),
            item.get("publicacao", ""),
            item.get("inicio_vigencia", ""),
            item.get("inicio_eficacia", ""),
            item.get("fim_vigencia", ""),
            item.get("status", ""),
            item.get("transicao_rt", ""),
            item.get("verificado_em", ""),
            item.get("validity_start", ""),
            item.get("validity_end", ""),
            item.get("conditions", ""),
            item.get("condicao", ""),
            item.get("prohibitions", ""),
            item.get("legal_basis", ""),
            benefit_index_text(item.get("prova_documental")),
            item.get("risco", ""),
            item.get("source_title", ""),
            item.get("legal_excerpt", ""),
        ]
        contract_prefix = " ".join(
            str(part) for part in [
                item.get("scope_summary", ""),
                item.get("validity_status", ""),
                item.get("status", ""),
                item.get("transicao_rt", ""),
                item.get("verificado_em", ""),
            ]
            if str(part).strip()
        )
        text = " ".join([contract_prefix, *(str(part) for part in parts if str(part).strip())])
        title = " · ".join(
            part for part in [
                item.get("jurisdiction", ""),
                item.get("tax", ""),
                item.get("benefit_type", ""),
            ]
            if part
        )
        summary = search_summary(
            " ".join([item.get("scope_summary", ""), item.get("conditions", ""), item.get("legal_basis", "")]),
            "",
        )
        entries.append({
            "title": title or "Beneficio fiscal validado",
            "url": f"beneficios/index.html#{item.get('id', '')}",
            "summary": summary,
            "tags": compact_search_terms(text),
            "body": search_body(text, 1100),
            "kind": "Beneficio fiscal validado",
            "jurisdiction": item.get("jurisdiction", ""),
            "tax": item.get("tax", ""),
            "theme": item.get("benefit_group", ""),
        })
    return entries


def ncm_full_search_entries() -> list[dict[str, str]]:
    payload = load_json(NCM_BENEFITS_INDEX, {"rows": []})
    entries: list[dict[str, str]] = []
    for item in payload.get("rows", []):
        parts = [
            item.get("ncm", ""),
            item.get("ncm_digits", ""),
            item.get("origin", ""),
            item.get("jurisdiction", ""),
            item.get("tax", ""),
            item.get("benefit_group", ""),
            item.get("benefit_type", ""),
            item.get("product_or_operation", ""),
            item.get("conditions", ""),
            item.get("prohibitions", ""),
            item.get("legal_basis", ""),
            item.get("source_title", ""),
        ]
        text = " ".join(str(part) for part in parts if str(part).strip())
        body_text = " ".join([text, item.get("legal_excerpt", "")])
        title = f"{item.get('ncm', '')} · {item.get('jurisdiction', '')} · {item.get('benefit_type', '')}"
        entries.append({
            "title": title,
            "url": f"beneficios/ncm.html#{item.get('id', '')}",
            "summary": search_summary(
                " ".join([item.get("product_or_operation", ""), item.get("conditions", ""), item.get("legal_basis", "")]),
                "",
            ),
            "tags": compact_search_terms(text),
            "body": search_body(body_text, 360),
            "kind": "NCM x beneficio",
            "jurisdiction": item.get("jurisdiction", ""),
            "tax": item.get("tax", ""),
            "theme": item.get("benefit_group", ""),
        })
    return entries


def pis_cofins_ncm_full_search_entries() -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for row in pis_cofins_ncm_public_rows():
        ncm = row.get("ncm", {}) if isinstance(row.get("ncm"), dict) else {}
        ato = row.get("ato_oficial", {}) if isinstance(row.get("ato_oficial"), dict) else {}
        treatment = str(row.get("tratamento", ""))
        treatment_label = PIS_COFINS_TREATMENT_LABELS.get(treatment, treatment.replace("_", " "))
        text = pis_ncm_search_text(row)
        title = f"{ncm.get('codigo', '')} · PIS/Cofins · {treatment_label}"
        summary = " | ".join(
            part
            for part in (
                pis_trim(row.get("resumo_operacional") or row.get("mercadoria_servico"), 220),
                f"status {row.get('status', '')}",
                f"ato {ato.get('tipo', '')} {ato.get('numero', '')}",
            )
            if str(part).strip()
        )
        entries.append({
            "title": title,
            "url": f"federal/legislacao/pis-cofins/ncm.html#{row.get('id', '')}",
            "summary": summary,
            "tags": compact_search_terms(text),
            "body": search_body(text, 1200),
            "kind": "PIS/Cofins por NCM",
            "jurisdiction": "Federal",
            "tax": "PIS/Cofins",
            "theme": treatment_label,
        })
    return entries


def produtos_ncm_full_search_entries() -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    source_map = produto_source_map()
    for product in produtos_ncm_products():
        ncm_codes = ", ".join(str(item.get("codigo", "")) for item in product.get("ncm", []) if item.get("codigo"))
        source_labels = ", ".join(
            produto_source_label(source_map.get(str(source.get("id", "")), {}))
            for source in product.get("official_sources", [])
            if isinstance(source, dict)
        )
        text_parts = [
            product.get("id", ""),
            product.get("produto", ""),
            product.get("status", ""),
            product.get("search_text", ""),
            ncm_codes,
            source_labels,
            " ".join(str(item) for item in product.get("why_not_green", [])),
        ]
        for ncm in product.get("ncm", []):
            text_parts.extend(str(ncm.get(key, "")) for key in ("codigo", "digitos", "descricao", "pis_cofins", "ibs_cbs", "status"))
        for reselo in product.get("reselos", []):
            text_parts.extend(str(reselo.get(key, "")) for key in ("id", "beneficio", "assertion", "status", "transicao_rt"))
        text = " ".join(part for part in text_parts if str(part).strip())
        entries.append({
            "title": f"{product.get('produto', 'Produto')} · Produto/NCM",
            "url": f"produto.html#{product.get('id', '')}",
            "summary": f"{ncm_codes or 'NCM a validar'} · status {product.get('status', 'A_VALIDAR')} · seed com fonte oficial e hashes.",
            "tags": compact_search_terms(text),
            "body": search_body(text, 1200),
            "kind": "Produto/NCM",
            "jurisdiction": "Federal/Estados",
            "tax": "PIS/Cofins IBS/CBS ICMS",
            "theme": "Produto e classificacao fiscal",
        })
    return entries


def full_text_search_entries() -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for html_path in iter_public_html_files():
        rel = html_path.relative_to(ROOT).as_posix()
        if rel.startswith("assets/"):
            continue
        if rel.startswith("beneficios/"):
            # Benefit/NCM records are indexed below as structured entries.
            # Parsing the large matrix HTML pages duplicates content and makes
            # the build unnecessarily slow.
            continue
        if rel == "federal/legislacao/pis-cofins/ncm.html":
            # PIS/Cofins NCM rows are indexed below from NDJSON so each record
            # keeps its own validity envelope and source link.
            continue
        if rel == "produto.html":
            # Produto/NCM is indexed below from JSON so A_VALIDAR and hashes stay inline.
            continue
        raw = html_path.read_text(encoding="utf-8", errors="ignore")
        parser = FullSearchTextParser()
        parser.feed(raw)
        text = parser.visible_text()
        if len(text) < 80:
            continue
        title_match = re.search(r"<title>(.*?)</title>", raw, flags=re.I | re.S)
        fallback_title = re.sub(r"\s+", " ", title_match.group(1)).strip() if title_match else rel
        title = parser.title(fallback_title)
        terms = compact_search_terms(text)
        if not terms:
            continue
        kind = "Texto legal" if "/legislacao/" in rel else "Página"
        if "/fontes/" in rel or "/atos/" in rel:
            kind = "Ato em tela"
        scope = search_scope(rel)
        entries.append({
            "title": title,
            "url": rel,
            "summary": search_summary(text, parser.meta_description),
            "tags": terms,
            "body": search_body(text),
            "kind": kind,
            **scope,
        })
    return entries


def search_index(data: dict) -> str:
    entries = [
        {"title": data["site"]["title"], "url": "index.html", "summary": data["site"]["subtitle"], "tags": "portal tributario aberto"}
    ]
    entries += [
        {
            "title": topic["titulo"],
            "url": topic["path"],
            "summary": topic["resumo"],
            "tags": " ".join([topic["jurisdicao"], topic["tema"], topic["tipo"], " ".join(topic["base_legal"])])
        }
        for topic in data["topics"]
    ]
    entries += [
        {
            "title": f'{state_display_name(state)}: ICMS e benefícios fiscais',
            "url": state_href(state["uf"]),
            "summary": (
                "Goiás publicado com ICMS, benefícios fiscais, cBenef, RCTE, prova e leitura legal."
                if state["uf"] == "GO"
                else "Página estadual com legislação de ICMS em tela, benefícios, documento e prova."
                if state_has_legal_pack(state["uf"])
                else f"Página estadual {state_review_suffix(state['uf'])}, com material de ICMS, benefícios, documento e prova para leitura na web."
            ),
            "tags": f'{state["uf"]} {state["name"]} {state_display_name(state)} ICMS beneficios fiscais RICMS ' + " ".join(inventory_state(data, state["uf"]).get("categories", []))
        }
        for state in data["states"]
    ]
    entries += [
        {
            "title": page["title"],
            "url": page["path"],
            "summary": page["summary"],
            "tags": page["theme"] + " " + FEDERAL_THEME_LABELS.get(page["theme"], "")
        }
        for page in FEDERAL_EXTRA_PAGES
    ]
    entries.append({
        "title": "Fontes federais por tema",
        "url": "federal/acervo.html",
        "summary": "Mapa de atos federais por tema, fonte publica e sinais de auditoria.",
        "tags": "PIS Cofins IPI IOF IRPJ CSLL reforma beneficios DIRBI previdencia folha"
    })
    entries += [
        {
            "title": "Auditoria mestre do portal",
            "url": "auditoria/index.html",
            "summary": "Cobertura, lacunas, status editorial, fontes e fila de curadoria do portal tributario.",
            "tags": "auditoria cobertura lacunas fonte oficial estados federal confaz",
        },
        {
            "title": "Matriz nacional de beneficios fiscais",
            "url": "beneficios/index.html",
            "summary": "Cruzamento por UF, tributo, NCM/CEST, grupo economico, tipo de beneficio e prova documental.",
            "tags": "beneficios fiscais NCM CEST cBenef CST cClassTrib isencao reducao credito presumido diferimento monofasico compensacao beneficio ICMS cBenef SP exportacao ICMS",
        },
        {
            "title": "Lista NCM x beneficios fiscais",
            "url": "beneficios/ncm.html",
            "summary": "NCM/TIPI cruzado com beneficios estaduais, federais e CONFAZ, com condicao, base legal e fonte.",
            "tags": "NCM TIPI beneficios fiscais estados federal CONFAZ isencao reducao credito presumido diferimento monofasico",
        },
        {
            "title": "Beneficios fiscais por setor",
            "url": "beneficios/setores.html",
            "summary": "Beneficios por cadeia economica: agro, alimentos, medicamentos, veiculos, eletronicos, informatica, energia, industria, atacado e logistica.",
            "tags": "beneficios fiscais setor agro alimentos cesta basica medicamentos veiculos eletronicos informatica combustiveis industria atacado logistica",
        },
        {
            "title": "Beneficios fiscais por UF",
            "url": "beneficios/uf.html",
            "summary": "Registros validados por jurisdicao estadual, Federal e CONFAZ.",
            "tags": "beneficios fiscais UF Estado Federal CONFAZ ICMS PIS Cofins IPI IBS CBS",
        },
        {
            "title": "Beneficios e tratamentos da Reforma Tributaria",
            "url": "beneficios/reforma.html",
            "summary": "IBS, CBS, cClassTrib, cCredPres, regimes diferenciados, reducoes, aliquota zero, creditos e transicao.",
            "tags": "IBS CBS Reforma Tributaria cClassTrib cCredPres CST regimes diferenciados cesta basica split payment",
        },
        {
            "title": "Compensacao, transicao e beneficios de ICMS",
            "url": "beneficios/compensacao-icms.html",
            "summary": "Beneficios atuais de ICMS, cBenef, LC 160, Convenio ICMS 190 e convivencia com IBS/CBS.",
            "tags": "ICMS cBenef LC 160 Convenio ICMS 190 compensacao beneficio ICMS transicao beneficios fiscais cBenef SP exportacao ICMS",
        },
        {
            "title": "Cesta basica, alimentos e agro",
            "url": "beneficios/cesta-basica.html",
            "summary": "Tratamentos fiscais para alimentos, cesta basica, agropecuaria, insumos e produtos essenciais.",
            "tags": "cesta basica alimentos agro insumos arroz feijao leite carne horticolas frutas ovos",
        },
        {
            "title": "Regimes diferenciados e creditos presumidos",
            "url": "beneficios/regimes-diferenciados.html",
            "summary": "Regimes especificos, reducoes, creditos presumidos, aliquota zero e tratamentos condicionados.",
            "tags": "regime diferenciado regime especifico credito presumido aliquota zero reducao beneficio fiscal",
        },
        {
            "title": "Documentos de prova dos beneficios fiscais",
            "url": "beneficios/documentos-de-prova.html",
            "summary": "XML, EFD, NCM, cBenef, CST, cClassTrib, guias, atos concessivos e memoria de calculo.",
            "tags": "prova documental XML EFD NCM cBenef CST cClassTrib guia ato concessivo memoria de calculo",
        },
        {
            "title": "CONFAZ dos ultimos 5 anos",
            "url": "confaz/ultimos-5-anos.html",
            "summary": "Indice de Convenios ICMS, Ajustes SINIEF e Protocolos ICMS para curadoria e cruzamentos.",
            "tags": "CONFAZ Convenios ICMS Ajustes SINIEF Protocolos ICMS 2022 2023 2024 2025 2026",
        },
    ]
    entries += legal_search_entries()
    entries += state_legal_search_entries(data)
    entries += [
        {
            "title": item["title"],
            "url": item["href"],
            "summary": item["summary"],
            "tags": item["type"]
        }
        for item in data["library"]
    ]
    payload = json.dumps(entries, ensure_ascii=False, indent=2)
    return "window.RJC_SEARCH = " + payload + ";\n"


def is_workspace_duplicate(path: Path) -> bool:
    return bool(re.search(r" \(\d+\)$", path.stem))


def iter_public_html_files() -> list[Path]:
    blocked = {".git", ".codex-screenshots"}
    return sorted(
        page
        for page in ROOT.rglob("*.html")
        if not any(part in blocked for part in page.relative_to(ROOT).parts) and not is_workspace_duplicate(page)
    )


def html_pages_for_discovery() -> list[Path]:
    return sorted(
        iter_public_html_files(),
        key=lambda item: (site_path(str(item.relative_to(ROOT))) != "index.html", site_path(str(item.relative_to(ROOT)))),
    )


def page_title(path: Path) -> str:
    try:
        head = path.open("r", encoding="utf-8", errors="ignore").read(8192)
    except OSError:
        return site_path(str(path.relative_to(ROOT)))
    match = re.search(r"<title>(.*?)</title>", head, flags=re.I | re.S)
    if not match:
        return site_path(str(path.relative_to(ROOT)))
    return re.sub(r"\s+", " ", match.group(1)).strip()


def sitemap_priority(relative_path: str) -> str:
    if relative_path == "index.html":
        return "1.0"
    if relative_path.endswith("/index.html") or relative_path in {
        "beneficios/ncm.html",
        "produto.html",
        "beneficios/reforma.html",
        "federal/pis-cofins-ncm.html",
        "federal/legislacao/pis-cofins/ncm.html",
        "confaz/ultimos-5-anos.html",
        "auditoria/index.html",
    }:
        return "0.9"
    if "/legislacao/" in relative_path or relative_path.startswith("beneficios/"):
        return "0.8"
    return "0.7"


def sitemap_xml() -> str:
    rows = []
    for page in html_pages_for_discovery():
        relative = site_path(str(page.relative_to(ROOT)))
        lastmod = datetime.fromtimestamp(page.stat().st_mtime).date().isoformat()
        rows.append(
            "  <url>\n"
            f"    <loc>{escape(canonical_url(relative), quote=True)}</loc>\n"
            f"    <lastmod>{lastmod}</lastmod>\n"
            "    <changefreq>weekly</changefreq>\n"
            f"    <priority>{sitemap_priority(relative)}</priority>\n"
            "  </url>"
        )
    return "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n" + (
        "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">\n"
        + "\n".join(rows)
        + "\n</urlset>\n"
    )


def sitemap_txt() -> str:
    return "\n".join(canonical_url(site_path(str(page.relative_to(ROOT)))) for page in html_pages_for_discovery()) + "\n"


def robots_txt() -> str:
    return f"""User-agent: *
Allow: /

Sitemap: {BASE_URL}/sitemap.xml
Sitemap: {BASE_URL}/sitemap.txt

# Portal publico de legislacao tributaria, fiscal, trabalhista e Reforma Tributaria.
# Conteudo essencial tambem fica em tela no proprio GitHub Pages.
"""


def llm_manifest() -> list[dict[str, str]]:
    items = []
    for page in html_pages_for_discovery():
        relative = site_path(str(page.relative_to(ROOT)))
        section = relative.split("/", 1)[0] if "/" in relative else "portal"
        items.append(
            {
                "title": page_title(page),
                "path": relative,
                "url": canonical_url(relative),
                "section": section,
            }
        )
    return items


def llms_txt() -> str:
    manifest = llm_manifest()
    featured = [
        ("Inicio", "index.html"),
        ("Federal", "federal/index.html"),
        ("Reforma Tributaria", "federal/legislacao/reforma-tributaria/index.html"),
        ("PIS/Cofins por NCM", "federal/pis-cofins-ncm.html"),
        ("Produto/NCM", "produto.html"),
        ("Beneficios fiscais", "beneficios/index.html"),
        ("Beneficios por NCM", "beneficios/ncm.html"),
        ("Beneficios por setor", "beneficios/setores.html"),
        ("Estados", "estados/index.html"),
        ("CONFAZ", "confaz/index.html"),
        ("CONFAZ ultimos 5 anos", "confaz/ultimos-5-anos.html"),
        ("Folha e CLT", "folha-clt/index.html"),
    ]
    lines = [
        "# Portal RJC Tributario Aberto",
        "",
        "> Base aberta, gratuita e versionada de legislacao tributaria, fiscal, trabalhista e Reforma Tributaria brasileira. O portal prioriza texto legal em tela, fonte oficial, analise didatica e cruzamentos por UF, tributo, beneficio, NCM, cBenef, CST, cClassTrib e documentos de prova.",
        "",
        "## Como usar esta base",
        "",
        "- Use as paginas HTML como fonte primaria navegavel.",
        "- Use `sitemap.xml` ou `sitemap.txt` para descobrir todas as URLs publicas.",
        "- Use `assets/portal-search-full.json`, `data/benefits_crosswalk.json`, `data/ncm_benefits_index.json`, `data/pis-cofins/ncm.ndjson` e `data/produtos-ncm/index.json` para busca e cruzamento estruturado.",
        "- Corpus estadual local em `data/corpus-local/legal_sources_registry.json` tem teto AMARELO; nao use como prova verde sem SEFAZ/CONFAZ oficial viva.",
        "- Em materia tributaria concreta, conferir a fonte oficial citada na propria pagina e fazer homologacao humana final.",
        "",
        "## Entradas principais",
        "",
    ]
    for label, path in featured:
        lines.append(f"- [{label}]({canonical_url(path)})")
    lines += [
        "",
        "## Indices para agentes",
        "",
        f"- [Sitemap XML]({BASE_URL}/sitemap.xml)",
        f"- [Sitemap texto]({BASE_URL}/sitemap.txt)",
        f"- [Manifesto JSON]({BASE_URL}/assets/llm-manifest.json)",
        f"- [Busca contextual JSON]({BASE_URL}/assets/portal-search-full.json)",
        f"- [Matriz de beneficios]({BASE_URL}/data/benefits_crosswalk.json)",
        f"- [NCM x beneficios]({BASE_URL}/data/ncm_benefits_index.json)",
        f"- [PIS/Cofins por NCM NDJSON]({BASE_URL}/data/pis-cofins/ncm.ndjson)",
        f"- [PIS/Cofins por NCM indice]({BASE_URL}/data/pis-cofins/ncm-index.json)",
        f"- [Produto/NCM indice]({BASE_URL}/data/produtos-ncm/index.json)",
        f"- [Produto/NCM capitulo 10]({BASE_URL}/data/produtos-ncm/cap-10.json)",
        f"- [Re-selo LC 214/224/227]({BASE_URL}/data/reforma-tributaria/reselo-lc214-lc224-lc227.ndjson)",
        f"- [Corpus estadual local amarelo]({BASE_URL}/data/corpus-local/legal_sources_registry.json)",
        f"- [Plano UF/cBenef A_VALIDAR]({BASE_URL}/data/corpus-local/uf-sealing-plan.json)",
        f"- [Registro de fontes legais]({BASE_URL}/data/legal_sources_registry.json)",
        "",
        "## Mapa completo de paginas HTML",
        "",
    ]
    for item in manifest:
        lines.append(f"- [{item['title']}]({item['url']})")
    return "\n".join(lines) + "\n"


def write_discovery_files() -> None:
    write("robots.txt", robots_txt())
    write("sitemap.xml", sitemap_xml())
    write("sitemap.txt", sitemap_txt())
    write("llms.txt", llms_txt())
    write("assets/llm-manifest.json", json.dumps(llm_manifest(), ensure_ascii=False, indent=2))


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    if path.suffix.lower() in {".html", ".txt", ".json", ".js", ".xml", ".ndjson", ".md"}:
        data = path.read_text(encoding="utf-8", errors="ignore").replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
        digest.update(data)
        return digest.hexdigest()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_build_freshness() -> None:
    artifact_paths = [
        "beneficios/index.html",
        "llms.txt",
        "assets/llm-manifest.json",
        "assets/portal-search.js",
        "assets/portal-search-full.json",
        "data/benefits_crosswalk.json",
        "produto.html",
        "data/produtos-ncm/index.json",
        "data/produtos-ncm/cap-10.json",
        "data/corpus-local/legal_sources_registry.json",
        "data/corpus-local/uf-sealing-plan.json",
        "data/reforma-tributaria/reselo-lc214-lc224-lc227.ndjson",
        "data/pis-cofins/ncm.ndjson",
        "data/pis-cofins/ncm-index.json",
        "federal/pis-cofins-ncm.html",
        "federal/legislacao/pis-cofins/ncm.html",
    ]
    artifacts = {}
    for rel in artifact_paths:
        path = ROOT / rel
        artifacts[rel] = {
            "sha256": file_sha256(path),
            "bytes": path.stat().st_size,
        }
    payload = {
        "schema": "rjc-build-freshness-v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "artifacts": artifacts,
    }
    write("assets/build-freshness.json", json.dumps(payload, ensure_ascii=False, indent=2))


def write(path: str, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    if path.endswith(".html"):
        content = polish_html_text(content)
    clean = "\n".join(line.rstrip() for line in content.splitlines()) + "\n"
    tmp = target.with_name(f".{target.name}.tmp")
    tmp.write_text(clean, encoding="utf-8", newline="\n")
    try:
        tmp.replace(target)
    except OSError:
        target.unlink(missing_ok=True)
        tmp.replace(target)


def normalize_legacy_editorial_dates() -> None:
    old_editorial_dates = [
        "/".join(["25", "04", "2026"]),
        "/".join(["14", "06", "2026"]),
    ]
    replacements = {
        "Conteudos profundos v1 atualizados em 17/05/2026": f"Conteudos profundos v1 atualizados em {EDITORIAL_UPDATED_ON}",
    }
    for old_editorial_date in old_editorial_dates:
        replacements.update({
            f"<span>{old_editorial_date}</span>": f"<span>{EDITORIAL_UPDATED_ON}</span>",
            f"Atualizacao editorial: {old_editorial_date}": f"Atualizacao editorial: {EDITORIAL_UPDATED_ON}",
            f"Atualizada em {old_editorial_date}": f"Atualizada em {EDITORIAL_UPDATED_ON}",
            f"Conteúdo atualizado em {old_editorial_date}": f"Conteúdo atualizado em {EDITORIAL_UPDATED_ON}",
            f"Conteudo atualizado em {old_editorial_date}": f"Conteudo atualizado em {EDITORIAL_UPDATED_ON}",
            f"organização editorial V3 atualizada em {old_editorial_date}": f"organização editorial V3 atualizada em {EDITORIAL_UPDATED_ON}",
            f"organizacao editorial V3 atualizada em {old_editorial_date}": f"organizacao editorial V3 atualizada em {EDITORIAL_UPDATED_ON}",
        })
    for path in iter_public_html_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        updated = text
        for old, new in replacements.items():
            updated = updated.replace(old, new)
        if updated == text:
            continue
        clean = "\n".join(line.rstrip() for line in updated.splitlines()) + "\n"
        tmp = path.with_name(f".{path.name}.tmp")
        tmp.write_text(clean, encoding="utf-8", newline="\n")
        try:
            tmp.replace(path)
        except OSError:
            path.unlink(missing_ok=True)
            tmp.replace(path)


def audit(data: dict) -> None:
    required = ["titulo", "jurisdicao", "tema", "tipo", "resumo", "base_legal", "fonte_oficial", "data_conferencia", "status_curadoria", "links_relacionados"]
    errors = []
    for topic in data["topics"]:
        for key in required:
            if not topic.get(key):
                errors.append(f'{topic.get("id", "?")}: missing {key}')
        for source in topic.get("fonte_oficial", []):
            if not source.get("url", "").startswith("https://"):
                errors.append(f'{topic["id"]}: source is not https: {source}')
    if errors:
        raise SystemExit("\n".join(errors))


def main() -> None:
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    data["inventory"] = load_inventory()
    audit(data)
    write("index.html", home(data))
    write("auditoria/index.html", source_audit_index_page(data))
    write("produto.html", produto_ncm_page(data))
    write("beneficios/index.html", benefits_crosswalk_page(data))
    write("beneficios/ncm.html", ncm_benefits_page(data))
    write("beneficios/setores.html", benefits_by_sector_page(data))
    write("beneficios/uf.html", benefits_by_uf_page(data))
    write("beneficios/reforma.html", benefits_reforma_page(data))
    write("beneficios/compensacao-icms.html", benefits_compensacao_icms_page(data))
    write("beneficios/cesta-basica.html", benefits_cesta_basica_page(data))
    write("beneficios/regimes-diferenciados.html", benefits_regimes_diferenciados_page(data))
    write("beneficios/documentos-de-prova.html", benefits_documents_page(data))
    write("estados/index.html", estados_index(data))
    write("estados/auditoria-fontes.html", state_source_audit_page(data))
    for state in data["states"]:
        write(state_href(state["uf"]), state_page(state, data))
    write("federal/index.html", federal_index(data))
    write("federal/pis-cofins-ncm.html", pis_cofins_ncm_landing_page(data))
    write("federal/legislacao/pis-cofins/ncm.html", pis_cofins_ncm_table_page(data))
    for topic in data["topics"]:
        if topic["path"] in {"estados/goias.html", "confaz/index.html", "folha-clt/index.html"}:
            continue
        if topic["path"].startswith("federal/"):
            extra = federal_inventory_sections(data, TOPIC_THEME_MAP.get(topic["id"], []), data["site"]["verified_on"], compact=True, current_path=topic["path"])
            write(topic["path"], topic_page(topic, "federal", extra))
    for page in FEDERAL_EXTRA_PAGES:
        if page.get("custom_page"):
            continue
        write(page["path"], federal_theme_page(data, page))
    write("federal/acervo.html", federal_acervo_page(data))
    write("confaz/index.html", topic_page(next(t for t in data["topics"] if t["id"] == "confaz-atos-beneficios"), "confaz"))
    write("confaz/ultimos-5-anos.html", confaz_5y_page(data))
    folha_topic = next(t for t in data["topics"] if t["id"] == "folha-clt-previdencia")
    folha_extra = federal_inventory_sections(data, TOPIC_THEME_MAP.get(folha_topic["id"], []), data["site"]["verified_on"], compact=True, current_path="folha-clt/index.html")
    write("folha-clt/index.html", topic_page(folha_topic, "folha", folha_extra))
    write("biblioteca/index.html", biblioteca(data))
    for legal_path, legal_content in build_legal_pages(layout).items():
        write(legal_path, legal_content)
    for state_legal_path, state_legal_content in build_state_legal_pages(layout, data).items():
        write(state_legal_path, state_legal_content)
    normalize_legacy_editorial_dates()
    write("assets/portal-search.js", search_index(data))
    write("assets/portal-search-full.json", json.dumps(full_text_search_entries() + benefit_full_search_entries() + ncm_full_search_entries() + pis_cofins_ncm_full_search_entries() + produtos_ncm_full_search_entries(), ensure_ascii=False, separators=(",", ":")))
    write_discovery_files()
    write_build_freshness()
    print("Portal generated successfully.")


if __name__ == "__main__":
    main()
