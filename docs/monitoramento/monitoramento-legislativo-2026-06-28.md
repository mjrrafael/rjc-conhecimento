# Monitoramento legislativo - 2026-06-28

## Escopo

Rodada recorrente do Portal RJC Tributario Aberto para verificar fontes oficiais primarias desde o ledger de 2026-06-26, reexecutar a bateria canonica v2.0 e decidir se havia conteudo novo a publicar.

Status literal da rodada: `CONCLUIDO COM RESSALVA`.

Ressalvas: o GET do HTML do CGIBS/DeRE sofreu reset de conexao em uma tentativa, mas o HEAD da pagina e o PDF oficial primario do Ato Conjunto 3/2026 responderam HTTP 200. O arquivo local nao rastreado `beneficios/cesta-basica (1).html` foi comparado integralmente e removido por ser snapshot antigo sem diferenca material apos normalizar datas/line endings.

## Criterios de pronto

| # | Criterio de pronto | Metodo | Status | Evidencia |
| --- | --- | --- | --- | --- |
| 1 | Hard gates canonicos saem com codigo `0` | execucao integral local | OK | bateria canonica executada em 2026-06-28 21h e reexecutada em 2026-06-28 22h local; todos os exits `0` |
| 2 | Nenhuma fonte oficial nova obrigatoria desde 2026-06-26 fica ausente | confronto com fonte primaria + busca local | OK | CONFAZ 2026 local contem `CONVENIO ICMS 62/26`, `AJUSTE SINIEF 16/26` e `PROTOCOLO ICMS 52/26`; CGIBS DeRE 1.1.0 coberta pelo Ato Conjunto 3/2026 |
| 3 | HTML, JSON, busca e LLM continuam convergentes | auditorias v2 e checks de checksum | OK | `audit_index_freshness`, `audit_divergence_html_json_search`, `audit_quarantine_isolation` verdes |
| 4 | Passe adversarial gera teste executavel e nao encontra defeito novo no portal | script PowerShell + auditorias independentes | OK | URLs oficiais individuais CONFAZ resolveram 200; JSON/HTML/busca contem os ultimos atos; gates adversariais verdes |

## Fontes conferidas

| Fonte | URL | HTTP | Ultimo item visto | Data verificada |
| --- | --- | ---: | --- | --- |
| CONFAZ - Convenios ICMS 2026 | https://www.confaz.fazenda.gov.br/legislacao/convenios/2026/CV062_26 | 200 | `CONVENIO ICMS 62/26` | 2026-06-28 |
| CONFAZ - Ajustes SINIEF 2026 | https://www.confaz.fazenda.gov.br/legislacao/ajustes/2026/AJ016_26 | 200 | `AJUSTE SINIEF 16/26` | 2026-06-28 |
| CONFAZ - Protocolos ICMS 2026 | https://www.confaz.fazenda.gov.br/legislacao/protocolos/2026/protocolo-icms-52-26 | 200 | `PROTOCOLO ICMS 52/26` | 2026-06-28 |
| CGIBS - DeRE | https://www.cgibs.gov.br/declaracao-de-regimes-especificos-dere | 200 via HEAD; GET com reset transitorio | pacote tecnico DeRE versao 1.1.0 ja coberto pelo Ato Conjunto 3/2026 | 2026-06-28 |
| CGIBS - PDF Ato Conjunto 3/2026 | https://www.cgibs.gov.br/upload/arquivos/202606/22083423-ato-conjunto-nro-3-dere.pdf | 200 | PDF oficial primario do Ato Conjunto RFB/CGIBS 3/2026, `Last-Modified: Mon, 22 Jun 2026` | 2026-06-28 |
| RFB/SIJUT - consulta de normas | https://normas.receita.fazenda.gov.br/sijut2consulta/consulta.action | 200 | consulta geral acessivel; sem achado material novo obrigatorio para beneficio/card nesta rodada | 2026-06-28 |

## Achados

| Status | Achado | Impacto | Arquivo afetado | Publico | Provenance | Confianca |
| --- | --- | --- | --- | --- | --- | ---: |
| OK | CONFAZ mais recente ja refletido na branch: `CONVENIO ICMS 62/26`, `AJUSTE SINIEF 16/26`, `PROTOCOLO ICMS 52/26` | sem lacuna nova de indice CONFAZ | `data/confaz_ultimos_5_anos.json`, `confaz/ultimos-5-anos.html`, `assets/portal-search.js` | humano e IA | fonte primaria CONFAZ + busca local | 0.98 |
| OK | Pacote DeRE 1.1.0 ja refletido pelo Ato Conjunto RFB/CGIBS 3/2026 | sem pagina nova necessaria | `federal/legislacao/atos/ato-conjunto-rfb-cgibs-3-2026-dere.html`, `llms.txt`, `assets/llm-manifest.json` | humano e IA | PDF primario CGIBS + busca local | 0.97 |
| A VALIDAR | GET do HTML da pagina CGIBS/DeRE sofreu reset de conexao em uma tentativa, apesar de HEAD 200 e PDF oficial 200 | rechecagem futura recomendada, sem bloqueio porque a fonte primaria PDF resolve | fonte CGIBS DeRE | editorial | teste de rede | 0.80 |
| CORRIGIR/OK | Arquivo local nao rastreado `beneficios/cesta-basica (1).html` era snapshot antigo do canonico | ruido de worktree eliminado; sem impacto publico | worktree local | local | diff integral: 1.154 linhas alteradas apenas por `verificado_em`/rodape 24/06 versus 25/06; normalizacao de datas e line endings deixou os arquivos identicos | 0.99 |

