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
- Cards de beneficios ainda carregam texto bruto demais, incluindo marcadores de listas vazias, linhas de separacao e historico de redacoes antigas misturado com regra atual. Risco: IA aplicar texto historico/revogado como vigente se o card nao separar claramente `vigente`, `historico` e `a validar`.

### CORRIGIDO NESTA REVISAO

- A Nota Tecnica 2025.002 `v1.35` deixou de ser tratada como referencia operacional atual. A fonte local foi marcada como `referencia historica superada`, o registro de fontes foi reexportado, 143 paginas legais foram regeneradas e `llms.txt`, `assets/llm-manifest.json`, `assets/portal-search.js` e `assets/portal-search-full.json` passaram a carregar alerta para conferir a versao mais recente no SVRS/NF-e antes de parametrizar NF-e/NFC-e.
- A varredura posterior nao encontrou mais as frases antigas que tratavam a NT 2025.002 v1.35 como leitura operacional vigente em HTML/JSON/TXT do portal.

### A VALIDAR ANTES DE CORRIGIR MERITO

- Foram encontrados varios trechos com vigencia ate `31/12/2025` ou periodos encerrados em paginas federais, estaduais e beneficios. Parte disso e historico legislativo legitimo, mas os trechos precisam ser reclassificados para impedir uso como regra atual sem conferencia fonte a fonte.
- Ha itens de cBenef/RJ e beneficios estaduais com datas finais de 2025 dentro de cards ainda pesquisaveis como regra atual. Precisam de confronto com tabelas 2026 antes de qualquer exclusao ou substituicao.
- Paginas com marcadores de `revisado com pendencias` somam volume relevante. Isso e transparente, mas precisa ser refletido nos metadados de IA como conteudo `nao aplicar sem validacao`.
- Resolvido localmente em 14/06/2026 17:09: paginas HTML, badges estruturais, `llms.txt` e indices de busca foram regenerados/normalizados para `Atualizacao editorial: 14/06/2026`. O auditor do portal agora bloqueia regressao para a data editorial antiga de abril/2026.

### OK ESTRUTURAL

- A conferencia local indicou 651 paginas HTML presentes simultaneamente em `llms.txt`, `assets/llm-manifest.json` e `sitemap.txt`. Portanto, nao foi encontrado buraco estrutural de pagina ausente nos indices principais; o problema atual e mais de frescor, qualidade textual e semantica de vigencia.

## Itens nao publicados nesta rodada

- `python scripts/build_portal.py` foi iniciado, mas excedeu o tempo local de execucao e foi interrompido; os artefatos globais gerados parcialmente foram descartados.
- Apos a revisao critica da NT 2025.002, houve regeneracao curta de paginas legais e indices globais essenciais (`llms.txt`, `assets/llm-manifest.json`, `assets/portal-search.js`, `assets/portal-search-full.json`, `sitemap.xml`, `sitemap.txt`). Isto nao equivale a build integral do portal.
- Alteracoes de `data/benefits_crosswalk.json` detectadas em execucao parcial nao foram mantidas, pois exigem curadoria propria antes de publicacao.

## Pendencias reais

- Build integral local reexecutado em 14/06/2026 com tempo maior e 651 paginas auditadas sem falhas; publicacao ainda depende de commit/PR/merge no GitHub.
- Capturar e versionar a fonte integral da NT 2025.002 v1.50 antes de regenerar as paginas profundas que ainda exibem a transcricao da v1.35 como documento em tela.
- Capturar e versionar o ADE RFB 3/2026, inclusive anexo de codigos Reintegra, antes de criar pagina propria ou alterar orientacao de exportadores.
- Ler integralmente IN RFB 2.327/2026, Portarias RFB 695/2026, 693/2026 e 690/2026 para decidir se entram em Confia, folha/previdenciario ou aduaneiro.
- Ler e classificar individualmente os Convenios ICMS 57/26 a 62/26 antes de qualquer aplicacao material.
- Revisar a matriz `benefits_crosswalk.json`, que segue acima de 50 MB e sensivel a churn de gerador.
- Confirmar Bahia Liquida Bahia 2026 com texto integral oficial do Decreto 24.538/2026 antes de incorporar ao portal.
- Revisitar CGIBS e portais estaduais que apresentaram bloqueio/reset na rodada de 06/06/2026.
- Publicacao em GitHub/Pages depende de autenticacao GitHub disponivel no ambiente local.

