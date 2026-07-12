# Revisão adversarial — Monitor Portal RJC Tributário v3.0

## 1. Três falhas mais prováveis

1. Conteúdo inseguro permanece em superfície derivada mesmo após retirar o card canônico.
2. Datas/editoriais sintéticas sobrevivem em outro gerador ou arquivo estático.
3. Uma fonte responde 200, mas é homepage, índice, challenge ou não prova o campo.

## 2. Cadeias re-derivadas

cadeia re-derivada: P0 do gerador legado | fonte crua reaberta: `scripts/validated_benefits.py` no SHA 23d864f | resultado: divergiu do contrato v3; fallbacks sintéticos e publicação presumida encontrados.

## 3. Detalhe interno que derrubaria a conclusão

Qualquer URL oficial sem identidade material do ato, qualquer arquivo fora do inventário, ou qualquer leitura da Onda 2 sobre artefato da Onda 1.

## 4. Frase de controle

- Erro mais provável restante: cobertura incompleta de superfície derivada.
- Evidência necessária: inventário reconciliado, crawl/hash e fingerprint completos; ainda não produzidos.
- Provas concretas atuais: SHA baseline, worktree isolado, grep material do gerador e estado GitHub.

## 5. Veredito do passe

Defeitos e bloqueios materiais abertos; conclusão proibida.
