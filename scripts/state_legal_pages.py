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


def paragraph_candidates(text: str) -> list[str]:
    chunks = re.split(r"\n\s*\n|\r\n\s*\r\n", text)
    cleaned = []
    for chunk in chunks:
        value = re.sub(r"\s+", " ", chunk).strip()
        if len(value) < 180:
            continue
        if re.search(r"\.{6,}|={8,}|-{8,}", value):
            continue
        cleaned.append(value)
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


STATE_ARTICLE_RE = re.compile(r"(?m)^\s*Art\.\s*(\d+(?:-[A-Za-z])?)\s*(?:º|°|o)?\.?")


def clean_law_segment(text: str, limit: int = 12000) -> str:
    skip_prefixes = ("TITULO:", "TEMA:", "TIPO:", "FONTE PUBLICA:", "DATA DA CAPTURA:", "TEXTO EXTRAIDO")
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            lines.append("")
            continue
        if stripped.startswith("====="):
            continue
        if any(stripped.startswith(prefix) for prefix in skip_prefixes):
            continue
        if stripped.lower().endswith(".doc") and len(stripped) < 80:
            continue
        lines.append(line.rstrip())
    cleaned = "\n".join(lines).strip()
    cleaned = re.sub(r"\n{4,}", "\n\n\n", cleaned)
    if len(cleaned) > limit:
        cleaned = cleaned[:limit].rsplit("\n", 1)[0].strip() + "\n\n[continua na fonte integral em tela]"
    return cleaned


def article_segments(doc: dict, numbers: list[str], max_segments_per_article: int = 4) -> list[tuple[str, str]]:
    matches = list(STATE_ARTICLE_RE.finditer(doc["text"]))
    wanted = {number.upper() for number in numbers}
    by_number: dict[str, list[str]] = {number.upper(): [] for number in numbers}
    for index, match in enumerate(matches):
        number = match.group(1).upper()
        if number not in wanted:
            continue
        end = matches[index + 1].start() if index + 1 < len(matches) else len(doc["text"])
        block = clean_law_segment(doc["text"][match.start():end], limit=14000)
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
  {render_chunks(doc['text'], doc['id'])}
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