## Rodada complementar de saneamento editorial e IA - 14/06/2026

### Fontes oficiais rechecadas

- CONFAZ 2026: https://www.confaz.fazenda.gov.br/legislacao/convenios/2026
- CONVENIO ICMS 62/26: https://www.confaz.fazenda.gov.br/legislacao/convenios/2026/CV062_26
- Portal NF-e/SVRS Documentos: https://dfe-portal.svrs.rs.gov.br/NFe/Documentos
- Noticia SVRS sobre NT 2025.002 v1.50: https://dfe-portal.svrs.rs.gov.br/DFE/Noticias/2976
- SIJUT/RFB consulta por publicacao decrescente: https://normas.receita.fazenda.gov.br/sijut2consulta/consulta.action?anoAtoFacet=&ano_ato=&dt_fim=&dt_inicio=&facetsExistentes=&lblTiposAtosSelecionados=&numero_ato=&optOrdem=Publicacao_DESC&ordemColuna=&ordemDirecao=&orgaosSelecionados=RFB%3B+RFB&siglaOrgaoFacet=&termoBusca=&tipoAtoFacet=&tipoConsulta=formulario&tipoData=2&tiposAtosSelecionados=
- Regulamentos do CGIBS: https://www.cgibs.gov.br/regulamentos
- Noticia RFB/CGIBS sobre split payment em 03/06/2026: https://www.gov.br/receitafederal/pt-br/assuntos/noticias/2026/junho/receita-federal-e-cgibs-publicaram-hoje-a-documentacao-tecnica-da-plataforma-publica-do-split-payment

### Achados consolidados com impacto

| URL oficial | Data | Ato/objeto | Impacto | Arquivo afetado | Publico afetado | Status |
| --- | --- | --- | --- | --- | --- | --- |
| https://www.confaz.fazenda.gov.br/legislacao/convenios/2026 | 14/06/2026 | Indice de Convenios ICMS 2026 conferido com 62 atos | Confirmou manutencao da contagem de 2026 e sustentou a atualizacao de totais no portal | `data/confaz_ultimos_5_anos.json`, `confaz/ultimos-5-anos.html`, `docs/master-audit.md` | ambos | OK |
| https://www.confaz.fazenda.gov.br/legislacao/convenios/2026/CV062_26 | 26/05/2026 publicacao; 12/06/2026 ratificacao | Convenio ICMS 62/26 | Reforcou a classificacao do CV062/26 como anistia ligada a instabilidade tecnica de arrecadacao no ES | `docs/monitoramento/monitoramento-legislativo-2026-06-14.md` | humano | OK |
| https://dfe-portal.svrs.rs.gov.br/NFe/Documentos | 14/06/2026 | Portal oficial NF-e/SVRS | Confirmou que a referencia operacional atual deve continuar fora da NT 2025.002 v1.35 historica | `llms.txt`, `assets/llm-manifest.json`, `assets/portal-search.js`, `assets/portal-search-full.json` | ambos | OK |
| https://www.gov.br/receitafederal/pt-br/assuntos/noticias/2026/junho/receita-federal-e-cgibs-publicaram-hoje-a-documentacao-tecnica-da-plataforma-publica-do-split-payment | 03/06/2026 | Manual + Swagger da Plataforma Publica do Split Payment | Confirmou a data publica usada no eixo de reforma e manteve o tema como tecnico, sem efeito automatico de carga tributaria | `federal/legislacao/atos/ato-conjunto-rfb-cgibs-2-2026-split-payment.html`, relatorio de monitoramento | ambos | OK |
| https://normas.receita.fazenda.gov.br/sijut2consulta/consulta.action?anoAtoFacet=&ano_ato=&dt_fim=&dt_inicio=&facetsExistentes=&lblTiposAtosSelecionados=&numero_ato=&optOrdem=Publicacao_DESC&ordemColuna=&ordemDirecao=&orgaosSelecionados=RFB%3B+RFB&siglaOrgaoFacet=&termoBusca=&tipoAtoFacet=&tipoConsulta=formulario&tipoData=2&tiposAtosSelecionados= | 09/06/2026 a 11/06/2026 | Portaria RFB 695/2026, IN RFB 2.327/2026, Portarias 693/2026 e 690/2026, ADE RFB 3/2026 | Confirmou que os atos seguem pendentes de captura integral antes de virar pagina normativa profunda | relatorio de monitoramento; backlog federal | ambos | A VALIDAR |
| https://www.cgibs.gov.br/regulamentos | 30/04/2026 | Resolucao CGIBS 6/2026 e Portaria Conjunta MF/CGIBS 7/2026 | Confirmou vigencia das referencias centrais da reforma ja usadas no portal | `federal/legislacao/reforma-tributaria/*`, `docs/master-audit.md` | ambos | OK |
| fontes locais curadas + build interno | 14/06/2026 | Matriz de beneficios reextraida com filtros de ruído em `scripts/validated_benefits.py` | Reduziu a publicacao de entradas validadas de 12.246 para 11.951 e elevou linhas NCM de 7.976 para 9.111 apos reprocessamento e deduplicacao atual | `data/benefits_crosswalk.json`, `data/ncm_benefits_index.json`, `data/ncm_benefits_index.csv`, `docs/master-audit.md` | ambos | CORRIGIR |

