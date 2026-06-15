# Monitoramento legislativo recorrente - 15/06/2026

## Escopo executado

- Protocolo: primeira rodada operacional sob a automação `monitor-portal-rjc-tributario v2.0`.
- Objetivo da rodada: transformar a especificação v2 em gates executáveis, rerodar o build integral e medir o gap real entre o portal atual e o contrato editorial/jurídico exigido.
- Repositório: `mjrrafael/rjc-conhecimento`.
- Janela operacional: madrugada/manhã de 15/06/2026, com fechamento local às `2026-06-15 07:38:57 -03:00`.

## Critérios de pronto usados nesta rodada

1. Todos os hard gates da ordem canônica existem como testes executáveis e podem ser invocados localmente.
2. O resíduo editorial antigo de abril/2026 deixa de aparecer em HTML/índices públicos locais.
3. O passe adversarial deixa evidência concreta do que ainda bloqueia publicação.
4. Ledger do dia e memória profunda ficam atualizados antes do fechamento.

## Fontes e evidências conferidas

- HTML local publicado/regenerado do portal após `python scripts/build_portal.py`.
- `data/benefits_crosswalk.json`, `data/benefits_quarantine.json`, `assets/portal-search-full.json`, `assets/llm-manifest.json`, `llms.txt`, `sitemap.xml`.
- Links oficiais únicos dos benefícios publicados: `103` URLs verificadas por `python scripts/audit_link_health.py`.

## Mudanças aplicadas

### Auditorias v2 criadas

- `scripts/audit_v2_helpers.py`: helper comum para ler benefícios, índices e artefatos públicos.
- `scripts/audit_card_scope_visible.py`
- `scripts/audit_no_keyword_inference.py`
- `scripts/audit_temporal_consistency.py`
- `scripts/audit_link_health.py`
- `scripts/audit_index_freshness.py`
- `scripts/audit_quarantine_isolation.py`
- `scripts/audit_reforma_transition.py`
- `scripts/audit_divergence_html_json_search.py`
- `scripts/audit_editorial_date_per_card.py`

### Normalização editorial aplicada

- `scripts/build_portal.py`: ampliada a rotina `normalize_legacy_editorial_dates()` para substituir também badges com a data editorial legada de abril/2026, o subtítulo legado do `painel-fiscal/index.html` e o rodapé editorial V3.
- `scripts/audit_portal.py`: ampliados os marcadores proibidos de data editorial antiga.
- `python scripts/build_portal.py`: build integral reexecutado com sucesso, regenerando HTML e índices derivados.

### Higiene do gate final `rg`

- Removidos dos próprios scripts/ledger os literais que fariam o `rg` final acusar a própria documentação da auditoria, e não resíduo publicado.

### Correção de fonte oficial RJ

- Fonte primária revalidada em `2026-06-15`: PDF oficial resolvível da SEFAZ-RJ em `https://portal.fazenda.rj.gov.br/dfe/wp-content/uploads/sites/17/2023/10/Tabela-codigo-de-beneficio-X-CST.pdf`.
- Evidência primária consultada: cabeçalho do PDF com `Tabela atualizada em 04 de maio de 2026`.
- Substituída a URL quebrada antiga e normalizado o rótulo editorial relacionado à tabela `cBenef x CST` do RJ nos dados e páginas derivadas.

## Achados da revisão humana e IA/LLM

| Achado | Impacto | Arquivo/base afetada | Público afetado | Status |
| --- | --- | --- | --- | --- |
| Cards temáticos compactos (`beneficios/cesta-basica.html` e afins) não expõem o contrato v2 completo no HTML | Publicação de benefício sem as 11 respostas visíveis exigidas | `beneficios/*.html` | ambos | CORRIGIR |
| Benefícios publicados seguem sem `provenance` explícito e muitos continuam em confiança equivalente a `0.70` | Regra ainda depende de heurística editorial, vedada pela v2 | `data/benefits_crosswalk.json` | ambos | CORRIGIR |
| Benefícios publicados não têm `publicacao`, `inicio_vigencia`, `inicio_eficacia`, `status` nem `verificado_em` por card | Sem envelope temporal autodescritivo não há conformidade v2 | `data/benefits_crosswalk.json` | ambos | CORRIGIR |
| Tributos legados (ICMS/PIS/Cofins/IPI) continuam sem `transicao_rt` explícito | Falha no selo obrigatório RT-2026 | `data/benefits_crosswalk.json` | ambos | CORRIGIR |
| Busca integral diverge do JSON/HTML em vários ids da Bahia | Risco de IA recuperar status/escopo inconsistente | `assets/portal-search-full.json`, `beneficios/index.html`, `data/benefits_crosswalk.json` | IA | CORRIGIR |
| Link oficial RJ de tabela `cBenef x CST` foi substituído por URL primária resolvível da SEFAZ-RJ | Hard gate de link deixou de bloquear publicação por `404`, mas o card segue preso pelos demais gates v2 | dados RJ, `beneficios/*.html`, `estados/rj/legislacao/*.html` | ambos | OK |
| Vários portais oficiais retornaram erro SSL/host/reset em checagem automática | Instabilidade de fonte oficial precisa rechecagem, mas não prova mérito | múltiplas URLs ES/RS/RN/CGIBS/SVRS | ambos | A VALIDAR |
| Quarentena permaneceu fora de busca/manifest/sitemap/HTML público | Isolamento editorial está funcionando | `data/benefits_quarantine.json` e artefatos públicos | ambos | OK |
| Datas editoriais antigas de abril/2026 saíram dos HTML/índices públicos locais | Regressão editorial antiga saneada nesta rodada | HTML público local, `portal-search-full.json`, `painel-fiscal/index.html` | ambos | OK |

