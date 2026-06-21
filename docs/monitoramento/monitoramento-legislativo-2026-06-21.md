# Monitoramento legislativo - 2026-06-21

## Escopo

Rodada dedicada a criar a secao `PIS/Cofins por NCM`, com banco profundo em `G:\Meu Drive\RJC\BD_LEGISLACAO\PIS_COFINS_NCM`, dados publicos NDJSON, paginas HTML, busca, manifest, `llms.txt`, sitemap e auditorias especificas.

Status literal da rodada: `CONCLUIDO COM RESSALVA`. A base inicial foi publicada localmente com registros validados e gates verdes, mas nao deve ser chamada de exaustiva enquanto o inventario expandido de PIS/Cofins por produto/aplicacao nao for integralmente percorrido.

## Fontes conferidas

Todas abaixo retornaram HTTP 200 no crawler de 2026-06-21 e foram gravadas com hash bruto e normalizado no banco profundo.

| Fonte | URL oficial | HTTP | Papel | Resultado |
|---|---|---:|---|---|
| Lei 10.147/2000 | https://www.planalto.gov.br/ccivil_03/leis/l10147.htm | 200 | dispositiva | OK |
| Lei 10.485/2002 | https://www.planalto.gov.br/ccivil_03/leis/2002/l10485.htm | 200 | dispositiva | OK |
| Lei 10.865/2004 | https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2004/lei/l10.865.htm | 200 | dispositiva | OK |
| Lei 10.925/2004 | https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2004/lei/l10.925.htm | 200 | dispositiva | OK |
| Lei 12.839/2013 | https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2013/Lei/L12839.htm | 200 | dispositiva/alteradora | OK |
| Lei 13.097/2015 | https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/L13097.htm | 200 | dispositiva/alteradora | OK |
| Decreto 5.195/2004 | https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2004/decreto/d5195.htm | 200 | regulamentar | OK |
| Decreto 5.630/2005 | https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2005/decreto/d5630.htm | 200 | regulamentar | OK |
| Decreto 6.426/2008 | https://www.planalto.gov.br/ccivil_03/_ato2007-2010/2008/decreto/d6426.htm | 200 | regulamentar | OK |
| Decreto 6.707/2008 | https://www.planalto.gov.br/ccivil_03/_ato2007-2010/2008/Decreto/D6707.htm | 200 | historica/regulamentar | fora do publico quando historico sem publicacao atual |
| Decreto 8.442/2015 | https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/decreto/D8442.htm | 200 | regulamentar | OK |
| Decreto 12.991/2026 | https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2026/decreto/d12991.htm | 200 | regulamentar | sem linha publica neste lote |
| Lei 15.394/2026 | https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2026/lei/L15394.htm | 200 | dispositiva | sem linha publica neste lote |
| Portaria RFB 688/2026 | https://normas.receita.fazenda.gov.br/sijut2consulta/link.action?idAto=151652 | 200 | inventario/controle | quarentena; nao dispositiva autonoma |

## Achados e mudancas aplicadas

| Achado | Impacto | Arquivo/artefato | Status |
|---|---|---|---|
| Necessidade de base PIS/Cofins por NCM com registro autodescritivo | Humano e LLM | `data/pis-cofins/ncm.ndjson` | OK |
| Necessidade de quarentena isolada para candidatos sem prova plena | Humano e LLM | `data/pis-cofins/quarentena.ndjson` local/ignorado pelo Git e banco profundo em `G:` | OK |
| Necessidade de pagina didatica e tabela pesquisavel | Humano | `federal/pis-cofins-ncm.html`, `federal/legislacao/pis-cofins/ncm.html` | OK |
| Necessidade de descoberta por LLM/busca | LLM | `llms.txt`, `assets/llm-manifest.json`, `assets/portal-search-full.json`, `sitemap.xml` | OK |
| Build completo reescreve paginas antigas com data gerada de 21/06/2026 | Revisao de PR | HTML gerado em massa | OK; diff esperado do build |

## Base gerada

| Medida | Valor |
|---|---:|
| Fontes capturadas | 14 |
| Linhas publicaveis | 291 |
| NCM/codigos unicos | 140 |
| Candidatos em quarentena | 183 |
| `verificado_em` | 2026-06-21 |

Distribuicao por tratamento:

| Tratamento | Linhas |
|---|---:|
| `credito_presumido` | 124 |
| `aliquota_zero` | 76 |
| `tratamento_especifico` | 32 |
| `monofasico` | 30 |
| `suspensao` | 25 |
| `isencao` | 4 |

Distribuicao por fonte com linha publica:

| Fonte | Linhas |
|---|---:|
| Lei 10.485/2002 | 72 |
| Lei 10.925/2004 | 64 |
| Lei 10.865/2004 | 45 |
| Lei 10.147/2000 | 44 |
| Decreto 6.426/2008 | 22 |
| Lei 12.839/2013 | 21 |
| Decreto 5.630/2005 | 12 |
| Decreto 5.195/2004 | 9 |
| Lei 13.097/2015 | 2 |

## Gates

