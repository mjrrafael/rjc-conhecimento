# Monitoramento legislativo — 2026-07-12

## Janela e fuso

- Execução atual iniciada em `2026-07-12T14:58:53-03:00`.
- Registro deste ledger: `2026-07-12T15:51:36-03:00`.
- Fuso obrigatório e aplicado: `America/Sao_Paulo` (`-03:00`).
- Última execução informada pela automação: `2026-07-12T16:27:36.578Z`, equivalente a `2026-07-12T13:27:36.578-03:00`.
- Esta foi uma vigília manual/adicional no mesmo dia; nenhuma janela foi alterada silenciosamente.

## Baseline

- Repositório: `mjrrafael/rjc-conhecimento`.
- SHA de `origin/main`: `23d864f510bfbb16d6ef5d73049c63a1003b5ac6`.
- Pages legado confirmado no mesmo SHA.
- Raiz de produção: HTTP 200, 15.559 bytes, SHA-256 `9e6fbc131c18f828659d6634b558f2d433cffb088b8732475b4460e3fd18fa2a`.

## Resultado da Onda 1

Os três revisores independentes reprovaram materialmente o baseline:

- `revisor_fontes_vigencia`: 92.980 identidades e 485 internalizações não comprovadas; somente 797 refetches HTTP 200 completos.
- `revisor_humano_portal`: 29.369 pares de fingerprint em 315 páginas; 3 respostas HTTP 503; rebuild alterou 499 hashes.
- `revisor_ia_dados`: 9.726 cards sem proveniência/recibos; 13.150 registros de quarentena expostos; 5.383 datas suspeitas; 27 contradições PIS candidatas.

## Correção candidata

- P0 de `scripts/validated_benefits.py` alterado para falhar fechado sem datas, proveniência, recibos, revalidação e internalização materiais.
- Conteúdo material de quarentena deixou de ser serializado pelo gerador candidato.
- Pages legado candidato reduzido a aviso neutro, 404, robots e llms por `_config.yml`; todo o acervo é excluído do artefato servido.
- SHA candidato da Onda 2: `e96aafa3e90c928f2b594dc1177293d194674877`.
- PR draft: `https://github.com/mjrrafael/rjc-conhecimento/pull/25`.

## Bloqueios

- Token GitHub sem escopo OAuth `workflow`; push dos workflows foi rejeitado.
- Duas raízes de confiança preexistentes, assinadas e independentes não estão disponíveis.
- Plataforma não fornece export nativo imutável de task graph/tool calls nem IDs HTTP confrontáveis.
- Hard gates materiais e mutation testing ainda não implementados/certificados.
- Onda 2 iniciada e pendente.

## Estado

`BLOQUEADO TEMPORÁRIO` — sem merge, sem alteração em `main` e sem alegação de publicação.
