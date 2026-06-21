# Plano - PIS/Cofins por NCM, setor e aplicacao

## P0 - Enquadramento

Objetivo: criar uma nova secao do portal para PIS/Pasep e Cofins por NCM, setor e aplicacao, cobrindo tratamentos diferentes da regra habitual, especialmente:

- monofasico;
- aliquota zero;
- suspensao;
- incidencia concentrada;
- importacao com tratamento especifico;
- regimes setoriais com recorte por produto, NCM, destinatario, finalidade ou habilitacao;
- qualquer outro tratamento federal de PIS/Cofins que dependa de mercadoria, NCM, setor ou aplicacao concreta.

Regra central: nenhum NCM entra como aplicavel/publicavel sem fonte oficial primaria resolvivel, trecho legal ou normativo em tela, vigencia/eficacia, condicoes e status explicito.

## Escopo negativo

Nao publicar como beneficio por NCM:

- regra geral de regime cumulativo ou nao cumulativo sem recorte por NCM, produto, setor ou aplicacao;
- comentario, artigo, tabela privada, planilha de fornecedor ou resumo de consultoria sem fonte oficial primaria;
- enquadramento inferido apenas por palavra-chave;
- NCM citado em fonte secundaria sem confirmacao no ato oficial;
- produto descrito genericamente quando a norma exige lista, codigo, anexo ou condicao especifica ainda nao capturada.

## Fontes oficiais obrigatorias

Inventario inicial, a ser expandido por crawler e revisao manual:

- Planalto: leis compiladas e medidas legais que criam, alteram, revogam ou prorrogam tratamentos de PIS/Cofins.
- Receita Federal/SIJUT: IN RFB 2.121/2022 e atos posteriores; solucoes de consulta somente como interpretacao auxiliar, nunca como origem do beneficio.
- DOU/IN.gov.br: atos publicados recentemente, decretos e normas ainda nao consolidados no Planalto/SIJUT.
- DIRBI/transparencia RFB: Portaria RFB 319/2023, Portaria RFB 688/2026, IN RFB 2.198/2024 e alteracoes, como fonte oficial de inventario/controle de beneficios; nao como fundamento autonomo do tratamento.
- TIPI/NCM oficial: TIPI, atos RFB de adequacao da TIPI e atos Gecex/Camex que alterem NCM, apenas para validar codigo e descricao vigentes. NCM vigente nao prova beneficio.
- Portal SPED/SVRS quando o tratamento tiver reflexo documental em CST, XML ou escrituracao.
- Portal Nacional da Tributacao sobre Consumo e CGIBS apenas para convivencia/transicao CBS quando houver reflexo no tratamento antigo ou futura migracao.

Fontes iniciais ja identificadas como nucleares:

- Lei 10.147/2000 - incidencia concentrada/monofasica para produtos especificos.
- Lei 10.485/2002 - setor automotivo e autopecas.
- Lei 10.637/2002 - PIS nao cumulativo e referencias cruzadas.
- Lei 10.833/2003 - Cofins nao cumulativa e referencias cruzadas.
- Lei 10.865/2004 - PIS/Cofins-Importacao e reducoes a zero.
- Lei 10.925/2004 - reducoes a zero para insumos/produtos agropecuarios e correlatos.
- Lei 13.097/2015 - aliquota zero e regimes de PIS/Cofins para itens especificos.
- IN RFB 2.121/2022 - consolidacao infralegal, com validacao contra lei quando houver divergencia.

Fontes adicionais localizadas na revisao adversarial de 2026-06-21 e que passam a ser obrigatorias no inventario antes de qualquer afirmacao de completude:

- Decreto 5.195/2004 e Decreto 5.630/2005 - regulamentacao da reducao a zero ligada ao art. 1o da Lei 10.925/2004.
- Decreto 6.426/2008 - reducao a zero para produtos quimicos/farmaceuticos e anexos por NCM.
- Decreto 6.707/2008 e Decreto 8.442/2015 - bebidas, revogacoes e regime setorial posterior.
- Lei 11.196/2005 - reducoes e regimes com impacto em PIS/Cofins por produto/aplicacao.
- Lei 11.488/2007 - REIDI e hipoteses de suspensao/isencao ligadas a aplicacao e habilitacao.
- Lei 12.839/2013 - azeites e itens especificos adicionados ao universo de aliquota zero.
- Lei 14.973/2024, IN RFB 2.198/2024 e alteracoes - DIRBI/controle de beneficios fiscais.
- Portaria RFB 319/2023 e Portaria RFB 688/2026 - transparencia ativa de beneficios, com anexos que listam beneficios PIS/Cofins-Importacao e mercado interno por fundamento legal/NCM.
- Lei 15.394/2026 - residuos e aparas, com tratamento especifico de credito/isencao.
- Decreto 12.991/2026 - combustiveis/querosene de aviacao e biodiesel, com reducao prorrogada.

Fontes com resolubilidade HTTP 200 testada em 2026-06-21:

- Planalto: Lei 10.147/2000, Lei 10.485/2002, Lei 10.637/2002, Lei 10.833/2003, Lei 10.865/2004, Lei 10.925/2004, Lei 12.839/2013, Lei 13.097/2015, Lei 15.394/2026, Decreto 5.195/2004, Decreto 5.630/2005, Decreto 6.426/2008, Decreto 6.707/2008, Decreto 8.442/2015 e Decreto 12.991/2026.
- Receita Federal/SIJUT: consulta recente de atos RFB com Portaria RFB 688/2026, IN RFB 2.294/2025 e atos RFB/CGIBS de transicao.

Este teste de HTTP prova apenas que a fonte resolve. Nao prova que todos os artigos, anexos, revogacoes e alteracoes foram extraidos.

## Banco de dados profundo no G:

Pasta proposta:

`G:\Meu Drive\RJC\BD_LEGISLACAO\PIS_COFINS_NCM`

Estrutura proposta:

- `fontes-brutas/`: HTML/PDF/TXT capturados de fonte oficial, preservando data de captura e URL.
- `fontes-normalizadas/`: texto limpo, com hash do bruto, sem perder artigo/inciso/anexo.
- `inventario-fontes.ndjson`: um registro por ato/fonte capturada.
- `extracoes-candidatas.ndjson`: tudo que parece NCM/produto/tratamento antes da validacao.
- `pis-cofins-ncm.validado.ndjson`: somente registros publicaveis.
- `pis-cofins-ncm.quarentena.ndjson`: registros com link quebrado, escopo incerto, vigencia duvidosa ou inferencia por palavra-chave.
- `logs/`: data, comando/fonte, HTTP, hash, erros e decisoes.

O repositorio deve receber apenas:

- scripts de captura/extracao/auditoria;
- indices publicaveis compactos;
- paginas HTML geradas;
- manifest/llms/search;
- ledger da rodada.

## Contrato do registro publicavel

Cada registro publicado deve conter:

- `id`;
- `ncm` ou intervalo/lista com granularidade explicita;
- `descricao_ncm`;
- `setor`;
- `aplicacao`;
- `tratamento`: `monofasico`, `aliquota_zero`, `suspensao`, `incidencia_concentrada`, `importacao_especifica`, `regime_especial`, `outro`;
- `tributo`: PIS, Cofins, PIS-Importacao, Cofins-Importacao ou combinacao;
- `ato_oficial`: tipo, numero, artigo, inciso, anexo, URL oficial e HTTP;
- `trecho_legal`;
- `publicacao`;
- `inicio_vigencia`;
- `inicio_eficacia`;
- `fim_vigencia`;
- `condicoes`;
- `vedacoes`;
- `prova_documental`;
- `cst_entrada_saida` quando a fonte permitir;
- `transicao_cbs`: relacao com CBS/LC 214/2025;
- `status`: `vigente`, `historico`, `a_validar`, `a_revalidar`;
- `verificado_em`;
- `provenance`;
- `classification_confidence`;
- `publishable`.

## Arquitetura da nova secao

Rotas propostas:

