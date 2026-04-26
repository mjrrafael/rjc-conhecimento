#!/usr/bin/env python3
"""Build the static RJC open tax portal from the curated catalog."""

from __future__ import annotations

import json
import re
from html import escape
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
    build_state_legal_pages,
    state_has_legal_pack,
    state_legal_search_entries,
    state_legislation_teaser,
    state_signal_links,
)


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "portal_catalog.json"
INVENTORY = ROOT / "data" / "legal_inventory.json"

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


def a(href: str, label: str, class_name: str = "") -> str:
    cls = f' class="{escape(class_name)}"' if class_name else ""
    return f'<a href="{escape(href)}"{cls}>{escape(label)}</a>'


def load_inventory() -> dict:
    if not INVENTORY.exists():
        return {"states": [], "federal": {"themes": {}, "documents": []}}
    return json.loads(INVENTORY.read_text(encoding="utf-8"))


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
        status = "Estrutura pronta para expansao"
    else:
        status = "Pagina em estruturacao"
    coverage = (
        "RICMS, leis, anexos e beneficios em tela"
        if state_has_legal_pack(state["uf"])
        else "Texto legal estadual em preparacao"
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
    nav = [
        ("index.html", "Inicio", "home"),
        ("estados/index.html", "Estados", "estados"),
        ("confaz/index.html", "CONFAZ", "confaz"),
        ("federal/index.html", "Federal", "federal"),
        ("folha-clt/index.html", "Folha e CLT", "folha"),
        ("biblioteca/index.html", "Biblioteca", "biblioteca")
    ]
    nav_html = "".join(
        f'<a href="{prefix}{href}" class="{ "active" if key == active else "" }">{label}</a>'
        for href, label, key in nav
    )
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escape(title)} | RJC Assessoria</title>
  <meta name="description" content="{escape(subtitle)}">
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
      <label for="globalSearch">Buscar no portal</label>
      <input id="globalSearch" type="search" placeholder="Ex.: cBenef Goias, DIRBI, Convênio ICMS, Lucro Real">
      <div id="searchResults" class="search-results" aria-live="polite"></div>
    </div>
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
      <span>Atualizacao editorial: 25/04/2026</span>
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


