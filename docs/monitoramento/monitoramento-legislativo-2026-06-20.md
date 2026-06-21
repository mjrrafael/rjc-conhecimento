# Monitoramento legislativo - 2026-06-20

## Fontes conferidas
- CGIBS: https://www.cgibs.gov.br/novo-marco-da-reforma-tributaria-inicia-em-03-de-agosto-com-preenchimento-obrigatorio-dos-campos-relativos-ao-ibs-e-a-cbs - HTTP 200 - ultima norma/comunicado visto: noticia institucional publicada em 2026-06-15 fixando marco operacional de 2026-08-03 para exigencia sistemica dos campos IBS/CBS.
- Receita Federal: https://www.gov.br/receitafederal/pt-br/assuntos/noticias/2026/junho/receita-federal-esclarece-as-regras-para-uso-de-creditos-de-pis-cofins-na-transicao-para-a-cbs - HTTP 200 - ultima orientacao vista: noticia de 2026-06-03 sobre creditos de PIS/Cofins na transicao para a CBS, sem novo ato normativo primario identificado nesta rodada.
- Auditoria automatica de links oficiais publicada localmente: `python scripts/audit_link_health.py` em 2026-06-20 - sem 404/410 em card publicado; soft warnings remanescentes em BA, ES, CGIBS, MS, RJ, RN e RS.

## Achados
- URL oficial: https://www.cgibs.gov.br/novo-marco-da-reforma-tributaria-inicia-em-03-de-agosto-com-preenchimento-obrigatorio-dos-campos-relativos-ao-ibs-e-a-cbs
  - data: 2026-06-15
  - ato: comunicado oficial CGIBS sobre implementacao operacional IBS/CBS
  - impacto: a formula do art. 3o do Ato Conjunto 1/2025 passou a ter data operacional explicita no portal: 03/08/2026 para exigencia sistemica dos campos IBS/CBS no regime regular, com rejeicao de documentos incompletos
  - arquivo afetado: `scripts/legal_modules.py` e paginas federais derivadas da trilha de reforma tributaria
  - publico: ambos
  - provenance: ato_oficial
  - confianca: 0.99
  - status: OK
- URL oficial: https://www.gov.br/receitafederal/pt-br/assuntos/noticias/2026/junho/receita-federal-esclarece-as-regras-para-uso-de-creditos-de-pis-cofins-na-transicao-para-a-cbs
  - data: 2026-06-03
  - ato: noticia/orientacao RFB
  - impacto: rechecado; permanece sem mudanca normativa primaria adicional a publicar nesta rodada
  - arquivo afetado: nenhum
  - publico: ambos
  - provenance: noticia_oficial_sem_novo_ato
  - confianca: 0.84
  - status: OK
- Workspace local:
  - data: 2026-06-20
  - ato: n/a
  - impacto: 154 arquivos `estados/*/legislacao/fontes/*.html` ja vinham alterados apenas por refresh de data editorial (`17/06/2026` -> `19/06/2026`), sem outra divergencia de conteudo detectada na amostra automatizada
  - arquivo afetado: varias fontes estaduais
  - publico: ambos
  - provenance: auditoria_local
  - confianca: 0.95
  - status: CONCLUIDO COM RESSALVA

## Mudancas aplicadas com prova
- id card: `cgibs-marco-03-08-2026-campos-ibs-cbs`
  - campo alterado: novo ato/fonte e pagina derivada
  - de: inexistente
  - para: comunicado oficial CGIBS incorporado ao acervo federal e aos materiais de reforma tributaria
  - ato/link: https://www.cgibs.gov.br/novo-marco-da-reforma-tributaria-inicia-em-03-de-agosto-com-preenchimento-obrigatorio-dos-campos-relativos-ao-ibs-e-a-cbs
  - verificado_em: 2026-06-20
- id card: `documentos-obrigacoes-2026-ato-conjunto`
  - campo alterado: analise editorial
  - de: formula legal sem data operacional explicita do CGIBS
  - para: registro expresso de que 03/08/2026 e o marco operacional informado pelo CGIBS, com rejeicao de documentos incompletos
  - ato/link: https://www.cgibs.gov.br/novo-marco-da-reforma-tributaria-inicia-em-03-de-agosto-com-preenchimento-obrigatorio-dos-campos-relativos-ao-ibs-e-a-cbs
  - verificado_em: 2026-06-20