- `federal/pis-cofins-ncm.html`: entrada executiva, filtros e aviso de metodologia.
- `federal/legislacao/pis-cofins/ncm.html`: tabela validada por NCM, com completude declarada por lote/fonte.
- `federal/legislacao/pis-cofins/monofasico.html`: recorte monofasico/incidencia concentrada.
- `federal/legislacao/pis-cofins/aliquota-zero.html`: recorte aliquota zero.
- `federal/legislacao/pis-cofins/setores.html`: agrupamento por setor.
- `data/pis-cofins/ncm.ndjson`: shard publicavel.
- `data/pis-cofins/quarentena.ndjson`: nao servido nos indices publicos; usado apenas em auditoria local.

Filtros esperados:

- NCM;
- descricao;
- setor;
- tratamento;
- tributo;
- operacao interna/importacao;
- vigente/historico/a validar;
- fonte legal;
- data de verificacao.

## Criterios de pronto

| # | Criterio | Metodo | Status |
|---|---|---|---|
| 1 | Inventario oficial cobre as fontes nucleares de PIS/Cofins por NCM | crawler + lista de fontes oficiais + hashes | A VALIDAR |
| 2 | Todo registro publicavel tem fonte primaria HTTP 200 | auditoria de links | A VALIDAR |
| 3 | Todo registro tem vigencia/eficacia/fim/status | auditoria temporal | A VALIDAR |
| 4 | Nenhum registro keyword-only entra como publicavel | auditoria de provenance/confidence | A VALIDAR |
| 5 | Quarentena nao aparece em HTML, busca, llms ou sitemap | auditoria de isolamento | A VALIDAR |
| 6 | HTML, NDJSON, busca e llms convergem por id | auditoria de divergencia | A VALIDAR |
| 7 | Todo registro PIS/Cofins tem selo de transicao CBS | auditoria de reforma/transicao | A VALIDAR |
| 8 | Paginas novas renderizam e navegam corretamente | build + auditoria HTML | A VALIDAR |
| 9 | PR publicado so apos hard gates verdes | PR + Pages + HTTP publico | A VALIDAR |

## Plano de execucao

1. Criar o inventario oficial de fontes.
2. Capturar fontes brutas no `G:` com URL, HTTP, data, hash e formato.
3. Normalizar texto preservando artigo, inciso, paragrafo, anexo e tabelas.
4. Extrair candidatos por NCM, produto, setor, aliquota zero, monofasico e termos correlatos.
5. Fazer segunda derivacao independente por artigo/anexo para pegar itens que nao contenham a palavra NCM.
6. Classificar cada candidato em tratamento, setor, operacao e tributo.
7. Validar vigencia, eficacia, revogacao, alteracoes e condicoes.
8. Separar `validado` de `quarentena`.
9. Gerar as paginas e indices.
10. Rodar hard gates existentes e novos gates especificos de PIS/Cofins por NCM.
11. Fazer passe adversarial com testes que tentem provar falso positivo, omissao e vazamento de quarentena.
12. Abrir PR de conteudo, mergear somente com gates verdes e verificar HTTP publico.

## Revisao adversarial do plano

Possiveis falhas:

- Fonte infralegal consolidada pode esconder alteracao legal; a IN RFB 2.121/2022 nao pode substituir a lei.
- Algumas regras sao por descricao/produto/finalidade, nao por NCM; forcar NCM pode publicar escopo falso.
- Monofasico e aliquota zero podem coexistir ou variar por etapa da cadeia; a tabela precisa distinguir fabricante/importador/atacadista/varejista.
- Importacao e mercado interno podem ter tratamentos diferentes para o mesmo NCM.
- A reforma tributaria pode mudar a leitura futura pela CBS, mas nao revoga automaticamente a regra antiga antes da data legal.
- Web search pode perder atos sem boa indexacao; e necessario crawler por fontes oficiais, nao apenas busca textual.
- Publicar uma tabela incompleta sem dizer que e incompleta pode induzir erro operacional.

## Plano corrigido apos revisao adversarial

