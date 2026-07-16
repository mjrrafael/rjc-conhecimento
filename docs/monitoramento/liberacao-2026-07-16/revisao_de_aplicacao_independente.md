# Revisão independente da aplicação — 2026-07-16

## Veredito

`NÃO CONFORME` para a publicação integral.

## Re-derivação a partir das fontes cruas

cadeia re-derivada: `scripts/audit_v3_readiness.py` aberto e executado no worktree isolado → saída com código 1 → 13 hard gates ausentes, duas raízes de confiança não comprovadas e 94 linhas canônicas sem URL, recibo e hash material. Resultado: DIVERGIU da hipótese de que o portal integral pudesse ser liberado.

O revisor também abriu `_config.yml`, `data/benefits_crosswalk.json` e `data/benefits_quarantine.json`: a configuração mantém o acervo fora do Pages; o crosswalk contém 9.726 entradas e a quarentena 13.150. Foram rederivadas ainda as contagens de 658 HTML, 655 URLs em sitemap e 19.089 entradas de busca.

## Falhas de execução corrigidas no dossiê

- O ledger inicial não continha os IDs `RAC-001` a `RAC-005`; eles foram incluídos com evidência rastreável.
- O resultado de `G4` não estava registrado; foi incluído como `CORRIGIR`, com o código de saída e os motivos materiais.

## Conclusão

Não religar o portal integral. A página neutra atual permanece isolada; a restauração exige prova por campo, recibos nativos, matriz nacional e os gates que ainda faltam.
