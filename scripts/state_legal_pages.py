#!/usr/bin/env python3
"""Render state ICMS legal pages from the local official-law corpus."""

from __future__ import annotations

import hashlib
import json
import os
import re
import unicodedata
from functools import lru_cache
from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BD_ROOT = Path(os.environ.get("RJC_BD_LEGISLACAO", r"C:\Users\kris2\OneDrive\COWORK\BD_LEGISLACAO"))
STATE_MAIN = BD_ROOT / "#ESTADUAIS-COMPILADO-NOTEBOOKLM"
STATE_COMPLEMENT = BD_ROOT / "Estados_Complementar"
CURATION_FILE = ROOT / "data" / "state_curadoria.json"
SOURCE_PACK_ROOT = ROOT / "data" / "fontes-estaduais-curadas"
UPDATED_ON = "25/04/2026"

STATE_NAMES = {
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

STATE_OFFICIAL_PORTALS = {
    "AC": "https://sefaz.ac.gov.br/",
    "AL": "https://www.sefaz.al.gov.br/",
    "AP": "https://www.sefaz.ap.gov.br/",
    "AM": "https://www.sefaz.am.gov.br/",
    "BA": "https://www.sefaz.ba.gov.br/",
    "CE": "https://www.sefaz.ce.gov.br/",
    "DF": "https://www.receita.fazenda.df.gov.br/",
    "ES": "https://sefaz.es.gov.br/legislacao-online",
    "GO": "https://goias.gov.br/economia/categoria/institucional/legislacao/tributaria/",
    "MA": "https://sistemas1.sefaz.ma.gov.br/portalsefaz/",
    "MT": "https://www.sefaz.mt.gov.br/",
    "MS": "https://www.sefaz.ms.gov.br/legislacao/",
    "MG": "http://www.fazenda.mg.gov.br/empresas/legislacao_tributaria/",
    "PA": "https://www.sefa.pa.gov.br/legislacao/",
    "PB": "https://www.sefaz.pb.gov.br/legislacao",
    "PR": "https://www.fazenda.pr.gov.br/",
    "PE": "https://www.sefaz.pe.gov.br/Legislacao/Tributaria/Paginas/default.aspx",
    "PI": "https://portal.sefaz.pi.gov.br/documentos/legislacao/",
    "RJ": "https://portal.fazenda.rj.gov.br/legislacao-tributaria/",
    "RN": "https://www.set.rn.gov.br/",
    "RS": "https://www.legislacao.sefaz.rs.gov.br/",
    "RO": "https://portal.sefin.ro.gov.br/legislacao",
    "RR": "https://www.sefaz.rr.gov.br/",
    "SC": "https://legislacao.sef.sc.gov.br/",
    "SP": "https://legislacao.fazenda.sp.gov.br/",
    "SE": "https://www.sefaz.se.gov.br/",
    "TO": "https://www.to.gov.br/sefaz/legislacao-tributaria/",
}

CATEGORY_LABELS = {
    "RICMS": "Regulamento do ICMS",
    "ICMS_LEIS": "Leis do ICMS",
    "ICMS_DECRETOS": "Decretos do ICMS",
    "ICMS_BENEFICIOS": "Benefícios fiscais de ICMS",
    "ICMS_ST": "Substituição tributária",
    "ICMS_ALIQUOTAS": "Alíquotas de ICMS",
    "ICMS_ANEXOS": "Anexos do ICMS",
    "DECRETOS": "Decretos com reflexo no ICMS",
    "LEIS": "Leis com reflexo no ICMS",
    "INSTRUCOES_NORMATIVAS": "Instruções normativas",
    "PORTARIAS": "Portarias",
    "RESOLUCOES": "Resoluções",
    "OUTROS": "Atos complementares",
}

ICMS_NAMED_CATEGORIES = {
    "RICMS",
    "ICMS_LEIS",
    "ICMS_DECRETOS",
    "ICMS_BENEFICIOS",
    "ICMS_ST",
    "ICMS_ALIQUOTAS",
    "ICMS_ANEXOS",
}

ICMS_FALLBACK_CATEGORIES = {"LEIS", "DECRETOS", "INSTRUCOES_NORMATIVAS", "PORTARIAS", "RESOLUCOES", "OUTROS"}

NON_ICMS_SCOPE_TERMS = {
    "Taxas": ["taxa", "taxas", "emolumento", "emolumentos", "prestacao de servicos", "poder executivo"],
    "IPVA": ["ipva", "propriedade de veiculos automotores"],
    "ITCMD/ITCD": ["itcmd", "itcd", "transmissao causa mortis", "doacao"],
}

SOURCE_SCOPE_TERMS = {
    "ICMS": ["icms/", "/icms", "ricms", "regulamento_do_icms", "regulamento do icms"],
    "Taxas": ["taxas/", "/taxas", "_taxas", "taxas_", "lei_taxas", "regulamento das taxas"],
    "IPVA": ["ipva/", "/ipva", "_ipva", "ipva_"],
    "ITCMD/ITCD": ["itcmd/", "/itcmd", "itcd/", "/itcd", "_itcmd", "_itcd"],
}

GROUP_DEFS = [
    {
        "id": "icms",
        "path": "icms.html",
        "title": "ICMS completo",
        "eyebrow": "Regra maior",
        "summary": "RICMS, leis materiais, decretos e anexos que formam a base de incidência, apuração e documentação do ICMS estadual.",
        "categories": {"RICMS", "ICMS_LEIS", "ICMS_DECRETOS", "ICMS_ANEXOS"},
        "needles": ["icms", "fato gerador", "base de cálculo", "base de calculo", "contribuinte", "regulamento"],
        "lesson": "Leia primeiro a incidência, depois contribuinte, responsável, base, alíquota, crédito, apuração e documento. Benefício só entra depois da regra maior.",
    },
    {
        "id": "beneficios",
        "path": "beneficios-fiscais.html",
        "title": "Benefícios fiscais de ICMS",
        "eyebrow": "Exceções legais",
        "summary": "Isenção, redução de base, crédito presumido/outorgado, diferimento, suspensão, fundos, regimes especiais e condicionantes.",
        "categories": {"ICMS_BENEFICIOS", "ICMS_ANEXOS", "RICMS"},
        "needles": ["benefício", "beneficio", "isenção", "isencao", "redução de base", "reducao de base", "crédito presumido", "credito presumido", "crédito outorgado", "credito outorgado", "diferimento", "suspensão", "suspensao"],
        "lesson": "Benefício fiscal é exceção. Só aplique quando produto, NCM, operação, destinatário, período, regime e condição estiverem dentro do texto legal.",
    },
    {
        "id": "aliquotas",
        "path": "aliquotas.html",
        "title": "Alíquotas e base de cálculo",
        "eyebrow": "Carga tributária",
        "summary": "Alíquota interna, interestadual, carga efetiva, redução de base, fundo estadual e formação da base de cálculo.",
        "categories": {"ICMS_ALIQUOTAS", "ICMS_LEIS", "RICMS"},
        "needles": ["alíquota", "aliquota", "base de cálculo", "base de calculo", "fundo", "adicional"],
        "lesson": "Não transforme redução de base em simples troca de alíquota no ERP. A memória deve mostrar base cheia, redução, carga final, crédito e eventual fundo.",
    },
    {
        "id": "st",
        "path": "substituicao-tributaria.html",
        "title": "Substituição tributária",
        "eyebrow": "Responsabilidade",
        "summary": "Responsável, substituído, MVA, pauta, protocolos, convênios, recolhimento e documento fiscal em operações sujeitas a ST.",
        "categories": {"ICMS_ST", "RICMS", "ICMS_ANEXOS"},
        "needles": ["substituição tributária", "substituicao tributaria", "substituto tributário", "substituto tributario", "mva", "pauta"],
        "lesson": "Em ST, separe mercadoria, NCM/CEST, protocolo ou convênio, MVA/pauta, responsável pelo recolhimento e forma de destaque no documento.",
    },
    {
        "id": "prova",
        "path": "documentos-prova.html",
        "title": "Documentos, SPED e prova",
        "eyebrow": "Fiscalização",
        "summary": "NF-e, CT-e, EFD, escrituração, cBenef quando aplicável, obrigações acessórias, comprovantes e memória de cálculo.",
        "categories": {"INSTRUCOES_NORMATIVAS", "PORTARIAS", "RESOLUCOES", "RICMS"},
        "needles": ["documento fiscal", "nota fiscal", "nf-e", "ct-e", "efd", "sped", "escrituração", "escrituracao", "cbenef", "informações complementares", "informacoes complementares"],
        "lesson": "A tese só sobrevive se o XML, a EFD, o cadastro, a memória de cálculo, a guia e o dispositivo legal apontarem para a mesma conclusão.",
    },
]

BENEFIT_SECTOR_DEFS = [
    {
        "id": "agro-alimentos",
        "title": "Agropecuário, alimentos e cesta básica",
        "summary": "Benefícios que normalmente dependem de produto, destinação, produtor rural, insumo, industrialização ou política de abastecimento.",
        "read": "Comece pela mercadoria e pela NCM; depois verifique destinatário, etapa da cadeia, manutenção de crédito e eventual vedação de acumulação.",
        "departments": "Fiscal parametriza CST, CFOP, base e crédito; compras prova origem e destinação; contábil concilia estoque, custo e crédito.",
        "documents": "NF-e de compra e venda, cadastro de produto, NCM, laudo técnico quando houver, pedido/contrato, EFD e memória de cálculo.",
        "risk": "Aplicar benefício de alimento ou insumo agropecuário por descrição comercial, sem confirmar o produto legalmente alcançado.",
        "keywords": [
            "agropecuário", "agropecuario", "produtor rural", "atividade rural", "insumo agropecuário", "insumo agropecuario",
            "fertilizante", "defensivo", "semente", "muda", "ração", "racao", "milho", "soja", "arroz", "feijão", "feijao",
            "leite", "carne", "frango", "peixe", "alimento", "cesta básica", "cesta basica"
        ],
    },
    {
        "id": "eletronicos-informatica-telecom",
        "title": "Eletrônicos, informática e telecomunicações",
        "summary": "Tratamentos ligados a equipamentos eletrônicos, bens de informática, telecomunicações, processamento de dados e cadeia tecnológica.",
        "read": "Leia a descrição legal junto com NCM, industrialização, origem, destinatário e eventual exigência de regime especial ou credenciamento.",
        "departments": "Fiscal controla NCM e documento; comercial valida produto vendido; jurídico confirma enquadramento; TI mantém cadastro e cBenef quando aplicável.",
        "documents": "XML, ficha técnica, NCM, catálogo do produto, contrato, laudo quando necessário, cadastro fiscal e memória do benefício.",
        "risk": "Enquadrar tecnologia por nome de mercado. A lei costuma exigir descrição, código fiscal, uso ou operação específica.",
        "keywords": [
            "eletrônico", "eletronico", "eletrônicos", "eletronicos", "informática", "informatica", "computador", "computadores",
            "software", "hardware", "processamento de dados", "telecomunicação", "telecomunicacao", "telecomunicações",
            "telefonia", "telefone", "celular", "aparelho", "equipamento de comunicação", "equipamento de comunicacao",
            "semicondutor", "componentes eletrônicos", "componentes eletronicos"
        ],
    },
    {
        "id": "veiculos-autopecas-transporte",
        "title": "Veículos, autopeças e transporte",
        "summary": "Benefícios e regimes para veículos, autopeças, transporte, frete, implementos, ônibus, caminhões e cadeias automotivas.",
        "read": "Separe mercadoria de serviço: veículo, peça, frete, ativo imobilizado, transporte de carga e transporte de passageiro têm lógicas diferentes.",
        "departments": "Fiscal valida NCM/CEST e ST; logística prova operação; financeiro guarda guias; contábil concilia ativo, estoque e crédito.",
        "documents": "NF-e, CT-e, MDF-e, RENAVAM/chassi quando aplicável, contrato de frete, EFD, guia e demonstrativo da base.",
        "risk": "Confundir benefício de mercadoria automotiva com regra de prestação de transporte ou substituição tributária.",
        "keywords": [
            "veículo", "veiculo", "veículos", "veiculos", "automotor", "automóvel", "automovel", "autopeça", "autopeca",
            "peças", "pecas", "caminhão", "caminhao", "ônibus", "onibus", "motocicleta", "chassi", "renavam",
            "transporte", "transportador", "frete", "carga", "passageiro", "implemento rodoviário", "implemento rodoviario"
        ],
    },
    {
        "id": "medicamentos-saude",
        "title": "Medicamentos, saúde e produtos hospitalares",
        "summary": "Hipóteses de tratamento favorecido para medicamentos, produtos médico-hospitalares, saúde pública, deficiência e equipamentos assistivos.",
        "read": "Confira produto, registro sanitário quando pertinente, destinatário, finalidade, operação e se a norma exige estorno ou manutenção de crédito.",
        "departments": "Fiscal parametriza item; compras guarda laudos e registros; jurídico valida condição; contábil acompanha crédito e estoque.",
        "documents": "NF-e, NCM, registro ou laudo técnico quando houver, contrato, prescrição ou destinação institucional quando exigida, EFD e memória.",
        "risk": "Ampliar isenção de saúde para produto correlato sem que a descrição legal alcance a mercadoria.",
        "keywords": [
            "medicamento", "medicamentos", "farmacêutico", "farmaceutico", "hospital", "hospitalar", "produto médico",
            "produto medico", "saúde", "saude", "deficiente", "deficiência", "deficiencia", "prótese", "protese",
            "órtese", "ortese", "cadeira de rodas", "insumo hospitalar", "equipamento hospitalar"
        ],
    },
    {
        "id": "energia-combustiveis-infraestrutura",
        "title": "Energia, combustíveis e infraestrutura",
        "summary": "Regras especiais envolvendo energia elétrica, combustíveis, gás, infraestrutura, obras, concessões e cadeias essenciais.",
        "read": "Identifique se a regra trata de mercadoria, fornecimento, uso em processo produtivo, ativo, obra, concessionária ou consumidor final.",
        "departments": "Fiscal separa operação e consumo; engenharia ou operação comprova destinação; financeiro guarda recolhimentos; auditoria cruza contrato e XML.",
        "documents": "Contrato, medição, XML, nota de energia ou combustível, laudo de uso, EFD, memória de cálculo e guia quando houver.",
        "risk": "Aproveitar regra de insumo ou infraestrutura fora da destinação prevista no ato estadual.",
        "keywords": [
            "energia elétrica", "energia eletrica", "combustível", "combustivel", "combustíveis", "combustiveis", "diesel",
            "gasolina", "etanol", "álcool", "alcool", "biodiesel", "biocombustível", "biocombustivel", "gás natural",
            "gas natural", "glp", "infraestrutura", "concessão", "concessao", "obra pública", "obra publica"
        ],
    },
    {
        "id": "industria-maquinas-equipamentos",
        "title": "Indústria, máquinas e equipamentos",
        "summary": "Benefícios de desenvolvimento industrial, máquinas, equipamentos, ativo imobilizado, bens de capital, implantação e modernização.",
        "read": "Aplique a matriz: projeto, bem, destinação, prazo, termo de acordo, crédito, diferimento e obrigação de manter o investimento.",
        "departments": "Operações comprova uso; fiscal parametriza entrada e saída; contábil controla ativo; jurídico acompanha regime e contrapartidas.",
        "documents": "Projeto, termo, NF-e, CIAP quando couber, laudo de instalação, EFD, controle de ativo e memória do incentivo.",
        "risk": "Usar benefício de implantação ou ativo para bem sem vinculação ao projeto autorizado ou fora do período de fruição.",
        "keywords": [
            "indústria", "industria", "industrial", "industrialização", "industrializacao", "máquina", "maquina", "máquinas",
            "maquinas", "equipamento", "equipamentos", "bem de capital", "bens de capital", "ativo imobilizado",
            "implantação", "implantacao", "modernização", "modernizacao", "investimento", "parque industrial"
        ],
    },
    {
        "id": "importacao-exportacao-comercio-exterior",
        "title": "Importação, exportação e comércio exterior",
        "summary": "Imunidade, não incidência, suspensão, diferimento, desembaraço, importação por conta e ordem, exportação e regimes ligados ao exterior.",
        "read": "Separe importação de exportação. Na exportação, prove saída e fim específico; na importação, prove desembaraço, adquirente, NCM e regime.",
        "departments": "Comex monta dossiê; fiscal reflete XML e EFD; financeiro guarda tributos; jurídico valida operação triangular ou regime.",
        "documents": "DU-E, DI/DUIMP, invoice, conhecimento, contrato, NF-e, comprovante de embarque, EFD e memória de crédito.",
        "risk": "Tratar operação interna preparatória como exportação sem comprovar fim específico e saída efetiva ao exterior.",
        "keywords": [
            "importação", "importacao", "importado", "desembaraço", "desembaraco", "exportação", "exportacao", "exterior",
            "comércio exterior", "comercio exterior", "drawback", "zona franca", "área de livre comércio",
            "area de livre comercio", "fim específico de exportação", "fim especifico de exportacao"
        ],
    },
    {
        "id": "atacado-comercio-distribuicao",
        "title": "Atacado, comércio e centros de distribuição",
        "summary": "Regimes e benefícios para atacadistas, varejo, distribuição, centrais, comércio, carga efetiva e credenciamentos.",
        "read": "Verifique CNAE, atividade real, volume, destinatários, termo de acordo, vedação de acumulação, fundo e escrituração.",
        "departments": "Comercial informa cadeia; fiscal parametriza carga; financeiro controla fundo; contábil mede margem e aderência ao regime.",
        "documents": "Termo de credenciamento, cadastro, XML, EFD, demonstrativo de apuração, guia do fundo e relatório de vendas.",
        "risk": "Aplicar regime atacadista a operação varejista, venda a consumidor final ou mercadoria excluída.",
        "keywords": [
            "atacadista", "atacado", "comércio atacadista", "comercio atacadista", "varejo", "varejista", "distribuição",
            "distribuicao", "distribuidor", "centro de distribuição", "centro de distribuicao", "central de distribuição",
            "central de distribuicao", "carga efetiva", "regime atacadista"
        ],
    },
    {
        "id": "social-educacao-cultura-entidades",
        "title": "Social, educação, cultura e entidades",
        "summary": "Benefícios vinculados a entidades, assistência, educação, cultura, livros, doações, pessoas com deficiência e políticas públicas.",
        "read": "Leia a finalidade e o sujeito favorecido: muitas regras exigem entidade específica, destinação pública ou vedação de revenda.",
        "departments": "Jurídico valida entidade e finalidade; fiscal documenta CST e fundamento; financeiro guarda doação ou termo; contábil evidencia baixa.",
        "documents": "Contrato, termo de doação, estatuto ou comprovação da entidade, NF-e, declaração de destinação, EFD e fundamento legal.",
        "risk": "Transformar benefício social em regra comercial comum, sem provar a destinação ou o sujeito beneficiado.",
        "keywords": [
            "educação", "educacao", "ensino", "escola", "universidade", "cultura", "livro", "livros", "entidade",
            "filantrópica", "filantropica", "assistência social", "assistencia social", "doação", "doacao",
            "deficiência", "deficiencia", "pessoa com deficiência", "pessoa com deficiencia"
        ],
    },
    {
        "id": "construcao-minerais-madeira",
        "title": "Construção, minerais, madeira e materiais",
        "summary": "Tratamentos para construção civil, minerais, madeira, cimento, cerâmica, aço, materiais e cadeias extrativas.",
        "read": "Defina se a operação é venda de mercadoria, fornecimento com instalação, extração, industrialização ou obra.",
        "departments": "Fiscal separa ICMS/ISS quando necessário; engenharia comprova aplicação; compras guarda origem; contábil concilia estoque e obra.",
        "documents": "NF-e, contrato de obra, laudo, NCM, romaneio, controle de estoque, EFD e memória de base ou crédito.",
        "risk": "Aplicar benefício de material ou mineral a prestação de serviço, obra ou produto fora da descrição legal.",
        "keywords": [
            "construção civil", "construcao civil", "cimento", "cerâmica", "ceramica", "madeira", "mineral", "minério",
            "minerio", "pedra", "areia", "brita", "aço", "aco", "ferro", "metalúrgica", "metalurgica", "material de construção",
            "material de construcao"
        ],
    },
]

SIGNAL_TO_GROUP = {
    "aliquota": "aliquotas",
    "reducao de base": "beneficios",
    "isencao": "beneficios",
    "credito outorgado": "beneficios",
    "diferimento": "beneficios",
    "suspensao": "beneficios",
    "regime especial": "beneficios",
    "protege/fundo": "beneficios",
    "fundo/contrapartida": "beneficios",
    "exportacao": "beneficios",
    "nao incidencia": "icms",
    "substituicao tributaria": "st",
    "efd/sped": "prova",
    "cBenef": "prova",
}

CURATED_CATEGORY_BY_SOURCE_ID = {
    "BA_LEI_7014_1996_ICMS": "ICMS_LEIS",
    "BA_DEC_13780_2012_RICMS": "RICMS",
    "BA_RICMS_ANEXO_1_ST_2026": "ICMS_ST",
    "BA_RICMS_ANEXO_2_RURAL": "ICMS_BENEFICIOS",
    "BA_LEI_7980_2001_DESENVOLVE": "ICMS_BENEFICIOS",
    "BA_DEC_8205_2002_DESENVOLVE": "ICMS_BENEFICIOS",
    "BA_DEC_18802_2018_PROIND": "ICMS_BENEFICIOS",
    "BA_LEI_9829_2005_PRONAVAL": "ICMS_BENEFICIOS",
    "BA_DEC_11015_2008_PRONAVAL": "ICMS_BENEFICIOS",
    "BA_LEI_7025_1997_CREDITO_PRESUMIDO": "ICMS_BENEFICIOS",
    "BA_DEC_6734_1997_CREDITO_PRESUMIDO": "ICMS_BENEFICIOS",
    "BA_DEC_4316_1995_INFORMATICA_ELETRONICA": "ICMS_BENEFICIOS",
    "BA_DEC_18270_2018_BENEFICIOS_LC160": "ICMS_BENEFICIOS",
    "BA_DEC_18288_2018_BENEFICIOS_LC160": "ICMS_BENEFICIOS",
    "BA_PORT_273_2014_EFD_INCENTIVOS": "INSTRUCOES_NORMATIVAS",
    "DF_LEI_1254_1996_ICMS": "ICMS_LEIS",
    "DF_DEC_18955_1997_RICMS": "RICMS",
    "DF_LEI_6225_2018_BENEFICIOS_LC160": "ICMS_BENEFICIOS",
    "DF_LEI_5005_2012_REGIME_APURACAO": "ICMS_BENEFICIOS",
    "DF_DEC_39753_2019_CREDITO_OUTORGADO": "ICMS_BENEFICIOS",
    "DF_DEC_39803_2019_EMPREGADF": "ICMS_BENEFICIOS",
    "DF_DEC_45287_2023_ALHO_CREDITO_OUTORGADO": "ICMS_BENEFICIOS",
    "DF_DEC_18726_1997_AGRO_DIFERIMENTO": "ICMS_BENEFICIOS",
    "DF_DEC_39789_2019_EFD_ICMS_IPI": "INSTRUCOES_NORMATIVAS",
    "DF_LEI_3196_2003_PRODF_II": "ICMS_BENEFICIOS",
    "DF_LEI_3266_2003_PRODF_II_COMPLEMENTAR": "ICMS_BENEFICIOS",
    "DF_DEC_46900_2025_PRODF_DESENVOLVEDF": "ICMS_BENEFICIOS",
    "MT_LEI_7098_1998_ICMS": "ICMS_LEIS",
    "MT_DEC_2212_2014_RICMS": "RICMS",
    "MT_LC_631_2019_BENEFICIOS_LC160": "ICMS_BENEFICIOS",
    "MT_PORT_211_2024_CBENEF": "INSTRUCOES_NORMATIVAS",
    "RN_DEC_31825_2022_RICMS_GERAL": "RICMS",
    "RN_RICMS_ANEXO_001_ISENCAO": "ICMS_BENEFICIOS",
    "RN_RICMS_ANEXO_002_DIFERIMENTO": "ICMS_BENEFICIOS",
    "RN_RICMS_ANEXO_003_CREDITO_PRESUMIDO": "ICMS_BENEFICIOS",
    "RN_RICMS_ANEXO_004_REDUCAO_BASE": "ICMS_BENEFICIOS",
    "RN_RICMS_ANEXO_005_ANTECIPACAO": "ICMS_ST",
    "RN_RICMS_ANEXO_007_ST": "ICMS_ST",
    "RN_RICMS_ANEXO_008_ST_COMBUSTIVEIS": "ICMS_ST",
    "RN_RICMS_ANEXO_009_TRIGO": "ICMS_ST",
    "RN_RICMS_ANEXO_010_VEICULOS": "ICMS_ST",
    "RN_RICMS_ANEXO_011_DOCUMENTOS": "INSTRUCOES_NORMATIVAS",
    "RN_PORT_022_2018_BENEFICIOS_LC160": "ICMS_BENEFICIOS",
    "RN_LEI_10640_2019_PROEDI": "ICMS_BENEFICIOS",
    "RN_DEC_29420_2019_PROEDI": "ICMS_BENEFICIOS",
    "RN_DEC_27608_2017_FUNDERN": "ICMS_BENEFICIOS",
    "RN_DEC_26789_2017_ATACADISTAS": "ICMS_BENEFICIOS",
    "RN_LEI_12111_2025_TAX_FREE": "ICMS_BENEFICIOS",
    "RN_LEI_11999_2024_ICMS_LC87": "ICMS_LEIS",
    "RN_PORT_970_2025_CBENEF": "INSTRUCOES_NORMATIVAS",
    "PR_LEI_11580_1996_ICMS": "ICMS_LEIS",
    "PR_DEC_7871_2017_RICMS": "RICMS",
    "PR_PORTAL_BENEFICIOS_GERAIS": "ICMS_BENEFICIOS",
    "PR_CODIGO_BENEFICIO_FISCAL": "INSTRUCOES_NORMATIVAS",
    "PR_TABELA_CBENEF_CST": "INSTRUCOES_NORMATIVAS",
    "PR_NPF_53_2018_CBENEF": "INSTRUCOES_NORMATIVAS",
    "PR_PROGRAMA_PARANA_COMPETITIVO": "ICMS_BENEFICIOS",
    "PR_DEC_7721_2024_PARANA_COMPETITIVO": "ICMS_BENEFICIOS",
    "ES_LEI_7000_2001_ICMS": "ICMS_LEIS",
    "ES_DEC_1090_2002_RICMS": "RICMS",
    "ES_LEI_10550_2016_INVEST_ES": "ICMS_BENEFICIOS",
    "ES_LEI_10568_2016_COMPETE_ES": "ICMS_BENEFICIOS",
    "ES_LEI_10574_2016_COMPETE_INVEST": "ICMS_BENEFICIOS",
    "ES_LEI_2508_1970_FUNDAP": "ICMS_BENEFICIOS",
    "ES_TABELA_CBENEF_2026": "INSTRUCOES_NORMATIVAS",
    "MG_LEI_6763_1975_ICMS": "ICMS_LEIS",
    "MG_DEC_48589_2023_RICMS_REGULAMENTO": "RICMS",
    "MG_RICMS_2023_ANEXO_I_ALIQUOTAS": "ICMS_ALIQUOTAS",
    "MG_RICMS_2023_ANEXO_II_REDUCAO_BASE": "ICMS_BENEFICIOS",
    "MG_RICMS_2023_ANEXO_III_CREDITO_ACUMULADO": "ICMS_BENEFICIOS",
    "MG_RICMS_2023_ANEXO_IV_CREDITO_PRESUMIDO": "ICMS_BENEFICIOS",
    "MG_RICMS_2023_ANEXO_V_DOCUMENTOS_EFD": "INSTRUCOES_NORMATIVAS",
    "MG_RICMS_2023_ANEXO_VI_DIFERIMENTO": "ICMS_BENEFICIOS",
    "MG_RICMS_2023_ANEXO_VII_ST": "ICMS_ST",
    "MG_RICMS_2023_ANEXO_VIII_DISPOSICOES_ESPECIAIS": "ICMS_BENEFICIOS",
    "RJ_LEI_2657_1996_ICMS": "ICMS_LEIS",
    "RJ_DEC_27427_2000_RICMS_LIVRO_I_OBRIGACAO_PRINCIPAL": "RICMS",
    "RJ_DEC_27427_2000_RICMS_LIVRO_II_ST": "ICMS_ST",
    "RJ_DEC_27427_2000_RICMS_LIVRO_III_CREDITO_ACUMULADO": "ICMS_BENEFICIOS",
    "RJ_DEC_27427_2000_RICMS_LIVRO_IV_TRANSPORTE": "RICMS",
    "RJ_DEC_27427_2000_RICMS_LIVRO_V_DOCUMENTOS_ANTIGOS": "INSTRUCOES_NORMATIVAS",
    "RJ_DEC_27427_2000_RICMS_LIVRO_VI_OBRIGACOES_ACESSORIAS": "INSTRUCOES_NORMATIVAS",
    "RJ_DEC_27427_2000_RICMS_LIVRO_IX_TRANSPORTE_SERVICOS": "RICMS",
    "RJ_DEC_27427_2000_RICMS_LIVRO_X_REGIMES_ESPECIAIS": "ICMS_BENEFICIOS",
    "RJ_DEC_27427_2000_RICMS_LIVRO_XI_IMPORTACAO": "RICMS",
    "RJ_DEC_27427_2000_RICMS_LIVRO_XII_COMBUSTIVEIS": "ICMS_ST",
    "RJ_DEC_27427_2000_RICMS_LIVRO_XIII_VEICULOS": "ICMS_ST",
    "RJ_DEC_27815_2001_MANUAL_BENEFICIOS": "ICMS_BENEFICIOS",
    "RJ_LEI_4531_2005_SETORIAL_INDUSTRIA": "ICMS_BENEFICIOS",
    "RJ_LEI_8890_2020_REPETRO": "ICMS_BENEFICIOS",
    "RJ_LEI_8645_2019_FOT": "ICMS_BENEFICIOS",
    "RJ_PORTAL_FEEF_FOT_2026": "ICMS_BENEFICIOS",
    "RJ_PORTAL_TRANSPARENCIA_BENEFICIOS_2026": "ICMS_BENEFICIOS",
    "RJ_ROTEIRO_BENEFICIOS_FISCAIS_TRANSPARENCIA_2025": "ICMS_BENEFICIOS",
    "RJ_MANUAL_DOCUMENTOS_BENEFICIOS_2025": "INSTRUCOES_NORMATIVAS",
    "RJ_TABELA_CODIGO_BENEFICIO_CST_2026": "INSTRUCOES_NORMATIVAS",
    "RJ_RES_SEFAZ_604_2024_EFD_BENEFICIOS": "INSTRUCOES_NORMATIVAS",
    "RJ_RES_SEFAZ_668_2024_SELF_STORAGE": "ICMS_BENEFICIOS",
    "RJ_RES_SEFAZ_754_2025_CCREDPRESUMIDO": "INSTRUCOES_NORMATIVAS",
    "RJ_RES_SEFAZ_766_2025_REPETRO_EFD": "INSTRUCOES_NORMATIVAS",
}

BA_CHAPTERS = [
    {
        "id": "icms-regra-matriz",
        "title": "ICMS/BA: incidência, não incidência e contribuinte",
        "summary": "A regra maior da Bahia: quando o ICMS nasce, quando não nasce e quem responde pelo imposto.",
        "theme": "Regra matriz",
        "refs": [
            {"source": "BA_LEI_7014_1996_ICMS", "articles": ["1", "2", "3", "4", "5", "6"]},
            {"source": "BA_DEC_13780_2012_RICMS", "articles": ["1", "2", "5"]},
        ],
        "analysis": [
            "A leitura começa pela Lei nº 7.014/1996. Ela fixa o campo do ICMS baiano: circulação de mercadorias, transporte intermunicipal e interestadual e comunicação. Sem essa pergunta inicial, qualquer benefício vira palpite.",
            "A não incidência do art. 3º deve ser separada de isenção. Na não incidência, o fato tributável não entra no campo do imposto; na isenção, o fato entra, mas a lei afasta a cobrança dentro de condições fechadas.",
            "O RICMS entra como manual operacional: cadastro, inscrição, substituto/responsável e controle documental. A empresa precisa ligar o dispositivo legal à inscrição estadual, ao XML, à EFD e ao responsável pelo recolhimento.",
        ],
        "departments": "Fiscal define CFOP, CST/CSOSN, destinatário, contribuinte e responsável. Cadastro garante inscrição e regime. Jurídico valida não incidência, imunidade, responsabilidade e risco de autuação.",
        "documents": "NF-e, CT-e, cadastro CAD-ICMS, contrato, pedido, comprovante de circulação/prestação, inscrição estadual, EFD e memória de enquadramento.",
        "risks": "Chamar de benefício aquilo que é não incidência; aplicar regra de contribuinte habitual a operação eventual sem ler as exceções; tratar substituto tributário como simples emissor de documento.",
    },
    {
        "id": "base-aliquota-apuracao",
        "title": "Base de cálculo, alíquotas, adicional e apuração",
        "summary": "Como a operação vira base tributável, qual alíquota se aplica e como a Bahia trata carga efetiva e adicional.",
        "theme": "Carga tributária",
        "refs": [
            {"source": "BA_LEI_7014_1996_ICMS", "articles": ["15", "16", "16-A", "17", "18", "19"]},
            {"source": "BA_DEC_13780_2012_RICMS", "keywords": ["base de cálculo", "alíquota", "apuração", "recolhimento"]},
        ],
        "analysis": [
            "A alíquota não pode ser cadastrada isoladamente. Primeiro vem a base; depois a alíquota; depois adicionais, reduções, crédito, fundo e forma de apuração.",
            "A Bahia usa alíquotas gerais, alíquotas específicas e adicional vinculado ao Fundo Estadual de Combate e Erradicação da Pobreza. Isso exige que o ERP mostre base cheia, adicional, carga final e fundamento.",
            "Quando houver redução de base, o correto não é simplesmente trocar a alíquota. A memória deve demonstrar a base reduzida e a carga efetiva, preservando eventual estorno ou manutenção de crédito.",
        ],
        "departments": "Fiscal parametriza base, alíquota, adicional e CST. Contábil concilia imposto, custo e crédito. Financeiro confere DAE/GNRE. Auditoria cruza XML, EFD e recolhimento.",
        "documents": "XML, cadastro NCM, tabela de alíquota, memória de cálculo, EFD, DAE, GNRE, guia de fundo quando aplicável e demonstrativo de carga efetiva.",
        "risks": "Aplicar alíquota vigente a período anterior; esquecer adicional de fundo; registrar redução de base como alíquota menor; deixar o crédito incompatível com a regra de benefício.",
    },
    {
        "id": "beneficios-matriz-lc160",
        "title": "Benefícios fiscais: matriz, LC 160 e Convênio ICMS 190/2017",
        "summary": "Como a Bahia documenta os benefícios fiscais e financeiro-fiscais reinstituídos, listados e conectados ao CONFAZ.",
        "theme": "Benefícios fiscais",
        "refs": [
            {"source": "BA_DEC_18270_2018_BENEFICIOS_LC160", "articles": ["1"]},
            {"source": "BA_DEC_18270_2018_BENEFICIOS_LC160", "keywords": ["ANEXO ÚNICO", "PROBAHIA", "crédito presumido", "redução de base", "DESENVOLVE"]},
            {"source": "BA_DEC_18288_2018_BENEFICIOS_LC160", "keywords": ["benefícios fiscais", "Convênio ICMS 190", "Anexo Único"]},
        ],
        "analysis": [
            "Na Bahia, o estudo dos benefícios começa pela lista de atos normativos publicada no Decreto nº 18.270/2018. Ele não é o benefício em si; é o mapa de atos que precisam ser lidos para saber o benefício, o setor, o dispositivo e a vigência.",
            "A LC 160/2017 e o Convênio ICMS 190/2017 são a camada de convalidação/reinstituição. A pergunta prática é: o benefício está listado, o ato-base está em vigor, o contribuinte cumpre as condições e a fruição aparece corretamente na EFD?",
            "Benefício fiscal é exceção. Ele precisa de operação, produto, setor, ato, período, condição, prova e forma de escrituração. Sem isso, a tese fica vulnerável.",
        ],
        "departments": "Jurídico identifica o ato e vigência. Fiscal parametriza CST, ajustes e EFD. Controladoria mede impacto. Financeiro guarda recolhimentos e contrapartidas.",
        "documents": "Ato concessivo quando houver, decreto/lei do benefício, relação da LC 160, XML, EFD, resolução, termo, guia, memória de cálculo e evidência de cumprimento das condições.",
        "risks": "Usar a relação do Decreto nº 18.270/2018 como se ela substituísse o ato material; aplicar benefício listado mas vencido; acumular benefícios vedados; não provar a contrapartida.",
    },
    {
        "id": "desenvolve",
        "title": "DESENVOLVE: diferimento, dilação de prazo, desconto e obrigações",
        "summary": "O principal programa baiano de desenvolvimento industrial lido como benefício condicionado e controlável.",
        "theme": "Programa estadual",
        "refs": [
            {"source": "BA_LEI_7980_2001_DESENVOLVE", "articles": ["1", "2", "3", "4", "5", "6"]},
            {"source": "BA_DEC_8205_2002_DESENVOLVE", "articles": ["1", "2", "3", "4", "5", "6", "14", "16", "17", "18", "19", "20"]},
            {"source": "BA_PORT_273_2014_EFD_INCENTIVOS", "keywords": ["Programa Desenvolve", "BA040120", "BA000120", "BA000121", "BA000125"]},
        ],
        "analysis": [
            "O DESENVOLVE não é uma simples redução de imposto. Ele combina política industrial, habilitação, diferimento, dilação de prazo, eventual desconto por liquidação antecipada, resolução do conselho e controle na EFD.",
            "A empresa só deve tratar como benefício aquilo que estiver dentro do projeto aprovado, da resolução, do prazo e da condição. O art. 18 do regulamento é ponto crítico: falta de recolhimento da parcela não incentivada pode fazer perder o direito no mês.",
            "No fechamento mensal, a leitura precisa sair da lei para a escrituração: valor incentivado, saldo devedor passível, piso, parcela com prazo dilatado, recolhimento e eventual fundo devem estar separados.",
        ],
        "departments": "Fiscal calcula incentivo e EFD. Contábil prova investimento e saldo. Financeiro controla vencimentos e liquidação. Jurídico acompanha resolução, prazo e manutenção.",
        "documents": "Projeto, protocolo, resolução, laudo de investimento, EFD E110/E111/E115/E116, DAE, memória do SDPI, guia do fundo quando aplicável e conciliação contábil.",
        "risks": "Usar incentivo fora do projeto aprovado; perder prazo de recolhimento; não informar corretamente na EFD; tratar desconto como remissão sem observar o regulamento.",
    },
    {
        "id": "programas-setoriais",
        "title": "PROIND, PRONAVAL, informática, eletrônica e crédito presumido",
        "summary": "Benefícios setoriais baianos por cadeia econômica, com leitura de programa, ato, condição e prova.",
        "theme": "Setores incentivados",
        "refs": [
            {"source": "BA_DEC_18802_2018_PROIND", "articles": ["1", "2", "3", "4", "5"]},
            {"source": "BA_LEI_9829_2005_PRONAVAL", "articles": ["1", "2", "3", "4"]},
            {"source": "BA_DEC_11015_2008_PRONAVAL", "articles": ["1", "2", "3", "4", "5"]},
            {"source": "BA_DEC_4316_1995_INFORMATICA_ELETRONICA", "keywords": ["informática", "eletrônica", "telecomunicações", "crédito presumido", "diferimento"]},
            {"source": "BA_LEI_7025_1997_CREDITO_PRESUMIDO", "articles": ["1", "2", "3"]},
            {"source": "BA_DEC_6734_1997_CREDITO_PRESUMIDO", "keywords": ["crédito presumido", "processo industrial incentivado", "estorno de crédito"]},
        ],
        "analysis": [
            "Os benefícios setoriais devem ser estudados por cadeia: indústria geral, naval, informática/eletrônica/telecomunicações, crédito presumido e programas substituídos ou listados.",
            "A lei costuma exigir projeto, atividade, produto, investimento, resolução, prazo, piso, estorno ou não apropriação de créditos. A vantagem fiscal nasce da combinação desses elementos.",
            "Quando o benefício envolve crédito presumido, a empresa precisa separar crédito legal, crédito comum, estorno, vedação de acumulação e ajuste na EFD.",
        ],
        "departments": "Fiscal parametriza por produto/setor. Operações comprova industrialização. Contábil controla crédito e estorno. Jurídico valida programa e prazo.",
        "documents": "Ato do programa, resolução, cadastro de produto, NCM, laudo, XML, EFD, demonstrativo de crédito, controle de investimento e memória por estabelecimento.",
        "risks": "Enquadrar setor por nome comercial; usar crédito presumido sem estornar o que a norma veda; aplicar benefício sem resolução; misturar operações incentivadas e não incentivadas.",
    },
    {
        "id": "substituicao-tributaria-antecipacao",
        "title": "Substituição tributária, antecipação e Anexo 1 do RICMS/BA",
        "summary": "Responsabilidade, mercadoria, CEST/NCM, MVA/pauta, antecipação e prova na cadeia.",
        "theme": "Responsabilidade tributária",
        "refs": [
            {"source": "BA_RICMS_ANEXO_1_ST_2026", "full_text": True},
            {"source": "BA_DEC_13780_2012_RICMS", "keywords": ["substituição tributária", "antecipação tributária", "MVA", "pauta fiscal"]},
        ],
        "analysis": [
            "ST e antecipação não são benefícios: são técnicas de responsabilidade e momento de recolhimento. O ponto de partida é identificar mercadoria, NCM/CEST, operação, origem, destino e responsável.",
            "O Anexo 1 deve ser lido como tabela viva de mercadorias sujeitas a substituição ou antecipação. A descrição legal precisa bater com o produto real, e não apenas com uma descrição comercial parecida.",
            "Quando houver adicional de fundo, MVA, pauta ou recolhimento antecipado, a memória precisa reconstruir o cálculo por item.",
        ],
        "departments": "Fiscal controla NCM/CEST, MVA, pauta e CST. Compras valida fornecedor/substituto. Financeiro guarda guias. Auditoria cruza estoque, XML e EFD.",
        "documents": "XML, NCM, CEST, pauta/MVA, GNRE/DAE, EFD, cadastro de item, comprovante de recolhimento e demonstrativo por produto.",
        "risks": "Aplicar ST por semelhança de produto; ignorar adicional de fundo; não controlar ressarcimento/complemento; confundir antecipação parcial com encerramento de cadeia.",
    },
    {
        "id": "rural-cesta-credito",
        "title": "Crédito fiscal rural, cesta básica e cadeias agroalimentares",
        "summary": "Tratamentos do Anexo 2 e leitura de benefícios ligados a produção rural, alimentos e insumos.",
        "theme": "Agro e alimentos",
        "refs": [
            {"source": "BA_RICMS_ANEXO_2_RURAL", "full_text": True},
            {"source": "BA_DEC_18270_2018_BENEFICIOS_LC160", "keywords": ["crédito fiscal nas", "cesta", "alimentos", "produtor rural", "agro"]},
        ],
        "analysis": [
            "Na cadeia agroalimentar, a pergunta nunca é só 'tem benefício?'. É preciso identificar produto, etapa da cadeia, produtor, destinatário, finalidade e manutenção ou estorno de crédito.",
            "Crédito rural e cesta básica exigem leitura literal. A descrição legal do item, a operação e o documento devem apontar para a mesma conclusão.",
        ],
        "departments": "Fiscal parametriza produto e CST. Compras guarda prova de origem. Operações comprova destinação. Contábil controla crédito e estoque.",
        "documents": "NF-e, cadastro NCM, contrato rural, inscrição, EFD, memória de crédito, romaneio e prova de destinação.",
        "risks": "Aplicar benefício por família comercial; não provar destinatário ou finalidade; manter crédito quando a norma manda estornar.",
    },
    {
        "id": "documentos-efd-prova",
        "title": "Documentos fiscais, EFD e prova dos incentivos",
        "summary": "Como a tese aparece no XML, nos registros da EFD e nos códigos de ajuste dos benefícios baianos.",
        "theme": "Prova digital",
        "refs": [
            {"source": "BA_DEC_13780_2012_RICMS", "articles": ["33", "42", "247", "248", "249", "250", "251", "252", "253"]},
            {"source": "BA_PORT_273_2014_EFD_INCENTIVOS", "articles": ["1", "2", "3"]},
        ],
        "analysis": [
            "A tese tributária só existe, para a fiscalização, se aparece no documento certo e na escrituração certa. A Bahia detalha a EFD dos incentivos por registros, códigos e valores declarados.",
            "A Portaria nº 273/2014 é essencial porque conecta benefício material e SPED. Ela indica como declarar crédito presumido, DESENVOLVE, PRONAVAL, PROIND e outros incentivos nos registros E110, E111, E115 e E116.",
            "O código de ajuste não cria direito; ele documenta o direito que a lei já concedeu. Se o ato material não sustenta a operação, o SPED apenas evidencia o erro.",
        ],
        "departments": "Fiscal transmite EFD. TI mantém parâmetros. Contábil concilia ajustes. Financeiro guarda recolhimentos. Auditoria valida cruzamentos.",
        "documents": "XML, EFD, recibo de transmissão, registros E110/E111/E115/E116, tabela de códigos, DAE/GNRE, memória de cálculo e ato legal.",
        "risks": "Informar ajuste sem benefício material; usar código errado; deixar valor de fundo fora do débito especial; transmitir EFD incoerente com o XML.",
    },
    {
        "id": "mapa-revisado-beneficios",
        "title": "Mapa revisado dos benefícios de ICMS da Bahia",
        "summary": "Revisão das espécies e rotas normativas de benefícios baianos: LC 160, DESENVOLVE, PROIND, PRONAVAL, crédito presumido, informática, rural, ST e EFD.",
        "theme": "Inventário de benefícios",
        "refs": [
            {"source": "BA_DEC_18270_2018_BENEFICIOS_LC160", "articles": ["1"]},
            {"source": "BA_DEC_18270_2018_BENEFICIOS_LC160", "keywords": ["ANEXO ÚNICO", "PROBAHIA", "DESENVOLVE", "crédito presumido", "redução de base", "diferimento"]},
            {"source": "BA_DEC_18288_2018_BENEFICIOS_LC160", "keywords": ["Convênio ICMS 190", "Anexo Único", "benefícios fiscais"]},
            {"source": "BA_LEI_7980_2001_DESENVOLVE", "articles": ["1", "2", "3"]},
            {"source": "BA_DEC_18802_2018_PROIND", "articles": ["1", "2", "3"]},
            {"source": "BA_LEI_9829_2005_PRONAVAL", "articles": ["1", "2", "3"]},
            {"source": "BA_LEI_7025_1997_CREDITO_PRESUMIDO", "articles": ["1", "2", "3"]},
            {"source": "BA_DEC_4316_1995_INFORMATICA_ELETRONICA", "keywords": ["informática", "eletrônica", "crédito presumido", "diferimento"]},
            {"source": "BA_RICMS_ANEXO_2_RURAL", "full_text": True},
            {"source": "BA_PORT_273_2014_EFD_INCENTIVOS", "articles": ["1", "2", "3"]},
        ],
        "analysis": [
            "A revisão de benefícios da Bahia foi organizada por rotas normativas. A porta de controle é o Decreto nº 18.270/2018, alterado pelo Decreto nº 18.288/2018, que publica a relação de atos de incentivos e benefícios fiscais ou financeiro-fiscais no ambiente da LC 160/2017 e do Convênio ICMS 190/2017.",
            "A Bahia não concentra todos os benefícios em um único anexo material. O mapa prático precisa separar programas de desenvolvimento, crédito presumido, informática/eletrônica, atividades rurais, substituição tributária/antecipação e escrituração dos incentivos.",
            "A lista de atos da LC 160 não substitui o ato material. Para aplicar o benefício, o leitor deve sair do inventário para a lei, decreto, anexo ou portaria específica, confirmando operação, produto, setor, prazo, condição, vedação, estorno e prova.",
            "No portal, a Bahia fica revisada como matriz de espécies e programas publicados. A exaustão de cada item individual permanece dependente do ato material e de atos modificadores posteriores, por isso a página conecta o inventário aos textos integrais em tela.",
        ],
        "departments": "Jurídico mantém o mapa de atos e vigência. Fiscal transforma cada benefício em CST, CFOP, ajuste e EFD. Contábil controla crédito, estorno e fundo. Financeiro prova recolhimentos e contrapartidas.",
        "documents": "Decreto nº 18.270/2018, Decreto nº 18.288/2018, ato material do programa, XML, EFD, memória de cálculo, resolução/termo quando houver, guias e evidência de condição.",
        "risks": "Tratar o anexo da LC 160 como benefício automático; usar programa sem ato de enquadramento; não escriturar incentivo na EFD; perder prova de condição setorial ou temporal.",
    },
    {
        "id": "fiscalizacao-riscos",
        "title": "Fiscalização, regularidade e perda de benefício",
        "summary": "Pontos de controle que fazem uma tese sobreviver: cadastro, regularidade, cumprimento, prova e coerência.",
        "theme": "Auditoria fiscal",
        "refs": [
            {"source": "BA_DEC_13780_2012_RICMS", "articles": ["18", "27", "31-A", "33", "42"]},
            {"source": "BA_DEC_8205_2002_DESENVOLVE", "articles": ["16", "17", "18", "19", "20"]},
            {"source": "BA_PORT_273_2014_EFD_INCENTIVOS", "keywords": ["confissão de dívida", "Débito Especial", "recolhimento", "beneficiários"]},
        ],
        "analysis": [
            "A fiscalização tende a procurar incoerência: benefício no cadastro mas não no XML; ajuste na EFD mas sem ato; crédito presumido sem estorno; regime com prazo vencido; recolhimento do fundo ausente.",
            "Regularidade é parte da tese. Nos programas condicionados, cumprir investimento, publicar resolução, manter recolhimentos e declarar corretamente pode ser tão importante quanto o dispositivo que concede o benefício.",
            "O padrão de defesa é dossiê por operação ou por programa: lei, ato concessivo, documento fiscal, cálculo, escrituração, pagamento e evidência da condição.",
        ],
        "departments": "Jurídico mantém matriz de risco. Fiscal e contábil fecham a prova mensal. Financeiro valida pagamentos. Diretoria acompanha contrapartidas e prazos.",
        "documents": "Checklists, certidões, resolução, XML, EFD, comprovantes, laudos, atas, contratos, memória de cálculo e parecer de enquadramento.",
        "risks": "Benefício materialmente correto, mas documentalmente frágil; perda mensal por recolhimento parcial; prova espalhada entre áreas; cadastro fiscal desatualizado.",
    },
]

BA_SIGNAL_CHAPTER_MAP = {
    "exportacao": "icms-regra-matriz",
    "nao incidencia": "icms-regra-matriz",
    "aliquota": "base-aliquota-apuracao",
    "reducao de base": "beneficios-matriz-lc160",
    "isencao": "beneficios-matriz-lc160",
    "credito outorgado": "programas-setoriais",
    "diferimento": "desenvolve",
    "suspensao": "beneficios-matriz-lc160",
    "regime especial": "desenvolve",
    "protege/fundo": "documentos-efd-prova",
    "fundo/contrapartida": "documentos-efd-prova",
    "substituicao tributaria": "substituicao-tributaria-antecipacao",
    "efd/sped": "documentos-efd-prova",
    "cBenef": "documentos-efd-prova",
}

DF_CHAPTERS = [
    {
        "id": "icms-regra-matriz",
        "title": "ICMS/DF: incidência, não incidência e contribuinte",
        "summary": "A base de todo estudo no Distrito Federal: campo de incidência, hipóteses de não incidência, momento do fato gerador e sujeito passivo.",
        "theme": "Regra matriz",
        "refs": [
            {"source": "DF_LEI_1254_1996_ICMS", "articles": ["1", "2", "3", "5", "22"]},
            {"source": "DF_DEC_18955_1997_RICMS", "articles": ["1", "2", "3", "5", "12"]},
        ],
        "analysis": [
            "No DF, a Lei nº 1.254/1996 faz o papel de lei material do ICMS. Ela delimita quando a operação entra no campo do imposto, quando fica fora dele e quem assume a posição de contribuinte.",
            "A não incidência, especialmente nas exportações e em situações que a Constituição retira do campo do ICMS, não deve ser tratada como favor fiscal. Ela é uma fronteira da própria competência tributária.",
            "O RICMS/DF transforma essa regra em rotina: inscrição, documento fiscal, escrituração, responsável pelo recolhimento e prova da operação. A interpretação correta sempre conecta lei, regulamento e XML.",
        ],
        "departments": "Fiscal define CFOP, CST/CSOSN, natureza da operação e responsável. Cadastro valida contribuinte e inscrição. Jurídico separa não incidência, imunidade, isenção e responsabilidade.",
        "documents": "NF-e, CT-e, cadastro fiscal, inscrição, contrato, pedido, comprovante de circulação, EFD ICMS/IPI e memória de enquadramento.",
        "risks": "Tratar não incidência como isenção; aplicar benefício antes de saber se o fato gerador existe; esquecer responsabilidade por substituição ou recolhimento antecipado.",
    },
    {
        "id": "base-aliquota-apuracao",
        "title": "Base de cálculo, alíquotas, DIFAL e apuração",
        "summary": "Como a operação vira base tributável, qual alíquota se aplica, quando há diferencial de alíquotas e como o débito é apurado.",
        "theme": "Carga tributária",
        "refs": [
            {"source": "DF_LEI_1254_1996_ICMS", "articles": ["6", "8", "10", "18", "20"]},
            {"source": "DF_DEC_18955_1997_RICMS", "articles": ["34", "46", "48", "49", "51", "74"]},
        ],
        "analysis": [
            "A alíquota só é a terceira pergunta. Antes dela vêm a operação, a base de cálculo e eventuais reduções. Depois dela vêm crédito, apuração, prazo de recolhimento e declaração.",
            "O DIFAL exige atenção própria: destinatário, uso ou consumo, ativo, contribuinte ou não contribuinte e período do fato gerador mudam a leitura prática.",
            "Na auditoria, o cálculo precisa mostrar base cheia, parcela excluída ou reduzida, alíquota nominal, carga efetiva, crédito admitido, débito apurado e recolhimento.",
        ],
        "departments": "Fiscal parametriza base, alíquota, DIFAL e prazo. Contábil concilia débito, crédito e custo. Financeiro guarda DAR/GNRE. Auditoria cruza XML, EFD e recolhimento.",
        "documents": "XML, cadastro NCM, tabela de alíquotas, memória de cálculo, EFD, guia de recolhimento, contrato e demonstrativo por operação.",
        "risks": "Cadastrar alíquota sem ler a base; tratar redução de base como alíquota menor; aplicar DIFAL sem reconstruir destinatário, finalidade e período.",
    },
    {
        "id": "beneficios-matriz-lc160",
        "title": "Benefícios fiscais do DF, LC 160 e Convênio ICMS 190/2017",
        "summary": "A porta de entrada para isenções, reduções, créditos, suspensões e diferimentos no DF, com leitura pela LC 160/2017 e pelos Cadernos do RICMS.",
        "theme": "Benefícios fiscais",
        "refs": [
            {"source": "DF_LEI_6225_2018_BENEFICIOS_LC160", "articles": ["1", "2", "3", "4", "5", "6", "7", "8"]},
            {"source": "DF_DEC_18955_1997_RICMS", "articles": ["6", "7", "8", "9", "10"]},
            {"source": "DF_DEC_18955_1997_RICMS", "keywords": ["Caderno I", "Caderno II", "Caderno III", "Caderno IV", "Caderno V"]},
        ],
        "analysis": [
            "O RICMS/DF organiza benefícios nos Cadernos do Anexo I: isenção, redução de base, crédito presumido, suspensão e diferimento. Esse desenho é didático e deve virar checklist de enquadramento.",
            "A Lei nº 6.225/2018 trata da remissão, reinstituição e adesão aos benefícios no ambiente da LC 160/2017 e do Convênio ICMS 190/2017. Ela não substitui a leitura do ato que concede o benefício; ela mostra a camada de convalidação e reinstituição.",
            "Todo benefício fiscal deve ser lido como exceção condicionada. Produto, operação, destinatário, período, regime, ato concessivo e escrituração precisam apontar para o mesmo fundamento.",
        ],
        "departments": "Jurídico identifica ato, vigência e condições. Fiscal parametriza CST, cBenef quando aplicável, ajustes e EFD. Contábil mede crédito/estorno. Financeiro controla contrapartidas e recolhimentos.",
        "documents": "Ato legal, Caderno aplicável do RICMS, ato concessivo quando houver, XML, EFD, memória de cálculo, comprovantes e dossiê de cumprimento das condições.",
        "risks": "Usar a lista da LC 160 como se fosse autorização material suficiente; acumular benefícios vedados; não provar condição, prazo ou escrituração.",
    },
    {
        "id": "regime-especial-apuracao",
        "title": "Regime especial de apuração e crédito outorgado",
        "summary": "Regime especial, atacado, cálculo favorecido, crédito outorgado, condições de fruição e perda do benefício.",
        "theme": "Regimes especiais",
        "refs": [
            {"source": "DF_LEI_5005_2012_REGIME_APURACAO", "articles": ["1", "2", "3", "4", "8", "9"]},
            {"source": "DF_DEC_39753_2019_CREDITO_OUTORGADO", "articles": ["1", "2", "3", "4"]},
        ],
        "analysis": [
            "O regime especial de apuração não é desconto livre. A lei define quem pode usar, como calcular, quais operações entram, quais ficam fora e em que situações o contribuinte perde o tratamento.",
            "O crédito outorgado deve ser lido como técnica de apuração. Ele altera o resultado fiscal dentro de condições fechadas, normalmente com controle por estabelecimento, mercadoria, operação e período.",
            "Para o atacado, a leitura operacional precisa separar venda interestadual, entrada, saída interna, substituição tributária, item excluído e documentação de fruição.",
        ],
        "departments": "Fiscal controla enquadramento, cálculo e EFD. Comercial e cadastro validam cliente, UF e operação. Contábil acompanha margem e crédito. Jurídico revisa condições e risco de exclusão.",
        "documents": "Termo, autorização ou enquadramento, XML por operação, EFD, memória de cálculo, controles de mercadorias excluídas, guias e demonstrativo do crédito outorgado.",
        "risks": "Aplicar regime a mercadoria fora do escopo; deixar de cumprir condição de regularidade; somar crédito outorgado com crédito comum vedado; não segregar operações.",
    },
    {
        "id": "emprega-df-prodf-desenvolve",
        "title": "EMPREGA-DF, PRÓ-DF II e Desenvolve-DF",
        "summary": "Programas de desenvolvimento econômico do DF: incentivo, crédito presumido, diferimento, projeto, investimento, emprego e prova de cumprimento.",
        "theme": "Programas estaduais",
        "refs": [
            {"source": "DF_DEC_39803_2019_EMPREGADF", "articles": ["1", "2", "3", "5", "8", "9", "10", "18", "24"]},
            {"source": "DF_LEI_3196_2003_PRODF_II", "articles": ["1", "2", "3", "4"]},
            {"source": "DF_LEI_3266_2003_PRODF_II_COMPLEMENTAR", "articles": ["1", "2", "3"]},
            {"source": "DF_DEC_46900_2025_PRODF_DESENVOLVEDF", "articles": ["1", "2", "3", "4", "5"]},
        ],
        "analysis": [
            "Programas de desenvolvimento econômico são benefícios condicionados. O direito nasce da combinação entre lei, regulamento, projeto, aprovação, prazo, metas e manutenção das condições.",
            "O EMPREGA-DF trabalha com estímulo à atividade econômica, emprego e incentivo fiscal. O PRÓ-DF II e o Desenvolve-DF exigem leitura de projeto, benefício autorizado, regularidade e acompanhamento.",
            "A empresa deve montar dossiê por programa: norma, ato de enquadramento, investimento, empregos, localização, recolhimento, EFD, cumprimento de metas e eventual renovação.",
        ],
        "departments": "Jurídico acompanha habilitação e ato concessivo. Controladoria mede investimento e empregos. Fiscal calcula o incentivo. Financeiro controla recolhimentos. RH e operações provam metas.",
        "documents": "Projeto econômico, ato de aprovação, contrato/termo, comprovantes de investimento, folha, EFD, XML, memória de cálculo, certidões, relatórios e guias.",
        "risks": "Reduzir imposto sem ato válido; perder condição por regularidade ou metas; não comprovar emprego/investimento; usar benefício fora do estabelecimento ou atividade aprovada.",
    },
    {
        "id": "beneficios-setoriais-agro-atacado",
        "title": "Benefícios setoriais: atacado, alho, agro e diferimento",
        "summary": "Tratamentos direcionados por setor ou produto, com foco em crédito outorgado, cadeia agropecuária e diferimento.",
        "theme": "Setores incentivados",
        "refs": [
            {"source": "DF_DEC_39753_2019_CREDITO_OUTORGADO", "articles": ["2", "3", "4"]},
            {"source": "DF_DEC_45287_2023_ALHO_CREDITO_OUTORGADO", "articles": ["1", "2", "3", "4"]},
            {"source": "DF_DEC_18726_1997_AGRO_DIFERIMENTO", "articles": ["1", "2", "3", "4", "5"]},
        ],
        "analysis": [
            "Benefício setorial deve ser lido por produto, NCM, etapa da cadeia e destinatário. O nome econômico do setor não substitui a descrição legal.",
            "Crédito outorgado e diferimento não são sinônimos. O primeiro atua na apuração do crédito; o segundo desloca o momento de pagamento ou transfere o recolhimento para etapa posterior.",
            "No agro e em alimentos, a prova costuma depender de origem, destino, finalidade, industrialização, revenda e manutenção ou estorno de créditos.",
        ],
        "departments": "Fiscal parametriza produto, NCM e CST. Compras guarda prova de origem. Operações comprova destinação. Contábil controla crédito, estorno e diferimento.",
        "documents": "XML, cadastro NCM, contrato, romaneio, laudo ou ficha do produto, EFD, memória de cálculo, guia e prova de destinação.",
        "risks": "Aplicar benefício por semelhança comercial; esquecer item excluído; manter crédito quando a norma exige estorno; não provar a etapa da cadeia.",
    },
    {
        "id": "substituicao-tributaria-antecipacao",
        "title": "Substituição tributária, antecipação e responsabilidade",
        "summary": "Responsável, substituto, substituído, recolhimento antecipado, mercadorias sujeitas e prova do imposto retido.",
        "theme": "Responsabilidade tributária",
        "refs": [
            {"source": "DF_LEI_1254_1996_ICMS", "articles": ["24", "46"]},
            {"source": "DF_DEC_18955_1997_RICMS", "articles": ["13", "18", "320", "321", "337"]},
            {"source": "DF_DEC_18955_1997_RICMS", "keywords": ["substituição tributária", "antecipação", "Caderno I do Anexo IV", "Caderno II do Anexo IV"]},
        ],
        "analysis": [
            "Substituição tributária não é benefício; é técnica de responsabilidade e antecipação do recolhimento. A leitura correta começa por mercadoria, operação, UF, NCM/CEST e responsável.",
            "O RICMS/DF organiza mercadorias e hipóteses nos Cadernos do Anexo IV. A tabela precisa conversar com a descrição real do produto e com o documento fiscal.",
            "Quando há antecipação ou ST, a memória deve demonstrar base presumida, MVA ou pauta quando aplicável, crédito, imposto próprio, imposto retido e recolhimento.",
        ],
        "departments": "Fiscal controla NCM/CEST, base, MVA/pauta e CST. Compras valida fornecedor e retenção. Financeiro guarda guia. Auditoria cruza estoque, XML e EFD.",
        "documents": "XML, NCM, CEST, tabela do Anexo IV, MVA/pauta, GNRE/DAR, EFD, cadastro de item e comprovante de recolhimento.",
        "risks": "Aplicar ST por descrição parecida; ignorar complemento ou ressarcimento; tratar antecipação como encerramento de cadeia sem base legal.",
    },
    {
        "id": "documentos-efd-prova",
        "title": "Documentos fiscais, EFD ICMS/IPI e prova",
        "summary": "Como a tese aparece no documento fiscal, na escrituração, nos registros digitais e no dossiê de auditoria.",
        "theme": "Prova digital",
        "refs": [
            {"source": "DF_LEI_1254_1996_ICMS", "articles": ["48", "49", "51"]},
            {"source": "DF_DEC_18955_1997_RICMS", "articles": ["79", "181", "207", "347", "349", "350"]},
            {"source": "DF_DEC_39789_2019_EFD_ICMS_IPI", "articles": ["1", "2", "3", "4", "5", "6", "7"]},
        ],
        "analysis": [
            "A tese tributária precisa aparecer em documento fiscal e escrituração. A lei dá a obrigação, o RICMS detalha documentos e fiscalização, e o decreto da EFD organiza o ambiente digital.",
            "EFD ICMS/IPI não cria o benefício. Ela declara e evidencia o direito que precisa existir na norma material, no ato concessivo e no documento fiscal.",
            "O melhor padrão de controle é o dossiê mensal: lei, ato, XML, EFD, cálculo, guia, prova de condição e conciliação contábil.",
        ],
        "departments": "Fiscal transmite EFD e valida XML. TI mantém parametrização. Contábil concilia ajustes. Financeiro prova pagamento. Auditoria testa coerência.",
        "documents": "NF-e, CT-e, EFD ICMS/IPI, recibo, registros e ajustes, memória de cálculo, guias, cadastro de item, ato legal e comprovantes.",
        "risks": "Declarar ajuste sem direito material; transmitir EFD incoerente com XML; perder prova por falta de dossiê; guardar só link externo e não o texto aplicável.",
    },
    {
        "id": "mapa-revisado-beneficios",
        "title": "Mapa revisado dos benefícios de ICMS do Distrito Federal",
        "summary": "Revisão das espécies e rotas normativas do DF: Cadernos do Anexo I, LC 160, regime especial, crédito outorgado, EMPREGA-DF, PRÓ-DF, Desenvolve-DF e EFD.",
        "theme": "Inventário de benefícios",
        "refs": [
            {"source": "DF_DEC_18955_1997_RICMS", "articles": ["6", "7", "7-A", "7-B", "8", "9", "10"]},
            {"source": "DF_DEC_18955_1997_RICMS", "keywords": ["Caderno I", "Caderno II", "Caderno III", "Caderno IV", "Caderno V", "Anexo I"]},
            {"source": "DF_LEI_6225_2018_BENEFICIOS_LC160", "articles": ["1", "2", "3", "4", "5", "6", "7", "8"]},
            {"source": "DF_LEI_5005_2012_REGIME_APURACAO", "articles": ["1", "2", "3", "4", "8"]},
            {"source": "DF_DEC_39753_2019_CREDITO_OUTORGADO", "articles": ["1", "2", "3", "4"]},
            {"source": "DF_DEC_39803_2019_EMPREGADF", "articles": ["1", "2", "3", "5", "8", "18", "24"]},
            {"source": "DF_DEC_46900_2025_PRODF_DESENVOLVEDF", "articles": ["1", "2", "3", "4", "5"]},
            {"source": "DF_DEC_39789_2019_EFD_ICMS_IPI", "articles": ["1", "2", "3", "4", "5", "6", "7"]},
        ],
        "analysis": [
            "No Distrito Federal, a revisão exaustiva começa nos arts. 6º a 10 do RICMS/DF. Eles apontam as espécies centrais e seus Cadernos no Anexo I: isenção, redução de base, crédito presumido, suspensão e diferimento.",
            "A Lei nº 6.225/2018 organiza remissão, reinstituição e adesão no ambiente da LC 160/2017 e do Convênio ICMS 190/2017. Essa camada valida o mapa, mas cada uso concreto depende do item do Caderno ou do ato especial.",
            "Os regimes e programas do DF ficam em trilhas próprias: Lei nº 5.005/2012, Decreto nº 39.753/2019, EMPREGA-DF, PRÓ-DF II, Desenvolve-DF, agro/diferimento e EFD ICMS/IPI.",
            "Para fins práticos, o benefício do DF deve ser classificado primeiro por espécie, depois por programa ou Caderno, e só então por operação, produto, destinatário, condição, código/escrituração e documento de prova.",
        ],
        "departments": "Jurídico identifica Caderno, programa e vigência. Fiscal parametriza CST, ajustes e EFD. Contábil controla crédito/estorno. Financeiro guarda guias e contrapartidas. Operações prova destino e condição.",
        "documents": "RICMS/DF, Caderno aplicável, Lei nº 6.225/2018, ato de regime/programa, XML, EFD, memória de cálculo, comprovante de condição e guia.",
        "risks": "Aplicar benefício por nome econômico; não abrir o Caderno correto; usar regime sem cumprir condição; declarar EFD sem fundamento material.",
    },
    {
        "id": "fiscalizacao-riscos",
        "title": "Fiscalização, perda de benefício e defesa documental",
        "summary": "Pontos que normalmente decidem a sobrevivência de um benefício: regularidade, condição, prazo, prova e coerência entre sistemas.",
        "theme": "Auditoria fiscal",
        "refs": [
            {"source": "DF_DEC_18955_1997_RICMS", "articles": ["347", "349", "350"]},
            {"source": "DF_LEI_5005_2012_REGIME_APURACAO", "articles": ["8", "9"]},
            {"source": "DF_DEC_39753_2019_CREDITO_OUTORGADO", "articles": ["4"]},
            {"source": "DF_DEC_39803_2019_EMPREGADF", "keywords": ["perda", "cancelamento", "irregularidade", "comprovação", "cumprimento"]},
        ],
        "analysis": [
            "A fiscalização costuma atacar a distância entre tese e prova: benefício no cadastro, mas sem ato; XML divergente da EFD; cálculo sem memória; operação fora do produto ou período.",
            "Programas condicionados exigem acompanhamento vivo. Regularidade fiscal, metas, investimento, emprego, localização e escrituração podem ser tão relevantes quanto a regra que concede o incentivo.",
            "Defesa documental boa nasce antes da autuação. O portal deve ensinar o contribuinte a criar a prova no mês do fato gerador, e não tentar reconstruí-la anos depois.",
        ],
        "departments": "Jurídico mantém matriz de risco. Fiscal e contábil fecham prova mensal. Financeiro valida pagamentos. Diretoria acompanha metas e contrapartidas.",
        "documents": "Checklists, certidões, atos concessivos, XML, EFD, comprovantes, relatórios de metas, contratos, memória de cálculo e parecer de enquadramento.",
        "risks": "Benefício materialmente correto, mas documentalmente frágil; condição vencida; prova espalhada em áreas diferentes; cálculo impossível de reconstruir.",
    },
]

DF_SIGNAL_CHAPTER_MAP = {
    "exportacao": "icms-regra-matriz",
    "nao incidencia": "icms-regra-matriz",
    "aliquota": "base-aliquota-apuracao",
    "reducao de base": "beneficios-matriz-lc160",
    "isencao": "beneficios-matriz-lc160",
    "credito outorgado": "regime-especial-apuracao",
    "diferimento": "beneficios-setoriais-agro-atacado",
    "suspensao": "beneficios-matriz-lc160",
    "regime especial": "regime-especial-apuracao",
    "protege/fundo": "emprega-df-prodf-desenvolve",
    "fundo/contrapartida": "emprega-df-prodf-desenvolve",
    "substituicao tributaria": "substituicao-tributaria-antecipacao",
    "efd/sped": "documentos-efd-prova",
    "cBenef": "documentos-efd-prova",
}

MT_CHAPTERS = [
    {
        "id": "icms-regra-matriz",
        "title": "ICMS/MT: incidência, não incidência e contribuinte",
        "summary": "A leitura de entrada do Mato Grosso: campo do imposto, fato gerador, não incidência, contribuinte e obrigações centrais.",
        "theme": "Regra matriz",
        "refs": [
            {"source": "MT_LEI_7098_1998_ICMS", "articles": ["1", "2", "3", "4", "16", "17"]},
            {"source": "MT_DEC_2212_2014_RICMS", "articles": ["1", "2", "3", "4", "5", "22"]},
        ],
        "analysis": [
            "Em Mato Grosso, o estudo começa pela Lei nº 7.098/1998. Ela consolida a incidência do ICMS, o momento do fato gerador, as hipóteses de não incidência e a posição do contribuinte.",
            "O RICMS/MT, aprovado pelo Decreto nº 2.212/2014, traduz a lei para a rotina fiscal: definição da operação, saída, documento, obrigação acessória, sujeição passiva e controle da prova.",
            "Antes de falar em benefício, é preciso responder se a operação está dentro do campo do ICMS. Se não houver incidência, o tratamento é estrutural; se houver incidência, benefícios e regimes entram como exceções legais.",
        ],
        "departments": "Fiscal define CFOP, CST/CSOSN, operação e responsável. Cadastro valida contribuinte e inscrição. Jurídico separa não incidência, imunidade, isenção e responsabilidade.",
        "documents": "NF-e, CT-e, cadastro fiscal, inscrição estadual, contrato, pedido, prova de circulação, EFD e memória de enquadramento.",
        "risks": "Aplicar benefício antes de confirmar a incidência; confundir não incidência com isenção; tratar contribuinte, responsável e substituto como figuras iguais.",
    },
    {
        "id": "base-aliquota-apuracao",
        "title": "Base de cálculo, alíquotas, crédito e apuração",
        "summary": "Como a operação vira base, qual alíquota se aplica, como o crédito é tomado e como o imposto é apurado no MT.",
        "theme": "Carga tributária",
        "refs": [
            {"source": "MT_LEI_7098_1998_ICMS", "articles": ["6", "14", "24", "25", "30", "31"]},
            {"source": "MT_DEC_2212_2014_RICMS", "articles": ["72", "81", "95", "96", "99", "131"]},
        ],
        "analysis": [
            "Alíquota não resolve sozinha a tributação. A ordem correta é operação, base de cálculo, eventual redução, alíquota, crédito, apuração, prazo e recolhimento.",
            "A não cumulatividade exige memória de crédito. Crédito comum, crédito outorgado, estorno e vedação precisam estar separados para evitar que um benefício fiscal contamine a apuração mensal.",
            "No fechamento, o cálculo precisa conversar com XML, EFD, guia e contabilidade. Quando houver carga reduzida, a prova deve mostrar se a redução veio da base, do crédito ou de regime específico.",
        ],
        "departments": "Fiscal parametriza base, alíquota, crédito e prazo. Contábil concilia imposto, custo e crédito. Financeiro guarda guias. Auditoria cruza XML, EFD e recolhimento.",
        "documents": "XML, cadastro NCM, tabela de alíquotas, memória de cálculo, EFD, guia de recolhimento, demonstrativo de crédito e conciliação contábil.",
        "risks": "Trocar base reduzida por alíquota menor; tomar crédito incompatível com benefício; aplicar alíquota de período errado; não demonstrar a carga efetiva.",
    },
    {
        "id": "beneficios-matriz-lc160",
        "title": "Benefícios fiscais, LC 160 e Convênio ICMS 190/2017",
        "summary": "A matriz de benefícios do MT: remissão, anistia, reinstituição, isenções, reduções, créditos, diferimentos e condições de fruição.",
        "theme": "Benefícios fiscais",
        "refs": [
            {"source": "MT_DEC_2212_2014_RICMS", "articles": ["12", "13", "14", "15", "16", "17", "18", "19", "20", "21"]},
            {"source": "MT_LC_631_2019_BENEFICIOS_LC160", "articles": ["1", "3", "7", "8", "10", "11", "12", "14", "56", "58", "59"]},
            {"source": "MT_DEC_2212_2014_RICMS", "keywords": ["ANEXO IV", "ANEXO V", "ANEXO VI", "ANEXO VII", "isenção", "redução de base", "créditos fiscais", "diferimento"]},
        ],
        "analysis": [
            "A LC nº 631/2019 é a camada de remissão, anistia, reinstituição e disciplina dos benefícios no ambiente da LC 160/2017 e do Convênio ICMS 190/2017.",
            "O RICMS/MT organiza benefícios em anexos: Anexo IV para isenções, Anexo V para reduções de base, Anexo VI para créditos fiscais/outorgados/presumidos e Anexo VII para diferimentos.",
            "Benefício fiscal é exceção condicionada. Produto, operação, destinatário, período, enquadramento, vedação, estorno, contrapartida e escrituração precisam estar no mesmo dossiê.",
        ],
        "departments": "Jurídico identifica ato, vigência e condições. Fiscal parametriza CST, cBenef quando aplicável e ajustes. Contábil mede crédito/estorno. Financeiro controla recolhimentos e fundos.",
        "documents": "LC 631/2019, RICMS/MT, anexo aplicável, XML, EFD, código de benefício, memória de cálculo, ato concessivo quando houver e prova de cumprimento.",
        "risks": "Usar a reinstituição como se fosse o benefício material; acumular benefícios vedados; esquecer estorno; não provar condição ou regularidade.",
    },
    {
        "id": "prodeic-desenvolvimento",
        "title": "PRODEIC, desenvolvimento econômico e regimes incentivados",
        "summary": "Programas e tratamentos de desenvolvimento econômico em Mato Grosso, com foco em crédito, redução, projeto e cumprimento de condições.",
        "theme": "Programas estaduais",
        "refs": [
            {"source": "MT_LC_631_2019_BENEFICIOS_LC160", "articles": ["18", "19", "24", "25", "36", "56"]},
            {"source": "MT_DEC_2212_2014_RICMS", "keywords": ["PRODEIC", "Programa de Desenvolvimento", "tratamento diferenciado", "benefícios fiscais"]},
            {"source": "MT_PORT_211_2024_CBENEF", "keywords": ["Desenvolvimento", "Agroindústria", "Comércio", "Industrial"]},
        ],
        "analysis": [
            "O PRODEIC e os módulos de desenvolvimento não devem ser lidos como simples desconto. Eles dependem de programa, resolução, setor, operação, metas, prazo e manutenção das condições.",
            "A LC nº 631/2019 reorganiza a fruição e os limites de vários benefícios reinstituídos. O contribuinte precisa sair da norma geral para o ato concreto e para a escrituração do benefício usado.",
            "A portaria de cBenef ajuda a transformar o benefício em linguagem de documento fiscal: setor, código, benefício, fundamento e classificação simplificada.",
        ],
        "departments": "Jurídico acompanha enquadramento, ato e vigência. Fiscal calcula incentivo e cBenef. Controladoria mede impacto. Financeiro controla recolhimentos e contrapartidas.",
        "documents": "Resolução, termo, ato concessivo, LC 631/2019, XML, EFD, cBenef, memória de cálculo, certidões, relatório de cumprimento e guias.",
        "risks": "Aplicar incentivo sem ato individual; não comprovar metas; usar código de benefício sem direito material; misturar operação incentivada e não incentivada.",
    },
    {
        "id": "isencoes-reducoes-creditos",
        "title": "Isenções, reduções de base e créditos outorgados",
        "summary": "Leitura dos Anexos IV, V e VI do RICMS/MT: benefício por produto, operação, setor, destinatário e prova.",
        "theme": "Benefícios por espécie",
        "refs": [
            {"source": "MT_DEC_2212_2014_RICMS", "keywords": ["ANEXO IV", "DAS OPERAÇÕES E PRESTAÇÕES ALCANÇADAS POR ISENÇÃO", "ANEXO V", "REDUÇÃO DE BASE DE CÁLCULO", "ANEXO VI", "CRÉDITOS FISCAIS, OUTORGADOS E PRESUMIDOS"]},
            {"source": "MT_PORT_211_2024_CBENEF", "keywords": ["Isenção", "Redução da base de cálculo", "Crédito outorgado", "Crédito presumido"]},
        ],
        "analysis": [
            "Isenção afasta a cobrança em hipótese específica; redução de base reduz a grandeza tributável; crédito outorgado ou presumido altera a apuração. Cada técnica exige prova diferente.",
            "Nos anexos do RICMS/MT, o título do capítulo ajuda, mas não basta. A descrição legal do item deve bater com produto, NCM, operação, destinatário e período.",
            "O cBenef deve ser consequência da norma material. Ele identifica o benefício no documento; não cria direito quando produto, operação ou condição estão fora do texto legal.",
        ],
        "departments": "Fiscal parametriza CST, cBenef e benefício. Cadastro valida NCM e produto. Contábil controla crédito/estorno. Auditoria testa aderência por item.",
        "documents": "XML, cadastro de item, NCM, anexo aplicável, cBenef, EFD, memória de cálculo, comprovação de destinatário e prova de finalidade.",
        "risks": "Usar benefício por semelhança comercial; informar cBenef indevido; manter crédito quando a norma manda estornar; não demonstrar a condição específica.",
    },
    {
        "id": "agro-cesta-diferimento",
        "title": "Agro, cesta básica, diferimento e cadeias produtivas",
        "summary": "Benefícios e diferimentos ligados a produtos de origem vegetal, animal, alimentos, insumos, biodiesel e cadeia agroindustrial.",
        "theme": "Agro e alimentos",
        "refs": [
            {"source": "MT_DEC_2212_2014_RICMS", "keywords": ["cesta básica", "produtos de origem", "reino vegetal", "reino animal", "biodiesel", "ANEXO VII", "DIFERIMENTO"]},
            {"source": "MT_PORT_211_2024_CBENEF", "keywords": ["Agroindústria", "cesta básica", "biodiesel", "carnes", "gado", "produtos vegetais"]},
        ],
        "analysis": [
            "Mato Grosso exige leitura cuidadosa das cadeias agroindustriais. O produto, a etapa, a origem, o destinatário e a finalidade costumam decidir se há isenção, redução, crédito ou diferimento.",
            "Diferimento não é perdão do imposto. Ele desloca o recolhimento para outro momento ou para outro responsável, e precisa de controle documental da etapa posterior.",
            "A cesta básica e os produtos agroalimentares exigem aderência literal à descrição do anexo. O cadastro comercial do ERP não substitui o texto normativo.",
        ],
        "departments": "Fiscal parametriza produto e CST. Compras prova origem. Operações prova destinação. Contábil controla crédito, estorno e diferimento.",
        "documents": "NF-e, NCM, romaneio, contrato, prova de origem/destino, EFD, memória de crédito, anexo aplicável e cBenef quando exigido.",
        "risks": "Aplicar benefício por família comercial; não provar finalidade; tratar diferimento como isenção; perder crédito por falta de controle da cadeia.",
    },
    {
        "id": "st-estimativa-anexos",
        "title": "Substituição tributária, estimativa simplificada e anexos de carga",
        "summary": "Responsabilidade, ST, antecipação, anexos de segmentos, carga média por CNAE e controles de recolhimento.",
        "theme": "Responsabilidade tributária",
        "refs": [
            {"source": "MT_DEC_2212_2014_RICMS", "articles": ["448", "450", "463", "573"]},
            {"source": "MT_DEC_2212_2014_RICMS", "keywords": ["ANEXO X", "substituição tributária", "regime de estimativa simplificado", "ANEXO XIII", "carga tributária média"]},
            {"source": "MT_LEI_7098_1998_ICMS", "articles": ["30", "31"]},
        ],
        "analysis": [
            "ST e antecipação não são benefícios: são técnicas de responsabilidade e momento de recolhimento. A leitura começa por mercadoria, operação, NCM/CEST, segmento e responsável.",
            "O regime de estimativa simplificada e anexos de carga exigem cuidado com CNAE, operação, período e hipótese de encerramento ou não encerramento da fase tributária.",
            "A prova deve reconstruir base, carga, imposto próprio, imposto retido ou antecipado, eventual complemento e escrituração.",
        ],
        "departments": "Fiscal controla NCM/CEST, segmento, base e carga. Compras valida fornecedor e retenção. Financeiro guarda guias. Auditoria cruza estoque, XML e EFD.",
        "documents": "XML, NCM, CEST, CNAE, Anexo X, Anexo XIII, MVA/carga, guia, EFD, cadastro de item e memória por operação.",
        "risks": "Aplicar ST por descrição parecida; ignorar CNAE ou segmento; tratar estimativa como benefício; não controlar complemento ou ressarcimento.",
    },
    {
        "id": "documentos-cbenef-efd-prova",
        "title": "Documentos fiscais, cBenef, EFD e prova",
        "summary": "Como o benefício aparece no XML, nos códigos de benefício, na escrituração e no dossiê mensal de auditoria.",
        "theme": "Prova digital",
        "refs": [
            {"source": "MT_PORT_211_2024_CBENEF", "keywords": ["Código Benefício", "Classificação Simplificada", "MT001", "MT002", "MT003"]},
            {"source": "MT_DEC_2212_2014_RICMS", "articles": ["174", "215", "216", "327", "328"]},
            {"source": "MT_DEC_2212_2014_RICMS", "keywords": ["documento fiscal", "escrituração fiscal", "NF-e", "EFD"]},
        ],
        "analysis": [
            "A tese só sobrevive se o documento fiscal e a escrituração contam a mesma história que a lei. cBenef, CST, CFOP, base, crédito e observações precisam ser coerentes.",
            "O anexo da Portaria nº 211/2024 organiza benefícios por código, descrição e classificação. Ele é ferramenta de prova documental, mas depende do fundamento legal material.",
            "O dossiê mensal deve permitir que alguém refaça o caminho: norma, produto, operação, código, cálculo, XML, EFD e guia.",
        ],
        "departments": "Fiscal emite e escritura. TI mantém parametrização. Contábil concilia ajustes. Financeiro prova pagamento. Auditoria testa coerência.",
        "documents": "NF-e, CT-e, cBenef, EFD, recibos, registros e ajustes, memória de cálculo, guias, cadastro de item e fundamento legal.",
        "risks": "Informar código sem direito material; usar código genérico; transmitir EFD divergente do XML; não guardar a memória do benefício usado.",
    },
    {
        "id": "mapa-revisado-beneficios",
        "title": "Mapa revisado dos benefícios de ICMS de Mato Grosso",
        "summary": "Revisão das espécies e rotas normativas do MT: art. 12 do RICMS, anexos IV a VIII, LC 631/2019, PRODEIC, cBenef, ST e estimativa.",
        "theme": "Inventário de benefícios",
        "refs": [
            {"source": "MT_DEC_2212_2014_RICMS", "articles": ["12", "13", "14", "15", "16", "17", "18", "19", "20", "21"]},
            {"source": "MT_DEC_2212_2014_RICMS", "keywords": ["ANEXO IV", "ANEXO V", "ANEXO VI", "ANEXO VII", "ANEXO VIII", "isenção", "redução de base", "créditos fiscais", "diferimento"]},
            {"source": "MT_LC_631_2019_BENEFICIOS_LC160", "articles": ["1", "3", "7", "8", "10", "11", "12", "14", "18", "19", "24", "25", "56", "58", "59"]},
            {"source": "MT_PORT_211_2024_CBENEF", "keywords": ["Código Benefício", "Isenção", "Redução", "Crédito", "Classificação Simplificada"]},
            {"source": "MT_DEC_2212_2014_RICMS", "keywords": ["ANEXO X", "substituição tributária", "ANEXO XIII", "regime de estimativa simplificado"]},
        ],
        "analysis": [
            "Mato Grosso tem a enumeração mais clara entre os três Estados revisados: o art. 12 do RICMS/MT lista as espécies de benefícios fiscais, incluindo isenção, redução de base, manutenção de crédito, devolução de imposto, crédito outorgado ou presumido, dedução, dispensa, dilação de prazo, antecipação de crédito, financiamento, crédito para investimento, remissão, anistia, moratória, transação, parcelamento favorecido e outras formas de exoneração ou redução do ônus do ICMS.",
            "Os arts. 13 a 16 funcionam como regra comum de fruição: nenhum benefício deve ser aplicado sem observar condições, abatimento do imposto dispensado, vedações e controles de regularidade.",
            "A leitura material se abre nos anexos do RICMS/MT: Anexo IV para isenções, Anexo V para reduções de base, Anexo VI para créditos fiscais/outorgados/presumidos, Anexo VII para diferimentos e Anexo VIII para anistia, remissão e convalidações.",
            "A LC nº 631/2019 organiza a remissão, anistia, reinstituição e fruição de benefícios no ambiente da LC 160/2017. A Portaria nº 211/2024-SEFAZ converte a tese em código de benefício, que precisa estar coerente com o fundamento legal e com o XML.",
        ],
        "departments": "Jurídico mantém a matriz de espécie, anexo e vigência. Fiscal parametriza CST, CFOP, cBenef e EFD. Contábil controla crédito/estorno. Financeiro acompanha recolhimentos, fundos e parcelamentos favorecidos.",
        "documents": "RICMS/MT art. 12 a 21, anexos IV a VIII, LC nº 631/2019, Portaria nº 211/2024, XML, EFD, cBenef, memória de cálculo, ato concessivo quando houver e guia.",
        "risks": "Chamar qualquer incentivo de crédito outorgado; aplicar benefício sem observar art. 13 a 16; usar cBenef sem base material; ignorar anistia/remissão/moratória como espécies listadas no art. 12.",
    },
    {
        "id": "fiscalizacao-riscos",
        "title": "Fiscalização, penalidades e perda de benefício",
        "summary": "Pontos de controle que sustentam ou derrubam benefício: regularidade, condição, prazo, escrituração, prova e defesa.",
        "theme": "Auditoria fiscal",
        "refs": [
            {"source": "MT_LEI_7098_1998_ICMS", "articles": ["35", "39", "45", "47"]},
            {"source": "MT_DEC_2212_2014_RICMS", "articles": ["917", "935", "936", "945"]},
            {"source": "MT_LC_631_2019_BENEFICIOS_LC160", "articles": ["12", "14", "56", "58", "59"]},
        ],
        "analysis": [
            "A fiscalização normalmente procura inconsistência: benefício no XML sem ato, código sem fundamento, crédito sem estorno, regime vencido ou prova dispersa.",
            "Nos benefícios reinstituídos e programas condicionados, regularidade e cumprimento de requisitos são parte da tese. A perda pode surgir por descumprimento operacional, não apenas por interpretação jurídica errada.",
            "A defesa documental deve nascer no mês do fato gerador. Depois da autuação, reconstruir prova de produto, condição, cálculo e escrituração fica caro e frágil.",
        ],
        "departments": "Jurídico mantém matriz de risco. Fiscal e contábil fecham prova mensal. Financeiro valida guias. Diretoria acompanha metas e contrapartidas.",
        "documents": "Checklists, certidões, atos concessivos, XML, EFD, comprovantes, relatórios, contratos, memória de cálculo e parecer de enquadramento.",
        "risks": "Benefício materialmente correto, mas sem prova; condição vencida; código indevido; cálculo impossível de reconstruir; falta de controle por estabelecimento.",
    },
]

MT_SIGNAL_CHAPTER_MAP = {
    "exportacao": "icms-regra-matriz",
    "nao incidencia": "icms-regra-matriz",
    "aliquota": "base-aliquota-apuracao",
    "reducao de base": "isencoes-reducoes-creditos",
    "isencao": "isencoes-reducoes-creditos",
    "credito outorgado": "isencoes-reducoes-creditos",
    "diferimento": "agro-cesta-diferimento",
    "suspensao": "beneficios-matriz-lc160",
    "regime especial": "prodeic-desenvolvimento",
    "protege/fundo": "prodeic-desenvolvimento",
    "fundo/contrapartida": "prodeic-desenvolvimento",
    "substituicao tributaria": "st-estimativa-anexos",
    "efd/sped": "documentos-cbenef-efd-prova",
    "cBenef": "documentos-cbenef-efd-prova",
}


RN_CHAPTERS = [
    {
        "id": "icms-regra-matriz",
        "title": "ICMS/RN: incidência, não incidência, suspensão e diferimento",
        "summary": "A porta de entrada do ICMS potiguar: campo de incidência, fato gerador, não incidência, isenção, suspensão, diferimento, contribuinte e responsabilidade.",
        "theme": "Regra matriz",
        "refs": [
            {"source": "RN_DEC_31825_2022_RICMS_GERAL", "articles": ["1", "2", "3", "4", "7", "8", "9"]},
            {"source": "RN_LEI_11999_2024_ICMS_LC87", "keywords": ["Lei nº 6.968", "Lei Complementar Federal nº 87", "ICMS", "não incidência"]},
        ],
        "analysis": [
            "No Rio Grande do Norte, a leitura começa pelo Decreto nº 31.825/2022. Ele consolida a operação, a prestação, o fato gerador e as hipóteses em que a cobrança não nasce ou fica deslocada para outro momento.",
            "Isenção, suspensão e diferimento não são sinônimos. A isenção afasta a cobrança dentro de hipótese legal; a suspensão condiciona a exigência a evento futuro; o diferimento adia lançamento e pagamento para etapa posterior.",
            "A Lei nº 11.999/2024 aparece como atualização material da Lei nº 6.968/1996 para compatibilizar a legislação estadual com alterações da LC 87/1996. Ela deve ser lida junto com o RICMS nas teses de incidência, não incidência e exportação.",
        ],
        "departments": "Fiscal define operação, CFOP, CST/CSOSN, incidência e responsável. Jurídico separa não incidência, imunidade, isenção e diferimento. Cadastro confirma inscrição e regime.",
        "documents": "NF-e, CT-e, cadastro fiscal, contrato, pedido, comprovante de circulação ou prestação, inscrição estadual, EFD e memória de enquadramento.",
        "risks": "Aplicar benefício antes de confirmar incidência; tratar diferimento como perdão; confundir suspensão com isenção; perder a prova do evento posterior que encerra a suspensão ou o diferimento.",
    },
    {
        "id": "base-aliquota-apuracao",
        "title": "Base de cálculo, alíquotas, FECOP, crédito e apuração",
        "summary": "Como o valor tributável é formado no RN, qual alíquota se aplica, quando há adicional do FECOP e como crédito, vedação, apuração e recolhimento se conectam.",
        "theme": "Carga tributária",
        "refs": [
            {"source": "RN_DEC_31825_2022_RICMS_GERAL", "articles": ["27", "28", "29", "30", "31", "35", "36", "40", "41", "58"]},
            {"source": "RN_RICMS_ANEXO_004_REDUCAO_BASE", "articles": ["1", "2", "8", "12"]},
        ],
        "analysis": [
            "A ordem correta é base, eventual redução, alíquota, adicional, crédito, estorno e recolhimento. Trocar a alíquota no cadastro sem demonstrar a base reduzida enfraquece a prova fiscal.",
            "O art. 29 do RICMS/RN reúne as alíquotas; o art. 30 adiciona pontos percentuais ao FECOP em produtos e serviços indicados. O cálculo precisa mostrar a carga final, e não apenas a alíquota nominal.",
            "O crédito comum nasce da não cumulatividade, mas o crédito presumido é benefício. Por isso, crédito do art. 36, crédito presumido do art. 40 e vedações do art. 41 devem ficar separados na memória de apuração.",
        ],
        "departments": "Fiscal parametriza base, alíquota, FECOP e crédito. Contábil concilia imposto, estoque, custo e estorno. Financeiro guarda guias. Auditoria cruza XML, EFD e recolhimento.",
        "documents": "XML, cadastro NCM, tabela de alíquotas, demonstrativo de base reduzida, memória de crédito, EFD, guia de recolhimento e conciliação contábil.",
        "risks": "Confundir redução de base com alíquota menor; esquecer FECOP; tomar crédito incompatível com benefício; não provar a carga efetiva aplicada.",
    },
    {
        "id": "beneficios-matriz-lc160",
        "title": "Benefícios fiscais, LC 160 e Convênio ICMS 190/2017",
        "summary": "A matriz potiguar de benefícios de ICMS: atos publicados para LC 160, isenções, incentivos, crédito presumido, regime especial, contrapartida e prova.",
        "theme": "Benefícios fiscais",
        "refs": [
            {"source": "RN_PORT_022_2018_BENEFICIOS_LC160", "full_text": True},
            {"source": "RN_DEC_31825_2022_RICMS_GERAL", "articles": ["7", "8", "9", "28", "40"]},
            {"source": "RN_DEC_27608_2017_FUNDERN", "articles": ["1", "2", "3", "4", "5"]},
        ],
        "analysis": [
            "A Portaria nº 022/2018-GS/SET é o mapa publicado pelo RN para a LC 160/2017 e o Convênio ICMS 190/2017. Ela não substitui o ato material do benefício; ela identifica o ato, o dispositivo, o início de vigência e o benefício que precisa ser lido.",
            "Benefício fiscal deve ser classificado pela técnica jurídica: isenção, suspensão, diferimento, redução de base, crédito presumido, regime especial ou incentivo financeiro-fiscal. Cada técnica muda XML, EFD, crédito e prova.",
            "Quando houver FUNDERN, a contrapartida financeira entra no dossiê do benefício. A empresa não prova só o direito ao incentivo; prova também que cumpriu depósito, prazo, condição e regularidade.",
        ],
        "departments": "Jurídico identifica ato e vigência. Fiscal transforma o benefício em CST, cBenef quando exigido, ajustes e EFD. Financeiro controla FUNDERN e guias. Controladoria mede renúncia e impacto.",
        "documents": "Portaria 022/2018, RICMS/RN, ato do benefício, termo de regime quando houver, XML, EFD, cBenef, guias, comprovante de FUNDERN e memória de cálculo.",
        "risks": "Usar a lista LC 160 sem abrir o ato material; acumular benefícios vedados; esquecer contrapartida; aplicar benefício vencido ou sem prova de condição.",
    },
    {
        "id": "isencoes-reducoes-creditos",
        "title": "Isenções, reduções de base e créditos presumidos",
        "summary": "Leitura por espécie: Anexo 001 para isenções, Anexo 004 para redução de base e Anexo 003 para crédito presumido.",
        "theme": "Benefícios por espécie",
        "refs": [
            {"source": "RN_RICMS_ANEXO_001_ISENCAO", "keywords": ["DAS OPERAÇÕES E PRESTAÇÕES ALCANÇADAS COM ISENÇÃO", "produtos", "medicamentos", "veículos", "taxista", "exportação"]},
            {"source": "RN_RICMS_ANEXO_004_REDUCAO_BASE", "keywords": ["REDUÇÃO DE BASE DE CÁLCULO", "carga tributária", "veículos", "produtos", "máquinas"]},
            {"source": "RN_RICMS_ANEXO_003_CREDITO_PRESUMIDO", "keywords": ["CRÉDITO PRESUMIDO", "óleo diesel", "biodiesel", "PROEDI", "aquisição"]},
            {"source": "RN_PORT_970_2025_CBENEF", "full_text": True},
        ],
        "analysis": [
            "Isenção afasta o débito; redução de base diminui o valor tributável; crédito presumido altera a apuração. As três figuras podem produzir cargas parecidas, mas a prova e a escrituração são diferentes.",
            "O Anexo 001 deve ser lido por sujeito, produto, operação, finalidade e prazo. O título do benefício não basta: a hipótese legal costuma restringir destinatário, condição sanitária, laudo, credenciamento ou finalidade.",
            "O cBenef é consequência da norma material. Ele ajuda a fiscalizar o benefício no documento fiscal, mas não cria direito quando a operação não cabe no texto do anexo ou da lei.",
        ],
        "departments": "Fiscal parametriza CST, cBenef, base e crédito. Cadastro valida NCM e descrição legal. Jurídico valida condições. Contábil controla estorno ou manutenção de crédito.",
        "documents": "XML, cBenef, cadastro de item, NCM, anexo aplicável, laudo quando houver, prova de destinatário/finalidade, EFD e memória de cálculo.",
        "risks": "Aplicar benefício por semelhança comercial; informar cBenef sem direito material; manter crédito quando a norma exige estorno; deixar de provar finalidade específica.",
    },
    {
        "id": "proedi-desenvolvimento",
        "title": "PROEDI, desenvolvimento industrial e FUNDERN",
        "summary": "Programa de Estímulo ao Desenvolvimento Industrial do RN: crédito presumido, adesão, enquadramento, regulamento, condições, recolhimento e contrapartida.",
        "theme": "Programas estaduais",
        "refs": [
            {"source": "RN_LEI_10640_2019_PROEDI", "full_text": True},
            {"source": "RN_DEC_29420_2019_PROEDI", "full_text": True},
            {"source": "RN_DEC_27608_2017_FUNDERN", "articles": ["3", "4", "5", "6"]},
            {"source": "RN_RICMS_ANEXO_003_CREDITO_PRESUMIDO", "keywords": ["PROEDI", "Programa de Estímulo ao Desenvolvimento Industrial", "crédito presumido"]},
        ],
        "analysis": [
            "O PROEDI é programa de desenvolvimento, não mero desconto de ICMS. A fruição depende de enquadramento, atividade industrial, ato, condições, regularidade, cálculo do crédito presumido e acompanhamento do projeto.",
            "A Lei nº 10.640/2019 institui o programa e o Decreto nº 29.420/2019 regula a operação. O contribuinte precisa sair da lei geral para o ato concreto e para a escrituração mensal.",
            "Quando houver depósito, fundo ou contrapartida, a prova do pagamento é parte do benefício. Sem ela, o crédito presumido pode estar correto no cálculo e frágil na defesa.",
        ],
        "departments": "Jurídico acompanha enquadramento e vigência. Fiscal calcula crédito e cBenef quando exigido. Financeiro controla depósitos e guias. Controladoria mede metas e impacto econômico.",
        "documents": "Lei do PROEDI, decreto regulamentar, requerimento, termo, ato concessivo, XML, EFD, cBenef, memória do crédito, comprovante de regularidade e comprovante de contrapartida.",
        "risks": "Aplicar PROEDI sem ato individual; usar crédito fora da operação habilitada; não comprovar regularidade; perder prazo, meta ou depósito vinculado.",
    },
    {
        "id": "agro-cesta-diferimento",
        "title": "Agro, alimentos, cesta, pesca e diferimento",
        "summary": "Tratamentos para cadeias agropecuárias, alimentos, abate, pesca, óleo diesel/biodiesel de transporte e diferimentos por etapa produtiva.",
        "theme": "Agro e alimentos",
        "refs": [
            {"source": "RN_RICMS_ANEXO_001_ISENCAO", "keywords": ["gado", "bovino", "bufalino", "suíno", "leite", "peixe", "cesta", "alimento"]},
            {"source": "RN_RICMS_ANEXO_002_DIFERIMENTO", "keywords": ["produtor", "agropecuária", "algodão", "camarão", "cana", "diferimento"]},
            {"source": "RN_RICMS_ANEXO_003_CREDITO_PRESUMIDO", "keywords": ["óleo diesel", "biodiesel", "embarcações pesqueiras", "transporte público"]},
            {"source": "RN_PORT_970_2025_CBENEF", "keywords": ["RN010001", "RN020001", "RN020002", "RN020003"]},
        ],
        "analysis": [
            "Nas cadeias agroalimentares, a descrição do produto e a etapa da cadeia são decisivas. Abate, produtor, industrialização, revenda e consumo final podem ter tratamentos diferentes.",
            "Diferimento desloca o recolhimento; não extingue o imposto. A prova precisa acompanhar a etapa posterior e quem assume a responsabilidade pelo pagamento.",
            "Os códigos cBenef publicados para RN mostram a lógica de controle: abate com isenção, óleo diesel/biodiesel com crédito presumido para transporte coletivo e óleo diesel para embarcações pesqueiras.",
        ],
        "departments": "Fiscal parametriza produto e etapa. Compras guarda origem e destinatário. Operações prova uso ou finalidade. Contábil controla crédito, estorno, diferimento e baixa.",
        "documents": "NF-e, NCM, romaneio, laudo sanitário quando aplicável, contrato, prova de origem/destino, EFD, cBenef e memória do tratamento aplicado.",
        "risks": "Aplicar benefício por nome comercial; não provar destinação; tratar diferimento como isenção; usar cBenef de produto sem aderência ao anexo.",
    },
    {
        "id": "atacado-distribuicao-regimes",
        "title": "Atacado, distribuição, regimes especiais e comércio",
        "summary": "Regimes de atacadistas, distribuição, cosméticos, perfumaria, produtos de higiene, centralização, credenciamento e limites de fruição.",
        "theme": "Regimes especiais",
        "refs": [
            {"source": "RN_DEC_26789_2017_ATACADISTAS", "full_text": True},
            {"source": "RN_PORT_022_2018_BENEFICIOS_LC160", "keywords": ["atacadista", "cosméticos", "perfumaria", "higiene pessoal", "regime especial"]},
            {"source": "RN_DEC_31825_2022_RICMS_GERAL", "keywords": ["regime especial", "atacadista", "PROEDI", "regularidade"]},
        ],
        "analysis": [
            "Regime especial para atacado depende de atividade real e critério de saídas. A leitura deve separar atacado, varejo, venda a contribuinte, venda a consumidor final e mercadoria excluída.",
            "A norma de alteração não substitui o controle mensal: percentual de saídas, cadastro, produto, destinatário, regularidade e vedação de acumulação precisam estar demonstrados.",
            "Quando o regime reduz carga ou desloca recolhimento, o dossiê deve mostrar cálculo, origem do direito, documento fiscal e cumprimento de condições.",
        ],
        "departments": "Comercial informa cadeia e perfil de clientes. Fiscal parametriza carga e documento. Financeiro guarda recolhimentos. Auditoria mede percentual de saídas e aderência do regime.",
        "documents": "Termo ou ato de regime, cadastro, XML, relatório de vendas por destinatário, EFD, guia, memória de apuração e prova de regularidade.",
        "risks": "Aplicar regime atacadista a operação varejista; descumprir percentual de saídas; usar produto fora do escopo; não provar regularidade fiscal.",
    },
    {
        "id": "st-antecipacao-combustiveis",
        "title": "Substituição tributária, antecipação, combustíveis, trigo e veículos",
        "summary": "Responsabilidade tributária por segmento: ST geral, antecipação, combustíveis e lubrificantes, trigo/farinha/derivados e veículos autopropulsados.",
        "theme": "Responsabilidade tributária",
        "refs": [
            {"source": "RN_DEC_31825_2022_RICMS_GERAL", "articles": ["59", "60"]},
            {"source": "RN_RICMS_ANEXO_005_ANTECIPACAO", "articles": ["1", "2", "3", "4"]},
            {"source": "RN_RICMS_ANEXO_007_ST", "articles": ["1", "2", "3", "4"]},
            {"source": "RN_RICMS_ANEXO_008_ST_COMBUSTIVEIS", "keywords": ["combustíveis", "lubrificantes", "substituição tributária"]},
            {"source": "RN_RICMS_ANEXO_009_TRIGO", "keywords": ["trigo", "farinha de trigo", "derivados"]},
            {"source": "RN_RICMS_ANEXO_010_VEICULOS", "keywords": ["veículos autopropulsados", "substituição tributária"]},
        ],
        "analysis": [
            "ST e antecipação não são benefícios; são técnicas de responsabilidade, momento e controle de recolhimento. O primeiro passo é identificar mercadoria, NCM/CEST, segmento e responsável.",
            "A antecipação do art. 59 e do Anexo 005 precisa ser separada da ST encerrada. Em algumas hipóteses, a antecipação é parcial e se transforma em crédito na apuração normal.",
            "Combustíveis, trigo e veículos têm anexos próprios. Nesses segmentos, convênios, protocolos, MVA, pauta, preço de referência e responsabilidade podem mudar o cálculo e a prova.",
        ],
        "departments": "Fiscal controla NCM/CEST, MVA, pauta e responsável. Compras valida retenção na entrada. Financeiro guarda GNRE/DAE. Auditoria cruza estoque, XML e EFD.",
        "documents": "XML, NCM, CEST, anexo do segmento, pauta/MVA, guia, EFD, cadastro de item e memória por operação.",
        "risks": "Aplicar ST por descrição parecida; misturar antecipação parcial com encerramento de fase; ignorar convênio ou protocolo; não controlar ressarcimento ou complemento.",
    },
    {
        "id": "documentos-cbenef-efd-prova",
        "title": "Documentos fiscais, cBenef, EFD e prova digital",
        "summary": "Como a tese tributária aparece no XML, na NFC-e, na NF-e, na EFD, nos livros, nos documentos fiscais e na prova mensal de auditoria.",
        "theme": "Prova digital",
        "refs": [
            {"source": "RN_DEC_31825_2022_RICMS_GERAL", "articles": ["119", "120", "121", "139", "143", "145"]},
            {"source": "RN_RICMS_ANEXO_011_DOCUMENTOS", "articles": ["1", "2", "3", "4", "11"]},
            {"source": "RN_PORT_970_2025_CBENEF", "full_text": True},
        ],
        "analysis": [
            "A prova nasce no documento fiscal. Se a operação usa benefício, o XML precisa refletir CST, base, crédito, cBenef quando exigido, fundamento e coerência com EFD.",
            "O art. 143 do RICMS/RN torna a EFD o repositório digital de apuração e informações de interesse do fisco. Por isso, tese sem escrituração compatível é tese incompleta.",
            "A Portaria-SEI nº 970/2025 mostra que o RN passou a exigir controle explícito do cBenef em operações alcançadas pelos benefícios listados. O código deve nascer da norma, não do desejo de reduzir imposto.",
        ],
        "departments": "Fiscal emite e escritura. TI mantém cadastro fiscal. Contábil concilia apuração. Jurídico guarda fundamento. Auditoria monta dossiê mensal.",
        "documents": "XML, DANFE, NFC-e, EFD, registros de ajuste, cBenef, memória de cálculo, guia, cadastro de produto, ato legal e comprovante de condição.",
        "risks": "Documento com benefício sem cBenef exigido; EFD sem ajuste; XML divergente da memória; código de benefício usado sem aderência ao texto legal.",
    },
    {
        "id": "mapa-revisado-beneficios",
        "title": "Mapa revisado dos benefícios fiscais do RN",
        "summary": "Roteiro de estudo por grupo: isenção, redução, crédito presumido, diferimento, PROEDI, Tax Free, FUNDERN, atacado, ST/antecipação, cBenef e prova.",
        "theme": "Mapa de benefícios",
        "refs": [
            {"source": "RN_PORT_022_2018_BENEFICIOS_LC160", "full_text": True},
            {"source": "RN_RICMS_ANEXO_001_ISENCAO", "keywords": ["isenção", "operações", "prestações"]},
            {"source": "RN_RICMS_ANEXO_003_CREDITO_PRESUMIDO", "keywords": ["crédito presumido", "PROEDI", "óleo diesel", "biodiesel"]},
            {"source": "RN_RICMS_ANEXO_004_REDUCAO_BASE", "keywords": ["redução de base de cálculo", "carga tributária"]},
            {"source": "RN_LEI_12111_2025_TAX_FREE", "full_text": True},
        ],
        "analysis": [
            "Este mapa é a rota de navegação: primeiro identificar a técnica do benefício; depois abrir o anexo ou lei; em seguida validar operação, produto, destinatário, vigência, prova e escrituração.",
            "O Tax Free de 2025 é benefício com restituição condicionada, não isenção automática na venda. A mercadoria precisa sair do país no prazo e o documento fiscal deve evidenciar a restituição e o montante.",
            "A leitura por grupo evita erro comum: chamar todo incentivo de isenção. No RN, há isenção, redução, crédito presumido, diferimento, regime especial, restituição condicionada e contrapartida financeira.",
        ],
        "departments": "Jurídico monta matriz de benefícios. Fiscal parametriza documento. Financeiro controla restituição, guias e FUNDERN. Auditoria testa aderência por operação.",
        "documents": "Ato legal, anexo aplicável, XML, EFD, cBenef, contrato, prova de destinatário, comprovante de saída do país quando Tax Free, guia e memória de cálculo.",
        "risks": "Usar o grupo errado; aplicar benefício sem ler condição específica; deixar restituição ou contrapartida fora da prova; informar benefício no XML sem base material.",
    },
    {
        "id": "fiscalizacao-riscos",
        "title": "Fiscalização, regularidade, perda de benefício e defesa documental",
        "summary": "Como a fiscalização tende a testar benefícios: regularidade, cadastro, documento, escrituração, prazo, contrapartida, condição e coerência entre sistemas.",
        "theme": "Auditoria fiscal",
        "refs": [
            {"source": "RN_DEC_31825_2022_RICMS_GERAL", "articles": ["77", "102", "103", "108", "121"]},
            {"source": "RN_DEC_29420_2019_PROEDI", "keywords": ["cancelamento", "regularidade", "obrigações tributárias", "penalidades", "termo"]},
            {"source": "RN_DEC_27608_2017_FUNDERN", "keywords": ["depósito mensal", "beneficiários", "FUNDERN"]},
            {"source": "RN_PORT_970_2025_CBENEF", "articles": ["1", "2"]},
        ],
        "analysis": [
            "A fiscalização costuma atacar a distância entre benefício informado e prova disponível. O direito pode estar no anexo, mas cai se cadastro, XML, EFD, cBenef, guia e condição não conversam.",
            "Regularidade fiscal, inscrição, depósito em fundo, credenciamento, prazo e ato individual são tão importantes quanto a regra que concede o benefício.",
            "Defesa boa é construída no mês do fato gerador: dispositivo, cálculo, documento, escrituração e comprovante precisam estar arquivados antes de qualquer intimação.",
        ],
        "departments": "Jurídico mantém matriz de risco. Fiscal fecha dossiê mensal. Financeiro guarda pagamentos e contrapartidas. Contábil concilia crédito, débito e estorno.",
        "documents": "Checklists, certidões, atos concessivos, XML, EFD, cBenef, guias, comprovante FUNDERN, relatórios de metas, memória de cálculo e parecer de enquadramento.",
        "risks": "Benefício materialmente correto, mas documentalmente frágil; condição vencida; cBenef ausente; regime sem ato; cálculo impossível de reconstruir.",
    },
]

RN_SIGNAL_CHAPTER_MAP = {
    "exportacao": "icms-regra-matriz",
    "nao incidencia": "icms-regra-matriz",
    "aliquota": "base-aliquota-apuracao",
    "reducao de base": "isencoes-reducoes-creditos",
    "isencao": "isencoes-reducoes-creditos",
    "credito outorgado": "isencoes-reducoes-creditos",
    "diferimento": "agro-cesta-diferimento",
    "suspensao": "icms-regra-matriz",
    "regime especial": "atacado-distribuicao-regimes",
    "protege/fundo": "proedi-desenvolvimento",
    "fundo/contrapartida": "proedi-desenvolvimento",
    "substituicao tributaria": "st-antecipacao-combustiveis",
    "efd/sped": "documentos-cbenef-efd-prova",
    "cBenef": "documentos-cbenef-efd-prova",
}


CONFIGURED_STATE_PROFILES = {
    "MS": {
        "name": "Mato Grosso do Sul",
        "hero": "Legislação estadual em tela: ICMS, benefícios fiscais, MS-Empreendedor, FUNDERSUL, ST, EFD, documentos, parcelamento e prova por assunto.",
        "material": "Lei nº 1.810/1997, RICMS/MS, Anexo I de benefícios, Anexos II, III, V, VI e XV, LC nº 93/2001, Lei nº 1.963/1999 e atos recentes de pagamento, cadastro e EFD.",
        "benefits": "Isenção, redução de base, crédito presumido, diferimento, regimes especiais, MS-Empreendedor, FUNDERSUL, benefícios agropecuários, máquinas, medicamentos, veículos, ST, parcelamento e restauração de incentivo.",
        "first_question": "A operação está no campo de incidência do ICMS sul-mato-grossense? Depois disso, separe regra comum, exoneração, benefício condicionado, regime especial, ST, documento e prova.",
        "tags": "MS Mato Grosso do Sul ICMS RICMS benefícios fiscais alíquotas base cálculo substituição tributária ST MS-Empreendedor FUNDERSUL crédito presumido diferimento Anexo I Anexo V Anexo VI EFD SPED LC 160 Convênio 190",
        "signal_map": {
            "exportacao": "icms-regra-matriz",
            "nao incidencia": "icms-regra-matriz",
            "aliquota": "base-aliquota-apuracao",
            "reducao de base": "isencoes-reducoes-creditos",
            "isencao": "isencoes-reducoes-creditos",
            "credito outorgado": "ms-empreendedor-regimes",
            "diferimento": "agro-fundersul-diferimento",
            "suspensao": "icms-regra-matriz",
            "regime especial": "ms-empreendedor-regimes",
            "protege/fundo": "agro-fundersul-diferimento",
            "fundo/contrapartida": "agro-fundersul-diferimento",
            "substituicao tributaria": "st-antecipacao-segmentos",
            "efd/sped": "documentos-efd-prova",
            "cBenef": "documentos-efd-prova",
        },
    },
    "ES": {
        "name": "Espírito Santo",
        "hero": "Legislação estadual em tela: ICMS, benefícios fiscais, COMPETE/ES, INVEST-ES, FUNDAP, ST, cBenef, EFD, documentos e prova por assunto.",
        "material": "Lei nº 7.000/2001, Decreto nº 1.090-R/2002 (RICMS/ES), Lei nº 10.568/2016 (COMPETE/ES), Lei nº 10.550/2016 (INVEST-ES), Lei nº 2.508/1970 (FUNDAP) e tabela cBenef da SEFAZ/ES.",
        "benefits": "Isenção, redução de base, crédito presumido, diferimento, suspensão, regimes especiais, COMPETE/ES, INVEST-ES, FUNDAP, indústria, importação, atacado, agro, medicamentos, transporte, ST, cBenef e prova fiscal.",
        "first_question": "A operação está no campo do ICMS capixaba? Depois disso, separe regra comum, não incidência, benefício condicionado, programa estadual, ST, documento e prova.",
        "tags": "ES Espírito Santo ICMS RICMS benefícios fiscais alíquotas base cálculo substituição tributária ST COMPETE INVEST-ES FUNDAP crédito presumido redução base isenção diferimento cBenef EFD SPED LC 160 Convênio 190",
        "signal_map": {
            "exportacao": "icms-regra-matriz",
            "nao incidencia": "icms-regra-matriz",
            "aliquota": "base-aliquota-apuracao",
            "reducao de base": "isencoes-reducoes-creditos",
            "isencao": "isencoes-reducoes-creditos",
            "credito outorgado": "invest-compete-fundap",
            "diferimento": "invest-compete-fundap",
            "suspensao": "icms-regra-matriz",
            "regime especial": "invest-compete-fundap",
            "protege/fundo": "invest-compete-fundap",
            "fundo/contrapartida": "invest-compete-fundap",
            "substituicao tributaria": "st-antecipacao-segmentos",
            "efd/sped": "documentos-efd-prova",
            "cBenef": "documentos-efd-prova",
        },
    },
    "MG": {
        "name": "Minas Gerais",
        "hero": "Legislação estadual em tela: Lei nº 6.763/1975, RICMS/MG 2023, anexos de alíquotas, redução de base, crédito acumulado, crédito presumido, diferimento, ST, EFD e disposições especiais.",
        "material": "Lei nº 6.763/1975, Decreto nº 48.589/2023 e Anexos I a VIII do RICMS/MG 2023, extraídos das publicações da Secretaria de Estado de Fazenda de Minas Gerais.",
        "benefits": "Redução de base, crédito presumido, crédito acumulado, diferimento, disposições especiais, regimes setoriais, exportação, agro, indústria, transporte, energia, medicamentos, mineração, ST, documentos fiscais e EFD.",
        "first_question": "A operação está no campo do ICMS mineiro? Depois disso, separe regra comum, alíquota, redução, crédito, diferimento, ST, regime especial, documento e prova.",
        "tags": "MG Minas Gerais ICMS RICMS benefícios fiscais alíquotas base cálculo redução base crédito presumido crédito acumulado diferimento substituição tributária ST Anexo I Anexo II Anexo III Anexo IV Anexo V Anexo VI Anexo VII Anexo VIII EFD SPED LC 160 Convênio 190",
        "signal_map": {
            "exportacao": "creditos-exportacao-acumulado",
            "nao incidencia": "icms-regra-matriz",
            "aliquota": "base-aliquota-apuracao",
            "reducao de base": "isencoes-reducoes-creditos",
            "isencao": "beneficios-matriz-lc160",
            "credito outorgado": "creditos-presumidos-acumulados",
            "diferimento": "diferimento-regimes-especiais",
            "suspensao": "icms-regra-matriz",
            "regime especial": "diferimento-regimes-especiais",
            "protege/fundo": "diferimento-regimes-especiais",
            "fundo/contrapartida": "diferimento-regimes-especiais",
            "substituicao tributaria": "st-antecipacao-segmentos",
            "efd/sped": "documentos-efd-prova",
            "cBenef": "documentos-efd-prova",
        },
    },
    "RJ": {
        "name": "Rio de Janeiro",
        "hero": "Legislação estadual em tela: Lei nº 2.657/1996, RICMS/RJ, Manual de Benefícios, FOT, Repetro, indústria setorial, ST, documentos, EFD, códigos de benefício e prova fiscal.",
        "material": "Lei nº 2.657/1996, Decreto nº 27.427/2000 (RICMS/RJ), Decreto nº 27.815/2001, Lei nº 8.645/2019, Lei nº 8.890/2020, Lei nº 4.531/2005, roteiro de benefícios, tabela de códigos de benefício e manuais da SEFAZ/RJ.",
        "benefits": "Isenção, não incidência, redução de base, suspensão, diferimento, crédito presumido, regimes especiais, FOT/FEEF, Repetro, tratamentos industriais, importação, transporte, veículos, combustíveis, ST e prova por EFD.",
        "first_question": "A operação está no campo do ICMS fluminense? Depois disso, separe regra comum, carga tributária, benefício, contrapartida FOT, regime setorial, ST, documento e prova.",
        "tags": "RJ Rio de Janeiro ICMS RICMS benefícios fiscais alíquotas base cálculo redução base crédito presumido diferimento suspensão FOT FEEF Repetro indústria Lei 4531 Manual de Benefícios Decreto 27815 cBenef cCredPresumido EFD SPED LC 160 Convênio 190",
        "signal_map": {
            "exportacao": "creditos-exportacao-saldo-credor",
            "nao incidencia": "icms-regra-matriz",
            "aliquota": "base-aliquota-apuracao",
            "reducao de base": "isencoes-reducoes-creditos",
            "isencao": "isencoes-reducoes-creditos",
            "credito outorgado": "isencoes-reducoes-creditos",
            "diferimento": "beneficios-matriz-lc160",
            "suspensao": "beneficios-matriz-lc160",
            "regime especial": "regimes-setoriais-industria-repetro",
            "protege/fundo": "fot-feef-contrapartidas",
            "fundo/contrapartida": "fot-feef-contrapartidas",
            "substituicao tributaria": "st-antecipacao-segmentos",
            "efd/sped": "documentos-efd-prova",
            "cBenef": "documentos-efd-prova",
        },
    },
}


CONFIGURED_STATE_CHAPTERS = {
    "MS": [
        {
            "id": "icms-regra-matriz",
            "title": "ICMS/MS: incidência, imunidades, não incidência, isenção, suspensão e diferimento",
            "summary": "A regra maior do ICMS em Mato Grosso do Sul: quando o imposto nasce, quando a competência é limitada e como a norma separa isenção, suspensão e diferimento.",
            "theme": "Regra matriz",
            "refs": [
                {"source": "MS_LEI_1810_1997_ICMS", "articles": ["1", "2", "5", "6", "7", "12", "13"]},
                {"source": "MS_DEC_9203_1998_RICMS_GERAL", "articles": ["1", "2", "3", "4", "5", "6", "7", "8", "9"]},
            ],
            "analysis": [
                "O estudo do MS começa pela Lei nº 1.810/1997 e pelo Decreto nº 9.203/1998. A lei fixa a competência tributária e o RICMS transforma essa competência em rotina fiscal: fato gerador, contribuinte, responsável, documento e prazo.",
                "Não incidência e isenção não são a mesma coisa. Na não incidência, o fato fica fora do campo do ICMS; na isenção, o fato entra no campo do imposto, mas a lei dispensa a cobrança dentro de condições fechadas.",
                "Suspensão e diferimento exigem controle de evento posterior. A empresa precisa saber quando a suspensão termina, quando o diferimento encerra e quem passa a responder pelo recolhimento.",
            ],
            "departments": "Fiscal define CFOP, CST/CSOSN, responsável e momento do imposto. Cadastro mantém inscrição e regime. Jurídico valida imunidade, não incidência, isenção e responsabilidade. Contábil concilia débito, crédito e efeitos de diferimento.",
            "documents": "XML, CT-e, cadastro de contribuinte, contrato, pedido, comprovante de circulação ou prestação, EFD, memória de enquadramento e fundamento legal usado no documento.",
            "risks": "Aplicar benefício antes de verificar incidência; tratar diferimento como dispensa definitiva; chamar não incidência de isenção; não controlar o evento que encerra suspensão ou diferimento.",
        },
        {
            "id": "base-aliquota-apuracao",
            "title": "Base de cálculo, alíquotas, DIFAL, FECOMP, importados e apuração",
            "summary": "Como a operação vira base tributável, qual alíquota se aplica, como ler carga efetiva, importados a 4%, consumidor final e recolhimento.",
            "theme": "Carga tributária",
            "refs": [
                {"source": "MS_LEI_1810_1997_ICMS", "articles": ["18", "20", "30", "31", "32", "41", "41-A", "41-B", "42", "43", "83", "84"]},
                {"source": "MS_DEC_9203_1998_RICMS_GERAL", "articles": ["15", "16", "17", "18", "19", "20", "41", "42", "42-A", "53", "61", "73", "74"]},
                {"source": "MS_RICMS_ANEXO_023_IMPORTADOS_ALIQUOTA_4", "full_text": True},
                {"source": "MS_RICMS_ANEXO_024_CONSUMIDOR_FINAL", "full_text": True},
                {"source": "MS_PORT_3760_2026_VALOR_REAL_PESQUISADO", "keywords": ["Valor Real Pesquisado", "base de cálculo", "produtos"]},
            ],
            "analysis": [
                "A alíquota só é lida depois da base de cálculo. Em auditoria, a pergunta correta é: qual operação ocorreu, qual base a lei mandou usar, quais parcelas entram, qual alíquota incide e se existe redução, adicional ou regime próprio.",
                "O art. 43 da Lei nº 1.810/1997 é importante para benefícios: ele autoriza o Regulamento a disciplinar redução de base ou crédito presumido para reduzir carga tributária dentro dos limites legais.",
                "Operações com importados, consumidor final não contribuinte, DIFAL, transporte e pauta fiscal precisam de demonstrativo próprio. O cadastro do ERP deve mostrar base cheia, base ajustada, alíquota, carga efetiva, crédito e guia.",
            ],
            "departments": "Fiscal parametriza base, alíquota, DIFAL, FECOMP, pauta e crédito. Contábil concilia imposto e custo. Financeiro guarda guias. Auditoria compara XML, EFD, memória de cálculo e período de vigência.",
            "documents": "XML, NCM, tabela de alíquotas, memória de base, valor real pesquisado quando houver, EFD, DAE/GNRE, guia de fundo e demonstrativo de carga efetiva.",
            "risks": "Trocar redução de base por alíquota menor no cadastro; aplicar alíquota atual a fato gerador antigo; ignorar regra de importados; calcular DIFAL sem reconstruir destinatário, finalidade e período.",
        },
        {
            "id": "beneficios-matriz-lc160",
            "title": "Benefícios fiscais: matriz legal, LC 160, CONFAZ e espécies admitidas",
            "summary": "A porta de entrada para benefícios no MS: isenção, redução de base, crédito presumido, diferimento, dispensa, regime especial e incentivo condicionado.",
            "theme": "Benefícios fiscais",
            "refs": [
                {"source": "MS_LEI_1810_1997_ICMS", "articles": ["43", "117-A", "228"]},
                {"source": "MS_RICMS_ANEXO_001_BENEFICIOS", "keywords": ["DOS BENEFÍCIOS FISCAIS", "isenção", "redução de base", "crédito presumido", "Convênio ICMS", "benefício fiscal"]},
                {"source": "MS_RICMS_ANEXO_005_REGIMES_ESPECIAIS", "keywords": ["favores fiscais", "benefícios fiscais", "regimes especiais", "condições", "manutenção"]},
                {"source": "MS_LC_93_2001_MS_EMPREENDEDOR", "articles": ["1", "5", "14", "22", "31"]},
            ],
            "analysis": [
                "Benefício fiscal é exceção expressa. Em Mato Grosso do Sul, o mapa começa no Anexo I do RICMS, passa pelos créditos do Anexo VI, pelos regimes do Anexo V, pelos programas da LC nº 93/2001 e pelas contrapartidas do FUNDERSUL quando aplicáveis.",
                "A LC 160/2017 e o Convênio ICMS 190/2017 não dispensam a leitura do ato material. Eles explicam a camada de convalidação e reinstituição; a aplicação concreta continua exigindo produto, operação, destinatário, período, condição e prova.",
                "A espécie do benefício muda o controle: isenção reduz débito, redução muda base, crédito presumido atua na apuração, diferimento desloca o pagamento, regime especial depende de ato e condição, e parcelamento regulariza crédito já constituído.",
            ],
            "departments": "Jurídico mantém matriz de ato, vigência, condição e vedação. Fiscal transforma a tese em CST, CFOP, EFD e ajuste. Contábil mede crédito, estorno e custo. Financeiro controla fundos, contribuições e recolhimentos.",
            "documents": "Lei, decreto, anexo, termo de acordo quando houver, XML, EFD, memória de cálculo, guia, comprovação de condição, evidência de regularidade e dossiê por benefício.",
            "risks": "Usar benefício por semelhança econômica; aplicar lista de CONFAZ como se fosse norma material completa; acumular benefício vedado; perder direito por falta de contribuição ou regularidade.",
        },
        {
            "id": "isencoes-reducoes-creditos",
            "title": "Isenções, reduções de base, créditos presumidos e subanexos setoriais",
            "summary": "Leitura aplicada do Anexo I e dos créditos fiscais: máquinas, agro, medicamentos, veículos, saúde, hortifrutigranjeiros, importação, indústria e demais grupos.",
            "theme": "Benefícios por grupo",
            "refs": [
                {"source": "MS_RICMS_ANEXO_001_BENEFICIOS", "full_text": True},
                {"source": "MS_RICMS_ANEXO_006_CREDITOS_PRESUMIDOS_PRODUTOR", "full_text": True},
                {"source": "MS_LEI_1810_1997_ICMS", "articles": ["43"]},
            ],
            "analysis": [
                "O Anexo I é o núcleo dos benefícios sul-mato-grossenses. Ele deve ser lido por grupo: isenções, reduções, subanexos de máquinas e equipamentos industriais, implementos agrícolas, medicamentos, veículos, saúde, hortifrutigranjeiros, infraestrutura e hipóteses específicas.",
                "O benefício não nasce do nome do setor. Ele nasce da descrição legal. Máquinas, informática, medicamentos, veículos, agro, energia, transporte e saúde exigem NCM, produto, destinatário, operação, finalidade, prazo e eventual convênio de suporte.",
                "Crédito presumido ou fixo não é crédito comum. A empresa precisa demonstrar base do crédito, percentual, operação alcançada, vedação de acumulação, estorno de crédito comum e reflexo na apuração.",
            ],
            "departments": "Fiscal parametriza CST, benefício e ajuste. Compras e comercial validam produto, NCM e destinatário. Contábil separa crédito normal e presumido. Jurídico revisa condição, prazo e vedação.",
            "documents": "XML, NCM, ficha técnica, laudo quando necessário, contrato, EFD, memória de cálculo, termo de regime quando houver, guia e fundamento legal no dossiê.",
            "risks": "Ampliar isenção por analogia; usar subanexo de máquina para bem fora da descrição; manter crédito quando a norma manda estornar; somar crédito presumido com benefício incompatível.",
        },
        {
            "id": "agro-fundersul-diferimento",
            "title": "Agro, produtor rural, FUNDERSUL, diferimento e crédito presumido de abate",
            "summary": "Como o MS trata cadeias agropecuárias: diferimento, contribuição condicionante, produtor rural, crédito presumido, circulação interna e prova da etapa posterior.",
            "theme": "Agro e fundo",
            "refs": [
                {"source": "MS_LEI_1963_1999_FUNDERSUL", "articles": ["1", "4", "9", "13", "14"]},
                {"source": "MS_RICMS_ANEXO_002_DIFERIMENTO", "full_text": True},
                {"source": "MS_RICMS_ANEXO_006_CREDITOS_PRESUMIDOS_PRODUTOR", "full_text": True},
                {"source": "MS_LEI_6495_2025_REFIS_ICMS", "articles": ["7", "8", "9"]},
            ],
            "analysis": [
                "O agro no MS precisa ser lido junto com o FUNDERSUL. A Lei nº 1.963/1999 conecta diferimento em operações internas com produtos agropecuários e crédito presumido de abate a contribuição específica, quando a norma a coloca como condição.",
                "Diferimento não elimina imposto: transfere o lançamento ou pagamento para etapa futura. Por isso, o controle exige mercadoria, produtor, adquirente, destino, evento de encerramento e contribuição quando aplicável.",
                "A Lei nº 6.495/2025 é relevante porque permite restaurar, em hipóteses específicas, direito a benefício ou incentivo condicionado à contribuição, quando a regularização ocorre nos termos legais.",
            ],
            "departments": "Fiscal controla diferimento, produtor rural, encerramento e EFD. Compras valida origem e produtor. Financeiro guarda contribuição e guias. Contábil mede custo, crédito e estoque. Jurídico acompanha regularidade do benefício.",
            "documents": "NF-e, cadastro agropecuário, inscrição estadual, romaneio, contrato, guia FUNDERSUL, EFD, memória de diferimento, comprovante de contribuição e prova da etapa posterior.",
            "risks": "Tratar diferimento como isenção; esquecer contribuição condicionante; não provar origem/destino; perder benefício por inadimplência; não restaurar formalmente o direito quando a lei exigir procedimento.",
        },
        {
            "id": "ms-empreendedor-regimes",
            "title": "MS-Empreendedor, regimes especiais, autorizações e crédito presumido",
            "summary": "Programas e regimes de desenvolvimento: LC nº 93/2001, Anexo V, termo de acordo, projeto, investimento, substituição por crédito presumido e perda do benefício.",
            "theme": "Programas estaduais",
            "refs": [
                {"source": "MS_LC_93_2001_MS_EMPREENDEDOR", "articles": ["1", "2", "5", "14", "19", "22", "24", "27-A", "31"]},
                {"source": "MS_RICMS_ANEXO_005_REGIMES_ESPECIAIS", "full_text": True},
            ],
            "analysis": [
                "A LC nº 93/2001 estrutura o ambiente de incentivos de MS, incluindo concessão, revisão, suspensão, cancelamento e substituição de benefícios por crédito fixo ou presumido. O ponto central é que o benefício depende de ato, projeto, condição e acompanhamento.",
                "O Anexo V do RICMS é a camada procedimental dos regimes especiais e autorizações específicas. Ele ensina quem decide, quais condições devem ser cumpridas, quais prazos valem e quando o favor fiscal pode ser suspenso ou cancelado.",
                "Para indústria, centro de distribuição ou empreendimento incentivado, a tese não é apenas tributária: é operacional. Investimento, emprego, localização, produção, prazo, regularidade e cumprimento do termo fazem parte da prova.",
            ],
            "departments": "Jurídico e controladoria acompanham projeto, termo e vigência. Fiscal calcula benefício e EFD. Operações prova investimento e produção. RH prova emprego quando relevante. Financeiro controla recolhimento e contrapartidas.",
            "documents": "Projeto, termo de acordo, deliberação, ato concessivo, relatórios de investimento, XML, EFD, memória de crédito presumido, certidões, guias e controles de metas.",
            "risks": "Usar incentivo fora do estabelecimento ou produto aprovado; ignorar prazo; deixar de cumprir condição; calcular crédito presumido sem autorização; perder benefício por irregularidade fiscal.",
        },
        {
            "id": "st-antecipacao-segmentos",
            "title": "Substituição tributária, antecipação, MVA, segmentos e transporte",
            "summary": "Responsabilidade por substituição, mercadorias sujeitas, base presumida, MVA, pauta, transporte e prova do imposto retido.",
            "theme": "Responsabilidade tributária",
            "refs": [
                {"source": "MS_LEI_1810_1997_ICMS", "articles": ["55", "56", "57", "57-A", "58", "61", "62"]},
                {"source": "MS_RICMS_ANEXO_003_ST", "full_text": True},
                {"source": "MS_RICMS_ANEXO_021_TABELA_TRANSPORTE", "full_text": True},
            ],
            "analysis": [
                "ST não é benefício; é técnica de responsabilidade. O estudo deve começar por mercadoria, NCM/CEST, protocolo ou convênio, operação, origem, destino, responsável e base presumida.",
                "O Anexo III reúne regras de substituição tributária e seus segmentos. A descrição legal precisa bater com o produto real; sem isso, MVA, pauta e recolhimento antecipado podem estar errados desde a origem.",
                "Transporte e pauta exigem leitura própria. O CT-e, MDF-e, percurso, carga, tarifa e responsável precisam fechar com a memória de cálculo e com a EFD.",
            ],
            "departments": "Fiscal controla NCM/CEST, MVA, pauta e CST. Compras valida fornecedor/substituto. Logística prova transporte. Financeiro guarda guia. Auditoria cruza estoque, XML, CT-e e EFD.",
            "documents": "XML, CT-e, MDF-e, NCM, CEST, tabela do anexo, pauta, MVA, GNRE/DAE, EFD, cadastro de item, comprovante de recolhimento e memória por produto.",
            "risks": "Aplicar ST por semelhança de produto; ignorar ressarcimento ou complemento; tratar antecipação como encerramento de cadeia sem base; usar pauta desatualizada.",
        },
        {
            "id": "documentos-efd-prova",
            "title": "Cadastro, documentos fiscais, EFD, automação comercial e prova digital",
            "summary": "Como a regra aparece no XML, no cadastro, nos livros, na EFD, nos controles de automação e no dossiê mensal de auditoria.",
            "theme": "Prova digital",
            "refs": [
                {"source": "MS_RICMS_ANEXO_004_CADASTRO", "full_text": True},
                {"source": "MS_RICMS_ANEXO_015_DOCUMENTOS_FISCAIS", "keywords": ["NF-e", "EFD", "Escrituração Fiscal Digital", "documentos fiscais", "livros fiscais", "Nota Fiscal Eletrônica"]},
                {"source": "MS_RICMS_ANEXO_018_AUTOMACAO_COMERCIAL", "full_text": True},
                {"source": "MS_DEC_14644_2016_CADASTRO_FISCAL", "keywords": ["Cadastro Fiscal", "inscrição", "suspensão", "cancelamento"]},
                {"source": "MS_RES_3485_2025_EFD", "full_text": True},
                {"source": "MS_ATO_DECL_1_2026_CADASTRO", "full_text": True},
            ],
            "analysis": [
                "A tese tributária só vira defesa quando aparece no documento certo. No MS, cadastro fiscal, NF-e, CT-e, EFD, livros, automação comercial e atos de suspensão ou cancelamento de inscrição formam a trilha de prova.",
                "EFD não cria direito. Ela declara o direito que precisa existir na lei, no decreto, no anexo ou no termo. Se o fundamento material estiver errado, o arquivo digital apenas torna o erro mais visível.",
                "Benefício, ST, diferimento e crédito presumido devem deixar rastro: CST/CSOSN, CFOP, informações complementares, ajuste, registro, guia, memória e conciliação contábil.",
            ],
            "departments": "Fiscal transmite e reconcilia EFD. TI mantém parâmetros de emissão. Cadastro cuida de inscrição e regime. Contábil fecha ajustes. Financeiro guarda guias. Auditoria valida coerência mensal.",
            "documents": "NF-e, NFC-e, CT-e, MDF-e, EFD, recibo, registros e ajustes, livros fiscais, cadastro, termo, XML, comprovante de guia, memória de cálculo e ato legal.",
            "risks": "Declarar ajuste sem direito material; manter cadastro incompatível com operação; perder inscrição por pendência; emitir XML sem fundamento; não guardar dossiê local do benefício.",
        },
        {
            "id": "mapa-revisado-beneficios",
            "title": "Mapa revisado dos benefícios de ICMS do Mato Grosso do Sul",
            "summary": "Inventário didático dos grupos de benefícios: Anexo I, diferimento, crédito presumido, MS-Empreendedor, FUNDERSUL, regimes especiais, ST e prova.",
            "theme": "Inventário de benefícios",
            "refs": [
                {"source": "MS_RICMS_ANEXO_001_BENEFICIOS", "full_text": True},
                {"source": "MS_RICMS_ANEXO_002_DIFERIMENTO", "keywords": ["diferimento", "produtos agropecuários", "operações internas", "encerramento"]},
                {"source": "MS_RICMS_ANEXO_006_CREDITOS_PRESUMIDOS_PRODUTOR", "full_text": True},
                {"source": "MS_RICMS_ANEXO_005_REGIMES_ESPECIAIS", "keywords": ["favores fiscais", "regimes especiais", "condições para concessão", "manutenção"]},
                {"source": "MS_LC_93_2001_MS_EMPREENDEDOR", "keywords": ["MS-EMPREENDEDOR", "incentivo", "benefício fiscal", "crédito fixo", "crédito presumido"]},
                {"source": "MS_LEI_1963_1999_FUNDERSUL", "keywords": ["diferimento", "crédito presumido", "FUNDERSUL", "contribuição"]},
                {"source": "MS_RICMS_ANEXO_015_DOCUMENTOS_FISCAIS", "keywords": ["EFD", "documentos fiscais", "Nota Fiscal Eletrônica"]},
            ],
            "analysis": [
                "O mapa de benefícios de MS deve ser lido por técnica e por setor. Técnica: isenção, redução, crédito presumido, diferimento, suspensão, regime especial e parcelamento/restauração. Setor: agro, indústria, máquinas, medicamentos, saúde, veículos, infraestrutura, importação, transporte e comércio.",
                "O Anexo I traz a lista material mais extensa. O Anexo II cuida de diferimento. O Anexo VI cuida de créditos fixos ou presumidos e produtor rural. O Anexo V dá o procedimento de regimes especiais. A LC nº 93/2001 organiza incentivos econômicos. A Lei nº 1.963/1999 conecta agro, FUNDERSUL e condições.",
                "A forma mais segura de aplicar qualquer item é montar matriz com: dispositivo, produto/operação, destinatário, vigência, condição, vedação, documento, EFD, guia e revisão de acumulação.",
            ],
            "departments": "Jurídico guarda a matriz de benefícios. Fiscal parametriza cada técnica. Compras, comercial e operações comprovam produto, destino e finalidade. Contábil mede crédito e estorno. Financeiro guarda contribuições e guias.",
            "documents": "Anexo ou lei do benefício, termo quando houver, XML, EFD, NCM, ficha técnica, memória de cálculo, guia, comprovante de contribuição, relatório de metas e parecer de enquadramento.",
            "risks": "Confundir técnica do benefício; aplicar por setor sem ler o item; esquecer contrapartida; não provar condição; usar benefício vencido ou acumulado indevidamente.",
        },
        {
            "id": "fiscalizacao-pagamento-restauracao",
            "title": "Fiscalização, parcelamento, REFIS, dívida ativa e restauração de benefício",
            "summary": "Pontos de controle do crédito tributário: auto de infração, trânsito, parcelamento, dívida ativa, REFIS/ICMS, contribuição condicionante e regularização.",
            "theme": "Fiscalização e regularização",
            "refs": [
                {"source": "MS_LEI_1810_1997_ICMS", "articles": ["117-A", "119", "228"]},
                {"source": "MS_LEI_6495_2025_REFIS_ICMS", "articles": ["1", "2", "3", "4", "7", "8", "9", "16"]},
                {"source": "MS_DEC_16721_2025_REFIS_PRORROGACAO", "full_text": True},
                {"source": "MS_RICMS_ANEXO_009_PARCELAMENTO", "full_text": True},
                {"source": "MS_RICMS_ANEXO_011_AUTO_INFRACAO", "full_text": True},
                {"source": "MS_RICMS_ANEXO_012_FISCALIZACAO_TRANSITO", "full_text": True},
                {"source": "MS_RICMS_ANEXO_013_DIVIDA_ATIVA", "full_text": True},
            ],
            "analysis": [
                "Fiscalização fecha o ciclo da tese: se a empresa aplicou benefício sem condição, crédito sem base, ST sem enquadramento ou diferimento sem encerramento, o risco aparece em auto, inscrição, parcelamento ou perda de benefício.",
                "A Lei nº 6.495/2025 é relevante para créditos de ICMS de fatos geradores até 28 de fevereiro de 2025 e para hipóteses de regularização ligadas a benefício ou incentivo condicionado à contribuição. Ela deve ser lida com o art. 228 da Lei nº 1.810/1997.",
                "Regularizar não apaga a necessidade de corrigir processo. Depois do parcelamento ou restauração, a empresa precisa corrigir cadastro, XML, EFD, memória, recolhimento e política interna para evitar repetição do erro.",
            ],
            "departments": "Jurídico conduz defesa, parcelamento e risco. Fiscal reconstrói documentos. Contábil concilia crédito e provisão. Financeiro acompanha adesão, parcela e guia. Auditoria ajusta controles internos.",
            "documents": "Auto de infração, notificação, processo administrativo, dívida ativa, termo de parcelamento, guia, comprovante de pagamento, EFD retificada, XML, memória e relatório de correção de causa.",
            "risks": "Aderir a regularização sem corrigir parametrização; pagar contribuição fora do prazo; manter benefício suspenso; não retificar EFD; perder prova de pagamento e restauração.",
        },
    ],
    "ES": [
        {
            "id": "icms-regra-matriz",
            "title": "ICMS/ES: incidência, fato gerador, não incidência e contribuinte",
            "summary": "A regra maior do ICMS capixaba: quando o imposto nasce, quando a Constituição e a lei afastam a incidência e quem assume a condição de contribuinte ou responsável.",
            "theme": "Regra matriz",
            "refs": [
                {"source": "ES_LEI_7000_2001_ICMS", "articles": ["1", "2", "3", "4", "5", "6", "10"]},
                {"source": "ES_DEC_1090_2002_RICMS", "articles": ["1", "2", "3", "4", "8", "9", "10", "15", "16", "17"]},
            ],
            "analysis": [
                "O estudo do Espírito Santo começa pela Lei nº 7.000/2001. Ela fixa a incidência do ICMS, os momentos do fato gerador, as hipóteses de não incidência e a forma de concessão de isenções, incentivos e benefícios fiscais.",
                "Não incidência, isenção, suspensão e diferimento não são palavras intercambiáveis. A não incidência tira a operação do campo do imposto; a isenção dispensa a cobrança dentro de condição legal; a suspensão paralisa a exigência; o diferimento desloca o pagamento para etapa posterior.",
                "O RICMS/ES transforma a regra material em rotina: inscrição, responsável, documento, escrituração, recolhimento e prova. Antes de qualquer benefício, a empresa precisa provar que a operação foi corretamente enquadrada na regra comum.",
            ],
            "departments": "Fiscal define CFOP, CST/CSOSN, contribuinte, responsável e momento do fato gerador. Jurídico valida não incidência, imunidade, isenção e responsabilidade. Cadastro mantém inscrição e regime. Contábil concilia débito, crédito e reflexos de suspensão ou diferimento.",
            "documents": "NF-e, CT-e, MDF-e, cadastro de contribuinte, contrato, pedido, comprovante de circulação ou prestação, EFD, memória de enquadramento e dispositivo legal usado no documento.",
            "risks": "Aplicar benefício antes de confirmar incidência; chamar não incidência de isenção; tratar diferimento como dispensa definitiva; não controlar o evento que encerra suspensão ou diferimento.",
        },
        {
            "id": "base-aliquota-apuracao",
            "title": "Base de cálculo, alíquotas, importação, DIFAL, créditos e apuração",
            "summary": "Como a operação vira base tributável, qual alíquota se aplica, como ler importação, consumidor final, crédito, estorno, apuração e recolhimento.",
            "theme": "Carga tributária",
            "refs": [
                {"source": "ES_LEI_7000_2001_ICMS", "articles": ["11", "12", "13", "14", "15", "16", "17", "18", "20", "21", "23", "24", "31", "32"]},
                {"source": "ES_DEC_1090_2002_RICMS", "keywords": ["base de cálculo", "alíquota", "diferencial de alíquotas", "importação", "crédito do imposto", "apuração", "recolhimento"]},
            ],
            "analysis": [
                "A alíquota vem depois da base. Em auditoria, a sequência é: identificar operação, localizar base legal, incluir ou excluir parcelas, aplicar alíquota nominal, verificar redução de base, adicional, crédito e forma de apuração.",
                "Importação, DIFAL, consumidor final, substituição tributária e benefício com carga efetiva exigem memória separada. Não basta cadastrar um percentual final no ERP; o cálculo precisa mostrar base cheia, ajuste, alíquota, crédito, estorno e guia.",
                "Crédito de ICMS depende de lastro documental e pertinência com operação tributada. Quando a norma traz isenção, redução ou crédito presumido, é indispensável ler a regra de manutenção, estorno ou vedação de aproveitamento.",
            ],
            "departments": "Fiscal parametriza base, alíquota, DIFAL, importação, crédito e ajuste. Compras preserva XML e NCM. Contábil concilia crédito, estorno e custo. Financeiro guarda guias. Auditoria compara EFD, XML e memória de cálculo.",
            "documents": "XML, DI/DUIMP quando houver, NCM, tabela de alíquotas, memória de base, demonstrativo de DIFAL, EFD, guia, razão contábil, controle de crédito e fundamento legal do ajuste.",
            "risks": "Trocar redução de base por alíquota menor; aplicar alíquota atual a fato gerador antigo; manter crédito vedado; calcular importação ou DIFAL sem reconstruir origem, destino, destinatário e finalidade.",
        },
        {
            "id": "beneficios-matriz-lc160",
            "title": "Benefícios fiscais: matriz legal, LC 160, CONFAZ, espécies e prova",
            "summary": "A porta de entrada para benefícios do Espírito Santo: isenção, redução de base, crédito presumido, diferimento, suspensão, regime especial, programas estaduais e cBenef.",
            "theme": "Benefícios fiscais",
            "refs": [
                {"source": "ES_LEI_7000_2001_ICMS", "articles": ["5", "6", "8", "10"]},
                {"source": "ES_DEC_1090_2002_RICMS", "keywords": ["isenção", "redução da base de cálculo", "crédito presumido", "diferimento", "benefício fiscal", "Convênio ICMS"]},
                {"source": "ES_TABELA_CBENEF_2026", "keywords": ["benefícios fiscais", "cBenef", "CST", "isenção", "redução de base", "diferimento"]},
            ],
            "analysis": [
                "Benefício fiscal é exceção expressa. No Espírito Santo, a leitura passa pela Lei nº 7.000/2001, pelo RICMS/ES, pela tabela cBenef, pelos programas COMPETE/ES, INVEST-ES e FUNDAP, e pelos convênios ou atos de suporte quando citados na norma.",
                "A LC 160/2017 e o Convênio ICMS 190/2017 ajudam a entender convalidação e reinstituição, mas não substituem o ato material. A aplicação prática continua dependendo de produto, operação, destinatário, período, condição, vedação e prova.",
                "A espécie do benefício muda o controle. Isenção afasta débito; redução altera base; crédito presumido atua na apuração; diferimento desloca pagamento; suspensão exige evento futuro; regime especial depende de ato e cumprimento contínuo.",
            ],
            "departments": "Jurídico mantém matriz de ato, vigência, condição e vedação. Fiscal traduz a tese em CST, CFOP, cBenef, EFD e ajuste. Contábil mede crédito, estorno e custo. Financeiro controla guias, fundos e contrapartidas quando houver.",
            "documents": "Lei, decreto, anexo, termo ou contrato quando houver, XML, EFD, cBenef, memória de cálculo, guia, comprovação da condição, regularidade fiscal e dossiê do benefício.",
            "risks": "Usar benefício por semelhança econômica; aplicar cBenef sem direito material; acumular benefício incompatível; esquecer prazo, condição, estorno ou contrapartida.",
        },
        {
            "id": "isencoes-reducoes-creditos",
            "title": "Isenções, reduções de base, créditos presumidos e benefícios por setor",
            "summary": "Leitura setorial dos benefícios capixabas: indústria, importação, atacado, agro, medicamentos, máquinas, transporte, energia, operações especiais e manutenção de crédito.",
            "theme": "Benefícios por grupo",
            "refs": [
                {"source": "ES_DEC_1090_2002_RICMS", "full_text": True},
                {"source": "ES_TABELA_CBENEF_2026", "full_text": True},
                {"source": "ES_LEI_7000_2001_ICMS", "articles": ["5", "6", "10", "31", "32"]},
            ],
            "analysis": [
                "O RICMS/ES contém hipóteses de isenção, suspensão, diferimento, redução de base, crédito presumido e tratamento específico por produto, setor ou operação. A leitura segura separa a técnica do benefício antes de olhar o setor econômico.",
                "Setores como indústria, importação, atacado, agro, medicamentos, máquinas, alimentos, transporte e energia não geram direito por nome. O direito nasce da descrição legal: produto, NCM, destinatário, finalidade, operação, vigência e condição.",
                "A tabela cBenef ajuda a transformar a legislação em documento fiscal, mas não substitui a lei. O código precisa corresponder ao dispositivo, ao CST, ao tipo de operação e ao benefício efetivamente aplicável.",
            ],
            "departments": "Fiscal parametriza CST, cBenef, CFOP e ajuste. Comercial valida operação e destinatário. Compras valida NCM e fornecedor. Contábil separa crédito comum e presumido. Jurídico revisa condição, prazo e vedação.",
            "documents": "XML, NCM, ficha técnica, laudo quando necessário, contrato, EFD, cBenef, memória de cálculo, termo de regime quando houver, guia e fundamento legal.",
            "risks": "Ampliar isenção por analogia; usar redução de base sem demonstrar carga efetiva; manter crédito quando a norma manda estornar; lançar cBenef por palavra-chave e não por enquadramento legal.",
        },
        {
            "id": "invest-compete-fundap",
            "title": "INVEST-ES, COMPETE/ES, FUNDAP, regimes especiais e desenvolvimento",
            "summary": "Programas estaduais de incentivo e competitividade: investimento, contrato, diferimento, crédito presumido, importação, comércio exterior, condições, perda e prova.",
            "theme": "Programas estaduais",
            "refs": [
                {"source": "ES_LEI_10550_2016_INVEST_ES", "articles": ["1", "2", "3", "4", "5", "6", "7", "8", "9"]},
                {"source": "ES_LEI_10568_2016_COMPETE_ES", "articles": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]},
                {"source": "ES_LEI_10574_2016_COMPETE_INVEST", "full_text": True},
                {"source": "ES_LEI_2508_1970_FUNDAP", "articles": ["1", "2", "3", "4", "5", "6"]},
                {"source": "ES_DEC_1090_2002_RICMS", "keywords": ["INVEST-ES", "COMPETE", "FUNDAP", "regime especial", "crédito presumido", "diferimento"]},
            ],
            "analysis": [
                "INVEST-ES, COMPETE/ES e FUNDAP devem ser lidos como regimes condicionados, não como descontos genéricos. Eles dependem de ato, contrato, atividade, investimento, operação, estabelecimento, prazo, regularidade e forma de cálculo.",
                "O INVEST-ES conversa com implantação, expansão, modernização, diversificação e revitalização de empreendimentos. O COMPETE/ES funciona como instrumento de competitividade por contrato. O FUNDAP tem foco histórico no financiamento ligado a operações de comércio exterior.",
                "A empresa precisa provar que o estabelecimento, o produto, a operação e o período estão dentro do ato. Crédito presumido, diferimento ou financiamento sem contrato, sem termo ou fora do escopo aprovado tende a virar autuação.",
            ],
            "departments": "Jurídico e controladoria acompanham contrato, termo, ato concessivo, vigência e metas. Fiscal calcula benefício, cBenef e EFD. Operações comprova investimento, produção, importação ou circulação. Financeiro guarda guias, financiamento e contrapartidas.",
            "documents": "Contrato de competitividade, ato concessivo, termo de acordo, projeto, relatórios de investimento, XML, DI/DUIMP, EFD, cBenef, memória de crédito presumido, certidões, guias e controles de metas.",
            "risks": "Usar incentivo fora do estabelecimento aprovado; ignorar prazo ou condição; confundir FUNDAP com benefício comum de ICMS; calcular crédito presumido sem ato; perder regime por irregularidade ou descumprimento contratual.",
        },
        {
            "id": "st-antecipacao-segmentos",
            "title": "Substituição tributária, antecipação, MVA, segmentos e ressarcimento",
            "summary": "Responsabilidade por substituição, mercadorias sujeitas, base presumida, MVA, pauta, antecipação, complemento, ressarcimento e prova do imposto retido.",
            "theme": "Responsabilidade tributária",
            "refs": [
                {"source": "ES_LEI_7000_2001_ICMS", "articles": ["16", "17", "18", "23", "24"]},
                {"source": "ES_DEC_1090_2002_RICMS", "keywords": ["substituição tributária", "MVA", "margem de valor agregado", "antecipação", "ressarcimento", "complemento"]},
            ],
            "analysis": [
                "Substituição tributária não é benefício: é técnica de responsabilidade. A leitura começa por mercadoria, NCM/CEST, convênio ou protocolo, operação, origem, destino, responsável, base presumida, MVA e forma de recolhimento.",
                "Antecipação, ST, complemento e ressarcimento precisam ser separados. Cada técnica tem documento, prazo e memória de cálculo próprios. O erro mais comum é tratar imposto antecipado como se encerrasse toda a cadeia sem verificar a regra aplicável.",
                "Em operação interestadual, a prova passa por XML, GNRE/DUA, protocolo, convênio, cadastro, EFD e controle de estoque. Se produto ou CEST estiver errado, toda a base presumida fica comprometida.",
            ],
            "departments": "Fiscal controla NCM/CEST, MVA, pauta, CST e recolhimento. Compras valida fornecedor/substituto. Comercial orienta preço e destinatário. Logística prova transporte. Financeiro guarda guias. Auditoria cruza estoque, XML e EFD.",
            "documents": "XML, CT-e, MDF-e, NCM, CEST, convênio, protocolo, pauta, MVA, DUA/GNRE, EFD, cadastro de item, comprovante de recolhimento e memória por produto.",
            "risks": "Aplicar ST por semelhança de produto; ignorar ressarcimento ou complemento; usar MVA vencida; recolher por UF errada; não provar retenção anterior.",
        },
        {
            "id": "documentos-efd-prova",
            "title": "cBenef, documentos fiscais, EFD, informações complementares e prova digital",
            "summary": "Como a regra aparece no XML, no cBenef, no CST, na EFD, nos ajustes, nos livros e no dossiê mensal de benefício ou regra especial.",
            "theme": "Prova digital",
            "refs": [
                {"source": "ES_TABELA_CBENEF_2026", "full_text": True},
                {"source": "ES_DEC_1090_2002_RICMS", "keywords": ["NF-e", "CT-e", "EFD", "Escrituração Fiscal Digital", "documentos fiscais", "cBenef", "Código de Benefício"]},
                {"source": "ES_LEI_7000_2001_ICMS", "keywords": ["documentos fiscais", "livros fiscais", "escrituração", "penalidade", "obrigação acessória"]},
            ],
            "analysis": [
                "O cBenef é a ponte entre benefício e documento fiscal. Ele só deve ser usado quando o dispositivo legal, o CST, a operação e a descrição da tabela apontarem para o mesmo enquadramento.",
                "EFD não cria direito: ela declara uma tese que precisa existir na lei, no decreto, no programa, no termo ou na tabela. Se o fundamento material estiver errado, o arquivo digital apenas torna o erro mais visível.",
                "Benefício, ST, diferimento, suspensão e crédito presumido precisam deixar rastro: CST, cBenef, CFOP, informações complementares, ajuste, registro, guia, memória e conciliação contábil.",
            ],
            "departments": "Fiscal transmite e reconcilia EFD. TI mantém parâmetros de emissão. Cadastro cuida de item, NCM, CST e cBenef. Contábil fecha ajustes. Financeiro guarda guias. Auditoria valida coerência mensal.",
            "documents": "NF-e, NFC-e, CT-e, MDF-e, EFD, recibo, registros e ajustes, livros fiscais, cadastro do item, XML, cBenef, comprovante de guia, memória de cálculo e ato legal.",
            "risks": "Declarar cBenef sem direito material; usar CST incompatível; transmitir EFD sem ajuste ou com ajuste errado; não manter dossiê local do benefício; perder a prova da condição do regime.",
        },
        {
            "id": "mapa-revisado-beneficios",
            "title": "Mapa revisado dos benefícios de ICMS do Espírito Santo",
            "summary": "Inventário didático dos grupos de benefícios: RICMS/ES, cBenef, COMPETE/ES, INVEST-ES, FUNDAP, redução, isenção, crédito presumido, diferimento, ST e prova.",
            "theme": "Inventário de benefícios",
            "refs": [
                {"source": "ES_DEC_1090_2002_RICMS", "full_text": True},
                {"source": "ES_TABELA_CBENEF_2026", "full_text": True},
                {"source": "ES_LEI_10550_2016_INVEST_ES", "keywords": ["INVEST-ES", "diferimento", "crédito presumido", "investimento"]},
                {"source": "ES_LEI_10568_2016_COMPETE_ES", "keywords": ["COMPETE/ES", "crédito presumido", "redução", "contrato de competitividade"]},
                {"source": "ES_LEI_2508_1970_FUNDAP", "keywords": ["FUNDAP", "operações de comércio exterior", "financiamento"]},
            ],
            "analysis": [
                "O mapa de benefícios do Espírito Santo deve ser lido por técnica e por programa. Técnica: isenção, não incidência, redução de base, crédito presumido, diferimento, suspensão, ST e regime especial. Programa: INVEST-ES, COMPETE/ES, FUNDAP e demais tratamentos previstos no RICMS/ES.",
                "A tabela cBenef ajuda a encontrar a capitulação e o CST, mas o portal mantém a regra material em tela para evitar aplicação por código solto. Código, dispositivo, operação, CST e documento precisam contar a mesma história.",
                "A forma mais segura de aplicar qualquer benefício é montar matriz com: ato, dispositivo, produto/operação, destinatário, vigência, condição, vedação, documento, cBenef, EFD, guia e revisão de acumulação.",
            ],
            "departments": "Jurídico guarda a matriz de benefícios. Fiscal parametriza cada técnica. Compras, comercial e operações comprovam produto, destino e finalidade. Contábil mede crédito e estorno. Financeiro guarda guias, financiamentos e contrapartidas.",
            "documents": "Lei, decreto, anexo, tabela cBenef, contrato ou termo quando houver, XML, EFD, NCM, ficha técnica, memória de cálculo, guia, comprovante de condição e parecer de enquadramento.",
            "risks": "Confundir técnica do benefício; aplicar por setor sem ler o item; esquecer cBenef; perder condição do contrato; usar benefício vencido ou acumulado indevidamente.",
        },
        {
            "id": "fiscalizacao-riscos",
            "title": "Fiscalização, penalidades, glosa, regularidade e defesa do benefício",
            "summary": "Pontos de controle do crédito tributário: documento, EFD, glosa de crédito, descumprimento de condição, perda de regime, autuação e correção de causa.",
            "theme": "Fiscalização e regularização",
            "refs": [
                {"source": "ES_LEI_7000_2001_ICMS", "keywords": ["penalidade", "infração", "fiscalização", "crédito tributário", "multa", "documentos fiscais"]},
                {"source": "ES_DEC_1090_2002_RICMS", "keywords": ["penalidade", "infração", "fiscalização", "glosa", "documentos fiscais", "EFD"]},
                {"source": "ES_LEI_10568_2016_COMPETE_ES", "keywords": ["perda", "suspensão", "cancelamento", "regularidade"]},
                {"source": "ES_LEI_10550_2016_INVEST_ES", "keywords": ["perda", "suspensão", "cancelamento", "regularidade"]},
            ],
            "analysis": [
                "Fiscalização fecha o ciclo da tese. Se a empresa aplicou benefício sem condição, crédito sem base, ST sem enquadramento ou cBenef sem dispositivo, o problema aparece no XML, na EFD, na guia, no estoque ou no contrato.",
                "A defesa começa antes da autuação: matriz legal, dossiê mensal, memória de cálculo, prova da condição, regularidade do contrato e conciliação contábil. Sem isso, o benefício vira narrativa sem lastro.",
                "Regularizar não é apenas pagar. Depois de autuação, glosa ou perda de regime, a empresa precisa corrigir cadastro, XML, EFD, memória, recolhimento e política interna para não repetir o erro.",
            ],
            "departments": "Jurídico conduz defesa, risco e revisão contratual. Fiscal reconstrói documentos. Contábil concilia crédito, provisão e estorno. Financeiro acompanha guia e eventual parcelamento. Auditoria ajusta controles internos.",
            "documents": "Auto de infração, notificação, processo administrativo, XML, EFD, guia, comprovante de pagamento, contrato de benefício, certidões, memória e relatório de correção de causa.",
            "risks": "Defender benefício sem dossiê; manter parametrização errada; não retificar EFD; perder contrato por descumprimento; pagar sem corrigir a causa operacional.",
        },
    ],
    "MG": [
        {
            "id": "icms-regra-matriz",
            "title": "ICMS/MG: regra matriz, fato gerador, não incidência e sujeição passiva",
            "summary": "A base do ICMS mineiro: quando o imposto nasce, quando a lei afasta a incidência, quem é contribuinte e quem pode ser responsável pelo recolhimento.",
            "theme": "Regra matriz",
            "refs": [
                {"source": "MG_LEI_6763_1975_ICMS", "keywords": ["fato gerador", "não incidência", "contribuinte", "responsabilidade", "substituição tributária"]},
                {"source": "MG_DEC_48589_2023_RICMS_REGULAMENTO", "articles": ["1", "2", "3", "4", "5", "6", "7", "8", "9"]},
            ],
            "analysis": [
                "Minas Gerais exige leitura em duas camadas. A Lei nº 6.763/1975 dá a estrutura legal do ICMS; o Decreto nº 48.589/2023 organiza a execução no RICMS/MG 2023.",
                "Antes de qualquer benefício, a pergunta é material: houve circulação de mercadoria, prestação de transporte interestadual ou intermunicipal, comunicação, importação, entrada para uso/consumo, ativo ou operação com consumidor final? Se a resposta muda, muda também o imposto.",
                "Não incidência, isenção, redução, suspensão e diferimento têm efeitos diferentes. A não incidência fica fora do campo tributável; isenção dispensa débito; redução altera base; suspensão posterga exigibilidade; diferimento transfere o recolhimento para outro momento ou sujeito.",
            ],
            "departments": "Fiscal define fato gerador, CFOP, CST/CSOSN, responsável e momento do imposto. Jurídico valida não incidência, imunidade, responsabilidade e risco de autuação. Cadastro mantém inscrição e regime. Contábil concilia débito, crédito e estoque.",
            "documents": "NF-e, CT-e, MDF-e, contrato, pedido, comprovante de circulação ou prestação, inscrição estadual, cadastro de item, EFD e memória de enquadramento.",
            "risks": "Aplicar benefício sem confirmar incidência; tratar não incidência como isenção; ignorar responsabilidade por substituição; deixar de provar destinatário, finalidade ou local da operação.",
        },
        {
            "id": "base-aliquota-apuracao",
            "title": "Base de cálculo, alíquotas, carga efetiva, DIFAL, crédito e apuração",
            "summary": "Como a operação vira base tributável em Minas Gerais, qual alíquota se aplica, como ler o Anexo I, crédito, estorno, DIFAL e apuração.",
            "theme": "Carga tributária",
            "refs": [
                {"source": "MG_LEI_6763_1975_ICMS", "keywords": ["base de cálculo", "alíquota", "diferencial de alíquotas", "crédito do imposto", "apuração"]},
                {"source": "MG_DEC_48589_2023_RICMS_REGULAMENTO", "keywords": ["base de cálculo", "alíquota", "diferencial de alíquotas", "crédito", "apuração", "recolhimento"]},
                {"source": "MG_RICMS_2023_ANEXO_I_ALIQUOTAS", "full_text": True},
            ],
            "analysis": [
                "A leitura correta começa pela base de cálculo. Só depois se aplica a alíquota do Anexo I, eventual redução de base, adicional, diferimento, crédito, estorno ou regra de apuração.",
                "Em Minas, muitas discussões práticas nascem da diferença entre alíquota nominal e carga efetiva. Redução de base não é alíquota menor: ela precisa aparecer como base ajustada, com fundamento legal e reflexo correto na EFD.",
                "DIFAL, importação, transferência, ativo, uso/consumo e operação interestadual devem ser tratados com memória própria. O ERP precisa guardar a trilha: base cheia, base ajustada, alíquota, crédito e guia.",
            ],
            "departments": "Fiscal parametriza base, alíquota, DIFAL, crédito e estorno. Compras preserva XML, NCM e origem. Contábil concilia crédito, custo e estoque. Financeiro guarda DAE/GNRE. Auditoria compara documento, EFD e memória.",
            "documents": "XML, NCM, Anexo I, demonstrativo de base, memória de DIFAL, EFD, guia, razão contábil, controle de crédito e fundamento legal do ajuste.",
            "risks": "Cadastrar carga efetiva como alíquota; aplicar alíquota antiga; ignorar estorno; calcular DIFAL sem destinatário correto; usar redução de base fora da descrição legal.",
        },
        {
            "id": "beneficios-matriz-lc160",
            "title": "Benefícios fiscais: matriz legal, LC 160, CONFAZ e anexos do RICMS/MG",
            "summary": "A porta de entrada para benefícios mineiros: redução de base, crédito presumido, crédito acumulado, diferimento, disposições especiais, regimes e prova documental.",
            "theme": "Benefícios fiscais",
            "refs": [
                {"source": "MG_LEI_6763_1975_ICMS", "keywords": ["benefícios fiscais", "isenção", "incentivos", "crédito presumido", "redução da base de cálculo"]},
                {"source": "MG_DEC_48589_2023_RICMS_REGULAMENTO", "keywords": ["benefício fiscal", "redução de base de cálculo", "crédito presumido", "diferimento", "regime especial"]},
                {"source": "MG_RICMS_2023_ANEXO_II_REDUCAO_BASE", "keywords": ["redução de base de cálculo", "carga tributária", "isenção"]},
                {"source": "MG_RICMS_2023_ANEXO_IV_CREDITO_PRESUMIDO", "full_text": True},
                {"source": "MG_RICMS_2023_ANEXO_VIII_DISPOSICOES_ESPECIAIS", "keywords": ["regime especial", "benefício fiscal", "crédito presumido", "diferimento"]},
            ],
            "analysis": [
                "Benefício fiscal em Minas deve ser lido pelo anexo correto. Alíquota está no Anexo I; redução de base no Anexo II; crédito acumulado no Anexo III; crédito presumido no Anexo IV; diferimento no Anexo VI; ST no Anexo VII; regimes e disposições especiais no Anexo VIII.",
                "A LC 160/2017 e o Convênio ICMS 190/2017 ajudam a entender a convalidação e reinstituição de benefícios, mas não substituem a norma mineira aplicável. A aplicação exige dispositivo, produto, operação, destinatário, vigência, condição e prova.",
                "A técnica jurídica muda o controle: redução mexe na base, crédito presumido mexe na apuração, crédito acumulado depende de autorização e uso, diferimento desloca pagamento e regime especial exige ato ou condição específica.",
            ],
            "departments": "Jurídico mantém a matriz de ato, anexo, vigência, condição e vedação. Fiscal transforma a tese em CST, CFOP, EFD e ajuste. Contábil mede crédito, estorno e custo. Financeiro acompanha guias e autorizações.",
            "documents": "Lei, decreto, anexo, regime especial quando houver, XML, EFD, memória de cálculo, DAE/GNRE, comprovação de condição, regularidade fiscal e dossiê por benefício.",
            "risks": "Aplicar benefício por semelhança; usar anexo errado; acumular benefício incompatível; ignorar estorno; aplicar benefício vencido ou sem regime especial exigido.",
        },
        {
            "id": "isencoes-reducoes-creditos",
            "title": "Reduções de base, isenções e cargas efetivas por mercadoria e setor",
            "summary": "Leitura do Anexo II e das disposições correlatas: cesta básica, medicamentos, máquinas, energia, transporte, agro, indústria, importação e operações especiais.",
            "theme": "Benefícios por grupo",
            "refs": [
                {"source": "MG_RICMS_2023_ANEXO_II_REDUCAO_BASE", "full_text": True},
                {"source": "MG_RICMS_2023_ANEXO_VIII_DISPOSICOES_ESPECIAIS", "keywords": ["redução de base de cálculo", "carga tributária", "mercadoria", "regime especial", "vedada a cumulação"]},
                {"source": "MG_LEI_6763_1975_ICMS", "keywords": ["isenção", "redução", "carga tributária", "benefício fiscal"]},
            ],
            "analysis": [
                "O Anexo II deve ser lido como mapa de cargas efetivas. Cada item precisa ser amarrado a mercadoria, NCM quando houver, destinatário, operação, período, convênio citado e regra de manutenção ou estorno de crédito.",
                "Setores como alimentos, medicamentos, máquinas, agro, energia, transporte e indústria não geram direito por rótulo econômico. O que autoriza o benefício é a descrição legal do item.",
                "Quando a norma fala em carga tributária final, a empresa precisa demonstrar a base cheia, a base reduzida, a alíquota nominal, a carga final, eventual vedação de crédito e o registro fiscal correspondente.",
            ],
            "departments": "Fiscal parametriza CST, CFOP, base reduzida e ajuste. Compras e comercial validam NCM, produto e destinatário. Contábil separa crédito comum e estorno. Jurídico revisa vigência, convênio e vedação.",
            "documents": "XML, NCM, ficha técnica, contrato, Anexo II, memória de carga efetiva, EFD, guia, laudo quando necessário e parecer de enquadramento.",
            "risks": "Usar redução por analogia; trocar redução de base por alíquota menor; manter crédito quando o item exige estorno; aplicar item a mercadoria fora da descrição.",
        },
        {
            "id": "creditos-presumidos-acumulados",
            "title": "Crédito presumido, crédito acumulado, transferência e utilização",
            "summary": "Como Minas trata créditos especiais: Anexo III para crédito acumulado e Anexo IV para crédito presumido, com controles de autorização, substituição de créditos e prova.",
            "theme": "Créditos fiscais",
            "refs": [
                {"source": "MG_RICMS_2023_ANEXO_III_CREDITO_ACUMULADO", "full_text": True},
                {"source": "MG_RICMS_2023_ANEXO_IV_CREDITO_PRESUMIDO", "full_text": True},
                {"source": "MG_DEC_48589_2023_RICMS_REGULAMENTO", "keywords": ["crédito acumulado", "crédito presumido", "transferência de crédito", "estorno de crédito"]},
            ],
            "analysis": [
                "Crédito presumido não é crédito comum. Ele substitui ou reduz a sistemática normal nos limites do item aplicável, podendo exigir renúncia a outros créditos, condição operacional, período e forma específica de lançamento.",
                "Crédito acumulado exige trilha própria: origem do saldo, motivo da acumulação, autorização, transferência, utilização, destinatário do crédito e escrituração. Exportação, diferimento e redução de base costumam ser portas relevantes.",
                "O ponto de auditoria é a conciliação: saldo fiscal, razão contábil, XML, EFD, pedido, autorização e utilização precisam fechar no mesmo período.",
            ],
            "departments": "Fiscal calcula crédito presumido e controla autorização. Contábil concilia saldo acumulado, estorno e razão. Jurídico valida item, condição e vedação. Financeiro acompanha transferência, uso e reflexo de caixa.",
            "documents": "Anexo III, Anexo IV, XML, EFD, demonstrativo de origem do crédito, pedido, autorização, termo, memória de cálculo, razão contábil e guia.",
            "risks": "Somar crédito presumido com crédito comum vedado; transferir crédito sem autorização; não provar origem do saldo; usar item de crédito presumido fora do produto ou setor.",
        },
        {
            "id": "creditos-exportacao-acumulado",
            "title": "Exportação, não incidência, manutenção de crédito e crédito acumulado",
            "summary": "Como exportação e operações equiparadas conversam com não incidência, manutenção de créditos, transferência e utilização de crédito acumulado em Minas Gerais.",
            "theme": "Exportação e crédito",
            "refs": [
                {"source": "MG_LEI_6763_1975_ICMS", "keywords": ["exportação", "não incidência", "crédito", "mercadoria destinada ao exterior"]},
                {"source": "MG_DEC_48589_2023_RICMS_REGULAMENTO", "keywords": ["exportação", "não incidência", "manutenção do crédito", "crédito acumulado"]},
                {"source": "MG_RICMS_2023_ANEXO_III_CREDITO_ACUMULADO", "keywords": ["exportação", "crédito acumulado", "transferência", "utilização de crédito"]},
            ],
            "analysis": [
                "Exportação costuma estar fora da incidência do ICMS, mas isso não encerra o estudo. A empresa precisa saber se pode manter crédito, como comprova a saída ao exterior e como transforma saldo acumulado em uso econômico.",
                "A não incidência da exportação não é benefício setorial comum; ela decorre de regra constitucional e legal. O controle prático fica nos documentos de exportação, na vinculação da mercadoria e na EFD.",
                "Quando houver crédito acumulado, o Anexo III passa a ser a trilha operacional: origem, pedido, autorização, transferência, utilização e conciliação.",
            ],
            "departments": "Fiscal vincula NF-e, DU-E, averbação e EFD. Exportação comprova embarque e destinatário no exterior. Contábil acompanha crédito acumulado. Jurídico valida manutenção e uso. Financeiro controla transferência ou utilização.",
            "documents": "NF-e, DU-E, comprovante de exportação, contrato, invoice, conhecimento de transporte, EFD, demonstrativo de crédito, pedido e autorização de uso ou transferência.",
            "risks": "Chamar venda indireta de exportação sem prova; perder manutenção de crédito por falha documental; acumular saldo sem trilha de origem; utilizar crédito antes da autorização.",
        },
        {
            "id": "diferimento-regimes-especiais",
            "title": "Diferimento, regimes especiais e disposições especiais de tributação",
            "summary": "Anexo VI e Anexo VIII: diferimento por operação, encerramento, regimes especiais, tratamento setorial, condições, vedações e prova.",
            "theme": "Regimes especiais",
            "refs": [
                {"source": "MG_RICMS_2023_ANEXO_VI_DIFERIMENTO", "full_text": True},
                {"source": "MG_RICMS_2023_ANEXO_VIII_DISPOSICOES_ESPECIAIS", "full_text": True},
                {"source": "MG_DEC_48589_2023_RICMS_REGULAMENTO", "keywords": ["diferimento", "regime especial", "encerramento do diferimento", "disposições especiais"]},
            ],
            "analysis": [
                "Diferimento não elimina o ICMS; ele desloca o lançamento ou pagamento para etapa posterior. Por isso, a matriz precisa indicar mercadoria, operação, responsável, evento de encerramento e documento.",
                "O Anexo VIII contém disposições especiais e regimes setoriais. Em muitos casos, o direito depende de ato, condição, CNAE, estabelecimento, período de apuração ou forma própria de cálculo.",
                "Regime especial deve ser tratado como contrato operacional com o Fisco: quem pode usar, onde, por quanto tempo, em quais operações, com quais vedações e qual prova mensal.",
            ],
            "departments": "Fiscal controla diferimento, encerramento e EFD. Jurídico acompanha regime especial e condições. Operações comprova mercadoria, destino e etapa posterior. Contábil mede débito e crédito. Financeiro guarda guias.",
            "documents": "Anexo VI, Anexo VIII, regime especial, XML, contrato, comprovante de etapa posterior, EFD, memória de encerramento, guia e relatório de condição.",
            "risks": "Tratar diferimento como isenção; não identificar encerramento; usar regime fora do estabelecimento autorizado; deixar de cumprir condição ou de guardar prova mensal.",
        },
        {
            "id": "st-antecipacao-segmentos",
            "title": "Substituição tributária, antecipação, MVA, segmentos, complemento e ressarcimento",
            "summary": "Anexo VII do RICMS/MG: responsabilidade por substituição, mercadorias sujeitas, base presumida, MVA, recolhimento, complemento, restituição e prova.",
            "theme": "Responsabilidade tributária",
            "refs": [
                {"source": "MG_RICMS_2023_ANEXO_VII_ST", "full_text": True},
                {"source": "MG_LEI_6763_1975_ICMS", "keywords": ["substituição tributária", "responsável", "ressarcimento", "restituição"]},
                {"source": "MG_DEC_48589_2023_RICMS_REGULAMENTO", "keywords": ["substituição tributária", "MVA", "antecipação", "ressarcimento", "complemento"]},
            ],
            "analysis": [
                "Substituição tributária não é benefício: é deslocamento de responsabilidade. A leitura começa por mercadoria, NCM/CEST, convênio ou protocolo, operação, origem, destino, responsável, base presumida e MVA.",
                "Complemento e ressarcimento precisam ser tratados como capítulos próprios do processo. A empresa deve provar imposto retido, operação subsequente, preço real, estoque e escrituração.",
                "Em Minas, o Anexo VII é o mapa operacional da ST. Sem ele, MVA, pauta, responsável e prazo podem ficar errados mesmo que o produto pareça semelhante.",
            ],
            "departments": "Fiscal controla NCM/CEST, MVA, pauta, CST e recolhimento. Compras valida fornecedor/substituto. Comercial orienta preço. Logística prova transporte. Financeiro guarda guias. Auditoria cruza estoque, XML e EFD.",
            "documents": "XML, CT-e, MDF-e, NCM, CEST, convênio, protocolo, pauta, MVA, DAE/GNRE, EFD, cadastro de item, comprovante de recolhimento e memória por produto.",
            "risks": "Aplicar ST por semelhança; ignorar complemento ou ressarcimento; usar MVA vencida; recolher por UF errada; não provar retenção anterior.",
        },
        {
            "id": "documentos-efd-prova",
            "title": "Documentos fiscais, EFD, escrituração, registros e prova digital",
            "summary": "Anexo V: como a regra aparece no XML, nos documentos fiscais, na EFD, nos ajustes, nos livros e no dossiê de benefício, crédito, ST ou regime.",
            "theme": "Prova digital",
            "refs": [
                {"source": "MG_RICMS_2023_ANEXO_V_DOCUMENTOS_EFD", "full_text": True},
                {"source": "MG_DEC_48589_2023_RICMS_REGULAMENTO", "keywords": ["documento fiscal", "NF-e", "CT-e", "Escrituração Fiscal Digital", "EFD", "livros fiscais"]},
                {"source": "MG_LEI_6763_1975_ICMS", "keywords": ["documentos fiscais", "livros fiscais", "escrituração", "obrigação acessória", "penalidade"]},
            ],
            "analysis": [
                "A tese tributária só vira defesa quando aparece no documento certo. Em Minas, o Anexo V conecta documento fiscal, escrituração, registros digitais, ajustes e obrigações acessórias.",
                "EFD não cria direito. Ela declara uma tese que precisa existir na Lei nº 6.763/1975, no RICMS/MG, em anexo, regime especial ou ato aplicável.",
                "Benefício, redução, diferimento, crédito presumido, crédito acumulado e ST devem deixar rastro: CST, CFOP, informações complementares, ajuste, registro, guia, memória e conciliação contábil.",
            ],
            "departments": "Fiscal transmite e reconcilia EFD. TI mantém parâmetros de emissão. Cadastro cuida de item, NCM e CST. Contábil fecha ajustes. Financeiro guarda guias. Auditoria valida coerência mensal.",
            "documents": "NF-e, NFC-e, CT-e, MDF-e, EFD, recibo, registros e ajustes, livros fiscais, cadastro do item, XML, comprovante de guia, memória de cálculo e ato legal.",
            "risks": "Declarar ajuste sem direito material; usar CST incompatível; transmitir EFD sem memória; não manter dossiê local do benefício; perder a prova da condição do regime.",
        },
        {
            "id": "mapa-revisado-beneficios",
            "title": "Mapa revisado dos benefícios de ICMS de Minas Gerais",
            "summary": "Inventário didático dos grupos de benefícios mineiros: redução de base, crédito presumido, crédito acumulado, diferimento, disposições especiais, regimes, ST e prova.",
            "theme": "Inventário de benefícios",
            "refs": [
                {"source": "MG_RICMS_2023_ANEXO_II_REDUCAO_BASE", "full_text": True},
                {"source": "MG_RICMS_2023_ANEXO_III_CREDITO_ACUMULADO", "full_text": True},
                {"source": "MG_RICMS_2023_ANEXO_IV_CREDITO_PRESUMIDO", "full_text": True},
                {"source": "MG_RICMS_2023_ANEXO_VI_DIFERIMENTO", "full_text": True},
                {"source": "MG_RICMS_2023_ANEXO_VIII_DISPOSICOES_ESPECIAIS", "keywords": ["benefício fiscal", "regime especial", "crédito presumido", "diferimento", "redução de base de cálculo"]},
                {"source": "MG_RICMS_2023_ANEXO_V_DOCUMENTOS_EFD", "keywords": ["EFD", "documentos fiscais", "escrituração"]},
            ],
            "analysis": [
                "O mapa mineiro precisa ser lido por técnica e por anexo. Redução de base está no Anexo II, crédito acumulado no Anexo III, crédito presumido no Anexo IV, diferimento no Anexo VI e disposições especiais no Anexo VIII.",
                "A organização por setor vem depois da técnica: agro, alimentos, medicamentos, máquinas, energia, transporte, indústria, mineração, comércio e importação só entram quando a descrição legal alcança produto, operação, destinatário e período.",
                "A matriz segura para qualquer benefício em Minas contém: ato, anexo, item, produto/operação, destinatário, vigência, condição, vedação, documento, EFD, guia, crédito/estorno e revisão de acumulação.",
            ],
            "departments": "Jurídico guarda a matriz de benefícios. Fiscal parametriza cada técnica. Compras, comercial e operações comprovam produto, destino e finalidade. Contábil mede crédito e estorno. Financeiro guarda guias e autorizações.",
            "documents": "Lei, decreto, anexo, item, regime especial quando houver, XML, EFD, NCM, ficha técnica, memória de cálculo, guia, comprovante de condição e parecer de enquadramento.",
            "risks": "Confundir técnica do benefício; aplicar por setor sem ler o item; ignorar vedação de acumulação; perder condição do regime; usar benefício vencido ou sem prova.",
        },
        {
            "id": "fiscalizacao-riscos",
            "title": "Fiscalização, multas, glosa, regime especial de controle e defesa",
            "summary": "Pontos de controle do crédito tributário mineiro: documento, EFD, glosa de crédito, descumprimento de condição, perda de regime, autuação e correção de causa.",
            "theme": "Fiscalização e regularização",
            "refs": [
                {"source": "MG_LEI_6763_1975_ICMS", "keywords": ["penalidade", "multa", "infração", "fiscalização", "crédito tributário", "regime especial de controle"]},
                {"source": "MG_DEC_48589_2023_RICMS_REGULAMENTO", "keywords": ["penalidade", "infração", "fiscalização", "glosa", "documentos fiscais", "EFD"]},
                {"source": "MG_RICMS_2023_ANEXO_V_DOCUMENTOS_EFD", "keywords": ["documentos fiscais", "escrituração", "EFD", "obrigação acessória"]},
            ],
            "analysis": [
                "Fiscalização fecha o ciclo da tese. Se a empresa aplicou redução sem item, crédito presumido sem condição, crédito acumulado sem autorização, diferimento sem encerramento ou ST sem enquadramento, o erro aparece nos documentos.",
                "A defesa começa antes da autuação: matriz legal, dossiê mensal, memória de cálculo, prova da condição, autorização de crédito e conciliação contábil.",
                "Regularizar não é só pagar. Depois de glosa, autuação ou perda de regime, a empresa precisa corrigir cadastro, XML, EFD, memória, recolhimento e política interna.",
            ],
            "departments": "Jurídico conduz defesa, risco e revisão de regime. Fiscal reconstrói documentos. Contábil concilia crédito, provisão e estorno. Financeiro acompanha guia e eventual parcelamento. Auditoria ajusta controles internos.",
            "documents": "Auto de infração, notificação, processo administrativo, XML, EFD, guia, comprovante de pagamento, regime especial, autorização de crédito, memória e relatório de correção de causa.",
            "risks": "Defender benefício sem dossiê; manter parametrização errada; não retificar EFD; perder autorização; pagar sem corrigir a causa operacional.",
        },
    ],
    "RJ": [
        {
            "id": "icms-regra-matriz",
            "title": "ICMS/RJ: incidência, fato gerador, contribuinte, não incidência e regra maior",
            "summary": "A porta de entrada do ICMS fluminense: quando o imposto nasce, quem responde, quais operações entram no campo de incidência e quando a tese começa por não incidência.",
            "theme": "Regra matriz",
            "refs": [
                {"source": "RJ_LEI_2657_1996_ICMS", "articles": ["1", "2", "3", "4", "5", "6", "7", "8", "9"]},
                {"source": "RJ_DEC_27427_2000_RICMS_LIVRO_I_OBRIGACAO_PRINCIPAL", "articles": ["1", "2", "3", "4", "5", "6", "7"]},
            ],
            "analysis": [
                "A Lei nº 2.657/1996 fixa a materialidade do ICMS/RJ; o Livro I do RICMS transforma essa regra em operação fiscal. A leitura correta começa pelo fato gerador, não pelo benefício.",
                "Não incidência, imunidade, isenção, suspensão e diferimento não são sinônimos. Se o fato não entra no campo do imposto, a conclusão é de não incidência. Se entra e a lei dispensa ou posterga a cobrança, já estamos no terreno das exceções.",
                "Em auditoria, a primeira pergunta é simples: houve circulação de mercadoria, prestação de transporte, prestação de comunicação, importação, entrada interestadual para consumo/ativo ou outra hipótese legal? Só depois vêm alíquota, crédito, benefício e documento.",
            ],
            "departments": "Fiscal define CFOP, CST/CSOSN, fato gerador e responsável. Jurídico valida incidência, não incidência e limites da lei. Contábil concilia débito, crédito e custo. Comercial e logística comprovam operação, destinatário e circulação.",
            "documents": "XML, CT-e, MDF-e, contrato, pedido, comprovante de entrega, DI/DUIMP quando houver importação, EFD, memória de enquadramento e dispositivo legal usado na operação.",
            "risks": "Começar pelo benefício sem provar incidência; tratar não incidência como isenção; deixar evento de importação, transporte ou comunicação sem documento; usar CST incompatível com o fato gerador.",
        },
        {
            "id": "base-aliquota-apuracao",
            "title": "Base de cálculo, alíquotas, FECP, DIFAL, importação e apuração do ICMS/RJ",
            "summary": "Como o fato gerador vira valor tributável: base, parcelas integrantes, alíquota interna, interestadual, FECP, diferencial, importação e apuração.",
            "theme": "Carga tributária",
            "refs": [
                {"source": "RJ_LEI_2657_1996_ICMS", "articles": ["14", "15", "16", "17", "18", "19", "20", "21", "22"]},
                {"source": "RJ_DEC_27427_2000_RICMS_LIVRO_I_OBRIGACAO_PRINCIPAL", "articles": ["4", "5", "6", "7", "8", "14", "15", "16", "17", "18", "19", "20", "21"]},
                {"source": "RJ_DEC_27427_2000_RICMS_LIVRO_XI_IMPORTACAO", "keywords": ["base de cálculo", "desembaraço", "importação", "recolhimento"]},
            ],
            "analysis": [
                "Alíquota não se lê isoladamente. A base de cálculo determina quais valores entram na operação; a alíquota incide sobre essa base; e benefícios como redução de base alteram a carga sem apagar a memória do cálculo.",
                "No Rio de Janeiro, FECP, importação, energia, combustíveis, DIFAL, transporte e operações interestaduais exigem revisão de vigência. A parametrização do ERP precisa guardar base cheia, ajustes, adicional, carga efetiva e guia.",
                "Redução de base não é troca informal de alíquota. O documento e a EFD devem revelar a técnica jurídica usada, porque a fiscalização cruza XML, registro, código de benefício, livro e recolhimento.",
            ],
            "departments": "Fiscal parametriza base, alíquota, FECP, DIFAL e recolhimento. Contábil mede crédito e custo. Financeiro guarda DARJ/GNRE. Compras e comercial mantêm NCM, destinatário e natureza da operação.",
            "documents": "XML, memória de cálculo, tabela de alíquotas vigente, NCM, cadastro de produto, EFD, DARJ/GNRE, DI/DUIMP na importação e demonstrativo de carga efetiva.",
            "risks": "Aplicar alíquota sem reconstruir a base; esquecer FECP; lançar redução como alíquota menor; usar regra atual em fato gerador antigo; calcular DIFAL sem validar destinatário, finalidade e período.",
        },
        {
            "id": "beneficios-matriz-lc160",
            "title": "Benefícios fiscais do RJ: matriz legal, Manual de Benefícios, LC 160 e CONFAZ",
            "summary": "Como o RJ organiza isenção, não incidência, redução de base, suspensão, diferimento, crédito presumido, tributação sobre saída e regimes especiais.",
            "theme": "Benefícios fiscais",
            "refs": [
                {"source": "RJ_DEC_27815_2001_MANUAL_BENEFICIOS", "keywords": ["Manual de Diferimento", "Ampliação de Prazo", "Suspensão", "Incentivos e Benefícios", "Decreto"]},
                {"source": "RJ_ROTEIRO_BENEFICIOS_FISCAIS_TRANSPARENCIA_2025", "full_text": True},
                {"source": "RJ_TABELA_CODIGO_BENEFICIO_CST_2026", "keywords": ["Isenção", "Não incidência", "Redução", "Diferimento", "Suspensão", "Crédito presumido"]},
                {"source": "RJ_PORTAL_TRANSPARENCIA_BENEFICIOS_2026", "full_text": True},
            ],
            "analysis": [
                "O Decreto nº 27.815/2001 aprova o Manual de Diferimento, Ampliação de Prazo, Suspensão e Incentivos/Benefícios. Ele é a chave operacional do RJ: a empresa deve localizar a norma material, a natureza do benefício e a forma de demonstrar o uso.",
                "A LC 160/2017 e o Convênio ICMS 190/2017 explicam a camada de convalidação e reinstituição de benefícios. Eles não substituem a leitura da lei estadual, do decreto, da resolução, do manual e da tabela de códigos aplicável ao caso concreto.",
                "A matriz de benefício fluminense precisa separar espécie jurídica: isenção, não incidência, redução de base, suspensão, diferimento, crédito presumido, tributação sobre faturamento/receita/saída, regime especial e contrapartida FOT quando houver.",
            ],
            "departments": "Jurídico mantém a matriz legal e a vigência. Fiscal transforma a regra em CST, CFOP, cBenef ou cCredPresumido, ajuste e EFD. Contábil mede crédito, estorno e custo. Financeiro controla FOT, guias e recolhimentos.",
            "documents": "Norma do benefício, Manual de Benefícios, tabela de códigos, XML, EFD, memória de cálculo, parecer de enquadramento, comprovante de condição, ato concessivo e guia de contrapartida.",
            "risks": "Usar benefício por nome comercial; aplicar código sem norma material; ignorar FOT; acumular benefícios incompatíveis; não comprovar vigência, condição ou setor alcançado.",
        },
        {
            "id": "isencoes-reducoes-creditos",
            "title": "Isenções, reduções de base, créditos presumidos e códigos de benefício do RJ",
            "summary": "Leitura aplicada das espécies de benefício: produto, operação, destinatário, período, CST, código, EFD, estorno, manutenção de crédito e prova.",
            "theme": "Benefícios por técnica",
            "refs": [
                {"source": "RJ_TABELA_CODIGO_BENEFICIO_CST_2026", "full_text": True},
                {"source": "RJ_MANUAL_DOCUMENTOS_BENEFICIOS_2025", "keywords": ["CST 20", "CST 30", "CST 40", "CST 51", "CST 53", "CST 70", "cBenef", "crédito presumido"]},
                {"source": "RJ_DEC_27427_2000_RICMS_LIVRO_X_REGIMES_ESPECIAIS", "keywords": ["isenção", "redução de base", "crédito presumido", "regime especial", "benefício"]},
                {"source": "RJ_LEI_2657_1996_ICMS", "keywords": ["isenção", "redução de base", "crédito presumido", "diferimento"]},
            ],
            "analysis": [
                "Isenção dispensa o débito dentro de hipótese fechada; redução de base muda a grandeza tributável; crédito presumido atua na apuração; suspensão e diferimento controlam evento futuro. A mesma mercadoria pode exigir respostas diferentes conforme operação e destinatário.",
                "A tabela de código de benefício x CST não cria o benefício. Ela documenta a tese no XML. Primeiro se prova a norma; depois se escolhe CST, cBenef ou cCredPresumido e o registro correto na EFD.",
                "Crédito presumido exige cuidado especial: percentual, base, vedações, estorno de crédito comum, acumulação com outros benefícios e reflexo no FOT podem mudar completamente a economia da operação.",
            ],
            "departments": "Fiscal parametriza CST, CFOP, código de benefício, ajuste e EFD. Cadastro controla NCM e item. Compras e comercial provam produto e destinatário. Contábil separa crédito comum e presumido. Jurídico revisa vedações.",
            "documents": "XML, tabela de benefício, Manual de Benefícios, EFD, cadastro do item, NCM, laudo técnico quando necessário, memória de crédito, guia FOT quando houver e parecer de enquadramento.",
            "risks": "Informar código sem direito; confundir redução com alíquota menor; manter crédito quando a norma manda estornar; acumular crédito presumido com outro favor vedado; perder prova do produto ou da condição.",
        },
        {
            "id": "fot-feef-contrapartidas",
            "title": "FOT/FEEF: contrapartida, redução indireta do benefício e controle mensal",
            "summary": "Como o Fundo Orçamentário Temporário conversa com incentivos, benefícios fiscais, financeiro-fiscais, base de cálculo, EFD, DARJ, exceções e transição até 2032.",
            "theme": "Fundo e contrapartida",
            "refs": [
                {"source": "RJ_LEI_8645_2019_FOT", "full_text": True},
                {"source": "RJ_PORTAL_FEEF_FOT_2026", "full_text": True},
                {"source": "RJ_ROTEIRO_BENEFICIOS_FISCAIS_TRANSPARENCIA_2025", "keywords": ["FOT", "FEEF", "benefício fiscal", "depósito", "Lei nº 8.645"]},
                {"source": "RJ_MANUAL_DOCUMENTOS_BENEFICIOS_2025", "keywords": ["FOT", "EFD", "benefícios fiscais", "Anexo XVIII"]},
            ],
            "analysis": [
                "No RJ, muitos benefícios não podem ser estudados sem FOT. A fruição de incentivo ou benefício pode depender de depósito calculado sobre a diferença entre o ICMS com e sem o benefício, conforme a legislação estadual aplicável.",
                "O FOT reduz a vantagem econômica do benefício, mas não apaga a técnica original. A empresa continua precisando provar isenção, redução de base, crédito presumido, diferimento ou regime e, além disso, demonstrar o depósito exigido.",
                "O controle deve ser mensal e por estabelecimento: benefício usado, base comparativa, percentual aplicável, exceção legal, DARJ, EFD e conciliação contábil.",
            ],
            "departments": "Fiscal calcula a diferença do ICMS com e sem benefício. Financeiro paga DARJ. Contábil reconhece custo, crédito e conciliação. Jurídico valida exceções, percentuais e vigência. Auditoria revisa a memória mensal.",
            "documents": "Lei do FOT, portal da SEFAZ/RJ, DARJ, EFD, XML, memória comparativa, relação de benefícios usados, parecer de exceção e comprovante de pagamento.",
            "risks": "Usar benefício sem recolher FOT; aplicar percentual errado; não separar benefício oneroso e não oneroso; excluir operação sem base expressa; pagar guia sem memória de cálculo defensável.",
        },
        {
            "id": "regimes-setoriais-industria-repetro",
            "title": "Regimes setoriais: indústria, Repetro, petróleo e tratamento tributário especial",
            "summary": "Leitura de benefícios setoriais relevantes: Lei nº 4.531/2005, Lei nº 8.890/2020, Repetro-SPED, Repetro-Industrialização, regimes especiais e obrigações de adesão.",
            "theme": "Programas setoriais",
            "refs": [
                {"source": "RJ_LEI_4531_2005_SETORIAL_INDUSTRIA", "full_text": True},
                {"source": "RJ_LEI_8890_2020_REPETRO", "full_text": True},
                {"source": "RJ_RES_SEFAZ_766_2025_REPETRO_EFD", "full_text": True},
                {"source": "RJ_DEC_27427_2000_RICMS_LIVRO_X_REGIMES_ESPECIAIS", "keywords": ["regime especial", "tratamento", "benefício", "diferimento"]},
            ],
            "analysis": [
                "Regime setorial não é benefício genérico para qualquer empresa do setor. A lei costuma exigir atividade, estabelecimento no Estado, regularidade, operação específica, termo, comunicação, habilitação ou documento próprio.",
                "Na Lei nº 4.531/2005, o ponto de auditoria é saber se o estabelecimento industrial, o produto, a operação e as vedações realmente cabem no tratamento. No Repetro, a leitura passa por bem, mercadoria, exploração ou produção, habilitação e adesão.",
                "Regimes especiais devem ser tratados como compromisso operacional com o Fisco: prazo, condição, perda, exclusão, escrituração e prova de que cada operação está dentro do ato que sustenta a fruição.",
            ],
            "departments": "Jurídico valida elegibilidade e ato de adesão. Fiscal parametriza operação, CST, código e EFD. Operações comprova atividade e destinação. Contábil mede carga efetiva. Financeiro controla FOT e guias.",
            "documents": "Lei setorial, ato concessivo ou comunicação, XML, EFD, contrato, habilitação Repetro quando aplicável, cadastro de estabelecimento, memória do benefício, DARJ e relatório de regularidade.",
            "risks": "Aplicar regime a estabelecimento não habilitado; ignorar vedação de consumidor final; usar Repetro fora do bem ou operação admitidos; perder benefício por irregularidade cadastral ou fiscal.",
        },
        {
            "id": "creditos-exportacao-saldo-credor",
            "title": "Exportação, não incidência, manutenção de crédito, saldo credor e transferência",
            "summary": "Como exportação, remessa com fim específico, crédito acumulado, saldo credor e transferência se conectam ao ICMS/RJ e à prova documental.",
            "theme": "Exportação e crédito",
            "refs": [
                {"source": "RJ_LEI_2657_1996_ICMS", "keywords": ["exportação", "não incidência", "crédito", "mercadoria destinada ao exterior"]},
                {"source": "RJ_DEC_27427_2000_RICMS_LIVRO_I_OBRIGACAO_PRINCIPAL", "keywords": ["exportação", "não incidência", "crédito", "exterior"]},
                {"source": "RJ_DEC_27427_2000_RICMS_LIVRO_III_CREDITO_ACUMULADO", "full_text": True},
                {"source": "RJ_MANUAL_DOCUMENTOS_BENEFICIOS_2025", "keywords": ["exportação", "EFD", "cBenef", "crédito"]},
            ],
            "analysis": [
                "Exportação normalmente começa como não incidência, mas a operação não termina aí. A empresa precisa provar saída ao exterior, vínculo da mercadoria e eventual direito de manutenção, utilização ou transferência de crédito.",
                "Saldo credor é ativo fiscal sensível. A origem do crédito, a operação que o gerou, a EFD e a autorização de uso precisam estar conciliadas antes de qualquer aproveitamento econômico.",
                "Venda com fim específico de exportação exige prova própria. Sem DU-E, averbação, contrato, destinatário e rastreio documental, a tese pode se descolar do fato.",
            ],
            "departments": "Fiscal vincula NF-e, CFOP, CST, DU-E e EFD. Exportação guarda contrato e embarque. Contábil controla saldo credor. Jurídico valida não incidência e manutenção. Financeiro acompanha pedidos e autorizações.",
            "documents": "NF-e, DU-E, invoice, contrato, comprovante de embarque, CT-e, EFD, demonstrativo de crédito, pedido de transferência ou utilização e autorização fiscal quando exigida.",
            "risks": "Chamar venda interna de exportação sem fim específico; manter crédito sem prova; transferir saldo antes da autorização; não amarrar XML, EFD e documentos aduaneiros.",
        },
        {
            "id": "st-antecipacao-segmentos",
            "title": "Substituição tributária, antecipação, combustíveis, veículos, MVA, complemento e ressarcimento",
            "summary": "Livro II, combustíveis e veículos: responsável, substituto, substituído, base presumida, retenção, operações subsequentes, complemento, ressarcimento e prova.",
            "theme": "Responsabilidade tributária",
            "refs": [
                {"source": "RJ_DEC_27427_2000_RICMS_LIVRO_II_ST", "full_text": True},
                {"source": "RJ_DEC_27427_2000_RICMS_LIVRO_XII_COMBUSTIVEIS", "full_text": True},
                {"source": "RJ_DEC_27427_2000_RICMS_LIVRO_XIII_VEICULOS", "full_text": True},
                {"source": "RJ_LEI_2657_1996_ICMS", "keywords": ["substituição tributária", "responsável", "retenção", "ressarcimento"]},
            ],
            "analysis": [
                "ST não é benefício. É técnica de responsabilidade e antecipação. A leitura começa por mercadoria, NCM/CEST, operação, origem, destino, responsável, base presumida, MVA ou pauta.",
                "Combustíveis e veículos têm controles próprios. Em muitos casos, a mercadoria é altamente fiscalizada, com regras próprias de retenção, complemento, ressarcimento e documentos.",
                "O contribuinte substituído também precisa de prova: imposto retido, estoque, operação subsequente, ressarcimento ou complemento, EFD e XML coerentes.",
            ],
            "departments": "Fiscal controla NCM/CEST, MVA, base e guia. Compras valida fornecedor substituto. Comercial observa preço e saída. Logística guarda transporte. Contábil concilia estoque e ressarcimento.",
            "documents": "XML, CT-e, MDF-e, NCM, CEST, pauta ou MVA, DARJ/GNRE, EFD, estoque, comprovante de retenção, planilha de complemento ou ressarcimento.",
            "risks": "Aplicar ST por descrição parecida; usar MVA vencida; ignorar complemento ou ressarcimento; não provar retenção anterior; recolher para UF errada.",
        },
        {
            "id": "importacao-transporte-veiculos-combustiveis",
            "title": "Importação, transporte, veículos, combustíveis, energia e setores de alto controle",
            "summary": "Livros XI, IV, IX, XII e XIII: desembaraço, transporte, serviços, veículos automotores, combustíveis, documentos, responsabilidade e benefícios setoriais.",
            "theme": "Setores fiscalizados",
            "refs": [
                {"source": "RJ_DEC_27427_2000_RICMS_LIVRO_XI_IMPORTACAO", "full_text": True},
                {"source": "RJ_DEC_27427_2000_RICMS_LIVRO_IV_TRANSPORTE", "keywords": ["transporte", "prestação", "documento fiscal", "ICMS"]},
                {"source": "RJ_DEC_27427_2000_RICMS_LIVRO_IX_TRANSPORTE_SERVICOS", "keywords": ["transporte", "comunicação", "documento fiscal", "prestação"]},
                {"source": "RJ_DEC_27427_2000_RICMS_LIVRO_XII_COMBUSTIVEIS", "keywords": ["combustível", "óleo diesel", "retenção", "substituição tributária"]},
                {"source": "RJ_DEC_27427_2000_RICMS_LIVRO_XIII_VEICULOS", "keywords": ["veículo", "automotor", "base de cálculo", "substituição tributária"]},
            ],
            "analysis": [
                "Importação deve ser lida pelo desembaraço, base, recolhimento, local, titularidade e eventual benefício. O benefício de importação não se presume pela existência de porto ou aeroporto no Estado.",
                "Transporte, energia, comunicação, combustíveis e veículos são campos de alta materialidade fiscal. O documento certo é parte da própria tese: CT-e, NF-e, NFC-e, MDF-e, registro e guia.",
                "Setor regulado exige prova operacional: contrato, rota, veículo, combustível, importador, destinatário, habilitação e aderência ao regime.",
            ],
            "departments": "Comércio exterior prova importação e desembaraço. Fiscal define base, alíquota, ST e documento. Logística guarda CT-e/MDF-e. Operações comprova uso e destino. Financeiro guarda guias.",
            "documents": "DI/DUIMP, invoice, comprovante de desembaraço, NF-e de entrada, CT-e, MDF-e, XML, EFD, contrato, laudo ou ficha técnica, guia e memória de base.",
            "risks": "Aplicar benefício de importação sem cumprir desembaraço/destino; separar transporte do documento; ignorar ST de combustíveis ou veículos; perder prova de uso operacional.",
        },
        {
            "id": "documentos-efd-prova",
            "title": "Documentos fiscais, EFD, cBenef, cCredPresumido, Anexo XVIII e prova digital",
            "summary": "Como a tese aparece no XML, na EFD ICMS/IPI, nos códigos de benefício, nos ajustes, no documento fiscal e no dossiê mensal.",
            "theme": "Prova digital",
            "refs": [
                {"source": "RJ_MANUAL_DOCUMENTOS_BENEFICIOS_2025", "full_text": True},
                {"source": "RJ_TABELA_CODIGO_BENEFICIO_CST_2026", "full_text": True},
                {"source": "RJ_RES_SEFAZ_604_2024_EFD_BENEFICIOS", "full_text": True},
                {"source": "RJ_RES_SEFAZ_754_2025_CCREDPRESUMIDO", "full_text": True},
                {"source": "RJ_DEC_27427_2000_RICMS_LIVRO_VI_OBRIGACOES_ACESSORIAS", "keywords": ["NF-e", "EFD", "documento fiscal", "escrituração"]},
            ],
            "analysis": [
                "No RJ, a prova do benefício passa por documento fiscal e EFD. O Manual de emissão/escrituração explica que a regra se aplica ao contribuinte que usufrui diretamente do benefício e precisa demonstrar CST, código, ajuste e reflexo na escrituração.",
                "cBenef e cCredPresumido são consequências documentais. A origem continua sendo a lei, decreto, resolução, manual ou ato concessivo. O código errado pode transformar uma tese correta em inconsistência digital.",
                "A EFD deve fechar a narrativa: XML, CST, base, alíquota, redução de base, crédito presumido, diferimento, suspensão, FOT e memória de cálculo precisam conversar.",
            ],
            "departments": "Fiscal emite e escritura. TI mantém cadastro fiscal e regra de emissão. Cadastro cuida de NCM, CST e código. Contábil fecha ajustes. Jurídico valida a norma. Auditoria monta dossiê mensal.",
            "documents": "NF-e, NFC-e, CT-e, MDF-e, EFD ICMS/IPI, recibo, registros C/D/E, tabela de código, cBenef, cCredPresumido, memória de cálculo, guia FOT e ato legal.",
            "risks": "Declarar código sem norma; usar CST incompatível; escriturar benefício no registro errado; esquecer FOT; não manter dossiê mensal; tratar manual operacional como substituto da lei material.",
        },
        {
            "id": "mapa-revisado-beneficios",
            "title": "Mapa revisado dos benefícios de ICMS do Rio de Janeiro",
            "summary": "Inventário didático dos benefícios fluminenses por técnica e grupo: isenção, redução, suspensão, diferimento, crédito presumido, FOT, Repetro, indústria, transporte, ST, cBenef e EFD.",
            "theme": "Inventário de benefícios",
            "refs": [
                {"source": "RJ_PORTAL_TRANSPARENCIA_BENEFICIOS_2026", "full_text": True},
                {"source": "RJ_ROTEIRO_BENEFICIOS_FISCAIS_TRANSPARENCIA_2025", "full_text": True},
                {"source": "RJ_TABELA_CODIGO_BENEFICIO_CST_2026", "full_text": True},
                {"source": "RJ_DEC_27815_2001_MANUAL_BENEFICIOS", "keywords": ["Manual de Diferimento", "Suspensão", "Incentivos e Benefícios"]},
                {"source": "RJ_LEI_8645_2019_FOT", "keywords": ["benefícios", "incentivos", "FOT", "depósito"]},
                {"source": "RJ_MANUAL_DOCUMENTOS_BENEFICIOS_2025", "keywords": ["isenção", "redução de base", "crédito presumido", "diferimento", "EFD"]},
            ],
            "analysis": [
                "O mapa do RJ deve ser lido em três camadas. Primeira: norma material do benefício. Segunda: classificação no Manual de Benefícios e na tabela de códigos. Terceira: documento, EFD, FOT e prova mensal.",
                "Por técnica, os grupos centrais são isenção, não incidência, redução de base, suspensão, diferimento, crédito presumido, tributação sobre saída/faturamento/receita, regime especial e contrapartida de fundo.",
                "Por setor, o estudo abre rotas para indústria, petróleo e gás/Repetro, importação, transporte, combustíveis, veículos, energia, atacado, comércio, saúde, alimentos, cadeia produtiva e regimes especiais. Cada rota só é defensável quando produto, operação, destinatário, prazo e condição estão no texto legal.",
            ],
            "departments": "Jurídico mantém inventário e vigência. Fiscal parametriza por técnica. Comercial, compras e operações provam produto e destino. Contábil mede crédito, estorno e custo. Financeiro paga FOT e guias.",
            "documents": "Manual de Benefícios, roteiro de benefícios, tabela de códigos, lei/decreto/resolução, XML, EFD, parecer de enquadramento, memória de cálculo, DARJ, autorização e relatório de condição.",
            "risks": "Mapear benefício apenas por palavra-chave; confundir técnica; deixar setor sem norma expressa; usar benefício sem FOT; esquecer que código documental não substitui a lei.",
        },
        {
            "id": "fiscalizacao-riscos",
            "title": "Fiscalização, penalidades, glosa, perda de benefício, consulta e defesa",
            "summary": "Pontos de controle do ICMS/RJ: documento, EFD, benefício, FOT, crédito, ST, importação, regime especial, autuação, correção de causa e defesa.",
            "theme": "Fiscalização e regularização",
            "refs": [
                {"source": "RJ_LEI_2657_1996_ICMS", "keywords": ["penalidade", "multa", "fiscalização", "infração", "crédito tributário"]},
                {"source": "RJ_DEC_27427_2000_RICMS_LIVRO_VI_OBRIGACOES_ACESSORIAS", "keywords": ["documento fiscal", "fiscalização", "escrituração", "EFD", "penalidade"]},
                {"source": "RJ_MANUAL_DOCUMENTOS_BENEFICIOS_2025", "keywords": ["retificação", "EFD", "benefício", "documento fiscal", "controle"]},
                {"source": "RJ_PORTAL_FEEF_FOT_2026", "keywords": ["FOT", "depósito", "EFD", "DARJ"]},
            ],
            "analysis": [
                "Fiscalização fecha a leitura. Se a tese está correta na lei, mas errada no XML, na EFD, no código, no FOT ou na memória, o risco permanece.",
                "Glosa de crédito e perda de benefício normalmente nascem de falhas simples: produto fora da descrição, destinatário errado, vigência encerrada, regime vencido, FOT não recolhido, código documental incorreto ou ausência de prova da condição.",
                "A defesa boa começa antes da autuação. O portal deve ensinar o contribuinte a manter dossiê mensal, parecer de enquadramento, conciliação contábil e rotina de revisão de alterações normativas.",
            ],
            "departments": "Jurídico conduz consulta, defesa e matriz de risco. Fiscal reconstrói XML e EFD. Contábil mede crédito, estorno e provisão. Financeiro guarda guias. Auditoria corrige cadastro, processo e causa raiz.",
            "documents": "Auto de infração, intimação, consulta tributária, XML, EFD, DARJ, comprovante FOT, parecer de enquadramento, regime especial, memória de cálculo, relatório de correção e provas operacionais.",
            "risks": "Defender benefício sem dossiê; corrigir guia sem retificar EFD; pagar autuação sem ajustar cadastro; ignorar alteração normativa; não provar condição, vigência ou operação real.",
        },
    ],
}


STANDARD_STATE_SOURCE_SETS = {
    "SP": {
        "name": "São Paulo",
        "hero": "Legislação estadual em tela: Lei nº 6.374/1989, RICMS/2000 integral, Anexos I, II e III, substituição tributária, regimes especiais, cBenef, EFD e prova fiscal.",
        "material": "Lei nº 6.374/1989, Decreto nº 45.490/2000 (RICMS/SP integral), Portaria SRE nº 70/2025 e página de cBenef da SEFAZ/SP.",
        "benefits": "Isenções, reduções de base, créditos outorgados, diferimento, suspensão, regimes especiais, alimentos, agro, medicamentos, veículos, eletrônicos, informática, energia, transporte, importação, indústria, comércio, ST, cBenef e prova fiscal.",
        "law": ["SP_LEI_6374_1989_ICMS"],
        "ricms": ["SP_RICMS_2000_INTEGRAL"],
        "benefits_sources": ["SP_RICMS_2000_INTEGRAL"],
        "program_sources": ["SP_RICMS_2000_INTEGRAL"],
        "st_sources": ["SP_RICMS_2000_INTEGRAL"],
        "docs_sources": ["SP_PORTARIA_SRE_70_2025_CBENEF", "SP_PORTAL_CBENEF_NFE", "SP_RICMS_2000_INTEGRAL"],
        "fund_name": "contrapartidas, regime especial e requisitos de fruição",
        "program_name": "regimes especiais paulistas, crédito outorgado e tratamentos setoriais do RICMS/SP",
    },
    "PR": {
        "name": "Paraná",
        "hero": "Legislação estadual em tela: Lei nº 11.580/1996, RICMS/PR, benefícios fiscais de caráter geral, Paraná Competitivo, ST, documentos, EFD e prova por assunto.",
        "material": "Lei nº 11.580/1996, Decreto nº 7.871/2017 (RICMS/PR), página de benefícios fiscais de caráter geral e Programa Paraná Competitivo.",
        "benefits": "Imunidade, não incidência, isenção, redução de base, crédito presumido, diferimento, suspensão, Paraná Competitivo, benefícios setoriais, agro, saúde, energia, indústria, comércio exterior, ST, documentos e prova fiscal.",
        "law": ["PR_LEI_11580_1996_ICMS"],
        "ricms": ["PR_DEC_7871_2017_RICMS"],
        "benefits_sources": ["PR_DEC_7871_2017_RICMS", "PR_PORTAL_BENEFICIOS_GERAIS"],
        "program_sources": ["PR_PROGRAMA_PARANA_COMPETITIVO", "PR_DEC_7721_2024_PARANA_COMPETITIVO", "PR_DEC_7871_2017_RICMS"],
        "st_sources": ["PR_DEC_7871_2017_RICMS"],
        "docs_sources": ["PR_CODIGO_BENEFICIO_FISCAL", "PR_TABELA_CBENEF_CST", "PR_NPF_53_2018_CBENEF", "PR_DEC_7871_2017_RICMS"],
        "fund_name": "Paraná Competitivo, SISCRED e condições de transferência de créditos",
        "program_name": "Paraná Competitivo, crédito presumido, dilação de prazo e investimento produtivo",
    },
    "RS": {
        "name": "Rio Grande do Sul",
        "hero": "Legislação estadual em tela: Decreto nº 37.699/1997, RICMS/RS integral, AMPARA-RS, importação, crédito presumido, ST, documentos e prova fiscal.",
        "material": "Decreto nº 37.699/1997 (RICMS/RS integral), orientações oficiais da Receita Estadual sobre importação, AMPARA-RS e serviços de opção a crédito presumido.",
        "benefits": "Isenção, redução de base, crédito fiscal presumido, diferimento, suspensão, importação, AMPARA-RS, benefícios setoriais, agro, indústria, informática, energia, transporte, ST e prova documental.",
        "law": ["RS_DEC_37699_1997_RICMS"],
        "ricms": ["RS_DEC_37699_1997_RICMS"],
        "benefits_sources": ["RS_DEC_37699_1997_RICMS", "RS_CREDITO_PRESUMIDO_DEMAIS_CASOS", "RS_CREDITO_PRESUMIDO_IMPORTACAO"],
        "program_sources": ["RS_DEC_37699_1997_RICMS", "RS_CREDITO_PRESUMIDO_DEMAIS_CASOS", "RS_CREDITO_PRESUMIDO_IMPORTACAO", "RS_AMPARA_RS"],
        "st_sources": ["RS_DEC_37699_1997_RICMS"],
        "docs_sources": ["RS_DEC_37699_1997_RICMS", "RS_ICMS_IMPORTACAO_FUNDAMENTOS", "RS_AMPARA_RS"],
        "fund_name": "AMPARA-RS, termos de opção e condições de fruição",
        "program_name": "créditos presumidos, importação, regimes especiais e tratamentos setoriais do RICMS/RS",
    },
    "SC": {
        "name": "Santa Catarina",
        "hero": "Legislação estadual em tela: RICMS/SC, Anexo 2 de benefícios fiscais, Anexo 3 de ST, Anexo 5 de obrigações, Anexo 6 de regimes especiais, NFe e prova fiscal.",
        "material": "Decreto nº 2.870/2001 (RICMS/SC), Anexos 1, 2, 3, 5, 6, 10 e 11 da legislação tributária catarinense.",
        "benefits": "Isenções, reduções de base, crédito presumido, diferimento, suspensão, regimes especiais, TTD, agro, alimentos, indústria, importação, medicamentos, veículos, energia, ST, NFe e documentos fiscais.",
        "law": ["SC_RICMS_2001_REGULAMENTO"],
        "ricms": ["SC_RICMS_2001_REGULAMENTO", "SC_RICMS_ANEXO_1"],
        "benefits_sources": ["SC_RICMS_ANEXO_2_BENEFICIOS", "SC_RICMS_ANEXO_6_REGIMES_ESPECIAIS"],
        "program_sources": ["SC_RICMS_ANEXO_6_REGIMES_ESPECIAIS", "SC_RICMS_ANEXO_2_BENEFICIOS"],
        "st_sources": ["SC_RICMS_ANEXO_3_ST"],
        "docs_sources": ["SC_RICMS_ANEXO_5_OBRIGACOES", "SC_RICMS_ANEXO_10_CODIGOS", "SC_RICMS_ANEXO_11_NFE"],
        "fund_name": "regime especial, TTD e condições de fruição",
        "program_name": "tratamentos tributários diferenciados, regimes especiais e benefícios do Anexo 2",
    },
}


def _profile_signal_map() -> dict[str, str]:
    return {
        "exportacao": "creditos-exportacao-acumulado",
        "nao incidencia": "icms-regra-matriz",
        "aliquota": "base-aliquota-apuracao",
        "reducao de base": "isencoes-reducoes-creditos",
        "isencao": "isencoes-reducoes-creditos",
        "credito outorgado": "isencoes-reducoes-creditos",
        "diferimento": "diferimento-regimes-especiais",
        "suspensao": "icms-regra-matriz",
        "regime especial": "diferimento-regimes-especiais",
        "protege/fundo": "beneficios-matriz-lc160",
        "fundo/contrapartida": "beneficios-matriz-lc160",
        "substituicao tributaria": "st-antecipacao-segmentos",
        "efd/sped": "documentos-efd-prova",
        "cBenef": "documentos-efd-prova",
    }


def _source_refs(source_ids: list[str], keywords: list[str]) -> list[dict]:
    return [{"source": source_id, "keywords": keywords} for source_id in source_ids]


def _standard_state_profile(uf: str, cfg: dict) -> dict:
    return {
        "name": cfg["name"],
        "hero": cfg["hero"],
        "material": cfg["material"],
        "benefits": cfg["benefits"],
        "first_question": (
            f"A operação está no campo do ICMS de {cfg['name']}? Depois disso, separe "
            "regra comum, não incidência, benefício, condição, regime especial, ST, "
            "documento fiscal, escrituração e prova."
        ),
        "tags": (
            f"{uf} {cfg['name']} ICMS RICMS benefícios fiscais isenção redução de base "
            "crédito presumido crédito outorgado diferimento suspensão regime especial "
            "substituição tributária ST EFD SPED cBenef exportação importação LC 160 Convênio 190"
        ),
        "signal_map": _profile_signal_map(),
    }


def _standard_state_chapters(uf: str, cfg: dict) -> list[dict]:
    name = cfg["name"]
    law = cfg["law"]
    ricms = cfg["ricms"]
    benefits = cfg["benefits_sources"]
    programs = cfg["program_sources"]
    st_sources = cfg["st_sources"]
    docs_sources = cfg["docs_sources"]
    return [
        {
            "id": "icms-regra-matriz",
            "title": f"ICMS/{uf}: regra matriz, incidência, não incidência, fato gerador e contribuinte",
            "summary": f"A porta de entrada do ICMS de {name}: quando o imposto nasce, quem responde, quando a operação fica fora do campo tributável e como ler exportação, imunidade, suspensão e diferimento.",
            "theme": "Regra matriz",
            "refs": (
                _source_refs(law, ["incide sobre", "não incide", "fato gerador", "contribuinte", "responsável", "exportação"])
                + _source_refs(ricms, ["incide sobre", "não incide", "fato gerador", "contribuinte", "suspensão", "diferimento"])
            ),
            "analysis": [
                f"O estudo de {name} começa pela regra matriz: operação ou prestação, mercadoria ou serviço, local, momento, contribuinte e responsável. Só depois dessa leitura faz sentido falar em benefício fiscal.",
                "Não incidência, imunidade e isenção não têm a mesma natureza. A não incidência deixa o fato fora do campo do ICMS; a isenção dispensa a cobrança de fato que entraria no campo do imposto; suspensão e diferimento deslocam o momento de exigência e exigem controle do evento posterior.",
                "Exportação deve ser lida com cuidado: a saída ao exterior costuma afastar a incidência, mas a manutenção de créditos, o fim específico de exportação, a documentação e o prazo de comprovação mudam o risco fiscal.",
            ],
            "departments": "Fiscal define CFOP, CST/CSOSN, local da operação e responsável. Jurídico valida imunidade, não incidência, isenção e responsabilidade. Contábil mede débito, crédito e estorno. Comercial e logística provam operação real.",
            "documents": "XML, CT-e, contrato, pedido, comprovante de entrega, despacho de exportação quando houver, cadastro do contribuinte, EFD, memória de enquadramento e fundamento legal aplicado.",
            "risks": "Aplicar benefício antes de confirmar incidência; tratar diferimento como perdão; confundir não incidência com isenção; não provar exportação ou destinatário; deixar o documento fiscal contar história diferente da lei.",
        },
        {
            "id": "base-aliquota-apuracao",
            "title": "Base de cálculo, alíquotas, carga efetiva, DIFAL, fundos e apuração",
            "summary": f"Como {name} transforma operação em imposto: base cheia, reduções, alíquota nominal, carga efetiva, adicionais, consumidor final, importação, crédito e recolhimento.",
            "theme": "Carga tributária",
            "refs": (
                _source_refs(law, ["base de cálculo", "alíquota", "adicional", "diferencial de alíquotas", "imposto devido", "crédito do imposto"])
                + _source_refs(ricms, ["base de cálculo", "alíquota", "carga tributária", "apuração", "DIFAL", "importação", "crédito"])
                + _source_refs(programs, ["adicional", "fundo", "contrapartida", "pagamento", "apuração"])
            ),
            "analysis": [
                "A alíquota nunca deve ser lida isoladamente. Primeiro vem a base de cálculo; depois entram redução, adicional, fundo, crédito admitido, vedação, estorno e forma de recolhimento.",
                "Carga efetiva é resultado, não ponto de partida. Quando a norma fala em carga reduzida, crédito presumido ou regime especial, o cadastro fiscal precisa demonstrar como a carga foi alcançada.",
                "DIFAL, importação, ST e consumidor final exigem memória própria porque mudam base, responsável, guia, prazo e documento. Em auditoria, o cálculo precisa ser reconstruível a partir do XML e da EFD.",
            ],
            "departments": "Fiscal parametriza base, alíquota, fundo, DIFAL e guia. Contábil concilia imposto, crédito e custo. Financeiro guarda recolhimentos. Auditoria compara cadastro, XML, EFD e memória de cálculo.",
            "documents": "XML, NCM, tabela de alíquotas, demonstrativo de base, guia de recolhimento, GNRE quando houver, EFD, planilha de apuração, laudo ou enquadramento setorial.",
            "risks": "Trocar redução de base por alíquota menor; esquecer adicional ou fundo; aplicar alíquota de período errado; calcular DIFAL sem destinatário e finalidade; não separar crédito comum de crédito presumido.",
        },
        {
            "id": "beneficios-matriz-lc160",
            "title": "Benefícios fiscais: matriz legal, LC 160, CONFAZ, condições e contrapartidas",
            "summary": f"O roteiro para ler benefícios de {name}: lei estadual, RICMS, convênio, reinstituição, termo, prazo, condição, vedação, fundo e prova mensal.",
            "theme": "Benefícios fiscais",
            "refs": (
                _source_refs(benefits, ["benefício fiscal", "Convênio ICMS", "LC 160", "isenção", "redução de base", "crédito presumido", "diferimento", "suspensão"])
                + _source_refs(programs, ["benefício", "incentivo", "regime especial", "contrapartida", "termo", cfg["fund_name"]])
            ),
            "analysis": [
                "Benefício fiscal é exceção expressa. Ele pode aparecer como isenção, redução de base, crédito presumido, crédito outorgado, diferimento, suspensão, regime especial, dilação de prazo ou tratamento setorial.",
                "A LC 160/2017 e o Convênio ICMS 190/2017 não substituem a leitura do ato material. Eles organizam convalidação e reinstituição, mas a aplicação concreta continua dependendo do dispositivo estadual, da mercadoria, da operação, do destinatário e da condição.",
                f"Em {name}, a fruição precisa ser tratada como rotina de prova. {cfg['fund_name']} não são detalhes administrativos: normalmente são a diferença entre benefício defensável e glosa.",
            ],
            "departments": "Jurídico mantém matriz de ato, vigência, condição e vedação. Fiscal transforma a regra em CST, CFOP, cBenef quando exigido, ajuste e EFD. Contábil mede crédito, estorno e resultado. Financeiro controla fundos e recolhimentos.",
            "documents": "Lei, decreto, anexo, convênio, termo de opção ou regime, XML, EFD, cBenef quando aplicável, guia, memória de cálculo, comprovação de condição e dossiê por benefício.",
            "risks": "Usar benefício por analogia econômica; ignorar prazo ou convênio; acumular benefícios incompatíveis; deixar de recolher fundo; aplicar crédito presumido sem termo ou sem estorno exigido.",
        },
        {
            "id": "isencoes-reducoes-creditos",
            "title": "Isenções, reduções de base, crédito presumido e grupos de benefícios",
            "summary": "Capítulo por grupos: alimentos, agro, medicamentos e saúde, informática e eletrônicos, veículos, energia, transporte, importação, indústria, comércio, máquinas, equipamentos e regimes especiais.",
            "theme": "Benefícios por grupo",
            "refs": _source_refs(benefits, ["ISENÇÕES", "isenção", "REDUÇÕES", "redução de base", "crédito presumido", "créditos outorgados", "produtos", "máquinas", "veículos", "medicamentos", "informática", "agropecuários"]),
            "analysis": [
                "A leitura por grupo evita o erro comum de procurar somente uma palavra. Alimentos, agro, medicamentos, eletrônicos, informática, veículos, energia, transporte, importação e indústria podem usar técnicas diferentes: isenção, redução, crédito presumido, diferimento ou regime especial.",
                "A descrição legal manda mais que o nome comercial. Produto, NCM, operação, destinatário, finalidade, prazo, convênio de suporte e manutenção ou estorno de crédito precisam aparecer no dossiê.",
                "Crédito presumido e crédito outorgado não são crédito comum. A empresa deve demonstrar base do crédito, percentual, limite, vedação de acúmulo, estorno do crédito de entrada quando exigido e reflexo na apuração.",
            ],
            "departments": "Fiscal parametriza CST, CFOP, cBenef quando houver, benefício e ajuste. Compras e comercial validam NCM, produto e destinatário. Contábil separa crédito comum e presumido. Jurídico revisa condição, prazo e vedação.",
            "documents": "XML, NCM, ficha técnica, laudo quando necessário, contrato, EFD, memória de cálculo, termo ou regime, guia, convênio e fundamento legal no cadastro fiscal.",
            "risks": "Ampliar isenção por analogia; usar redução para produto fora da descrição; manter crédito quando a regra exige estorno; somar crédito presumido com benefício incompatível; esquecer cBenef ou código documental.",
        },
        {
            "id": "creditos-exportacao-acumulado",
            "title": "Exportação, manutenção de créditos, saldo credor e crédito acumulado",
            "summary": "Como ler exportação e créditos: não incidência, fim específico de exportação, manutenção de crédito, saldo credor, transferência, apropriação e prova documental.",
            "theme": "Exportação e créditos",
            "refs": (
                _source_refs(law, ["exterior", "exportação", "crédito", "saldo credor", "manutenção do crédito", "transferência de crédito"])
                + _source_refs(ricms, ["exterior", "exportação", "crédito acumulado", "saldo credor", "apropriação do crédito", "transferência de crédito"])
                + _source_refs(programs, ["crédito", "transferência", "habilitados", "exportação"])
            ),
            "analysis": [
                "Exportação não é apenas uma saída sem débito. O ponto sensível é provar que a operação chegou ao exterior ou saiu com fim específico, e que o crédito mantido decorre de entradas vinculadas a essa cadeia.",
                "Saldo credor e crédito acumulado exigem método. A empresa precisa separar crédito comum, crédito incentivado, estorno, apropriação, autorização de uso ou transferência e eventual limite por regime.",
                "Quando houver programa de transferência de crédito ou tratamento especial, o controle passa a ser jurídico, fiscal e financeiro ao mesmo tempo: ato, habilitação, contrapartida, escrituração e comprovação de uso.",
            ],
            "departments": "Exportação e logística guardam documentos aduaneiros. Fiscal vincula CFOP, CST, EFD e crédito. Contábil reconstrói saldo. Financeiro acompanha transferência, autorização e recebimento. Jurídico valida regime e prazo.",
            "documents": "NF-e, DU-E, contrato de câmbio quando aplicável, comprovante de exportação, EFD, razão do crédito, memória de saldo, autorização de transferência e dossiê de entradas vinculadas.",
            "risks": "Manter crédito sem provar exportação; transferir crédito sem autorização; misturar crédito comum e crédito presumido; esquecer estorno; não reconciliar saldo credor com a EFD.",
        },
        {
            "id": "diferimento-regimes-especiais",
            "title": f"Diferimento, suspensão, regimes especiais e {cfg['program_name']}",
            "summary": f"A leitura dos tratamentos condicionados em {name}: quando o pagamento fica para etapa posterior, quando há termo, quando há requisito operacional e como provar a fruição.",
            "theme": "Regimes especiais",
            "refs": (
                _source_refs(ricms, ["diferimento", "suspensão", "regime especial", "tratamento tributário", "termo de acordo", "credenciamento"])
                + _source_refs(programs, ["diferimento", "suspensão", "regime especial", "crédito presumido", "incentivo", "termo", "opção"])
            ),
            "analysis": [
                "Diferimento e suspensão não encerram o imposto; eles deslocam a exigência ou condicionam a cobrança a evento posterior. O risco aparece quando a empresa não controla o encerramento.",
                f"{cfg['program_name']} devem ser lidos como contrato fiscal com o Estado: ato, prazo, condição, estabelecimento, produto, investimento, regularidade e escrituração compõem a prova.",
                "Regime especial sem rotina de acompanhamento perde força. O benefício precisa aparecer no documento, na EFD, na apuração, no financeiro e no arquivo jurídico.",
            ],
            "departments": "Jurídico acompanha ato e vigência. Fiscal controla diferimento, suspensão, regime e EFD. Operações prova destino e etapa posterior. Contábil mede efeito. Financeiro guarda pagamentos e garantias.",
            "documents": "Termo de acordo, despacho ou regime, XML, EFD, memória de diferimento, prova de destino, guia, relatório de cumprimento de condição e evidência de regularidade fiscal.",
            "risks": "Tratar diferimento como isenção; esquecer evento de encerramento; aplicar regime a produto ou estabelecimento não autorizado; não renovar termo; não provar condição operacional.",
        },
        {
            "id": "st-antecipacao-segmentos",
            "title": "Substituição tributária, antecipação, MVA, segmentos, CEST e responsabilidade",
            "summary": f"Como {name} organiza ST: mercadoria, NCM, CEST, protocolo ou convênio, base presumida, MVA, responsável, antecipação, ressarcimento e prova da retenção.",
            "theme": "Responsabilidade tributária",
            "refs": (
                _source_refs(law, ["substituição tributária", "responsável", "retenção", "antecipação", "mercadorias"])
                + _source_refs(st_sources, ["SUBSTITUIÇÃO TRIBUTÁRIA", "substituição tributária", "MVA", "CEST", "responsável", "ressarcimento", "antecipação"])
            ),
            "analysis": [
                "ST não é benefício fiscal. É técnica de responsabilidade que desloca o recolhimento para outro sujeito. Por isso, a primeira leitura é mercadoria, NCM, CEST, segmento, origem, destino e convênio ou protocolo aplicável.",
                "A base presumida precisa ser documentada: preço, pauta, margem, MVA ajustada, redução de base, alíquota e eventual adicional. O XML deve permitir reconstituir o cálculo.",
                "Ressarcimento, complemento ou restituição exigem comparação entre base presumida e operação real, além de controle por item. Sem EFD e XML consistentes, a tese fica frágil.",
            ],
            "departments": "Fiscal parametriza NCM, CEST, MVA, base e responsável. Compras valida fornecedor e retenção. Comercial avalia preço final. Contábil controla ressarcimento e complemento. Jurídico acompanha convênios e protocolos.",
            "documents": "XML com ICMS-ST, CEST, NCM, planilha de MVA, protocolo ou convênio, EFD, GNRE ou guia, comprovante de retenção, pedido de ressarcimento e memória por item.",
            "risks": "Usar ST para mercadoria fora da lista; aplicar MVA errada; ignorar redução de base; não recolher antecipação; perder ressarcimento por falta de XML e EFD por item.",
        },
        {
            "id": "documentos-efd-prova",
            "title": "Documentos fiscais, EFD, cBenef, códigos, NFe e prova do benefício",
            "summary": "Como a legislação vira prova: NF-e, CT-e, EFD ICMS/IPI, cBenef quando exigido, código de ajuste, livro fiscal, guia, memória de cálculo e dossiê de fruição.",
            "theme": "Prova fiscal",
            "refs": (
                _source_refs(docs_sources, ["EFD", "SPED", "Nota Fiscal Eletrônica", "NF-e", "documento fiscal", "cBenef", "Código de Benefício Fiscal", "registro", "ajuste"])
                + _source_refs(benefits, ["documento fiscal", "EFD", "cBenef", "crédito presumido", "redução de base", "diferimento"])
            ),
            "analysis": [
                "Benefício bom precisa aparecer no documento certo. A lei pode autorizar a fruição, mas o XML, a EFD, o código de ajuste, o cBenef quando exigido e a memória de cálculo precisam contar a mesma história.",
                "A prova deve ser mensal. Não basta guardar o ato legal; é preciso manter dossiê por benefício, por estabelecimento e por período, com cálculo, condição, documento e escrituração.",
                "Quando o Estado exige cBenef ou código específico, o erro deixa de ser só formal. Ele prejudica a leitura da operação pela fiscalização e pode travar autorização, escrituração ou defesa.",
            ],
            "departments": "Fiscal emite e escritura. TI/ERP parametriza códigos. Contábil concilia. Financeiro guarda guias. Jurídico mantém ato e vigência. Auditoria testa aderência entre cadastro, XML e EFD.",
            "documents": "NF-e, NFC-e, CT-e, EFD ICMS/IPI, código de ajuste, cBenef quando aplicável, guia, memória de cálculo, termo de regime, planilha por item e parecer de enquadramento.",
            "risks": "Documento sem código de benefício; EFD sem ajuste; XML com CST incompatível; guia sem vínculo; cadastro fiscal desatualizado; dossiê incapaz de provar condição ou cálculo.",
        },
        {
            "id": "mapa-revisado-beneficios",
            "title": "Mapa revisado dos benefícios por setor, produto e técnica tributária",
            "summary": "Índice de estudo dos benefícios: agro, alimentos, saúde, medicamentos, informática, eletrônicos, máquinas, veículos, energia, transporte, importação, indústria, comércio e regimes especiais.",
            "theme": "Mapa dos benefícios",
            "refs": (
                _source_refs(benefits, ["isenção", "redução de base", "crédito presumido", "diferimento", "suspensão", "veículos", "medicamentos", "energia", "máquinas", "agropecuários", "informática"])
                + _source_refs(programs, ["programa", "incentivo", "regime especial", "crédito", "investimento", "termo", "opção"])
                + _source_refs(docs_sources, ["EFD", "cBenef", "documento fiscal", "Código de Benefício Fiscal"])
            ),
            "analysis": [
                "Este mapa é a mesa de trabalho do consultor: primeiro classifique o benefício pela técnica, depois pelo setor e só então pela mercadoria ou operação.",
                "Os grupos de leitura são alimentos e cesta básica, agro e insumos, saúde e medicamentos, informática e eletrônicos, máquinas e equipamentos, veículos, energia, transporte, importação, indústria, atacado e comércio.",
                "Cada grupo deve terminar com a mesma pergunta: qual é o dispositivo, qual é a condição, qual é o prazo, há vedação de acúmulo, há fundo ou termo, como isso sai no documento e como aparece na EFD?",
            ],
            "departments": "Consultoria monta matriz. Fiscal aplica. Comercial e compras validam produto e destinatário. Contábil testa efeito econômico. Jurídico valida base legal. Auditoria revisa prova por período.",
            "documents": "Matriz de benefícios, dispositivo legal, NCM, setor, destinatário, XML, EFD, guia, cBenef quando exigido, termo, prova de condição e revisão de vigência.",
            "risks": "Transformar benefício setorial em regra geral; usar notícia como norma; ignorar prazo; aplicar por NCM parecida; não controlar vedação de acúmulo; não guardar prova documental.",
        },
        {
            "id": "fiscalizacao-riscos",
            "title": "Fiscalização, autuação, glosa, penalidades e defesa do enquadramento",
            "summary": "Como defender o ICMS aplicado: reconstrução da operação, prova de benefício, glosa de crédito, penalidade, consulta, retificação e correção de cadastro.",
            "theme": "Fiscalização e risco",
            "refs": (
                _source_refs(law, ["penalidade", "infração", "fiscalização", "auto de infração", "crédito tributário", "multa"])
                + _source_refs(ricms, ["fiscalização", "penalidade", "glosa", "auto de infração", "crédito tributário", "documentos fiscais"])
                + _source_refs(docs_sources, ["documento fiscal", "EFD", "NF-e", "cBenef", "registro"])
            ),
            "analysis": [
                "A fiscalização normalmente ataca a distância entre benefício informado e prova disponível. O direito pode estar no anexo, mas cai se cadastro, XML, EFD, guia e condição não conversam.",
                "Glosa de crédito e perda de benefício costumam nascer de falhas simples: produto fora da descrição, destinatário errado, vigência encerrada, regime vencido, código documental incorreto ou ausência de prova.",
                "Defesa boa começa antes da autuação. O portal deve ensinar a manter dossiê mensal, parecer de enquadramento, conciliação contábil e rotina de revisão de alteração normativa.",
            ],
            "departments": "Jurídico conduz consulta, defesa e matriz de risco. Fiscal reconstrói XML e EFD. Contábil mede crédito, estorno e provisão. Financeiro guarda guias. Auditoria corrige cadastro e causa raiz.",
            "documents": "Auto de infração, intimação, consulta tributária, XML, EFD, guia, parecer de enquadramento, regime especial, memória de cálculo, relatório de correção e provas operacionais.",
            "risks": "Defender benefício sem dossiê; corrigir guia sem retificar EFD; pagar autuação sem ajustar cadastro; ignorar alteração normativa; não provar condição, vigência ou operação real.",
        },
    ]


for _uf, _cfg in STANDARD_STATE_SOURCE_SETS.items():
    CONFIGURED_STATE_PROFILES[_uf] = _standard_state_profile(_uf, _cfg)
    CONFIGURED_STATE_CHAPTERS[_uf] = _standard_state_chapters(_uf, _cfg)


def slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_text = ascii_text.lower()
    ascii_text = re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")
    return ascii_text or "item"


def normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return normalized.encode("ascii", "ignore").decode("ascii").lower()


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


def read_text(path: Path) -> str:
    for encoding in ("utf-8", "windows-1252", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")


@lru_cache(maxsize=1)
def curation_statuses() -> dict:
    if not CURATION_FILE.exists():
        return {}
    data = json.loads(CURATION_FILE.read_text(encoding="utf-8"))
    return data.get("statuses", {})


def state_curation(uf: str) -> dict:
    return curation_statuses().get(uf, {})


@lru_cache(maxsize=None)
def state_source_manifest_path(uf: str) -> Path | None:
    uf = uf.upper()
    if not SOURCE_PACK_ROOT.exists():
        return None
    matches = sorted(SOURCE_PACK_ROOT.glob(f"*/{uf}/manifest.json"))
    return matches[0] if matches else None


@lru_cache(maxsize=None)
def state_source_manifest(uf: str) -> dict:
    path = state_source_manifest_path(uf)
    if not path or not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def state_is_deep_published(uf: str) -> bool:
    if uf == "GO":
        return True
    return bool(state_curation(uf).get("publish_deep"))


def clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[\x01-\x08\x0b\x0c\x0e-\x1f]", " ", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{5,}", "\n\n\n", text)
    return text.strip()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def category_from_file(uf: str, path: Path) -> str:
    name = path.stem
    if name.upper().startswith(f"{uf}_"):
        name = name[len(uf) + 1 :]
    name = re.sub(r"_(parte|pt)\d+$", "", name, flags=re.I)
    return name.upper()


def curated_category(source: dict) -> str:
    source_id = source.get("id", "")
    if source_id in CURATED_CATEGORY_BY_SOURCE_ID:
        return CURATED_CATEGORY_BY_SOURCE_ID[source_id]
    theme = normalize(source.get("tema", ""))
    if "substituicao" in theme:
        return "ICMS_ST"
    if "beneficio" in theme or "credito" in theme:
        return "ICMS_BENEFICIOS"
    if "regulamento" in theme:
        return "RICMS"
    if "lei material" in theme:
        return "ICMS_LEIS"
    return "OUTROS"


@lru_cache(maxsize=None)
def collect_curated_state_documents(uf: str) -> tuple[dict, ...]:
    manifest = state_source_manifest(uf)
    manifest_path = state_source_manifest_path(uf)
    if not manifest or not manifest_path or not manifest.get("fontes"):
        return tuple()
    docs: list[dict] = []
    for source in manifest.get("fontes", []):
        source_file = source.get("arquivo", "")
        path = manifest_path.parent / source_file
        if not path.exists():
            continue
        text = clean_text(read_text(path))
        category = curated_category(source)
        source_id = source.get("id") or path.stem
        docs.append({
            "id": slug(source_id),
            "source_id": source_id,
            "uf": uf,
            "origin": "curated",
            "path": path,
            "file": source_file,
            "category": category,
            "category_label": source.get("tema") or CATEGORY_LABELS.get(category, category.replace("_", " ").title()),
            "title": source.get("titulo") or title_from_file(uf, path, category),
            "text": text,
            "chars": len(text),
            "sha256": source.get("sha256") or sha256_file(path),
            "source_documents": [source.get("url", "")] if source.get("url") else [],
            "official_url": source.get("url", STATE_OFFICIAL_PORTALS.get(uf, "")),
            "dominant_scope": "ICMS",
            "scores": {"ICMS": normalize(text).count("icms")},
            "source_scopes": ["ICMS"],
            "scope_flags": [],
            "scope_blocked": False,
            "named_icms": True,
            "fallback_icms": False,
        })
    return tuple(docs)


def source_documents(text: str) -> list[str]:
    docs: list[str] = []
    in_sources = False
    for line in text.splitlines()[:90]:
        stripped = line.strip()
        low = normalize(stripped)
        if low.startswith("documentos fonte"):
            in_sources = True
            continue
        if in_sources and stripped.startswith(("•", "-", "*")):
            docs.append(stripped.lstrip("•-* ").strip())
        elif in_sources and low.startswith(("observacao", "observação")):
            break
    return docs[:24]


def source_scope_labels(sources: list[str]) -> list[str]:
    labels: set[str] = set()
    for source in sources:
        low = normalize(source).replace("\\", "/")
        for label, terms in SOURCE_SCOPE_TERMS.items():
            if any(term in low for term in terms):
                labels.add(label)
    return sorted(labels)


def content_scope_scores(text: str) -> dict[str, int]:
    low = normalize(text)
    scores = {
        "ICMS": low.count("icms") + low.count("regulamento do icms") * 8 + low.count("conv icms") * 3,
    }
    for label, terms in NON_ICMS_SCOPE_TERMS.items():
        scores[label] = sum(low.count(term) for term in terms)
    return scores


def material_scope_profile(category: str, text: str, sources: list[str]) -> dict:
    scores = content_scope_scores(text)
    source_scopes = source_scope_labels(sources)
    dominant_scope = max(scores, key=lambda key: scores[key]) if scores else "indefinido"
    non_icms_sources = [scope for scope in source_scopes if scope != "ICMS"]
    non_icms_scores = {key: value for key, value in scores.items() if key != "ICMS"}
    strongest_non_icms = max(non_icms_scores, key=lambda key: non_icms_scores[key]) if non_icms_scores else ""
    strongest_non_icms_score = non_icms_scores.get(strongest_non_icms, 0)
    flags: list[str] = []

    if category in ICMS_NAMED_CATEGORIES:
        if non_icms_sources and "ICMS" not in source_scopes:
            flags.append(
                "escopo incompatível: arquivo classificado como ICMS, mas os documentos fonte indicam "
                + ", ".join(non_icms_sources)
            )
        if strongest_non_icms_score >= 10 and scores.get("ICMS", 0) < max(5, strongest_non_icms_score // 3):
            flags.append(
                f"escopo dominante incompatível: conteúdo parece tratar de {strongest_non_icms}, não de ICMS"
            )
    elif category in ICMS_FALLBACK_CATEGORIES and strongest_non_icms_score > max(20, scores.get("ICMS", 0) * 2):
        flags.append(
            f"fallback amplo contaminado: categoria {category} contém ICMS, mas o escopo dominante é {strongest_non_icms}"
        )

    return {
        "dominant_scope": dominant_scope,
        "scores": scores,
        "source_scopes": source_scopes,
        "scope_flags": sorted(set(flags)),
        "scope_blocked": bool(flags),
    }


def state_folders(uf: str) -> list[tuple[str, Path]]:
    return [
        ("principal", STATE_MAIN / uf),
        ("complementar", STATE_COMPLEMENT / uf),
    ]


@lru_cache(maxsize=None)
def collect_state_documents(uf: str) -> tuple[dict, ...]:
    curated_docs = collect_curated_state_documents(uf)
    if curated_docs:
        return curated_docs
    candidates: list[dict] = []
    for origin, folder in state_folders(uf):
        if not folder.exists():
            continue
        for path in sorted(folder.glob("*.txt")):
            if path.name.startswith("00_"):
                continue
            text = clean_text(read_text(path))
            category = category_from_file(uf, path)
            normalized = normalize(text)
            is_named_icms = category in ICMS_NAMED_CATEGORIES
            is_fallback_icms = "icms" in normalized and category in ICMS_FALLBACK_CATEGORIES
            if not (is_named_icms or is_fallback_icms):
                continue
            sources = source_documents(text)
            scope_profile = material_scope_profile(category, text, sources)
            doc_id = slug(f"{origin}-{path.stem}")
            candidates.append({
                "id": doc_id,
                "uf": uf,
                "origin": origin,
                "path": path,
                "file": path.name,
                "category": category,
                "category_label": CATEGORY_LABELS.get(category, category.replace("_", " ").title()),
                "title": title_from_file(uf, path, category),
                "text": text,
                "chars": len(text),
                "sha256": sha256_file(path),
                "source_documents": sources,
                **scope_profile,
                "named_icms": is_named_icms,
                "fallback_icms": is_fallback_icms,
            })
    has_named_icms = any(doc["named_icms"] for doc in candidates)
    docs = [
        doc for doc in candidates
        if doc["named_icms"] or (doc["fallback_icms"] and not has_named_icms)
    ]
    return tuple(docs)


def publishable_state_documents(uf: str) -> tuple[dict, ...]:
    return tuple(doc for doc in collect_state_documents(uf) if not doc.get("scope_blocked"))


def title_from_file(uf: str, path: Path, category: str) -> str:
    label = CATEGORY_LABELS.get(category, category.replace("_", " ").title())
    part = ""
    match = re.search(r"_(parte|pt)(\d+)$", path.stem, flags=re.I)
    if match:
        part = f" - parte {match.group(2)}"
    return f"{STATE_NAMES.get(uf, uf)}: {label}{part}"


def group_by_id(group_id: str) -> dict:
    return next(group for group in GROUP_DEFS if group["id"] == group_id)


def doc_matches_group(doc: dict, group: dict) -> bool:
    if doc["category"] in group["categories"]:
        return True
    normalized = normalize(doc["text"])
    return any(normalize(needle) in normalized for needle in group["needles"])


def group_docs(docs: list[dict], group: dict) -> list[dict]:
    matched = [doc for doc in docs if doc_matches_group(doc, group)]
    if group["id"] == "icms" and not matched:
        matched = docs[:]
    if group["id"] == "beneficios" and not matched:
        matched = [doc for doc in docs if doc["category"] in {"RICMS", "ICMS_LEIS", "ICMS_ANEXOS"}]
    return matched


def index_path(uf: str) -> str:
    return f"estados/{uf.lower()}/legislacao/index.html"


def group_path(uf: str, group_id: str) -> str:
    group = group_by_id(group_id)
    return f"estados/{uf.lower()}/legislacao/{group['path']}"


def source_path(uf: str, doc: dict) -> str:
    return f"estados/{uf.lower()}/legislacao/fontes/{doc['id']}.html"


def state_page_path(uf: str) -> str:
    return "estados/goias.html" if uf == "GO" else f"estados/{uf.lower()}.html"


def state_has_legal_pack(uf: str) -> bool:
    if uf == "GO":
        return True
    return state_is_deep_published(uf) and bool(publishable_state_documents(uf))


def render_doc_links(current_path: str, uf: str, docs: list[dict]) -> str:
    if not docs:
        return '<p class="empty-note">Não há texto de ICMS selecionado para este tema nesta remessa.</p>'
    links = []
    for doc in docs:
        links.append(f"""
<a class="source-card searchable-card" href="{escape(rel_href(current_path, source_path(uf, doc)))}"
   data-search="{escape(doc['title'] + ' ' + doc['file'] + ' ' + doc['category_label'])}">
  <span>{escape(doc['category_label'])}</span>
  <strong>{escape(doc['title'])}</strong>
  <small>{fmt_num(doc['chars'])} caracteres em tela; {escape(doc['file'])}</small>
</a>
""")
    return f'<div class="source-grid">{"".join(links)}</div>'


def render_sources_list(docs: list[dict]) -> str:
    items = []
    for doc in docs[:8]:
        for item in doc.get("source_documents", [])[:4]:
            items.append(f"<li>{escape(item)}</li>")
    if not items:
        return "<p>Os documentos fonte estão preservados no cabeçalho do texto publicado.</p>"
    return f"<ul>{''.join(items[:18])}</ul>"


SOURCE_HEADER_PREFIXES = (
    "TITULO:",
    "TÍTULO:",
    "TEMA:",
    "TIPO:",
    "FONTE PUBLICA:",
    "FONTE PÚBLICA:",
    "DATA DA CAPTURA:",
    "TEXTO EXTRAIDO",
    "TEXTO EXTRAÍDO",
)


def strip_source_header(text: str) -> str:
    lines = []
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        low = normalize(stripped)
        if any(low.startswith(normalize(prefix)) for prefix in SOURCE_HEADER_PREFIXES):
            continue
        lines.append(raw_line)
    return "\n".join(lines).strip()


def excerpt_base_text(text: str) -> str:
    value = strip_source_header(text)
    head = normalize(value[:70000])
    if "indice sistematico" in head:
        match = re.search(r"(?mi)^\s*(?:Artigo|Art\.?)\s*1\s*(?:º|°|o)?\s*(?:[-–.]|\b)", value)
        if match and match.start() > 500:
            value = value[match.start():]
    return value


def paragraph_candidates(text: str) -> list[str]:
    text = excerpt_base_text(text)
    chunks = re.split(r"\n\s*\n|\r\n\s*\r\n", text)
    cleaned = []
    for chunk in chunks:
        value = re.sub(r"\s+", " ", chunk).strip()
        value = re.sub(r"={5,}\s*P[ÁA]GINA\s+\d+\s*={5,}", " ", value, flags=re.I)
        value = re.sub(r"={8,}|-{8,}|\.{6,}", " ", value)
        value = re.sub(r"\s+", " ", value).strip()
        if len(value) < 180:
            continue
        low = normalize(value)
        if any(term in low for term in (
            "comando para ignorar faixa de opcoes",
            "ativar o modo mais acessivel",
            "desativar o modo mais acessivel",
            "ir para o conteudo principal",
            "pesquisa de satisfacao",
        )):
            continue
        if (low.count("capitulo") + low.count("secao") + low.count("subsecao") > 10) and not re.search(r"\bart(?:igo|\.)\b", low):
            continue
        cleaned.append(value)
    if not cleaned:
        lines = []
        for raw_line in text.splitlines():
            line = raw_line.strip()
            low = normalize(line)
            if not line or line.startswith("=====") or any(low.startswith(normalize(prefix)) for prefix in SOURCE_HEADER_PREFIXES):
                continue
            lines.append(line)
        for index in range(0, len(lines), 24):
            value = re.sub(r"\s+", " ", " ".join(lines[index:index + 24])).strip()
            if len(value) >= 180:
                cleaned.append(value)
            if len(cleaned) >= 80:
                break
    return cleaned


def excerpts(text: str, needles: list[str], limit: int = 3) -> list[str]:
    normalized_needles = [normalize(needle) for needle in needles]
    found = []
    for chunk in paragraph_candidates(text):
        low = normalize(chunk)
        if any(needle in low for needle in normalized_needles):
            found.append(chunk[:1200].rsplit(" ", 1)[0] + ("..." if len(chunk) > 1200 else ""))
        if len(found) >= limit:
            break
    if not found:
        for chunk in paragraph_candidates(text)[:1]:
            found.append(chunk[:900].rsplit(" ", 1)[0] + ("..." if len(chunk) > 900 else ""))
    return found


def sector_anchor(sector: dict) -> str:
    return f"beneficio-{sector['id']}"


def benefit_sector_results(docs: list[dict]) -> list[dict]:
    normalized_docs = [(doc, normalize(doc["text"])) for doc in docs]
    results: list[dict] = []
    for sector in BENEFIT_SECTOR_DEFS:
        normalized_keywords = [normalize(keyword) for keyword in sector["keywords"]]
        hits: list[dict] = []
        total = 0
        for doc, low in normalized_docs:
            matched_terms = []
            score = 0
            for raw_keyword, keyword in zip(sector["keywords"], normalized_keywords):
                count = low.count(keyword)
                if count:
                    matched_terms.append(raw_keyword)
                    score += count
            if score:
                total += score
                hits.append({
                    "doc": doc,
                    "score": score,
                    "terms": matched_terms[:8],
                })
        if hits:
            hits.sort(key=lambda item: (-item["score"], item["doc"]["title"]))
            results.append({
                "sector": sector,
                "hits": hits,
                "score": total,
            })
    results.sort(key=lambda item: (-item["score"], item["sector"]["title"]))
    return results


def render_benefit_sector_index(current_path: str, uf: str, results: list[dict]) -> str:
    if not results:
        return ""
    name = STATE_NAMES.get(uf, uf)
    cards = []
    for result in results:
        sector = result["sector"]
        terms = ", ".join(sorted({term for hit in result["hits"][:4] for term in hit["terms"]})[:6])
        cards.append(f"""
<a class="benefit-sector-card searchable-card" href="#{escape(sector_anchor(sector))}"
   data-search="{escape(name + ' ' + sector['title'] + ' ' + sector['summary'] + ' ' + ' '.join(sector['keywords']))}">
  <span>{escape(fmt_num(len(result['hits'])))} fontes</span>
  <strong>{escape(sector['title'])}</strong>
  <small>{escape(terms or 'benefício fiscal setorial')}</small>
</a>
""")
    return f"""
<section class="section-wrap benefit-sector-map">
  <div class="section-heading">
    <span class="eyebrow">Benefícios por setor</span>
    <h2>Entre pelo assunto econômico</h2>
    <p>O índice abaixo leva a seções reais desta página. Ele ajuda a estudar a lei por cadeia econômica: mercadoria, operação, destinatário, documento e risco.</p>
  </div>
  <div class="benefit-sector-grid">{''.join(cards)}</div>
</section>
"""


def render_benefit_sector_sections(current_path: str, uf: str, results: list[dict]) -> str:
    if not results:
        return ""
    articles = []
    for result in results:
        sector = result["sector"]
        quotes = []
        for hit in result["hits"][:4]:
            doc = hit["doc"]
            quote_text = excerpts(doc["text"], sector["keywords"], limit=1)
            if not quote_text:
                continue
            terms = ", ".join(hit["terms"][:5])
            quotes.append(f"""
<blockquote class="law-quote">
  <p>{escape(quote_text[0])}</p>
  <cite>{escape(doc['file'])}{' · sinais: ' + escape(terms) if terms else ''}</cite>
</blockquote>
<div class="chapter-application">
  <strong>Texto integral</strong>
  <span><a href="{escape(rel_href(current_path, source_path(uf, doc)))}">abrir fonte em tela</a></span>
</div>
""")
        if not quotes:
            continue
        related = [
            ("Alíquotas e base", group_path(uf, "aliquotas")),
            ("ST", group_path(uf, "st")),
            ("Documentos e prova", group_path(uf, "prova")),
        ]
        related_links = "".join(f'<a href="{escape(rel_href(current_path, target))}">{escape(label)}</a>' for label, target in related)
        articles.append(f"""
<article class="benefit-sector" id="{escape(sector_anchor(sector))}">
  <div class="benefit-sector-heading">
    <span>{escape(fmt_num(result['score']))} ocorrências no texto legal</span>
    <h3>{escape(sector['title'])}</h3>
    <p>{escape(sector['summary'])}</p>
  </div>
  <dl class="benefit-sector-rules">
    <dt>Como ler</dt>
    <dd>{escape(sector['read'])}</dd>
    <dt>Aplicação</dt>
    <dd>{escape(sector['departments'])}</dd>
    <dt>Prova</dt>
    <dd>{escape(sector['documents'])}</dd>
    <dt>Risco</dt>
    <dd>{escape(sector['risk'])}</dd>
  </dl>
  <div class="law-quotes">{''.join(quotes)}</div>
  <div class="signal-law-links">
    <strong>Continuar este estudo</strong>
    <div>{related_links}</div>
  </div>
</article>
""")
    if not articles:
        return ""
    return f"""
<section class="benefit-sector-list">
  <div class="section-heading">
    <span class="eyebrow">Estudo setorial</span>
    <h2>Benefício fiscal precisa de contexto</h2>
    <p>Cada bloco mostra a porta de entrada do tema, os cuidados de interpretação e trechos legais que levaram à classificação. A íntegra continua disponível em tela.</p>
  </div>
  {''.join(articles)}
</section>
"""


def render_excerpts(current_path: str, uf: str, docs: list[dict], group: dict) -> str:
    blocks = []
    for doc in docs[:8]:
        doc_excerpts = excerpts(doc["text"], group["needles"], limit=2)
        quotes = "".join(
            f'<blockquote class="law-quote"><p>{escape(item)}</p><cite>{escape(doc["file"])}</cite></blockquote>'
            for item in doc_excerpts
        )
        blocks.append(f"""
<article class="law-chapter searchable-card">
  <h3>{escape(doc['title'])}</h3>
  <p>Trecho de leitura para orientar o tema. O texto integral está no botão logo abaixo.</p>
  <div class="law-quotes">{quotes}</div>
  <div class="chapter-application">
    <strong>Texto integral</strong>
    <span><a href="{escape(rel_href(current_path, source_path(uf, doc)))}">abrir legislação completa em tela</a></span>
  </div>
</article>
""")
    if not blocks:
        return ""
    return f"""
<section class="legal-chapters">
  <div class="section-heading">
    <span class="eyebrow">Legislação em tela</span>
    <h2>Primeiros dispositivos para leitura</h2>
    <p>Estes trechos abrem o estudo. A íntegra de cada ato está nas páginas-fonte, sem depender do site externo para leitura.</p>
  </div>
  <div class="law-chapter-list">{''.join(blocks)}</div>
</section>
"""


def render_chunks(text: str, doc_id: str, chunk_size: int = 30000) -> str:
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
<article class="article-block text-chunk" id="{escape(doc_id)}-parte-{index}">
  <div class="article-number">Parte {index}</div>
  <pre class="law-pre">{escape(chunk)}</pre>
</article>
""")
            index += 1
        start = end
    return "".join(chunks)


STATE_ARTICLE_RE = re.compile(r"(?mi)^\s*(?:Art\.?|Artigo)\s*(\d+(?:-[A-Za-z])?)\s*(?:º|°|o)?\s*(?:[-–.]|\b)")


def clean_law_segment(text: str, limit: int | None = 12000) -> str:
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            lines.append("")
            continue
        if stripped.startswith("====="):
            continue
        if stripped == "TEXTO EXTRAIDO":
            continue
        if stripped.startswith("TEXTO EXTRAIDO "):
            line = stripped.replace("TEXTO EXTRAIDO ", "", 1)
            stripped = line.strip()
        low = normalize(stripped)
        if any(low.startswith(normalize(prefix)) for prefix in SOURCE_HEADER_PREFIXES):
            continue
        if stripped.lower().endswith(".doc") and len(stripped) < 80:
            continue
        lines.append(line.rstrip())
    cleaned = "\n".join(lines).strip()
    cleaned = re.sub(r"\n{4,}", "\n\n\n", cleaned)
    if limit is not None and len(cleaned) > limit:
        cleaned = cleaned[:limit].rsplit("\n", 1)[0].strip() + "\n\n[continua na fonte integral em tela]"
    return cleaned


def split_complete_segment(label: str, segment: str, chunk_size: int = 900_000) -> list[tuple[str, str]]:
    if len(segment) <= chunk_size:
        return [(label, segment)]
    chunks: list[tuple[str, str]] = []
    start = 0
    index = 1
    while start < len(segment):
        end = min(start + chunk_size, len(segment))
        if end < len(segment):
            window = segment[start:end]
            numbered_items = [start + match.start() for match in re.finditer(r"\n\d{1,3}\s+", window)]
            natural = max(
                segment.rfind("\nITEM ", start, end),
                segment.rfind("\nArt. ", start, end),
                segment.rfind("\n\n", start, end),
                segment.rfind("\n", start, end),
                max(numbered_items) if numbered_items else -1,
            )
            if natural > start + 20_000:
                end = natural
        chunk = segment[start:end].strip()
        if chunk:
            chunks.append((f"{label} - parte {index}", chunk))
            index += 1
        start = end
    return chunks


def expand_complete_segments(segments: list[tuple[str, str]], chunk_size: int = 900_000) -> list[tuple[str, str]]:
    expanded: list[tuple[str, str]] = []
    for label, segment in segments:
        expanded.extend(split_complete_segment(label, segment, chunk_size=chunk_size))
    return expanded


def nearby_law_heading(text: str, start: int) -> str:
    window = text[max(0, start - 3500):start]
    headings: list[str] = []
    for raw_line in reversed(window.splitlines()):
        line = re.sub(r"\s+", " ", raw_line).strip()
        if not line:
            continue
        low = normalize(line)
        if low.startswith(("anexo ", "titulo ", "capitulo ", "secao ", "subsecao ")):
            headings.append(line)
        if len(headings) >= 2:
            break
    return " · ".join(reversed(headings))


def keyword_article_segments(
    doc: dict,
    keywords: list[str],
    max_segments: int = 8,
    per_segment_limit: int | None = None,
) -> list[tuple[str, str]]:
    matches = list(STATE_ARTICLE_RE.finditer(doc["text"]))
    normalized_needles = [normalize(keyword) for keyword in keywords]
    segments: list[tuple[str, str]] = []
    seen: set[str] = set()
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(doc["text"])
        block = doc["text"][match.start():end]
        low = normalize(block)
        if not any(needle in low for needle in normalized_needles):
            continue
        cleaned = clean_law_segment(block, limit=per_segment_limit)
        if len(cleaned) < 80:
            continue
        fingerprint = normalize(cleaned[:900])
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        context = nearby_law_heading(doc["text"], match.start())
        label = f"{context} · Art. {match.group(1)}" if context else f"Art. {match.group(1)}"
        segments.append((label, cleaned))
        if len(segments) >= max_segments:
            break
    return segments


def top_level_heading_positions(text: str) -> list[tuple[int, str, str]]:
    positions: list[tuple[int, str, str]] = []
    offset = 0
    for raw_line in text.splitlines(keepends=True):
        line = raw_line.strip()
        low = normalize(line)
        is_anexo_heading = bool(re.fullmatch(r"anexo\s+(?:[ivxlcdm]+|unico)", low)) and not low.startswith("subanexo ")
        is_other_heading = low.startswith(("titulo ", "capitulo "))
        if is_anexo_heading or is_other_heading:
            positions.append((offset, line, low))
        offset += len(raw_line)
    return positions


def heading_segments(doc: dict, specs: list[tuple[str, str, str]]) -> list[tuple[str, str]]:
    text = doc["text"]
    positions = top_level_heading_positions(text)
    segments: list[tuple[str, str]] = []
    for label, heading_low, confirmation_low in specs:
        scoped_positions = [item for item in positions if item[2].startswith("anexo ")] if heading_low.startswith("anexo ") else positions
        for index, (start, _line, low) in enumerate(scoped_positions):
            if low != heading_low:
                continue
            preview = normalize(text[start:start + 900])
            if confirmation_low and confirmation_low not in preview:
                continue
            end = scoped_positions[index + 1][0] if index + 1 < len(scoped_positions) else len(text)
            block = clean_law_segment(text[start:end], limit=None)
            if block:
                segments.append((label, block))
            break
    return segments


PR_RICMS_HEADING_SEGMENTS: dict[str, list[tuple[str, str, str]]] = {
    "isencoes-reducoes-creditos": [
        ("Anexo V - Isenções", "anexo v", "das isencoes"),
        ("Anexo VI - Redução na base de cálculo", "anexo vi", "reducao na base de calculo"),
        ("Anexo VII - Crédito presumido", "anexo vii", "credito presumido"),
    ],
    "diferimento-regimes-especiais": [
        ("Anexo VIII - Suspensão e diferimento", "anexo viii", "suspensao e do diferimento"),
    ],
    "st-antecipacao-segmentos": [
        ("Anexo IX - Substituição tributária", "anexo ix", "substituicao tributaria"),
    ],
    "mapa-revisado-beneficios": [
        ("Anexo V - Isenções", "anexo v", "das isencoes"),
        ("Anexo VI - Redução na base de cálculo", "anexo vi", "reducao na base de calculo"),
        ("Anexo VII - Crédito presumido", "anexo vii", "credito presumido"),
        ("Anexo VIII - Suspensão e diferimento", "anexo viii", "suspensao e do diferimento"),
    ],
}


def pr_complete_law_segments(doc: dict, ref: dict, chapter: dict) -> list[tuple[str, str]]:
    source_id = doc.get("source_id", "")
    if doc["chars"] <= 80_000 and source_id != "PR_DEC_7871_2017_RICMS":
        return [("Texto integral do ato", clean_law_segment(doc["text"], limit=None))]
    if source_id == "PR_DEC_7871_2017_RICMS":
        segments = heading_segments(doc, PR_RICMS_HEADING_SEGMENTS.get(chapter["id"], []))
        if segments:
            return expand_complete_segments(segments)
    if ref.get("articles"):
        segments = []
        for label, segment in article_segments(doc, ref["articles"], max_segments_per_article=8, segment_limit=None):
            segments.append((label, segment))
        return expand_complete_segments(segments)
    if ref.get("keywords"):
        segments = keyword_article_segments(doc, ref["keywords"], max_segments=10, per_segment_limit=None)
        if segments:
            return expand_complete_segments(segments)
    fallback_keywords = [chapter["title"], chapter["summary"]]
    segments = keyword_article_segments(doc, fallback_keywords, max_segments=4, per_segment_limit=None)
    return expand_complete_segments(segments)


def article_segments(
    doc: dict,
    numbers: list[str],
    max_segments_per_article: int = 4,
    segment_limit: int | None = 14000,
) -> list[tuple[str, str]]:
    matches = list(STATE_ARTICLE_RE.finditer(doc["text"]))
    wanted = {number.upper() for number in numbers}
    by_number: dict[str, list[str]] = {number.upper(): [] for number in numbers}
    for index, match in enumerate(matches):
        number = match.group(1).upper()
        if number not in wanted:
            continue
        end = matches[index + 1].start() if index + 1 < len(matches) else len(doc["text"])
        block = clean_law_segment(doc["text"][match.start():end], limit=segment_limit)
        if len(block) < 80:
            continue
        if block in by_number[number]:
            continue
        by_number[number].append(block)
    segments: list[tuple[str, str]] = []
    for number in numbers:
        for block in by_number.get(number.upper(), [])[:max_segments_per_article]:
            segments.append((f"Art. {number}", block))
    return segments


def docs_by_source_id(docs: list[dict] | tuple[dict, ...]) -> dict[str, dict]:
    mapping = {}
    for doc in docs:
        mapping[doc.get("source_id", doc["id"])] = doc
        mapping[doc["id"]] = doc
    return mapping


def ba_chapter_path(chapter_id: str) -> str:
    return f"estados/ba/legislacao/{chapter_id}.html"


def ba_chapter_by_id(chapter_id: str) -> dict:
    return next(chapter for chapter in BA_CHAPTERS if chapter["id"] == chapter_id)


def ba_law_blocks(current_path: str, docs: tuple[dict, ...], chapter: dict) -> str:
    source_map = docs_by_source_id(docs)
    blocks = []
    for ref in chapter.get("refs", []):
        doc = source_map.get(ref["source"])
        if not doc:
            continue
        segments: list[tuple[str, str]] = []
        if ref.get("articles"):
            segments = article_segments(doc, ref["articles"])
        elif ref.get("full_text"):
            if doc["chars"] <= 25000:
                segments = [("Texto integral do ato", clean_law_segment(doc["text"], limit=26000))]
            else:
                needles = ["substituição tributária", "mercadorias", "CEST", "MVA", "antecipação", "crédito fiscal"]
                segments = [(f"Trecho {idx}", clean_law_segment(item, limit=5000)) for idx, item in enumerate(excerpts(doc["text"], needles, limit=5), start=1)]
        elif ref.get("keywords"):
            segments = [(f"Trecho {idx}", clean_law_segment(item, limit=5000)) for idx, item in enumerate(excerpts(doc["text"], ref["keywords"], limit=5), start=1)]
        if not segments:
            segments = [(f"Trecho {idx}", clean_law_segment(item, limit=5000)) for idx, item in enumerate(excerpts(doc["text"], [chapter["title"], chapter["summary"]], limit=2), start=1)]
        law_html = "".join(f"""
<article class="article-block">
  <div class="article-number">{escape(label)}</div>
  <pre class="law-pre">{escape(segment)}</pre>
</article>
""" for label, segment in segments if segment)
        blocks.append(f"""
<section class="legal-document">
  <div class="document-heading">
    <div>
      <span class="eyebrow">{escape(doc['category_label'])}</span>
      <h3>{escape(doc['title'])}</h3>
      <p>Dispositivos essenciais para este capítulo. A íntegra está preservada na página-fonte.</p>
    </div>
    <div class="document-actions">
      <a href="{escape(rel_href(current_path, source_path('BA', doc)))}">abrir fonte integral</a>
      <a href="{escape(doc.get('official_url', STATE_OFFICIAL_PORTALS['BA']))}" target="_blank" rel="noopener">fonte pública</a>
    </div>
  </div>
  {law_html}
</section>
""")
    return "".join(blocks)


def render_ba_index_page(docs: tuple[dict, ...], layout_func) -> str:
    current = index_path("BA")
    chapter_cards = []
    for chapter in BA_CHAPTERS:
        chapter_cards.append(f"""
<a class="portal-card searchable-card" href="{escape(rel_href(current, ba_chapter_path(chapter['id'])))}"
   data-search="{escape('Bahia BA ICMS beneficios fiscais ' + chapter['title'] + ' ' + chapter['summary'] + ' ' + chapter['theme'])}">
  <span class="card-kicker">{escape(chapter['theme'])}</span>
  <h3>{escape(chapter['title'])}</h3>
  <p>{escape(chapter['summary'])}</p>
  <small>lei em tela + análise aplicada</small>
</a>
""")
    source_cards = render_doc_links(current, "BA", list(docs))
    body = f"""
<section class="hero-panel legal-hero">
  <div>
    <span class="eyebrow">Bahia completa</span>
    <h1>Bahia: ICMS e benefícios fiscais em tela</h1>
    <p>Lei nº 7.014/1996, RICMS/BA, anexos, substituição tributária, DESENVOLVE, PROIND, PRONAVAL, crédito presumido, informática, eletrônica, LC 160/Convênio 190 e EFD dos incentivos.</p>
  </div>
  <aside class="hero-proof">
    <strong>Como ler</strong>
    <p>Primeiro a regra matriz; depois base e alíquota; só então benefícios, programas, ST e prova digital.</p>
  </aside>
</section>
<section class="law-ledger">
  <div>
    <h2>Textos publicados</h2>
    <p>{fmt_num(len(docs))} atos normativos e {fmt_num(sum(int(doc['chars']) for doc in docs))} caracteres em tela no portal.</p>
  </div>
  <div>
    <h2>Arquitetura baiana</h2>
    <p>Bahia não tem um único anexo de benefícios. A leitura passa por lei material, regulamento, anexos, programas e atos listados na LC 160/Convênio 190.</p>
  </div>
  <div>
    <h2>Fonte pública</h2>
    <p><a href="https://www.sefaz.ba.gov.br/legislacao/textos-legais/" target="_blank" rel="noopener">Textos legais da SEFAZ-BA</a></p>
  </div>
</section>
<section class="topic-index">
  <div class="section-heading">
    <span class="eyebrow">Índice por tema</span>
    <h2>Estude pela matéria, não pelo número do ato</h2>
    <p>Cada capítulo abre com dispositivos legais em tela e depois ensina como aplicar, provar e auditar a regra.</p>
  </div>
  <div class="card-grid">{''.join(chapter_cards)}</div>
</section>
<section class="section-wrap">
  <div class="section-heading">
    <span class="eyebrow">Fontes integrais</span>
    <h2>Legislação em tela</h2>
    <p>As páginas abaixo preservam a íntegra textual capturada das fontes públicas, para que o portal não dependa do link externo para ensinar.</p>
  </div>
  {source_cards}
</section>
<section class="continuity">
  <h2>Continuar a leitura</h2>
  <div>
    <a href="{escape(rel_href(current, 'estados/ba.html'))}">página da Bahia</a>
    <a href="{escape(rel_href(current, 'estados/goias/legislacao/index.html'))}">comparar com Goiás</a>
    <a href="{escape(rel_href(current, 'confaz/index.html'))}">CONFAZ e Convênio 190/2017</a>
    <a href="{escape(rel_href(current, 'manual-fiscal.html'))}">manual fiscal</a>
  </div>
</section>
"""
    return layout_func(current, "Bahia: ICMS e benefícios fiscais em tela", "Lei, RICMS, benefícios, ST, programas e prova do ICMS baiano.", body, "estados")


def render_ba_chapter_page(docs: tuple[dict, ...], chapter: dict, layout_func) -> str:
    current = ba_chapter_path(chapter["id"])
    related = []
    for other in BA_CHAPTERS:
        if other["id"] == chapter["id"]:
            continue
        if other["theme"] == chapter["theme"] or len(related) < 4:
            related.append(other)
        if len(related) >= 5:
            break
    related_links = "".join(
        f'<a href="{escape(rel_href(current, ba_chapter_path(item["id"])))}">{escape(item["title"])}</a>'
        for item in related
    )
    analysis_items = "".join(f"<p>{escape(item)}</p>" for item in chapter.get("analysis", []))
    body = f"""
<section class="hero-panel legal-hero">
  <div>
    <span class="eyebrow">Bahia · {escape(chapter['theme'])}</span>
    <h1>{escape(chapter['title'])}</h1>
    <p>{escape(chapter['summary'])}</p>
  </div>
  <aside class="hero-proof">
    <strong>Ordem correta</strong>
    <p>Leia os dispositivos em tela antes da interpretação. Depois confira aplicação, prova e risco.</p>
  </aside>
</section>
<section class="topic-index compact-index">
  <div class="section-heading">
    <span class="eyebrow">Voltar ao índice</span>
    <h2>Bahia por capítulos</h2>
  </div>
  <div class="signal-law-links">
    <strong>Continuar no Estado</strong>
    <div>
      <a href="{escape(rel_href(current, index_path('BA')))}">índice da Bahia</a>
      <a href="{escape(rel_href(current, 'estados/ba.html'))}">página principal</a>
      <a href="{escape(rel_href(current, 'confaz/index.html'))}">CONFAZ</a>
    </div>
  </div>
</section>
<section class="legal-chapters">
  <div class="section-heading">
    <span class="eyebrow">Legislação em tela</span>
    <h2>Texto legal antes da análise</h2>
    <p>Os blocos abaixo trazem os dispositivos nucleares deste assunto. A íntegra de cada ato fica aberta nas páginas-fonte do portal.</p>
  </div>
  {ba_law_blocks(current, docs, chapter)}
</section>
<section class="content-block">
  <span class="eyebrow">Análise aplicada</span>
  <h2>Como interpretar</h2>
  {analysis_items}
</section>
<section class="law-ledger">
  <div>
    <h2>Aplicação por departamento</h2>
    <p>{escape(chapter.get('departments', 'Fiscal, contábil, financeiro e jurídico devem amarrar regra, documento, escrituração e pagamento.'))}</p>
  </div>
  <div>
    <h2>Documentos de prova</h2>
    <p>{escape(chapter.get('documents', 'XML, EFD, memória de cálculo, ato legal e comprovantes.'))}</p>
  </div>
  <div>
    <h2>Riscos comuns</h2>
    <p>{escape(chapter.get('risks', 'Aplicar tese sem dispositivo, condição, vigência ou prova documental suficiente.'))}</p>
  </div>
</section>
<section class="continuity">
  <h2>Continuar este estudo</h2>
  <div>{related_links}</div>
</section>
"""
    return layout_func(current, f"Bahia: {chapter['title']}", chapter["summary"], body, "estados")


def render_ba_pages(docs: tuple[dict, ...], layout_func) -> dict[str, str]:
    pages = {index_path("BA"): render_ba_index_page(docs, layout_func)}
    for chapter in BA_CHAPTERS:
        pages[ba_chapter_path(chapter["id"])] = render_ba_chapter_page(docs, chapter, layout_func)
    for doc in docs:
        pages[source_path("BA", doc)] = render_source_page("BA", doc, layout_func)
    return pages


def df_chapter_path(chapter_id: str) -> str:
    return f"estados/df/legislacao/{chapter_id}.html"


def df_chapter_by_id(chapter_id: str) -> dict:
    return next(chapter for chapter in DF_CHAPTERS if chapter["id"] == chapter_id)


def df_law_blocks(current_path: str, docs: tuple[dict, ...], chapter: dict) -> str:
    source_map = docs_by_source_id(docs)
    blocks = []
    for ref in chapter.get("refs", []):
        doc = source_map.get(ref["source"])
        if not doc:
            continue
        segments: list[tuple[str, str]] = []
        if ref.get("articles"):
            segments = article_segments(doc, ref["articles"])
        elif ref.get("full_text"):
            if doc["chars"] <= 25000:
                segments = [("Texto integral do ato", clean_law_segment(doc["text"], limit=26000))]
            else:
                needles = ["substituição tributária", "mercadorias", "CEST", "MVA", "antecipação", "crédito fiscal"]
                segments = [(f"Trecho {idx}", clean_law_segment(item, limit=5000)) for idx, item in enumerate(excerpts(doc["text"], needles, limit=5), start=1)]
        elif ref.get("keywords"):
            segments = [(f"Trecho {idx}", clean_law_segment(item, limit=5000)) for idx, item in enumerate(excerpts(doc["text"], ref["keywords"], limit=5), start=1)]
        if not segments:
            segments = [(f"Trecho {idx}", clean_law_segment(item, limit=5000)) for idx, item in enumerate(excerpts(doc["text"], [chapter["title"], chapter["summary"]], limit=2), start=1)]
        law_html = "".join(f"""
<article class="article-block">
  <div class="article-number">{escape(label)}</div>
  <pre class="law-pre">{escape(segment)}</pre>
</article>
""" for label, segment in segments if segment)
        blocks.append(f"""
<section class="legal-document">
  <div class="document-heading">
    <div>
      <span class="eyebrow">{escape(doc['category_label'])}</span>
      <h3>{escape(doc['title'])}</h3>
      <p>Dispositivos essenciais para este capítulo. A íntegra está preservada na página-fonte.</p>
    </div>
    <div class="document-actions">
      <a href="{escape(rel_href(current_path, source_path('DF', doc)))}">abrir fonte integral</a>
      <a href="{escape(doc.get('official_url', STATE_OFFICIAL_PORTALS['DF']))}" target="_blank" rel="noopener">fonte pública</a>
    </div>
  </div>
  {law_html}
</section>
""")
    return "".join(blocks)


def render_df_index_page(docs: tuple[dict, ...], layout_func) -> str:
    current = index_path("DF")
    chapter_cards = []
    for chapter in DF_CHAPTERS:
        chapter_cards.append(f"""
<a class="portal-card searchable-card" href="{escape(rel_href(current, df_chapter_path(chapter['id'])))}"
   data-search="{escape('Distrito Federal DF ICMS beneficios fiscais ' + chapter['title'] + ' ' + chapter['summary'] + ' ' + chapter['theme'])}">
  <span class="card-kicker">{escape(chapter['theme'])}</span>
  <h3>{escape(chapter['title'])}</h3>
  <p>{escape(chapter['summary'])}</p>
  <small>lei em tela + análise aplicada</small>
</a>
""")
    source_cards = render_doc_links(current, "DF", list(docs))
    body = f"""
<section class="hero-panel legal-hero">
  <div>
    <span class="eyebrow">Distrito Federal completo</span>
    <h1>Distrito Federal: ICMS e benefícios fiscais em tela</h1>
    <p>Lei nº 1.254/1996, RICMS/DF, Cadernos do Anexo I, Anexo IV, LC 160/Convênio 190, regime especial de apuração, crédito outorgado, EMPREGA-DF, PRÓ-DF II, Desenvolve-DF, diferimento agro e EFD ICMS/IPI.</p>
  </div>
  <aside class="hero-proof">
    <strong>Como ler</strong>
    <p>Comece pela regra matriz; depois base, alíquota e apuração; em seguida benefícios, regimes, programas, ST, EFD e prova.</p>
  </aside>
</section>
<section class="law-ledger">
  <div>
    <h2>Textos publicados</h2>
    <p>{fmt_num(len(docs))} atos normativos e {fmt_num(sum(int(doc['chars']) for doc in docs))} caracteres em tela no portal.</p>
  </div>
  <div>
    <h2>Arquitetura do DF</h2>
    <p>O estudo passa pela lei material, pelo RICMS, pelos Cadernos dos Anexos, pela LC 160/Convênio 190 e pelos programas de desenvolvimento econômico.</p>
  </div>
  <div>
    <h2>Fonte pública</h2>
    <p><a href="https://www.sinj.df.gov.br/sinj/" target="_blank" rel="noopener">Sistema Integrado de Normas Jurídicas do DF</a></p>
  </div>
</section>
<section class="topic-index">
  <div class="section-heading">
    <span class="eyebrow">Índice por tema</span>
    <h2>Estude pela matéria, não pelo número do ato</h2>
    <p>Cada capítulo abre com dispositivos legais em tela e depois ensina como aplicar, provar e auditar a regra.</p>
  </div>
  <div class="card-grid">{''.join(chapter_cards)}</div>
</section>
<section class="section-wrap">
  <div class="section-heading">
    <span class="eyebrow">Fontes integrais</span>
    <h2>Legislação em tela</h2>
    <p>As páginas abaixo preservam a íntegra textual capturada das fontes públicas, para que o portal não dependa do link externo para ensinar.</p>
  </div>
  {source_cards}
</section>
<section class="continuity">
  <h2>Continuar a leitura</h2>
  <div>
    <a href="{escape(rel_href(current, 'estados/df.html'))}">página do Distrito Federal</a>
    <a href="{escape(rel_href(current, 'estados/ba/legislacao/index.html'))}">comparar com Bahia</a>
    <a href="{escape(rel_href(current, 'estados/goias/legislacao/index.html'))}">comparar com Goiás</a>
    <a href="{escape(rel_href(current, 'confaz/index.html'))}">CONFAZ e Convênio 190/2017</a>
    <a href="{escape(rel_href(current, 'manual-fiscal.html'))}">manual fiscal</a>
  </div>
</section>
"""
    return layout_func(current, "Distrito Federal: ICMS e benefícios fiscais em tela", "Lei, RICMS, benefícios, ST, programas e prova do ICMS no Distrito Federal.", body, "estados")


def render_df_chapter_page(docs: tuple[dict, ...], chapter: dict, layout_func) -> str:
    current = df_chapter_path(chapter["id"])
    related = []
    for other in DF_CHAPTERS:
        if other["id"] == chapter["id"]:
            continue
        if other["theme"] == chapter["theme"] or len(related) < 4:
            related.append(other)
        if len(related) >= 5:
            break
    related_links = "".join(
        f'<a href="{escape(rel_href(current, df_chapter_path(item["id"])))}">{escape(item["title"])}</a>'
        for item in related
    )
    analysis_items = "".join(f"<p>{escape(item)}</p>" for item in chapter.get("analysis", []))
    body = f"""
<section class="hero-panel legal-hero">
  <div>
    <span class="eyebrow">Distrito Federal · {escape(chapter['theme'])}</span>
    <h1>{escape(chapter['title'])}</h1>
    <p>{escape(chapter['summary'])}</p>
  </div>
  <aside class="hero-proof">
    <strong>Ordem correta</strong>
    <p>Leia os dispositivos em tela antes da interpretação. Depois confira aplicação, prova e risco.</p>
  </aside>
</section>
<section class="topic-index compact-index">
  <div class="section-heading">
    <span class="eyebrow">Voltar ao índice</span>
    <h2>Distrito Federal por capítulos</h2>
  </div>
  <div class="signal-law-links">
    <strong>Continuar no Estado</strong>
    <div>
      <a href="{escape(rel_href(current, index_path('DF')))}">índice do DF</a>
      <a href="{escape(rel_href(current, 'estados/df.html'))}">página principal</a>
      <a href="{escape(rel_href(current, 'confaz/index.html'))}">CONFAZ</a>
    </div>
  </div>
</section>
<section class="legal-chapters">
  <div class="section-heading">
    <span class="eyebrow">Legislação em tela</span>
    <h2>Texto legal antes da análise</h2>
    <p>Os blocos abaixo trazem os dispositivos nucleares deste assunto. A íntegra de cada ato fica aberta nas páginas-fonte do portal.</p>
  </div>
  {df_law_blocks(current, docs, chapter)}
</section>
<section class="content-block">
  <span class="eyebrow">Análise aplicada</span>
  <h2>Como interpretar</h2>
  {analysis_items}
</section>
<section class="law-ledger">
  <div>
    <h2>Aplicação por departamento</h2>
    <p>{escape(chapter.get('departments', 'Fiscal, contábil, financeiro e jurídico devem amarrar regra, documento, escrituração e pagamento.'))}</p>
  </div>
  <div>
    <h2>Documentos de prova</h2>
    <p>{escape(chapter.get('documents', 'XML, EFD, memória de cálculo, ato legal e comprovantes.'))}</p>
  </div>
  <div>
    <h2>Riscos comuns</h2>
    <p>{escape(chapter.get('risks', 'Aplicar tese sem dispositivo, condição, vigência ou prova documental suficiente.'))}</p>
  </div>
</section>
<section class="continuity">
  <h2>Continuar este estudo</h2>
  <div>{related_links}</div>
</section>
"""
    return layout_func(current, f"Distrito Federal: {chapter['title']}", chapter["summary"], body, "estados")


def render_df_pages(docs: tuple[dict, ...], layout_func) -> dict[str, str]:
    pages = {index_path("DF"): render_df_index_page(docs, layout_func)}
    for chapter in DF_CHAPTERS:
        pages[df_chapter_path(chapter["id"])] = render_df_chapter_page(docs, chapter, layout_func)
    for doc in docs:
        pages[source_path("DF", doc)] = render_source_page("DF", doc, layout_func)
    return pages


def mt_chapter_path(chapter_id: str) -> str:
    return f"estados/mt/legislacao/{chapter_id}.html"


def mt_chapter_by_id(chapter_id: str) -> dict:
    return next(chapter for chapter in MT_CHAPTERS if chapter["id"] == chapter_id)


def mt_law_blocks(current_path: str, docs: tuple[dict, ...], chapter: dict) -> str:
    source_map = docs_by_source_id(docs)
    blocks = []
    for ref in chapter.get("refs", []):
        doc = source_map.get(ref["source"])
        if not doc:
            continue
        segments: list[tuple[str, str]] = []
        if ref.get("articles"):
            segments = article_segments(doc, ref["articles"])
        elif ref.get("full_text"):
            if doc["chars"] <= 25000:
                segments = [("Texto integral do ato", clean_law_segment(doc["text"], limit=26000))]
            else:
                needles = ["isenção", "redução de base", "crédito outorgado", "diferimento", "substituição tributária"]
                segments = [(f"Trecho {idx}", clean_law_segment(item, limit=5000)) for idx, item in enumerate(excerpts(doc["text"], needles, limit=5), start=1)]
        elif ref.get("keywords"):
            segments = [(f"Trecho {idx}", clean_law_segment(item, limit=5000)) for idx, item in enumerate(excerpts(doc["text"], ref["keywords"], limit=5), start=1)]
        if not segments:
            segments = [(f"Trecho {idx}", clean_law_segment(item, limit=5000)) for idx, item in enumerate(excerpts(doc["text"], [chapter["title"], chapter["summary"]], limit=2), start=1)]
        law_html = "".join(f"""
<article class="article-block">
  <div class="article-number">{escape(label)}</div>
  <pre class="law-pre">{escape(segment)}</pre>
</article>
""" for label, segment in segments if segment)
        blocks.append(f"""
<section class="legal-document">
  <div class="document-heading">
    <div>
      <span class="eyebrow">{escape(doc['category_label'])}</span>
      <h3>{escape(doc['title'])}</h3>
      <p>Dispositivos essenciais para este capítulo. A íntegra está preservada na página-fonte.</p>
    </div>
    <div class="document-actions">
      <a href="{escape(rel_href(current_path, source_path('MT', doc)))}">abrir fonte integral</a>
      <a href="{escape(doc.get('official_url', STATE_OFFICIAL_PORTALS['MT']))}" target="_blank" rel="noopener">fonte pública</a>
    </div>
  </div>
  {law_html}
</section>
""")
    return "".join(blocks)


def render_mt_index_page(docs: tuple[dict, ...], layout_func) -> str:
    current = index_path("MT")
    chapter_cards = []
    for chapter in MT_CHAPTERS:
        chapter_cards.append(f"""
<a class="portal-card searchable-card" href="{escape(rel_href(current, mt_chapter_path(chapter['id'])))}"
   data-search="{escape('Mato Grosso MT ICMS beneficios fiscais ' + chapter['title'] + ' ' + chapter['summary'] + ' ' + chapter['theme'])}">
  <span class="card-kicker">{escape(chapter['theme'])}</span>
  <h3>{escape(chapter['title'])}</h3>
  <p>{escape(chapter['summary'])}</p>
  <small>lei em tela + análise aplicada</small>
</a>
""")
    source_cards = render_doc_links(current, "MT", list(docs))
    body = f"""
<section class="hero-panel legal-hero">
  <div>
    <span class="eyebrow">Mato Grosso completo</span>
    <h1>Mato Grosso: ICMS e benefícios fiscais em tela</h1>
    <p>Lei nº 7.098/1998, RICMS/MT, LC nº 631/2019, anexos de isenção, redução de base, créditos outorgados, diferimento, substituição tributária, estimativa simplificada, PRODEIC e cBenef.</p>
  </div>
  <aside class="hero-proof">
    <strong>Como ler</strong>
    <p>Comece pela regra matriz; depois base, alíquota e crédito; em seguida benefícios, PRODEIC, agro, ST, cBenef, EFD e fiscalização.</p>
  </aside>
</section>
<section class="law-ledger">
  <div>
    <h2>Textos publicados</h2>
    <p>{fmt_num(len(docs))} atos normativos e {fmt_num(sum(int(doc['chars']) for doc in docs))} caracteres em tela no portal.</p>
  </div>
  <div>
    <h2>Arquitetura do MT</h2>
    <p>A leitura passa pela lei material, pelo RICMS, pela LC 631/2019, pelos anexos de benefícios e pela tabela de códigos de benefício.</p>
  </div>
  <div>
    <h2>Fonte pública</h2>
    <p><a href="https://www.sefaz.mt.gov.br/" target="_blank" rel="noopener">SEFAZ-MT: legislação tributária</a></p>
  </div>
</section>
<section class="topic-index">
  <div class="section-heading">
    <span class="eyebrow">Índice por tema</span>
    <h2>Estude pela matéria, não pelo número do ato</h2>
    <p>Cada capítulo abre com dispositivos legais em tela e depois ensina como aplicar, provar e auditar a regra.</p>
  </div>
  <div class="card-grid">{''.join(chapter_cards)}</div>
</section>
<section class="section-wrap">
  <div class="section-heading">
    <span class="eyebrow">Fontes integrais</span>
    <h2>Legislação em tela</h2>
    <p>As páginas abaixo preservam a íntegra textual capturada das fontes públicas, para que o portal não dependa do link externo para ensinar.</p>
  </div>
  {source_cards}
</section>
<section class="continuity">
  <h2>Continuar a leitura</h2>
  <div>
    <a href="{escape(rel_href(current, 'estados/mt.html'))}">página de Mato Grosso</a>
    <a href="{escape(rel_href(current, 'estados/df/legislacao/index.html'))}">comparar com DF</a>
    <a href="{escape(rel_href(current, 'estados/ba/legislacao/index.html'))}">comparar com Bahia</a>
    <a href="{escape(rel_href(current, 'estados/goias/legislacao/index.html'))}">comparar com Goiás</a>
    <a href="{escape(rel_href(current, 'confaz/index.html'))}">CONFAZ e Convênio 190/2017</a>
  </div>
</section>
"""
    return layout_func(current, "Mato Grosso: ICMS e benefícios fiscais em tela", "Lei, RICMS, benefícios, ST, cBenef e prova do ICMS no Mato Grosso.", body, "estados")


def render_mt_chapter_page(docs: tuple[dict, ...], chapter: dict, layout_func) -> str:
    current = mt_chapter_path(chapter["id"])
    related = []
    for other in MT_CHAPTERS:
        if other["id"] == chapter["id"]:
            continue
        if other["theme"] == chapter["theme"] or len(related) < 4:
            related.append(other)
        if len(related) >= 5:
            break
    related_links = "".join(
        f'<a href="{escape(rel_href(current, mt_chapter_path(item["id"])))}">{escape(item["title"])}</a>'
        for item in related
    )
    analysis_items = "".join(f"<p>{escape(item)}</p>" for item in chapter.get("analysis", []))
    body = f"""
<section class="hero-panel legal-hero">
  <div>
    <span class="eyebrow">Mato Grosso · {escape(chapter['theme'])}</span>
    <h1>{escape(chapter['title'])}</h1>
    <p>{escape(chapter['summary'])}</p>
  </div>
  <aside class="hero-proof">
    <strong>Ordem correta</strong>
    <p>Leia os dispositivos em tela antes da interpretação. Depois confira aplicação, prova e risco.</p>
  </aside>
</section>
<section class="topic-index compact-index">
  <div class="section-heading">
    <span class="eyebrow">Voltar ao índice</span>
    <h2>Mato Grosso por capítulos</h2>
  </div>
  <div class="signal-law-links">
    <strong>Continuar no Estado</strong>
    <div>
      <a href="{escape(rel_href(current, index_path('MT')))}">índice de MT</a>
      <a href="{escape(rel_href(current, 'estados/mt.html'))}">página principal</a>
      <a href="{escape(rel_href(current, 'confaz/index.html'))}">CONFAZ</a>
    </div>
  </div>
</section>
<section class="legal-chapters">
  <div class="section-heading">
    <span class="eyebrow">Legislação em tela</span>
    <h2>Texto legal antes da análise</h2>
    <p>Os blocos abaixo trazem os dispositivos nucleares deste assunto. A íntegra de cada ato fica aberta nas páginas-fonte do portal.</p>
  </div>
  {mt_law_blocks(current, docs, chapter)}
</section>
<section class="content-block">
  <span class="eyebrow">Análise aplicada</span>
  <h2>Como interpretar</h2>
  {analysis_items}
</section>
<section class="law-ledger">
  <div>
    <h2>Aplicação por departamento</h2>
    <p>{escape(chapter.get('departments', 'Fiscal, contábil, financeiro e jurídico devem amarrar regra, documento, escrituração e pagamento.'))}</p>
  </div>
  <div>
    <h2>Documentos de prova</h2>
    <p>{escape(chapter.get('documents', 'XML, EFD, memória de cálculo, ato legal e comprovantes.'))}</p>
  </div>
  <div>
    <h2>Riscos comuns</h2>
    <p>{escape(chapter.get('risks', 'Aplicar tese sem dispositivo, condição, vigência ou prova documental suficiente.'))}</p>
  </div>
</section>
<section class="continuity">
  <h2>Continuar este estudo</h2>
  <div>{related_links}</div>
</section>
"""
    return layout_func(current, f"Mato Grosso: {chapter['title']}", chapter["summary"], body, "estados")


def render_mt_pages(docs: tuple[dict, ...], layout_func) -> dict[str, str]:
    pages = {index_path("MT"): render_mt_index_page(docs, layout_func)}
    for chapter in MT_CHAPTERS:
        pages[mt_chapter_path(chapter["id"])] = render_mt_chapter_page(docs, chapter, layout_func)
    for doc in docs:
        pages[source_path("MT", doc)] = render_source_page("MT", doc, layout_func)
    return pages


def rn_chapter_path(chapter_id: str) -> str:
    return f"estados/rn/legislacao/{chapter_id}.html"


def rn_chapter_by_id(chapter_id: str) -> dict:
    return next(chapter for chapter in RN_CHAPTERS if chapter["id"] == chapter_id)


def rn_law_blocks(current_path: str, docs: tuple[dict, ...], chapter: dict) -> str:
    source_map = docs_by_source_id(docs)
    blocks = []
    for ref in chapter.get("refs", []):
        doc = source_map.get(ref["source"])
        if not doc:
            continue
        segments: list[tuple[str, str]] = []
        if ref.get("articles"):
            segments = article_segments(doc, ref["articles"])
        elif ref.get("full_text"):
            if doc["chars"] <= 28000:
                segments = [("Texto integral do ato", clean_law_segment(doc["text"], limit=30000))]
            else:
                needles = ["isenção", "redução de base", "crédito presumido", "diferimento", "PROEDI", "FUNDERN", "cBenef"]
                segments = [
                    (f"Trecho {idx}", clean_law_segment(item, limit=6200))
                    for idx, item in enumerate(excerpts(doc["text"], needles, limit=6), start=1)
                ]
        elif ref.get("keywords"):
            segments = [
                (f"Trecho {idx}", clean_law_segment(item, limit=6200))
                for idx, item in enumerate(excerpts(doc["text"], ref["keywords"], limit=6), start=1)
            ]
        if not segments:
            segments = [
                (f"Trecho {idx}", clean_law_segment(item, limit=5000))
                for idx, item in enumerate(excerpts(doc["text"], [chapter["title"], chapter["summary"]], limit=2), start=1)
            ]
        law_html = "".join(f"""
<article class="article-block">
  <div class="article-number">{escape(label)}</div>
  <pre class="law-pre">{escape(segment)}</pre>
</article>
""" for label, segment in segments if segment)
        blocks.append(f"""
<section class="legal-document">
  <div class="document-heading">
    <div>
      <span class="eyebrow">{escape(doc['category_label'])}</span>
      <h3>{escape(doc['title'])}</h3>
      <p>Dispositivos essenciais para este capítulo. A íntegra está preservada na página-fonte do portal.</p>
    </div>
    <div class="document-actions">
      <a href="{escape(rel_href(current_path, source_path('RN', doc)))}">abrir fonte integral</a>
      <a href="{escape(doc.get('official_url', STATE_OFFICIAL_PORTALS['RN']))}" target="_blank" rel="noopener">fonte pública</a>
    </div>
  </div>
  {law_html}
</section>
""")
    return "".join(blocks)


def render_rn_index_page(docs: tuple[dict, ...], layout_func) -> str:
    current = index_path("RN")
    chapter_cards = []
    for chapter in RN_CHAPTERS:
        chapter_cards.append(f"""
<a class="portal-card searchable-card" href="{escape(rel_href(current, rn_chapter_path(chapter['id'])))}"
   data-search="{escape('Rio Grande do Norte RN ICMS beneficios fiscais ' + chapter['title'] + ' ' + chapter['summary'] + ' ' + chapter['theme'])}">
  <span class="card-kicker">{escape(chapter['theme'])}</span>
  <h3>{escape(chapter['title'])}</h3>
  <p>{escape(chapter['summary'])}</p>
</a>
""")
    body = f"""
<section class="hero-panel legal-hero">
  <div>
    <span class="eyebrow">RN · ICMS em tela</span>
    <h1>Rio Grande do Norte: ICMS e benefícios fiscais em tela</h1>
    <p>RICMS/RN, anexos de isenção, diferimento, crédito presumido, redução de base, antecipação, ST, documentos fiscais, PROEDI, FUNDERN, Tax Free, cBenef e matriz LC 160 organizados por assunto.</p>
  </div>
  <aside class="hero-proof">
    <strong>Como estudar</strong>
    <p>Leia primeiro a regra maior. Depois vá para benefícios, regimes, documentos e riscos. A análise vem sempre depois do texto legal.</p>
  </aside>
</section>
<section class="law-ledger">
  <div>
    <h2>Material publicado</h2>
    <p>{fmt_num(len(docs))} fontes normativas de ICMS/RN, com {fmt_num(sum(int(doc['chars']) for doc in docs))} caracteres em tela.</p>
  </div>
  <div>
    <h2>Benefícios cobertos</h2>
    <p>Isenção, redução de base, crédito presumido, diferimento, suspensão, PROEDI, Tax Free, FUNDERN, atacado, ST e cBenef.</p>
  </div>
  <div>
    <h2>Ordem de leitura</h2>
    <p>Regra matriz, base/alíquota, benefícios, programas, ST/antecipação, documentos e fiscalização.</p>
  </div>
</section>
<section class="topic-index">
  <div class="section-heading">
    <span class="eyebrow">Índice por tema</span>
    <h2>Capítulos do ICMS potiguar</h2>
    <p>Cada entrada leva a uma seção específica, com lei em tela, explicação, aplicação por departamento, documentos de prova e riscos.</p>
  </div>
  <div class="card-grid">{''.join(chapter_cards)}</div>
</section>
<section class="continuity">
  <h2>Continuar a leitura</h2>
  <div>
    <a href="{escape(rel_href(current, state_page_path('RN')))}">voltar ao Estado</a>
    <a href="{escape(rel_href(current, 'confaz/index.html'))}">CONFAZ e LC 160</a>
    <a href="{escape(rel_href(current, 'federal/pis-cofins.html'))}">conectar com PIS/Cofins</a>
    <a href="{escape(rel_href(current, 'biblioteca/index.html'))}">biblioteca avançada</a>
  </div>
</section>
"""
    return layout_func(current, "Rio Grande do Norte: ICMS e benefícios fiscais em tela", "ICMS/RN, benefícios fiscais, PROEDI, ST, cBenef e prova documental.", body, "estados")


def render_rn_chapter_page(docs: tuple[dict, ...], chapter: dict, layout_func) -> str:
    current = rn_chapter_path(chapter["id"])
    related = []
    for other in RN_CHAPTERS:
        if other["id"] == chapter["id"]:
            continue
        if other["theme"] == chapter["theme"] or len(related) < 4:
            related.append(other)
        if len(related) >= 5:
            break
    related_links = "".join(
        f'<a href="{escape(rel_href(current, rn_chapter_path(item["id"])))}">{escape(item["title"])}</a>'
        for item in related
    )
    analysis_items = "".join(f"<p>{escape(item)}</p>" for item in chapter.get("analysis", []))
    body = f"""
<section class="hero-panel legal-hero">
  <div>
    <span class="eyebrow">Rio Grande do Norte · {escape(chapter['theme'])}</span>
    <h1>{escape(chapter['title'])}</h1>
    <p>{escape(chapter['summary'])}</p>
  </div>
  <aside class="hero-proof">
    <strong>Leitura guiada</strong>
    <p>Primeiro a legislação em tela; depois interpretação, aplicação por departamento, prova e risco.</p>
  </aside>
</section>
<section class="topic-index compact-index">
  <div class="section-heading">
    <span class="eyebrow">Voltar ao índice</span>
    <h2>RN por capítulos</h2>
  </div>
  <div class="signal-law-links">
    <strong>Continuar no Estado</strong>
    <div>
      <a href="{escape(rel_href(current, index_path('RN')))}">índice do RN</a>
      <a href="{escape(rel_href(current, 'estados/rn.html'))}">página principal</a>
      <a href="{escape(rel_href(current, 'confaz/index.html'))}">CONFAZ</a>
    </div>
  </div>
</section>
<section class="legal-chapters">
  <div class="section-heading">
    <span class="eyebrow">Legislação em tela</span>
    <h2>Texto legal antes da análise</h2>
    <p>Os blocos abaixo trazem os dispositivos nucleares deste assunto. A íntegra de cada ato fica aberta nas páginas-fonte do portal.</p>
  </div>
  {rn_law_blocks(current, docs, chapter)}
</section>
<section class="content-block">
  <span class="eyebrow">Análise aplicada</span>
  <h2>Como interpretar</h2>
  {analysis_items}
</section>
<section class="law-ledger">
  <div>
    <h2>Aplicação por departamento</h2>
    <p>{escape(chapter.get('departments', 'Fiscal, contábil, financeiro e jurídico devem amarrar regra, documento, escrituração e pagamento.'))}</p>
  </div>
  <div>
    <h2>Documentos de prova</h2>
    <p>{escape(chapter.get('documents', 'XML, EFD, memória de cálculo, ato legal e comprovantes.'))}</p>
  </div>
  <div>
    <h2>Riscos comuns</h2>
    <p>{escape(chapter.get('risks', 'Aplicar tese sem dispositivo, condição, vigência ou prova documental suficiente.'))}</p>
  </div>
</section>
<section class="continuity">
  <h2>Continuar este estudo</h2>
  <div>{related_links}</div>
</section>
"""
    return layout_func(current, f"Rio Grande do Norte: {chapter['title']}", chapter["summary"], body, "estados")


def render_rn_pages(docs: tuple[dict, ...], layout_func) -> dict[str, str]:
    pages = {index_path("RN"): render_rn_index_page(docs, layout_func)}
    for chapter in RN_CHAPTERS:
        pages[rn_chapter_path(chapter["id"])] = render_rn_chapter_page(docs, chapter, layout_func)
    for doc in docs:
        pages[source_path("RN", doc)] = render_source_page("RN", doc, layout_func)
    return pages


def configured_chapters(uf: str) -> list[dict]:
    return CONFIGURED_STATE_CHAPTERS.get(uf, [])


def configured_profile(uf: str) -> dict:
    return CONFIGURED_STATE_PROFILES.get(uf, {"name": STATE_NAMES.get(uf, uf), "signal_map": {}})


def configured_chapter_path(uf: str, chapter_id: str) -> str:
    return f"estados/{uf.lower()}/legislacao/{chapter_id}.html"


def configured_chapter_by_id(uf: str, chapter_id: str) -> dict:
    return next(chapter for chapter in configured_chapters(uf) if chapter["id"] == chapter_id)


def configured_law_blocks(current_path: str, uf: str, docs: tuple[dict, ...], chapter: dict) -> str:
    source_map = docs_by_source_id(docs)
    blocks = []
    for ref in chapter.get("refs", []):
        doc = source_map.get(ref["source"])
        if not doc:
            continue
        segments: list[tuple[str, str]] = []
        if uf == "PR":
            segments = pr_complete_law_segments(doc, ref, chapter)
        elif ref.get("articles"):
            segments = article_segments(doc, ref["articles"])
        elif ref.get("full_text"):
            if doc["chars"] <= 28000:
                segments = [("Texto integral do ato", clean_law_segment(doc["text"], limit=30000))]
            else:
                needles = [
                    "isenção", "redução de base", "crédito presumido", "diferimento",
                    "regime especial", "benefício fiscal", "EFD", "substituição tributária",
                ]
                segments = [
                    (f"Trecho {idx}", clean_law_segment(item, limit=6200))
                    for idx, item in enumerate(excerpts(doc["text"], needles, limit=6), start=1)
                ]
        elif ref.get("keywords"):
            segments = [
                (f"Trecho {idx}", clean_law_segment(item, limit=6200))
                for idx, item in enumerate(excerpts(doc["text"], ref["keywords"], limit=6), start=1)
            ]
        if not segments:
            segments = [
                (f"Trecho {idx}", clean_law_segment(item, limit=5000))
                for idx, item in enumerate(excerpts(doc["text"], [chapter["title"], chapter["summary"]], limit=2), start=1)
            ]
        law_html = "".join(f"""
<article class="article-block">
  <div class="article-number">{escape(label)}</div>
  <pre class="law-pre">{escape(segment)}</pre>
</article>
""" for label, segment in segments if segment)
        blocks.append(f"""
<section class="legal-document">
  <div class="document-heading">
    <div>
      <span class="eyebrow">{escape(doc['category_label'])}</span>
      <h3>{escape(doc['title'])}</h3>
      <p>Dispositivos essenciais para este capítulo. A íntegra está preservada na página-fonte do portal.</p>
    </div>
    <div class="document-actions">
      <a href="{escape(rel_href(current_path, source_path(uf, doc)))}">abrir fonte integral</a>
      <a href="{escape(doc.get('official_url', STATE_OFFICIAL_PORTALS.get(uf, '#')))}" target="_blank" rel="noopener">fonte pública</a>
    </div>
  </div>
  {law_html}
</section>
""")
    return "".join(blocks)


def render_configured_state_index_page(uf: str, docs: tuple[dict, ...], layout_func) -> str:
    profile = configured_profile(uf)
    name = profile.get("name", STATE_NAMES.get(uf, uf))
    current = index_path(uf)
    chapter_cards = []
    for chapter in configured_chapters(uf):
        chapter_cards.append(f"""
<a class="portal-card searchable-card" href="{escape(rel_href(current, configured_chapter_path(uf, chapter['id'])))}"
   data-search="{escape(name + ' ' + uf + ' ICMS beneficios fiscais ' + chapter['title'] + ' ' + chapter['summary'] + ' ' + chapter['theme'])}">
  <span class="card-kicker">{escape(chapter['theme'])}</span>
  <h3>{escape(chapter['title'])}</h3>
  <p>{escape(chapter['summary'])}</p>
</a>
""")
    body = f"""
<section class="hero-panel legal-hero">
  <div>
    <span class="eyebrow">{escape(uf)} · ICMS em tela</span>
    <h1>{escape(name)}: ICMS e benefícios fiscais em tela</h1>
    <p>{escape(profile.get('hero', 'Legislação estadual em tela por capítulos temáticos.'))}</p>
  </div>
  <aside class="hero-proof">
    <strong>Como estudar</strong>
    <p>Leia primeiro a regra maior. Depois avance para benefícios, regimes, documentos, fiscalização e riscos. A análise vem sempre depois do texto legal.</p>
  </aside>
</section>
<section class="law-ledger">
  <div>
    <h2>Material publicado</h2>
    <p>{fmt_num(len(docs))} fontes normativas de ICMS/{escape(uf)}, com {fmt_num(sum(int(doc['chars']) for doc in docs))} caracteres em tela.</p>
  </div>
  <div>
    <h2>Fontes centrais</h2>
    <p>{escape(profile.get('material', 'RICMS, leis, anexos e atos complementares de ICMS.'))}</p>
  </div>
  <div>
    <h2>Benefícios cobertos</h2>
    <p>{escape(profile.get('benefits', 'Isenção, redução, crédito, diferimento, ST, regimes especiais e prova fiscal.'))}</p>
  </div>
</section>
<section class="topic-index">
  <div class="section-heading">
    <span class="eyebrow">Índice por tema</span>
    <h2>Capítulos do ICMS de {escape(name)}</h2>
    <p>Cada entrada leva a uma seção específica, com lei em tela, explicação, aplicação por departamento, documentos de prova e riscos.</p>
  </div>
  <div class="card-grid">{''.join(chapter_cards)}</div>
</section>
<section class="continuity">
  <h2>Continuar a leitura</h2>
  <div>
    <a href="{escape(rel_href(current, state_page_path(uf)))}">voltar ao Estado</a>
    <a href="{escape(rel_href(current, 'confaz/index.html'))}">CONFAZ e LC 160</a>
    <a href="{escape(rel_href(current, 'federal/pis-cofins.html'))}">conectar com PIS/Cofins</a>
    <a href="{escape(rel_href(current, 'biblioteca/index.html'))}">biblioteca avançada</a>
  </div>
</section>
"""
    return layout_func(current, f"{name}: ICMS e benefícios fiscais em tela", f"ICMS/{uf}, benefícios fiscais, regimes, ST e prova documental.", body, "estados")


def render_configured_state_chapter_page(uf: str, docs: tuple[dict, ...], chapter: dict, layout_func) -> str:
    profile = configured_profile(uf)
    name = profile.get("name", STATE_NAMES.get(uf, uf))
    current = configured_chapter_path(uf, chapter["id"])
    related = []
    for other in configured_chapters(uf):
        if other["id"] == chapter["id"]:
            continue
        if other["theme"] == chapter["theme"] or len(related) < 4:
            related.append(other)
        if len(related) >= 5:
            break
    related_links = "".join(
        f'<a href="{escape(rel_href(current, configured_chapter_path(uf, item["id"])))}">{escape(item["title"])}</a>'
        for item in related
    )
    analysis_items = "".join(f"<p>{escape(item)}</p>" for item in chapter.get("analysis", []))
    body = f"""
<section class="hero-panel legal-hero">
  <div>
    <span class="eyebrow">{escape(name)} · {escape(chapter['theme'])}</span>
    <h1>{escape(chapter['title'])}</h1>
    <p>{escape(chapter['summary'])}</p>
  </div>
  <aside class="hero-proof">
    <strong>Leitura guiada</strong>
    <p>Primeiro a legislação em tela; depois interpretação, aplicação por departamento, prova e risco.</p>
  </aside>
</section>
<section class="topic-index compact-index">
  <div class="section-heading">
    <span class="eyebrow">Voltar ao índice</span>
    <h2>{escape(uf)} por capítulos</h2>
  </div>
  <div class="signal-law-links">
    <strong>Continuar no Estado</strong>
    <div>
      <a href="{escape(rel_href(current, index_path(uf)))}">índice de {escape(uf)}</a>
      <a href="{escape(rel_href(current, state_page_path(uf)))}">página principal</a>
      <a href="{escape(rel_href(current, 'confaz/index.html'))}">CONFAZ</a>
    </div>
  </div>
</section>
<section class="legal-chapters">
  <div class="section-heading">
    <span class="eyebrow">Legislação em tela</span>
    <h2>Texto legal antes da análise</h2>
    <p>Os blocos abaixo trazem os dispositivos nucleares deste assunto. A íntegra de cada ato fica aberta nas páginas-fonte do portal.</p>
  </div>
  {configured_law_blocks(current, uf, docs, chapter)}
</section>
<section class="content-block">
  <span class="eyebrow">Análise aplicada</span>
  <h2>Como interpretar</h2>
  {analysis_items}
</section>
<section class="law-ledger">
  <div>
    <h2>Aplicação por departamento</h2>
    <p>{escape(chapter.get('departments', 'Fiscal, contábil, financeiro e jurídico devem amarrar regra, documento, escrituração e pagamento.'))}</p>
  </div>
  <div>
    <h2>Documentos de prova</h2>
    <p>{escape(chapter.get('documents', 'XML, EFD, memória de cálculo, ato legal e comprovantes.'))}</p>
  </div>
  <div>
    <h2>Riscos comuns</h2>
    <p>{escape(chapter.get('risks', 'Aplicar tese sem dispositivo, condição, vigência ou prova documental suficiente.'))}</p>
  </div>
</section>
<section class="continuity">
  <h2>Continuar este estudo</h2>
  <div>{related_links}</div>
</section>
"""
    return layout_func(current, f"{name}: {chapter['title']}", chapter["summary"], body, "estados")


def render_configured_state_pages(uf: str, docs: tuple[dict, ...], layout_func) -> dict[str, str]:
    pages = {index_path(uf): render_configured_state_index_page(uf, docs, layout_func)}
    for chapter in configured_chapters(uf):
        pages[configured_chapter_path(uf, chapter["id"])] = render_configured_state_chapter_page(uf, docs, chapter, layout_func)
    for doc in docs:
        pages[source_path(uf, doc)] = render_source_page(uf, doc, layout_func)
    return pages


def render_index_page(uf: str, docs: list[dict], layout_func) -> str:
    name = STATE_NAMES.get(uf, uf)
    current = index_path(uf)
    cards = []
    for group in GROUP_DEFS:
        docs_for_group = group_docs(docs, group)
        cards.append(f"""
<a class="portal-card searchable-card" href="{escape(rel_href(current, group_path(uf, group['id'])))}"
   data-search="{escape(name + ' ' + group['title'] + ' ICMS beneficios fiscais')}">
  <span class="card-kicker">{escape(group['eyebrow'])}</span>
  <h3>{escape(group['title'])}</h3>
  <p>{escape(group['summary'])}</p>
  <small>{fmt_num(len(docs_for_group))} textos em tela</small>
</a>
""")
    body = f"""
<section class="hero-panel legal-hero">
  <div>
    <span class="eyebrow">{escape(uf)}</span>
    <h1>{escape(name)}: legislação de ICMS em tela</h1>
    <p>Regulamento, leis, anexos, benefícios fiscais, substituição tributária, alíquotas e prova documental organizados por assunto.</p>
  </div>
  <aside class="hero-proof">
    <strong>Fonte pública</strong>
    <p>Texto extraído dos atos oficiais baixados dos portais estaduais. O link do portal do ente fica indicado em cada página.</p>
  </aside>
</section>
<section class="law-ledger">
  <div>
    <h2>Material publicado</h2>
    <p>{fmt_num(len(docs))} textos estaduais de ICMS, com {fmt_num(sum(int(doc['chars']) for doc in docs))} caracteres em tela.</p>
  </div>
  <div>
    <h2>Como estudar</h2>
    <p>Abra primeiro ICMS completo, depois benefícios fiscais, alíquotas, ST e documentos. A tese prática deve nascer do texto em tela.</p>
  </div>
  <div>
    <h2>Portal do Estado</h2>
    <p><a href="{escape(STATE_OFFICIAL_PORTALS.get(uf, '#'))}" target="_blank" rel="noopener">abrir legislação tributária oficial</a></p>
  </div>
</section>
<section class="topic-index">
  <div class="section-heading">
    <span class="eyebrow">Índice por tema</span>
    <h2>Escolha o assunto antes do artigo</h2>
    <p>Cada entrada leva a uma página com leitura guiada e links para o texto integral em tela.</p>
  </div>
  <div class="card-grid">{''.join(cards)}</div>
</section>
<section class="continuity">
  <h2>Continuar a leitura</h2>
  <div>
    <a href="{escape(rel_href(current, state_page_path(uf)))}">voltar ao Estado</a>
    <a href="{escape(rel_href(current, 'confaz/index.html'))}">CONFAZ e benefícios</a>
    <a href="{escape(rel_href(current, 'federal/legislacao/index.html'))}">tributos federais em tela</a>
  </div>
</section>
"""
    return layout_func(current, f"{name}: legislação de ICMS em tela", f"ICMS, benefícios fiscais e prova de {name}.", body, "estados")


def render_group_page(uf: str, docs: list[dict], group: dict, layout_func) -> str:
    name = STATE_NAMES.get(uf, uf)
    current = group_path(uf, group["id"])
    matched = group_docs(docs, group)
    benefit_results = benefit_sector_results(matched) if group["id"] == "beneficios" else []
    benefit_sector_html = ""
    if benefit_results:
        benefit_sector_html = render_benefit_sector_index(current, uf, benefit_results) + render_benefit_sector_sections(current, uf, benefit_results)
    body = f"""
<section class="hero-panel legal-hero">
  <div>
    <span class="eyebrow">{escape(name)}</span>
    <h1>{escape(group['title'])}</h1>
    <p>{escape(group['summary'])}</p>
  </div>
  <aside class="hero-proof">
    <strong>Ordem de leitura</strong>
    <p>{escape(group['lesson'])}</p>
  </aside>
</section>
<section class="law-ledger">
  <div>
    <h2>Textos deste tema</h2>
    <p>{fmt_num(len(matched))} textos em tela, extraídos de atos oficiais estaduais.</p>
  </div>
  <div>
    <h2>Aplicação por departamento</h2>
    <p>Fiscal parametriza documento e escrituração; contábil concilia efeito; financeiro prova guia; jurídico fecha risco e vigência.</p>
  </div>
  <div>
    <h2>Portal oficial</h2>
    <p><a href="{escape(STATE_OFFICIAL_PORTALS.get(uf, '#'))}" target="_blank" rel="noopener">abrir legislação do Estado</a></p>
  </div>
</section>
<section class="content-block">
  <h2>Como interpretar</h2>
  <p>{escape(group['lesson'])}</p>
  <p>Não aplique a regra por título do arquivo. Leia o dispositivo, identifique operação, mercadoria, destinatário, período, condição e prova documental.</p>
</section>{benefit_sector_html}
{render_excerpts(current, uf, matched, group)}
<section class="section-wrap">
  <div class="section-heading">
    <span class="eyebrow">Texto integral</span>
    <h2>Fontes em tela</h2>
    <p>Abra cada fonte para ler a íntegra já publicada no portal.</p>
  </div>
  {render_doc_links(current, uf, matched)}
</section>
<section class="continuity">
  <h2>Continuar</h2>
  <div>
    <a href="{escape(rel_href(current, index_path(uf)))}">índice estadual</a>
    <a href="{escape(rel_href(current, group_path(uf, 'icms')))}">ICMS completo</a>
    <a href="{escape(rel_href(current, group_path(uf, 'beneficios')))}">benefícios fiscais</a>
    <a href="{escape(rel_href(current, 'confaz/index.html'))}">CONFAZ</a>
  </div>
</section>
"""
    return layout_func(current, f"{name}: {group['title']}", group["summary"], body, "estados")


def render_source_page(uf: str, doc: dict, layout_func) -> str:
    name = STATE_NAMES.get(uf, uf)
    current = source_path(uf, doc)
    body = f"""
<section class="hero-panel legal-hero">
  <div>
    <span class="eyebrow">{escape(doc['category_label'])}</span>
    <h1>{escape(doc['title'])}</h1>
    <p>Texto integral em tela para leitura, estudo, prova e conferência operacional de ICMS.</p>
  </div>
  <aside class="hero-proof">
    <strong>Arquivo publicado</strong>
    <p>{escape(doc['file'])}<br>{fmt_num(doc['chars'])} caracteres</p>
  </aside>
</section>
<section class="law-ledger">
  <div>
    <h2>Origem normativa</h2>
    {render_sources_list([doc])}
  </div>
  <div>
    <h2>Hash do texto</h2>
    <p>{escape(doc['sha256'][:32])}</p>
  </div>
  <div>
    <h2>Portal oficial</h2>
    <p><a href="{escape(doc.get('official_url', STATE_OFFICIAL_PORTALS.get(uf, '#')))}" target="_blank" rel="noopener">abrir fonte pública</a></p>
  </div>
</section>
<section class="legal-document searchable-card" data-search="{escape(doc['title'] + ' ' + doc['file'] + ' ' + doc['category_label'])}">
  <div class="document-heading">
    <div>
      <span class="eyebrow">Legislação em tela</span>
      <h2>{escape(doc['category_label'])}</h2>
      <p>Leia o texto antes da análise prática. Depois volte ao índice temático do Estado para conectar regra, benefício, documento e prova.</p>
    </div>
    <div class="document-actions">
      <a href="{escape(rel_href(current, index_path(uf)))}">índice estadual</a>
      <span>{escape(UPDATED_ON)}</span>
    </div>
  </div>
  {render_chunks(clean_law_segment(doc['text'], limit=max(len(doc['text']) + 1000, 12000)), doc['id'])}
</section>
"""
    return layout_func(current, f"{doc['title']} | {name}", f"Texto integral de ICMS de {name}.", body, "estados")


def build_state_legal_pages(layout_func, data: dict) -> dict[str, str]:
    pages: dict[str, str] = {}
    for state in data.get("states", []):
        uf = state["uf"]
        if uf == "GO":
            continue
        if not state_is_deep_published(uf):
            continue
        docs = publishable_state_documents(uf)
        if not docs:
            continue
        if uf == "BA":
            pages.update(render_ba_pages(docs, layout_func))
            continue
        if uf == "DF":
            pages.update(render_df_pages(docs, layout_func))
            continue
        if uf == "MT":
            pages.update(render_mt_pages(docs, layout_func))
            continue
        if uf == "RN":
            pages.update(render_rn_pages(docs, layout_func))
            continue
        if uf in CONFIGURED_STATE_CHAPTERS:
            pages.update(render_configured_state_pages(uf, docs, layout_func))
            continue
        pages[index_path(uf)] = render_index_page(uf, docs, layout_func)
        for group in GROUP_DEFS:
            pages[group_path(uf, group["id"])] = render_group_page(uf, docs, group, layout_func)
        for doc in docs:
            pages[source_path(uf, doc)] = render_source_page(uf, doc, layout_func)
    return pages


def state_legislation_teaser(uf: str, current_path: str) -> str:
    if uf == "GO":
        links = [
            ("ICMS/GO em tela", "estados/goias/legislacao/index.html"),
            ("benefícios fiscais de Goiás", "estados/goias/legislacao/beneficios-regra-maior.html"),
        ]
    elif uf == "BA" and state_is_deep_published(uf) and publishable_state_documents(uf):
        links = [
            ("Bahia: índice completo", index_path("BA")),
            ("ICMS: regra matriz", ba_chapter_path("icms-regra-matriz")),
            ("base, alíquotas e apuração", ba_chapter_path("base-aliquota-apuracao")),
            ("benefícios fiscais e LC 160", ba_chapter_path("beneficios-matriz-lc160")),
            ("DESENVOLVE", ba_chapter_path("desenvolve")),
            ("EFD, documentos e prova", ba_chapter_path("documentos-efd-prova")),
        ]
    elif uf == "DF" and state_is_deep_published(uf) and publishable_state_documents(uf):
        links = [
            ("Distrito Federal: índice completo", index_path("DF")),
            ("ICMS: regra matriz", df_chapter_path("icms-regra-matriz")),
            ("base, alíquotas e apuração", df_chapter_path("base-aliquota-apuracao")),
            ("benefícios fiscais e LC 160", df_chapter_path("beneficios-matriz-lc160")),
            ("regime especial e crédito outorgado", df_chapter_path("regime-especial-apuracao")),
            ("EMPREGA-DF, PRÓ-DF e Desenvolve-DF", df_chapter_path("emprega-df-prodf-desenvolve")),
            ("EFD, documentos e prova", df_chapter_path("documentos-efd-prova")),
        ]
    elif uf == "MT" and state_is_deep_published(uf) and publishable_state_documents(uf):
        links = [
            ("Mato Grosso: índice completo", index_path("MT")),
            ("ICMS: regra matriz", mt_chapter_path("icms-regra-matriz")),
            ("base, alíquotas e apuração", mt_chapter_path("base-aliquota-apuracao")),
            ("benefícios fiscais e LC 160", mt_chapter_path("beneficios-matriz-lc160")),
            ("PRODEIC e desenvolvimento", mt_chapter_path("prodeic-desenvolvimento")),
            ("cBenef, EFD e prova", mt_chapter_path("documentos-cbenef-efd-prova")),
        ]
    elif uf == "RN" and state_is_deep_published(uf) and publishable_state_documents(uf):
        links = [
            ("Rio Grande do Norte: índice completo", index_path("RN")),
            ("ICMS: regra matriz", rn_chapter_path("icms-regra-matriz")),
            ("base, alíquotas, FECOP e crédito", rn_chapter_path("base-aliquota-apuracao")),
            ("benefícios fiscais e LC 160", rn_chapter_path("beneficios-matriz-lc160")),
            ("PROEDI e desenvolvimento", rn_chapter_path("proedi-desenvolvimento")),
            ("ST, antecipação e combustíveis", rn_chapter_path("st-antecipacao-combustiveis")),
            ("cBenef, EFD e prova", rn_chapter_path("documentos-cbenef-efd-prova")),
        ]
    elif uf in CONFIGURED_STATE_CHAPTERS and state_is_deep_published(uf) and publishable_state_documents(uf):
        chapters = configured_chapters(uf)
        links = [(f"{STATE_NAMES.get(uf, uf)}: índice completo", index_path(uf))]
        for chapter_id in [
            "icms-regra-matriz",
            "base-aliquota-apuracao",
            "beneficios-matriz-lc160",
            "mapa-revisado-beneficios",
            "documentos-efd-prova",
        ]:
            if any(chapter["id"] == chapter_id for chapter in chapters):
                chapter = configured_chapter_by_id(uf, chapter_id)
                links.append((chapter["title"], configured_chapter_path(uf, chapter_id)))
    else:
        if not state_is_deep_published(uf):
            step = state_curation(uf).get("next_step", "Curadoria fonte-a-fonte pendente.")
            manifest = state_source_manifest(uf)
            if manifest:
                manifest_path = state_source_manifest_path(uf)
                manifest_rel = manifest_path.relative_to(ROOT).as_posix() if manifest_path else "#"
                source_links = []
                if manifest.get("fontes"):
                    for source in manifest.get("fontes", []):
                        target = (manifest_path.parent / source["arquivo"]).relative_to(ROOT).as_posix() if manifest_path else "#"
                        source_links.append(
                            f'<a href="{escape(rel_href(current_path, target))}">{escape(source["titulo"])}</a>'
                        )
                else:
                    for filename in manifest.get("arquivos", []):
                        target = (manifest_path.parent / filename).relative_to(ROOT).as_posix() if manifest_path else "#"
                        label = filename.rsplit(".", 1)[0]
                        label = re.sub(r"_fonte_oficial", "", label, flags=re.I)
                        label = re.sub(r"_\d{4}-\d{2}-\d{2}$", "", label)
                        label = label.replace("_", " ")
                        source_links.append(
                            f'<a href="{escape(rel_href(current_path, target))}">{escape(label)}</a>'
                        )
                source_links.append(
                    f'<a href="{escape(rel_href(current_path, manifest_rel))}">Manifesto do pacote normativo</a>'
                )
                rendered_links = "".join(source_links)
                return f"""
<section class="continuity legal-continuity">
  <h2>Pacote normativo em organização</h2>
  <p>Os textos legais principais deste Estado já foram salvos no repositório em formato aberto. A próxima passagem é transformar esse material em capítulos temáticos, com lei em tela, análise, prova documental e riscos por assunto.</p>
  <div>{rendered_links}</div>
  <p>{escape(step)}</p>
</section>
"""
            return f"""
<section class="continuity legal-continuity">
  <h2>Curadoria estadual em andamento</h2>
  <p>O conteúdo profundo deste Estado foi retirado da publicação até que RICMS, benefícios fiscais e atos modificadores sejam revisados contra fonte pública vigente e salvos em texto local limpo.</p>
  <div>
    <a href="{escape(STATE_OFFICIAL_PORTALS.get(uf, '#'))}" target="_blank" rel="noopener">{escape(step)}</a>
  </div>
</section>
"""
        docs = publishable_state_documents(uf)
        if not docs:
            return ""
        links = [
            (f"{STATE_NAMES.get(uf, uf)}: índice estadual", index_path(uf)),
            ("ICMS completo", group_path(uf, "icms")),
            ("benefícios fiscais", group_path(uf, "beneficios")),
            ("alíquotas e base", group_path(uf, "aliquotas")),
            ("substituição tributária", group_path(uf, "st")),
        ]
    rendered = "".join(f'<a href="{escape(rel_href(current_path, target))}">{escape(label)}</a>' for label, target in links)
    return f"""
<section class="continuity legal-continuity">
  <h2>Legislação estadual em tela</h2>
  <p>Esta página tem caminho direto para o texto normativo estadual, organizado por assunto.</p>
  <div>{rendered}</div>
</section>
"""


def state_signal_links(uf: str, signal_key: str, current_path: str) -> str:
    if uf == "GO":
        return ""
    if uf == "BA":
        if not state_is_deep_published(uf) or not publishable_state_documents(uf):
            return ""
        chapter_id = BA_SIGNAL_CHAPTER_MAP.get(signal_key, "icms-regra-matriz")
        chapter = ba_chapter_by_id(chapter_id)
        return f"""
<div class="signal-law-links">
  <strong>Capítulo baiano para estudar agora</strong>
  <div>
    <a href="{escape(rel_href(current_path, ba_chapter_path(chapter_id)))}">{escape(chapter['title'])}</a>
    <a href="{escape(rel_href(current_path, index_path('BA')))}">índice completo da Bahia</a>
  </div>
</div>
"""
    if uf == "DF":
        if not state_is_deep_published(uf) or not publishable_state_documents(uf):
            return ""
        chapter_id = DF_SIGNAL_CHAPTER_MAP.get(signal_key, "icms-regra-matriz")
        chapter = df_chapter_by_id(chapter_id)
        return f"""
<div class="signal-law-links">
  <strong>Capítulo do DF para estudar agora</strong>
  <div>
    <a href="{escape(rel_href(current_path, df_chapter_path(chapter_id)))}">{escape(chapter['title'])}</a>
    <a href="{escape(rel_href(current_path, index_path('DF')))}">índice completo do DF</a>
  </div>
</div>
"""
    if uf == "MT":
        if not state_is_deep_published(uf) or not publishable_state_documents(uf):
            return ""
        chapter_id = MT_SIGNAL_CHAPTER_MAP.get(signal_key, "icms-regra-matriz")
        chapter = mt_chapter_by_id(chapter_id)
        return f"""
<div class="signal-law-links">
  <strong>Capítulo de MT para estudar agora</strong>
  <div>
    <a href="{escape(rel_href(current_path, mt_chapter_path(chapter_id)))}">{escape(chapter['title'])}</a>
    <a href="{escape(rel_href(current_path, index_path('MT')))}">índice completo de MT</a>
  </div>
</div>
"""
    if uf == "RN":
        if not state_is_deep_published(uf) or not publishable_state_documents(uf):
            return ""
        chapter_id = RN_SIGNAL_CHAPTER_MAP.get(signal_key, "icms-regra-matriz")
        chapter = rn_chapter_by_id(chapter_id)
        return f"""
<div class="signal-law-links">
  <strong>Capítulo do RN para estudar agora</strong>
  <div>
    <a href="{escape(rel_href(current_path, rn_chapter_path(chapter_id)))}">{escape(chapter['title'])}</a>
    <a href="{escape(rel_href(current_path, index_path('RN')))}">índice completo do RN</a>
  </div>
</div>
"""
    if uf in CONFIGURED_STATE_CHAPTERS:
        if not state_is_deep_published(uf) or not publishable_state_documents(uf):
            return ""
        profile = configured_profile(uf)
        chapter_id = profile.get("signal_map", {}).get(signal_key, "icms-regra-matriz")
        chapter = configured_chapter_by_id(uf, chapter_id)
        return f"""
<div class="signal-law-links">
  <strong>Capítulo de {escape(uf)} para estudar agora</strong>
  <div>
    <a href="{escape(rel_href(current_path, configured_chapter_path(uf, chapter_id)))}">{escape(chapter['title'])}</a>
    <a href="{escape(rel_href(current_path, index_path(uf)))}">índice completo de {escape(uf)}</a>
  </div>
</div>
"""
    if not state_is_deep_published(uf) or not publishable_state_documents(uf):
        return ""
    group_id = SIGNAL_TO_GROUP.get(signal_key, "icms")
    target = group_path(uf, group_id)
    source = group_path(uf, "icms")
    return f"""
<div class="signal-law-links">
  <strong>Legislação estadual para estudar agora</strong>
  <div>
    <a href="{escape(rel_href(current_path, target))}">{escape(group_by_id(group_id)['title'])}</a>
    <a href="{escape(rel_href(current_path, source))}">ICMS completo</a>
  </div>
</div>
"""


def state_legal_search_entries(data: dict) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for state in data.get("states", []):
        uf = state["uf"]
        if uf == "GO":
            continue
        if not state_is_deep_published(uf):
            continue
        docs = publishable_state_documents(uf)
        if not docs:
            continue
        name = STATE_NAMES.get(uf, uf)
        if uf == "BA":
            entries.append({
                "title": "Bahia: ICMS e benefícios fiscais em tela",
                "url": index_path("BA"),
                "summary": "Lei do ICMS, RICMS, anexos, substituição tributária, DESENVOLVE, PROIND, PRONAVAL, crédito presumido, informática, eletrônica, LC 160 e EFD.",
                "tags": "BA Bahia ICMS RICMS benefícios fiscais alíquotas base cálculo substituição tributária ST DESENVOLVE PROIND PRONAVAL crédito presumido informática eletrônica EFD SPED LC 160 Convênio 190",
            })
            for chapter in BA_CHAPTERS:
                entries.append({
                    "title": f"Bahia: {chapter['title']}",
                    "url": ba_chapter_path(chapter["id"]),
                    "summary": chapter["summary"],
                    "tags": f"BA Bahia ICMS benefícios fiscais {chapter['theme']} {chapter['title']} {chapter['summary']}",
                })
            for title, url, tags in [
                ("Bahia: benefícios para indústria e implantação", ba_chapter_path("desenvolve"), "DESENVOLVE dilação diferimento implantação ampliação indústria incentivo"),
                ("Bahia: eletrônicos, informática e automação", ba_chapter_path("programas-setoriais"), "informática eletrônica automação PROIND Decreto 4316 indústria tecnologia"),
                ("Bahia: naval e PROIND", ba_chapter_path("programas-setoriais"), "PRONAVAL PROIND naval indústria implantação incentivo fiscal"),
                ("Bahia: crédito presumido e outorgado", ba_chapter_path("beneficios-matriz-lc160"), "crédito presumido crédito outorgado incentivo benefício LC 160 Convênio 190"),
                ("Bahia: substituição tributária por mercadoria", ba_chapter_path("substituicao-tributaria-antecipacao"), "substituição tributária ST CEST MVA mercadoria antecipação"),
            ]:
                entries.append({
                    "title": title,
                    "url": url,
                    "summary": "Entrada direta para o capítulo temático correspondente, com texto legal em tela e análise aplicada.",
                    "tags": f"BA Bahia ICMS benefícios fiscais {tags}",
                })
            continue
        if uf == "DF":
            entries.append({
                "title": "Distrito Federal: ICMS e benefícios fiscais em tela",
                "url": index_path("DF"),
                "summary": "Lei do ICMS/DF, RICMS/DF, Cadernos, LC 160, regime especial, crédito outorgado, EMPREGA-DF, PRÓ-DF II, Desenvolve-DF, diferimento agro, ST e EFD.",
                "tags": "DF Distrito Federal ICMS RICMS benefícios fiscais alíquotas base cálculo substituição tributária ST EMPREGA-DF PRO-DF Desenvolve-DF crédito outorgado diferimento EFD SPED LC 160 Convênio 190",
            })
            for chapter in DF_CHAPTERS:
                entries.append({
                    "title": f"Distrito Federal: {chapter['title']}",
                    "url": df_chapter_path(chapter["id"]),
                    "summary": chapter["summary"],
                    "tags": f"DF Distrito Federal ICMS benefícios fiscais {chapter['theme']} {chapter['title']} {chapter['summary']}",
                })
            for title, url, tags in [
                ("Distrito Federal: atacado e crédito outorgado", df_chapter_path("regime-especial-apuracao"), "atacado atacadista crédito outorgado regime especial apuração Lei 5005 Decreto 39753"),
                ("Distrito Federal: EMPREGA-DF, PRÓ-DF II e Desenvolve-DF", df_chapter_path("emprega-df-prodf-desenvolve"), "EMPREGA-DF PRODF PRÓ-DF Desenvolve-DF desenvolvimento econômico incentivo investimento emprego"),
                ("Distrito Federal: alho, agro e diferimento", df_chapter_path("beneficios-setoriais-agro-atacado"), "alho agro agropecuário diferimento insumos crédito outorgado setor produto"),
                ("Distrito Federal: substituição tributária e antecipação", df_chapter_path("substituicao-tributaria-antecipacao"), "substituição tributária ST antecipação CEST MVA Anexo IV responsabilidade"),
                ("Distrito Federal: EFD ICMS/IPI e prova", df_chapter_path("documentos-efd-prova"), "EFD SPED ICMS IPI documento fiscal XML prova escrituração ajuste"),
            ]:
                entries.append({
                    "title": title,
                    "url": url,
                    "summary": "Entrada direta para o capítulo temático correspondente, com texto legal em tela e análise aplicada.",
                    "tags": f"DF Distrito Federal ICMS benefícios fiscais {tags}",
                })
            continue
        if uf == "MT":
            entries.append({
                "title": "Mato Grosso: ICMS e benefícios fiscais em tela",
                "url": index_path("MT"),
                "summary": "Lei do ICMS/MT, RICMS/MT, LC 631/2019, anexos de benefícios, PRODEIC, cBenef, substituição tributária, estimativa simplificada, agro e EFD.",
                "tags": "MT Mato Grosso ICMS RICMS benefícios fiscais alíquotas base cálculo substituição tributária ST PRODEIC crédito outorgado crédito presumido redução base isenção diferimento cBenef EFD SPED LC 160 Convênio 190",
            })
            for chapter in MT_CHAPTERS:
                entries.append({
                    "title": f"Mato Grosso: {chapter['title']}",
                    "url": mt_chapter_path(chapter["id"]),
                    "summary": chapter["summary"],
                    "tags": f"MT Mato Grosso ICMS benefícios fiscais {chapter['theme']} {chapter['title']} {chapter['summary']}",
                })
            for title, url, tags in [
                ("Mato Grosso: PRODEIC e desenvolvimento econômico", mt_chapter_path("prodeic-desenvolvimento"), "PRODEIC desenvolvimento econômico indústria comércio incentivo fiscal programa estadual"),
                ("Mato Grosso: isenção, redução e crédito outorgado", mt_chapter_path("isencoes-reducoes-creditos"), "isenção redução base crédito outorgado crédito presumido Anexo IV V VI cBenef"),
                ("Mato Grosso: agro, cesta básica e diferimento", mt_chapter_path("agro-cesta-diferimento"), "agro alimentos cesta básica vegetal animal biodiesel diferimento Anexo VII"),
                ("Mato Grosso: ST e estimativa simplificada", mt_chapter_path("st-estimativa-anexos"), "substituição tributária ST estimativa simplificada carga média CNAE Anexo X XIII"),
                ("Mato Grosso: cBenef, EFD e prova", mt_chapter_path("documentos-cbenef-efd-prova"), "cBenef EFD SPED XML documento fiscal código benefício Portaria 211"),
            ]:
                entries.append({
                    "title": title,
                    "url": url,
                    "summary": "Entrada direta para o capítulo temático correspondente, com texto legal em tela e análise aplicada.",
                    "tags": f"MT Mato Grosso ICMS benefícios fiscais {tags}",
                })
            continue
        if uf == "RN":
            entries.append({
                "title": "Rio Grande do Norte: ICMS e benefícios fiscais em tela",
                "url": index_path("RN"),
                "summary": "RICMS/RN, anexos de isenção, redução, crédito presumido, diferimento, antecipação, ST, PROEDI, FUNDERN, Tax Free, cBenef e matriz LC 160.",
                "tags": "RN Rio Grande do Norte ICMS RICMS benefícios fiscais alíquotas FECOP base cálculo substituição tributária ST antecipação PROEDI FUNDERN Tax Free crédito presumido redução base isenção diferimento cBenef EFD SPED LC 160 Convênio 190",
            })
            for chapter in RN_CHAPTERS:
                entries.append({
                    "title": f"Rio Grande do Norte: {chapter['title']}",
                    "url": rn_chapter_path(chapter["id"]),
                    "summary": chapter["summary"],
                    "tags": f"RN Rio Grande do Norte ICMS benefícios fiscais {chapter['theme']} {chapter['title']} {chapter['summary']}",
                })
            for title, url, tags in [
                ("Rio Grande do Norte: PROEDI e desenvolvimento industrial", rn_chapter_path("proedi-desenvolvimento"), "PROEDI desenvolvimento industrial crédito presumido incentivo fiscal FUNDERN regularidade"),
                ("Rio Grande do Norte: isenção, redução e crédito presumido", rn_chapter_path("isencoes-reducoes-creditos"), "isenção redução base crédito presumido Anexo 001 Anexo 003 Anexo 004 cBenef"),
                ("Rio Grande do Norte: agro, alimentos, pesca e diferimento", rn_chapter_path("agro-cesta-diferimento"), "agro alimentos abate gado bovino pesca óleo diesel biodiesel diferimento"),
                ("Rio Grande do Norte: ST, antecipação, combustíveis, trigo e veículos", rn_chapter_path("st-antecipacao-combustiveis"), "substituição tributária ST antecipação combustíveis lubrificantes trigo farinha veículos autopropulsados"),
                ("Rio Grande do Norte: Tax Free e restituição de ICMS", rn_chapter_path("mapa-revisado-beneficios"), "Tax Free restituição turistas estrangeiros saída país Convênio 150"),
                ("Rio Grande do Norte: cBenef, EFD e prova", rn_chapter_path("documentos-cbenef-efd-prova"), "cBenef EFD SPED XML NF-e NFC-e código benefício Portaria 970"),
            ]:
                entries.append({
                    "title": title,
                    "url": url,
                    "summary": "Entrada direta para o capítulo temático correspondente, com texto legal em tela e análise aplicada.",
                    "tags": f"RN Rio Grande do Norte ICMS benefícios fiscais {tags}",
                })
            continue
        if uf in CONFIGURED_STATE_CHAPTERS:
            profile = configured_profile(uf)
            entries.append({
                "title": f"{name}: ICMS e benefícios fiscais em tela",
                "url": index_path(uf),
                "summary": profile.get("hero", f"RICMS, leis, anexos, benefícios fiscais, alíquotas, ST e prova documental de {name}."),
                "tags": profile.get("tags", f"{uf} {name} ICMS RICMS benefícios fiscais alíquotas ST"),
            })
            for chapter in configured_chapters(uf):
                entries.append({
                    "title": f"{name}: {chapter['title']}",
                    "url": configured_chapter_path(uf, chapter["id"]),
                    "summary": chapter["summary"],
                    "tags": f"{uf} {name} ICMS benefícios fiscais {chapter['theme']} {chapter['title']} {chapter['summary']}",
                })
            for title, chapter_id, tags in [
                (f"{name}: isenções, reduções e créditos", "isencoes-reducoes-creditos", "isenção redução base crédito presumido máquinas medicamentos veículos saúde agro"),
                (f"{name}: mapa revisado dos benefícios", "mapa-revisado-beneficios", "inventário benefícios regimes especiais LC 160 CONFAZ crédito presumido redução base diferimento"),
                (f"{name}: agro, FUNDERSUL e diferimento", "agro-fundersul-diferimento", "agro produtor rural FUNDERSUL diferimento crédito presumido abate contribuição"),
                (f"{name}: MS-Empreendedor e regimes especiais", "ms-empreendedor-regimes", "MS-Empreendedor LC 93 incentivo industrial regime especial crédito presumido"),
                (f"{name}: COMPETE, INVEST e FUNDAP", "invest-compete-fundap", "COMPETE INVEST-ES FUNDAP regime especial contrato competitividade investimento importação crédito presumido diferimento"),
                (f"{name}: crédito presumido e acumulado", "creditos-presumidos-acumulados", "crédito presumido crédito acumulado transferência utilização Anexo III Anexo IV"),
                (f"{name}: exportação e crédito acumulado", "creditos-exportacao-acumulado", "exportação não incidência manutenção crédito acumulado transferência utilização"),
                (f"{name}: diferimento e regimes especiais", "diferimento-regimes-especiais", "diferimento regime especial disposições especiais Anexo VI Anexo VIII"),
                (f"{name}: ST, EFD e prova", "documentos-efd-prova", "substituição tributária EFD SPED XML documento fiscal cadastro prova"),
            ]:
                if any(chapter["id"] == chapter_id for chapter in configured_chapters(uf)):
                    entries.append({
                        "title": title,
                        "url": configured_chapter_path(uf, chapter_id),
                        "summary": "Entrada direta para o capítulo temático correspondente, com texto legal em tela e análise aplicada.",
                        "tags": f"{uf} {name} ICMS benefícios fiscais {tags}",
                    })
            continue
        entries.append({
            "title": f"{name}: legislação de ICMS em tela",
            "url": index_path(uf),
            "summary": f"RICMS, leis, anexos, benefícios fiscais, alíquotas, ST e prova documental de {name}.",
            "tags": f"{uf} {name} ICMS RICMS benefícios fiscais alíquotas ST",
        })
        for group in GROUP_DEFS:
            entries.append({
                "title": f"{name}: {group['title']}",
                "url": group_path(uf, group["id"]),
                "summary": group["summary"],
                "tags": f"{uf} {name} {group['title']} ICMS benefícios fiscais",
            })
        beneficios_group = group_by_id("beneficios")
        for result in benefit_sector_results(group_docs(docs, beneficios_group)):
            sector = result["sector"]
            entries.append({
                "title": f"{name}: benefícios fiscais - {sector['title']}",
                "url": f"{group_path(uf, 'beneficios')}#{sector_anchor(sector)}",
                "summary": sector["summary"],
                "tags": f"{uf} {name} ICMS benefícios fiscais incentivo isenção redução crédito presumido {sector['title']} {' '.join(sector['keywords'])}",
            })
    return entries


def state_source_records() -> list[dict]:
    records: list[dict] = []
    for uf in STATE_NAMES:
        if uf == "GO":
            continue
        if not state_is_deep_published(uf):
            continue
        for doc in publishable_state_documents(uf):
            if doc["path"].is_relative_to(ROOT):
                file_ref = doc["path"].relative_to(ROOT).as_posix()
            elif doc["path"].is_relative_to(BD_ROOT):
                file_ref = doc["path"].relative_to(BD_ROOT).as_posix()
            else:
                file_ref = str(doc["path"])
            if uf == "BA":
                used_chapters = [
                    chapter["id"]
                    for chapter in BA_CHAPTERS
                    if any(ref.get("source") == doc.get("source_id") for ref in chapter.get("refs", []))
                ]
                module_title = "Bahia: ICMS e benefícios fiscais em tela"
            elif uf == "DF":
                used_chapters = [
                    chapter["id"]
                    for chapter in DF_CHAPTERS
                    if any(ref.get("source") == doc.get("source_id") for ref in chapter.get("refs", []))
                ]
                module_title = "Distrito Federal: ICMS e benefícios fiscais em tela"
            elif uf == "MT":
                used_chapters = [
                    chapter["id"]
                    for chapter in MT_CHAPTERS
                    if any(ref.get("source") == doc.get("source_id") for ref in chapter.get("refs", []))
                ]
                module_title = "Mato Grosso: ICMS e benefícios fiscais em tela"
            elif uf == "RN":
                used_chapters = [
                    chapter["id"]
                    for chapter in RN_CHAPTERS
                    if any(ref.get("source") == doc.get("source_id") for ref in chapter.get("refs", []))
                ]
                module_title = "Rio Grande do Norte: ICMS e benefícios fiscais em tela"
            elif uf in CONFIGURED_STATE_CHAPTERS:
                used_chapters = [
                    chapter["id"]
                    for chapter in configured_chapters(uf)
                    if any(ref.get("source") == doc.get("source_id") for ref in chapter.get("refs", []))
                ]
                module_title = f"{STATE_NAMES.get(uf, uf)}: ICMS e benefícios fiscais em tela"
            else:
                used_chapters = [group["id"] for group in GROUP_DEFS if doc_matches_group(doc, group)]
                module_title = f"{STATE_NAMES.get(uf, uf)}: legislação de ICMS em tela"
            records.append({
                "source_id": f"state-{uf.lower()}-{doc['id']}",
                "jurisdiction": uf,
                "title": doc["title"],
                "short": doc["category_label"],
                "official_url": doc.get("official_url") or STATE_OFFICIAL_PORTALS.get(uf, ""),
                "storage": {
                    "type": "local_text",
                    "files": [file_ref],
                    "sha256": {doc["file"]: doc["sha256"]},
                    "fetch_url": doc.get("official_url", ""),
                },
                "note": f"Texto estadual de ICMS publicado em {source_path(uf, doc)}.",
                "render": "full_text",
                "source_ranges": [],
                "modified_by": [],
                "used_by": [
                    {
                        "module_id": f"state-{uf.lower()}",
                        "module_title": module_title,
                        "chapters": used_chapters,
                    }
                ],
            })
    return records
