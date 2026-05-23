# Monitoramento legislativo semanal - 23/05/2026

Automacao: RJC Portal - atualizacao legislativa semanal  
Execucao: 23/05/2026, America/Sao_Paulo  
Repositorio: `C:\Users\kris2\OneDrive\Documentos\Playbook\rjc-conhecimento`

## Fontes oficiais consultadas

- Planalto: indices oficiais de decretos, leis ordinarias, medidas provisorias e leis complementares de 2026.
  - https://www.planalto.gov.br/ccivil_03/_Ato2023-2026/2026/Decreto/_decretos2026.htm
  - https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2026/lei/_leis2026.htm
  - https://www.planalto.gov.br/ccivil_03/mpv/Quadro/_Quadro2023-2026.htm
  - https://www.planalto.gov.br/ccivil_03/leis/lcp/Quadro_Lcp.htm
- DOU/In.gov.br: buscas por publicacoes de 19/05/2026 a 22/05/2026 ligadas a Receita Federal, CGIBS, IBS, CBS, tributos, instrucoes normativas e Fazenda.
- Receita Federal e Ministerio da Fazenda: noticias, Reforma Tributaria do Consumo, Painel Nacional de Tributacao sobre o Consumo, Compras Internacionais, orientacoes 2026 e marcos regulatorios.
- SPED e Portal Nacional DF-e/SVRS: busca por EFD ICMS/IPI, EFD-Contribuicoes, NF-e, NFC-e, CT-e, MDF-e, IT 2025.002, cClassTrib e cCredPres.
- CGIBS: noticias e regulamentos oficiais sobre adequacao de sistemas de NF-e ao IBS/CBS e atos da Reforma.
- CONFAZ: indice vivo de Convenios ICMS, Ajustes SINIEF e Protocolos ICMS nos ultimos cinco anos.
- Portais oficiais estaduais: AC, AL, AP, AM, BA, CE, DF, ES, GO, MA, MT, MS, MG, PA, PB, PR, PE, PI, RJ, RN, RS, RO, RR, SC, SP, SE e TO, com fallback por busca oficial quando o portal retornou erro de SSL, DNS ou conexao.

## Resultado CONFAZ

Comparacao viva contra `data/confaz_ultimos_5_anos.json`:

- Convenios ICMS: local 874, vivo 874, novos 0.
- Ajustes SINIEF: local 161, vivo 161, novos 0.
- Protocolos ICMS: local 318, vivo 318, novos 0.

Sem alteracao objetiva no indice CONFAZ nesta rodada.

## Atos novos ou modificadores aplicados

