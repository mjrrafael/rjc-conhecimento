# Revisão cega IA/dados — Onda 1

Baseline único: `f814f80efbab84bf43b671bf544c4678d4dda82a`
Execução: `2026-07-13T07:57:07-03:00`
Decisão: **NÃO CONFORME**
Status: **BLOQUEADO**

## Resultado executivo

A produção atual está efetivamente fechada em quatro arquivos seguros: a varredura de **1.024 URLs** derivadas integralmente do `git ls-tree` retornou **5 HTTP 200 esperados** (raiz + quatro arquivos) e **1.019 HTTP 404 esperados**, sem divergência. A quarentena de **13.150 entradas** não aparece nessa projeção por ID, literal, hash canônico, texto normalizado ou shingle de oito palavras.

Isso não autoriza o pipeline. O dataset commitado contém **9.726/9.726 registros `publishable=true` sem proveniência por campo nem recibos**, **241 `A_REVALIDAR`** entram em HTML e busca como “Benefício fiscal validado”, **291/291** linhas PIS/Cofins-NCM publicáveis carregam dois campos `A_VALIDAR`, **37/154** hashes de manifestos estaduais não batem, **13 hard gates declarados estão ausentes** e **0/94** raízes canônicas têm recibo nativo comprovável nas entradas permitidas.

## Universo e cobertura integral

- `git ls-tree`: 1.023 blobs; 20 sob `auditoria/execucoes/**` foram apenas identificados, nunca tiveram corpo lido.
- Filesystem permitido: 1.004 arquivos (1.003 versionados + ponteiro `.git`), 770.703.312 bytes; todos hashados.
- JSON/NDJSON permitidos: 36/36 parseáveis; 2 NDJSON lidos linha a linha, sem amostra.
- `data/**` e `assets/**`: cada arquivo consta individualmente em `inventario.csv` e `superficies.csv` com hash/estado.
- HTML/grafo: 658 páginas, 194.246 referências, 174.240 internas e 20.006 externas (1.223 URLs únicas); 0 arquivo ou âncora ausente.
- Descoberta: busca integral 19.089 entradas/17.681 URLs únicas; manifest LLM e sitemaps 655/655/655, mesmos conjuntos e 0 destinos ausentes.

## Cadeias adversariais rederivadas

cadeia re-derivada: inventário | fonte crua: `git ls-tree -r -z -l f814f80efbab84bf43b671bf544c4678d4dda82a` + filesystem permitido | resultado: 1.023 blobs; 1.004 arquivos permitidos; 20 corpos proibidos não lidos.

cadeia re-derivada: JSON/NDJSON | fonte crua: 36 arquivos permitidos | resultado: 36 parseáveis; `ncm_benefits_index.json` tem 32 grupos e 34 IDs duplicados excedentes.

cadeia re-derivada: produção | fonte crua: 1.024 URLs derivadas do tree | resultado: 5×200 + 1.019×404, 0 divergências; 20 caminhos proibidos testados somente por HEAD.

cadeia re-derivada: quarentena | fonte crua: 13.150 entradas/126.347 campos materiais + quatro arquivos seguros | resultado: 0 ID, 0 literal, 0 hash canônico, 0 texto normalizado, 0 shingle.

cadeia re-derivada: álgebra pública | fonte crua: `_config.yml`, quatro fontes seguras, produção e `publishable` do crosswalk | resultado: produção=allowlist segura, mas 9.726 flags publishable não fecham com o artefato nem com a proveniência atual; divergência.

cadeia re-derivada: proveniência | fonte crua: `data/benefits_crosswalk.json` | resultado: 0/9.726 `field_provenance`, 0/9.726 recibos HTTP independentes, 0/9.726 recibos de verificação; 7.827 hashes de origem batem, 1.596 divergem e 303 apontam corpo remoto não atestado.

cadeia re-derivada: estados inseguros | fonte crua: crosswalk, NDJSON PIS/Cofins, busca e HTML | resultado: 241 `A_REVALIDAR` em busca+HTML; 291 linhas publicáveis têm `cst_entrada_saida.fonte` e `ncm.tipi_versao` como `A_VALIDAR`.

