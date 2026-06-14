# Monitoramento legislativo recorrente - 14/06/2026

## Escopo executado

- Protocolo: continuidade da rotina de conferencia, revisao, atualizacao e correcao do Portal RJC Tributario Aberto.
- Repositorio: `mjrrafael/rjc-conhecimento`.
- Janela operacional: fontes oficiais conferidas em 14/06/2026, a partir do ultimo monitoramento publicado em 06/06/2026.
- Rotina localizada na memoria profunda: monitoramento semanal do portal, com varredura de fontes oficiais, atualizacao de dados/paginas, auditorias locais, registro em `docs/monitoramento` e validacao GitHub Pages quando houver publicacao.

## Criterio permanente de revisao dupla

Toda rodada do monitor deve gerar duas leituras independentes do mesmo portal:

- Revisao humana integral: menus, navegacao, hierarquia visual, organizacao didatica, clareza de explicacoes, datas, avisos de vigencia, links cruzados, referencias oficiais, coerencia entre pagina principal, subindices e paginas profundas.
- Revisao IA/LLM integral: `llms.txt`, `assets/llm-manifest.json`, `assets/portal-search.js`, `assets/portal-search-full.json`, `data-search`, metadados, chunks, separacao entre vigente/historico/a validar, stale content, texto corrompido, ruido OCR e risco de uma IA aplicar regra vencida como atual.

Cada achado deve indicar se afeta `humano`, `IA` ou `ambos`, e deve ser classificado como `CORRIGIR`, `A VALIDAR` ou `OK`.

## Fontes oficiais conferidas

- CONFAZ - Convenios ICMS 2026: https://www.confaz.fazenda.gov.br/legislacao/convenios/2026
- SVRS/NF-e - Documentos e Notas Tecnicas: https://dfe-portal.svrs.rs.gov.br/NFe/Documentos
- Receita Federal/SIJUT: conferida por publicacao decrescente; localizados Portaria RFB 695/2026, IN RFB 2.327/2026, Portarias RFB 693/2026 e 690/2026, ADE RFB 3/2026 e Ato Conjunto RFB/CGIBS 2/2026. Nenhum deles foi incorporado como pagina normativa integral nesta rodada sem captura do texto/anexos oficiais; houve apenas triagem e alerta publico.

## Achados incorporados

### CONFAZ - Convenios ICMS

- O indice oficial de 2026 passou a listar os Convenios ICMS 57/26 a 62/26.
- `data/confaz_ultimos_5_anos.json`: total dos ultimos 5 anos atualizado de 874 para 880 atos; 2026 atualizado de 56 para 62 atos.
- `confaz/ultimos-5-anos.html`: painel visual atualizado para refletir 880 atos e 62 convenios em 2026.
- `docs/master-audit.md`: contagem de Convenios ICMS atualizada para 880.
- Limite de interpretacao: os novos atos ficaram marcados como `a_classificar`; nao foi publicada conclusao tributaria material sem leitura individual do texto oficial de cada convenio.

#### Triagem inicial dos convenios novos

- CV057/26: transacao/litigio; altera o Convenio ICMS 210/2023.
- CV058/26: transacao administrativa; inclui o Para no Convenio ICMS 44/2026.
- CV059/26: recuperacao de creditos; altera o Convenio ICMS 35/2025.
- CV060/26: ampliacao de prazo de pagamento de ICMS em Rondonia, com recorte temporal proprio.
- CV061/26: isencao ligada a agricultura familiar, PNAE/PAA e convalidacao de operacoes.
- CV062/26: anistia no Espirito Santo para multas moratorias de ICMS ligadas a instabilidade tecnica de arrecadacao.

### SVRS/NF-e - Notas Tecnicas

