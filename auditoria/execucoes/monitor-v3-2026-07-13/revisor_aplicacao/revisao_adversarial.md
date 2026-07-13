# Revisão adversarial independente

cadeia re-derivada: SHA exato | fonte crua: Git no worktree | resultado: baseline `f814f80efbab84bf43b671bf544c4678d4dda82a` bateu; Onda 2=`074bff85c7c560386ca0ed7f0802d4e896534571` divergiu do HEAD=`3d27f5a71f23358b32673afd767d7ef9295aa0a9`.

cadeia re-derivada: estado executável atual | fonte crua: `git status` + diff do worktree | resultado: seis arquivos de código/workflow têm 86 inserções e 10 remoções não commitadas; nenhum SHA exato representa o estado atual.

cadeia re-derivada: presença contratual | fonte crua: `contrato_execucao.yaml` + enumeração top-level | resultado: `manifesto_diff.csv` ausente; G4 divergiu.

cadeia re-derivada: independência | fonte crua: `subagents.json` e `subagents_platform_receipts.json` | resultado: 3+3 tasks distintas existem, mas recibos nativos e prova negativa não existem; certificação divergiu.

cadeia re-derivada: raízes e mutações | fonte crua: `matriz_fontes_canonicas.csv`, `gate_invariant_matrix.csv` e `gate_mutation_results.json` | resultado: 0/94 raízes completas, 0 recibos nativos, 0/138 mutantes certificados e 0/2 raízes; divergiu.

cadeia re-derivada: cobertura | fonte crua: `git ls-tree`, filesystem e `inventario_integral.csv` | resultado: rastreados=1.038, filesystem=1.142, extras=104; inventário=1.107 e faltantes atuais=35; divergiu.

cadeia re-derivada: produção | fonte crua: arquivos locais e `production_observation.json` | resultado: hashes canônicos 4/4 bateram para a superfície neutra do baseline; candidato e pós-deploy continuam não provados.

Qual detalhe derruba um falso concluído? O SHA final não revisado, o manifesto inexistente, a ausência de recibos/raízes e a cobertura não fechada.

Veredito: defeitos críticos permanecem; NÃO CONFORME.
