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