### Correcao aplicada nesta rodada complementar

- `scripts/validated_benefits.py`: passou a rejeitar parte dos trechos espurios de transporte/CFOP/NFCom e a limpar marcadores vazios simples ao compactar excertos.
- `scripts/build_portal.py`: passou a serializar listas de busca sem `str(list)` bruto, preparando limpeza de `data-search` e dos indices LLM na proxima reconstrucao integral estavel.
- `python scripts/build_master_indexes.py`: reexecutado com sucesso; arquivos `data/master_taxonomy.json`, `data/master_source_coverage.json`, `data/benefits_crosswalk.json`, `data/confaz_ultimos_5_anos.json` e `docs/master-audit.md` ficaram com `generated_on` em `2026-06-14`.
- `python scripts/build_ncm_benefits_index.py`: reexecutado com sucesso; `data/ncm_benefits_index.json` e CSV regenerados com `9.111` linhas.
- `python scripts/build_portal.py`: houve uma execucao completa bem-sucedida apos a reextracao dos dados; auditoria estrutural voltou a passar em `651` paginas HTML.

### Segunda revisao independente

#### Revisao humana integral

- Navegacao, indices principais, `llms.txt`, `llm-manifest`, `portal-search` e `sitemap` ficaram estruturalmente coerentes segundo `audit_portal.py`.
- As paginas de beneficios continuam semanticamente pesadas para leitura humana por acumularem historico normativo, notas de vigencia antigas e `data-search` muito extenso.
- O problema de mojibake permanece visivel em trechos do HTML bruto de varias paginas de beneficios e alguns materiais federais/estaduais. Isso ainda afeta experiencia de leitura e revisao manual.

#### Revisao IA/LLM integral

- A data `generated_on` dos indices mestres e NCM foi atualizada para `2026-06-14`, reduzindo risco de stale metadata.
- O risco de aplicar a NT 2025.002 v1.35 como regra atual continua mitigado.
- Persistem residuos textuais como marcadores de listas vazias, listas serializadas e blocos historicos extensos em `data-search` de cards de beneficios; a limpeza de serializacao foi codificada, mas nao propagou integralmente para todas as paginas geradas dentro do tempo local disponivel.
- Conclusao IA: a recuperacao melhorou nos indices mestres, mas ainda ha ruído material em beneficios tematicos; qualquer uso automatizado deve tratar `beneficios/*.html` como corpus de apoio, nao como resposta pronta sem conferencia no dispositivo legal.

### Validacoes complementares executadas

- `python -m compileall -q scripts`: sem erro.
- `python scripts/audit_master_coverage.py`: sem falhas estruturais; 15 requisitos federais, 27 Estados, 11.951 beneficios, 9.111 linhas NCM e 3 familias CONFAZ auditadas.
- `python scripts/audit_portal.py`: 651 paginas HTML auditadas, sem falhas, apos reconstruir o portal com os JSONs atualizados.
- `gh auth status`: autenticacao GitHub disponivel no ambiente local.

