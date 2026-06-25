# Monitoramento legislativo - 2026-06-25

## Escopo

Rodada extraordinaria para corrigir achado hard de qualidade publicado em 2026-06-25: card RS de credito presumido com fonte oficial retornando HTTP 404 no gate local.

Status literal da rodada: `CONCLUIDO`.

Publicacao concluida via PR #21, merge commit `f914054f74997e6f3175af6c979ae0c55a16b074`, com GitHub Pages publicado e verificacao HTTP publica final em 2026-06-25.

## Criterios de pronto

| # | Criterio de pronto | Metodo | Status | Evidencia |
| --- | --- | --- | --- | --- |
| 1 | Nenhum card publishable depende de `https://receita.fazenda.rs.gov.br/servicos-a-empresas/servicos?servico=2959` | teste automatizado + busca integral | OK | `data/benefits_crosswalk.json`: `9726` entradas, `old_id_public=False`, `source_public=False` |
| 2 | Fonte RS sem URL primaria resolvivel fica em quarentena, nao em indice publico | rebuild + auditoria de isolamento | OK | `data/benefits_quarantine.json`: `10` entradas da fonte; `llms.txt`, `sitemap`, `portal-search*`, `data/legal_sources_registry.json` e HTML publico sem `servico=2959` |
| 3 | Gates hard canonicos passam | bateria local | OK | bateria canonica com exit `0` em 2026-06-25 |
| 4 | Passe adversarial nao encontra novo defeito relacionado ao card RS | teste executavel independente | OK | `PASSE ADVERSARIAL OK: rs-4ab7ac6454f0 removido; 10 quarentenados; 662 artefatos publicos inspecionados.` |

## Fontes conferidas

| Fonte | URL | HTTP | Ultima norma/servico visto | Data verificada |
| --- | --- | ---: | --- | --- |
| Receita Estadual/RS - URL publicada anterior | https://receita.fazenda.rs.gov.br/servicos-a-empresas/servicos?servico=2959 | 404 | Opção ao Crédito Presumido - Demais Casos nao resolvivel no gate local | 2026-06-25 |
| Portal de Atendimento da Receita Estadual/RS | https://atendimento.receita.rs.gov.br/empresas/servicos?servico=2959 | 404 no gate local; visivel via navegador externo | Opção ao Crédito Presumido - Demais Casos | 2026-06-25 |
| Portal RS.GOV.BR - Carta de Serviços | https://www.rs.gov.br/carta-de-servicos/servicos?servico=2959 | 404 no gate local; visivel via navegador externo | Opção ao Crédito Presumido - Demais Casos | 2026-06-25 |

## Achados

| Status | Achado | Impacto | Arquivo afetado | Publico | Provenance | Confianca |
| --- | --- | --- | --- | --- | --- | ---: |
| OK | Card `rs-4ab7ac6454f0` estava `publishable=true` com fonte oficial que retorna HTTP 404 no gate local; foi removido dos artefatos publicos e levado a quarentena | viola a politica "fonte primaria resolvivel ou nada"; corrigido localmente | `data/benefits_crosswalk.json`, paginas de beneficios, indices e registry | humano e IA | `python scripts/audit_link_health.py` + teste adversarial | 0.99 |
| A VALIDAR | Existem espelhos oficiais com o mesmo conteudo vistos pelo navegador, mas todos retornaram 404 no gate local | insuficiente para publicar como fato validado ate haver URL que passe no gate | fonte RS de credito presumido demais casos | editorial | confronto web + teste local | 0.90 |
| CORRIGIR/OK | O primeiro rebuild deixou link quebrado em `estados/auditoria-fontes.html` para a pagina-fonte apagada | auditoria publica ainda vazava a fonte bloqueada | `scripts/build_portal.py`, `scripts/state_legal_pages.py`, `data/legal_sources_registry.json` | humano e IA | `python scripts/audit_portal.py` falhou, depois passou | 0.99 |

## Mudancas aplicadas com prova

| Id card | Campo | De | Para | Ato/link | Verificado em |
| --- | --- | --- | --- | --- | --- |
| `rs-4ab7ac6454f0` | `publishable` | `true` | quarentena por fonte `a_validar_link_404` | `https://receita.fazenda.rs.gov.br/servicos-a-empresas/servicos?servico=2959` retornou 404 | 2026-06-25 |
| fonte `RS_CREDITO_PRESUMIDO_DEMAIS_CASOS` | exposicao publica | pagina HTML, busca, sitemap, llms e registry | removida de artefatos publicos; mantida apenas como quarentena editorial | gate local + teste adversarial | 2026-06-25 |