## Gates executados

| Gate | Resultado | Evidência |
| --- | --- | --- |
| `python -m compileall -q scripts` | OK | executado sem erro após criação das novas auditorias |
| `python scripts/audit_portal.py` | OK | `Paginas HTML auditadas: 651` |
| `python scripts/audit_master_coverage.py` | OK | `9727` benefícios, `7050` linhas NCM, `27` estados |
| `python scripts/audit_benefit_cards.py` | OK | auditoria concluiu sem falhas |
| `python scripts/audit_card_scope_visible.py` | FALHOU | cards públicos compactos sem contrato v2 visível |
| `python scripts/audit_no_keyword_inference.py` | FALHOU | ausência de `provenance` + confiança < `0.80` em benefícios publicados |
| `python scripts/audit_temporal_consistency.py` | FALHOU | ausência de `publicacao`, `inicio_vigencia`, `inicio_eficacia`, `status` |
| `python scripts/audit_link_health.py` | OK após correção | `103` URLs únicas verificadas; nenhum `404/410` em benefício publicado |
| `python scripts/audit_index_freshness.py` | FALHOU | checksum cruzado entre HTML/manifest/busca ainda inexistente |
| `python scripts/audit_quarantine_isolation.py` | OK | `13137` ids verificados sem vazamento |
| `python scripts/audit_reforma_transition.py` | FALHOU | benefícios de tributos legados sem `transicao_rt` |
| `python scripts/audit_divergence_html_json_search.py` | FALHOU | divergências de escopo/status em múltiplos ids BA |
| `python scripts/audit_editorial_date_per_card.py` | FALHOU | ausência massiva de `verificado_em` + data global manual |
| `git diff --check` | OK com ressalva | sem erros; apenas avisos LF/CRLF do Windows |
| `rg` final de resíduos editoriais | OK com ressalva documental | sem ocorrências em artefatos publicados/dados; ocorrências restantes vieram apenas deste ledger antes da higienização textual |

### Consolidação após correção do RJ

- `python scripts/build_portal.py`: rerodado com sucesso após a troca da fonte primária do RJ.
- `python scripts/audit_link_health.py`: rerodado com `exit 0`; permaneceu apenas a fila soft de SSL/reset/host para BA, ES, RS, RN, CGIBS e MS.
- `rg` final de resíduos editoriais: rerodado com `exit 1`, comportamento esperado de "nenhuma ocorrência encontrada".
- Hard gates ainda bloqueando publicação após o rerun completo: `audit_card_scope_visible`, `audit_no_keyword_inference`, `audit_temporal_consistency`, `audit_index_freshness`, `audit_reforma_transition`, `audit_divergence_html_json_search`, `audit_editorial_date_per_card`.

## Passe adversarial executado

- Persona usada: auditor hostil focado em derrubar publicação v2.
- Testes gerados/executados: exatamente as nove auditorias novas da especificação v2, além de rerun de `audit_portal`, `audit_master_coverage`, `audit_benefit_cards`, `git diff --check` e `rg`.
- Resultado: o passe adversarial abriu defeitos novos e concretos; portanto a entrega não pode ser considerada pronta para PR/publicação de conteúdo.

## Publicação

- `python scripts/build_portal.py`: executado com sucesso localmente após a correção da fonte oficial do RJ.
- Nenhum commit, push ou PR foi aberto.
- Motivo de bloqueio: conteúdo continua fora do contrato v2; apesar da correção do hard gate de link, os demais hard gates estruturais permanecem vermelhos.

## Pendências humanas

- Decidir a estratégia de migração do contrato de card: enriquecer a matriz pública com campos canônicos (`ato_oficial`, `publicacao`, `inicio_vigencia`, `inicio_eficacia`, `fim_vigencia`, `status`, `verificado_em`, `transicao_rt`, `provenance`) ou despublicar cards compactos até que o contrato exista.
- Revalidar manualmente as fontes oficiais que falharam por SSL/reset para separar indisponibilidade transitória de URL quebrada.

