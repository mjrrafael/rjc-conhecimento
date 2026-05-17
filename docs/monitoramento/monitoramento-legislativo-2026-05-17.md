# Monitoramento legislativo semanal - 2026-05-17

Automacao: RJC Portal - atualizacao legislativa semanal  
Repositorio: `C:\Users\kris2\OneDrive\Documentos\Playbook\rjc-conhecimento`  
Regra usada: fonte oficial, texto em tela, data absoluta, hash e sem conclusao interpretativa sem base legal expressa.

## Fontes oficiais consultadas

- Planalto: indice de decretos de 2026, MPV 1.357/2026, MPV 1.358/2026, Decreto 12.974/2026, Lei 15.394/2026 e indice de leis complementares/leis ordinarias.
- DOU/In.gov.br: buscas por atos RFB, CGIBS, CONFAZ, Ajustes SINIEF, Convenios ICMS, Protocolos ICMS e atos trabalhistas/previdenciarios recentes.
- Receita Federal: paginas oficiais da Reforma Tributaria do Consumo, orientacoes 2026, marcos regulatorios, DIRBI, DCTFWeb e EFD-Reinf.
- SPED: noticias e arquivos de EFD-Contribuicoes, EFD ICMS/IPI, EFD-Reinf, NF-e/NFC-e RTC, Nota Tecnica 2025.002, Nota Tecnica 012/2026 e Guia Pratico EFD ICMS/IPI 3.2.2.
- CONFAZ: Convenios ICMS 2026, Ajustes SINIEF 2026, Protocolos ICMS 2026 e Atos COTEPE/ICMS 2026.
- CGIBS e Ministerio da Fazenda: buscas por resolucoes, portarias conjuntas, split payment, cClassTrib, cCredPres e grupos de trabalho da Reforma.
- Trabalhista/previdenciario: eSocial, Ministerio do Trabalho e Emprego, Caixa/FGTS Digital, Receita Federal/DCTFWeb/Reinf e Planalto/CLT.
- Estados: portais oficiais de Fazenda/Receita/Tributacao/legislacao das 27 UFs: AC, AL, AM, AP, BA, CE, DF, ES, GO, MA, MG, MS, MT, PA, PB, PE, PI, PR, RJ, RN, RO, RR, RS, SC, SE, SP e TO.

## Atos novos ou modificadores confirmados

| Ato/fonte | Data oficial | URL oficial | Hash/registro | Tratamento |
| --- | ---: | --- | --- | --- |
| Medida Provisoria 1.357/2026 - remessas postais internacionais | 2026-05-12 | https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2026/mpv/mpv1357.htm | repo text `0aea6d00a5739990a65e42b56ec714f9db28efe3acfe55d6274699338f236d6c` | Aplicado em modulo aduaneiro, sem ampliar conclusao alem do texto legal. |
| Lei 15.394/2026 - creditos/isencao de PIS/Cofins para residuos e aparas | 2026-04-22 | https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2026/lei/l15394.htm | repo text `5b072d0d8f2ba8ce2c3fa643c7cf05b27e1b8c9434a0f1f31deccb29d6e2cc23` | Aplicado nos capitulos de PIS/Cofins de creditos e beneficios. |
| Receita Federal - Orientacoes da Reforma Tributaria para 2026 | atualizado em 2026-05-06 | https://www.gov.br/receitafederal/pt-br/acesso-a-informacao/acoes-e-programas/programas-e-atividades/reforma-tributaria-do-consumo/orientacoes-2026 | repo text `ea5203f98a4ae161d92868bf193f7706c2d66875ee6cc1f2052af830b1f8fd1a` | URL oficial, data de captura e paginas regeneradas. |
| Receita Federal - Marcos regulatorios da Reforma Tributaria | atualizado em 2026-05-06 | https://www.gov.br/receitafederal/pt-br/acesso-a-informacao/acoes-e-programas/programas-e-atividades/reforma-tributaria-do-consumo/marcos | repo text `e8c1f8c7086f62db871241340b5d32874b5f9ddbce7c34dfa5651d172bd55d35` | URL oficial, data de captura e paginas regeneradas. |
| Ajuste SINIEF 15/26 | publicado no DOU em 2026-04-30 | https://www.confaz.fazenda.gov.br/legislacao/ajustes/2026/AJ015_26 | texto CONFAZ `ebae4c85d05960c9a5bb0b2afc40332eb1e83cd4efe57bcbca06914c2e080c48` | Indexado no CONFAZ 2026; sem tese propria. |
| Ajuste SINIEF 16/26 | publicado no DOU em 2026-05-13 | https://www.confaz.fazenda.gov.br/legislacao/ajustes/2026/AJ016_26 | texto CONFAZ `2a1583670abe1b477373e5fbe6634fa3de4cab1c5afb70bdb16daae64c849706` | Indexado no CONFAZ 2026; pendente curadoria de NFGas. |
| MPV 1.358/2026 - subvenção econômica a combustiveis | 2026-05-13 | https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2026/mpv/mpv1358.htm | captura textual `1bdb21689e9aba8daa14b528426382a3243ddb5f566760a651523438c2a24ad5` | Pendente; exige modulo/curadoria de combustiveis e subvenção, sem publicacao interpretativa. |
| Decreto 12.974/2026 - altera Decreto 12.930/2026 | 2026-05-14 | https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2026/decreto/D12974.htm | captura textual `072e15fc877f3bb98da55c9ebb068f3f4a2c3840d347d04cc07a337da5c38234` | Pendente; conexo a combustiveis/subvencao/transparencia. |

