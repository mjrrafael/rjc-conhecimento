# Monitoramento legislativo - 2026-06-24

## Escopo

Rodada de monitoramento focada em:

- reexecutar a bateria canonica local do portal;
- verificar se houve norma oficial nova desde o ledger de 2026-06-23;
- decidir se existia publicacao segura nesta worktree.

Status literal da rodada: `BLOQUEADO`.

Motivo do bloqueio: existe fonte oficial nova material para a trilha da Reforma Tributaria, mas a worktree local esta massivamente alterada em arquivos gerados/publicos. Regenerar HTML, busca e manifest agora poderia sobrescrever trabalho alheio sem isolamento previo de branch/worktree.

## Criterios de pronto da rodada

| # | Criterio de pronto | Metodo | Status | Evidencia |
| --- | --- | --- | --- | --- |
| 1 | Reexecutar os hard gates canonicos e registrar se o estado local ainda e coerente | testes automatizados locais | OK | bateria abaixo com todos os auditores principais em `0` |
| 2 | Confirmar se houve fonte oficial nova apos o ledger de 2026-06-23 | confronto com fonte primaria oficial | OK | CGIBS publicou `ATO CONJUNTO RFB/CGIBS Nº 3, DE 19 DE JUNHO DE 2026`, noticia de 22/06/2026 e PDF oficial |
| 3 | Verificar se a fonte nova ja estava incorporada no repositório | busca textual integral + confronto com paginas federais atuais | OK | inexistencia de `ato-conjunto-rfb-cgibs-3-2026` local e ausencia do ato nas paginas da trilha federal |
| 4 | Publicar ou deixar bloqueio com causa concreta | revisao adversarial de risco de sobrescrita | BLOQUEADO | `git status --short` mostra worktree ampla e arquivos publicos/scritps duplicados com ` (1)` |

## Fontes oficiais conferidas

| Fonte | URL | HTTP | Ultima norma vista | Data verificada |
| --- | --- | ---: | --- | --- |
| CGIBS - Atos Conjuntos | https://www.cgibs.gov.br/atos-conjuntos | 200 | `ATO CONJUNTO RFB/CGIBS Nº 3, DE 19 DE JUNHO DE 2026` | 2026-06-24 |
| CGIBS - noticia DeRE | https://www.cgibs.gov.br/comite-gestor-do-ibs-e-receita-federal-publicam-ato-conjunto-n-3-2026-com-nova-etapa-da-documentacao-da-dere | 200 | noticia publicada em `22/06/2026 15:04` | 2026-06-24 |
| CGIBS - PDF do Ato 3/2026 | https://www.cgibs.gov.br/upload/arquivos/202606/22083423-ato-conjunto-nro-3-dere.pdf | 200 | versao oficial 1.1.0 da documentacao tecnica da DeRE | 2026-06-24 |
| CONFAZ - home | https://www.confaz.fazenda.gov.br/ | 200 | vitrine segue com itens de `12/06/2026`, `10/06/2026`, `29/05/2026` e `26/05/2026` | 2026-06-24 |
| Receita Federal - programa RTC | https://www.gov.br/receitafederal/pt-br/acesso-a-informacao/acoes-e-programas/programas-e-atividades/reforma-tributaria-do-consumo | 200 | noticias visiveis sem nova norma material alem da janela ja monitorada | 2026-06-24 |

## Achados

