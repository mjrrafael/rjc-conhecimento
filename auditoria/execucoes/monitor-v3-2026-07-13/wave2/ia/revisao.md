# Revisão cega IA/dados — Onda 2

**Candidato:** `074bff85c7c560386ca0ed7f0802d4e896534571`
**Decisão:** NÃO APROVAR
**Status:** BLOQUEADO
**Veredito material:** NÃO CONFORME

## Resultado executivo

A produção está efetivamente contida em quatro arquivos seguros e seus hashes coincidem com o candidato. Isso não torna o corpus interno conforme: os 13 gates candidatos fecharam em **0 PASS, 12 FAIL e 1 BLOQUEADO**; não há recibos nativos, duas raízes administrativas preexistentes nem prova negativa de isolamento confrontáveis. O fail-closed é obrigatório.

Foram inventariados 309 arquivos permitidos (249.376.272 bytes). Todos os 34 JSON/NDJSON parsearam, sem chaves duplicadas. A falha é material, não sintática: 10.017 objetos continuam `publishable=true` sem qualquer um dos campos probatórios novos detectáveis.

## Achados determinantes

1. **Proveniência e datas quebradas.** Os 9.726 benefícios estão publishable, mas têm 0 `field_provenance`, 0 `verification_receipt_id`, 0 pares de recibos HTTP e 0 provas específicas de internalização. Em 9.726/9.726, publicação e inícios de vigência coincidem com a data de captura; 9.611 ainda carregam `internalizado_uf=true` sem objeto de prova. Há 241 cards `a_revalidar` simultaneamente publishable.
2. **Fingerprints obsoletos.** Das 154 fontes curadas, 66 não batem com o SHA declarado. Nos benefícios: 3.442 hashes atuais, 5.866 antigos e 418 externos/desconhecidos. No NCM: 3.863 atuais, 1.749 antigos e 1.438 externos/desconhecidos.
3. **Quarentena sem fingerprint.** Os 13.150 registros têm 0 `source_fingerprint` e 0 `sha256`; o arquivo material está rastreado. O gate de fingerprints falha no candidato e, ao mesmo tempo, aceita um registro `a_validar` sem qualquer fingerprint quando o nome do path não denuncia quarentena.
4. **Colisão de IDs/grafo.** As 7.050 linhas NCM contêm apenas 7.016 IDs únicos: 34 ocorrências excedentes, com conteúdos diferentes compartilhando âncoras. A busca full tem 19.089 entradas e 1.408 repetições de URL; sete das 655 páginas do manifesto não aparecem como base da busca.
5. **Build/freshness incoerente.** O freshness tem 19 artefatos e 16 divergências/não comprovabilidades: `llms.txt` possui hash e tamanho antigos; 11 tamanhos dependem de CRLF embora o hash seja canônico; quatro artefatos ficam fora do universo local autorizado. O rebuild isolado falhou após 114,4 s por `Decreto_6306_2007_Regulamento_IOF.txt` ausente numa raiz externa e já havia escrito páginas na cópia temporária, logo não é hermético nem atômico.
6. **Gates moldáveis.** Foram executados 26 mutantes próprios (dois por gate), todos rejeitados. Porém 16 de 17 sondas de bypass foram aceitas: evidência meramente formatada, hashes arbitrários, inventário sem hashes, publicação autodeclarada, arquivo público extra ignorado e registros sem campos obrigatórios. O workflow ainda omite `audit_publication.py` e `audit_public_http_hashes.py`.
7. **Produção contida.** Em 674 URLs derivadas do manifesto e endpoints protegidos, houve cinco respostas 200 representando quatro superfícies únicas (`index.html`, `404.html`, `robots.txt`, `llms.txt`) e 669 respostas 404. Os quatro hashes públicos coincidem. Sitemap, assets, dados e 655 paths antigos não são servidos.

## Cadeias rederivadas

cadeia re-derivada: inventário | fonte crua: `git ls-tree -r -l 074bff85 -- data assets scripts .github _config.yml index.html 404.html robots.txt llms.txt` | resultado: 309 arquivos; hashes canônicos item a item.

cadeia re-derivada: JSON/NDJSON | fonte crua: 34 arquivos permitidos | resultado: todos parseiam; nenhuma chave duplicada; a não conformidade é semântica.

cadeia re-derivada: benefícios/datas | fonte crua: `data/benefits_crosswalk.json` | resultado: 9.726 cards sem prova nova; datas jurídicas derivadas da captura.

cadeia re-derivada: NCM/CSV | fonte crua: `data/ncm_benefits_index.json` + CSV | resultado: 7.050 linhas equivalentes nos 21 campos; 34 colisões de ID materiais.

cadeia re-derivada: PIS/Cofins | fonte crua: `data/pis-cofins/ncm.ndjson` + índice | resultado: 291/291 registros projetados corretamente.

cadeia re-derivada: fontes/fingerprints | fonte crua: 12 manifestos e 154 textos curados | resultado: 66 hashes divergiram.

cadeia re-derivada: quarentena | fonte crua: `data/benefits_quarantine.json` | resultado: 13.150 registros sem SHA/fingerprint; isolamento probatório não demonstrado.

cadeia re-derivada: busca/manifesto/grafo | fonte crua: `portal-search-full.json`, `portal-search.js`, `llm-manifest.json` | resultado: sete páginas órfãs da busca e colisões de âncora NCM.

cadeia re-derivada: build/freshness | fonte crua: geradores e cópia aleatória isolada | resultado: freshness incoerente; build não hermético e com escrita parcial.

cadeia re-derivada: produção | fonte crua: 674 GETs em `https://mjrrafael.github.io/rjc-conhecimento/` | resultado: somente quatro superfícies únicas servidas; demais 404.

cadeia re-derivada: gates | fonte crua: `portal_v3_gates.py` e 26 mutantes próprios | resultado: candidato 0/13 PASS; mutantes 26/26 detectados; 16 bypasses moldados aceitos.

cadeia re-derivada: recibos/raízes/isolamento | fonte crua: diretório autorizado da revisão | resultado: recibos nativos, raízes distintas e prova negativa ausentes; conclusão BLOQUEADA sem prova inventada.

## Porta de saída e limitação

Os seis artefatos mínimos foram emitidos. O erro residual mais provável é existir prova nativa fora do escopo permitido; justamente por não poder ser lida nem confrontada, ela não pode sustentar aprovação. A evidência que mudaria o veredito é: bundle nativo autenticável, duas raízes administrativas preexistentes, prova de isolamento, matriz canônica completa, rebuild hermético e reexecução dos 13 gates com 13 PASS.

Veredito: NÃO CONFORME — NÃO APROVAR; recibos, raízes e isolamento permanecem BLOQUEADOS.
