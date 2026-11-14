# Reconstrução nacional por prova material — 2026-07-16

## 1. Resumo de uma linha

Reconstruir o portal tributário a partir da legislação primária, restituindo ao
público somente regras que possam ser explicadas a uma pessoa e verificadas por uma IA.

## 2. Contexto / objetivo

O portal deve ser gratuito, acessível e útil para consulta tributária brasileira. A
medida de contenção anterior não é a entrega: os cards devem ser corrigidos pela
leitura do ato oficial e então republicados. Uma lacuna de prova vira fila de
pesquisa; não é licença para inventar, resumir por memória ou manter o trabalho
vazio.

## 3. Definição de prova material

Para cada campo jurídico não nulo, há: ato identificado (tipo, número, órgão e
jurisdição), URL oficial final HTTP 200, corpo com hash, trecho literal, localizador,
regra de normalização, e recibos de captura e refetch independentes. Publicação,
vigência, eficácia e término são campos distintos. `AUSENTE`, `INDETERMINADO` e
`NÃO_APLICÁVEL` não podem ser substituídos por metadados técnicos.

Para pessoas, a norma será exibida como explicação clara, escopo, condições, período,
alertas e link ao ato. Para IA, o mesmo conteúdo terá JSON estruturado, proveniência
por campo, identificador estável, datas tipadas e texto-fonte/localizador.

## 4. Inventário das fontes

- União: Planalto, DOU/Imprensa Nacional, RFB/Normas, PGFN, CONFAZ, CGIBS/Portal
  Nacional da Tributação sobre Consumo, Senado, STF, STJ e CARF.
- Estados: para cada UF, SEFAZ/legislação, Diário Oficial e Assembleia Legislativa.
- O portal e seus derivados: HTML, dados, busca, sitemap, manifestos, robots e llms.txt.

Portal, índice ou homepage servem apenas para descoberta. A prova de uma regra nasce
do ato e do dispositivo localizável.

## 5. Critérios de pronto (criterio → evidencia)

| ID | criterio falsificável | método | evidencia |
| --- | --- | --- | --- |
| PM-001 | matriz possui 81 linhas estaduais e famílias federais exigidas | geração e contagem por UF/classe | escopo YAML e matriz CSV |
| PM-002 | fonte validada tem captura anônima, cadeia de redirect, hash e identificação institucional | refetch | banco de capturas e corpos externos |
| PM-003 | todo campo de card público possui ato, trecho, localizador, hash e duas capturas | auditoria de proveniência | `field_provenance` e ledger |
| PM-004 | data jurídica não deriva de captura, build, mtime, TODAY ou outro campo | testes negativos | log de auditoria de datas |
| PM-005 | público, busca e IA projetam somente cards aprovados | build, crawl e hash | logs e inventário de superfície |
| PM-006 | PR, CI, Pages e refetch pós-deploy correspondem ao mesmo SHA | GitHub + HTTP | prova de publicação |

## 6. Fases (G0..G5)

- G0: contrato e critérios — executado antes da captura.
- G1: matriz fechada de fontes e capturas institucionais — em execução; há 96 linhas e cinco falhas de captura registradas.
- G2: leitura dos atos, extração de cards e derivados humano/IA — executado somente para dois cards não públicos.
- G3: refetch e revisão adversarial por fonte crua — encontrou defeito de publicação do CTN; correção aguarda revalidação independente.
- G4: auditorias, mutações de proveniência e comparação de superfícies — parcialmente executado; testes de falha segura existem, certificação independente não.
- G5: PR, CI, Pages e validação HTTP/hashes em produção — não iniciado; não há autorização para publicação.

## 7. Pendências para fechar 100%

O acervo legado não pode ser tomado como fonte jurídica. Cada item terá de ser
rederivado. O site continua em contenção até PM-001 a PM-005 serem satisfeitos.

## 8. Próximos passos

- [x] Gerar a matriz nacional de fontes candidatas, sem chamar candidatura de validade jurídica.
- [x] Capturar e classificar as fontes institucionais, preservando falhas e reintentos.
- [x] Selecionar dois atos federais iniciais, extrair campos e redigir prévia humana/IA não pública.
- [ ] Revalidar correções, concluir a leitura nacional e submeter ao refetch, build e publicação.

## 9. Decisão do usuário registrada

O usuário determinou reconstruir, corrigir e recolocar o portal no ar, com normas
legíveis por pessoas e por IA; não aceitar um portal vazio como resultado final.
