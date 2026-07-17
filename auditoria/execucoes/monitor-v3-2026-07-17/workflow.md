# Monitor Portal RJC Tributário v3.0 — 2026-07-17

## Objetivo

Revalidar o estado publicado e o baseline remoto, sem tocar no worktree do usuário, e decidir se há evidência suficiente para publicação ou se a contenção segura deve permanecer.

## Escopo e baseline

- Janela desta vigília: `2026-07-17T07:32:19-03:00` em `America/Sao_Paulo`.
- Baseline remoto: `origin/main` = `4caecc1c61e98e76a6c4a4eedaf10ada9e1d4e5f`.
- Worktree exclusivo: `C:\Users\rafae\Documents\Codex\2026-06-14\pesquisa-na-mem-ria-profunda-l\worktrees\rjc-monitor-2026-07-17-0732`.
- Produção: https://mjrrafael.github.io/rjc-conhecimento/.

## Critérios de pronto falsificáveis

| ID | Critério | Método | Evidência exigida |
| --- | --- | --- | --- |
| M17-01 | A produção não expõe orientação tributária operacional sem prova | HTTP anônimo da raiz e superfícies públicas | status, hash e inspeção do corpo |
| M17-02 | O SHA de `main`, PRs abertas e a produção são reconciliados | `git fetch`, GitHub CLI e HTTP | SHAs, estados de PR e hashes |
| M17-03 | Há condições materiais para restaurar conteúdo público | revisão de matriz, recibos, proveniência, ondas e gates | todos os requisitos v3 verificáveis |
| M17-04 | A revisão independente não revela defeito novo de contenção | três papéis somente-leitura, confronto posterior | relatórios, cadeias e achados |
| M17-05 | O resultado e a retomada são rastreáveis | rito, memória e commit isolado | artefatos do contrato e SHA |

## Regra de decisão

Somente `CONCLUÍDO E PUBLICADO` ou `SEM ALTERAÇÃO — PRODUÇÃO INTEGRALMENTE VERIFICADA` podem ser sucessos. Se a evidência v3 ou a independência certificável faltar, o estado obrigatório é `BLOQUEADO TEMPORÁRIO`; nenhuma superfície tributária legada pode ser reativada.

## Limites conhecidos no início

O histórico persistido relata ausência de recibos HTTP/subagentes nativos, de duas raízes de confiança administrativamente independentes e de isolamento verificável entre ondas. Estes fatos precisam ser refutados por evidência nova, não por repetição do relatório anterior.