## Alteracoes aplicadas

- Criado modulo federal de `Aduaneiro e remessas internacionais`, com pagina de tema, capitulos legais e ato da MP 1.357/2026 em tela.
- Incluida a Lei 15.394/2026 nos modulos de PIS e Cofins, nos capitulos de nao cumulatividade/creditos e beneficios, com texto oficial versionado em `data/legal_sources/federal/Lei_15394_2026_PIS_COFINS_Residuos.txt`.
- Atualizadas as fontes oficiais da Receita Federal para o novo caminho `reforma-tributaria-do-consumo` e data de atualizacao de 2026-05-06.
- Atualizado `data/legal_sources_registry.json` para 200 fontes registradas.
- Corrigido o gerador de CONFAZ para nao deixar Ajustes SINIEF 2026 zerados quando o indice anual nao expuser links no HTML principal.
- Atualizado `data/confaz_ultimos_5_anos.json` e `confaz/ultimos-5-anos.html`: Ajustes SINIEF 2026 passaram de 0 para 16 atos.
- Regenerados busca, manifesto LLM, sitemap XML/texto e paginas federais afetadas.

## Comparacao com bases internas

- `data/legal_sources_registry.json`: agora inclui MP 1.357/2026, Lei 15.394/2026 e URLs corrigidas da Receita Federal.
- `data/benefits_crosswalk.json` e `data/ncm_benefits_index.json`: sem regeneracao de conteudo de beneficio/NCM nesta rodada; as alteracoes de PIS/Cofins entraram nos modulos legais e paginas tematicas.
- `data/confaz_ultimos_5_anos.json`: atualizado para refletir Ajustes SINIEF 2026.
- Paginas publicadas: atualizadas Federal, Aduaneiro, PIS, Cofins, Reforma, CONFAZ, busca, sitemap e `llms.txt`.

## Auditorias

- `portal_monitor.py --live`: concluido e salvo em `docs/monitoramento/portal-monitor-2026-05-17.md`; sem achado critico ou alto.
- `python -m py_compile scripts/*.py`: OK.
- `python scripts/audit_master_coverage.py`: OK, sem falhas estruturais.
- `python scripts/audit_state_source_quality.py`: OK, relatorio estadual regenerado sem mudanca material.
- `audit_portal.py`: chamada direta instavel no wrapper; subchecks internos rodados separadamente com 633 paginas HTML auditadas, 0 erros em links, busca, fontes legais, regioes e conteudo critico.
- `build_portal.py`: a execucao completa ficou instavel em OneDrive/wrapper; a etapa final foi executada isoladamente e concluiu `assets/portal-search-full.json`, `assets/portal-search.js`, `sitemap.xml`, `sitemap.txt`, `llms.txt` e `assets/llm-manifest.json`.

## Pendencias reais

- MPV 1.358/2026 e Decreto 12.974/2026 precisam de curadoria antes de virarem pagina: o tema mistura subvenção econômica, tributos federais deduzidos do preço, combustiveis, importadores/produtores e transparência de distribuição.
- Ajuste SINIEF 16/26 precisa de leitura operacional propria para NFGas, NF-e substitutiva e prazo de obrigatoriedade; nesta rodada foi apenas indexado no CONFAZ.
- SPED apresentou sinais relevantes de NT 012/2026, EFD-Contribuicoes/LC 224 e Guia Pratico EFD ICMS/IPI 3.2.2, mas o host `sped.rfb.gov.br` ficou inacessivel por `Invoke-WebRequest/curl` nesta maquina. Mantido como pendencia de captura direta do PDF/texto antes de publicar conclusao.
- Estados: nenhuma mudanca estadual foi publicada automaticamente nesta rodada. Alguns portais oficiais retornaram sinais de atos recentes por busca, mas nao houve captura completa com texto legal/hash suficiente para atualizar beneficio, cBenef, NCM, aliquota ou obrigacao estadual sem revisao humana.
- Indexacao real no Google segue pendente de Search Console/URL Inspection; auditoria so comprova indexabilidade tecnica.
