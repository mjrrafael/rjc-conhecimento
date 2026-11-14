# Liberação do Portal RJC — 2026-07-16

## Objetivo

Restaurar integralmente o Portal RJC Tributário em produção, mas somente com informação jurídica que tenha prova material atual, fonte oficial e vínculo por campo. A versão anterior só pode ser incorporada após essa revalidação integral.

## Baseline e escopo

- Baseline: `origin/main` em `f814f80efbab84bf43b671bf544c4678d4dda82a`.
- Universo encontrado: 658 HTML, 655 URLs em sitemap, 9.726 cards do crosswalk, 13.150 itens em quarentena, 7.050 linhas NCM e 19.089 entradas no índice de busca.
- Candidato anterior apenas local: `6d8dc9d7`; contém sete cards públicos, todos vinculados à IN RFB nº 2.324/2026, e não substitui a revalidação integral.

## Critérios de pronto falsificáveis

| ID | Critério | Evidência exigida |
|---|---|---|
| RLS-01 | Cada card público possui proveniência por campo, fonte oficial resolvida, recibo HTTP nativo e rechecagem independente. | Dados, recibos e ledger por card. |
| RLS-02 | Nenhum card, busca, sitemap, HTML ou LLM expõe material em quarentena. | Auditorias de projeção e fingerprints sem divergência. |
| RLS-03 | A matriz fechada cobre União e as 27 UFs nas três classes mínimas, com URL final, hash e recibo. | Matriz canônica completa e confrontada. |
| RLS-04 | Todo o acervo publicado é reconstruído e conciliado, sem diferença entre dados, HTML, busca, sitemap e produção. | Inventário integral, build determinístico e crawl. |
| RLS-05 | PR, CI no SHA exato, merge, Pages e hashes HTTP da produção estão confirmados. | PR, checks, execução Pages e confronto pós-deploy. |

## Limite de segurança

Não religar o acervo legado por simples alteração de exclusões. Isso recolocaria 9.726 cards sem proveniência material e 13.150 itens de quarentena na superfície pública. Enquanto RLS-01 a RLS-05 não forem atendidos, o status não pode ser de publicação integral.

## Handoff

Próximo passo: decidir se a autorização de publicação inclui expor o acervo legado sem a prova exigida; sem essa autorização explícita, revalidar e rederivar o corpus antes de qualquer mudança pública.
