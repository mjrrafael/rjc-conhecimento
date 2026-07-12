# Revisão adversarial — Monitor Portal RJC Tributário v3.0

## 1. Três falhas mais prováveis

1. Conteúdo inseguro permanece em superfície derivada mesmo após retirar o card canônico.
2. Datas/editoriais sintéticas sobrevivem em outro gerador ou arquivo estático.
3. Uma fonte responde 200, mas é homepage, índice, challenge ou não prova o campo.

## 2. Cadeias re-derivadas

cadeia re-derivada: P0 do gerador legado | fonte crua reaberta: `scripts/validated_benefits.py` no SHA 23d864f | resultado: divergiu do contrato v3; fallbacks sintéticos e publicação presumida encontrados.

cadeia re-derivada: superfície/quarentena | fontes cruas reabertas: 13.150 registros e 678 URLs de produção pela Onda 1 IA/dados | resultado: endpoint da quarentena HTTP 200 e 6.728 sobreposições por shingle.

cadeia re-derivada: portal humano | fontes cruas reabertas: 990 arquivos, 655 HTML e 991 GETs anônimos pela Onda 1 humana | resultado: 29.369 pares fingerprint registro×página; 3 respostas HTTP 503.

cadeia re-derivada: fontes/vigência | fontes cruas reabertas: 1.917 alvos e 1.865 recibos persistidos pela Onda 1 jurídica | resultado: só 797 HTTP 200 completos; 92.980 identidades e 485 internalizações não comprovadas.

## 3. Detalhe interno que derrubaria a conclusão

Qualquer URL oficial sem identidade material do ato, qualquer arquivo fora do inventário, ou qualquer leitura da Onda 2 sobre artefato da Onda 1.

## 4. Frase de controle

- Erro mais provável restante: cobertura incompleta de superfície derivada.
- Evidência necessária: inventário reconciliado, crawl/hash e fingerprint completos; ainda não produzidos.
- Provas concretas atuais: SHA baseline, worktree isolado, grep material do gerador e estado GitHub.

## 5. Veredito do passe

Onda 1 convergiu em NÃO CONFORME. A projeção candidata foi reduzida a aviso neutro via Jekyll, mas Onda 2, recibos nativos, raízes de confiança, CI, merge e produção permanecem bloqueados; conclusão proibida.
