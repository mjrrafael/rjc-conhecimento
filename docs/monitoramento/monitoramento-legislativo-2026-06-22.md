# Monitoramento legislativo - 2026-06-22

## Escopo

Rodada dedicada a verificar a janela desde o ledger de 2026-06-21, validar se havia ato oficial novo com impacto imediato no portal e fechar um defeito de hard gate no `audit_index_freshness.py` em ambiente Windows com `core.autocrlf=true`.

Status literal da rodada: `CONCLUIDO COM RESSALVA`.

Ressalva: nao houve nova publicacao de conteudo nesta rodada; a entrega fecha localmente com todos os hard gates verdes, mas permanece com avisos soft de disponibilidade/SSL em algumas fontes oficiais ja conhecidas e sem PR aberto nesta execucao.

## Criterios de pronto da rodada

| # | Criterio de pronto | Metodo | Status | Evidencia |
| --- | --- | --- | --- | --- |
| 1 | Confirmar se houve ato oficial novo com impacto editorial imediato desde 2026-06-21 | confronto com fonte primaria oficial | OK | consultas oficiais em CONFAZ, RFB, CGIBS, Planalto e Portal Gov.br |
| 2 | Reproduzir o defeito do gate e isolar causa concreta | teste executavel local + recalc de hash | OK | `python scripts/audit_index_freshness.py` inicialmente falhou; hashes canonicos vs bytes crus comparados |
| 3 | Corrigir o gate sem relaxar o contrato editorial | patch + reexecucao da bateria canonica | OK | ajustes em `scripts/audit_v2_helpers.py`, `scripts/audit_index_freshness.py` e `scripts/build_portal.py` |
| 4 | Fechar a rodada com hard gates verdes | testes automatizados | OK | bateria completa local executada em 2026-06-22 com todos os hard gates saindo `0` |

## Fontes conferidas

| Fonte | URL oficial | HTTP/resultado | Ultima norma vista | Data observada | Impacto |
| --- | --- | --- | --- | --- | --- |
| CONFAZ - home | https://www.confaz.fazenda.gov.br/ | acessivel | `DESPACHO Nº 26, DE 16 DE JUNHO DE 2026`; `ATO COTEPE/ICMS Nº 61/62/63, DE 16 DE JUNHO DE 2026` | 2026-06-22 | nenhum ato novo posterior a 2026-06-21 identificado na vitrine publica |
| RFB - Normas (ordenacao por publicacao desc) | https://normas.receita.fazenda.gov.br/sijut2consulta/consulta.action?anoAtoFacet=&ano_ato=&dt_fim=&dt_inicio=&facetsExistentes=&lblTiposAtosSelecionados=&numero_ato=&optOrdem=Publicacao_DESC&ordemColuna=&ordemDirecao=&orgaosSelecionados=RFB%3B+RFB&siglaOrgaoFacet=&termoBusca=&tipoAtoFacet=&tipoConsulta=formulario&tipoData=2&tiposAtosSelecionados= | acessivel | ato mais recente visivel: alteracao publicada em `18/06/2026`; depois disso, na consulta aberta hoje, nao apareceu ato tributario novo posterior a 2026-06-21 | 2026-06-22 | nenhum impacto editorial imediato confirmado |
| CGIBS - resolucoes | https://www.cgibs.gov.br/resolucoes | acessivel | `RESOLUCAO CGIBS Nº 9, DE 10 DE JUNHO DE 2026` | 2026-06-22 | sem ato novo posterior a 2026-06-21 na listagem consultada |
| Receita Federal - orientacoes RTC 2026 | https://www.gov.br/receitafederal/pt-br/acesso-a-informacao/acoes-e-programas/programas-e-atividades/reforma-tributaria-do-consumo/orientacoes-2026 | acessivel | pagina institucional continua atualizada em `06/05/2026` | 2026-06-22 | sem mudanca normativa nova para capturar |
| Receita Federal - agenda tributaria 22/06/2026 | https://www.gov.br/receitafederal/pt-br/assuntos/agenda-tributaria/2026/junho/dia-22-06-2026 | acessivel | agenda operacional de `22/06/2026` | 2026-06-22 | util como referencia operacional; sem alteracao normativa material para cards |
| Planalto - busca dirigida | https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2026/decreto/d12955.htm | acessivel | `Decreto nº 12.955, de 29 de abril de 2026` continuou como marco principal encontrado para CBS | 2026-06-22 | sem novo decreto tributario material identificado na janela curta desta rodada |

