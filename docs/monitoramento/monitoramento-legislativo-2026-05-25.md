# Monitoramento legislativo semanal - 25/05/2026

Automacao: RJC Portal - atualizacao legislativa semanal  
Execucao: 25/05/2026, America/Sao_Paulo  
Repositorio: `C:\Users\kris2\OneDrive\Documentos\Playbook\rjc-conhecimento`

## Fontes oficiais consultadas

- Planalto: indices de leis, leis complementares, decretos e medidas provisorias de 2026.
- DOU/IN.gov e Receita Federal/SIJUT: busca por atos federais recentes e instrucoes normativas com impacto em IPI, PIS, Cofins, IRPJ, CSLL, IOF, importacao/exportacao e obrigacoes acessorias.
- SPED, Portal DF-e/SVRS, Ministerio da Fazenda e CGIBS: verificacao de Reforma Tributaria, CST, cClassTrib, cCredPres, documentos fiscais e orientacoes 2026.
- CONFAZ: comparacao viva dos indices de convenios, ajustes SINIEF e protocolos ICMS contra o cache local dos ultimos 5 anos.
- Secretarias de Fazenda/Receita das 27 UFs: varredura dos portais oficiais cadastrados em `STATE_OFFICIAL_PORTALS`, com foco em ICMS, beneficios, cBenef, NCM, ST, fundos, regimes especiais, importacao e obrigacoes acessorias.
- Evidencia tecnica leve da varredura de URLs-base: `docs/monitoramento/fontes-oficiais-scan-2026-05-25.json` com 43 endpoints oficiais testados; 27 responderam diretamente, e bloqueios/timeouts ficaram registrados como pendencia de acesso, nao como prova de ausencia de ato.

## Resultado CONFAZ

Comparacao viva com os indices oficiais:

- Convenios ICMS: local 874, vivo 874, novos 0.
- Ajustes SINIEF: local 161, vivo 161, novos 0.
- Protocolos ICMS: local 318, vivo 318, novos 0.

Sem atualizacao objetiva no indice CONFAZ nesta rodada.

## Atos novos ou modificadores com impacto objetivo

| Fonte | Data | Hash SHA256 | Tratamento |
| --- | --- | --- | --- |
| [IN RFB 2.324/2026](https://normas.receita.fazenda.gov.br/sijut2consulta/link.action?antigo=1&idAto=150886) | 24/04/2026, DOU 05/05/2026 | HTML oficial `15b53e8a8ef950fcdfe1339311697261a1b1bd81c1741518fbf9d65ed71cec86`; texto capturado `abcd6556619832859d0d6fec4263441264d2331a0ff6f52bc8043019887d7f34` | Aplicado. Disciplina hipoteses de suspensao do IPI previstas nas Leis 9.826/1999 e 10.637/2002, com condicoes, declaracoes, registro e informacao expressa em nota fiscal. |

## Sinais revisados sem publicacao aplicada

- CGIBS publicou comunicacao sobre prazo de adequacao dos sistemas de emissao de notas fiscais ao regulamento do IBS; o texto remete ao Ato Conjunto RFB/CGIBS 1/2025, ja publicado no portal, sem ato normativo novo a incorporar nesta rodada.
- Planalto trouxe atos recentes em maio de 2026, mas sem mudanca objetiva adicional para as paginas tributarias ja publicadas nesta execucao. A MPV 1.358/2026 e o Decreto 12.974/2026 continuam como pendencia anterior por exigirem modulo setorial de combustiveis/subvencao antes de leitura aplicada.
- Portal DF-e/SVRS segue indicando Tabela CST/cClassTrib de 15/04/2026 e cCredPres de 12/12/2025, ambas ja tratadas no portal.
- Nos portais estaduais, nao foi identificado ato novo seguro para aplicacao automatica alem da manutencao das pendencias ja registradas; endpoints com bloqueio/timeouts na captura tecnica ficaram listados no JSON de varredura para nova tentativa.

## Alteracoes aplicadas

- Criada fonte versionada em `data/legal_sources/federal/IN_RFB_2324_2026_IPI_Suspensao.txt`, com URL oficial, data de captura e hashes do HTML oficial e do texto local.
- Atualizado `scripts/legal_modules.py`:
  - `UPDATED_ON = "25/05/2026"`;
  - nova fonte `in-rfb-2324-2026-ipi-suspensao`;
  - modulo de IPI passou a usar a fonte no capitulo `suspensoes-isencoes`;
  - analise do capitulo passou a registrar requisitos objetivos da IN RFB 2.324/2026.
- Atualizado `scripts/validated_benefits.py` para permitir que a fonte federal de IPI alimente a matriz de beneficios quando houver gancho operacional expresso.
- Exportado `data/legal_sources_registry.json`, agora com 206 fontes.
- Regeneradas as bases derivadas:
  - `data/benefits_crosswalk.json`: 12.246 entradas, 2.389 com NCM, 2.259 com cBenef, 203 com CST;
  - `data/ncm_benefits_index.json`: 7.976 linhas, 1.381 NCMs, 15 jurisdicoes.
- Regenerado o portal completo, incluindo pagina nova `federal/legislacao/atos/in-rfb-2324-2026-ipi-suspensao.html`, pagina de IPI, busca, sitemap, `llms.txt` e manifesto LLM.

## Auditorias executadas

- `portal_monitor.py --live` inicial: sem critico/alto; medio ja conhecido para `data/benefits_crosswalk.json` acima de 50 MB.
- `python scripts/export_legal_registry.py`: registro exportado com 206 fontes.
- `python scripts/build_master_indexes.py`: taxonomia, cobertura, matriz de beneficios e CONFAZ regenerados.
- `python scripts/build_ncm_benefits_index.py`: indice NCM regenerado com 7.976 linhas.
- `python scripts/build_portal.py`: portal regenerado; processo concluiu apos execucao longa por causa da matriz grande.
- `python -m compileall -q scripts`: sem erro.
- `python scripts/audit_master_coverage.py`: sem falhas estruturais.
- `python scripts/audit_state_source_quality.py`: auditoria estadual regravada.
- `python -X dev scripts/audit_portal.py`: 645 paginas HTML auditadas, sem falhas.
- `portal_monitor.py --live` pos-atualizacao: sem critico/alto; medios apenas worktree suja antes do commit e `data/benefits_crosswalk.json` acima de 50 MB.

Relatorios salvos:

- `docs/monitoramento/portal-monitor-2026-05-25.md`
- `docs/monitoramento/portal-monitor-2026-05-25-pos-atualizacao.md`
- `docs/monitoramento/fontes-oficiais-scan-2026-05-25.json`

## Pendencias reais

- Dividir ou paginar `data/benefits_crosswalk.json`, que segue acima de 50 MB e deixa `build_portal.py` lento.
- Criar modulo federal/setorial para combustiveis e subvencoes antes de aplicar MPV 1.358/2026 e Decreto 12.974/2026.
- Definir modelo de dados para pautas/valores estaduais antes de integrar INs estaduais de pauta por produto.
- Localizar texto normativo oficial completo da Bahia para Liquida Bahia 2026 antes de qualquer publicacao aplicada.
- Recapturar/curar pacote do Acre antes de publicar atos profundos do Estado.
- Revalidar endpoints estaduais com bloqueio/timeouts no scan: MA, PI, RJ, RN, RO e RS.
- Validar indexacao real via Search Console; a auditoria confirma indexabilidade tecnica, nao indexacao efetiva.
