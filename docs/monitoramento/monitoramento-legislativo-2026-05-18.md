# Monitoramento legislativo semanal - 18/05/2026

Automação: RJC Portal - atualização legislativa semanal  
Execução: 18/05/2026, America/Sao_Paulo  
Repositório: `C:\Users\kris2\OneDrive\Documentos\Playbook\rjc-conhecimento`

## Fontes oficiais consultadas

- Planalto: quadros de leis, decretos e medidas provisórias de 2026; textos da MPV 1.358/2026 e do Decreto 12.974/2026.
- DOU/IN.gov: conferência de publicação indicada nos atos do Planalto e busca por atos tributários recentes.
- Receita Federal, SPED, Portal Nacional DF-e, Ministério da Fazenda e CGIBS: busca por mudanças em Reforma Tributária, PIS/Cofins, IPI, IRPJ, CSLL, obrigações acessórias, CST, cClassTrib e cCredPres.
- CONFAZ: comparação viva do índice local com atos de 2026.
- Secretarias de Fazenda/Receita das 27 UFs: varredura dos portais oficiais cadastrados em `STATE_OFFICIAL_PORTALS`, com foco em atos recentes, ICMS, benefícios, cBenef, NCM, ST, importação e obrigações acessórias.

## Resultado CONFAZ

Comparação com índice vivo:

- Convênios ICMS: local 56, vivo 56, novos 0.
- Ajustes SINIEF: local 16, vivo 16, novos 0.
- Protocolos ICMS: local 37, vivo 37, novos 0.

Sem atualização objetiva no índice CONFAZ nesta rodada.

## Atos novos ou modificadores com impacto objetivo

