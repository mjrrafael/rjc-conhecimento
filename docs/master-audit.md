# Auditoria Mestre v2

Gerado em 2026-06-15.

Este arquivo resume cobertura e cruzamentos do Portal RJC Tributario Aberto. Ele e uma trilha de auditoria, nao um parecer tributario.

## Cobertura

- Fontes registradas: 210
- Requisitos federais mapeados: 15
- Requisitos federais publicados: 11
- Requisitos federais com fonte local disponivel: 4
- Estados profundos: 13
- Estados aguardando revisao: 0
- Estados revisados sem aprovacao profunda: 14
- Entradas validadas na matriz de beneficios: 9727
- Entradas em quarentena editorial: 13137
- Entradas com NCM/TIPI: 1752
- Entradas com CEST: 174
- Entradas com cBenef: 3633

## Lacunas Federais

| Tema | Status | Minimo editorial | Fontes locais |
| --- | --- | --- | --- |
| IRPJ | publicado_v1 | regra matriz, contribuinte, lucro real, presumido, arbitrado, adicionais, pagamentos, ECF e prova | Decreto_9580_2018_Regulamento_IRPJ.txt, Lei_9430_1996_Compilada_IRPJ.txt |
| CSLL | publicado_v1 | base, aliquotas, adicional, compensacao, base negativa, ECF e prova | Lei_7689_1988_CSLL_Original.txt, Lei_15079_2024_Adicional_CSLL.txt |
| PIS/Pasep | publicado_v1 | cumulativo, nao cumulativo, importacao, monofasico, aliquota zero, creditos e EFD | Lei_10637_2002_PIS_Nao_Cumulativo.txt, IN_RFB_2121_2022_PIS_COFINS_Parte1.txt |
| Cofins | publicado_v1 | cumulativo, nao cumulativo, importacao, retencoes, monofasico, creditos e EFD | Lei_10833_2003_Compilada_COFINS.txt, LC_70_1991_COFINS_Original.txt |
| IPI | publicado_v1 | industrializacao, equiparados, fato gerador, TIPI, suspensoes, isencoes, ZFM e prova | Decreto_7212_2010_RIPI.txt, TIPI_Vigente_2022_Parte1.txt |
| IOF | publicado_v1 | credito, cambio, seguro, titulos, valores mobiliarios, aliquotas e alteracoes vigentes | Decreto_6306_2007_Regulamento_IOF.txt, Decreto_12499_2025_IOF_Alteracoes2.txt |
| IRPF e pessoa fisica | fonte_local_disponivel | rendimentos, deducoes, ganho de capital, tabela progressiva, declaracao e prova | Lei_9250_1995_IRPF.txt, Lei_15191_2025_IRPF_Tabela_Progressiva.txt |
| Simples Nacional e MEI | fonte_local_disponivel | enquadramento, anexos, sublimites, segregacao de receita, monofasico/ST/retencoes e PGDAS-D | LC_123_2006_Simples_Nacional.txt, LC_128_2008_MEI.txt |
| Lucro Real | publicado_v1 | adicoes, exclusoes, compensacoes, estimativa, trimestral/anual, ECD, ECF e prova contabil | Decreto_9580_2018_Regulamento_IRPJ.txt, Lei_9430_1996_Compilada_IRPJ.txt |
| Lucro Presumido | publicado_v1 | percentuais, segregacao de receita, limite, retencoes, PIS/Cofins cumulativo e ECF | Lei_8981_1995_Lucro_Real_Presumido.txt, Decreto_12808_2026_Lucro_Presumido.txt |
| Lucro Arbitrado | fonte_local_disponivel | hipoteses de arbitramento, base, percentuais, provas e riscos | Lei_8981_1995_Lucro_Real_Presumido.txt, Decreto_9580_2018_Regulamento_IRPJ.txt |
| Importacao, exportacao e regimes aduaneiros | fonte_local_disponivel | II, IPI importacao, PIS/Cofins-Importacao, despacho, regimes especiais, drawback, REINTEGRA e prova | Decreto_6759_2009_Regulamento_Aduaneiro.txt, Lei_10865_2004_PIS_COFINS_Importacao.txt |
| Beneficios federais, DIRBI e reducao de beneficios | publicado_v1 | habilitacao, fruicao, declaracao, DIRBI, reducao de beneficios, prova e controles | Lei_14973_2024_DIRBI.txt, Lei_15321_2025_DIRBI_Obrigatoriedade.txt, Decreto_12861_2026_Regulamento_Beneficios.txt |
| Reforma Tributaria | publicado_v1 | EC 132, LC 214, LC 227, Decreto CBS, Resolucao IBS, Portaria comum, Ato Conjunto 2026, CST, cClassTrib, cCredPres, transicao e documentos fiscais | EC_132_2023_Reforma_Tributaria.txt, LC_214_2025_Compilada_IBS_CBS_IS.txt, LC_227_2026_Comite_Gestor_IBS.txt, data/legal_sources/reforma_tributaria/Decreto_12955_2026_Regulamento_CBS.txt, data/legal_sources/reforma_tributaria/Resolucao_CGIBS_6_2026_Regulamento_IBS.txt, data/legal_sources/reforma_tributaria/Portaria_Conjunta_MF_CGIBS_7_2026.txt, data/legal_sources/reforma_tributaria/Ato_Conjunto_RFB_CGIBS_1_2025_Obrigacoes_2026.txt |
| Folha, CLT e previdenciario | publicado_v1 | contrato, jornada, salario, encargos, seguridade, eSocial, DCTFWeb, Reinf, FGTS e prova | Lei_8212_1991_Custeio_Previdencia.txt, Lei_8213_1991_Beneficios_Previdencia.txt |

