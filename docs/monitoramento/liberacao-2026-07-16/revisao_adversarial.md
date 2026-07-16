# Revisão adversarial — liberação 2026-07-16

## Hipótese de falha

Se a versão integral anterior for religada removendo apenas as exclusões do Pages, o usuário receberá informações tributárias que não têm prova atual por campo, enquanto os itens de quarentena voltarão à busca, ao sitemap e a páginas HTML.

## Cadeia re-derivada

cadeia re-derivada: fontes cruas abertas `data/benefits_crosswalk.json` (chave `entries`, 9.726 elementos) e `data/benefits_quarantine.json` (chave `entries`, 13.150 elementos) → fonte crua `scripts/audit_v3_readiness.py` (SHA-256 `7646dbf68e0205d31f9189f9bf07cbf76d38a621bd37e315ab0e952342f95d59`) executada no baseline → resultado: DIVERGIU da hipótese de prontidão, pois informou 94 linhas canônicas sem URL/recibo/hash material e 13 hard gates ausentes. A comparação com `_config.yml:3-33` (SHA-256 `cedf76ae9da7968a24c138ef5bee2c6b1b30f44bc658ee9c7cef3321d9e354c3`) confirma que a publicação atual é neutra e não permite concluir que o acervo integral está pronto.

## O que ainda poderia derrubar a conclusão

Uma fonte oficial atualmente válida para todos os campos de todos os cards, associada a recibos nativos independentes, poderia tornar subconjuntos publicáveis. Essa evidência ainda não foi produzida nesta execução.

Veredito: defeito material confirmado; não publicar integralmente o acervo legado nesta etapa.
