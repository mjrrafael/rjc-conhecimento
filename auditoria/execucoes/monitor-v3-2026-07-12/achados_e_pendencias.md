# Achados e Pendências

## Achados com lastro

- P0 confirmado: `scripts/validated_benefits.py` usa `captured_on`/`TODAY` como datas jurídicas, `len(jurisdiction)==2` como internalização, `verificado_em=TODAY` e `publishable=True`.
- Não existe diretório `.github`; portanto zero workflow `portal-audit` no baseline.
- PR #24 é draft, contém acúmulo legado e zero checks; não será mesclada diretamente.
- O checkout original contém centenas de modificações/não rastreados e foi preservado; a execução ocorre em worktree limpo de `origin/main`.
- Onda 1 (parcial, ainda em execução): 9.726/9.726 cards públicos sem `field_provenance` e sem recibo nativo de `verificado_em`; 5.383 datas suspeitas; 5.341 hashes de `source_path` divergentes; 13.150 registros materiais de quarentena servidos; 6.728 IDs com sobreposição por shingle.
- Onda 1 (parcial): somente 17/81 células estaduais referenciadas; faltam famílias federais PGFN, Senado, STJ e CARF, e o CONFAZ está reduzido a três famílias.
- Onda 1 final — fontes/vigência: 119.811 cards HTML, 89.068 objetos jurídicos, 68.542 em quarentena; 1.865 recibos JSON válidos para 1.917 alvos, apenas 797 HTTP 200 completos; 92.980 identidades e 485 internalizações não comprovadas.
- Onda 1 final — humano: 29.369 pares de fingerprint em 315 páginas, 9.419 IDs únicos; produção com 988 HTTP 200 e 3 HTTP 503; rebuild alterou 499 hashes.
- Onda 1 final — IA/dados: 9.726 históricos sem cadeia explícita, 27 contradições PIS candidatas e build só-Git não reproduzível.
- PR draft #25 aberta no SHA `48e51c48566468ce70b54b6a43d9579be1db74e8`, com labels `codex` e `codex-automation`, sem autorização para merge.
- O push dos workflows foi rejeitado pelo GitHub porque o token OAuth não possui escopo `workflow`; SSH também não está configurado.
- Onda 2 fontes/vigência: 9.726/9.726 cards sem proveniência/recibos, 9.611 ICMS sem internalização específica e produção com quarentena bruta HTTP 200.
- Onda 2 humano: dois builds Jekyll emitiram exatamente quatro arquivos; crawl de 2.432 rotas não encontrou vazamento candidato, mas a independência foi contaminada por leitura acidental de snippets internos ao SHA.
- Onda 2 IA/dados: pipeline integral levou 821,6 s, alterou 674 arquivos; `build_portal.py` desfaz a quarentena da raiz e gera 658 URLs; 16 gates passaram e 4 falharam.
- Revisor de aplicação independente: veredito `NÃO CONFORME`; confirmou status `BLOQUEADO`, detectou artefatos obsoletos e dois hashes de inventário divergentes, posteriormente corrigidos por geração do inventário por último.

## Pendências

- [ ] Produzir universos e recibos materiais completos — status: A VALIDAR.
- [ ] Resolver todos os achados da Onda 1 — status: A VALIDAR.
- [ ] Localizar duas raízes de confiança preexistentes, assinadas e independentes — status: BLOQUEADO.
- [ ] Provar isolamento somente leitura e export nativo das sessões dos subagentes — status: A VALIDAR.
- [ ] Publicar e confrontar produção — status: A VALIDAR.
- [ ] Autorizar o push de `.github/workflows/*.yml` executando `gh auth refresh -h github.com -s workflow` — status: BLOQUEADO.
- [ ] Disponibilizar export nativo imutável de task graph/tool calls e recibos HTTP com IDs confrontáveis — status: BLOQUEADO.
- [ ] Disponibilizar duas raízes de confiança preexistentes, assinadas e administrativamente distintas — status: BLOQUEADO.

## Pontos cegos / não feito

- Nenhuma alegação de cobertura nacional ou segurança material foi feita neste estágio.
