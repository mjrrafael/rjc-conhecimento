# Revisao adversarial — Monitor Portal RJC Tributario v3.0

## 1. Falhas mais provaveis

1. Confundir a pagina neutra em producao com certificacao do acervo juridico.
2. Aceitar JSONs/autorretratos como recibos nativos e independencia real de subagentes.
3. Retomar a PR #26 apesar de CI vermelho e commits locais posteriores que removem gates.

## 2. Cadeias re-derivadas da fonte crua

cadeia re-derivada: superficie humana | fonte crua reaberta: `C:\Users\rafae\Documents\Codex\2026-06-14\pesquisa-na-mem-ria-profunda-l\worktrees\rjc-monitor-2026-07-15-1200\_config.yml` e `https://mjrrafael.github.io/rjc-conhecimento/` | resultado: bateu; 653 HTMLs excluidos, quatro superficies emitidas, raiz 200 e 654 caminhos 404 seguros.

cadeia re-derivada: dados/IA | fonte crua reaberta: `C:\Users\rafae\Documents\Codex\2026-06-14\pesquisa-na-mem-ria-profunda-l\worktrees\rjc-monitor-2026-07-15-1200\data\benefits_crosswalk.json`, `C:\Users\rafae\Documents\Codex\2026-06-14\pesquisa-na-mem-ria-profunda-l\worktrees\rjc-monitor-2026-07-15-1200\data\benefits_quarantine.json` e `C:\Users\rafae\Documents\Codex\2026-06-14\pesquisa-na-mem-ria-profunda-l\worktrees\rjc-monitor-2026-07-15-1200\.github\workflows\portal-audit.yml` | resultado: bateu; 9.726 cards sem campos materiais, 13.150 itens em quarentena e gates v3 ausentes do workflow.

cadeia re-derivada: fontes/vigencia | fonte crua reaberta: `C:\Users\rafae\Documents\Codex\2026-06-14\pesquisa-na-mem-ria-profunda-l\worktrees\rjc-monitor-2026-07-12-1610\auditoria\execucoes\monitor-v3-2026-07-12\matriz_fontes_canonicas.csv` | resultado: bateu; 94/94 linhas minimas sem URL final, recibo HTTP, status ou hash.

cadeia re-derivada: candidate/CI | fonte crua reaberta: `https://github.com/mjrrafael/rjc-conhecimento/pull/26`, `pr_26_observation.json` e `local_candidate_workflow_diff.md` | resultado: bateu; CI da PR esta vermelho e a arvore local posterior remove os gates materiais.

## 3. Detalhe que derrubaria a conclusao

Uma URL juridica servida fora da projecao segura derrubaria a conclusao de quarentena. O revisor humano reabriu os 655 caminhos: apenas a raiz respondeu 200; os demais retornaram a 404 segura. A conclusao nunca e de liberacao do acervo.

## 4. Controle

- Erro que ainda pode restar: comportamento de Jekyll diferente da normalizacao observada via HTTP. Evidencia local exata: nao produzida, pois o binario nao esta instalado; o run Pages remoto verde e os hashes normalizados cobrem o estado deployado.
- Provas concretas: SHA Pages `f814f80e`, run Pages `29210072066`, run portal-audit `29210072326`, quatro hashes HTTP normalizados e tres revisoes desta vigilia.

## 5. Veredito

Veredito: nenhum defeito novo. Os impedimentos existentes da certificacao v3 foram confirmados; nao aprovar, nao mesclar e nao publicar conteudo juridico.