## Achados

| URL/objeto | Data | Ato/objeto | Impacto | Arquivo afetado | Publico | Provenance | Confianca | Status |
| --- | --- | --- | --- | --- | --- | --- | ---: | --- |
| workspace local | 2026-06-22 | `audit_index_freshness.py` | hard gate falhava localmente mesmo sem divergencia semantica entre artefatos e `HEAD` | `scripts/audit_index_freshness.py` | ambos | teste local executavel | 0.99 | CORRIGIR |
| workspace local | 2026-06-22 | `core.autocrlf=true` + arquivos textuais com `CRLF` no worktree | causa raiz: comparacao de checksum em bytes crus, sensivel a newline de checkout Windows | `scripts/audit_v2_helpers.py`, `scripts/build_portal.py`, `assets/build-freshness.json` | ambos | recalc independente de hash bruto x hash canonico | 0.99 | CORRIGIR |
| https://www.confaz.fazenda.gov.br/ | 2026-06-22 | CONFAZ continuou exibindo como mais recentes atos de `16/06/2026` e `11/06/2026` | sem novo ato posterior ao ledger de 2026-06-21 na vitrine consultada | sem alteracao de conteudo | ambos | fonte primaria oficial | 0.95 | OK |
| https://normas.receita.fazenda.gov.br/sijut2consulta/consulta.action?anoAtoFacet=&ano_ato=&dt_fim=&dt_inicio=&facetsExistentes=&lblTiposAtosSelecionados=&numero_ato=&optOrdem=Publicacao_DESC&ordemColuna=&ordemDirecao=&orgaosSelecionados=RFB%3B+RFB&siglaOrgaoFacet=&termoBusca=&tipoAtoFacet=&tipoConsulta=formulario&tipoData=2&tiposAtosSelecionados= | 2026-06-22 | consulta de normas RFB | ultimo item recente visto permaneceu em `18/06/2026`; nao emergiu ato novo material posterior a 2026-06-21 na consulta aberta | sem alteracao de conteudo | ambos | fonte primaria oficial | 0.90 | OK |

## Mudancas aplicadas com prova

| Id/objeto | Campo alterado | De | Para | Prova | `verificado_em` |
| --- | --- | --- | --- | --- | --- |
| `scripts/audit_v2_helpers.py` | funcao de hash | inexistente | `canonical_sha256()` com normalizacao `CRLF -> LF` para artefatos textuais | patch local + reexecucao do gate | 2026-06-22 |
| `scripts/audit_index_freshness.py` | comparacao de checksum | `sha256()` em bytes crus | uso de `canonical_sha256()` | patch local + gate verde | 2026-06-22 |
| `scripts/build_portal.py` | geracao de `assets/build-freshness.json` | hash sensivel a newline do worktree | hash canonico para artefatos textuais | patch local + regeneracao isolada de `assets/build-freshness.json` | 2026-06-22 |
| `assets/build-freshness.json` | checksums registrados | mix anterior sensivel a bytes crus | checksums canonicos coerentes com gate novo | `write_build_freshness()` rerodado isoladamente | 2026-06-22 |

## Quarentena

Nenhuma alteracao de quarentena nesta rodada.

## Gates

### Primeiro passe adversarial

| Gate | Resultado | Evidencia |
| --- | --- | --- |
| `python -m compileall -q scripts` | OK | exit `0` |
| `python scripts/audit_portal.py` | OK | `Paginas HTML auditadas: 654` |
| `python scripts/audit_master_coverage.py` | OK | `Requisitos federais auditados: 15`; `Estados auditados: 27` |
| `python scripts/audit_benefit_cards.py` | OK | sem falhas |
| `python scripts/audit_card_scope_visible.py` | OK | contrato v2 visivel |
| `python scripts/audit_no_keyword_inference.py` | OK | sem keyword-only publico |
| `python scripts/audit_temporal_consistency.py` | OK | sem inconsistencias temporais |
| `python scripts/audit_link_health.py` | OK com avisos soft | 103 URLs unicas; nenhum `404/410` em beneficio publicado |
| `python scripts/audit_index_freshness.py` | FALHOU | divergencia de checksum em `llms.txt`, `assets/llm-manifest.json` e `assets/portal-search-full.json` |
| `python scripts/audit_quarantine_isolation.py` | OK | 13137 ids fora dos artefatos publicos |
| `python scripts/audit_reforma_transition.py` | OK | `transicao_rt` presente |
| `python scripts/audit_divergence_html_json_search.py` | OK | convergencia preservada |
| `python scripts/audit_editorial_date_per_card.py` | OK | data editorial derivada |
| `git diff --check` | OK | exit `0` |
| varredura final de data editorial antiga e ruidos de listas serializadas | OK | exit `1` por ausencia de matches |

