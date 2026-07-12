# Achados e Pendências

## Achados com lastro

- P0 confirmado: `scripts/validated_benefits.py` usa `captured_on`/`TODAY` como datas jurídicas, `len(jurisdiction)==2` como internalização, `verificado_em=TODAY` e `publishable=True`.
- Não existe diretório `.github`; portanto zero workflow `portal-audit` no baseline.
- PR #24 é draft, contém acúmulo legado e zero checks; não será mesclada diretamente.
- O checkout original contém centenas de modificações/não rastreados e foi preservado; a execução ocorre em worktree limpo de `origin/main`.
- Onda 1 (parcial, ainda em execução): 9.726/9.726 cards públicos sem `field_provenance` e sem recibo nativo de `verificado_em`; 5.383 datas suspeitas; 5.341 hashes de `source_path` divergentes; 13.150 registros materiais de quarentena servidos; 6.728 IDs com sobreposição por shingle.
- Onda 1 (parcial): somente 17/81 células estaduais referenciadas; faltam famílias federais PGFN, Senado, STJ e CARF, e o CONFAZ está reduzido a três famílias.
- PR draft #25 aberta no SHA `48e51c48566468ce70b54b6a43d9579be1db74e8`, com labels `codex` e `codex-automation`, sem autorização para merge.
- O push dos workflows foi rejeitado pelo GitHub porque o token OAuth não possui escopo `workflow`; SSH também não está configurado.

## Pendências

- [ ] Produzir universos e recibos materiais completos — status: A VALIDAR.
- [ ] Resolver todos os achados da Onda 1 — status: A VALIDAR.
- [ ] Localizar duas raízes de confiança preexistentes, assinadas e independentes — status: BLOQUEADO.
- [ ] Provar isolamento somente leitura e export nativo das sessões dos subagentes — status: A VALIDAR.
- [ ] Publicar e confrontar produção — status: A VALIDAR.
- [ ] Autorizar o push de `.github/workflows/*.yml` executando `gh auth refresh -h github.com -s workflow` — status: BLOQUEADO.

## Pontos cegos / não feito

- Nenhuma alegação de cobertura nacional ou segurança material foi feita neste estágio.
