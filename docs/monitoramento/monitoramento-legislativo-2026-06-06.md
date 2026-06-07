# Monitoramento legislativo semanal - 06/06/2026

## Escopo executado

- Protocolo: RJC Portal Tributario Aberto - atualizacao legislativa semanal.
- Janela operacional: atos localizados e conferidos em fontes oficiais ate 06/06/2026.
- Fontes varridas: Planalto, DOU/Imprensa Nacional, Receita Federal/SIJUT, noticias da Receita Federal, SPED/gov.br, CONFAZ, Ministerio da Fazenda, Portal Nacional da Tributacao sobre Consumo, CGIBS e portais oficiais das Secretarias de Fazenda/Receita das 27 UFs.
- Scan tecnico salvo em `docs/monitoramento/fontes-oficiais-scan-2026-06-06.json`: 47 endpoints, 33 OK e 14 bloqueados, indisponiveis ou sem indice no caminho testado.

## CONFAZ

- Convenios ICMS: local 874, oficial 874, novos 0.
- Ajustes SINIEF: local 161, oficial 161, novos 0.
- Protocolos ICMS: local 318, oficial 318, novos 0.
- Resultado: nenhuma alteracao objetiva de CONFAZ foi aplicada nesta rodada.

## Atos novos ou modificadores incorporados

### Ato Conjunto RFB/CGIBS 2/2026 - Plataforma Publica do Split Payment

- Fonte oficial capturada: https://normas.receita.fazenda.gov.br/sijut2consulta/link.action?antigo=1&idAto=151582
- Referencia DOU localizada: https://in.gov.br/en/web/dou/-/ato-conjunto-rfb/cgibs-n-2-de-27-de-maio-de-2026-710138574
- Publicacao: DOU de 03/06/2026, secao 1, pagina 75.
- Hash HTML oficial capturado: `5e0c5983ad49ed4915779c2bbcd253219637a4f5fc3db8cff10b934c4b4ef5f0`.
- Efeito publicado no portal: fonte em tela e vinculo nos capitulos de Reforma Tributaria sobre base, creditos, recolhimento e split payment.
- Limite de interpretacao: ato tratado como marco tecnico de publicacao do Manual de Integracao e Swagger; nao foi publicado como alteracao de carga, credito ou regra material.

### Decreto 12.991/2026 - PIS/Cofins sobre querosene de aviacao e biodiesel

- Fonte oficial capturada: https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2026/decreto/d12991.htm
- Publicacao: 29/05/2026, edicao extra do DOU.
- Hash HTML oficial capturado: `2f256fb2b2cab12dda1688e9d08521cb05b8628848ea2e6097bd25cc862e3354`.
- Efeito publicado no portal: fonte em tela e referencia nos capitulos de beneficios/monofasico de PIS e Cofins.
- Limite de interpretacao: incorporado apenas como prorrogacao setorial de coeficientes de reducao para QAV e biodiesel, com vigencia a conferir no proprio decreto antes de parametrizacao.

### Instrucao Normativa RFB 2.326/2026 - valor aduaneiro

- Fonte oficial capturada: https://normas.receita.fazenda.gov.br/sijut2consulta/link.action?antigo=1&idAto=151412
- Publicacao: DOU de 26/05/2026, secao 1, pagina 41.
- Hash HTML oficial capturado: `bf1b1c535e054e722114252d156e1b3a96d0d21e77eec142375a89502fd7b5aa`.
- Efeito publicado no portal: nova fonte em tela e novo capitulo em Aduaneiro sobre valor aduaneiro e instrumentos CTVA/OMA.
- Limite de interpretacao: publicado como atualizacao de referencias tecnicas da IN RFB 2.090/2022; sem conclusao aplicada por produto ou operacao concreta.

### Portaria RFB 688/2026 - transparencia ativa, beneficios e Dirbi

- Fonte oficial capturada: https://normas.receita.fazenda.gov.br/sijut2consulta/link.action?antigo=1&idAto=151498
- Publicacao: DOU de 29/05/2026, secao 1, pagina 61.
- Hash HTML oficial capturado: `fedcaefcbf436031d80a2ad58d8965aa5d920727dfca25eee300b5da726fe768`.
- Efeito publicado no portal: nova fonte em tela e novo capitulo de IRPJ sobre transparencia de beneficios federais e Dirbi.
- Limite de interpretacao: ato nao cria beneficio novo; ajusta transparencia ativa e prevalencia das informacoes coletadas via Dirbi para essa finalidade, ressalvados tributos de comercio exterior.

## Sinais revisados sem publicacao aplicada

