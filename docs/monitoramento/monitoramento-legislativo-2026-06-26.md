# Monitoramento legislativo - 2026-06-26

## Escopo

Rodada recorrente de monitoramento do Portal RJC Tributario Aberto para verificar fatos oficiais novos desde 2026-06-25, revalidar os hard gates canonicos e confirmar a publicacao publica dos artefatos criticos.

Status literal da rodada: `CONCLUIDO COM RESSALVA`.

Ressalva: nao surgiu ato oficial novo obrigatorio a incorporar, mas a worktree local exigiu sincronizacao de artefatos publicos para corrigir um hard gate de frescor (`assets/portal-search.js` fora do mesmo build de `beneficios/index.html`). A publicacao depende de PR.

## Criterios de pronto

| # | Criterio de pronto | Metodo | Status | Evidencia |
| --- | --- | --- | --- | --- |
| 1 | Todos os hard gates canonicos saem com codigo `0` | execucao integral local | OK | bateria local apos saneamento do resíduo RS e rebuild coerente do portal |
| 2 | Nenhum ato oficial novo obrigatorio desde 2026-06-25 ficou ausente do portal | confronto com fonte primaria + busca no repo/publico | OK | portal ja continha `cgibs-marco-03-08-2026-campos-ibs-cbs`, `Ato Conjunto RFB/CGIBS 3/2026` e `PROTOCOLO ICMS 52/26` |
| 3 | Portal publico continua servindo artefatos criticos e mantendo a remocao publica da pagina RS 404 | verificacao HTTP publica | OK | `llms.txt`, `llm-manifest`, `portal-search.js` e `portal-search-full.json` com HTTP `200`; pagina RS `rs-credito-presumido-demais-casos.html` com HTTP `404` |
| 4 | Passe adversarial nao encontra divergencia nova entre HTML, JSON, busca, quarentena e CONFAZ | auditorias executaveis independentes | OK | `audit_divergence_html_json_search.py`, `audit_quarantine_isolation.py` e `audit_confaz_recent_protocols.py` verdes |

## Fontes conferidas

| Fonte | URL | HTTP | Ultimo item visto | Data verificada |
| --- | --- | ---: | --- | --- |
| CGIBS - Comunicados/atos operacionais | https://www.cgibs.gov.br/ | 200 via browser | marco operacional de 03/08/2026 para campos IBS/CBS ja refletido no portal | 2026-06-26 |
| CONFAZ - Protocolos 2026 | https://www.confaz.fazenda.gov.br/legislacao/protocolos/2026 | 200 via browser | `PROTOCOLO ICMS 52/26` segue refletido em JSON/HTML/busca | 2026-06-26 |
| GitHub Pages do portal | https://mjrrafael.github.io/rjc-conhecimento/ | 200 | artefatos publicos criticos respondendo e contendo item CGIBS 03/08 | 2026-06-26 |

## Achados

| Status | Achado | Impacto | Arquivo afetado | Publico | Provenance | Confianca |
| --- | --- | --- | --- | --- | --- | ---: |
| CORRIGIR/OK | HTML residual nao rastreado `estados/rs/legislacao/fontes/rs-credito-presumido-demais-casos.html` reapareceu na worktree e derrubou `audit_portal.py` | falso artefato publico local contrariando a quarentena RS de 2026-06-25 | `estados/rs/legislacao/fontes/rs-credito-presumido-demais-casos.html` | humano e IA | gate local + inspeção de arquivo | 0.99 |
| CORRIGIR/OK | `assets/portal-search.js` estava mais antigo que `beneficios/index.html`, quebrando `audit_index_freshness.py` | build publico incoerente na worktree local | `assets/portal-search.js`, `assets/portal-search-full.json`, `assets/llm-manifest.json`, `llms.txt`, `sitemap*`, HTMLs gerados | humano e IA | gate local + rebuild | 0.99 |
| OK | Nenhum fato oficial novo obrigatorio ficou ausente do portal desde 2026-06-25 | sem lacuna normativa identificada | portal federal/CONFAZ | humano e IA | confronto externo + busca local/publica | 0.95 |
| A VALIDAR | Warnings soft persistem em `audit_link_health.py` por SSL/reset/DNS/timeout em fontes BA/ES/DF/MS/RJ/RN/RS/CGIBS | nao bloqueia publicacao, mas exige rechecagem futura | fontes oficiais diversas | editorial | auditoria automatizada | 0.85 |

