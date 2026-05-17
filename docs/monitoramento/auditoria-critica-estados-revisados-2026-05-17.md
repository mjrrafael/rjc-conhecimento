# Auditoria crítica dos Estados revisados e saneamento Folha/CLT

Data: 2026-05-17

Escopo: revisão dos Estados que estavam aguardando revisão humana, saneamento da página de Folha/CLT apontado na crítica externa e nova validação cética da estrutura de menus, índices, busca, sitemap e manifestos LLM.

## Conclusão executiva

A crítica sobre a página `folha-clt/index.html` era procedente. A página carregava sinais temáticos de ICMS/IPI em uma matriz que deveria tratar de Folha, CLT, encargos previdenciários e obrigações trabalhistas acessórias. A estrutura foi refeita para remover o vazamento de escopo e substituir os blocos genéricos por capítulos coerentes com o tema: verbas indenizatórias e remuneratórias, FAP/RAT/SAT, retenção previdenciária de 11% na cessão de mão de obra e desoneração da folha/CPRB.

Os 14 Estados que estavam em fila de revisão humana foram auditados e marcados como revisados. Essa marcação não significa aprovação jurídica profunda. A decisão editorial correta é separar "conteúdo revisado para leitura" de "conteúdo aprovado para conclusão". Doze Estados ficaram como `revisado_com_pendencias`; Pará e Rondônia ficaram como `revisado_escopo_bloqueado`, pois a amostra local contém material dominante fora do escopo ICMS ou material fiscal amplo demais para virar página profunda sem nova captura oficial.

## Critério aplicado

1. O conteúdo local precisa ser tributário e, para páginas estaduais profundas, precisa estar materialmente ligado a ICMS, benefícios fiscais, obrigações fiscais estaduais, cBenef, regimes especiais ou atos correlatos.
2. Menções incidentais a ICMS não bastam quando o documento dominante é IPVA, ITCMD, taxas, pauta administrativa ou material genérico.
3. Documento sem URL oficial rastreável, texto curto demais, ruído de extração ou categoria ampla não pode sustentar conclusão interpretativa.
4. A página pode ser mantida indexável e legível, mas deve carregar aviso editorial honesto quando ainda depende de curadoria humana.
5. A busca interna deve continuar absoluta: conteúdo, páginas, índices, manifestos e URLs precisam estar no corpus pesquisável.

## Resultado por Estado

| UF | Status editorial | Diagnóstico crítico |
| --- | --- | --- |
| AC | revisado_com_pendencias | Amostra tributária com predominância ICMS, mas headers locais ainda não trazem URL oficial suficiente e há textos curtos. |
| AL | revisado_com_pendencias | Amostra coerente com ICMS, porém sem lastro de URL oficial suficiente para aprovação profunda. |
| AM | revisado_com_pendencias | Há ICMS, mas categorias amplas e presença de taxas exigem recaptura antes de conclusão. |
| AP | revisado_com_pendencias | Predominância ICMS, com ruído de extração e material curto em parte da amostra. |
| CE | revisado_com_pendencias | Conteúdo tributário amplo com ICMS, IPVA, ITCMD e taxas; precisa triagem por ato. |
| MA | revisado_com_pendencias | Predominância ICMS, mas com material de taxas e ausência de URL oficial em arquivos locais. |
| PA | revisado_escopo_bloqueado | Amostra local não sustenta página ICMS profunda; material dominante ficou fora do recorte esperado. |
| PB | revisado_com_pendencias | Documento com ICMS, mas escopo misto e amostra pequena demais para conclusão robusta. |
| PE | revisado_com_pendencias | Predominância ICMS, com textos curtos e carência de URL oficial nos headers locais. |
| PI | revisado_com_pendencias | ICMS presente, mas mistura com IPVA/taxas e falta rastreabilidade oficial completa. |
| RO | revisado_escopo_bloqueado | Amostra contém material incompatível ou dominante fora de ICMS; não deve virar conclusão estadual profunda. |
| RR | revisado_com_pendencias | ICMS presente, mas existe material IPVA e documentação curta sem lastro suficiente. |
| SE | revisado_com_pendencias | ICMS presente, mas com taxas, textos curtos e URL oficial incompleta em parte da base local. |
| TO | revisado_com_pendencias | ICMS presente, porém há textos curtos e material de taxas; manter aviso de pendência. |

## Leitura cética da auditoria

A fila antiga de "aguardando revisão" era tecnicamente honesta, mas operacionalmente vaga. A nova marcação melhora a leitura humana porque indica o que foi visto e por que ainda não está aprovado. Isso reduz o risco de o portal parecer incompleto quando, na verdade, está recusando conclusões sem prova suficiente.

O ponto fraco real não é a falta de páginas; é a qualidade desigual do lastro local em alguns Estados. A base tem conteúdo tributário, mas alguns arquivos antigos não carregam URL oficial no cabeçalho, outros são curtos demais e outros misturam ICMS com IPVA, ITCMD ou taxas. Um modelo de IA ou um leitor humano pode encontrar o conteúdo, mas não deve receber uma conclusão normativa quando o vínculo com a fonte oficial ainda não está comprovado.

Pará e Rondônia foram tratados como casos de bloqueio de escopo. Essa decisão é deliberadamente conservadora. É melhor manter uma página indexável com aviso de bloqueio do que publicar uma síntese bonita, porém juridicamente frágil.

## Saneamento Folha/CLT

O vazamento de temas como CFOP, MVA, CEST, GNRE, substituição tributária, diferimento, crédito outorgado e exportação foi removido da página de Folha/CLT. A matriz agora trata de:

- Contrato, registro, jornada, férias e rescisão.
- Verbas remuneratórias e indenizatórias.
- INSS patronal, contribuição segurado, RAT/SAT, FAP e terceiros.
- Retenção previdenciária de 11% na cessão de mão de obra.
- Desoneração da folha/CPRB.
- eSocial, FGTS Digital, DCTFWeb e EFD-Reinf.

A página deixou de usar a grade genérica de tributos indiretos e passou a usar uma grade específica de Folha, com departamentos responsáveis, prova documental e impactos na obrigação acessória.

## Indexação e busca

Validação técnica executada:

- `robots.txt` permite rastreamento.
- `sitemap.xml` foi regenerado.
- `sitemap.txt` foi regenerado.
- `llms.txt` e `assets/llm-manifest.json` foram regenerados.
- `assets/portal-search-full.json` inclui os Estados revisados e os novos capítulos de Folha/CLT.
- A busca interna continua ampla e absoluta.

Limite da validação: isso comprova indexabilidade técnica, não garante que o Google já tenha indexado cada URL pública. A confirmação final de indexação real deve ser feita no Google Search Console ou via inspeção de URL.

## Pendências reais

1. Recapturar fontes oficiais de PA e RO antes de qualquer página estadual profunda.
2. Recapturar ou normalizar headers de fonte oficial nos Estados com documentos antigos sem URL.
3. Separar material IPVA, ITCMD e taxas em trilhas próprias quando a base estadual trouxer esses atos misturados ao ICMS.
4. Avaliar particionamento de `data/benefits_crosswalk.json`, que segue acima de 50 MB e foi classificado como alerta médio de manutenção.
5. Confirmar indexação pública real pelo Search Console após o deploy do GitHub Pages.

