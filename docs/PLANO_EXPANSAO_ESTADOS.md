# Plano De Expansao Dos Estados

Este roteiro transforma cada UF no mesmo padrao aprovado para Goias: texto legal em tela, indice por tema, analise didatica, documentos de prova, riscos e continuidade com CONFAZ e federal.

## Estado Da Esteira Em 28/04/2026

- Estados profundos publicados ou aprovados: GO, BA, DF, MT, MS, RN, ES, MG, RJ, SP, PR, RS e SC.
- Estados publicados para leitura como `aguardando revisao`, sem conclusao tributaria aprovada ate nova curadoria: AC, AL, AM, AP, CE, MA, PA, PB, PE, PI, RO, RR, SE e TO.
- Regra de seguranca: pagina estadual estrutural nao significa conteudo completo. A UF so entra como profunda quando RICMS, lei material, beneficios fiscais, atos modificadores e fonte oficial limpa estiverem salvos em texto local, com manifesto e auditoria sem contaminacao por Taxas, IPVA ou ITCD/ITCMD.

## Regra Editorial

1. Ler lei material do ICMS, RICMS, anexos de beneficios, pauta, substituicao tributaria, regimes especiais, fundos, obrigacoes acessorias e atos modificadores.
2. Publicar apenas quando a tese estiver amarrada a ato oficial do Estado, CONFAZ ou Planalto.
3. Separar regra geral, excecoes, beneficios, isencoes, reducao de base, credito outorgado, diferimento, ST, cBenef, fundos, penalidades e prova.
4. Mostrar a legislacao em tela antes da analise.
5. Registrar fonte, URL oficial, arquivo de texto, hash, modulo e capitulos em `data/legal_sources_registry.json`.

## Ordem De Trabalho Por Regiao

### Centro-Oeste

- Goias: publicado e aprovado como modelo.
- Distrito Federal: ICMS, beneficios, FCP/Fundo, regimes, ST, documento fiscal.
- Mato Grosso: RICMS, incentivos, PRODEIC, diferimento, ST, fundos e prova.
- Mato Grosso do Sul: revisar ingestao do acervo, RICMS, incentivos, MS Forte/beneficios, ST e obrigações.

### Sudeste

- Sao Paulo: RICMS/SP, Anexos, Portarias CAT/SRE, credito outorgado, ST, DIFAL, regimes especiais.
- Minas Gerais: RICMS/MG, anexos, beneficios, regimes especiais, diferimento, ST e e-PTA.
- Rio de Janeiro: Livro/Regulamento, FECP, incentivos, beneficios, ST, regimes e fiscalizacao.
- Espirito Santo: RICMS/ES, Compete, Fundap/legados quando pertinentes, beneficios, ST e prova.

### Sul

- Parana: RICMS/PR, beneficios, diferimento, credito presumido, ST e documentos.
- Santa Catarina: RICMS/SC, TTD, beneficios, regimes especiais, ST e fiscalizacao.
- Rio Grande do Sul: RICMS/RS, Livro I/II/III, beneficios, Fundopem quando pertinente, ST e obrigações.

### Nordeste

- Bahia e Rio Grande do Norte: publicados.
- Pendentes, nesta ordem: Ceara, Maranhao, Paraiba, Pernambuco, Piaui, Alagoas e Sergipe.
- Prioridade: beneficios industriais e atacadistas, fundos, regimes especiais, substituicao tributaria, importacao, cBenef e prova.

### Norte

- Pendentes, nesta ordem: Acre, Amazonas, Amapa, Para, Rondonia, Roraima e Tocantins.
- Prioridade: Zona Franca, areas de livre comercio, incentivos regionais, beneficios estaduais, ICMS importacao, ST e conexao com IPI/PIS/Cofins.

## Esteira De Cada UF

1. Inventario dos atos oficiais.
2. Normalizacao do texto legal.
3. Cadastro da fonte no registro versionado.
4. Criacao dos capitulos tematicos.
5. Insercao da lei em tela.
6. Analise didatica por departamento.
7. Links de continuidade com CONFAZ, federal, manuais e painel fiscal.
8. Auditoria de links, ancoras, fontes, capitulos e mobile.
9. Publicacao em GitHub Pages.

## Atos Modificadores

Qualquer decreto, convenio, ajuste SINIEF, protocolo, portaria ou instrucao normativa que altere regra publicada deve entrar como nova fonte ou como `modified_by` no registro versionado, com impacto descrito no capitulo afetado.

## Pacote Minimo Para Aprovar Uma UF

Cada UF pendente precisa ter, no minimo:

1. Lei material do ICMS ou codigo tributario estadual com os dispositivos de ICMS identificados.
2. RICMS vigente em texto local limpo.
3. Anexos ou atos especificos de beneficios fiscais de ICMS.
4. Tabelas de cBenef/codigos de beneficio quando a UF exigir.
5. Normas de substituicao tributaria, antecipacao, pauta, MVA ou segmentos.
6. Normas de documentos fiscais, EFD, ajustes, guias, regimes especiais e prova.
7. Relacao com CONFAZ, LC 160/2017 e Convenio ICMS 190/2017 quando houver beneficio fiscal.
8. Manifesto com URL oficial, data de captura, hash, arquivo local e capitulos que usam a fonte.