### Passe apos correcao

| Gate | Resultado | Evidencia |
| --- | --- | --- |
| `python -m compileall -q scripts` | OK | exit `0` |
| `python scripts/audit_portal.py` | OK | `Paginas HTML auditadas: 654` |
| `python scripts/audit_master_coverage.py` | OK | `Requisitos federais auditados: 15`; `Estados auditados: 27`; `Entradas de beneficios auditadas: 9727`; `Linhas NCM x beneficios auditadas: 7050` |
| `python scripts/audit_benefit_cards.py` | OK | sem falhas |
| `python scripts/audit_card_scope_visible.py` | OK | contrato v2 visivel |
| `python scripts/audit_no_keyword_inference.py` | OK | sem keyword-only publico |
| `python scripts/audit_temporal_consistency.py` | OK | sem inconsistencias |
| `python scripts/audit_link_health.py` | OK com avisos soft | mesmos avisos transitivos/SSL; nenhum `404/410` em beneficio publicado |
| `python scripts/audit_index_freshness.py` | OK | `Indices e HTML aparentam ter sido regenerados no mesmo build.` |
| `python scripts/audit_quarantine_isolation.py` | OK | 13137 ids verificados |
| `python scripts/audit_reforma_transition.py` | OK | sem falhas |
| `python scripts/audit_divergence_html_json_search.py` | OK | sem falhas |
| `python scripts/audit_editorial_date_per_card.py` | OK | sem falhas |
| `git diff --check` | OK | exit `0` |
| varredura final de data editorial antiga e ruidos de listas serializadas | OK | exit `1` por ausencia de matches |

## Pendencias humanas

- Abrir PR para a correcao de portabilidade do hard gate, se a intencao for publicar o ajuste de script.
- Revalidar manualmente as fontes com erro de SSL/host no proximo ciclo, em especial BA, ES, RN, RS, RJ e CGIBS.

## Pendencias IA/LLM

- Nenhuma pendencia nova de conteudo/indice apos a correcao canonica de checksum.
- Manter observacao de que `audit_link_health.py` continua sujeito a falsos softs por SSL/host remoto, sem 404/410 em beneficio publicado nesta rodada.

## Passe adversarial

Revisao adversarial executada em dois ciclos.

Testes gerados/executados:

- bateria canonica completa de hard gates;
- recalc independente de hash bruto x hash canonico para `llms.txt`, `assets/llm-manifest.json`, `assets/portal-search-full.json` e `data/benefits_crosswalk.json`;
- confronto dos bytes do worktree com `git show HEAD:<arquivo>` para provar que a divergencia era de newline/checkout, nao de conteudo editorial.

Resultado:

- ciclo 1 derrubou a entrega com defeito novo e concreto no gate de frescor;
- causa raiz confirmada: comparacao em bytes crus sensivel a `CRLF` do Windows;
- ciclo 2, apos patch e regeneracao de `assets/build-freshness.json`, nao revelou defeito novo.

## Publicacao

Politica aplicavel: como a rodada alterou script de build/auditoria e nao conteudo editorial, a publicacao pode seguir fluxo tecnico, mas nesta execucao nenhum commit/PR foi aberto.

Status:

- patch local pronto;
- nenhum PR aberto;
- nenhuma validacao HTTP publica aplicavel nesta rodada, porque nao houve publicacao.

---

# Rodada adicional - integracao Cowork Produto/NCM (2026-06-22 21:30 BRT)

## Fontes e pacote conferidos

