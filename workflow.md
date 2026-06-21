# Workflow - Secao PIS/Cofins por NCM

Data de abertura: 2026-06-21

## P0 - Enquadramento executavel

Objetivo: construir uma secao dedicada do portal para PIS/Pasep e Cofins por NCM, produto, setor e aplicacao, com foco em tratamentos diferentes da regra habitual:

- monofasico/incidencia concentrada;
- aliquota zero;
- suspensao;
- isencao/nao incidencia quando vinculada a produto, NCM, aplicacao, destinatario ou habilitacao;
- importacao com tratamento especifico;
- regimes setoriais e excecoes que alterem a leitura operacional por item.

Entregaveis esperados:

- banco profundo em `G:\Meu Drive\RJC\BD_LEGISLACAO\PIS_COFINS_NCM`;
- inventario oficial de fontes, com URL, HTTP, data de captura, hash bruto e hash normalizado;
- `data/pis-cofins/ncm.ndjson` com registros publicaveis;
- `data/pis-cofins/quarentena.ndjson` local/ignorado pelo Git, com candidatos nao publicaveis;
- pagina executiva `federal/pis-cofins-ncm.html`;
- tabela pesquisavel `federal/legislacao/pis-cofins/ncm.html`;
- busca/LLM atualizados para descobrir a nova secao e seus registros;
- auditorias especificas para bloquear fonte ausente, vigencia ausente, escopo inferido e vazamento de quarentena;
- ledger da rodada em `docs/monitoramento/monitoramento-legislativo-2026-06-21.md` quando houver conteudo publicavel.

Regra mestre: nenhuma linha publica pode afirmar tratamento de PIS/Cofins sem fonte oficial primaria resolvivel, trecho legal, vigencia/eficacia/fim, condicoes, status, `verificado_em` e relacao com CBS/transicao.

## Subagentes

| Agente | Frente | Status | Produto esperado |
|---|---|---|---|
| Curie | Arquitetura do portal | concluido como insumo | mapa de build, busca, llms, manifest, paginas e gates |
| Cicero | Inventario oficial PIS/Cofins | concluido como insumo | tabela de fontes oficiais, URLs, artigos/anexos e riscos |
| Fermat | Schema/auditoria | concluido como insumo | contrato NDJSON, auditorias minimas e testes adversariais |

Observacao: subagentes nao substituem prova. O resultado deles entra como insumo; publicacao depende de testes e evidencia local.

## P1 - Criterios de pronto falsificaveis

