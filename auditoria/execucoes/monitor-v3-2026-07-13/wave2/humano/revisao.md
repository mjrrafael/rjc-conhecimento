# Revisão cega humana — Onda 2

## Escopo e porta de saída

- Candidato único: `074bff85c7c560386ca0ed7f0802d4e896534571`.
- Worktree único: `C:\Users\rafae\Documents\Codex\2026-06-14\pesquisa-na-mem-ria-profunda-l\worktrees\rjc-monitor-2026-07-13-wave2-humano`.
- Trabalho somente leitura; `git status --porcelain=v2` permaneceu vazio na coleta.
- Regra fail-closed: ausência de recibos nativos, raízes de confiança e prova de isolamento verificáveis implica `BLOQUEADO` e `NÃO CONFORME`.

## Evidência material obtida

O `HEAD` coincide com o candidato; objeto é commit, árvore `cd1858ccdabb600d5d91545adbff88c4932986a8`, pai `f814f80efbab84bf43b671bf544c4678d4dda82a`. O inventário conciliou 1.180 entradas (1.039 arquivos e 141 diretórios), sem arquivo rastreado faltante. Vinte arquivos sob `auditoria/execucoes/**` foram apenas inventariados e marcados `PROIBIDO_NAO_LIDO`, sem leitura ou hash.

O build reproduziu o workflow com Ruby 3.1.7, `github-pages` 232 e Jekyll 3.10.0. `jekyll build --source . --destination <temp>` retornou 0 e emitiu exatamente quatro arquivos: `index.html` (948 B), `404.html` (611 B), `robots.txt` (28 B) e `llms.txt` (223 B). A fonte contém bloqueio integral em `robots.txt`; `index.html` e `404.html` contêm `noindex,nofollow,noarchive` e aviso de revisão técnica.

## Achado crítico sobre os gates novos

O commit adiciona treze wrappers materiais em `NEW_GATES`, mas `.github/workflows/portal-audit.yml` chama apenas onze gates detalhados. Ficam fora do CI `audit_publication.py` e `audit_public_http_hashes.py`, justamente os gates que exigem prova de publicação e hashes HTTP pós-deploy. `audit_v3_readiness.py` testa a existência desses scripts, não comprova que eles rodaram no workflow.

Os gates de recibos e independência dependem de `http_platform_receipts.json`, `subagents_platform_receipts.json` e `trust_roots/*.attestation.json` dentro da execução monitorada. Nenhum recibo nativo, raiz administrativamente independente ou prova negativa de acesso cruzado foi disponibilizado em superfície legível deste revisor. Como `auditoria/execucoes/**` era proibido, não há prova admissível para aprovar esses requisitos.

## Revisão adversarial

Falhas mais prováveis: aprovação baseada apenas no build seguro; confusão entre existência de wrapper e execução do gate; confiança em recibos sintéticos ou inacessíveis.

cadeia re-derivada: identidade do candidato | fonte crua: git rev-parse/cat-file no worktree autorizado | resultado: bateu; HEAD=074bff85c7c560386ca0ed7f0802d4e896534571 e status limpo.

cadeia re-derivada: projeção Pages | fonte crua: `_config.yml`, quatro fontes públicas e saída Jekyll temporária | resultado: bateu; build exit 0 e conjunto emitido de quatro arquivos.

cadeia re-derivada: cobertura de gates de produção | fonte crua: `.github/workflows/portal-audit.yml` versus `NEW_GATES` em `scripts/audit_v3_readiness.py` | resultado: divergiu; `audit_publication` e `audit_public_http_hashes` existem, mas não são executados pelo workflow.

cadeia re-derivada: recibos raízes e isolamento | fonte crua: diff do candidato e dependências declaradas pelos gates | resultado: divergiu; nenhuma prova nativa verificável foi disponibilizada no escopo permitido, e a única área potencial foi expressamente proibida.

Erro mais provável ainda restante: uma produção divergente do build local. A evidência que o revelaria seria crawl HTTP integral com hashes e recibos nativos pós-deploy; ela não foi produzida. Se perguntado “tem certeza?”, a prova concreta é o diff entre lista de gates e workflow, o build exato e o ledger de pendências bloqueantes.

Veredito: NÃO CONFORME — ausência de recibos/raízes/isolamento verificáveis e gates de produção omitidos do workflow.

Status: BLOQUEADO
