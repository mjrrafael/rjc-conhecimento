# Templates de artefatos obrigatórios anti-pulo

Copie estes 7 arquivos para a PASTA DE TRABALHO antes de executar a skill.
`inventario_documentos.csv` é obrigatório neste contrato, ainda que liste apenas fontes e artefatos produzidos.
Preencha durante a execução: linhas/trechos "Exemplo" e placeholders `<...>` dos
templates NÃO contam para o verificador (v4 falha template não preenchido).
Use IDs únicos no ledger. Os checks `RAC-*` exigem linha semanticamente correspondente no ledger.
Em risco alto, hash precisa estar ligado a arquivo existente e corresponder ao conteúdo; hash isolado não prova execução.
Antes de declarar CONCLUÍDO, rode:

    python scripts/verificar_conformidade.py --contrato contrato_execucao.yaml --pasta <PASTA_DE_TRABALHO>

Arquivos: workflow.md, ledger_verificacao.csv (com coluna `id`), fontes_lidas.csv,
achados_e_pendencias.md, revisao_adversarial.md, relatorio_final.md
e inventario_documentos.csv.