- Receita Federal - creditos de PIS/Cofins na transicao para CBS: orientacao administrativa baseada na LC 214/2025, art. 378; sem ato normativo novo a incorporar como mudanca objetiva.
- Goias - reducao de ICMS do feijao para outros Estados: noticia oficial de proposta/projeto; sem lei ou decreto vigente localizado para publicacao.
- Goias - integracao EFD com meios de pagamento: marco operacional relacionado a IN 1.608/2025; sem ato novo nesta janela.
- Bahia - Liquida Bahia 2026: FAQ oficial da SEFAZ/BA menciona Decreto 24.538/2026, mas o texto integral oficial do decreto/DOE ainda precisa ser capturado antes de publicacao em matriz legal.
- SPED: portal gov.br/SPED respondeu, mas o legado `sped.rfb.gov.br` falhou por timeout; nenhuma alteracao de obrigacao acessoria foi publicada apenas por migracao/indisponibilidade de portal.
- CGIBS: caminhos `/resolucoes` e `/regulamentos` bloquearam/conectaram com reset no scan; acompanhar novamente na proxima rodada.

## Alteracoes aplicadas no portal

- `scripts/legal_modules.py`: data de atualizacao para 06/06/2026; quatro novas fontes oficiais; capitulos e referencias em PIS, Cofins, Aduaneiro, IRPJ e Reforma Tributaria.
- `data/legal_sources_registry.json`: registro exportado com 210 fontes.
- Novos textos legais salvos em `data/legal_sources/federal/` e `data/legal_sources/reforma_tributaria/`.
- Novas paginas em tela:
  - `federal/legislacao/atos/ato-conjunto-rfb-cgibs-2-2026-split-payment.html`
  - `federal/legislacao/atos/decreto-12991-2026-pis-cofins-combustiveis.html`
  - `federal/legislacao/atos/in-rfb-2326-2026-valor-aduaneiro.html`
  - `federal/legislacao/atos/portaria-rfb-688-2026-transparencia-dirbi.html`
  - `federal/legislacao/aduaneiro/valor-aduaneiro-in-rfb-2326.html`
  - `federal/legislacao/irpj/transparencia-beneficios-dirbi.html`
- Artefatos globais regenerados: `assets/portal-search.js`, `assets/portal-search-full.json`, `assets/llm-manifest.json`, `sitemap.xml`, `sitemap.txt` e `llms.txt`.
- Matrizes `data/benefits_crosswalk.json` e `data/ncm_benefits_index.json` foram regravadas pelo gerador com `generated_on` 06/06/2026 e nova captura/hash do Anexo IX/GO; contagens permaneceram em 12.246 beneficios e 7.976 linhas NCM.

## Auditorias

- `portal_monitor.py --live` inicial: `docs/monitoramento/portal-monitor-2026-06-06.md`; 645 paginas HTML, 0 critico, 0 alto.
- `python scripts/export_legal_registry.py`: registro exportado com 210 fontes.
- `python -m compileall -q scripts`: sem erro.
- `python scripts/audit_master_coverage.py`: sem falhas estruturais; 15 requisitos federais, 27 Estados, 12.246 beneficios, 7.976 linhas NCM e 3 familias CONFAZ auditadas.
- `python scripts/audit_state_source_quality.py`: relatorios estadual e JSON regravados.
- `python -X dev scripts/audit_portal.py`: 651 paginas HTML auditadas, sem falhas.
- `portal_monitor.py --live` pos-atualizacao: `docs/monitoramento/portal-monitor-2026-06-06-pos-atualizacao.md`; 651 paginas HTML, 0 critico, 0 alto, 2 medios.

## Validacao GitHub Pages pos-push

- Commit publicado: `afe53e9`.
- URLs novas validadas com HTTP 200 e conteudo esperado:
  - https://mjrrafael.github.io/rjc-conhecimento/federal/legislacao/atos/ato-conjunto-rfb-cgibs-2-2026-split-payment.html
  - https://mjrrafael.github.io/rjc-conhecimento/federal/legislacao/atos/decreto-12991-2026-pis-cofins-combustiveis.html
  - https://mjrrafael.github.io/rjc-conhecimento/federal/legislacao/aduaneiro/valor-aduaneiro-in-rfb-2326.html
  - https://mjrrafael.github.io/rjc-conhecimento/sitemap.xml
  - https://mjrrafael.github.io/rjc-conhecimento/assets/llm-manifest.json

## Pendencias reais

- `data/benefits_crosswalk.json` segue acima de 50 MB; dividir matriz/pagina continua sendo melhoria tecnica pendente.
- Bahia Liquida Bahia 2026: localizar e capturar texto integral oficial do Decreto 24.538/2026 antes de qualquer conclusao aplicada.
- CGIBS e alguns portais estaduais com bloqueio/reset no scan devem ser revisitados em proxima rodada.
- Search Console/indexacao real continuam fora da prova tecnica local; confirmar por Search Console ou URL Inspection.
