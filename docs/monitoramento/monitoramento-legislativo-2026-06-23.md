# Monitoramento legislativo - 2026-06-23

## Escopo

Retomada do Portal Tributario RJC Aberto apos reclamacao operacional de que a nova pagina `produto.html` tinha layout, mas nao tinha consulta real. A rodada recomeçou do zero na camada funcional da busca Produto/NCM e preservou a Regra #0: sem fonte oficial, vigencia e prova, nada vira verde.

## Fontes e artefatos conferidos

| Fonte/artefato | URL/caminho | HTTP/status | Evidencia | Data |
|---|---|---:|---|---|
| Portal publico Produto/NCM antes da correcao | `https://mjrrafael.github.io/rjc-conhecimento/produto.html` | 200 | pagina tinha apenas seed de arroz | 2026-06-23 |
| Indice publico Produto/NCM antes da correcao | `https://mjrrafael.github.io/rjc-conhecimento/data/produtos-ncm/index.json` | 200 | `products=1`, `ncm_codes=3` no seed | 2026-06-23 |
| Lista publica NCM x beneficios | `https://mjrrafael.github.io/rjc-conhecimento/beneficios/ncm.html` | 200 | pagina tecnica existente respondia com base ampla | 2026-06-23 |
| Busca integral publica | `https://mjrrafael.github.io/rjc-conhecimento/assets/portal-search-full.json` | 200 | 17.713 itens publicados | 2026-06-23 |
| Base tecnica local NCM x beneficios | `data/ncm_benefits_index.json` | local | 7.050 linhas, 1.441 NCM unicos, 15 jurisdicoes | 2026-06-23 |
| Crosswalk local de beneficios | `data/benefits_crosswalk.json` | local | 9.727 entradas; 2.605 registros com NCM detectavel | 2026-06-23 |

## Achados

| Status | Achado | Impacto | Arquivo afetado | Publico | Evidencia |
|---|---|---|---|---|---|
| CORRIGIR | `produto.html` filtrava apenas cards estaticos e mostrava 1 seed de arroz/3 NCMs | consulta Produto/NCM parecia existir, mas nao acessava o conteudo real | `scripts/build_portal.py`, `assets/portal-tributario.js`, `produto.html` | humano/IA | `data-product-result.count=1` antes; indice real tinha 7.050 linhas |
| CORRIGIR | Auditoria Produto/NCM validava coerencia do seed, mas nao bloqueava pagina sem dados reais | regressao funcional passava nos gates | `scripts/audit_produtos_ncm.py`, `scripts/audit_produtos_ncm_adversarial.py` | humano/IA | adversarial anterior nao simulava base pequena |
| OK | Conteudo real do portal nao tinha sumido; estava publicado em `beneficios/ncm.html`, `data/ncm_benefits_index.json` e `portal-search-full.json` | problema era integracao da nova experiencia Produto/NCM | dados/HTML existentes | humano/IA | `beneficios/ncm.html` 200; `portal-search-full.json` 17.713 itens |
| A_VALIDAR | Avisos soft de link continuam em fontes estaduais/CGIBS com SSL, timeout, reset ou DNS | nao houve 404/410 em card publicado; manter fila de revalidacao | fontes BA, ES, MS, RJ, RN, RS, CGIBS | humano/IA | `audit_link_health.py` com soft warnings e exit 0 |

## Mudancas aplicadas

| Item | De | Para | Prova |
|---|---|---|---|
| Consulta Produto/NCM | HTML seed-only de 1 produto/3 NCMs | pagina leve com amostras reais e carregamento dinamico de `data/ncm_benefits_index.json` | `produto.html` com `data-product-dataset="data/ncm_benefits_index.json"` |
| Motor de busca Produto/NCM | filtro DOM sobre cards estaticos | `fetch(datasetUrl)`, busca no dataset completo e renderizacao limitada a 250 cards por consulta | `assets/portal-tributario.js` |
| Auditoria Produto/NCM | validava seed federal, corpus amarelo e plano UF | valida tambem schema/volume do indice real, arroz `1006.20` com URL oficial, loader JS e tamanho divulgado | `scripts/audit_produtos_ncm.py` |
| Passe adversarial | 12 casos contra seed/corpus | 14 casos, incluindo indice NCM pequeno e ausencia de arroz real | `scripts/audit_produtos_ncm_adversarial.py` |
| Frescor de build | nao rastreava `data/ncm_benefits_index.json` nem JS funcional Produto/NCM | checksums cruzados incluem `data/ncm_benefits_index.json` e `assets/portal-tributario.js` | `scripts/build_portal.py`, `scripts/audit_index_freshness.py` |