cadeia re-derivada: manifestos | fonte crua: 12 manifestos estaduais e 154 textos | resultado: 117 hashes batem (raw ou normalizado), 37 divergem: MS 35, RJ 1, RS 1.

cadeia re-derivada: freshness | fonte crua: `assets/build-freshness.json` e 19 artefatos | resultado: 1 hash divergente (`llms.txt`) e 8 tamanhos divergentes; o gate só testa hashes selecionados, não bytes nem idade.

cadeia re-derivada: grafo | fonte crua: 658 HTML, busca, sitemaps e manifest | resultado: 0 alvos/âncoras faltantes, mas 322 IDs duplicados em 15 HTML; o gate geral não detectou.

cadeia re-derivada: gates | fonte crua: workflow e scripts primários | resultado: 27/27 mutantes seguros rejeitados e 41/41 scripts compilam; 13 hard gates declarados ausentes, committed dataset não reconstruído e filtros de publicação ignoram `status`/`publishable`.

cadeia re-derivada: raízes canônicas | fonte crua: UFs/classes/famílias fixadas e JSON permitidos | resultado: 81+13=94 requisitos, 0 com `http_receipt_id`/status/hash nativo classificável; BLOQUEADO.

cadeia re-derivada: isolamento | fonte crua: log desta sessão | resultado: um `rg` amplo exibiu trechos de `workflow.md` e `docs/monitoramento/**`; nenhum desses trechos foi usado como evidência, mas a cegueira não é demonstrável. BLOQUEADO.

## Execuções e evidências

| Teste | Resultado |
|---|---:|
| parser JSON/NDJSON integral | 36/36 OK |
| compilação Python em memória | 41/41 OK |
| auditorias locais seguras | 15 passaram; 4 falharam |
| mutantes da projeção | 27/27 rejeitados |
| URLs de produção | 1.024/1.024 conforme expectativa |
| links/âncoras locais | 0 faltantes |
| hashes manifestos estaduais | 117 OK; 37 divergentes |
| build freshness | 18 hashes OK; 1 divergente; 8 bytes divergentes |
| raízes canônicas com recibo nativo | 0/94 |

Comandos centrais: `git rev-parse HEAD`, `git status --short`, `git ls-tree -r -z -l f814f80efbab84bf43b671bf544c4678d4dda82a`, parsers Python integrais, `python -B` nos 19 auditores seguros, `test_safe_pages_projection_gate.py`, `test_validated_benefits_fail_closed.py`, varredura HTTP concorrente de todas as 1.024 rotas e rederivação independente do grafo HTML.

## Hard gates ausentes, stubs e bypasses

Os 13 hard gates declarados em `audit_v3_readiness.py` estão individualizados em `gate_review.csv`. Adicionalmente faltam gates de unicidade de IDs/âncoras, rejeição de status inseguro em item publicável e rebuild reproduzível em destino isolado. `monitor_v3_inventory.py` gera as 94 linhas canônicas vazias e `A_VALIDAR`; `audit_scope` testa forma, não recibo. O teste fail-closed valida uma fixture, mas o CI não valida/reconstrói o dataset já commitado.

## Limitações impeditivas

- Ruby/Jekyll não existem no runtime; o build exato não foi reproduzido. Produção e cópia segura corroboram, mas não substituem isso.
- Não há recibos nativos/plataforma para as 94 raízes nem para os 9.726 itens publishable.
- As raízes externas `G:/`, `C:/.../BD_LEGISLACAO` e 36 documentos do pacote externo não estão disponíveis.
- A cegueira de revisão foi comprometida pelo `rg` amplo descrito acima; por regra expressa, isso impede status conclusivo.

## Frase de controle

Erro mais provável restante: um artefato alternativo de deploy ou raiz externa conter material não refletido no baseline permitido. A evidência necessária seria build Jekyll isolado com toolchain idêntico, recibos nativos e hashes das raízes externas; ela não foi produzida. As provas concretas disponíveis são os 1.024 recibos HTTP de runtime, hashes do inventário, 36 parses integrais, 27 mutantes e as rederivações acima.

Veredito: NÃO CONFORME; nenhum defeito novo no passe terminal de coerência dos seis artefatos.

Status: BLOQUEADO