## Quarentena

| Id | Motivo | Destino |
| --- | --- | --- |
| fonte `RS_CREDITO_PRESUMIDO_DEMAIS_CASOS` | fonte oficial retornou HTTP 404 no gate local de 2026-06-25; nao publicar card ate haver URL primaria resolvivel | `data/benefits_quarantine.json`, `10` registros; isolada de HTML publico, `llms.txt`, sitemap, busca e registry |

## Gates

| Gate | Resultado | Evidencia |
| --- | --- | --- |
| `python -m compileall -q scripts` | OK | exit `0` |
| `python scripts/audit_portal.py` | OK | `Paginas HTML auditadas: 655`; sem falhas |
| `python scripts/audit_master_coverage.py` | OK | `15` requisitos federais, `27` estados, `9726` beneficios, `7050` linhas NCM, `3` familias CONFAZ |
| `python scripts/audit_benefit_cards.py` | OK | sem falhas |
| `python scripts/audit_card_scope_visible.py` | OK | contrato v2 visivel |
| `python scripts/audit_no_keyword_inference.py` | OK | nenhum keyword-only publico |
| `python scripts/audit_temporal_consistency.py` | OK | envelope temporal consistente |
| `python scripts/audit_link_health.py` | OK com warnings soft | `102` URLs unicas; nenhum `404/410` em beneficio publicado |
| `python scripts/audit_index_freshness.py` | OK | indices e HTML no mesmo build |
| `python scripts/audit_quarantine_isolation.py` | OK | `13150` ids de quarentena isolados |
| `python scripts/audit_reforma_transition.py` | OK | `transicao_rt` presente nos tributos legados |
| `python scripts/audit_divergence_html_json_search.py` | OK | HTML, JSON e busca convergem |
| `python scripts/audit_editorial_date_per_card.py` | OK | data editorial derivada e `verificado_em` presente |
| `git diff --check` | OK | exit `0` |
| `rg -n "25/04/2026|\[\] \[\] \[\]|str\(\[" .` | OK com ressalva documental | ocorrencias apenas em ledgers anteriores |

## Passe adversarial

Teste executavel independente rodado apos os gates:

- `rs-4ab7ac6454f0` ausente de `data/benefits_crosswalk.json`;
- `RS_CREDITO_PRESUMIDO_DEMAIS_CASOS_2026-04-26.txt` sem beneficios publicados;
- `10` registros da fonte em `data/benefits_quarantine.json`;
- `662` artefatos publicos inspecionados sem `rs-4ab7ac6454f0`, `servico=2959`, slug da fonte ou ids de quarentena.

Resultado: `PASSE ADVERSARIAL OK`.

## Publicacao

Publicacao concluida.

- PR: https://github.com/mjrrafael/rjc-conhecimento/pull/21
- Branch: `codex/corrige-fonte-rs-credito-presumido`
- Commit da correcao: `699ff9c2ecd5108231a294730b0f020f32967722`
- Merge em `main`: `f914054f74997e6f3175af6c979ae0c55a16b074`
- GitHub Pages: run `28201074973`, `pages-build-deployment`, sucesso em 2026-06-25T21:18:13Z
- Verificacao HTTP publica final: `PUBLIC_VERIFY_OK`

Artefatos publicos verificados com cache-buster em 2026-06-25:

| Artefato publico | HTTP | Evidencia |
| --- | ---: | --- |
| `llms.txt` | 200 | sem `rs-4ab7ac6454f0`, `servico=2959`, `RS_CREDITO_PRESUMIDO_DEMAIS_CASOS` ou slug |
| `sitemap.xml` | 200 | sem vazamento |
| `sitemap.txt` | 200 | sem vazamento |
| `assets/llm-manifest.json` | 200 | sem vazamento |
| `assets/portal-search.js` | 200 | sem vazamento |
| `assets/portal-search-full.json` | 200 | sem vazamento |
| `data/benefits_crosswalk.json` | 200 | sem vazamento |
| `beneficios/index.html` | 200 | sem vazamento |
| `estados/auditoria-fontes.html` | 200 | sem vazamento |
| `data/legal_sources_registry.json` | 200 | sem vazamento |
| `estados/rs/legislacao/fontes/rs-credito-presumido-demais-casos.html` | 404 | pagina-fonte removida do publico |