## Evidencias funcionais

| Teste | Resultado |
|---|---|
| `produto.html` apos rebuild | 119.242 bytes; 19 amostras reais/seed no HTML; sem resumo `1 produto(s) e 3 codigo(s)` |
| Dataset real | 7.050 linhas NCM x beneficio; 1.441 NCM unicos; 15 jurisdicoes |
| Busca local no dataset por `arroz` | 204 hits |
| Busca local no dataset por `1006.20` | 7 hits |
| Busca local no dataset por `2711.21.00` | 4 hits |
| Busca local no dataset por `credito presumido` | 424 hits |
| Busca local no dataset por `MG ICMS` | 708 hits |
| Sintaxe JavaScript | `node --check assets/portal-tributario.js` exit 0 |

## Gates

| Gate | Resultado | Evidencia |
|---|---|---|
| `python scripts/build_portal.py` | OK | `Portal generated successfully.` |
| `python -m compileall -q scripts` | OK | exit 0 |
| `node --check assets/portal-tributario.js` | OK | exit 0 |
| `python scripts/audit_produtos_ncm.py` | OK | Produto/NCM coerente |
| `python scripts/audit_produtos_ncm_adversarial.py` | OK | `{"status": "OK", "adversarial_cases": 14}` |
| `python scripts/audit_portal.py` | OK | 655 paginas HTML auditadas |
| `python scripts/audit_master_coverage.py` | OK | 15 requisitos federais; 27 estados; 9.727 beneficios; 7.050 linhas NCM |
| `python scripts/audit_benefit_cards.py` | OK | sem falhas |
| `python scripts/audit_card_scope_visible.py` | OK | contrato v2 visivel |
| `python scripts/audit_no_keyword_inference.py` | OK | sem keyword-only publico |
| `python scripts/audit_temporal_consistency.py` | OK | envelopes consistentes |
| `python scripts/audit_link_health.py` | OK com soft warnings | 103 URLs unicas; nenhum 404/410 |
| `python scripts/audit_index_freshness.py` | OK | checksums coerentes |
| `python scripts/audit_quarantine_isolation.py` | OK | 13.137 ids isolados |
| `python scripts/audit_reforma_transition.py` | OK | `transicao_rt` presente |
| `python scripts/audit_divergence_html_json_search.py` | OK | HTML, JSON e busca convergem |
| `python scripts/audit_editorial_date_per_card.py` | OK | data editorial derivada e `verificado_em` por card |
| `git diff --check` | OK | apenas avisos CRLF do Git |
| `rg -n "25/04/2026|\[\] \[\] \[\]|str\(\[" .` invertido | OK | nenhum marcador residual encontrado |

## Passe adversarial

Teste executavel: `python scripts/audit_produtos_ncm_adversarial.py`.

Casos adicionados nesta rodada:

- Base NCM artificialmente reduzida para 3 linhas deve falhar com `too small`.
- Base NCM sem linha real de arroz `1006.20` com URL oficial deve falhar com `missing real arroz 1006.20`.

Resultado: OK, 14 casos adversariais derrubados.

## Quarentena

Nenhum item de quarentena foi promovido. O corpus estadual local segue no maximo `AMARELO_CORPUS_LOCAL`; cBenef de UF nao-GO permanece `A_VALIDAR_SEFAZ_VIVA`.

## Pendencias

| Tipo | Pendencia |
|---|---|
| Humana | Revisar UX publica da consulta apos Pages atualizar, especialmente tempo de carregamento do JSON amplo em conexao comum |
| IA/LLM | Proxima rodada pode particionar `data/ncm_benefits_index.json` por capitulo/UF para reduzir payload inicial sem perder cobertura |
| Soft gate | Revalidar URLs com SSL/timeout/reset/DNS em BA, ES, MS, RJ, RN, RS e CGIBS |

## Publicacao

Branch: `fix/produto-ncm-real-data`.

PR, merge, Pages e verificacao HTTP publica serao registrados no fechamento da automacao apos push.