### Pendencias humanas

- Ler integralmente e capturar os textos oficiais de IN RFB 2.327/2026, Portarias RFB 695/2026, 693/2026 e 690/2026, alem do ADE RFB 3/2026 com anexos.
- Classificar materialmente os Convenios ICMS 57/26 a 62/26 antes de publicar leitura tributaria de merito.
- Decidir se a rodada deve abrir PR mesmo com ruido residual em `beneficios/*.html`.

### Pendencias IA

- Propagar a limpeza de serializacao do `data-search` para todas as paginas de beneficios em execucao integral estavel de `build_portal.py`, com tempo maior ou CI.
- Refinar o gerador para separar, nos cards e chunks, `vigente`, `historico` e `nao aplicar sem validacao`, evitando mistura de texto operacional antigo com regra atual.
- Criar auditoria especifica para detectar marcadores de listas vazias, blocos `===== PAGINA =====`, residuos de OCR e trechos de documento fiscal que nao deveriam virar card de beneficio.

## Rodada especifica de saneamento de beneficios - 14/06/2026

### Objetivo

Atender a revisao humana que apontou que os cards de beneficios estavam misturando beneficio material, historico normativo, listas serializadas e ruido IA/editorial. O foco desta rodada foi impedir que paginas tematicas, especialmente `beneficios/cesta-basica.html`, publiquem card por associacao textual fraca, como combustiveis ou energia aparecendo em recorte de cesta/alimentos.

### Achados saneados

| URL oficial | Data | Ato/objeto | Impacto | Arquivo afetado | Publico afetado | Status |
| --- | --- | --- | --- | --- | --- | --- |
| URLs oficiais preservadas individualmente em `data/benefits_crosswalk.json` e `data/benefits_quarantine.json` | 14/06/2026 | Fontes estaduais/federais locais ja capturadas de origem oficial | Registros sem escopo operacional claro deixaram de ser publicados e foram enviados para quarentena editorial rastreavel | `scripts/validated_benefits.py`, `data/benefits_crosswalk.json`, `data/benefits_quarantine.json` | ambos | CORRIGIDO |
| URLs oficiais preservadas individualmente nos registros NCM | 14/06/2026 | NCM/TIPI, cBenef, CST e cClassTrib extraidos de texto legal | Indice NCM passou a carregar `scope_summary`, `goods_or_services`, `validity_status` e `classification_confidence` | `scripts/build_ncm_benefits_index.py`, `data/ncm_benefits_index.json`, `data/ncm_benefits_index.csv` | IA | CORRIGIDO |
| Portal publico local gerado a partir de fontes oficiais registradas | 14/06/2026 | Cards de beneficios e paginas tematicas | Cards passaram a exibir `Escopo publicado`, mercadoria/operacao, vigencia/status e confianca; `data-search` deixou de serializar lista bruta | `scripts/build_portal.py`, `beneficios/*.html`, `assets/portal-search*.json/js` | ambos | CORRIGIDO |
| Portal publico local gerado a partir de fontes oficiais registradas | 14/06/2026 | Pagina `beneficios/cesta-basica.html` | Recorte de cesta/alimentos passou a exigir termo alimentar/agro publico e vetar energia, combustiveis, biodiesel, diesel, gas natural, etanol, PCH, solar/fotovoltaica e similares | `beneficios/cesta-basica.html`, `scripts/build_portal.py` | humano | CORRIGIDO |
| Portal publico local gerado a partir de fontes oficiais registradas | 14/06/2026 | Auditoria de regressao dos cards | Criada auditoria propria contra `[] []`, lista serializada, marcador de pagina, baixa confianca publicada, quarentena misturada na matriz publica e combustiveis em cesta basica | `scripts/audit_benefit_cards.py` | ambos | OK |

### Mudancas aplicadas

