# Achados e pendências da reconstrução

## P0 — conteúdo público ainda não está pronto para retorno

O acervo legado não deve ser reintroduzido por volume, similaridade textual ou confiança de busca. A reconstrução atual contém apenas dois cards de teste, mantidos fora da superfície pública por ausência de recibos nativos, revisão cega isolada e cobertura nacional.

## P1 — publicação do CTN foi corrigida, mas requer revalidação

**Status: CORRIGIDO, aguardando revisor independente.** A data 27/10/1966 antes citava um corpo consolidado que não apresentava a publicação. O registro oficial específico do Senado foi capturado duas vezes em `act_capture_receipts_tentativa_3.json` e `act_capture_receipts_tentativa_4.json`; ele agora sustenta exclusivamente `temporal.publicacao` do card do CTN.

## P1 — recibo local não substitui recibo nativo

**Status: A VALIDAR.** O capturador registra redirects, cabeçalhos, corpo e hash, mas todos os recibos continuam `LOCAL_REPRODUCIBLE_NOT_PLATFORM_NATIVE`. A publicação exige recibos confrontáveis da plataforma e novo refetch cego.

## P1 — matriz nacional incompleta por falhas técnicas de captura

**Status: A VALIDAR.** Após nova tentativa, SP/Assembleia foi capturada. Permanecem falhas registradas para Planalto, STF, DOE-RJ, DOE-RN e SEFAZ-RN. A lista e as causas ficam em `recaptura_criticos_tentativa_4/http_capture_receipts.json`; nenhuma delas foi convertida em fonte validada.

## Próximas ações verificáveis

1. Revalidar as correções do CTN e a cobertura de proveniência com revisor cego.
2. Resolver ou substituir por endpoint oficial acessível cada captura institucional falha, preservando a tentativa original.
3. Ler atos individuais por assunto/UF, extrair os campos e só então colocar cards na fila de aprovação.
4. Antes de publicar, executar inventário integral, gates independentes, PR, CI, Pages e confronto HTTP/hash.
