# workflow.md — Monitor Portal RJC Tributário v3.0 — 2026-07-12

## 1. Resumo de uma linha
Vigília v3 em execução sobre baseline `23d864f510bfbb16d6ef5d73049c63a1003b5ac6`, em worktree isolado.

## 2. Contexto / objetivo
Sanear integralmente o portal, corrigir o gerador legado, provar cobertura jurídica e técnica, publicar por PR e confrontar Pages/produção.

## 3. Critérios de pronto e evidência exigida

1. Inventário integral reconciliado entre Git, filesystem, geradores, build e produção, com diferença simétrica zero.
2. Escopo canônico fechado para União, 27 jurisdições, classes estaduais e famílias federais, com recibos HTTP nativos.
3. Zero conteúdo público sem fonte oficial primária, proveniência por campo, datas não sintéticas e internalização comprovada.
4. Zero vazamento da quarentena em HTML, JSON, busca, sitemap ou LLM, inclusive por fingerprint.
5. Todos os hard gates implementados, mutation-tested por duas raízes de confiança preexistentes e verdes no SHA candidato.
6. Duas ondas cegas de três revisores, com isolamento somente leitura e prova negativa de acesso entre ondas.
7. Diff classificado, commit explícito, worktree limpo, PR/CI no SHA exato, merge, Pages e hashes HTTP comprovados.
8. Refetch pós-deploy de todas as fontes oficiais públicas verde.

## 4. Metodologia / fases

- G0: baseline, memória, PRs, produção e isolamento Git.
- G1: universos canônicos e inventário antes de conteúdo.
- G2: correção segura; dúvida implica quarentena não pública.
- G3: revisão adversarial e duas ondas independentes.
- G4: gates locais, CI, mutation testing e prova de publicação.
- G5: somente `CONCLUÍDO E PUBLICADO`, `SEM ALTERAÇÃO — PRODUÇÃO INTEGRALMENTE VERIFICADA` ou `BLOQUEADO TEMPORÁRIO`.

## 5. Estado inicial observado

- Checkout do usuário sujo e preservado.
- PR draft #24 aberta, sem checks, marcada como legado não isolado.
- `origin/main` no SHA baseline acima.
- `.github/workflows/portal-audit.yml` ausente.
- `scripts/validated_benefits.py` contém fallbacks sintéticos proibidos.
- PR draft #25 registra o checkpoint fail-closed; workflows permanecem apenas em branch local por falta do escopo OAuth `workflow`.
- Achados parciais da Onda 1 confirmam ausência universal de proveniência/recibos nos 9.726 cards e vazamento material da quarentena.

## 6. Arquivos gerados

- Pasta desta execução e artefatos enumerados pelo contrato.

## 7. Achados com lastro

Ver `achados_e_pendencias.md` e `ledger_verificacao.csv`.

## 8. Pendências para fechar 100%

Todos os critérios 1–8 permanecem abertos até evidência integral.

## 9. Próximos passos

- [ ] Reconstruir inventário e escopo canônico.
- [ ] Reconciliar Onda 1.
- [ ] Corrigir/quarentenar integralmente.
- [ ] Executar Onda 2 e gates.
- [ ] Publicar e verificar produção.
- [ ] Após autorização externa, adicionar os workflows completos à PR #25 e exigir check no SHA exato.

## 10. Notas técnicas

Worktree: `C:\Users\rafae\Documents\Codex\2026-06-14\pesquisa-na-mem-ria-profunda-l\worktrees\rjc-monitor-2026-07-12-1458`.

## 11. Decisões do usuário

Aplicar literalmente o contrato v3.0 da automação; PR aberta ou patch local não é sucesso.