| Fonte/arquivo | Resultado | Evidencia |
| --- | --- | --- |
| `G:\...\#codex\BD_LEGISLACAO\Memoria_profunda\INGESTAO_PORTAL_TRIBUTARIO_2026-06-22.json` | OK | 384 entradas estaduais, 36 docs do projeto, snapshots Planalto |
| `portal_tributario_estado_atual_2026-06-22.md` | OK | LC 214/224/227 e arroz re-selados pelo pacote |
| `uf_sealing_plan_2026-06-22.md` | OK | corpus local = AMARELO; cBenef nao-GO = A_VALIDAR |
| `PROMPT-SOFIA-CODEX-v2.md` | OK | regras de integracao e regra #0 confirmadas |
| Planalto LC 214/2025 | HTTP 200 | `276ee6ba1da661057331ac8e6c059c6b73d53f62ab90bdbaed91345e1170fc91` snapshot; live hash gravado em `data/produtos-ncm/index.json` |
| Planalto LC 224/2025 | HTTP 200 | `450b76a97ba4cc40eb4f07263cadb145320dc0f539ad8526b3a8d711249c0611` snapshot; live hash gravado |
| Planalto LC 227/2026 | HTTP 200 | `0770059d59454ee81218d5ce0262a6bd45a0cd7e3a7bce6ea18556baa444e14c` snapshot; live hash gravado |
| Planalto Lei 10.925/2004 | HTTP 200 | `08abfce2984d16c3e5e95a995759dcb677c34576791dd2119940608f2c03c67d` snapshot; live hash gravado |

## Achados

| Objeto | Impacto | Status |
| --- | --- | --- |
| Produto arroz NCM 1006 | Seed importado com fontes Planalto e hashes; nao publicado como beneficio verde por faltar envelope temporal completo do card | A_VALIDAR |
| LC 224/2025 | Re-selo preserva que LC 224 nao institui IBS/CBS e que a mecanica dos 10% vem de seus dispositivos, com excecao da Cesta Basica Nacional | OK |
| LC 214/2025 | Re-selo preserva IBS/CBS/IS e arroz no art. 125 + Anexo I para 1006.20, 1006.30 e 1006.40.00 | OK com A_VALIDAR operacional |
| LC 227/2026 | Re-selo negativo: CGIBS/admin do IBS, nao fonte da mecanica dos 10% | OK |
| Corpus estadual | 384 entradas integradas como registro local amarelo, sem caminho absoluto e sem promocao para verde | OK |
| cBenef UFs | GO fica com snapshot local a revalidar; 26 UFs nao-GO ficam A_VALIDAR_SEFAZ_VIVA | OK |

## Mudancas aplicadas

| Arquivo/objeto | Mudanca |
| --- | --- |
| `scripts/import_cowork_portal_package.py` | importador reexecutavel do pacote Cowork/Bruno em `G:\...\#codex` |
| `data/produtos-ncm/index.json` e `data/produtos-ncm/cap-10.json` | schema `rjc-produto-ncm-v1` com seed arroz, fontes Planalto, snapshot/live sha e A_VALIDAR |
| `data/corpus-local/legal_sources_registry.json` | registry estadual local normalizado, sem paths absolutos, teto AMARELO_CORPUS_LOCAL |
| `data/corpus-local/uf-sealing-plan.json` | plano cBenef por UF com nao-GO em A_VALIDAR_SEFAZ_VIVA |
| `data/reforma-tributaria/reselo-lc214-lc224-lc227.ndjson` | re-selo federal LC 214/224/227 importado |
| `data/cowork/portal-package-manifest.json` | manifest dos documentos ingeridos do projeto Cowork |
| `produto.html` | nova consulta Produto/NCM com busca local, arroz 1006, hashes e bloqueios para verde |
| `scripts/build_portal.py` | Produto/NCM integrado a home, sitemap, manifest, busca integral, llms e build-freshness |
| `assets/portal-tributario.js` e CSS | filtro local e layout responsivo da consulta Produto/NCM |
| `scripts/audit_produtos_ncm.py` | gate especifico para Produto/NCM, corpus amarelo e cBenef A_VALIDAR |
| `scripts/audit_produtos_ncm_adversarial.py` | 11 mutacoes adversariais executaveis |
| `scripts/audit_index_freshness.py` | frescor tambem cobre Produto/NCM, corpus local e re-selo |

## Gates