| Status | Achado | Impacto | Arquivo afetado | Publico | Provenance | Confianca |
| --- | --- | --- | --- | --- | --- | ---: |
| OK | Todos os hard gates principais de integridade e convergencia passaram novamente no estado local atual | o portal local segue coerente do ponto de vista dos auditores | artefatos publicos atuais | ambos | teste executavel local | 0.99 |
| CORRIGIR | O portal ainda nao materializa o `ATO CONJUNTO RFB/CGIBS Nº 3, DE 19 DE JUNHO DE 2026`, embora a fonte oficial ja exista | lacuna na trilha federal da Reforma para documentacao tecnica da DeRE | `scripts/legal_modules.py`, `data/legal_sources_registry.json`, `federal/legislacao/atos/*`, paginas de Reforma geradas | ambos | fonte primaria CGIBS | 0.98 |
| BLOQUEADO | A worktree contem centenas de arquivos publicos modificados e duplicatas com sufixo ` (1)`; rebuild agora e inseguro sem isolamento | risco real de sobrescrever trabalho alheio e produzir diff impossivel de auditar | HTML publico, docs e scripts | ambos | `git status --short` e lista de arquivos | 0.99 |
| A_VALIDAR | `audit_link_health.py` segue com warnings soft de SSL, timeout, reset e DNS em BA, ES, MS, RJ, RN, RS, SP e CGIBS; sem `404/410` em beneficio publicado | nao bloqueou a integridade, mas permanece fila de revalidacao | fontes oficiais remotas | ambos | teste local de link health | 0.90 |

## Fonte nova identificada

### ATO CONJUNTO RFB/CGIBS Nº 3, DE 19 DE JUNHO DE 2026

- Fonte oficial do indice: `https://www.cgibs.gov.br/atos-conjuntos`
- Fonte oficial do PDF: `https://www.cgibs.gov.br/upload/arquivos/202606/22083423-ato-conjunto-nro-3-dere.pdf`
- Noticia oficial: `https://www.cgibs.gov.br/comite-gestor-do-ibs-e-receita-federal-publicam-ato-conjunto-n-3-2026-com-nova-etapa-da-documentacao-da-dere`
- Conteudo nuclear confirmado no PDF oficial:
  - autoriza a publicacao da documentacao tecnica da DeRE na versao `1.1.0`;
  - lista `MOD`, `Leiautes`, `Anexo I - Tabelas`, `Anexo II - Regras de Validacao` e `XSD`;
  - integra pacote tecnico para desenvolvedores na versao `1.0.0`;
  - ratifica as versoes preliminares `1.0.0` e `1.0.1`;
  - produz efeitos a partir da publicacao.

## Gates executados

| Gate | Resultado | Evidencia |
| --- | --- | --- |
| `python -m compileall -q scripts` | OK | exit `0` |
| `python scripts/audit_portal.py` | OK | `Paginas HTML auditadas: 655` |
| `python scripts/audit_master_coverage.py` | OK | `15` requisitos federais; `27` estados; `9727` beneficios; `7050` linhas NCM |
| `python scripts/audit_benefit_cards.py` | OK | sem falhas |
| `python scripts/audit_card_scope_visible.py` | OK | contrato v2 visivel |
| `python scripts/audit_no_keyword_inference.py` | OK | sem keyword-only publico |
| `python scripts/audit_temporal_consistency.py` | OK | envelopes consistentes |
| `python scripts/audit_link_health.py` | OK com warnings soft | `103` URLs unicas; nenhum `404/410` em beneficio publicado |
| `python scripts/audit_index_freshness.py` | OK | indices e HTML no mesmo build |
| `python scripts/audit_quarantine_isolation.py` | OK | `13137` ids isolados |
| `python scripts/audit_reforma_transition.py` | OK | `transicao_rt` presente |
| `python scripts/audit_divergence_html_json_search.py` | OK | HTML, JSON e busca convergem |
| `python scripts/audit_editorial_date_per_card.py` | OK | data editorial derivada e `verificado_em` presentes |
| `git diff --check` | OK com ressalva | exit `0`; apenas avisos de CRLF do Git |
| `rg -n "25/04/2026|\[\] \[\] \[\]|str\(\[" .` | OK com ressalva documental | unico match veio do proprio ledger de `2026-06-23`, nao de artefato publico material |

## Passe adversarial

Pergunta adversarial usada:

> O que derruba a conclusao de que esta rodada esta pronta para publicar?

Teste executavel usado:

- bateria canonica local de hard gates;
- `git status --short`;
- `rg -n "Ato Conjunto RFB/CGIBS 3|ato-conjunto-rfb-cgibs-3|DeRE" federal assets data llms.txt docs`.

