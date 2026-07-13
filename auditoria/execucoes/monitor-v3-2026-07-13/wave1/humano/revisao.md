# Revisão cega — portal humano — Onda 1

Baseline único: `f814f80efbab84bf43b671bf544c4678d4dda82a`
Portal: `https://mjrrafael.github.io/rjc-conhecimento/`
Modo: somente leitura no worktree autorizado; saídas apenas nesta pasta.

## Resultado central

A superfície pública observada está reduzida e segura: somente raiz/`index.html`, `404.html`, `llms.txt` e `robots.txt` retornam HTTP 200; as demais 1.065 rotas do portal retornam HTTP 404 sem erro de coleta. O build Pages emitiu quatro arquivos e a produção coincide byte a byte após a única transformação observada, CRLF→LF.

Ainda assim, a revisão exigida não pode receber conformidade final: não foi obtido recibo nativo de deployment/Pages vinculado ao baseline e não foi fechada a matriz conceitual item a item das 81 células UF nem de todas as famílias federais antes da ordem de encerramento. Pela regra expressa do escopo, isso impõe `NÃO CONFORME` e `BLOQUEADO`.

## Contagens integrais

- Git: 1.023 arquivos; 21 em `auditoria/**`; 20 sob `auditoria/execucoes/**` apenas contabilizados por metadado de árvore.
- Universo autorizado reconciliado: 1.002 arquivos Git = 1.002 arquivos físicos; 0 faltantes, 0 extras, 0 OID divergente.
- HTML: 658 no Git; 656 analisados estruturalmente; 2 artefatos anteriores sensíveis não interpretados.
- Build: 4 arquivos, 0 diretórios, exit 0.
- Links extraídos: 193.929 ocorrências; 1.070 rotas únicas do portal; 562 URLs externas únicas.
- Crawl local: 1.070; HTTP 200=5; HTTP 404=1.065; erros=0.
- Crawl produção/portal: 1.070; HTTP 200=5; HTTP 404=1.065; erros=0.
- Links externos: 562; HTTP 200=448; HTTP 403=21; HTTP 404=6; erro/timeout=87 (`A VALIDAR`).
- Manifestos: 12 `manifest.json`; 12 válidos.
- Quarentena: 13.150 IDs + 68.436 literais + 13.150 fingerprints; zero ocorrência no build/produção.
- Histórico: 57 candidatos derivados integralmente; 57 HTTP 404; zero falha.
- Visual: 8 renderizações (local/produção × index/404 × 390x844/1440x900); zero overflow; zero elemento excedente.

## Hashes

- `inventario.csv`: `a530dbbdefc71a6498e30dc457772eb92c1b699ba8f26bece214e674489dfbd2`
- `crawl_local.csv`: `883e4a0b472ca00611da2af0a4c5aaa15254c7f0f0b4ca47016a7f246d7c970d`
- `crawl_producao.csv`: `bbcf6ed063cf810659482fcdb70c6fcc9b9111dade122a53e9a46d990ce3822a`
- `data/benefits_quarantine.json`: `cb9ae22b8932ee8487606b8db2cb033900b5cacb8b42a3a3036f396a88f7a032`
- `quarantine_checks.csv`: `acbc8b6d3f116afef2d274da57848a74b085a043a2bd5bb3e9cda68c742171b6`
- `historical_checks.csv`: `beb2ac41127976cc2f2618f9ce994036e0f944d5f2ba0b41312990fbf57f3311`

Produção após LF:

| arquivo | SHA-256 produção/LF |
|---|---|
| index.html / raiz | `f3f84f1276d7dfb911624c02ed8a56891473d60cc41d18481321254611e53368` |
| 404.html | `07e4f9f163f5653ca81949a694ba17f00d8416bcdb84f13fafbb7f5d154d13e7` |
| llms.txt | `08f53be6f0f48b242d6d82bc41ccf287ecace2088813b58f9c1f2d5205f0dd07` |
| robots.txt | `331ea9090db0c9f6f597bd9840fd5b171830f6e0b3ba1cb24dfa91f0c95aedc1` |

## Comandos/cadeia executada

