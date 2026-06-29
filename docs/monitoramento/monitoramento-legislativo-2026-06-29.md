# Monitoramento legislativo - 2026-06-29

## Escopo

Rodada recorrente do Portal RJC Tributario Aberto para verificar fontes oficiais primarias desde o ledger de 2026-06-28, aplicar atualizacao federal comprovada, reexecutar a bateria canonica v2.0 e preparar publicacao por PR.

Status literal da rodada: `CONCLUIDO COM RESSALVA`.

Ressalvas: a noticia equivalente do CGIBS sobre CNPJ de pessoas fisicas retornou HTTP `404` no teste por `curl`, portanto nao foi usada como ancora publicada. Durante o build, o Anexo IX consolidado de Goias retornou conteudo oficial diferente do publicado anteriormente; como essa mudanca estadual exige revisao propria, os HTMLs e registros de busca de Goias foram restaurados para a versao anterior e o achado ficou `A VALIDAR`.

## Criterios de pronto

| # | Criterio de pronto | Metodo | Status | Evidencia |
| --- | --- | --- | --- | --- |
| 1 | Hard gates canonicos saem com codigo `0` | execucao integral local | OK | bateria canonica executada em 2026-06-29; todos os exits `0` |
| 2 | Fonte oficial primaria da nova afirmacao resolve | `curl -L` + fonte RFB | OK | noticia RFB sobre prorrogacao do CNPJ de pessoas fisicas retornou HTTP `200` |
| 3 | Nenhuma ancora 404 e publicada como prova | teste adversarial de URLs | OK | URL CGIBS equivalente retornou `404` e nao foi incluida como fonte publicada |
| 4 | HTML, JSON, busca e LLM convergem | auditorias v2 + teste adversarial de indices | OK | `audit_index_freshness`, `audit_divergence_html_json_search`, `audit_quarantine_isolation` verdes |
| 5 | Efeito colateral de fonte estadual dinamica fica isolado | diff estruturado de `portal-search-full.json` e rollback de HTMLs GO | OK com ressalva | zero divergencia Goias no indice final; pendencia registrada como `A VALIDAR` |
| 6 | Passe adversarial gera teste executavel e nao encontra defeito novo | Python assertivo + `curl` | OK | `ADVERSARIAL_TESTS_OK` |

## Fontes conferidas

| Fonte | URL | HTTP | Ultimo item visto | Data verificada |
| --- | --- | ---: | --- | --- |
| Receita Federal - noticia RFB/CGIBS | https://www.gov.br/receitafederal/pt-br/assuntos/noticias/obrigatoriedade-de-inscricao-de-pessoas-fisicas-no-cnpj-para-emissao-de-documentos-fiscais-e-prorrogada-para-2027 | 200 | prorrogacao para `01/01/2027` da obrigatoriedade de CNPJ para pessoas fisicas que emitem documentos fiscais | 2026-06-29 |
| CGIBS - noticia equivalente CNPJ PF | https://www.cgibs.gov.br/obrigatoriedade-de-inscricao-no-cnpj-por-pessoas-fisicas-vinculada-a-emissao-de-documentos-fiscais-foi-estendida-para-1-de-janeiro-de-2027 | 404 | nao usada como ancora publicada | 2026-06-29 |
| CGIBS - marco operacional 03/08/2026 | https://www.cgibs.gov.br/novo-marco-da-reforma-tributaria-inicia-em-03-de-agosto-com-preenchimento-obrigatorio-dos-campos-relativos-ao-ibs-e-a-cbs | 200 | comunicado de 15/06/2026 versionado localmente para evitar ruido de navegacao/cookies | 2026-06-29 |
| CONFAZ - Convenios ICMS 2026 | https://www.confaz.fazenda.gov.br/legislacao/convenios/2026/CV062_26 | 200 | `CONVENIO ICMS 62/26` ja coberto localmente | 2026-06-29 |
| CONFAZ - Ajustes SINIEF 2026 | https://www.confaz.fazenda.gov.br/legislacao/ajustes/2026/AJ016_26 | 200 | `AJUSTE SINIEF 16/26` ja coberto localmente | 2026-06-29 |
| CONFAZ - Protocolos ICMS 2026 | https://www.confaz.fazenda.gov.br/legislacao/protocolos/2026/protocolo-icms-52-26 | 200 | `PROTOCOLO ICMS 52/26` ja coberto localmente | 2026-06-29 |