| Fonte oficial | Data | Hash SHA256 do texto versionado | Tratamento |
| --- | --- | --- | --- |
| [DF Lei Complementar 1.068/2026](https://www.sinj.df.gov.br/sinj/Norma/1cd1e9da5d464be4b22ffc0ca173e58b/LC_1068_2026.html) | 06/05/2026, promulgada em 07/05/2026 | `dbc7306540fdbc0a2c65c3338c57684edd52ba64d345f9234764f88199e57765` | Aplicado. Incluida como fonte oficial no capitulo de fiscalizacao/riscos do Distrito Federal por tratar de devedor contumaz, regime especial de fiscalizacao, impedimento de beneficios de ICMS, ST e medidas de controle. |
| [SP Portaria SRE 24/2026](https://legislacao.fazenda.sp.gov.br/Paginas/Portaria-SRE-24-de-2026.aspx) | 15/05/2026, DOE 18/05/2026 | `6c23a92d919b7a346f3f01aaf295fa900d73cbbfe089c9ea948dd7911f7428e7` | Aplicado. Incluida no capitulo de substituicao tributaria de Sao Paulo por alterar a Portaria SRE 59/2023 sobre base de calculo/IVA-ST para eletronicos, eletroeletronicos e eletrodomesticos, com marco de 01/08/2026. |

## Sinais oficiais sem publicacao aplicada

- Planalto: atos federais publicados entre 19/05/2026 e 22/05/2026 foram majoritariamente organizacionais, credito extraordinario, transito, violencia contra mulher, pesca artesanal e estruturas de agencias. O Decreto 12.979/2026 altera estrutura da ANP, mas nao trouxe regra material tributaria para o portal.
- Receita Federal: noticias sobre IRPF 2026, Painel Nacional de Tributacao sobre o Consumo e Compras Internacionais foram tratadas como sinais operacionais. A MPV 1.357/2026 de remessas postais ja esta registrada no portal; nao houve novo ato material adicional a aplicar.
- CGIBS: noticia de 22/05/2026 sobre prazo de adequacao dos sistemas de emissao de notas fiscais ao regulamento do IBS nao foi tratada como novo ato normativo, porque o Ato Conjunto RFB/CGIBS 1/2025 ja esta registrado no portal.
- Acre: o portal oficial da SEFAZ/AC lista o Decreto 11.888/2026, de 11/05/2026, sobre prazos do Refis 2021. Nao aplicado porque AC permanece `revisado_com_pendencias` e a mudanca e de programa de regularizacao, nao de matriz de beneficio/NCM ja publicada.
- Bahia: noticia oficial de 20/05/2026 informa parcelamento de ICMS para lojistas da Liquida Bahia 2026. Nao aplicada porque a rodada localizou a noticia, mas nao capturou o decreto/ato normativo completo com numero e texto legal em tela.
- Distrito Federal: Portaria 353/2026 sobre prazos para inscricao em divida ativa foi localizada como publicacao administrativa. Nao aplicada por nao alterar diretamente pagina material de ICMS, beneficio, NCM, cBenef, CST ou cClassTrib.
- Goias: o portal oficial continuou apontando INs de maio sobre valores correntes/base de calculo de mercadorias. Mantida a pendencia da rodada anterior: falta modelo proprio para pautas/valores por produto antes de publicar em tabela operacional.

## Comparacao com dados do portal

- `data/legal_sources_registry.json`: atualizado de 203 para 205 fontes; `updated_on` passou para 23/05/2026.
- `data/benefits_crosswalk.json`: atualizado de 12.221 para 12.223 entradas. As novas entradas refletem tratamento de fiscalizacao/regime especial de ICMS; nao houve NCM novo.
- `data/ncm_benefits_index.json`: permaneceu com 7.942 linhas e 1.374 NCM unicos; SP Portaria SRE 24/2026 nao trouxe tabela NCM nova em texto capturado nesta rodada.
- `data/confaz_ultimos_5_anos.json`: regenerado sem novos atos.
- `assets/llm-manifest.json`, `llms.txt`, `sitemap.xml`, `sitemap.txt` e busca integral regenerados para 644 paginas HTML.

## Alteracoes aplicadas

- Criado `data/fontes-estaduais-curadas/centro-oeste/DF/DF_LC_1068_2026_DEVEDOR_CONTUMAZ_2026-05-23.txt`.
- Criado `data/fontes-estaduais-curadas/sudeste/SP/SP_PORTARIA_SRE_24_2026_IVA_ST_ELETRONICOS_2026-05-23.txt`.
- Atualizados os manifests oficiais de DF e SP.
- Atualizado `scripts/state_legal_pages.py` para vincular a LC DF 1.068/2026 ao capitulo de fiscalizacao/riscos e a Portaria SRE/SP 24/2026 ao capitulo de ST.
- Atualizado `scripts/legal_modules.py` para marcar `UPDATED_ON = "23/05/2026"` e tornar a leitura de fontes publicas mais resiliente a timeout de portais oficiais.
- Regeneradas as paginas publicadas:
  - `estados/df/legislacao/fiscalizacao-riscos.html`
  - `estados/df/legislacao/fontes/df-lc-1068-2026-devedor-contumaz.html`
  - `estados/sp/legislacao/st-antecipacao-segmentos.html`
  - `estados/sp/legislacao/fontes/sp-portaria-sre-24-2026-iva-st-eletronicos.html`

## Auditorias executadas

- `portal_monitor.py --live` pre-atualizacao: sem critico/alto; medio apenas `data/benefits_crosswalk.json` acima de 50 MB.
- `python scripts/export_legal_registry.py`: 205 fontes exportadas.
- `python scripts/build_master_indexes.py`: executado com sucesso; matriz de beneficios em 12.223 entradas.
- `python scripts/build_portal.py`: executado com sucesso; 644 paginas HTML geradas.
- `python -m py_compile scripts/*.py`: sem erro.
- `python scripts/audit_master_coverage.py`: sem falhas estruturais.
- `python scripts/audit_state_source_quality.py`: relatorio estadual regravado.
- `python -X dev scripts/audit_portal.py`: 644 paginas auditadas, sem falhas.
- `portal_monitor.py --live` pos-atualizacao: sem critico/alto; medio por worktree suja antes do commit e `data/benefits_crosswalk.json` acima de 50 MB.

Relatorios salvos:

- `docs/monitoramento/portal-monitor-2026-05-23.md`
- `docs/monitoramento/portal-monitor-2026-05-23-pos-atualizacao.md`
- `docs/monitoramento/portal-monitor-2026-05-23-final.md`

## Pendencias reais

- Tratar performance do `data/benefits_crosswalk.json`, agora com 56.101.124 bytes.
- Criar modelo especifico para pautas/valores estaduais antes de integrar INs estaduais de base de calculo por produto.
- Capturar ato normativo completo da Bahia sobre parcelamento da Liquida Bahia 2026 antes de publicar qualquer regra.
- Recapturar/curar AC antes de publicar efeito operacional do Decreto 11.888/2026.
- Validar indexacao real no Search Console; a auditoria confirma indexabilidade e acesso tecnico, nao indexacao efetiva.
