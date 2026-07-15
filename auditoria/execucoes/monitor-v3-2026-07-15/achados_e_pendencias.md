# Achados e pendencias — vigilia 2026-07-15

## Achados

- A producao aponta ao SHA `f814f80e`; Pages e `portal-audit` desse SHA estao verdes, e a superficie emitida e somente a pagina de revisao, 404, robots e llms — fonte: `production_observation.json`.
- A PR #26 esta draft no SHA remoto `5fd60192` e seu `portal-audit` falhou materialmente por ausencia de raizes confiaveis, mutacao certificada e 94 linhas de fonte — fonte: `pr_26_observation.json`.
- Os commits locais posteriores da branch da PR removem os gates v3 materiais do workflow; por isso essa arvore local nao pode ser retomada — fonte: `local_candidate_workflow_diff.md`.
- A matriz minima tem 94/94 linhas sem URL inicial/final, dominio, recibo, HTTP ou hash; o acervo nao pode ser republicado — fonte: `revisao_adversarial.md`.
- Os 9.726 cards do crosswalk nao possuem os quatro campos de prova material examinados pelo revisor IA; a quarentena tem 13.150 IDs — fonte: `revisao_adversarial.md`.

## Pendencias

- [ ] Duas raizes de confianca externas, preexistentes e assinadas — motivo: nao existem nesta plataforma — status: BLOQUEADO.
- [ ] Recibos nativos HTTP/subagentes e exportacao imutavel de sessoes — motivo: ferramenta nao os expoe — status: BLOQUEADO.
- [ ] Prova primaria e refetch independente para 94 linhas e todos os cards — motivo: corpus ainda sem lastro — status: BLOQUEADO.
- [ ] Reintroduzir/executar os 13 gates v3 no CI de qualquer novo candidato — motivo: baseline nao os chama e a versao local posterior os remove — status: BLOQUEADO.

## Pontos cegos / nao feito

- Jekyll nao esta instalado nesta maquina; o build local exato nao foi reproduzido. O build Pages remoto verde do SHA de producao e o confronto HTTP normalizado mitigam apenas a superficie segura atual.
- Observacoes HTTP desta vigilia nao sao recibos nativos e nao foram promovidas a prova juridica.