- Revisao critica posterior: a referencia publica de leiaute da Reforma em NF-e/NFC-e foi corrigida de NT 2025.002 v1.35 para NT 2025.002 v1.50, publicada em 02/06/2026 no portal SVRS/NF-e.
- NT NF-e 2026.001 PAA v.1.02, publicada em 09/06/2026, registrada como alerta de governanca documental sobre Provedor de Assinatura e Autorizacao.
- NT NF-e 2026.004 CNPJ Alfa v.1.01, publicada em 08/06/2026, registrada como alerta de schema/homologacao e layout do web service NFeInutilizacao.
- `manual-fiscal.html` e `painel-fiscal/index.html`: textos de atualizacao oficial revisados para 14/06/2026.
- Limite de interpretacao: as notas foram tratadas como controle tecnico de DF-e; nao como alteracao automatica de carga tributaria.

### Receita Federal/SIJUT - triagem critica

- Portaria RFB 695/2026: identidade institucional do Programa Confia; alerta de compliance/governanca, sem efeito automatico de carga tributaria.
- IN RFB 2.327/2026: altera regra de CPSS; potencial interesse para modulo previdenciario/folha, pendente de leitura integral.
- Portaria RFB 693/2026: reabertura extraordinaria do PGD-C para informacoes do ano-calendario de 2025; assunto operacional especifico.
- Portaria RFB 690/2026: altera administracao/destinacao de mercadorias apreendidas; potencial interesse aduaneiro, pendente de leitura integral.
- ADE RFB 3/2026: codigos de enquadramento de exportacao com direito ao Reintegra; item potencialmente material para exportadores e marcado para captura prioritaria do anexo de codigos.
- Ato Conjunto RFB/CGIBS 2/2026: autorizacao de publicacao do Manual de Integracao e Swagger da Plataforma Publica do Split Payment; ja tratado no eixo de reforma/split payment como fonte tecnica.

## Ajustes tecnicos aplicados

- `scripts/legal_modules.py`: base `BD_LEGISLACAO` passa a ser resolvida por `RJC_BD_LEGISLACAO`, pelo caminho local `OneDrive/COWORK/BD_LEGISLACAO` ou, em ultimo caso, pelo caminho historico do ambiente anterior.
- `scripts/build_master_indexes.py`: mesmo criterio de autodeteccao aplicado a `BD_FEDERAL`.
- Motivo: permitir que a rotina rode neste computador sem depender do caminho antigo `C:\Users\kris2\...`.

## Validacoes executadas

- `python -m compileall -q scripts`: sem erro.
- `python scripts/audit_master_coverage.py`: sem falhas estruturais; 15 requisitos federais, 27 Estados, 12.246 beneficios, 7.976 linhas NCM e 3 familias CONFAZ auditadas.
- `python scripts/audit_portal.py`: 651 paginas HTML auditadas, sem falhas.
- `git diff --check`: sem erros de whitespace.
- Observacao: as validacoes acima foram reexecutadas apos a segunda revisao critica que localizou os atos SIJUT/RFB e corrigiu a referencia NT 2025.002 v1.50.

## Revisao critica de conteudo ja publicado

### CORRIGIR

- O build integral do portal ainda nao foi concluido nesta maquina. Houve regeneracao curta de `llms.txt`, `assets/llm-manifest.json`, `assets/portal-search.js`, `assets/portal-search-full.json` e sitemaps depois da correcao da NT 2025.002, mas isso nao substitui uma execucao completa de `build_portal.py` com todas as paginas de beneficios e estaduais.
- Ha mojibake visivel em paginas publicadas, especialmente no painel fiscal e em paginas estaduais de AM/CE/AP/GO, com textos como `alteraÃ§Ãµes`, `pÃ¡gina`, `legislaÃ§Ã£o`, `cÃ³digo`. Risco: leitura humana ruim, busca imprecisa e chunking ruim para IA.
- Paginas/arquivos de beneficios continuam grandes demais para leitura humana, GitHub Pages e ingestao por IA: `beneficios/index.html`, `data/benefits_crosswalk.json`, `assets/portal-search-full.json`, `beneficios/uf.html` e paginas tematicas acima de dezenas de MB. Risco: lentidao, falhas de renderizacao e respostas de IA com contexto ruidoso.
- Cards de beneficios ainda carregam texto bruto demais, incluindo residuos como `[] [] []`, linhas de separacao e historico de redacoes antigas misturado com regra atual. Risco: IA aplicar texto historico/revogado como vigente se o card nao separar claramente `vigente`, `historico` e `a validar`.

