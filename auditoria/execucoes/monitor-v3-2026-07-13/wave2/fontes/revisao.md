# Revisão cega de fontes e vigência — Onda 2

Candidato: `074bff85c7c560386ca0ed7f0802d4e896534571`
Execução: `2026-07-13T08:15:46-03:00`

## Veredito

**NÃO CONFORME.** A execução fica **BLOQUEADA**: faltam recibos nativos, raízes canônicas e isolamento; nenhum recibo foi fabricado. A produção está corretamente contida em página neutra, mas isso não torna o candidato materialmente conforme.

## Contagens

- Inventário: 862 arquivos autorizados, hashados desde `git ls-tree`.
- Matriz fixa: 0/94 classes nativas.
- Cards: 9726 — vigentes=9485, `a_revalidar`=241, históricos=0.
- Quarentena: 13150.
- `field_provenance` ausente: 9726; recibo nativo ausente: 9726; duas capturas ausentes: 9726.
- Internalização não comprovada: 9611/9611 cards ICMS estaduais.
- Hash de card: match=4385, mismatch=5038; raiz local ausente=303; trecho divergente=544.
- Manifestos: match=29, mismatch=125.
- Quarentena sem fingerprint: 13150.
- Mutantes: 18/18 mortos, 2 por classe em 9 classes; paths temporários aleatórios removidos.

## Cadeias

cadeia re-derivada: cards/datas | fonte crua: data/benefits_crosswalk.json | resultado: 9726/9726 copiam captured_on em publicação/vigência/eficácia e não têm field_provenance.

cadeia re-derivada: recibos | fonte crua: scripts/validated_benefits.py + 9726 cards | resultado: 9726 sem recibo, 9726 sem duas capturas e bloqueio externo incondicional.

cadeia re-derivada: internalização | fonte crua: data/benefits_crosswalk.json | resultado: 9611/9611 cards ICMS estaduais sem prova.

cadeia re-derivada: raízes | fonte crua: 129 fontes locais lidas | resultado: hash match=4385, mismatch=5038, raiz ausente=303, trecho diverge=544.

cadeia re-derivada: quarentena | fonte crua: data/benefits_quarantine.json | resultado: 13150/13150 sem fingerprint e com conteúdo material.

cadeia re-derivada: matriz | fonte crua: git ls-tree + inputs autorizados | resultado: 0/94 classes nativas exatas.

cadeia re-derivada: isolamento | fonte crua: scripts/build_diff_manifest.py | resultado: 2/2 travessias relativas escreveram fora da raiz do repositório temporário.

cadeia re-derivada: produção | fonte crua: refetch anônimo já realizado | resultado: portal neutro 200; superfícies tributárias testadas 404.

## Limitações fail-closed

O conteúdo dos scripts `audit_*` não foi lido porque ficou fora da lista expressa de inputs autorizados; sua existência e invocação no workflow foram conferidas. O refetch direto do Planalto terminou em reset de conexão. Essas lacunas permanecem bloqueantes e não foram convertidas em recibos inferidos.

Veredito: BLOQUEADO / NÃO CONFORME

Status: BLOQUEADO