def state_inventory_sections(state_inv: dict, verified_on: str, compact: bool = False, current_path: str = "") -> str:
    docs = state_inv.get("documents", [])
    if not docs:
        return f"""
<section class="law-ledger">
  {inventory_badge('pagina estadual em estruturacao', state_inv.get('compiled_on', '11/04/2026'), verified_on)}
  <div>
    <h2>Leitura juridica</h2>
    <p>A pagina ainda nao possui texto legal estadual suficiente para publicacao responsavel.</p>
  </div>
  <div>
    <h2>Conduta segura</h2>
    <p>Nao aplique conclusao estadual sem portal publico do ente, norma vigente e prova documental da operacao.</p>
  </div>
</section>
"""
    lead = f"""
<section class="content-block">
  <h2>Leitura da legislacao estadual</h2>
  <p>A leitura estadual deve partir da regra-matriz do ICMS, passar pelos anexos e beneficios, e terminar no documento fiscal, na escrituracao e na prova.</p>
  <p>Tratamento favorecido nao se presume por semelhanca comercial: produto, NCM, operacao, destinatario, periodo, regime da empresa e condicoes precisam caber no texto legal.</p>
  <p>Antes de configurar ERP, valide o dispositivo aplicavel, a vigencia, a forma de demonstracao no XML/EFD e o documento que sustentara a defesa em fiscalizacao.</p>
</section>
"""
    ledger = f"""
<section class="law-ledger">
  {inventory_badge('legislacao estadual organizada', state_inv.get('compiled_on', '11/04/2026'), verified_on)}
  <div>
    <h2>Material coberto</h2>
    <p>{fmt_num(state_inv.get('file_count', 0))} atos normativos, {fmt_num(state_inv.get('total_chars', 0))} caracteres de texto legal e {fmt_num(len(state_inv.get('categories', [])))} categorias.</p>
  </div>
  <div>
    <h2>Como usar</h2>
    <p>Use a tabela como roteiro: norma material, anexos, beneficios, aliquotas, ST, atos infralegais e prova. A tese concreta sempre volta ao portal oficial da UF.</p>
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
{signal_grid(theme.get('signals', {}), 'Capítulos temáticos do tema', 'Abra cada assunto como aula: conceito, lei em tela, interpretação, prova documental e risco de aplicação.', current_path, key)}
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
        federal_legislation_card("index.html"),
        goias_legislation_card("index.html"),
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
      <span class="eyebrow">Regiao</span>
      <h3>{escape(label)}</h3>
      <p>{escape(STATE_REGION_SUMMARIES.get(region_id, 'Estados organizados para expansao por RICMS, beneficios, documentos e prova.'))}</p>
    </div>
    <a href="#topo-estados">voltar ao mapa</a>
  </div>
  {card_grid(region_cards, "states-grid")}
</section>
""")
    body = f"""
{hero("ICMS por Estado", "Arquitetura nacional para organizar RICMS, leis do imposto, beneficios fiscais, cBenef, aliquotas, ST, regimes e prova por UF.", "Estados")}
<section class="law-ledger">
  <div>
  <h2>Modelo estadual</h2>
  <p>O portal organiza a leitura por UF, categoria legal, regra de ICMS, beneficio fiscal, documento e prova. Goias continua como modelo profundo; os demais Estados agora têm legislação de ICMS em tela para estudo e expansão didática.</p>
  </div>
  <div>
    <h2>Como estudar uma UF</h2>
    <p>Comece por RICMS e lei material; depois avance para anexos, beneficios, aliquotas, ST, regimes especiais, atos infralegais e prova documental.</p>
  </div>
  <div>
  <h2>Postura editorial</h2>
  <p>A tese concreta sempre volta ao texto vigente no portal da UF, CONFAZ ou Planalto na data da operacao.</p>
  </div>
</section>
<section class="section-wrap" id="topo-estados">
  <div class="section-heading">
    <span class="eyebrow">Mapa nacional</span>
    <h2>Estados estruturados por regiao</h2>
    <p>{fmt_num(total_docs)} atos estaduais mapeados e {fmt_num(total_chars)} caracteres de acervo organizados para virar capitulo por UF, com Goias como modelo editorial aprovado.</p>
  </div>
  <nav class="region-jump" aria-label="Regioes do Brasil">{region_nav}</nav>
  {''.join(region_sections)}
</section>
"""
    return layout("estados/index.html", "ICMS por Estado", "Mapa nacional de ICMS e beneficios fiscais por UF.", body, "estados")


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
{hero(f'{display_name}: ICMS e beneficios fiscais', 'Pagina preservada para publicacao responsavel quando houver texto legal estadual suficiente para leitura publica.', state["uf"])}
{state_inventory_sections(inv, verified_on, current_path=path)}
<section class="continuity">
  <h2>Continuar com seguranca</h2>
  <div>
    <a href="goias.html">Ver modelo publicado de Goias</a>
    <a href="../confaz/index.html">Entender CONFAZ e beneficios</a>
    <a href="../federal/index.html">Estudar tributos federais</a>
  </div>
