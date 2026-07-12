# Achados e Pendências

## Achados com lastro

- P0 confirmado: `scripts/validated_benefits.py` usa `captured_on`/`TODAY` como datas jurídicas, `len(jurisdiction)==2` como internalização, `verificado_em=TODAY` e `publishable=True`.
- Não existe diretório `.github`; portanto zero workflow `portal-audit` no baseline.
- PR #24 é draft, contém acúmulo legado e zero checks; não será mesclada diretamente.
- O checkout original contém centenas de modificações/não rastreados e foi preservado; a execução ocorre em worktree limpo de `origin/main`.

## Pendências

- [ ] Produzir universos e recibos materiais completos — status: A VALIDAR.
- [ ] Resolver todos os achados da Onda 1 — status: A VALIDAR.
- [ ] Localizar duas raízes de confiança preexistentes, assinadas e independentes — status: BLOQUEADO.
- [ ] Provar isolamento somente leitura e export nativo das sessões dos subagentes — status: A VALIDAR.
- [ ] Publicar e confrontar produção — status: A VALIDAR.

## Pontos cegos / não feito

- Nenhuma alegação de cobertura nacional ou segurança material foi feita neste estágio.