- `scripts/validated_benefits.py`: adicionados saneamento de excertos, remocao de marcadores de pagina, classificacao por escopo publicado, campos `scope_summary`, `goods_or_services`, `validity_status`, `classification_confidence`, `audience_status` e `publishable`.
- `scripts/validated_benefits.py`: itens com escopo baixo, obrigacao documental, indice/sumario de anexo ou baixa confianca passam para quarentena em vez de matriz publica.
- `scripts/build_master_indexes.py`: passou a gerar `data/benefits_quarantine.json` separado da matriz publica.
- `scripts/build_portal.py`: cards de beneficios passaram a renderizar escopo e vigencia/status; busca estruturada passou por limpeza de listas e marcadores; pagina de cesta basica recebeu filtro tematico conservador.
- `scripts/build_ncm_benefits_index.py`: indice NCM x beneficios passou a receber campos de escopo e confianca.
- `scripts/audit_benefit_cards.py`: nova auditoria especifica de cards e indices LLM.

### Resultado quantitativo

- `data/benefits_crosswalk.json`: `9.727` registros publicos validados, com `5.345` de confianca alta e `4.382` de confianca media.
- `data/benefits_quarantine.json`: `13.137` registros em quarentena editorial, status `a_validar`, com motivo rastreavel.
- `data/ncm_benefits_index.json`: `7.050` linhas NCM x beneficios, `1.441` NCM unicos e `15` jurisdicoes/origens.
- `beneficios/cesta-basica.html`: `545` cards apos filtro conservador; busca por `diesel`, `gas natural`, `combustivel`, `energia`, `querosene`, `biodiesel`, `etanol`, `AEHC`, `fotovoltaica`, `hidreletrica`, `PCH` e `metanol` sem ocorrencias.

### Validacoes finais desta rodada especifica

- `python -m compileall -q scripts`: sem erro.
- `python scripts/audit_benefit_cards.py`: sem falhas.
- `python scripts/audit_master_coverage.py`: sem falhas estruturais; 15 requisitos federais, 27 Estados, 9.727 beneficios, 7.050 linhas NCM e 3 familias CONFAZ auditadas.
- `python scripts/audit_portal.py`: 651 paginas HTML auditadas, sem falhas.
- `rg` para `[] []`, listas serializadas, `===== PAGINA`, `PAGINA [0-9]`, `PÃ.?GINA` e caractere de substituicao em beneficios, busca integral e dados principais: sem ocorrencias.
- `rg` de combustiveis/energia em `beneficios/cesta-basica.html`: sem ocorrencias.
- `git diff --check`: sem erros; apenas avisos esperados de normalizacao LF/CRLF no ambiente Windows.

### Revisao humana integral

- A pagina de cesta basica deixou de exibir cards de combustiveis/energia no recorte alimentar.
- Os cards agora indicam explicitamente o escopo publicado, em vez de depender de grupo/tema inferido.
- Permanece ressalva humana: ainda ha cards com escopo juridico longo e alguns recortes amplos de produtor rural/agro que precisam de refinamento didatico manual para ficarem agradaveis de ler, embora ja nao estejam no mesmo nivel de ruido anterior.

### Revisao IA/LLM integral

- `assets/portal-search-full.json` e `data-search` deixaram de carregar listas serializadas e marcadores de pagina detectaveis pelos padroes auditados.
- A matriz publica ficou separada da quarentena, evitando que uma IA recupere como validado um trecho apenas extraido.
- Permanece ressalva IA: a classificacao automatica ainda usa heuristica de media/alta confianca; qualquer resposta fiscal continua obrigada a citar `official_url`, `legal_basis`, `scope_summary`, `validity_status` e conferir o trecho legal antes de aplicar regra.

### Pendencias remanescentes

- Fazer uma rodada de leitura humana fina dos 545 cards restantes de `beneficios/cesta-basica.html` para reduzir tamanho e melhorar explicacao didatica por mercadoria.
- Decidir se a pagina de cesta basica deve ser desmembrada em `cesta-basica`, `agro-produtor-rural` e `insumos-agropecuarios`, porque o tema atual ainda mistura cesta alimentar e cadeia agro.
- Abrir PR somente apos revisao do diff gerado, pois a regeneracao completa alterou muitos HTMLs e indices derivados.