## Mudancas aplicadas com prova

| Id/artefato | Campo/acao | De | Para | Prova | Verificado em |
| --- | --- | --- | --- | --- | --- |
| `estados/rs/legislacao/fontes/rs-credito-presumido-demais-casos.html` | exposicao local residual | HTML publico local indevido | removido da worktree | `git ls-files` vazio + falha inicial de `audit_portal.py` + nova passada verde | 2026-06-26 |
| artefatos de descoberta/busca | sincronizacao de build | `portal-search.js` de `2026-06-25 16:28` versus `beneficios/index.html` de `2026-06-25 18:18` | rebuild coerente em `2026-06-26 07:45-07:46` | `audit_index_freshness.py` passou apos `python scripts/build_portal.py` | 2026-06-26 |
| sitemap/rodapes editoriais | data derivada | `25/06/2026` | `26/06/2026` | diff amostral em `sitemap.xml` e `estados/rs/legislacao/fontes/rs-ampara-rs.html` | 2026-06-26 |

## Quarentena

| Id | Motivo | Destino |
| --- | --- | --- |
| fonte `RS_CREDITO_PRESUMIDO_DEMAIS_CASOS` | mantida fora do publico porque a URL oficial primaria de 2026-06-25 seguia 404 no gate local | continua isolada de HTML publico, `llms.txt`, busca, sitemap e registry |

## Gates

| Gate | Resultado | Evidencia |
| --- | --- | --- |
| `python -m compileall -q scripts` | OK | exit `0` |
| `python scripts/audit_portal.py` | OK | primeira passada falhou no resíduo RS; segunda passada: `Paginas HTML auditadas: 655` |
| `python scripts/audit_master_coverage.py` | OK | `15` requisitos federais, `27` estados, `9726` beneficios, `7050` linhas NCM, `3` familias CONFAZ |
| `python scripts/audit_benefit_cards.py` | OK | sem falhas |
| `python scripts/audit_card_scope_visible.py` | OK | contrato v2 visivel |
| `python scripts/audit_no_keyword_inference.py` | OK | nenhum keyword-only publico |
| `python scripts/audit_temporal_consistency.py` | OK | envelope temporal consistente |
| `python scripts/audit_link_health.py` | OK com warnings soft | `102` URLs unicas; nenhum `404/410` em beneficio publicado |
| `python scripts/audit_index_freshness.py` | OK | falhou antes do rebuild; passou apos sincronizacao dos artefatos |
| `python scripts/audit_quarantine_isolation.py` | OK | `13150` ids de quarentena isolados |
| `python scripts/audit_reforma_transition.py` | OK | `transicao_rt` presente |
| `python scripts/audit_divergence_html_json_search.py` | OK | convergencia entre HTML, JSON e busca |
| `python scripts/audit_editorial_date_per_card.py` | OK | data editorial derivada e `verificado_em` presente |
| `git diff --check` | OK com warnings CRLF do Git | sem erro de diff; warnings apenas de normalizacao futura CRLF |
| `rg -n "25/04/2026|\[\] \[\] \[\]|str\(\[" .` | OK com ressalva documental | ocorrencias apenas em ledgers historicos |

## Passe adversarial

Testes executaveis independentes apos o rebuild:

- `python scripts/audit_divergence_html_json_search.py`
- `python scripts/audit_quarantine_isolation.py`
- `python scripts/audit_confaz_recent_protocols.py`
- verificacao HTTP publica de `llms.txt`, `assets/llm-manifest.json`, `assets/portal-search.js`, `assets/portal-search-full.json` e da pagina RS removida

Resultado: `PASSE ADVERSARIAL OK`.

## Publicacao

Sem publicacao concluida nesta etapa do ledger.

- Branch local no inicio da rodada: `main`
- `main` local estava em `04797b7`
- Diff gerado apos rebuild coerente: `156` arquivos rastreados, `649` insercoes e `649` remocoes segundo `git diff --stat`
- Politica de publicacao aplicavel: qualquer HTML/manifest/busca via PR

## Pendencias humanas

- Decidir se a sincronizacao deterministica dos artefatos gerados em 2026-06-26 sera publicada via PR.

## Pendencias IA/LLM

- Remover o duplicado nao rastreado `beneficios/cesta-basica (1).html` em rodada futura para reduzir ruído da worktree.
- Rever warnings soft recorrentes de SSL/reset/DNS nas fontes estaduais e CGIBS.