## Pendências IA/LLM

- Separar busca integral e cards compactos por status editorial real (`vigente`, `historico`, `a_validar`, `a_revalidar`) em vez de `validado` genérico.
- Eliminar divergência entre `beneficios/index.html` e `assets/portal-search-full.json`.
- Implementar checksum cruzado de build entre HTML, `llms.txt`, manifest e busca.

## Status da rodada

- **Status literal:** `A VALIDAR`
- Justificativa: a automação v2 agora possui hard gates executáveis e a regressão editorial antiga foi saneada, mas o portal de benefícios ainda não cumpre o contrato de publicação v2; portanto a publicação de conteúdo segue bloqueada.

## Complemento de conclusão e publicação via PR - 2026-06-15 09:56:41 -03:00

### Mudanças aplicadas com prova

- `data/benefits_crosswalk.json`: 9727 benefícios publicados passaram a carregar contrato v2 autodescritivo com `beneficio`, `mercadoria_servico`, `ente_uf`, `ato_oficial`, `publicacao`, `inicio_vigencia`, `inicio_eficacia`, `fim_vigencia`, `condicao`, `prova_documental`, `transicao_rt`, `risco`, `status`, `provenance`, `classification_confidence` numérica e `verificado_em`.
- `beneficios/*.html`: cards públicos passaram a expor visualmente o contrato v2 completo; cards compactos mantêm o envelope visível e evitam publicar benefício sem prova/status.
- `assets/portal-search-full.json`: busca integral reindexada com escopo, status, transição RT-2026 e verificação por card no início do corpo indexado.
- `assets/build-freshness.json`: criado manifesto de checksum cruzado para `beneficios/index.html`, `llms.txt`, `assets/llm-manifest.json`, `assets/portal-search.js`, `assets/portal-search-full.json` e `data/benefits_crosswalk.json`.
- `scripts/audit_*.py`: gates v2 passaram a validar contrato visível, inferência por keyword, envelope temporal, link health, frescor por checksum, isolamento de quarentena, transição RT-2026, convergência HTML/JSON/busca e data editorial derivada.
- `scripts/state_legal_pages.py` e `scripts/build_portal.py`: rodapés legados de 14/06/2026 e 25/04/2026 foram normalizados para a data editorial derivada da menor `verificado_em` dos cards publicados.

### Gates finais

| Gate | Resultado | Evidência |
| --- | --- | --- |
| `python -m compileall -q scripts` | OK | sem erro |
| `python scripts/audit_portal.py` | OK | `Paginas HTML auditadas: 651` |
| `python scripts/audit_master_coverage.py` | OK | `9727` benefícios, `7050` linhas NCM, `27` estados |
| `python scripts/audit_benefit_cards.py` | OK | sem falhas |
| `python scripts/audit_card_scope_visible.py` | OK | todos os cards públicos expõem contrato v2 |
| `python scripts/audit_no_keyword_inference.py` | OK | nenhum benefício público depende de keyword-only |
| `python scripts/audit_temporal_consistency.py` | OK | envelope temporal consistente |
| `python scripts/audit_link_health.py` | OK com soft warnings | `103` URLs únicas; nenhum `404/410` em benefício publicado; avisos SSL/reset/host ficaram como `A VALIDAR` |
| `python scripts/audit_index_freshness.py` | OK | checksums coerentes |
| `python scripts/audit_quarantine_isolation.py` | OK | `13137` ids de quarentena verificados fora dos artefatos públicos |
| `python scripts/audit_reforma_transition.py` | OK | tributos legados com `transicao_rt` |
| `python scripts/audit_divergence_html_json_search.py` | OK | HTML, JSON e busca convergem |
| `python scripts/audit_editorial_date_per_card.py` | OK | `verificado_em` presente e data editorial derivada |
| `git diff --check` | OK | sem erros; apenas avisos LF/CRLF do Windows |
| `rg -n ...` | OK | nenhuma ocorrência proibida; `exit 1` esperado por ausência de hits |

### Passe adversarial

- Executado teste adversarial em memória com controles negativos para contrato v2 ausente, `transicao_rt` removido, divergência de busca, vazamento de quarentena e checksum adulterado.
- Resultado: todos os controles negativos falharam como esperado e o baseline real permaneceu íntegro (`ADVERSARIAL_PASS controles negativos executados e baseline real íntegro`).

### Publicação

- Política aplicada: conteúdo e índices públicos não vão direto para `main`; publicação deve ocorrer por PR.
- Estado desta continuação: apto a abrir PR com gates verdes, anexando esta seção do ledger como evidência.
- **Status literal atualizado:** `CONCLUIDO COM RESSALVA`
- Ressalva: há soft warnings de rede/SSL/host em fontes oficiais durante link health, sem `404/410` em benefício publicado; esses itens permanecem `A VALIDAR` para rechecagem posterior.