## Mudancas aplicadas com prova

Nenhuma mudanca em artefatos publicos, dados de beneficio, HTML servido, busca, sitemap ou manifest.

Gravado este ledger de monitoramento e removido o snapshot local nao rastreado `beneficios/cesta-basica (1).html`.

## Quarentena

Sem nova quarentena nesta rodada.

## Gates

| Gate | Resultado | Evidencia |
| --- | --- | --- |
| `python -m compileall -q scripts` | OK | exit `0` |
| `python scripts/audit_portal.py` | OK | `Paginas HTML auditadas: 655` |
| `python scripts/audit_master_coverage.py` | OK | `15` requisitos federais, `27` estados, `9726` beneficios, `7050` linhas NCM, `3` familias CONFAZ |
| `python scripts/audit_benefit_cards.py` | OK | sem falhas |
| `python scripts/audit_card_scope_visible.py` | OK | contrato v2 visivel |
| `python scripts/audit_no_keyword_inference.py` | OK | nenhum keyword-only publico |
| `python scripts/audit_temporal_consistency.py` | OK | envelope temporal consistente |
| `python scripts/audit_link_health.py` | OK com warnings soft | `102` URLs unicas; nenhum `404/410` em beneficio publicado; warnings de SSL/reset/DNS/timeout semelhantes aos ledgers anteriores |
| `python scripts/audit_index_freshness.py` | OK | indices e HTML coerentes pelo `assets/build-freshness.json` |
| `python scripts/audit_quarantine_isolation.py` | OK | `13150` ids de quarentena isolados |
| `python scripts/audit_reforma_transition.py` | OK | `transicao_rt` presente |
| `python scripts/audit_divergence_html_json_search.py` | OK | convergencia entre HTML, JSON e busca |
| `python scripts/audit_editorial_date_per_card.py` | OK | data editorial derivada e `verificado_em` por card |
| `git diff --check` | OK | exit `0` |
| `rg -n "25/04/2026|\[\] \[\] \[\]|str\(\[" .` | OK com ressalva documental | ocorrencias apenas em ledgers historicos |

## Passe adversarial

Testes executaveis usados:

- PowerShell: resolve URLs oficiais individuais CONFAZ (`CV062_26`, `AJ016_26`, `protocolo-icms-52-26`) e exige o mesmo ato em `data/confaz_ultimos_5_anos.json`, `confaz/ultimos-5-anos.html` e `assets/portal-search.js`.
- `curl -I` no PDF oficial CGIBS do Ato Conjunto RFB/CGIBS 3/2026.
- `rg` em fonte local, HTML, manifest, busca e `llms.txt` para confirmar DeRE 1.1.0 e o link oficial CGIBS.
- `python scripts/audit_divergence_html_json_search.py`
- `python scripts/audit_quarantine_isolation.py`
- `python scripts/audit_confaz_recent_protocols.py`

Resultado: `PASSE ADVERSARIAL OK`.

Observacao adversarial: a primeira versao do teste falhou por regex fragil contra o indice de Ajustes SINIEF e por tentativa de regex atravessando quebras de linha no HTML local. O teste foi corrigido para validar URLs oficiais individuais e assercoes separadas por ato. Nao foi identificado defeito novo no portal.

## Publicacao

Publicacao feita por PR, sem push direto em `main`.

- PR: `#22` - https://github.com/mjrrafael/rjc-conhecimento/pull/22
- Branch: `codex/monitor-portal-2026-06-26-freshness-sync`
- Commit adicional de ledger anexado a PR: `345bfa3a6011d3d3b1ac8ef5f868e03de4b9bf37`
- Merge commit: `fd021dabd18eca63a650c39949342bece9a81d2f`
- Pages run: `28343979900`, `success`, https://github.com/mjrrafael/rjc-conhecimento/actions/runs/28343979900
- Verificacao HTTP publica apos Pages: raiz `200`; este ledger `200`; `beneficios/cesta-basica.html` `200`; `beneficios/cesta-basica%20(1).html` `404`; `llms.txt` `200`; `assets/llm-manifest.json` `200`; `assets/portal-search.js` `200`; `assets/build-freshness.json` `200`.

## Pendencias humanas

Sem pendencia humana da rodada.

## Pendencias IA/LLM

- Revalidar em rodada futura o GET da pagina CGIBS/DeRE, pois o HEAD e o PDF primario resolveram 200, mas o HTML reiniciou conexao uma vez.