| Gate | Resultado | Evidencia |
| --- | --- | --- |
| `python scripts/import_cowork_portal_package.py` | OK | 384 entradas; 4 Planalto HTTP 200 |
| `python scripts/build_portal.py` | OK | `Portal generated successfully.` |
| `python scripts/audit_produtos_ncm.py` | OK | Produto/NCM, re-selo, corpus amarelo e cBenef A_VALIDAR coerentes |
| `python scripts/audit_produtos_ncm_adversarial.py` | OK | 11 casos adversariais derrubados |
| `python -m compileall -q scripts` | OK | exit `0` |
| `python scripts/audit_portal.py` | OK | 655 paginas HTML auditadas |
| `python scripts/audit_master_coverage.py` | OK | 15 requisitos federais; 27 estados; 9727 beneficios; 7050 linhas NCM |
| `python scripts/audit_benefit_cards.py` | OK | sem falhas |
| `python scripts/audit_card_scope_visible.py` | OK | contrato v2 visivel |
| `python scripts/audit_no_keyword_inference.py` | OK | sem keyword-only publico |
| `python scripts/audit_temporal_consistency.py` | OK | envelopes temporais consistentes |
| `python scripts/audit_link_health.py` | OK com soft warnings | 103 URLs unicas; nenhum 404/410 em beneficio publicado |
| `python scripts/audit_index_freshness.py` | OK | indices e HTML regenerados no mesmo build |
| `python scripts/audit_quarantine_isolation.py` | OK | 13137 ids isolados |
| `python scripts/audit_reforma_transition.py` | OK | transicao_rt presente |
| `python scripts/audit_divergence_html_json_search.py` | OK | HTML, JSON e busca convergem |
| `python scripts/audit_editorial_date_per_card.py` | OK | data editorial derivada e verificado_em por card |
| `git diff --check` | OK | exit `0`; apenas avisos CRLF do Git |
| varredura final de datas antigas e ruidos serializados | OK | exit `1` sem matches |

## A_VALIDAR / pendencias

- Arroz PIS/Cofins e IBS/CBS esta visivel como seed de pesquisa, nao como beneficio publishable, ate extrair publicacao, vigencia, eficacia e fim em contrato completo.
- TIPI/NCM oficial da posicao 1006 ainda precisa ser capturada para elevar produto a verde operacional.
- CST/cClassTrib aplicavel ao arroz na Reforma Tributaria segue A_VALIDAR.
- cBenef das 26 UFs nao-GO permanece A_VALIDAR_SEFAZ_VIVA.
- GO cBenef tem snapshot local, mas ainda exige revalidacao das URLs SEFAZ antes de verde.
- Soft warnings de link health por SSL/timeout/host recusado seguem para rechecagem humana; nenhum 404/410 bloqueante.

## Publicacao

- Branch publicada: `feat/busca-ncm`.
- Commit: `018994c` (`feat: integra busca produto ncm cowork`).
- PR: https://github.com/mjrrafael/rjc-conhecimento/pull/16
- Politica aplicavel: conteudo/dados via PR; nada publicado direto em `main`.
- PR cita re-selo Planalto, hashes, Produto/NCM A_VALIDAR e pendencias SEFAZ/cBenef.

## Correcao pos-publicacao - sanitizacao de caminhos locais

- Achado adversarial: verificacao HTTP publica detectou `snapshot_path` absoluto do ambiente `G:\...` no NDJSON `data/reforma-tributaria/reselo-lc214-lc224-lc227.ndjson`.
- Impacto: vazamento de caminho local; nao alterava o status legal dos registros, mas violava higiene de publicacao de dados.
- Correcao aplicada: `scripts/import_cowork_portal_package.py` passou a converter `snapshot_path` em `snapshot_file` e a redigir `source_root` do manifesto como `#codex`.
- Gate novo: `scripts/audit_produtos_ncm.py` bloqueia drive absoluto e marcadores sensiveis (`Outros computadores`, `LOCALHOST`, `#administra`) nos datasets publicos Produto/NCM, corpus, manifesto e re-selo.
- Passe adversarial atualizado: `scripts/audit_produtos_ncm_adversarial.py` subiu para 12 casos, incluindo vazamento de drive e marcador local.
- Evidencia: `rg -n "[A-Z]:[\\/]|Outros computadores|LOCALHOST|#administra" data/produtos-ncm data/reforma-tributaria data/cowork data/corpus-local produto.html llms.txt assets/portal-search-full.json` retornou exit `1` sem matches.
- Gates reexecutados: bateria canonica completa com exit `0`; `audit_link_health.py` manteve apenas soft warnings e nenhum 404/410.
