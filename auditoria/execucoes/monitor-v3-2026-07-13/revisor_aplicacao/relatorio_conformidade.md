# Revisão de aplicação — Monitor Portal RJC Tributário v3.0

**Status literal: NÃO CONFORME.**

**Decisão operacional:** manter `BLOQUEADO TEMPORÁRIO`; não aprovar, não mesclar e não publicar o candidato.

## Síntese

A decisão conservadora do executor está correta, mas a execução não cumpriu integralmente o contrato. O baseline foi preservado, seis revisores produziram artefatos em duas ondas, os gates falharam de modo seguro diante do corpus inseguro e os quatro hashes da superfície neutra atual batem com a observação de produção. Isso não sana os gates incompletos, a ausência de recibos/raízes, a falta de independência certificável, a cobertura não reconciliada nem o fato de a Onda 2 ter revisado um SHA anterior ao HEAD final.

## Falhas críticas

1. `manifesto_diff.csv` está ausente. Pelo princípio artefato-não-narrativa, G4 é **NÃO EXECUTADO** em sua definição contratual. O verificador v3.1.1 retornou exit `1` e marcou G4 como falho.
2. A Onda 2 revisou `074bff85c7c560386ca0ed7f0802d4e896534571`; o HEAD final é `3d27f5a71f23358b32673afd767d7ef9295aa0a9`, com correção posterior em `monitor_v3_inventory.py`. No passe terminal surgiram ainda alterações não commitadas em seis arquivos de código/workflow (86 inserções, 10 remoções). Não existe revisão cega de um SHA que represente o estado executável atual.
3. As seis tasks têm caminhos distintos e `fork_turns=none`, mas a independência não é certificável: recibos nativos, prompts/hashes, tool calls, timestamps e exports são nulos; `negative_access_proof=false`; todos os agentes usam o mesmo usuário Windows. A própria Onda 1/IA registra comprometimento da cegueira por `rg` amplo.
4. Há zero recibos HTTP nativos, zero raízes de confiança, zero runners confiáveis e zero das 94 raízes mínimas com linha material completa. A matriz contém 94 raízes + 33.848 URLs referenciadas, mas nenhum `http_receipt_id`.
5. A certificação material dos gates não ocorreu: 69 células de invariantes estão `BLOQUEADO`, com 138 mutantes esperados e zero executados no artefato contratual. Testes locais de revisores existiram, mas a Onda 2/IA encontrou 16 de 17 bypasses aceitos. O workflow chama 11 dos 13 gates materiais e omite `audit_publication` e `audit_public_http_hashes`.
6. A cobertura integral não fecha. Na recontagem final: 1.038 arquivos rastreados, 1.142 arquivos no filesystem, 104 extras; o inventário possui 1.107 linhas, 69 `A_VALIDAR` e deixa 35 arquivos atuais fora. Os universos de crawl também divergem (1.070, 1.024 e 674 URLs) sem reconciliação única.
7. A suíte top-level mais recente terminou com 33 checks: 16 passaram e 17 falharam. Embora executada após o commit final, `gate_runs.json` não registra o SHA, logo não constitui recibo de SHA exato. `audit_v3_readiness` continua reprovando por manifesto, raízes, mutações/runners e 94 linhas canônicas incompletas.
8. Não houve deploy do candidato, prova de CI/Pages do SHA exato, `publication_proof.json`, `public_http_hashes.json` nem refetch pós-deploy. A produção observada é do baseline `f814f80...` e não possui recibo nativo.

## Itens substancialmente executados

- G0: baseline/merge-base conferem exatamente com `f814f80efbab84bf43b671bf544c4678d4dda82a`; trabalho ocorreu em worktree separado.
- Duas ondas produziram três revisões cada, com decisões convergentes `NÃO CONFORME`/`BLOQUEADO`; os hashes declarados dos artefatos copiados conferem.
- O universo mínimo de 81 classes estaduais + 13 federais foi enumerado; fontes, cards e quarentena foram percorridos em detalhe suficiente para sustentar o bloqueio.
- Gates v3 foram implementados e executados em modo fail-closed; o corpus inseguro não foi legitimado.
- Os hashes canônicos locais de `index.html`, `404.html`, `robots.txt` e `llms.txt` batem 4/4 com a observação HTTP da produção neutra atual.
- O fechamento literal `BLOQUEADO TEMPORÁRIO` é coerente com oito pendências abertas no ledger e com a ausência dos dois estados de sucesso.

## Itens não executados ou não comprovados

- G4 completo e `manifesto_diff.csv`.
- Independência real/certificável das ondas e prova negativa de leitura cruzada.
- Duas raízes administrativas preexistentes, dois runners confiáveis e mutação certificada por célula.
- Revisão da Onda 2 e prova de gates vinculadas ao HEAD final exato.
- Reconciliação integral Git × filesystem × inventário × geradores × build × produção.
- Recibos nativos para as 94 raízes e para o universo público referenciado.
- CI completo dos 13 gates, publicação do candidato, hashes pós-deploy e refetch integral.

## Re-derivações independentes

- cadeia re-derivada: SHA | fonte crua: `git rev-parse`, `merge-base` e commits | resultado: baseline bateu; SHA da Onda 2 divergiu do HEAD final.
- cadeia re-derivada: estado executável | fonte crua: `git status` + diff do worktree | resultado: seis arquivos de código/workflow diferem do HEAD; nenhum SHA exato representa o estado atual.
- cadeia re-derivada: G4 | fonte crua: contrato + filesystem | resultado: `manifesto_diff.csv` ausente; gate divergiu.
- cadeia re-derivada: independência | fonte crua: `subagents.json` + recibos de plataforma | resultado: seis tasks existem, mas recibos/prova negativa estão indisponíveis; certificação divergiu.
- cadeia re-derivada: raízes/gates | fonte crua: matriz canônica, matriz de invariantes e mutações | resultado: 0 recibos, 0/94 raízes completas e 0/138 mutantes certificados; divergiu.
- cadeia re-derivada: cobertura | fonte crua: `git ls-tree`, filesystem e inventário | resultado: diferenças 104/35 e 69 itens `A_VALIDAR`; divergiu.
- cadeia re-derivada: produção | fonte crua: quatro arquivos locais + observação HTTP | resultado: hashes 4/4 bateram para a superfície neutra do baseline, sem provar candidato ou pós-deploy.

Veredito: defeitos críticos permanecem; `NÃO CONFORME`.
