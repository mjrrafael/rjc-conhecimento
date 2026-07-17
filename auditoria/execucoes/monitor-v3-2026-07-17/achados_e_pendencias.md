# Achados e pendências

## Achados confirmados nesta vigília

1. O worktree compartilhado do usuário está sujo em larga escala; foi preservado. A análise ocorre em worktree novo, limpo, criado diretamente de `origin/main`.
2. A raiz de produção retornou HTTP 200, corpo de 929 bytes e o mesmo SHA-256 registrado no último monitoramento. O aviso técnico está presente e não houve padrão de conteúdo tributário operacional na raiz.
3. O repositório ainda possui quatro PRs draft. Nenhuma foi tratada como publicação ou candidata a merge nesta vigília.
4. P0 — o domínio Pages está fail-closed, mas `raw.githubusercontent.com` expõe 875/875 arquivos legados do SHA de `main`: 658 HTML (~508 MB), 212 arquivos `data/*` (~101 MB) e cinco artefatos de busca (~51 MB). O NCM raw contém 7.050 registros sem `field_provenance` ou `verification_receipt_id`.
5. O `assets/build-freshness.json` ainda descrevia versões anteriores de `llms.txt` e do crosswalk saneado. O manifesto foi reconciliado e os gates de matriz/editorial agora distinguem explicitamente um conjunto público vazio fail-closed de uma matriz vazia indevida.

## Pendências que impedem restauração de conteúdo

- Provar integralmente matriz canônica, proveniência por campo e refetches com recibos HTTP nativos confrontáveis.
- Disponibilizar duas raízes de confiança preexistentes e administrativamente independentes para os ensaios de mutação.
- Disponibilizar isolamento efetivo e prova negativa de leitura entre ondas de revisão; este ambiente compartilhado não permite certificá-lo sozinho.
- Executar os gates integrais e a publicação somente após os três itens anteriores.
- Migrar o corpus não comprovado para armazenamento privado e remover/purgar sua exposição no GitHub Raw, inclusive o histórico público aplicável. Isto exige decisão externa de retenção, destino privado e estratégia de reescrita; não é seguro nem possível certificá-lo apenas neste ambiente compartilhado.