Resultado:

- os hard gates nao derrubaram a integridade do portal atual;
- a busca local confirmou lacuna editorial do Ato 3/2026;
- `git status --short` derrubou a possibilidade de rebuild/publicacao segura nesta rodada, porque a tree publica esta suja demais para regeneracao sem risco de sobrescrita.

## Pendencias humanas

- Isolar a automacao em branch/worktree limpa antes de incorporar o `ATO CONJUNTO RFB/CGIBS Nº 3/2026`.
- Revisar a origem das duplicatas com sufixo ` (1)` em `scripts/`, `docs/monitoramento/` e `beneficios/`.

## Pendencias IA/LLM

- Capturar e versionar o texto oficial do `ATO CONJUNTO RFB/CGIBS Nº 3/2026` em `data/legal_sources/reforma_tributaria/`.
- Declarar a nova fonte em `scripts/legal_modules.py` e regenerar as paginas federais da Reforma em ambiente limpo.
- Reexecutar a bateria canonica apos o rebuild e, se tudo passar, abrir PR de conteudo com prova primaria no corpo.

## Publicacao

Nenhuma publicacao foi feita nesta rodada.

Politica aplicada:

- sem PR e sem isolamento da worktree, nao houve atualizacao de conteudo publico;
- a rodada fecha bloqueando publicacao, nao mascarando a lacuna da fonte nova.

## Atualizacao complementar - 2026-06-24 07:35 -03

### Evidencia nova desta segunda passada