</section>
"""
        return layout(path, f'{display_name}: ICMS e beneficios fiscais', "Pagina estrutural por UF.", body, "estados")
    if has_pack:
        body = f"""
{hero(f'{display_name}: ICMS e beneficios fiscais', 'Legislação estadual em tela: ICMS, benefícios fiscais, alíquotas, ST, documentos e prova por assunto.', state["uf"])}
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
        return layout(path, f'{display_name}: ICMS e beneficios fiscais', "ICMS estadual em tela por UF.", body, "estados")
    body = f"""
{hero(f'{display_name}: ICMS e beneficios fiscais', 'Leitura estadual: RICMS, leis, decretos, beneficios, aliquotas, ST, atos infralegais e prova.', state["uf"])}
<section class="law-ledger">
  <div>
    <h2>Estado do estudo</h2>
    <p>Pagina estadual em preparacao. O texto legal sera publicado por capitulos antes de qualquer conclusao operacional.</p>
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
<section class="matrix-section">
  <h2>Matriz estadual de trabalho</h2>
  <div class="matrix-grid">
    <article class="matrix-card"><h3>ICMS material</h3><p>Localize fato gerador, contribuinte, responsavel, base, aliquota, diferimento, ST e obrigacoes acessorias.</p></article>
    <article class="matrix-card"><h3>Beneficios fiscais</h3><p>Classifique o favor fiscal: isencao, reducao de base, credito outorgado, suspensao, regime especial ou incentivo condicionado.</p></article>
    <article class="matrix-card"><h3>Documento e SPED</h3><p>Confira NF-e, CT-e, MDF-e, cBenef quando houver, EFD, ajustes e memoria de calculo.</p></article>
    <article class="matrix-card"><h3>Risco comum</h3><p>Nao aplique beneficio por semelhanca comercial. Produto, operacao, destinatario, vigencia e condicao precisam caber no texto legal.</p></article>
  </div>
</section>
{state_inventory_sections(inv, verified_on, current_path=path)}
<section class="continuity">
  <h2>Continuar a leitura</h2>
  <div>
    <a href="goias.html">Ver modelo publicado de Goias</a>
    <a href="../confaz/index.html">Entender CONFAZ e beneficios</a>
    <a href="../federal/pis-cofins.html">Conectar com PIS/Cofins</a>
    <a href="../biblioteca/index.html">Consultar manuais e painel</a>
  </div>
</section>
"""
    return layout(path, f'{display_name}: ICMS e beneficios fiscais', "Pagina estrutural por UF.", body, "estados")


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
            "title": f'{state_display_name(state)}: ICMS e beneficios fiscais',
            "url": state_href(state["uf"]),
            "summary": (
                "Goias publicado com ICMS, beneficios fiscais, cBenef, RCTE, prova e leitura legal."
                if state["uf"] == "GO"
                else "Pagina estadual com legislação de ICMS em tela, beneficios, documento e prova."
                if state_has_legal_pack(state["uf"])
                else "Pagina estadual estruturada para futura publicacao por UF, com foco em ICMS, beneficios, documento e prova."
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


def write(path: str, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    if path.endswith(".html"):
        content = polish_html_text(content)
    clean = "\n".join(line.rstrip() for line in content.splitlines()) + "\n"
    target.write_text(clean, encoding="utf-8", newline="\n")


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
    write("estados/index.html", estados_index(data))
    for state in data["states"]:
        write(state_href(state["uf"]), state_page(state, data))
    write("federal/index.html", federal_index(data))
    for topic in data["topics"]:
        if topic["path"] in {"estados/goias.html", "confaz/index.html", "folha-clt/index.html"}:
            continue
        if topic["path"].startswith("federal/"):
            extra = federal_inventory_sections(data, TOPIC_THEME_MAP.get(topic["id"], []), data["site"]["verified_on"], compact=True, current_path=topic["path"])
            write(topic["path"], topic_page(topic, "federal", extra))
    for page in FEDERAL_EXTRA_PAGES:
        write(page["path"], federal_theme_page(data, page))
    write("federal/acervo.html", federal_acervo_page(data))
    write("confaz/index.html", topic_page(next(t for t in data["topics"] if t["id"] == "confaz-atos-beneficios"), "confaz"))
    folha_topic = next(t for t in data["topics"] if t["id"] == "folha-clt-previdencia")
    folha_extra = federal_inventory_sections(data, TOPIC_THEME_MAP.get(folha_topic["id"], []), data["site"]["verified_on"], compact=True, current_path="folha-clt/index.html")
    write("folha-clt/index.html", topic_page(folha_topic, "folha", folha_extra))
    write("biblioteca/index.html", biblioteca(data))
    for legal_path, legal_content in build_legal_pages(layout).items():
        write(legal_path, legal_content)
    for state_legal_path, state_legal_content in build_state_legal_pages(layout, data).items():
        write(state_legal_path, state_legal_content)
    write("assets/portal-search.js", search_index(data))
    print("Portal generated successfully.")


if __name__ == "__main__":
    main()
