# Achados e pendências — 2026-07-13

Status operacional: **BLOQUEADO TEMPORÁRIO**.

## Achados materiais

- A produção continua contida em quatro artefatos neutros. Raiz, `index.html`, `404.html`, `robots.txt` e `llms.txt` foram confrontados por HTTP e SHA-256; as rotas tributárias testadas retornam a página 404 segura.
- O corpus rastreado não satisfaz o contrato v3: 9.726 benefícios não têm `field_provenance` nem recibos de verificação, 9.726 repetem data de captura em campos jurídicos e 9.611 cards estaduais de ICMS não têm prova específica de internalização.
- A quarentena contém 13.150 registros materiais sem fingerprints. Eles não foram encontrados na projeção Pages segura, mas continuam no repositório público e fazem falhar a álgebra pública fail-closed.
- Nenhuma das 94 raízes mínimas tem recibo HTTP nativo confrontável. Os revisores encontraram milhares de hashes divergentes e centenas de raízes locais ausentes.
- Os 13 gates materiais v3 foram adicionados ao código e falham diante do corpus inseguro. A certificação de eficácia é impossível nesta execução: não existem duas raízes administrativas preexistentes, assinadas e independentes, nem runners nativos externos.
- A Onda 2 revisou `074bff85c7c560386ca0ed7f0802d4e896534571`. O fix posterior de preservação da matriz está em `3d27f5a71f23358b32673afd767d7ef9295aa0a9`; logo não existe revisão cega do SHA final.
- O workflow de PR não chama os gates pós-publicação `audit_publication` e `audit_public_http_hashes`; ambos existem e foram executados localmente em estado fail-closed.

## Correções após a revisão adversarial

- O caminho `RJC_MONITOR_RUN` foi confinado a `auditoria/execucoes/monitor-v3-*`; as duas travessias apontadas pela Onda 2 agora são rejeitadas antes de qualquer escrita.
- Os gates passaram a rejeitar card sem campos jurídicos/datas, recibo cujo hash não corresponde ao card, internalização sem vínculo a card/benefício, inventário sem hashes, matriz sem vínculo a recibo nativo, arquivo extra na superfície e quarentena sem fingerprints materiais.
- Os gates pós-publicação foram incluídos no `workflow_dispatch`, preservando a ordem PR → merge → Pages → prova pós-deploy.

Essas correções ocorreram depois do SHA entregue à Onda 2 e, por isso, melhoram o fail-closed mas não removem o bloqueio de certificação.

## Pendências bloqueantes

1. Provisionar duas raízes de confiança independentes e preexistentes, com runners/atestados verificáveis pela plataforma.
2. Disponibilizar exportação nativa imutável dos tool calls, prompts, caminhos lidos e recibos HTTP, ou executar a revisão em plataforma que a forneça.
3. Sanear ou remover integralmente o corpus legado, com refetch oficial e proveniência material campo a campo; dúvida implica quarentena sem conteúdo material público.
4. Reexecutar toda a Onda 2 em worktrees efetivamente isolados sobre um único SHA congelado.
5. Corrigir os bypasses encontrados, completar os gates de publicação no fluxo e somente então marcar a PR pronta.

Até isso ocorrer, a PR deve permanecer draft e não pode ser mesclada.
