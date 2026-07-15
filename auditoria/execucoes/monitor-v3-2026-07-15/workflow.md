# Monitor Portal RJC Tributario v3.0 — vigilia 2026-07-15

## 1. Resumo de uma linha

Producao do SHA `f814f80efbab84bf43b671bf544c4678d4dda82a` permanece em quarentena segura; a certificacao para republicar conteudo juridico esta bloqueada por prova material e infraestrutura externa ausentes.

## 2. Objetivo e criterio de pronto

Objetivo: revalidar o baseline, a producao e a PR #26 sem tocar no worktree compartilhado.

Critério de sucesso: somente `CONCLUIDO E PUBLICADO` ou `SEM ALTERACAO — PRODUCAO INTEGRALMENTE VERIFICADA`, com todos os recibos nativos, duas raizes confiaveis e revalidacao material exigidos pelo contrato de automacao.

Evidência observada: Pages e `portal-audit` verdes no SHA de producao, mas a matriz de 94 fontes, os cards e a certificacao de independencia nao atingem o criterio acima.

## 3. Fontes e inventario

- Baseline: `origin/main` no SHA `f814f80efbab84bf43b671bf544c4678d4dda82a`.
- Produção: raiz, `404.html`, `robots.txt` e `llms.txt` do GitHub Pages; hashes normalizados em `production_observation.json`.
- PR candidata: #26, SHA remoto `5fd601925898042926cd9cd3d760ae8a033672d5`, ainda draft e com `portal-audit` reprovado.
- Inventario de leitura: `inventario_documentos.csv`. O inventario integral do baseline nao foi regenerado nesta vigilia porque nao houve candidato juridico novo; isso e bloqueio explicito, nao uma cobertura alegada.

## 4. Metodo / gates

- G0: branch/worktree exclusivo derivado de `origin/main`; worktree compartilhado preservado.
- G1: SHA, workflow, producao, CI/Pages, matriz v3, dados e superficies rederivados.
- G2: confrontadas quatro superficies emitidas e a integridade da PR #26.
- G3: tres revisores novos, somente leitura e `fork_turns=none`, com escopos fontes, humano e dados/IA.
- G4: verificador do rito executado contra esta pasta; a ausencia de isolamento/recibos nativos permanece fail-closed.
- G5: decisao literal de nao publicar/republicar.

## 5. Arquivos gerados

Todos os artefatos desta vigilia estao em `auditoria/execucoes/monitor-v3-2026-07-15/`; o resumo versionado esta em `docs/monitoramento/monitoramento-legislativo-2026-07-15.md`.

## 6. Pendencias para fechar 100%

- [ ] Disponibilizar duas raizes de confianca preexistentes, assinadas e administrativamente distintas.
- [ ] Exportar recibos HTTP e de subagentes nativos, confrontaveis e com prova negativa de acesso entre ondas.
- [ ] Preencher, com refetch independente, as 94 linhas minimas de fonte e a proveniencia por campo dos cards.
- [ ] Implementar e executar no CI os 13 gates v3; somente entao congelar candidato e repetir a Onda 2.

## 7. Notas para a proxima vigilia

Nao retomar os commits locais posteriores da PR #26: eles removem gates materiais do workflow. Partir de `origin/main` e conservar a quarentena Pages ate o criterio integral ser atingido.
