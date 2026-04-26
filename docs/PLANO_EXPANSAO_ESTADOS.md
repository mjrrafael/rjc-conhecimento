# Plano De Expansao Dos Estados

Este roteiro transforma cada UF no mesmo padrao aprovado para Goias: texto legal em tela, indice por tema, analise didatica, documentos de prova, riscos e continuidade com CONFAZ e federal.

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

- Bahia, Pernambuco, Ceara, Maranhao, Paraiba, Alagoas, Piaui, Rio Grande do Norte e Sergipe.
- Prioridade: beneficios industriais e atacadistas, fundos, regimes especiais, substituicao tributaria, importacao, cBenef e prova.

### Norte

- Amazonas, Para, Rondonia, Acre, Amapa, Roraima e Tocantins.
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
