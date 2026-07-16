# Revalidação material do corpus tributário — 2026-07-16

- Janela da execução: `2026-07-16T13:07:43-03:00` a `2026-07-16T13:20:04-03:00` (`America/Sao_Paulo`).
- Base revisada: `f814f80efbab84bf43b671bf544c4678d4dda82a`.
- Estado: **BLOQUEADO TEMPORÁRIO — conteúdo tributário não autorizado para publicação**.

## Correções aplicadas

1. Foi criado um revalidador *fail-closed*: ele examina todos os registros e nunca promove card legado a conteúdo público.
2. A regra de ICMS passou a rejeitar explicitamente `NÃO_COMPROVADA` e a exigir prova material tanto para `COMPROVADA` quanto para `DISPENSADA_COM_FUNDAMENTO`.
3. Os geradores deixam de depender do perfil de outro computador. O acervo local é agora configurável por `RJC_BD_LEGISLACAO`, com fallback relativo ao perfil em uso.

## Resultado integral

| Conjunto | Quantidade | Destino da revisão |
|---|---:|---|
| Cards legados | 9.726 | `QUARENTENA_NAO_PUBLICA` |
| Quarentena sem efeito favorecido literal | 8.008 | `DESCARTAR_NAO_BENEFICIO` |
| Quarentena com possível efeito favorecido | 5.142 | `QUARENTENA_REVALIDAR_BENEFICIO` |
| Total | 22.876 | Nenhum registro promovido |

Foram consultadas 115 URLs oficiais sem autenticação: 103 responderam HTTP 200; 12 permaneceram não confirmadas (erro, indisponibilidade ou HTTP 404). As capturas e o ledger individual ficaram preservados em arquivo local de evidências, fora do repositório público. São recibos locais reprodutíveis, não recibos nativos da plataforma, e portanto **não constituem prova suficiente para publicação**.

## Motivos do bloqueio

- Todos os 9.726 cards têm pelo menos uma falha material: datas jurídicas herdadas da captura, ausência de proveniência por campo, ausência de recibo de verificação ou de prova de internalização.
- A cobertura existente só alcança 14 das 28 jurisdições esperadas (BR + 27 UFs) e não preenche a matriz obrigatória de fontes estaduais e federais.
- O repositório público ainda expõe por URL bruta o arquivo de quarentena e corpus legado. A exclusão do GitHub Pages não controla esse acesso.
- Não há duas raízes independentes de confiança nem execução dos 13 gates v3 requeridos.
- O ambiente não permite certificar isolamento de leitura entre revisores, portanto a independência das revisões não pode ser atestada.

## Próxima ação obrigatória

Antes de qualquer reabertura, separar o corpus/evidências em armazenamento privado e retirar a quarentena e os dados jurídicos não comprovados da superfície pública do repositório, incluindo validação de histórico, forks e cache. Depois, reobter fontes primárias, preencher proveniência por campo e repetir as duas ondas de revisão em ambientes realmente isolados.