### CORRIGIDO NESTA REVISAO

- A Nota Tecnica 2025.002 `v1.35` deixou de ser tratada como referencia operacional atual. A fonte local foi marcada como `referencia historica superada`, o registro de fontes foi reexportado, 143 paginas legais foram regeneradas e `llms.txt`, `assets/llm-manifest.json`, `assets/portal-search.js` e `assets/portal-search-full.json` passaram a carregar alerta para conferir a versao mais recente no SVRS/NF-e antes de parametrizar NF-e/NFC-e.
- A varredura posterior nao encontrou mais as frases antigas que tratavam a NT 2025.002 v1.35 como leitura operacional vigente em HTML/JSON/TXT do portal.

### A VALIDAR ANTES DE CORRIGIR MERITO

- Foram encontrados varios trechos com vigencia ate `31/12/2025` ou periodos encerrados em paginas federais, estaduais e beneficios. Parte disso e historico legislativo legitimo, mas os trechos precisam ser reclassificados para impedir uso como regra atual sem conferencia fonte a fonte.
- Ha itens de cBenef/RJ e beneficios estaduais com datas finais de 2025 dentro de cards ainda pesquisaveis como regra atual. Precisam de confronto com tabelas 2026 antes de qualquer exclusao ou substituicao.
- Paginas com marcadores de `revisado com pendencias` somam volume relevante. Isso e transparente, mas precisa ser refletido nos metadados de IA como conteudo `nao aplicar sem validacao`.
- Muitas paginas ainda exibem `Atualizacao editorial: 25/04/2026` e alguns arquivos de dados seguem com `generated_on: 2026-06-06`. Nem toda data antiga e erro, mas paginas alteradas nesta rodada precisam de carimbo editorial coerente.

### OK ESTRUTURAL

- A conferencia local indicou 651 paginas HTML presentes simultaneamente em `llms.txt`, `assets/llm-manifest.json` e `sitemap.txt`. Portanto, nao foi encontrado buraco estrutural de pagina ausente nos indices principais; o problema atual e mais de frescor, qualidade textual e semantica de vigencia.

## Itens nao publicados nesta rodada

- `python scripts/build_portal.py` foi iniciado, mas excedeu o tempo local de execucao e foi interrompido; os artefatos globais gerados parcialmente foram descartados.
- Apos a revisao critica da NT 2025.002, houve regeneracao curta de paginas legais e indices globais essenciais (`llms.txt`, `assets/llm-manifest.json`, `assets/portal-search.js`, `assets/portal-search-full.json`, `sitemap.xml`, `sitemap.txt`). Isto nao equivale a build integral do portal.
- Alteracoes de `data/benefits_crosswalk.json` detectadas em execucao parcial nao foram mantidas, pois exigem curadoria propria antes de publicacao.

## Pendencias reais

- Reexecutar `build_portal.py` em ambiente com tempo maior ou CI antes de publicar uma rodada completa de assets globais.
- Capturar e versionar a fonte integral da NT 2025.002 v1.50 antes de regenerar as paginas profundas que ainda exibem a transcricao da v1.35 como documento em tela.
- Capturar e versionar o ADE RFB 3/2026, inclusive anexo de codigos Reintegra, antes de criar pagina propria ou alterar orientacao de exportadores.
- Ler integralmente IN RFB 2.327/2026, Portarias RFB 695/2026, 693/2026 e 690/2026 para decidir se entram em Confia, folha/previdenciario ou aduaneiro.
- Ler e classificar individualmente os Convenios ICMS 57/26 a 62/26 antes de qualquer aplicacao material.
- Revisar a matriz `benefits_crosswalk.json`, que segue acima de 50 MB e sensivel a churn de gerador.
- Confirmar Bahia Liquida Bahia 2026 com texto integral oficial do Decreto 24.538/2026 antes de incorporar ao portal.
- Revisitar CGIBS e portais estaduais que apresentaram bloqueio/reset na rodada de 06/06/2026.
- Publicacao em GitHub/Pages depende de autenticacao GitHub disponivel no ambiente local.
