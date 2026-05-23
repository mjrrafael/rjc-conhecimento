# Auditoria Da Base Estadual

Gerado em 26/04/2026.

Esta auditoria mede qualidade editorial do acervo estadual antes de publicação profunda. Ela não aprova tese tributária; aponta risco de fonte, ruído, escopo e contaminação por tributo diferente de ICMS.

## Resumo

- Estados avaliados: 27
- Documentos estaduais candidatos a ICMS: 227
- Documentos úteis após teste de escopo: 224
- Documentos bloqueados por escopo material: 3
- Estados sem aprovação profunda após auditoria: 14

## Estados

| UF | Região | Status | Docs | Úteis | Escopo bloqueado | Recomendação | Principais alertas |
| --- | --- | --- | ---: | ---: | ---: | --- | --- |
| AC | Norte | revisado_com_pendencias | 6 | 6 | 0 | bloquear_publicacao_ate_curadoria | contém IPVA, contém ITCMD/ITCD, contém Taxas, fonte local sem URL oficial no cabeçalho, texto curto para RICMS/benefícios |
| AL | Nordeste | revisado_com_pendencias | 3 | 3 | 0 | bloquear_publicacao_ate_curadoria | fonte local sem URL oficial no cabeçalho, texto curto para RICMS/benefícios |
| AM | Norte | revisado_com_pendencias | 4 | 4 | 0 | bloquear_publicacao_ate_curadoria | categoria não específica de ICMS, contém IPVA, contém ITCMD/ITCD, contém Taxas, fallback amplo |
| AP | Norte | revisado_com_pendencias | 7 | 7 | 0 | bloquear_publicacao_ate_curadoria | contém Taxas, fonte local sem URL oficial no cabeçalho, ruído de extração/encoding, texto curto para RICMS/benefícios |
| BA | Nordeste | publicado_v1 | 15 | 15 | 0 | manter_publicado | sem alerta automatizado |
| CE | Nordeste | revisado_com_pendencias | 8 | 8 | 0 | bloquear_publicacao_ate_curadoria | categoria não específica de ICMS, contém IPVA, contém ITCMD/ITCD, contém Taxas, fallback amplo |
| DF | Centro-Oeste | publicado_v1 | 13 | 13 | 0 | manter_publicado | sem alerta automatizado |
| ES | Sudeste | publicado_v1 | 7 | 7 | 0 | manter_publicado | sem alerta automatizado |
| GO | Centro-Oeste | aprovado_v1 | 0 | 0 | 0 | manter_publicado | sem alerta automatizado |
| MA | Nordeste | revisado_com_pendencias | 10 | 10 | 0 | bloquear_publicacao_ate_curadoria | contém Taxas, fonte local sem URL oficial no cabeçalho |
| MG | Sudeste | publicado_v1 | 10 | 10 | 0 | manter_publicado | sem alerta automatizado |
| MS | Centro-Oeste | publicado_v1 | 35 | 35 | 0 | manter_publicado | sem alerta automatizado |
| MT | Centro-Oeste | publicado_v1 | 4 | 4 | 0 | manter_publicado | sem alerta automatizado |
| PA | Norte | revisado_escopo_bloqueado | 2 | 0 | 2 | bloquear_publicacao_ate_reclassificar_escopo | categoria não específica de ICMS, contém IPVA, contém ITCMD/ITCD, contém Taxas, escopo material incompatível com ICMS |
| PB | Nordeste | revisado_com_pendencias | 1 | 1 | 0 | bloquear_publicacao_ate_curadoria | contém IPVA, contém ITCMD/ITCD, contém Taxas |
| PE | Nordeste | revisado_com_pendencias | 8 | 8 | 0 | bloquear_publicacao_ate_curadoria | contém Taxas, fonte local sem URL oficial no cabeçalho, texto curto para RICMS/benefícios |
| PI | Nordeste | revisado_com_pendencias | 9 | 9 | 0 | bloquear_publicacao_ate_curadoria | contém IPVA, contém Taxas, fonte local sem URL oficial no cabeçalho |
| PR | Sul | publicado_v1 | 8 | 8 | 0 | manter_publicado | sem alerta automatizado |
| RJ | Sudeste | publicado_v1 | 25 | 25 | 0 | manter_publicado | sem alerta automatizado |
| RN | Nordeste | publicado_v1 | 19 | 19 | 0 | manter_publicado | sem alerta automatizado |
| RO | Norte | revisado_escopo_bloqueado | 4 | 3 | 1 | bloquear_publicacao_ate_reclassificar_escopo | contém IPVA, contém Taxas, escopo dominante incompatível: conteúdo parece tratar de IPVA, não de ICMS, escopo material incompatível com ICMS, fonte local sem URL oficial no cabeçalho |
| RR | Norte | revisado_com_pendencias | 5 | 5 | 0 | bloquear_publicacao_ate_curadoria | contém IPVA, contém Taxas, fonte local sem URL oficial no cabeçalho, texto curto para RICMS/benefícios |
| RS | Sul | publicado_v1 | 5 | 5 | 0 | manter_publicado | sem alerta automatizado |
| SC | Sul | publicado_v1 | 8 | 8 | 0 | manter_publicado | sem alerta automatizado |
| SE | Nordeste | revisado_com_pendencias | 4 | 4 | 0 | bloquear_publicacao_ate_curadoria | contém IPVA, contém Taxas, fonte local sem URL oficial no cabeçalho, texto curto para RICMS/benefícios |
| SP | Sudeste | publicado_v1 | 5 | 5 | 0 | manter_publicado | sem alerta automatizado |
| TO | Norte | revisado_com_pendencias | 2 | 2 | 0 | bloquear_publicacao_ate_curadoria | contém Taxas, texto curto para RICMS/benefícios |

## Regra De Leitura Do Resultado

- `escopo material incompatível com ICMS` indica que o texto foi rotulado ou capturado como ICMS, mas os documentos-fonte ou a dominância do conteúdo apontam para Taxas, IPVA, ITCMD/ITCD ou outro escopo.
- `fallback amplo` indica que o portal encontrou a palavra ICMS em categoria genérica, mas não necessariamente um RICMS ou anexo de benefício.
- `ruído de extração/encoding` indica texto vindo de PDF ou HTML com caracteres corrompidos; não deve alimentar explicação didática sem limpeza.
- `contém IPVA/ITCMD/Taxas` indica que o arquivo pode misturar tributos estaduais fora do escopo de ICMS.
- `fonte local sem URL oficial no cabeçalho` indica que o texto pode ser aproveitado como acervo, mas precisa ser amarrado a link oficial antes de publicar.

## Regra Editorial Nova

Estados em `revisado_com_pendencias`, `revisado_escopo_bloqueado` ou `aguardando_revisao` podem ficar publicados para leitura na web, mas não representam conclusão tributária aprovada. Nenhum Estado sai desse selo apenas porque existe arquivo chamado RICMS ou ICMS. A curadoria precisa ler o cabeçalho, os documentos-fonte, o índice interno e amostras do texto. Se um bloco de ICMS estiver falando de Taxas, IPVA, ITCMD/ITCD ou outro escopo material incompatível, ele deve ser reclassificado, excluído da trilha de ICMS e substituído por fonte limpa antes de qualquer explicação didática.