- A bateria canonica foi reexecutada integralmente nesta rodada e permaneceu verde: todos os hard gates sairam com `exit 0`.
- A confirmacao externa na fonte oficial do CGIBS mostrou que, em `24/06/2026`, a pagina [`https://www.cgibs.gov.br/atos-conjuntos`](https://www.cgibs.gov.br/atos-conjuntos) continua listando o `ATO CONJUNTO RFB/CGIBS Nº 3, DE 19 DE JUNHO DE 2026` como ato mais recente do bloco relevante.
- A noticia oficial do CGIBS permanece publicada em `22/06/2026 15:04`, confirmando a disponibilizacao da versao `1.1.0` da documentacao tecnica da DeRE.
- `git status --short | Measure-Object` retornou `343` entradas alteradas na worktree.
- As duplicatas com sufixo ` (1)` continuam presentes em `beneficios/`, `docs/monitoramento/` e `scripts/`, reforcando o risco de sobrescrita.

### Passe adversarial complementar

Pergunta adversarial:

> Se os gates passaram, o que ainda impede publicar?

Testes executados:

- reexecucao da ordem canonica completa;
- verificacao externa do CGIBS para confirmar se o Ato 3/2026 continua sendo a fonte nova material;
- `git status --short | Measure-Object`;
- `git status --short | Select-String ' \\(1\\)'`.

Resultado:

- os gates continuam sem apontar defeito estrutural no portal atual;
- a fonte oficial nova continua ausente da materializacao local;
- a worktree continua impropria para rebuild seguro, logo o bloqueio permanece valido por evidencia nova, nao por heranca da rodada anterior.

## Atualizacao complementar - 2026-06-24 13:39 -03

### Premissa corrigida

O trabalho local foi reclassificado como produzido por secoes anteriores do proprio Codex, nao como trabalho alheio. Com essa premissa, a decisao operacional mudou: as alteracoes locais poderiam ser consolidadas desde que passassem por auditoria integral e comparacao com o portal publico.

### Mudancas aplicadas com prova

| Item | Campo/arquivo | De | Para | Prova |
| --- | --- | --- | --- | --- |
| Ato 3/2026 | `data/legal_sources/reforma_tributaria/Ato_Conjunto_RFB_CGIBS_3_2026_DeRE.txt` | inexistente | texto em tela do Ato Conjunto RFB/CGIBS 3/2026 | PDF oficial CGIBS `https://www.cgibs.gov.br/upload/arquivos/202606/22083423-ato-conjunto-nro-3-dere.pdf`, resolvido por leitura web em 2026-06-24 |
| Fonte legal | `scripts/legal_modules.py` | Reforma sem `ato-conjunto-rfb-cgibs-3-2026-dere` | fonte declarada, vinculada a documentos/obrigacoes e regimes diferenciados | build gerou `federal/legislacao/atos/ato-conjunto-rfb-cgibs-3-2026-dere.html` |
| Cobertura mestre | `scripts/build_master_indexes.py` | fontes locais da Reforma sem Ato 3/2026 | Ato 3/2026 incluído na lista de fontes locais | `python scripts/build_master_indexes.py` gerou `docs/master-audit.md` sem falha estrutural |
| Data editorial | `scripts/build_portal.py` | normalizador nao alcançava `15/06/2026` em paginas estaduais antigas | normalizador atualiza qualquer `Atualizacao editorial: dd/mm/aaaa` | `python scripts/audit_portal.py` passou em 656 paginas |

### Localhost versus portal publico

| Recurso | Localhost | GitHub Pages antes da publicacao | Decisao |
| --- | --- | --- | --- |
| `federal/legislacao/reforma-tributaria/index.html` | HTTP 200 com Ato 3/2026 | HTTP 200 sem Ato 3/2026 | atualizar publico |
| `federal/legislacao/atos/ato-conjunto-rfb-cgibs-3-2026-dere.html` | HTTP 200 | ausente | publicar pagina nova |
| `llms.txt` | contem Ato 3/2026 | nao contem Ato 3/2026 | atualizar LLM |
| `assets/llm-manifest.json` | contem Ato 3/2026 | nao contem Ato 3/2026 | atualizar manifest |
| `assets/portal-search.js` | contem Ato 3/2026 | nao contem Ato 3/2026 | atualizar busca |

### Gates apos correcao

Todos os hard gates canonicos foram reexecutados apos rebuild final:

- `python -m compileall -q scripts`: OK.
- `python scripts/audit_portal.py`: OK, 656 paginas auditadas.
- `python scripts/audit_master_coverage.py`: OK, 15 requisitos federais, 27 estados, 9727 beneficios, 7050 linhas NCM, 3 familias CONFAZ.
- `python scripts/audit_benefit_cards.py`: OK.
- `python scripts/audit_card_scope_visible.py`: OK.
- `python scripts/audit_no_keyword_inference.py`: OK.
- `python scripts/audit_temporal_consistency.py`: OK.
- `python scripts/audit_link_health.py`: OK com warnings soft; 103 URLs unicas e nenhum 404/410 em beneficio publicado.
- `python scripts/audit_index_freshness.py`: OK.
- `python scripts/audit_quarantine_isolation.py`: OK, 13143 ids verificados.
- `python scripts/audit_reforma_transition.py`: OK.
- `python scripts/audit_divergence_html_json_search.py`: OK.
- `python scripts/audit_editorial_date_per_card.py`: OK.
- `git diff --check`: OK.
- `rg -n "25/04/2026|\\[\\] \\[\\] \\[\\]|str\\(\\[" .`: apenas ocorrencias documentais nos ledgers de monitoramento.

### Passe adversarial complementar

Pergunta adversarial:

> Se o localhost esta correto, o que ainda poderia impedir publicar?

Teste executavel:

- Rebuild completo do portal apos inclusao do Ato 3/2026.
- Bateria canonica integral.
- Comparacao HTTP de localhost contra GitHub Pages nos recursos críticos.
- Busca por vazamento de arquivos ` (1)` em `assets`, `llms.txt`, `sitemap` e dados publicos.

Resultado:

- Nenhum hard gate bloqueou.
- O portal publico estava defasado em relacao ao localhost justamente na fonte nova material.
- Arquivos duplicados ` (1)` nao apareceram em indices publicos.
- Decisao: publicar a atualizacao do portal.