```text
git -C <worktree> rev-parse HEAD
git -C <worktree> status --porcelain=v1 --untracked-files=all
git -C <worktree> ls-tree -r -l --full-tree f814f80efbab84bf43b671bf544c4678d4dda82a
01_inventario.ps1
gem install github-pages -v 232 --no-document
jekyll build --source <worktree> --destination <saida>/build/site
02_crawl.py
03_visual.py
04_isolation.py
```

## Passe adversarial

Falhas mais prováveis assumidas: (1) arquivo excluído ainda publicável por rota direta; (2) produção diferente da projeção local; (3) registro de quarentena vazando sob literal diferente; (4) overflow/aviso ausente em viewport móvel; (5) conclusão sustentada apenas por resumo.

cadeia re-derivada: inventário | fonte crua: `git ls-tree` + enumeração física podada antes de `auditoria/execucoes` | resultado: 1.002=1.002, zero faltante/extra/OID divergente.

cadeia re-derivada: build | fonte crua: `_config.yml` + workflow versionado + GitHub Pages 232/Jekyll 3.10.0 | resultado: exit 0, quatro arquivos emitidos.

cadeia re-derivada: rotas | fonte crua: 1.023 paths Git + 193.929 links HTML + sitemap/robots | resultado: 1.070 rotas únicas do portal, cobertura local e produção integral.

cadeia re-derivada: superfície pública | fonte crua: cada linha de `crawl_producao.csv` | resultado: cinco HTTP 200 seguros e 1.065 HTTP 404; zero erro de portal.

cadeia re-derivada: equivalência build-produção | fonte crua: bytes dos quatro arquivos locais e quatro respostas 200 | resultado: hashes divergiam por CRLF; após normalização CRLF→LF, os quatro hashes batem exatamente.

cadeia re-derivada: robots/meta | fonte crua: `robots.txt`, index e 404 publicados | resultado: `Disallow: /` e `noindex,nofollow,noarchive` presentes.

cadeia re-derivada: quarentena-ID | fonte crua: 13.150 entradas de `benefits_quarantine.json` | resultado: 13.150 verificadas, zero ocorrência.

cadeia re-derivada: quarentena-literal | fonte crua: campos textuais normalizados de cada entrada | resultado: 68.436 literais verificados, zero ocorrência.

cadeia re-derivada: quarentena-fingerprint | fonte crua: JSON canônico de cada entrada | resultado: 13.150 SHA-256 verificados, zero ocorrência.

cadeia re-derivada: histórico | fonte crua: todos os 57 paths candidatos derivados por padrão | resultado: 57 HTTP 404 e nenhum fingerprint de arquivo igual a corpo público.

cadeia re-derivada: visual | fonte crua: DOM renderizado em Chrome headless | resultado: 8/8 sem overflow e com estrutura mínima; um 404 automático de recurso ocorreu apenas na raiz móvel e não alterou o conteúdo.

cadeia re-derivada: links externos | fonte crua: 562 URLs externas únicas | resultado: 448=200, 21=403, 6=404, 87=erro/timeout; pendência `A VALIDAR`, porém esses links não são emitidos na projeção pública.

cadeia re-derivada: matriz UF | fonte crua exigida: HTML de cada UF | resultado: BLOQUEADO; 81 células não fechadas antes da ordem de encerramento, sem inferência de matriz anterior.

cadeia re-derivada: famílias federais | fonte crua exigida: links federais/CONFAZ | resultado: BLOQUEADO; classificação integral não fechada.

cadeia re-derivada: recibo nativo | fonte crua exigida: deployment/Pages/Actions vinculado ao commit | resultado: BLOQUEADO; não coletado, e build/HTTP não substituem recibo nativo.

Qual erro mais provável ainda resta? Um deployment não vinculado ao baseline ou uma célula jurisdicional/federal omitida.
Qual evidência o revelaria? Recibo nativo de Pages/Actions e ledger 81/81 + famílias federais item a item. Ela foi produzida? Não.
O que mostrar se Rafael perguntar “tem certeza?” Os três CSVs integrais, hashes, 39.450 verificações de ID/fingerprint mais 68.436 literais, 57 verificações históricas e oito medições visuais; e a limitação impeditiva acima.

Veredito: NÃO CONFORME — BLOQUEADO

Decisão: NÃO CONFORME

Status: BLOQUEADO
