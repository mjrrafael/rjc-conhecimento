# Revisão adversarial consolidada

## Porta de saída testada

`CONCLUÍDO E PUBLICADO` falha porque o candidato não foi mesclado, o CI material não está verde, Pages não incorpora o candidato e não existe refetch pós-deploy. `SEM ALTERAÇÃO — PRODUÇÃO INTEGRALMENTE VERIFICADA` falha porque há mudanças e a reconstrução jurídica integral não tem recibos nativos. O único estado honesto é **BLOQUEADO TEMPORÁRIO**.

## Cadeias re-derivadas

- cadeia re-derivada: `data/benefits_crosswalk.json` foi percorrido pelos revisores de fontes e IA; 9.726/9.726 cards publicáveis não apresentam proveniência/recibos e reproduzem `captured_on` nos campos jurídicos.
- cadeia re-derivada: os cards ICMS foram filtrados por jurisdição e imposto; 9.611/9.611 não apresentam ato específico da autoridade competente sustentando internalização.
- cadeia re-derivada: `data/benefits_quarantine.json` foi inventariado integralmente; 13.150/13.150 itens carregam conteúdo material e não têm fingerprint de isolamento.
- cadeia re-derivada: a matriz mínima fixa foi reconstruída sem herdar a matriz do coordenador; 94/94 classes foram enumeradas, mas 0/94 possui recibo nativo.
- cadeia re-derivada: o build Pages 232 emite somente `index.html`, `404.html`, `robots.txt` e `llms.txt`; os hashes HTTP da produção permanecem iguais ao baseline seguro.
- cadeia re-derivada: os gates foram executados contra o corpus real e contra mutantes dos revisores; eles falham no corpus inseguro, mas sua eficácia não pode ser certificada sem duas raízes/runners independentes.

## Ataques à própria conclusão

- “A produção está segura, então o ciclo pode concluir”: rejeitado; o contrato também exige corpus, proveniência, recibos, ondas independentes e CI/Pages do SHA exato.
- “Os agentes usaram worktrees somente leitura, então são independentes”: rejeitado; todos executam sob o mesmo usuário Windows e não existe prova negativa nativa dos caminhos lidos.
- “Os mutantes locais provam os gates”: rejeitado; executor e revisores da rodada não formam as duas raízes administrativas preexistentes exigidas.
- “A matriz tem linhas OK, então as fontes estão provadas”: rejeitado; conectividade e hash autocapturado sem recibo de plataforma não provam ato, localizador ou campo.
- “Onda 2 certificou o candidato”: rejeitado; houve alteração posterior no gerador de inventário.

Resultado adversarial: não existe caminho legítimo de sucesso nesta vigília.

## Reteste de correções locais

A travessia `RJC_MONITOR_RUN=../../escape-monitor-v3-test` passou a terminar com código 1 antes da criação do destino. O workflow passou a expor os dois gates pós-publicação apenas em execução manual posterior ao deploy. As classes de bypass material identificadas foram endurecidas no código; como essas alterações não pertencem ao SHA cego, permanecem não certificadas e exigem nova Onda 2.
