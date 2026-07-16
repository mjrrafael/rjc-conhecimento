# Achados e pendências — liberação 2026-07-16

## CORRIGIR antes de publicar integralmente

1. `audit_v3_readiness.py` reprovou o baseline: faltam 13 hard gates materiais, não há duas raízes de confiança preexistentes comprovadas e as 94 linhas da matriz canônica não possuem URL, recibo e hash materiais.
2. O corpus legado contém 9.726 cards e 13.150 entradas em quarentena. O código histórico usava datas de captura e valores padrão; o acervo não pode ser tornado público só removendo exclusões do Pages.
3. O candidato local `6d8dc9d7` só seleciona sete cards e declara expressamente recibos `LOCAL_REPRODUCIBLE_NOT_PLATFORM_NATIVE`; portanto, ele não atende à exigência de recibos nativos nem representa a restauração integral solicitada.
4. A revisão independente da aplicação confirmou que o dossiê inicial não continha os IDs obrigatórios `RAC-001` a `RAC-005` no ledger nem o resultado do gate material `G4`; ambos foram registrados nesta correção. A revisão também rederivou diretamente as contagens de 9.726 cards, 13.150 itens de quarentena, 658 HTML, 655 URLs de sitemap e 19.089 entradas de busca.

## Pendências objetivas

- Revalidar cada fonte/campo do conjunto publicável e registrar recibos nativos e revisão independente.
- Reconstruir a matriz nacional de fontes e o inventário público completo.
- Regerar a projeção e executar a bateria de gates no SHA candidato.
- Publicar por PR, confirmar CI, Pages, hashes e refetch pós-deploy.
- Não tomar a aprovação estrutural do verificador de rito como certificação jurídica: a revisão independente declarou `NÃO CONFORME` para uma liberação integral e prevalece sobre essa checagem de forma.
