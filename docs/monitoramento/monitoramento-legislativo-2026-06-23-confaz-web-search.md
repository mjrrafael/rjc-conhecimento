# Monitoramento Legislativo - 2026-06-23 - CONFAZ Web Search

## Escopo da rodada

- Automacao: `monitor-portal-rjc-tributario`.
- Pedido: revisar novamente, fazer nova busca web oficial e validar se havia conteudo novo.
- Criterio de pronto: fonte oficial lida/resolvida, dado novo refletido no JSON servido, HTML, busca leve, busca integral e checksum; hard gates verdes; passe adversarial executavel.

## Fontes conferidas

| Fonte | URL | HTTP | Ultima norma vista | Data |
| --- | --- | ---: | --- | --- |
| CONFAZ - Protocolos ICMS 2026 | https://www.confaz.fazenda.gov.br/legislacao/protocolos/2026 | 200 | PROTOCOLO ICMS 52/26 | 2026-06-23 |
| CONFAZ - Protocolo ICMS 52/26 | https://www.confaz.fazenda.gov.br/legislacao/protocolos/2026/protocolo-icms-52-26 | 200 | PROTOCOLO ICMS 52/26 | 2026-06-23 |
| CONFAZ - Atos COTEPE/ICMS 2026 | https://www.confaz.fazenda.gov.br/legislacao/atos/2026 | 200 | Atos COTEPE/ICMS 2026 em familia ainda nao publicada neste indice | 2026-06-23 |

## Achados

| Status | Achado | Prova oficial | Impacto | Arquivo afetado |
| --- | --- | --- | --- | --- |
| CORRIGIDO | O coletor de Protocolos ICMS so capturava o padrao antigo `ptNNN_YY` e perdia slugs novos `protocolo-icms-NN-YY`. | CONFAZ 2026 lista PROTOCOLO ICMS 37/26 a 52/26. | Portal ficava sem protocolos recentes no JSON e na busca. | `scripts/build_master_indexes.py`, `data/confaz_ultimos_5_anos.json` |
| CORRIGIDO | A pagina CONFAZ mostrava os primeiros 12 atos de cada ano, nao os mais recentes. | Comparacao local com JSON gerado e HTML. | Usuario/LLM nao encontravam o ato novo mesmo com JSON atualizado. | `scripts/build_portal.py`, `confaz/ultimos-5-anos.html` |
| CORRIGIDO | A busca leve e a busca integral nao indexavam atos CONFAZ individualmente. | Busca local por `PROTOCOLO ICMS 52/26` retornava zero antes e positivo depois. | Pesquisa do portal ficava funcionalmente incompleta. | `assets/portal-search.js`, `assets/portal-search-full.json` |
| CORRIGIDO | `build-freshness` nao carregava checksum do indice CONFAZ. | Auditoria local de checksum. | Dificultava provar que dados CONFAZ, HTML e busca pertencem ao mesmo build. | `scripts/build_portal.py`, `scripts/audit_index_freshness.py`, `assets/build-freshness.json` |
| A_VALIDAR | Atos COTEPE/ICMS 2026 existem em fonte oficial, mas a pagina atual e o contrato do indice publicado cobrem Convenios ICMS, Ajustes SINIEF e Protocolos ICMS. | https://www.confaz.fazenda.gov.br/legislacao/atos/2026 | Criar familia propria em rodada separada, com texto e politica de curadoria. | Nenhum conteudo publicado como fato material nesta rodada. |

## Mudancas aplicadas com prova

| Item | De | Para | Prova | Verificado em |
| --- | --- | --- | --- | --- |
| `data/confaz_ultimos_5_anos.json` Protocolos ICMS 2026 | 37 registros capturados na base anterior | 53 registros, incluindo retificacao e PROTOCOLO ICMS 52/26 | https://www.confaz.fazenda.gov.br/legislacao/protocolos/2026 | 2026-06-23 |
| Busca leve | Sem entrada direta para `PROTOCOLO ICMS 52/26` | Entrada `PROTOCOLO ICMS 52/26 · CONFAZ` apontando para `confaz/ultimos-5-anos.html#protocolos` | Busca local no arquivo gerado | 2026-06-23 |
| Busca integral | Sem entrada estruturada de ato CONFAZ | 1.377 entradas `kind=Ato CONFAZ` | `scripts/audit_confaz_recent_protocols.py` | 2026-06-23 |

## Quarentena

- Nenhum card de beneficio novo foi publicado.
- Nenhuma conclusao material de beneficio/ST foi criada a partir dos Protocolos ICMS novos.
- Atos COTEPE/ICMS 2026: `A_VALIDAR` para familia futura, sem publicacao como regra aplicavel.

## Gates

| Gate | Resultado | Evidencia |
| --- | --- | --- |
| `python -m compileall -q scripts` | OK | codigo 0 |
| `python scripts/audit_portal.py` | OK | 655 paginas HTML auditadas |
| `python scripts/audit_master_coverage.py` | OK | 15 requisitos federais, 27 UFs, 9.727 beneficios, 7.050 NCM, 3 familias CONFAZ |
| `python scripts/audit_benefit_cards.py` | OK | sem falhas |
| `python scripts/audit_card_scope_visible.py` | OK | contrato v2 visivel |
| `python scripts/audit_no_keyword_inference.py` | OK | sem inferencia por keyword em beneficio publico |
| `python scripts/audit_temporal_consistency.py` | OK | envelope temporal consistente |
| `python scripts/audit_link_health.py` | OK | 103 URLs unicas; nenhum 404/410; avisos soft de SSL/conexao |
| `python scripts/audit_index_freshness.py` | OK | indices e HTML coerentes |
| `python scripts/audit_quarantine_isolation.py` | OK | 13.137 ids de quarentena isolados |
| `python scripts/audit_reforma_transition.py` | OK | transicao_rt presente |
| `python scripts/audit_divergence_html_json_search.py` | OK | HTML, JSON e busca convergem |
| `python scripts/audit_editorial_date_per_card.py` | OK | data editorial derivada e `verificado_em` presentes |
| `git diff --check` | OK | codigo 0; somente avisos CRLF do Git |

## Passe adversarial

- Teste gerado: `python scripts/audit_confaz_recent_protocols.py`.
- Objetivo: falhar se `PROTOCOLO ICMS 52/26` sumir do JSON CONFAZ, HTML, busca leve, busca integral, destino interno ou checksum.
- Resultado: OK - `Passe adversarial CONFAZ OK: PROTOCOLO ICMS 52/26 em JSON, HTML, busca e frescor.`

## Pendencias humanas

- Decidir se a proxima rodada deve criar uma familia publica separada para Atos COTEPE/ICMS.

## Pendencias IA/LLM

- Manter instrução: CONFAZ indexado e fonte para curadoria; nenhum Protocolo ICMS novo vira beneficio aplicavel sem leitura integral do ato, vigencia e internalizacao estadual quando cabivel.

## Publicacao

- PR pendente nesta rodada ao terminar commit/push.
