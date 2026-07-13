# Porta de saída — revisão cega IA/dados Onda 2

- Universo: candidato `074bff85c7c560386ca0ed7f0802d4e896534571`; somente `data/**`, `assets/**`, `scripts/**`, `.github/**`, `_config.yml`, `index.html`, `404.html`, `robots.txt`, `llms.txt` e produção pública.
- Cobertura: inventário integral por `git ls-tree`; parse de 100% dos JSON/NDJSON; consistência de busca, manifestos/chunks, sitemap/robots/LLM, geradores, build/freshness, grafo e produção.
- Gates: identificar e revisar materialmente os 13 gates candidatos, com pelo menos dois mutantes próprios por classe efetivamente testada e paths temporários aleatórios fora do worktree.
- Provas críticas: recibos nativos, raízes, isolamento, álgebra pública e fingerprints de quarentena devem ser provados por fonte crua/reexecução; ausência implica `BLOQUEADO`/`NÃO CONFORME`.
- Encerramento: seis entregáveis solicitados existem, seus CSVs/JSON parseiam, contagens fecham com o universo e um passe adversarial terminal não gera defeito novo não registrado.
