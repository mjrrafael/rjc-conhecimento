# Auditoria Da Base Estadual

Gerado em 26/04/2026.

Esta auditoria mede qualidade editorial do acervo estadual antes de publicação profunda. Ela não aprova tese tributária; aponta risco de fonte, ruído, escopo e contaminação por tributo diferente de ICMS.

## Resumo

- Estados avaliados: 27
- Documentos estaduais candidatos a ICMS: 183
- Documentos úteis após teste de escopo: 174
- Documentos bloqueados por escopo material: 9
- Estados bloqueados para publicação profunda: 26

## Estados

| UF | Região | Status | Docs | Úteis | Escopo bloqueado | Recomendação | Principais alertas |
| --- | --- | --- | ---: | ---: | ---: | --- | --- |
| AC | Norte | revisao_fonte | 6 | 6 | 0 | bloquear_publicacao_ate_curadoria | contém IPVA, contém ITCMD/ITCD, contém Taxas, fonte local sem URL oficial no cabeçalho, ruído de extração/encoding |
| AL | Nordeste | revisao_fonte | 3 | 3 | 0 | bloquear_publicacao_ate_curadoria | fonte local sem URL oficial no cabeçalho, ruído de extração/encoding, texto curto para RICMS/benefícios |
| AM | Norte | revisao_fonte | 4 | 4 | 0 | bloquear_publicacao_ate_curadoria | categoria não específica de ICMS, contém IPVA, contém ITCMD/ITCD, contém Taxas, fallback amplo |
| AP | Norte | revisao_fonte | 7 | 7 | 0 | bloquear_publicacao_ate_curadoria | contém Taxas, fonte local sem URL oficial no cabeçalho, ruído de extração/encoding, texto curto para RICMS/benefícios |
| BA | Nordeste | revisao_fonte | 7 | 5 | 2 | bloquear_publicacao_ate_reclassificar_escopo | contém Taxas, escopo dominante incompatível: conteúdo parece tratar de Taxas, não de ICMS, escopo incompatível: arquivo classificado como ICMS, mas os documentos fonte indicam Taxas, escopo material incompatível com ICMS, fonte local sem URL oficial no cabeçalho |
| CE | Nordeste | revisao_fonte | 8 | 8 | 0 | bloquear_publicacao_ate_curadoria | categoria não específica de ICMS, contém IPVA, contém ITCMD/ITCD, contém Taxas, fallback amplo |
| DF | Centro-Oeste | revisao_fonte | 5 | 1 | 4 | bloquear_publicacao_ate_reclassificar_escopo | categoria não específica de ICMS, contém IPVA, contém ITCMD/ITCD, contém Taxas, escopo material incompatível com ICMS |
| ES | Sudeste | revisao_fonte | 7 | 7 | 0 | bloquear_publicacao_ate_curadoria | contém IPVA, contém Taxas, ruído de extração/encoding |
| GO | Centro-Oeste | aprovado_v1 | 0 | 0 | 0 | manter_publicado | sem alerta automatizado |
| MA | Nordeste | revisao_fonte | 10 | 10 | 0 | bloquear_publicacao_ate_curadoria | contém Taxas, fonte local sem URL oficial no cabeçalho, ruído de extração/encoding |
| MG | Sudeste | revisao_fonte | 31 | 31 | 0 | bloquear_publicacao_ate_curadoria | contém Taxas, ruído de extração/encoding |
| MS | Centro-Oeste | revisao_fonte | 5 | 5 | 0 | bloquear_publicacao_ate_curadoria | contém IPVA, contém ITCMD/ITCD, contém Taxas, ruído de extração/encoding |
| MT | Centro-Oeste | capturado_sem_aprovacao | 3 | 3 | 0 | bloquear_publicacao_ate_curadoria | contém IPVA, contém Taxas, ruído de extração/encoding |
| PA | Norte | revisao_fonte | 2 | 0 | 2 | bloquear_publicacao_ate_reclassificar_escopo | categoria não específica de ICMS, contém IPVA, contém ITCMD/ITCD, contém Taxas, escopo material incompatível com ICMS |
| PB | Nordeste | revisao_fonte | 1 | 1 | 0 | bloquear_publicacao_ate_curadoria | contém IPVA, contém ITCMD/ITCD, contém Taxas, ruído de extração/encoding |
| PE | Nordeste | revisao_fonte | 8 | 8 | 0 | bloquear_publicacao_ate_curadoria | contém Taxas, fonte local sem URL oficial no cabeçalho, ruído de extração/encoding, texto curto para RICMS/benefícios |
| PI | Nordeste | revisao_fonte | 9 | 9 | 0 | bloquear_publicacao_ate_curadoria | contém IPVA, contém Taxas, fonte local sem URL oficial no cabeçalho, ruído de extração/encoding |
| PR | Sul | revisao_fonte | 11 | 11 | 0 | bloquear_publicacao_ate_curadoria | contém Taxas, fonte local sem URL oficial no cabeçalho, ruído de extração/encoding |
| RJ | Sudeste | revisao_fonte | 1 | 1 | 0 | bloquear_publicacao_ate_curadoria | ruído de extração/encoding |
| RN | Nordeste | revisao_fonte | 8 | 8 | 0 | bloquear_publicacao_ate_curadoria | contém IPVA, contém ITCMD/ITCD, contém Taxas, fonte local sem URL oficial no cabeçalho, ruído de extração/encoding |
| RO | Norte | revisao_fonte | 4 | 3 | 1 | bloquear_publicacao_ate_reclassificar_escopo | contém IPVA, contém Taxas, escopo dominante incompatível: conteúdo parece tratar de IPVA, não de ICMS, escopo material incompatível com ICMS, fonte local sem URL oficial no cabeçalho |
| RR | Norte | revisao_fonte | 5 | 5 | 0 | bloquear_publicacao_ate_curadoria | contém IPVA, contém Taxas, fonte local sem URL oficial no cabeçalho, ruído de extração/encoding, texto curto para RICMS/benefícios |
| RS | Sul | revisao_fonte | 9 | 9 | 0 | bloquear_publicacao_ate_curadoria | contém IPVA, contém Taxas, ruído de extração/encoding |
| SC | Sul | revisao_fonte | 2 | 2 | 0 | bloquear_publicacao_ate_curadoria | ruído de extração/encoding, texto curto para RICMS/benefícios |
| SE | Nordeste | revisao_fonte | 4 | 4 | 0 | bloquear_publicacao_ate_curadoria | contém IPVA, contém Taxas, fonte local sem URL oficial no cabeçalho, ruído de extração/encoding, texto curto para RICMS/benefícios |
| SP | Sudeste | revisao_fonte | 21 | 21 | 0 | bloquear_publicacao_ate_curadoria | contém IPVA, contém Taxas, fonte local sem URL oficial no cabeçalho, ruído de extração/encoding, possível duplicidade de fonte |
| TO | Norte | revisao_fonte | 2 | 2 | 0 | bloquear_publicacao_ate_curadoria | contém Taxas, ruído de extração/encoding, texto curto para RICMS/benefícios |