| # | Criterio | Metodo mais forte | Status | Evidencia |
|---|---|---|---|---|
| 1 | `workflow.md` detalha subtarefas, revisoes, gates e regra de parada | leitura direta + diff | OK | este arquivo |
| 2 | Fontes oficiais nucleares foram inventariadas com URL e HTTP | crawler/fetch + hash | OK COM RESSALVA | 14 fontes HTTP 200 em `G:\Meu Drive\RJC\BD_LEGISLACAO\PIS_COFINS_NCM\inventario-fontes.ndjson`; completude ampliada segue A VALIDAR |
| 3 | Cada fonte bruta capturada no `G:` tem hash bruto e normalizado | script + comparacao de hash | OK | `fontes-brutas/`, `fontes-normalizadas/`, `raw_sha256`, `normalized_sha256` |
| 4 | Registro publicavel contem fonte primaria, trecho, vigencia, condicoes, status e `verificado_em` | auditoria automatizada | OK | `python scripts\audit_pis_cofins_ncm.py` |
| 5 | Nenhum registro keyword-only ou `classification_confidence < 0.80` e publicavel | auditoria automatizada | OK | `audit_pis_cofins_ncm.py` + `audit_pis_cofins_ncm_adversarial.py` |
| 6 | Quarentena nao aparece em HTML, busca, sitemap, llms ou manifest | auditoria automatizada | OK | `audit_quarantine_isolation.py` verificou 13137 ids; auditoria PIS/Cofins isolou 183 candidatos |
| 7 | Consulta publica e pesquisavel por NCM, descricao, setor, tratamento, fonte e status, com cards antes da tabela tecnica | build + busca local + render Chrome | OK | `federal/legislacao/pis-cofins/ncm.html`; 291 ids presentes no HTML; `#pisNcmSearch` filtra cards |
| 8 | HTML, NDJSON e busca convergem por id | auditoria automatizada | OK | prova direta: 291 ids, 0 ausentes no HTML, 0 ausentes no `portal-search-full.json` |
| 9 | LLM consegue ler cada registro com envelope completo de validade | manifest/search + inspecao adversarial | OK | `llms.txt`, manifest e busca incluem pagina, NDJSON e indice |
| 10 | Hard gates canonicos do portal ficam verdes | bateria oficial | OK COM AVISOS SOFT | gates verdes; `audit_link_health.py` trouxe avisos de SSL/conexao sem 404/410 em beneficio publicado |
| 11 | Passe adversarial gera teste executavel e nao encontra defeito novo | teste dedicado | OK | `python scripts\audit_pis_cofins_ncm_adversarial.py` => 11 casos adversariais OK |
| 12 | Conteudo so sobe via PR e Pages HTTP publico | PR + Actions + HTTP 200 | OK | PR #12 mergeado; commit `68ac619`; Pages run `27914470566`; verificacao publica HTTP 200 |
| 13 | Portal humano traz busca local por NCM, descricao, setor, tratamento, fonte e status | auditoria automatizada + HTML gerado | OK | `python scripts\audit_pis_cofins_ncm_ui.py` => 291 cards, 291 linhas e 291 entradas de busca/LLM |
| 14 | NDJSON servido para LLM inclui resumo operacional, texto pesquisavel e salvaguardas de leitura | auditoria automatizada | OK | `python scripts\audit_pis_cofins_ncm.py`; campos `resumo_operacional`, `pesquisa_texto`, `leitura_humana` obrigatorios |
| 15 | Excel local pesquisavel foi gerado e bate com a base publica | exportacao + auditoria da planilha | OK | `python scripts\export_pis_cofins_ncm_excel.py`; `python scripts\audit_pis_cofins_ncm_excel.py` |
| 16 | A tabela larga nao domina a leitura humana do portal | auditoria UI + render Chrome local | OK | `audit_pis_cofins_ncm_ui.py` bloqueia tabela antes da busca/cards, tabela aberta por padrao e texto antigo; Chrome local mostrou tabela tecnica fechada e busca `3004` com 43 cards |

## Decomposicao das subtarefas

### Fase A - Inventario e captura oficial

1. Criar `scripts/build_pis_cofins_ncm.py`.
2. Definir lista inicial oficial em codigo, com Planalto, RFB/SIJUT, DOU/gov.br e fontes de TIPI/NCM.
3. Baixar cada fonte oficial para `G:\Meu Drive\RJC\BD_LEGISLACAO\PIS_COFINS_NCM\fontes-brutas`.
4. Normalizar texto em `fontes-normalizadas`.
5. Gerar `inventario-fontes.ndjson` com URL, HTTP, data, hash bruto, hash normalizado, ato, tipo, papel da fonte e status.
6. Registrar falhas de HTTP como `A VALIDAR` e nunca como publicavel.

### Fase B - Extracao e quarentena

1. Extrair candidatos por termos: `NCM`, `TIPI`, `aliquota zero`, `aliquota 0`, `monofasico`, `suspensao`, `isencao`, `PIS`, `Cofins`.
2. Extrair por artigo/anexo, mesmo quando a palavra NCM nao aparece na janela imediata.
3. Separar `extracoes-candidatas.ndjson`.
4. Classificar cada candidato por tratamento, setor, etapa da cadeia, mercado interno/importacao e fonte dispositiva.
5. Enviar para quarentena quando houver link sem HTTP 200, escopo por inferencia, vigencia ausente, fonte apenas interpretativa, ou confianca baixa.

### Fase C - Base publicavel