- A primeira entrega publicavel deve ser marcada como `base inicial validada`, nao como base exaustiva nacional.
- O portal deve diferenciar claramente `NCM confirmado`, `descricao sem NCM` e `NCM a validar`.
- O registro deve ter campo de etapa da cadeia: fabricante, importador, distribuidor, varejista, consumidor final ou nao especificado.
- Deve haver campo separado para mercado interno e importacao.
- A IN RFB 2.121/2022 entra como consolidacao, mas cada regra publicavel deve apontar tambem para a lei/decreto quando a propria IN remeter ao fundamento.
- A pesquisa completa deve combinar: lista normativa conhecida, busca oficial, crawler SIJUT/Planalto/DOU e extracao dos atos ja existentes no BD.
- A pagina deve mostrar aviso: "tabela operacional em curadoria; aplicar somente registros com status vigente e prova legal completa".
- Subida no site somente por PR, com hard gates e verificacao HTTP publica.

## Revisao adversarial 2026-06-21

Resultado: o plano existe e foi corrigido, mas a certeza plena de que "toda a legislacao que trata da materia" ja foi pesquisada continua `A VALIDAR`.

O erro mais provavel que ainda resta seria omitir ato setorial que nao usa a expressao "NCM" no texto, mas cria tratamento por descricao, destinatario, finalidade, habilitacao ou etapa da cadeia. A evidencia que derruba esse erro e um inventario executavel por fonte oficial, com captura bruta, hash, extracao por artigo/anexo e segunda derivacao por fundamento legal/DIRBI. Esta evidencia ainda nao foi produzida integralmente.

Achados da revisao:

- O plano inicial citava as leis nucleares, mas ainda nao trazia DIRBI/Portaria RFB 688/2026 como fonte obrigatoria de inventario de beneficios.
- Faltavam decretos e atos com anexos por NCM, especialmente Decreto 6.426/2008, Decreto 5.195/2004, Decreto 5.630/2005, Decreto 6.707/2008 e Decreto 8.442/2015.
- Faltava registrar que solucoes de consulta ajudam a revelar falsos positivos e interpretacoes, mas nao criam beneficio publicavel.
- A expressao "tabela completa por NCM" podia induzir o leitor a acreditar em exaustividade antes do crawler; foi corrigida para "tabela validada por NCM, com completude declarada por lote/fonte".
- A pesquisa local encontrou atos recentes ja capturados no portal, incluindo Portaria RFB 688/2026, Lei 15.394/2026 e Decreto 12.991/2026, que precisam entrar no banco profundo antes de qualquer publicacao operacional.

Porta de saida para poder afirmar completude com seguranca:

1. `inventario-fontes.ndjson` gerado por crawler de Planalto, SIJUT/RFB, DOU/IN.gov.br e fontes oficiais de TIPI/NCM.
2. Todas as fontes do inventario com HTTP, data de captura, hash bruto, hash normalizado e origem oficial.
3. Extracao dupla: uma por termos (`NCM`, `aliquota zero`, `monofasico`, `suspensao`, `PIS`, `Cofins`) e outra por artigo/anexo/fundamento legal/DIRBI, para pegar normas sem palavra-chave obvia.
4. Relatorio de omissoes provaveis: atos revogados, atos alteradores, anexos substituidos, regimes por habilitacao e regimes sem NCM explicito.
5. Auditoria adversarial automatizada tentando provar falso positivo, falso negativo, vigencia errada, link quebrado e escopo inferido.
6. So depois disso a secao pode sair de `A VALIDAR` para `base inicial validada`; "exaustiva nacional" so se o inventario oficial fechado tambem for publicado com hashes e data.

## Decisao de publicacao

Pode subir no site, mas em duas etapas:

1. Primeiro PR: infraestrutura, metodologia, pagina de entrada e banco vazio/diagnostico sem afirmar tratamento por NCM.
2. Segundo PR: primeiros lotes de registros `vigente` e `publishable=true`, com fonte oficial, vigencia e prova.

Nao publicar lote completo se a pesquisa ainda estiver em andamento. Registros incompletos ficam em quarentena.