## Estados

| UF | Status | Docs | Alertas principais | Proximo passo |
| --- | --- | ---: | --- | --- |
| AC | revisado_com_pendencias | 6 | contém IPVA, contém ITCMD/ITCD, contém Taxas, fonte local sem URL oficial no cabeçalho | Recapturar RICMS, beneficios de ICMS e atos modificadores no portal oficial do Acre, com URL oficial e limpeza de escopo. |
| AL | revisado_com_pendencias | 3 | fonte local sem URL oficial no cabeçalho, texto curto para RICMS/benefícios | Recapturar RICMS, beneficios e ST no portal oficial de Alagoas, com URL oficial, vigencia e hash por fonte. |
| AM | revisado_com_pendencias | 4 | categoria não específica de ICMS, contém IPVA, contém ITCMD/ITCD, contém Taxas | Separar Codigo Tributario, RICMS, beneficios e atos modificadores do Amazonas, mantendo apenas trilha de ICMS nas paginas de ICMS. |
| AP | revisado_com_pendencias | 7 | contém Taxas, fonte local sem URL oficial no cabeçalho, ruído de extração/encoding, texto curto para RICMS/benefícios | Recapturar RICMS, beneficios e anexos do Amapa em fonte oficial limpa antes de aprovar analise profunda. |
| BA | publicado_v1 | 15 | sem alerta automatizado | Bahia publicada como pÃƒÂ¡gina profunda: Lei do ICMS, RICMS, anexos, substituiÃƒÂ§ÃƒÂ£o tributÃƒÂ¡ria, DESENVOLVE, PROIND, PRONAVAL, crÃƒÂ©dito presumido, informÃƒÂ¡tica/eletrÃƒÂ´nica, atos da LC 160/ConvÃƒÂªnio 190 e EFD dos incentivos. |
| CE | revisado_com_pendencias | 8 | categoria não específica de ICMS, contém IPVA, contém ITCMD/ITCD, contém Taxas | Recapturar RICMS, decretos modificadores e beneficios de ICMS no portal oficial do Ceara, separando escopo nao ICMS. |
| DF | publicado_v1 | 13 | sem alerta automatizado | Distrito Federal publicado como pÃƒÂ¡gina profunda: Lei do ICMS, RICMS, Cadernos do Anexo I, Anexo IV, LC 160/ConvÃƒÂªnio 190, regime especial de apuraÃƒÂ§ÃƒÂ£o, crÃƒÂ©dito outorgado, EMPREGA-DF, PRÃƒâ€œ-DF II, Desenvolve-DF, diferimento agro e EFD ICMS/IPI. |
| ES | publicado_v1 | 7 | sem alerta automatizado | EspÃƒÂ­rito Santo publicado como pÃƒÂ¡gina profunda: Lei nÃ‚Âº 7.000/2001, RICMS/ES, COMPETE/ES, INVEST-ES, FUNDAP, cBenef, isenÃƒÂ§ÃƒÂ£o, reduÃƒÂ§ÃƒÂ£o de base, crÃƒÂ©dito presumido, diferimento, ST, EFD e prova fiscal. |
| GO | aprovado_v1 | 0 | sem alerta automatizado | Manter monitoramento de RCTE, Anexo IX, cBenef e atos modificadores. |
| MA | revisado_com_pendencias | 10 | contém Taxas, fonte local sem URL oficial no cabeçalho | Recapturar RICMS/MA, anexos de beneficios e atos modificadores com URL oficial e separar Taxas da trilha de ICMS. |
| MG | publicado_v1 | 10 | sem alerta automatizado | Minas Gerais publicada como pÃƒÂ¡gina profunda: Lei nÃ‚Âº 6.763/1975, Decreto nÃ‚Âº 48.589/2023, RICMS/MG 2023, Anexos I a VIII, alÃƒÂ­quotas, reduÃƒÂ§ÃƒÂ£o de base, crÃƒÂ©dito presumido, crÃƒÂ©dito acumulado, diferimento, ST, EFD e prova fiscal. |
| MS | publicado_v1 | 35 | sem alerta automatizado | Mato Grosso do Sul publicado como pÃƒÂ¡gina profunda: Lei nÃ‚Âº 1.810/1997, RICMS/MS, Anexos I, II, III, V, VI e XV, LC nÃ‚Âº 93/2001, FUNDERSUL, MS-Empreendedor, diferimento, crÃƒÂ©dito presumido, ST, EFD, parcelamento e prova fiscal. |
| MT | publicado_v1 | 4 | sem alerta automatizado | Mato Grosso publicado como pÃƒÂ¡gina profunda: Lei do ICMS, RICMS, LC 631/2019, anexos de isenÃƒÂ§ÃƒÂ£o, reduÃƒÂ§ÃƒÂ£o de base, crÃƒÂ©ditos fiscais, diferimento, PRODEIC, substituiÃƒÂ§ÃƒÂ£o tributÃƒÂ¡ria, estimativa simplificada, cBenef e prova fiscal. |
| PA | revisado_escopo_bloqueado | 2 | categoria não específica de ICMS, contém IPVA, contém ITCMD/ITCD, contém Taxas | Refazer captura do Para do zero: RICMS/PA, beneficios de ICMS, aliquotas, ST e documentos no portal oficial da SEFA antes de publicar qualquer conclusao. |
| PB | revisado_com_pendencias | 1 | contém IPVA, contém ITCMD/ITCD, contém Taxas | Recapturar RICMS/PB e beneficios de ICMS no portal oficial da Paraiba, separando tributos nao ICMS. |
| PE | revisado_com_pendencias | 8 | contém Taxas, fonte local sem URL oficial no cabeçalho, texto curto para RICMS/benefícios | Recapturar RICMS/PE, beneficios e atos modificadores com URL oficial, vigencia e hash antes de aprovar analise. |
| PI | revisado_com_pendencias | 9 | contém IPVA, contém Taxas, fonte local sem URL oficial no cabeçalho | Recapturar RICMS/PI e beneficios de ICMS no portal oficial do Piaui, separando IPVA/Taxas. |
| PR | publicado_v1 | 8 | sem alerta automatizado | ParanÃƒÂ¡ publicado como pÃƒÂ¡gina profunda: Lei nÃ‚Âº 11.580/1996, RICMS/PR, benefÃƒÂ­cios fiscais de carÃƒÂ¡ter geral, ParanÃƒÂ¡ Competitivo, isenÃƒÂ§ÃƒÂ£o, reduÃƒÂ§ÃƒÂ£o de base, crÃƒÂ©dito presumido, diferimento, ST, documentos, EFD e prova fiscal. |
| RJ | publicado_v1 | 25 | sem alerta automatizado | Rio de Janeiro publicado como pÃƒÂ¡gina profunda: Lei nÃ‚Âº 2.657/1996, RICMS/RJ, Manual de BenefÃƒÂ­cios, FOT/FEEF, Repetro, tratamento setorial industrial, ST, importaÃƒÂ§ÃƒÂ£o, transporte, veÃƒÂ­culos, combustÃƒÂ­veis, EFD, cBenef/cCredPresumido e prova fiscal. |
| RN | publicado_v1 | 19 | sem alerta automatizado | RN publicado com RICMS, anexos de isenÃƒÂ§ÃƒÂ£o, diferimento, crÃƒÂ©dito presumido, reduÃƒÂ§ÃƒÂ£o de base, antecipaÃƒÂ§ÃƒÂ£o, ST, PROEDI, FUNDERN, Tax Free, cBenef e matriz LC 160. |
| RO | revisado_escopo_bloqueado | 4 | contém IPVA, contém Taxas, escopo dominante incompatível: conteúdo parece tratar de IPVA, não de ICMS, escopo material incompatível com ICMS | Refazer captura de RICMS/RO e beneficios no portal oficial de Rondonia, removendo IPVA/Taxas da trilha de ICMS. |
| RR | revisado_com_pendencias | 5 | contém IPVA, contém Taxas, fonte local sem URL oficial no cabeçalho, texto curto para RICMS/benefícios | Recapturar RICMS/RR e beneficios de ICMS no portal oficial de Roraima, saneando anexos de IPVA. |
| RS | publicado_v1 | 5 | sem alerta automatizado | Rio Grande do Sul publicado como pÃƒÂ¡gina profunda: Decreto nÃ‚Âº 37.699/1997, RICMS/RS integral, AMPARA-RS, importaÃƒÂ§ÃƒÂ£o, crÃƒÂ©dito presumido, diferimento, ST, documentos, EFD e prova fiscal. |
| SC | publicado_v1 | 8 | sem alerta automatizado | Santa Catarina publicada como pÃƒÂ¡gina profunda: RICMS/SC, Anexo 2 de benefÃƒÂ­cios fiscais, Anexo 3 de substituiÃƒÂ§ÃƒÂ£o tributÃƒÂ¡ria, Anexo 5 de obrigaÃƒÂ§ÃƒÂµes acessÃƒÂ³rias, Anexo 6 de regimes especiais, NF-e e prova fiscal. |
| SE | revisado_com_pendencias | 4 | contém IPVA, contém Taxas, fonte local sem URL oficial no cabeçalho, texto curto para RICMS/benefícios | Recapturar RICMS/SE, anexos e beneficios de ICMS no portal oficial de Sergipe, separando Taxas/IPVA. |
| SP | publicado_v1 | 5 | sem alerta automatizado | SÃƒÂ£o Paulo publicado como pÃƒÂ¡gina profunda: Lei nÃ‚Âº 6.374/1989, RICMS/2000 integral, Anexos de isenÃƒÂ§ÃƒÂµes, reduÃƒÂ§ÃƒÂµes e crÃƒÂ©ditos outorgados, substituiÃƒÂ§ÃƒÂ£o tributÃƒÂ¡ria, regimes especiais, cBenef, EFD e prova fiscal. |
| TO | revisado_com_pendencias | 2 | contém Taxas, texto curto para RICMS/benefícios | Recapturar beneficios, anexos e atos complementares do Tocantins com URL oficial e validar separadamente do RICMS. |

## CONFAZ 5 anos

| Familia | Total indexado | Fonte oficial |
| --- | ---: | --- |
| Convenios ICMS | 880 | https://www.confaz.fazenda.gov.br/legislacao/convenios |
| Ajustes SINIEF | 161 | https://www.confaz.fazenda.gov.br/legislacao/ajustes |
| Protocolos ICMS | 318 | https://www.confaz.fazenda.gov.br/legislacao/protocolos |