1. Gerar `data/pis-cofins/ncm.ndjson` somente com registros completos.
2. Cada registro deve conter `validity_status`, `ato`, `vigencia`, `status`, `publishable`, `verificado_em`, `transicao_cbs`, `provenance` e `classification_confidence`.
3. Gerar `data/pis-cofins/quarentena.ndjson` local/nao indexado e ignorado pelo Git para nao virar artefato publico do Pages.
4. Gerar resumo de cobertura por fonte, NCM, tratamento, setor e lacuna.

### Fase D - Site humano

1. Criar pagina executiva `federal/pis-cofins-ncm.html`.
2. Criar tabela `federal/legislacao/pis-cofins/ncm.html`.
3. Exibir filtros e campos visiveis: NCM, descricao, setor, aplicacao, tratamento, tributo, ato, publicacao, vigencia, eficacia, fim, condicao, prova, transicao CBS, risco, status e verificado em.
4. Incluir aviso claro de escopo: aplicar somente registros `vigente` com prova completa.
5. Linkar a partir da pagina PIS/Cofins e do hub federal.

### Fase E - LLM e busca

1. Incluir registros publicaveis em `assets/portal-search-full.json`.
2. Incluir a nova pagina e dados em `llms.txt`.
3. Incluir a nova pagina em `assets/llm-manifest.json`.
4. Garantir que nenhum registro de quarentena aparece em indices publicos.
5. Garantir que cada entrada de busca carregue status, ato e vigencia no corpo.

### Fase F - Auditorias e passe adversarial

1. Criar auditoria de schema PIS/Cofins NCM.
2. Criar auditoria de links/fonte primaria para `data/pis-cofins/ncm.ndjson`.
3. Criar auditoria de isolamento de quarentena.
4. Criar auditoria de divergencia HTML x NDJSON x busca.
5. Criar teste adversarial que injeta ou procura casos ruins: keyword-only, fonte interpretativa, vigencia ausente, link quebrado, status futuro marcado vigente e vazamento de quarentena.

## Fontes oficiais iniciais obrigatorias

| Fonte | Papel | Status |
|---|---|---|
| Lei 10.147/2000 | dispositiva, monofasico/produtos especificos | HTTP 200 testado; extracao pendente |
| Lei 10.485/2002 | dispositiva, automotivo/autopecas | HTTP 200 testado; extracao pendente |
| Lei 10.637/2002 | dispositiva, PIS nao cumulativo e referencias cruzadas | HTTP 200 testado; extracao pendente |
| Lei 10.833/2003 | dispositiva, Cofins nao cumulativa e referencias cruzadas | HTTP 200 testado; extracao pendente |
| Lei 10.865/2004 | dispositiva, PIS/Cofins-Importacao e aliquota zero | HTTP 200 testado; extracao pendente |
| Lei 10.925/2004 | dispositiva, insumos/produtos agropecuarios e alimentos | HTTP 200 testado; extracao pendente |
| Lei 12.839/2013 | dispositiva/alteradora, azeites e itens especificos | HTTP 200 testado; extracao pendente |
| Lei 13.097/2015 | dispositiva/alteradora, aliquota zero e regimes especificos | HTTP 200 testado; extracao pendente |
| Lei 15.394/2026 | dispositiva, residuos e aparas | HTTP 200 testado; extracao pendente |
| Decreto 5.195/2004 | regulamentar, Lei 10.925 | HTTP 200 testado; extracao pendente |
| Decreto 5.630/2005 | regulamentar, Lei 10.925 | HTTP 200 testado; extracao pendente |
| Decreto 6.426/2008 | regulamentar, anexos NCM quimicos/farmaceuticos | HTTP 200 testado; extracao pendente |
| Decreto 6.707/2008 | regulamentar, bebidas | HTTP 200 testado; extracao pendente |
| Decreto 8.442/2015 | regulamentar/revogador, bebidas | HTTP 200 testado; extracao pendente |
| Decreto 12.991/2026 | regulamentar, combustiveis/querosene/biodiesel | HTTP 200 testado; extracao pendente |
| IN RFB 2.121/2022 | consolidacao infralegal; nao substitui lei | HTTP 200 testado; extracao pendente |
| Portaria RFB 319/2023 + 688/2026 | inventario/transparencia de beneficios | HTTP 200 testado; extracao pendente |
| IN RFB 2.198/2024 e alteracoes | DIRBI/inventario de beneficios | A VALIDAR |
| TIPI/NCM oficial | valida codigo/descricao; nao prova beneficio | A VALIDAR |

