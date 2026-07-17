# Revisão adversarial

cadeia re-derivada: contenção Pages | fonte crua: crawl anônimo de `https://mjrrafael.github.io/rjc-conhecimento/` e 927 URLs pelo revisor humano | resultado: bateu — raiz, `404.html`, `robots.txt` e `llms.txt` são as únicas superfícies servidas; rotas legadas retornam 404 seguro.

cadeia re-derivada: exposição pública fora de Pages | fonte crua: `raw.githubusercontent.com/mjrrafael/rjc-conhecimento/4caecc1c61e98e76a6c4a4eedaf10ada9e1d4e5f/...` | resultado: divergiu da conclusão de contenção global — 875/875 arquivos legados deram HTTP 200, incluindo busca e índices jurídicos materiais.

cadeia re-derivada: fontes e vigência | fonte crua: 41 refetches anônimos de URLs oficiais pelo revisor de fontes | resultado: divergiu — há 36 HTTP 200 e cinco falhas, mas não há recibos nativos, proveniência por campo nem cobertura nacional completa.

cadeia re-derivada: coerência de dados fail-closed | fonte crua: `data/benefits_crosswalk.json`, `assets/build-freshness.json` e gates Python | resultado: bateu após correção — crosswalk público está vazio/bloqueado, manifesto coincide e mutantes sem marcador fail-closed são rejeitados.

Veredito: P0 — conteúdo tributário sem prova material continua publicamente acessível pelo GitHub Raw. A contenção do Pages não autoriza restauração, certificação ou fechamento de sucesso.