- id card: `orientacoes-operacionais-reforma-2026`
  - campo alterado: analise editorial
  - de: cronograma descrito apenas pela formula normativa
  - para: cronograma com data operacional concreta 03/08/2026 suportada por fonte oficial primaria do CGIBS
  - ato/link: https://www.cgibs.gov.br/novo-marco-da-reforma-tributaria-inicia-em-03-de-agosto-com-preenchimento-obrigatorio-dos-campos-relativos-ao-ibs-e-a-cbs
  - verificado_em: 2026-06-20

## Quarentena
- nenhum novo id enviado para quarentena nesta rodada

## Gates
- `python -m compileall -q scripts`: OK
- `python scripts/audit_portal.py`: OK - 652 paginas HTML auditadas
- `python scripts/audit_master_coverage.py`: OK - 9727 beneficios e 7050 linhas NCM auditadas
- `python scripts/audit_benefit_cards.py`: OK
- `python scripts/audit_card_scope_visible.py`: OK
- `python scripts/audit_no_keyword_inference.py`: OK
- `python scripts/audit_temporal_consistency.py`: OK
- `python scripts/audit_link_health.py`: OK com soft warnings - 103 URLs oficiais unicas verificadas; nenhum 404/410 em beneficio publicado
- `python scripts/audit_index_freshness.py`: OK
- `python scripts/audit_quarantine_isolation.py`: OK - 13137 ids verificados
- `python scripts/audit_reforma_transition.py`: OK
- `python scripts/audit_divergence_html_json_search.py`: OK
- `python scripts/audit_editorial_date_per_card.py`: OK
- `git diff --check`: OK
- busca final de ruidos historicos (data editorial antiga de abril/2026, listas vazias serializadas e serializacao textual de listas): OK na rerrodagem; a primeira passada acusou apenas o proprio arquivo temporario de log da bateria

## Pendencias humanas
- Abrir PR de conteudo com titulo canonico `[codex] Atualiza portal tributario - 2026-06-20`; esta rodada deixou patch local e evidencias, mas nao publicou em `main`.
- Decidir o tratamento dos arquivos duplicados nao rastreados com sufixo ` (1)` para evitar ruido recorrente no workspace.

## Pendencias IA/LLM
- Reverificar os links oficiais com falha transitoria/SSL de BA, ES, CGIBS, MS, RJ, RN e RS em proxima rodada; seguem como soft gate e nao invalidaram card publicado nesta execucao.
- Monitorar se o comunicado operacional do CGIBS sera convertido em ato normativo estruturado adicional; se houver, substituir a noticia por ancora normativa ainda mais forte no acervo.

## Passe adversarial
- teste 1: script executavel de presenca cruzada da data `03/08/2026` em HTML, `assets/portal-search.js`, `assets/portal-search-full.json`, `llms.txt` e `assets/build-freshness.json`
  - resultado: OK
- teste 2: `python scripts/audit_divergence_html_json_search.py`
  - resultado: OK
- teste 3: `python scripts/audit_index_freshness.py`
  - resultado: OK
- teste 4: `python scripts/audit_link_health.py`
  - resultado: OK com warnings soft preexistentes/externos; nenhum 404/410 em card publicado
- defeitos novos abertos: nenhum

## Publicacao
- commit/PR: PR #8 - https://github.com/mjrrafael/rjc-conhecimento/pull/8 - merge squash em `f951c4f5095f2bf3ed8396e1b0dd21d63161f029`
- run do Pages: https://github.com/mjrrafael/rjc-conhecimento/actions/runs/27911232574 - sucesso em 2026-06-21
- verificacao HTTP publica:
  - https://mjrrafael.github.io/rjc-conhecimento/federal/legislacao/atos/cgibs-marco-03-08-2026-campos-ibs-cbs.html - HTTP 200 com `03/08/2026`
  - https://mjrrafael.github.io/rjc-conhecimento/assets/build-freshness.json - HTTP 200 com `2026-06-20T03:14:07`
  - https://mjrrafael.github.io/rjc-conhecimento/llms.txt - HTTP 200 com `cgibs-marco-03-08-2026-campos-ibs-cbs`
  - https://mjrrafael.github.io/rjc-conhecimento/assets/llm-manifest.json - HTTP 200 com `cgibs-marco-03-08-2026-campos-ibs-cbs`
  - https://mjrrafael.github.io/rjc-conhecimento/assets/portal-search.js - HTTP 200 com `CGIBS - marco operacional de 03/08/2026`
  - https://mjrrafael.github.io/rjc-conhecimento/docs/monitoramento/monitoramento-legislativo-2026-06-20.md - HTTP 200 com o ledger da rodada antes deste registro final de publicacao