## Ledger de execucao

| Data/hora | Acao | Resultado | Proxima acao |
|---|---|---|---|
| 2026-06-21 | Criado workflow detalhado | OK | implementar captura/extracao |
| 2026-06-21 | Criados scripts `build_pis_cofins_ncm.py`, `audit_pis_cofins_ncm.py` e `audit_pis_cofins_ncm_adversarial.py` | OK | integrar ao portal |
| 2026-06-21 | Gerada base profunda em `G:\Meu Drive\RJC\BD_LEGISLACAO\PIS_COFINS_NCM` | OK | registrar ledger |
| 2026-06-21 | Gerados `data/pis-cofins/ncm.ndjson`, `quarentena.ndjson` e `ncm-index.json` | OK: 291 publicaveis, 183 quarentena, 140 NCM/codigos unicos | ampliar inventario |
| 2026-06-21 | Integradas paginas `federal/pis-cofins-ncm.html` e `federal/legislacao/pis-cofins/ncm.html` ao build, busca, manifest, sitemap, llms e freshness | OK | abrir PR |
| 2026-06-21 | Build normal do portal | OK: `python scripts\build_portal.py` => `Portal generated successfully.` em ~399s | publicar via PR |
| 2026-06-21 | Gates e passe adversarial | OK com avisos soft de link health | PR + verificacao Pages |
| 2026-06-21 | Revisao UX solicitada apos publicacao inicial | CORRIGIR aplicado: tabela tecnica deixou de ser a primeira leitura; criada consulta guiada por NCM/tratamento/setor/fonte/status | publicar nova revisao via PR |
| 2026-06-21 | Artefatos LLM enriquecidos | OK: NDJSON e busca carregam resumo operacional, texto pesquisavel, como validar e nao usar sem | revalidar gates |
| 2026-06-21 | Excel local gerado | OK: `G:\Meu Drive\RJC\BD_LEGISLACAO\PIS_COFINS_NCM\pis-cofins-ncm-2026-06-21.xlsx` auditado com 291 linhas | manter fora do Pages |
| 2026-06-21 | Revisao UX/LLM publicada | OK: PR #12 mergeado, Pages run `27914470566`, HTTP publico conferido | fechamento com ressalva de completude |
| 2026-06-21 | Revisao UX pos-print aplicada e publicada | OK: PR #14 mergeado em `7132fa6`; Pages run `27915401092`; HTTP publico conferido com 291 cards, busca presente e tabela tecnica fechada | manter monitoramento |

## Passe adversarial vivo

Pergunta de controle: O resumo esta bonito, mas qual detalhe interno poderia derrubar essa conclusao?

Resposta atual: o maior risco e omitir regra setorial por descricao/finalidade que nao usa a palavra NCM. Evidencia necessaria: inventario oficial com crawler e extracao por artigo/anexo, nao apenas busca textual.

Status apos execucao de 2026-06-21: esse risco permanece como ressalva de completude. A secao publicada localmente nao afirma cobertura exaustiva da legislacao inteira; afirma apenas registros validados no lote inicial de 14 fontes oficiais HTTP 200. A proxima revisao deve ampliar o crawler para IN RFB 2.121/2022 completa, tabelas EFD-Contribuicoes 4.3.10 a 4.3.17, TIPI/NCM oficial, DIRBI/transparencia RFB e demais leis setoriais listadas no plano.

## Regra de parada

Esta tarefa so fecha quando:

- um passe adversarial completo nao revelar defeito novo;
- todos os criterios de pronto estiverem `OK` com evidencia;
- hard gates canonicos e auditorias PIS/Cofins NCM passarem;
- quarentena estiver isolada;
- a secao estiver publicada via PR e verificada por HTTP publico.

Enquanto qualquer criterio estiver `A VALIDAR`, a entrega pode ser considerada progresso executado, mas nao conclusao plena.