| Gate | Resultado | Evidencia |
|---|---|---|
| `python -m compileall -q scripts` | OK | exit 0 |
| `python scripts\build_pis_cofins_ncm.py` | OK | 14 fontes, 291 publicaveis, 183 quarentena |
| `python scripts\audit_pis_cofins_ncm.py` | OK | `OK: 291 public PIS/Cofins NCM rows; 183 quarantine rows isolated.` |
| `python scripts\audit_pis_cofins_ncm_adversarial.py` | OK | `{"status": "OK", "adversarial_cases": 8}` |
| `python scripts\build_portal.py` | OK | `Portal generated successfully.` em aproximadamente 399s |
| `python scripts\audit_portal.py` | OK | 654 paginas HTML auditadas |
| `python scripts\audit_master_coverage.py` | OK | requisitos federais, Estados, beneficios, NCM e CONFAZ sem falhas estruturais |
| `python scripts\audit_benefit_cards.py` | OK | cards de beneficios sem falhas |
| `python scripts\audit_card_scope_visible.py` | OK | contrato v2 visivel nos cards publicos |
| `python scripts\audit_no_keyword_inference.py` | OK | nenhum beneficio publico depende de keyword-only |
| `python scripts\audit_temporal_consistency.py` | OK | envelopes temporais consistentes |
| `python scripts\audit_link_health.py` | OK com avisos soft | 103 URLs unicas; nenhum 404/410 em beneficio publicado |
| `python scripts\audit_index_freshness.py` | OK | indices e HTML regenerados no mesmo build |
| `python scripts\audit_quarantine_isolation.py` | OK | 13137 ids de quarentena verificados fora dos artefatos publicos |
| `python scripts\audit_reforma_transition.py` | OK | tributos legados com transicao_rt |
| `python scripts\audit_divergence_html_json_search.py` | OK | HTML, JSON e busca convergem para beneficios publicados |
| `python scripts\audit_editorial_date_per_card.py` | OK | data editorial derivada e `verificado_em` por card |
| Prova direta PIS/Cofins id x HTML x busca | OK | 291 ids; 0 ausentes no HTML; 0 ausentes no `portal-search-full.json` |
| Prova direta LLM | OK | `llms.txt` inclui pagina, NDJSON e indice; manifest inclui landing e tabela |
| `git diff --check` | OK | exit 0; apenas warnings de CRLF |
| `rg -n "25/04/2026|\[\] \[\] \[\]|str\(\[" .` | OK | exit 1 por ausencia de matches |

## Avisos soft de link health

`audit_link_health.py` registrou falhas transitorias/SSL/conexao em algumas fontes estaduais e externas ja existentes, mas nao retornou 404/410 em beneficio publicado. Exemplos: certificado em URLs de BA/ES/RN, conexao recusada em SEFAZ ES, host remoto fechando conexao em RJ/RS/CGIBS. Status: `A REVALIDAR` em rodada futura, sem bloqueio automatico.

## Quarentena

`data/pis-cofins/quarentena.ndjson` contem 183 candidatos no workspace local e foi incluido em `.gitignore`, para nao virar artefato publico do Pages. Motivos principais: fonte de inventario nao dispositiva, candidato sem NCM extraido, historico/regra nao publicavel, baixa confianca ou necessidade de revisao humana. Nenhum id de quarentena entra em HTML publico, `llms.txt`, manifest, sitemap ou busca.

## Passe adversarial

Teste executavel: `scripts/audit_pis_cofins_ncm_adversarial.py`.

Casos que precisam falhar e falharam:

- id de quarentena em base publica;
- baixa confianca publicada;
- link oficial quebrado;
- `inicio_eficacia` ausente;
- descricao curta demais para tabela humana;
- provenance `keyword_only`;
- transicao CBS ausente;
- codigo suspeito/data/artigo sem trecho legal suficiente.

Resultado: 8 casos adversariais, status OK.

## Pendencias humanas

- Revisar semanticamente as descricoes legais mais truncadas antes de usar a base como cadastro ERP.
- Ampliar inventario para IN RFB 2.121/2022 completa, tabelas EFD-Contribuicoes 4.3.10 a 4.3.17, TIPI/NCM oficial, DIRBI/transparencia RFB e leis setoriais adicionais.
- Nao afirmar "legislacao completa" ate existir inventario exaustivo com cobertura/faltantes.

## Pendencias IA/LLM

- Enriquecer `descricao_tipi` por fonte TIPI/NCM oficial.
- Criar auditoria especifica de convergencia PIS/Cofins HTML x NDJSON x busca dentro da bateria canonica, hoje coberta por prova direta.
- Separar paginas futuras por recorte: monofasico, aliquota zero, setores e importacao.

## Publicacao

Politica aplicavel: conteudo via PR, nunca direto em `main`.

Status: PR aberto em https://github.com/mjrrafael/rjc-conhecimento/pull/10, convertido para ready e mergeado em `main`.

Commit inicial da secao: `eb808cc`.

Merge/publicacao: `99b8fe1` - `[codex] Atualiza portal tributario - 2026-06-21`.

Run Pages: `27913604935`, concluido com sucesso em 2026-06-21.

Verificacao HTTP publica:

| URL | HTTP | Evidencia |
|---|---:|---|
| https://mjrrafael.github.io/rjc-conhecimento/federal/pis-cofins-ncm.html | 200 | landing publicada |
| https://mjrrafael.github.io/rjc-conhecimento/federal/legislacao/pis-cofins/ncm.html | 200 | tabela publicada |
| https://mjrrafael.github.io/rjc-conhecimento/data/pis-cofins/ncm.ndjson | 200 | 291 linhas remotas; schema `rjc-pis-cofins-ncm-v1` |
| https://mjrrafael.github.io/rjc-conhecimento/data/pis-cofins/ncm-index.json | 200 | 291 linhas publicadas, 140 NCM/codigos unicos, 183 candidatos locais em quarentena |
| https://mjrrafael.github.io/rjc-conhecimento/llms.txt | 200 | entrada PIS/Cofins por NCM presente |
| https://mjrrafael.github.io/rjc-conhecimento/data/pis-cofins/quarentena.ndjson | 404 | quarentena nao publicada |