| Fonte | Data | Hash SHA256 | Tratamento |
| --- | --- | --- | --- |
| [GO Decreto 10.904/2026](https://goias.gov.br/economia/wp-content/uploads/sites/45/2026/05/D_10904.doc) | 07/05/2026 | `4a65770b54f2abc320f3d8df79c11c0c0c33c3f05c8d05542ed7dcb338c2a47e` | Aplicado ao portal. Altera Anexo IX do RCTE/GO para entradas de mercadorias e bens destinados a linhas de transmissão de energia elétrica. |
| [GO Decreto 10.905/2026](https://goias.gov.br/economia/wp-content/uploads/sites/45/2026/05/D_10905.doc) | 07/05/2026 | `95b2e19ab19b423ee57413b989a17ecec659d2f489d259e38fcd3e672a0e626f` | Aplicado ao portal. Altera Anexo IX do RCTE/GO para crédito especial de investimento ligado a biogás/biometano e TARE. |
| [GO Decreto 10.907/2026](https://goias.gov.br/economia/wp-content/uploads/sites/45/2026/05/D_10907.doc) | 07/05/2026 | `7365f01515d8b7a1cedc18e627081e17686b975ad4fdaceb603886178aae4a40` | Não aplicado. Altera PROTEGE Goiás; exige curadoria específica de fundo/contrapartida antes de página operacional. |
| [MPV 1.358/2026](https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2026/mpv/mpv1358.htm) | 13/05/2026 | `f5491c3148de3daf4c17b63952724f54f1b8b8024ec7bc5101a79d3eed0b5688` | Pendente. Subvenção econômica em combustíveis; precisa módulo setorial próprio antes de conclusão aplicada. |
| [Decreto 12.974/2026](https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2026/decreto/d12974.htm) | 14/05/2026 | `3a392671d2cf25f79757ada435d799c9adc4747866ae4e52b9f78d7a3124c1af` | Pendente. Regulamenta ponto ligado ao regime emergencial de abastecimento interno de combustíveis. |

## Sinais estaduais registrados sem publicação profunda

- Goiás publicou ainda as INs 044 a 051/2026, todas capturadas por hash na triagem. Elas tratam de pautas/valores de mercadorias específicas e não foram aplicadas ao portal porque o modelo atual não possui tabela operacional de pauta estadual por produto.
- Paraíba publicou os Decretos 48.145 a 48.149/2026 em ICMS. Foram registrados como pendência porque PB permanece `revisado_com_pendencias` em `data/state_curadoria.json`; publicar interpretação aplicada exigiria recaptura do RICMS/PB e benefícios em pacote estadual separado.
- Ceará publicou comunicado oficial sobre Siscoex2 e DUIMP, com início operacional em 18/05/2026. Registro como sinal operacional de importação; sem atualização de página legislativa por não ser ato normativo material completo.
- Mato Grosso apresentou notícia sobre Fethab, mas sem texto legal capturado nesta execução. Pendente até localizar ato normativo oficial.

Hashes de triagem:

- GO IN 044/2026: `dfce474c516c46de0d9e81036f1a12f2a10fa91afb18c62ec538db9917f6a8f9`
- GO IN 045/2026: `0c007135d3dc376dfa1201a5ee6272bcf5fd0ac7926e143be4bb4db93661f178`
- GO IN 046/2026: `629c6300b92af9c4f15dc372a36ba176d3b76f091c7f0498e6c7708c3e901c62`
- GO IN 047/2026: `6201e7a3fd604b421ad3167e396d55614ffe2c50d88ed93d469acf8fa84daab6`
- GO IN 048/2026: `196bd83e3cf7f04ef3e00904bae758ee9e819f2d2a6a72411c828f67db8cae9e`
- GO IN 049/2026: `0467f0a76a0b3af018151bda151e3ed69fccb953cfa6763793f6b3504a094a2b`
- GO IN 050/2026: `854924210291b7ce3360ec2e694b05de9d09aa217b9480017855271f1332631f`
- GO IN 051/2026: `96e46b57e91c195cbb3127e3daa284bbbc51ae3d54befedba2e56fabcf9449f2`
- PB Decreto 48.145/2026: `658deacf88912d1218279bdc8dddd6a6df15b01403924cfdd2726ff40980b471`
- PB Decreto 48.146/2026: `919a0a600ffc9eab478683daf0ba4e636e3347bb3f4b61d2d29ecfcdf3b55c99`
- PB Decreto 48.147/2026: `6009c2af28ec867ed83f304d559c9f86e3385183bc86cd651a02193a32d539a0`
- PB Decreto 48.148/2026: `efb1eebd6739c88f5a52bd3b7e4240db2c16a3090167800c8aacff57a0594a0d`
- PB Decreto 48.149/2026: `f85097e15fc45291a2af8a80fd1caf4f87781a136612afc26715cfca63f1f469`
- CE Siscoex2: `8872a8c38b4fe1f83bba6c671562f69a2745c89ee3f08872bb54ef34d7a0031f`

## Alterações aplicadas

- Criadas fontes versionadas em `data/legal_sources/goias/` para os Decretos GO 10.904/2026 e 10.905/2026, com URL oficial, data de captura e SHA256 do `.doc` oficial.
- Atualizado `scripts/legal_modules.py`:
  - `UPDATED_ON = "18/05/2026"`;
  - novas fontes `decreto-go-10904-2026-anexo-ix-transmissao-energia` e `decreto-go-10905-2026-anexo-ix-biogas-biometano`;
  - novos capítulos no módulo de Goiás:
    - `transmissao-energia-anexo-ix-2026`;
    - `biogas-biometano-investimento-2026`.
- Exportado `data/legal_sources_registry.json`, agora com 203 fontes.
- Regenerado o portal completo, incluindo busca, sitemap, llms.txt e manifesto.

Não houve atualização em `data/benefits_crosswalk.json` nem em `data/ncm_benefits_index.json`, porque os dois decretos aplicados não trouxeram tabela direta de NCM, cBenef ou linha operacional granular suficiente para inclusão automática segura.

## Auditorias executadas

- `portal_monitor.py --live` antes da alteração: sem achados críticos ou altos; médio já existente para `data/benefits_crosswalk.json` acima de 50 MB.
- `python scripts/export_legal_registry.py`: registro exportado com 203 fontes.
- `python scripts/build_portal.py`: portal gerado com sucesso.
- `python -m py_compile scripts/*.py`: sem erro.
- `python scripts/audit_master_coverage.py`: sem falhas estruturais.
- `python scripts/audit_state_source_quality.py`: auditoria estadual regravada.
- `python -X dev scripts/audit_portal.py`: 642 páginas auditadas, sem falhas.
- `portal_monitor.py --live` pós-atualização: sem crítico/alto; médios apenas worktree suja antes do commit e `data/benefits_crosswalk.json` acima de 50 MB.

Relatórios salvos:

- `docs/monitoramento/portal-monitor-2026-05-18.md`
- `docs/monitoramento/portal-monitor-2026-05-18-pos-atualizacao.md`

## Pendências reais

- Criar módulo federal específico para combustíveis/subvenções antes de publicar MPV 1.358/2026 e Decreto 12.974/2026 com leitura aplicada.
- Curar pacote estadual da Paraíba antes de publicar os Decretos PB 48.145 a 48.149/2026 no portal profundo.
- Definir modelo de dados para pautas/valores estaduais antes de integrar as INs GO 044 a 051/2026.
- Confirmar atos SPED em fonte direta quando o portal SPED estiver estável para captura completa.
- Tratar performance do `data/benefits_crosswalk.json` acima de 50 MB.
- Validar indexação real no Search Console; a auditoria técnica confirma indexabilidade, não indexação efetiva.
