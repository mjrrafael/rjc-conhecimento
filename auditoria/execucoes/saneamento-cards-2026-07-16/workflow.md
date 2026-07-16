# Saneamento direto dos cards e da quarentena

## Objetivo

Aplicar a correção diretamente aos dois datasets públicos: preservar os originais fora do repositório e publicar zero entradas até que cada card tenha prova material. O criterio de pronto é que ambos os arquivos tenham `entries: []`; a evidencia é o manifesto externo com hashes, o auditor determinístico e a revisão adversarial.

## Fases

- G0: escopo definido antes da escrita.
- G1: ler integralmente os dois JSON e conferir as cópias por SHA-256.
- G2: executar saneamento atômico e registrar o ledger.
- G3: reabrir os arquivos produzidos e confrontar a cópia externa.
- G4: executar o auditor e o verificador de conformidade.
- G5: decidir se o conteúdo pode ser publicado. A resposta esperada é `BLOQUEADO` para conteúdo tributário.

## Limite

O saneamento corrige a superfície atual dos dois datasets; não apaga histórico, forks ou os demais acervos legados. Nenhum card é considerado validado por esta ação.
