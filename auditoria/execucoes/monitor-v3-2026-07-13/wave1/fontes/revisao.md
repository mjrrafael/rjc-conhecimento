# Revisao cega Onda 1 - fontes e vigencia

- Baseline: `f814f80efbab84bf43b671bf544c4678d4dda82a`
- Execucao: `2026-07-13T07:58:57-03:00`
- Decisao: **NÃO CONFORME**
- Status: **BLOQUEADO**

## Resultado executivo

Foram inventariados 856 arquivos, 9726 cards publicados, 0 historicos e 13150 itens em quarentena. A projecao HTML local coincide com os 9726 IDs do JSON. O portal publico responde apenas com aviso de revisao; os dois JSONs de cards retornam 404.

O fechamento e BLOQUEADO: recibos nativos e `field_provenance` faltam em 9726/9726 publicados; 5038 cards divergem do SHA-256 local e 303 nao tem fonte local; 9611 cards ICMS estaduais nao tem evidencia estruturada de internalizacao; as datas juridicas de 9726 cards repetem a data de captura.

## Contagens integrais

| Classe | Entrada | Auditada | Resultado |
|---|---:|---:|---|
| Arquivos | 856 | 853 + 3 excluidos cegos | 856 inventariados |
| Publicados | 9726 | 9726 | vigente=9485; a_revalidar=241; historico=0 |
| Quarentena | 13150 | 13150 | gate_ok=13150; fonte_ausente=504 |
| Matriz fixa | 94 | 94 | OK=67; A VALIDAR=13; BLOQUEADO=14 |
| URLs unicas | 212 | 212 | 2xx=182; HTTP erro=5; rede/TLS=25 |
| PDFs | 4 | 335 paginas | erros=0 |
| XLSX | 2 | 4 abas | formulas=0 |

## Achados

1. Recibos/proveniencia ausentes em 100% dos publicados e quarentenados.
2. Datas `publicacao`, `inicio_vigencia` e `inicio_eficacia` iguais a `captured_on` em 9726; 351 cards tem limite literal passado e 217 seguem `vigente`.
3. Fonte: hash_ok=4385; hash_divergente=5038; ausente=303.
4. Probe literal: publicados ok=9228, falha=498; quarentena ok=12304, falha=846.
5. Internalizacao estadual estruturada: 0 de 9611.
6. `transicao_rt`: coerente em 9726/9726, sem sanar os bloqueios.

## Cadeias adversariais

cadeia re-derivada: baseline -> `git rev-parse HEAD` -> `f814f80efbab84bf43b671bf544c4678d4dda82a` -> bateu.

cadeia re-derivada: universo -> `git ls-tree` restrito -> 856 arquivos -> 853 lidos e 3 excluidos.

cadeia re-derivada: publicados -> SHA-256 `552ded43ab72c3fd94c6a92d64bdda554bc56372f668346a784070cac8878f20` -> 9726 unicos -> 9485 vigente, 241 a_revalidar, 0 historico.

cadeia re-derivada: quarentena -> SHA-256 `cb9ae22b8932ee8487606b8db2cb033900b5cacb8b42a3a3036f396a88f7a032` -> 13150 unicos -> gate_ok=13150.

cadeia re-derivada: fonte -> cada `source_path` relido e SHA-256 recalculado -> ok=4385, divergiu=5038, ausente=303.

cadeia re-derivada: vigencia -> datas versus captura e expressoes `ate/efeitos ate` -> sem prova=9726; limite passado=351; vigente_passado=217.

cadeia re-derivada: internalizacao -> 9611 cards estaduais ICMS -> evidencia estruturada=0 -> divergiu.

cadeia re-derivada: recibos -> busca item a item por `field_provenance`, `verification_receipt_id`, `verification_receipt` e duas capturas independentes -> completos=0 -> BLOQUEADO.

cadeia re-derivada: portal -> GET anonimo sem cookie -> raiz=200; JSONs=404/404 -> sem publicacao confrontavel.

cadeia re-derivada: matriz -> 27 UFs x 3 + BR x 13 -> 94 linhas -> bateu estruturalmente.

cadeia re-derivada: PDF/XLSX -> 335 paginas e 4 abas -> leitura estrutural completa.

## Comandos/testes

- `git -C "C:\Users\rafae\Documents\Codex\2026-06-14\pesquisa-na-mem-ria-profunda-l\worktrees\rjc-monitor-2026-07-13-wave1-fontes" rev-parse HEAD`
- `git -C "C:\Users\rafae\Documents\Codex\2026-06-14\pesquisa-na-mem-ria-profunda-l\worktrees\rjc-monitor-2026-07-13-wave1-fontes" status --short`
- `git -C "C:\Users\rafae\Documents\Codex\2026-06-14\pesquisa-na-mem-ria-profunda-l\worktrees\rjc-monitor-2026-07-13-wave1-fontes" ls-tree -r --name-only f814f80efbab84bf43b671bf544c4678d4dda82a -- data beneficios estados federal confaz scripts/validated_benefits.py`
- SHA-256 integral local; reconciliacao integral de IDs; GET anonimo com `Cookie:` vazio; pypdf em todas as paginas; ZIP/XML em todas as abas.

Tres artefatos previos foram excluidos da evidencia. Nenhum `auditoria/execucoes/**`, outro worktree ou temporario de outro revisor foi usado. Falhas permanecem A VALIDAR/BLOQUEADO; nenhum recibo foi fabricado.

Veredito: ausencia universal de recibos/proveniencia, datas juridicas sem prova e divergencias de fonte.

Decisao: NÃO CONFORME

Status: BLOQUEADO