## Caso Bahia: erro de escopo material

A Bahia mostrou o risco central: arquivo com rótulo de ICMS não pode ser aceito quando o próprio texto ou os documentos-fonte indicam Taxas, IPVA, ITCMD ou outro tributo. Categoria, nome do arquivo e ocorrência da palavra ICMS não bastam.

| Arquivo | Categoria | Escopo dominante | Documentos-fonte | Alerta |
| --- | --- | --- | --- | --- |
| BA_ICMS_ANEXOS.txt | ICMS_ANEXOS | Taxas | TAXAS/legest_2009_11631_taxas_anexo_II_anterior.pdf | escopo dominante incompatível: conteúdo parece tratar de Taxas, não de ICMS; escopo incompatível: arquivo classificado como ICMS, mas os documentos fonte indicam Taxas |
| BA_ICMS_ANEXOS_parte2.txt | ICMS_ANEXOS | Taxas | TAXAS/legest_2009_11631_taxas_anexo_I_anterior.pdf | escopo dominante incompatível: conteúdo parece tratar de Taxas, não de ICMS; escopo incompatível: arquivo classificado como ICMS, mas os documentos fonte indicam Taxas |

## Regra De Leitura Do Resultado

- `escopo material incompatível com ICMS` indica que o texto foi rotulado ou capturado como ICMS, mas os documentos-fonte ou a dominância do conteúdo apontam para Taxas, IPVA, ITCMD/ITCD ou outro escopo.
- `fallback amplo` indica que o portal encontrou a palavra ICMS em categoria genérica, mas não necessariamente um RICMS ou anexo de benefício.
- `ruído de extração/encoding` indica texto vindo de PDF ou HTML com caracteres corrompidos; não deve alimentar explicação didática sem limpeza.
- `contém IPVA/ITCMD/Taxas` indica que o arquivo pode misturar tributos estaduais fora do escopo de ICMS.
- `fonte local sem URL oficial no cabeçalho` indica que o texto pode ser aproveitado como acervo, mas precisa ser amarrado a link oficial antes de publicar.

## Regra Editorial Nova

Nenhum Estado pode sair de `revisao_fonte` apenas porque existe arquivo chamado RICMS ou ICMS. A curadoria precisa ler o cabeçalho, os documentos-fonte, o índice interno e amostras do texto. Se um bloco de ICMS estiver falando de Taxas, ele deve ser reclassificado, excluído da trilha de ICMS e substituído por fonte limpa antes de qualquer explicação didática.
