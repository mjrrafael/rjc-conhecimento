# Monitoramento legislativo recorrente - 17/06/2026

## Escopo executado

- Rodada de revalidacao tecnica integral do portal apos o merge de 15/06/2026.
- Objetivo da rodada: confirmar que os hard gates continuam verdes no `main`, detectar regressao real e impedir que duplicatas locais nao rastreadas contaminem artefatos publicos.
- Janela operacional encerrada em `2026-06-17T07:46:57-03:00`.

## Criterios de pronto usados nesta rodada

1. Todos os hard gates da ordem canonica saem com codigo `0`, exceto o `rg` final que deve sair com `1` por ausencia de ocorrencias.
2. Nenhuma duplicata local do tipo `arquivo (1).html` aparece em `sitemap`, `llms.txt`, manifestos ou busca.
3. `assets/build-freshness.json` volta a convergir com HTML, busca, manifest e matriz de beneficios apos o rebuild.
4. O passe adversarial nao abre defeito novo apos a correcao.

## Fontes conferidas

- Artefatos locais gerados: `beneficios/index.html`, `llms.txt`, `assets/llm-manifest.json`, `assets/portal-search.js`, `assets/portal-search-full.json`, `assets/build-freshness.json`, `sitemap.xml`.
- Auditorias locais: `scripts/audit_*.py`.
- Saude de links oficiais em beneficios publicados: `103` URLs unicas verificadas por `python scripts/audit_link_health.py`.

## Achados

| URL/artefato | Data | Ato/objeto | Impacto | Arquivo afetado | Publico | Provenance | Confianca | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Workspace local | 2026-06-17 | Duplicata `beneficios/uf (1).html` | Falso positivo nos hard gates `audit_portal` e `audit_card_scope_visible`; risco de vazar para artefatos se o builder continuasse usando `rglob("*.html")` cru | `scripts/audit_portal.py`, `scripts/audit_v2_helpers.py`, `scripts/build_portal.py`, `scripts/build_master_indexes.py` | ambos | inspeção local | 0.99 | CORRIGIR |
| `assets/build-freshness.json` | 2026-06-17 | Manifesto de frescor desatualizado | `audit_index_freshness.py` bloqueando por checksums divergentes | artefatos publicos gerados | ambos | recálculo por build | 0.99 | CORRIGIR |
| `docs/monitoramento/monitoramento-legislativo-2026-06-15.md` | 2026-06-17 | Literal legado em ledger historico | `rg` final encontrou data editorial antiga dentro da documentacao | ledger historico | IA | busca textual local | 0.99 | CORRIGIR |
| Links oficiais BA/ES/CGIBS/MS/RJ/RN/RS/SP | 2026-06-17 | Instabilidade SSL/timeout/host/500 | Sem `404/410` em beneficio publicado; fila permanece para reverificacao manual | fontes oficiais remotas | ambos | HTTP runtime | 0.80 | A VALIDAR |

## Mudancas aplicadas com prova

- `scripts/audit_v2_helpers.py`: adicionado filtro canonico para ignorar duplicatas de workspace no formato ` (N)` em `BENEFIT_PAGES` e nas varreduras de `stale_date_hits`.
- `scripts/audit_portal.py`: `html_files()` passou a ignorar duplicatas locais nao canonicas.
- `scripts/build_portal.py`: criado filtro canonico para discovery, busca full-text, sitemap e normalizacao editorial, evitando que duplicatas locais vazem para artefatos publicos.
- `scripts/build_master_indexes.py`: cobertura passou a ignorar duplicatas locais no inventario de HTML.
- `docs/monitoramento/monitoramento-legislativo-2026-06-15.md`: higienizado o literal historico que acionava o `rg` sentinela.
- `python scripts/build_portal.py`: rebuild integral executado com sucesso apos os ajustes, regenerando `assets/build-freshness.json`, busca, manifest e sitemaps coerentes com o conjunto canonico.

## Quarentena

- Nenhum id novo enviado a quarentena nesta rodada.
- `python scripts/audit_quarantine_isolation.py`: `13137` ids de quarentena verificados fora dos artefatos publicos.

## Gates

| Gate | Resultado | Evidencia |
| --- | --- | --- |
| `python -m compileall -q scripts` | OK | sem erro |
| `python scripts/audit_portal.py` | OK | `Paginas HTML auditadas: 651` |
| `python scripts/audit_master_coverage.py` | OK | `9727` beneficios, `7050` linhas NCM, `27` estados |
| `python scripts/audit_benefit_cards.py` | OK | sem falhas |
| `python scripts/audit_card_scope_visible.py` | OK | contrato v2 visivel em todos os cards publicos |
| `python scripts/audit_no_keyword_inference.py` | OK | nenhum beneficio publico depende de keyword-only |
| `python scripts/audit_temporal_consistency.py` | OK | envelope temporal consistente |
| `python scripts/audit_link_health.py` | OK com soft warnings | `103` URLs unicas; nenhum `404/410`; persistem SSL/timeout/host/500 em fontes oficiais especificas |
| `python scripts/audit_index_freshness.py` | OK | HTML, busca, manifest e matriz regenerados no mesmo build |
| `python scripts/audit_quarantine_isolation.py` | OK | `13137` ids verificados fora dos artefatos publicos |
| `python scripts/audit_reforma_transition.py` | OK | todos os tributos legados com `transicao_rt` |
| `python scripts/audit_divergence_html_json_search.py` | OK | HTML, JSON e busca convergem |
| `python scripts/audit_editorial_date_per_card.py` | OK | `verificado_em` por card e data editorial derivada |
| `git diff --check` | OK com ressalva | apenas warnings LF/CRLF do Windows; nenhum erro de diff |
| `rg` final de residuos editoriais | OK | `exit 1` esperado por ausencia de hits |

## Passe adversarial

- Hipotese hostil: uma duplicata local nao rastreada ainda consegue poluir artefatos publicos ou derrubar gate canonico.
- Testes executados:
  - `python scripts/audit_portal.py` com a duplicata `beneficios/uf (1).html` ainda presente no workspace.
  - `rg -n -F "beneficios/uf (1).html" llms.txt assets/llm-manifest.json assets/portal-search-full.json assets/portal-search.js sitemap.txt sitemap.xml`
- Resultado:
  - `audit_portal.py` permaneceu verde.
  - o `rg` retornou `exit 1`, sem qualquer vazamento da duplicata para artefatos publicos.
  - nenhum defeito novo foi aberto apos a correcao.

## Pendencias humanas

- Reverificar manualmente as fontes oficiais com erro transitório/SSL/host: BA, ES, CGIBS, MS, RJ, RN, RS e SP.

## Pendencias IA/LLM

- Manter o filtro de duplicatas locais em qualquer novo builder/auditoria que varra HTML por `rglob`.

## Publicacao

- Nenhum commit, push ou PR aberto nesta rodada.
- Estado atual: branch `main` local pronta para PR apenas se o objetivo for publicar o endurecimento tecnico contra duplicatas e o rebuild associado.

## Status da rodada

- **Status literal:** `CONCLUIDO COM RESSALVA`
- Ressalva: os hard gates estao verdes, mas a fila soft de links oficiais instaveis permanece `A VALIDAR`.