## Achados

| Status | Achado | Impacto | Arquivo afetado | Publico | Provenance | Confianca |
| --- | --- | --- | --- | --- | --- | ---: |
| CORRIGIR/OK | A RFB publicou que a obrigatoriedade de inscricao no CNPJ por pessoas fisicas emissoras de documentos fiscais foi prorrogada para `01/01/2027` | acrescenta fonte federal operacional da Reforma Tributaria sem alterar card de beneficio | `scripts/legal_modules.py`, `data/legal_sources/reforma_tributaria/RFB_CGIBS_CNPJ_Pessoas_Fisicas_Documentos_Fiscais_2027.txt`, pagina federal gerada, busca, manifest e `llms.txt` | humano e IA | fonte primaria RFB HTTP 200 | 0.98 |
| CORRIGIR/OK | A pagina CGIBS do marco 03/08/2026 era lida ao vivo e trouxe ruido de navegacao/cookies em build adversarial | fonte foi versionada localmente e renderizada sem ruido | `data/legal_sources/reforma_tributaria/CGIBS_Marco_03082026_Campos_IBS_CBS.txt`, `scripts/legal_modules.py`, pagina federal gerada | humano e IA | fonte primaria CGIBS HTTP 200 + snapshot curado | 0.96 |
| CORRIGIR/OK | `state_legal_pages.py` usava `date.today()` como data editorial padrao de paginas estaduais | evitada falsa revalidacao de fontes estaduais nao revisitadas | `scripts/state_legal_pages.py` | humano e IA | revisao adversarial de diff | 0.95 |
| A VALIDAR | O fetch ao vivo do Anexo IX consolidado de Goias alterou texto/ancoras/contagens durante o build | exige rodada estadual propria antes de publicar qualquer mudanca GO | `estados/goias/legislacao/*.html` e registros GO em `portal-search-full.json` foram revertidos para a versao anterior | humano e IA | fonte oficial dinamica GO observada no build, sem auditoria linha a linha nesta rodada | 0.75 |
| OK | CONFAZ mais recente segue coberto: `CONVENIO ICMS 62/26`, `AJUSTE SINIEF 16/26`, `PROTOCOLO ICMS 52/26` | sem lacuna nova de indice CONFAZ | `data/confaz_ultimos_5_anos.json`, `confaz/ultimos-5-anos.html` | humano e IA | fonte primaria CONFAZ + busca local | 0.98 |

## Mudancas aplicadas com prova

| Id/arquivo | Campo alterado | De | Para | Prova |
| --- | --- | --- | --- | --- |
| `rfb-cgibs-cnpj-pessoas-fisicas-documentos-2027` | nova fonte federal | ausente | pagina, manifest, busca e `llms.txt` com fonte RFB | URL RFB HTTP `200`, publicada em 26/06/2026 |
| `cgibs-marco-03-08-2026-campos-ibs-cbs` | origem do texto | `fetch_url` ao vivo | `repo_files` versionado localmente | URL CGIBS HTTP `200`; teste adversarial sem `ACEITAR TODOS`/`Conteudo [1]` |
| `scripts/state_legal_pages.py` | data estadual padrao | `date.today()` | `RJC_STATE_LEGAL_UPDATED_ON` ou `26/06/2026` | impede falsa revalidacao automatica |
| `assets/portal-search-full.json` | registros Goias | cinco registros alterados pelo fetch vivo | cinco registros restaurados do `HEAD` | teste estruturado: zero `changed_goias` |

Nenhum card de beneficio foi promovido, alterado para `vigente` ou publicado com base em inferencia.

## Quarentena

Sem nova quarentena de card nesta rodada.

Achados em observacao editorial:

- `A VALIDAR`: URL CGIBS equivalente da prorrogacao CNPJ PF retornou HTTP `404`; nao linkar ate resolver.
- `A VALIDAR`: Anexo IX/GO consolidado mudou no fetch vivo; revisar em rodada estadual separada antes de atualizar paginas GO ou qualquer beneficio derivado.

## Gates

| Gate | Resultado | Evidencia |
| --- | --- | --- |
| `python -m compileall -q scripts` | OK | exit `0` |
| `python scripts/audit_portal.py` | OK | `Paginas HTML auditadas: 656`; sem falhas |
| `python scripts/audit_master_coverage.py` | OK | `15` requisitos federais, `27` estados, `9726` beneficios, `7050` linhas NCM, `3` familias CONFAZ |
| `python scripts/audit_benefit_cards.py` | OK | sem falhas |
| `python scripts/audit_card_scope_visible.py` | OK | contrato v2 visivel |
| `python scripts/audit_no_keyword_inference.py` | OK | nenhum keyword-only publico |
| `python scripts/audit_temporal_consistency.py` | OK | envelope temporal consistente |
| `python scripts/audit_link_health.py` | OK com warnings soft | `102` URLs unicas; nenhum `404/410` em beneficio publicado; warnings de SSL/reset/DNS/recusa semelhantes aos ledgers anteriores |
| `python scripts/audit_index_freshness.py` | OK | indices e HTML coerentes pelo `assets/build-freshness.json` |
| `python scripts/audit_quarantine_isolation.py` | OK | `13150` ids de quarentena isolados |
| `python scripts/audit_reforma_transition.py` | OK | `transicao_rt` presente |
| `python scripts/audit_divergence_html_json_search.py` | OK | convergencia entre HTML, JSON e busca |
| `python scripts/audit_editorial_date_per_card.py` | OK | data editorial derivada e `verificado_em` por card |
| `git diff --check` | OK | exit `0` |
| `rg -n "25/04/2026|\[\] \[\] \[\]|str\(\[" .` | OK com ressalva documental | ocorrencias apenas em ledgers historicos |

## Passe adversarial

Testes executaveis usados:

- `curl -L` nas URLs RFB/CGIBS/CONFAZ; resultado: RFB `200`, CGIBS CNPJ PF `404`, CGIBS marco 03/08 `200`, CONFAZ `200`.
- Python assertivo conferindo: nova fonte existe no TXT, HTML, `llms.txt`, `assets/llm-manifest.json`, `assets/portal-search.js`, `assets/portal-search-full.json`; HTML exibe `01/01/2027` e `Novembro de 2026`; URL RFB aparece no HTML; ruido `ACEITAR TODOS`, `ACEITAR NECESSARIOS`, `Conteudo [1]` e `Orgaos do Governo` nao vazou; registros Goias no `portal-search-full.json` nao mudaram; checksums de frescor batem.
- Reexecucao da bateria canonica v2.0 completa.

Resultado: `ADVERSARIAL_TESTS_OK`.

Defeitos derrubados pelo passe adversarial:

- A pagina CGIBS da prorrogacao CNPJ PF nao podia ser usada como prova publicada porque retornou `404`.
- O build ao vivo do CGIBS marco 03/08 vazava ruido de interface; corrigido por snapshot local curado.
- O build ao vivo de Goias alterava conteudo estadual fora do escopo revisado; isolado e registrado para revalidacao futura.

## Publicacao

Publicacao obrigatoriamente por PR, sem push direto em `main`.

Estado no momento de gravacao inicial deste ledger: PR a abrir apos commit dos artefatos validados.

## Pendencias humanas

- Revisar em rodada separada o Anexo IX/GO consolidado antes de publicar qualquer diferenca estadual observada no fetch vivo de 2026-06-29.

## Pendencias IA/LLM

- Nao usar a URL CGIBS da prorrogacao CNPJ PF enquanto retornar `404`; a ancora publicada e a RFB.
- Monitorar se o gerador deve substituir outros `fetch_url` estaduais por snapshots versionados quando a alteracao nao for objetivo da rodada.
