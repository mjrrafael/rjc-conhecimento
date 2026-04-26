# Auditoria Da Base Estadual

Gerado em 26/04/2026.

Esta auditoria mede qualidade editorial do acervo estadual antes de publicação profunda. Ela não aprova tese tributária; apenas aponta risco de fonte, ruído e escopo.

## Resumo

- Estados avaliados: 27
- Documentos estaduais detectados: 183
- Estados bloqueados para publicação profunda: 26

## Estados

| UF | Região | Status | Docs | Recomendação | Principais alertas |
| --- | --- | --- | ---: | --- | --- |
| AC | Norte | revisao_fonte | 6 | bloquear_publicacao_ate_curadoria | contém IPVA, contém ITCMD/ITCD, contém Taxas, fonte local sem URL oficial no cabeçalho, ruído de extração/encoding |
| AL | Nordeste | revisao_fonte | 3 | bloquear_publicacao_ate_curadoria | fonte local sem URL oficial no cabeçalho, ruído de extração/encoding, texto curto para RICMS/benefícios |
| AM | Norte | revisao_fonte | 4 | bloquear_publicacao_ate_curadoria | categoria não específica de ICMS, contém IPVA, contém ITCMD/ITCD, contém Taxas, fallback amplo |
| AP | Norte | revisao_fonte | 7 | bloquear_publicacao_ate_curadoria | contém Taxas, fonte local sem URL oficial no cabeçalho, ruído de extração/encoding, texto curto para RICMS/benefícios |
| BA | Nordeste | revisao_fonte | 7 | bloquear_publicacao_ate_curadoria | contém Taxas, fonte local sem URL oficial no cabeçalho, ruído de extração/encoding, texto curto para RICMS/benefícios |
| CE | Nordeste | revisao_fonte | 8 | bloquear_publicacao_ate_curadoria | categoria não específica de ICMS, contém IPVA, contém ITCMD/ITCD, contém Taxas, fallback amplo |
| DF | Centro-Oeste | revisao_fonte | 5 | bloquear_publicacao_ate_curadoria | categoria não específica de ICMS, contém IPVA, contém ITCMD/ITCD, contém Taxas, fallback amplo |
| ES | Sudeste | revisao_fonte | 7 | bloquear_publicacao_ate_curadoria | contém IPVA, contém Taxas, ruído de extração/encoding |
| GO | Centro-Oeste | aprovado_v1 | 0 | manter_publicado | sem alerta automatizado |
| MA | Nordeste | revisao_fonte | 10 | bloquear_publicacao_ate_curadoria | contém Taxas, fonte local sem URL oficial no cabeçalho, ruído de extração/encoding |
| MG | Sudeste | revisao_fonte | 31 | bloquear_publicacao_ate_curadoria | contém Taxas, ruído de extração/encoding |
| MS | Centro-Oeste | revisao_fonte | 5 | bloquear_publicacao_ate_curadoria | contém IPVA, contém ITCMD/ITCD, contém Taxas, ruído de extração/encoding |
| MT | Centro-Oeste | capturado_sem_aprovacao | 3 | bloquear_publicacao_ate_curadoria | contém IPVA, contém Taxas, ruído de extração/encoding |
| PA | Norte | revisao_fonte | 2 | bloquear_publicacao_ate_curadoria | categoria não específica de ICMS, contém IPVA, contém ITCMD/ITCD, contém Taxas, fallback amplo |
| PB | Nordeste | revisao_fonte | 1 | bloquear_publicacao_ate_curadoria | contém IPVA, contém ITCMD/ITCD, contém Taxas, ruído de extração/encoding |
| PE | Nordeste | revisao_fonte | 8 | bloquear_publicacao_ate_curadoria | contém Taxas, fonte local sem URL oficial no cabeçalho, ruído de extração/encoding, texto curto para RICMS/benefícios |
| PI | Nordeste | revisao_fonte | 9 | bloquear_publicacao_ate_curadoria | contém IPVA, contém Taxas, fonte local sem URL oficial no cabeçalho, ruído de extração/encoding |
| PR | Sul | revisao_fonte | 11 | bloquear_publicacao_ate_curadoria | contém Taxas, fonte local sem URL oficial no cabeçalho, ruído de extração/encoding |
| RJ | Sudeste | revisao_fonte | 1 | bloquear_publicacao_ate_curadoria | ruído de extração/encoding |
| RN | Nordeste | revisao_fonte | 8 | bloquear_publicacao_ate_curadoria | contém IPVA, contém ITCMD/ITCD, contém Taxas, fonte local sem URL oficial no cabeçalho, ruído de extração/encoding |
| RO | Norte | revisao_fonte | 4 | bloquear_publicacao_ate_curadoria | contém IPVA, contém Taxas, fonte local sem URL oficial no cabeçalho, ruído de extração/encoding |
| RR | Norte | revisao_fonte | 5 | bloquear_publicacao_ate_curadoria | contém IPVA, contém Taxas, fonte local sem URL oficial no cabeçalho, ruído de extração/encoding, texto curto para RICMS/benefícios |
| RS | Sul | revisao_fonte | 9 | bloquear_publicacao_ate_curadoria | contém IPVA, contém Taxas, ruído de extração/encoding |
| SC | Sul | revisao_fonte | 2 | bloquear_publicacao_ate_curadoria | ruído de extração/encoding, texto curto para RICMS/benefícios |
| SE | Nordeste | revisao_fonte | 4 | bloquear_publicacao_ate_curadoria | contém IPVA, contém Taxas, fonte local sem URL oficial no cabeçalho, ruído de extração/encoding, texto curto para RICMS/benefícios |
| SP | Sudeste | revisao_fonte | 21 | bloquear_publicacao_ate_curadoria | contém IPVA, contém Taxas, fonte local sem URL oficial no cabeçalho, ruído de extração/encoding, possível duplicidade de fonte |
| TO | Norte | revisao_fonte | 2 | bloquear_publicacao_ate_curadoria | contém Taxas, ruído de extração/encoding, texto curto para RICMS/benefícios |

## Leitura Do Resultado

- `fallback amplo` indica que o portal encontrou a palavra ICMS em categoria genérica, mas não necessariamente um RICMS ou anexo de benefício.
- `ruído de extração/encoding` indica texto vindo de PDF ou HTML com caracteres corrompidos; não deve alimentar explicação didática sem limpeza.
- `contém IPVA/ITCMD/Taxas` indica que o arquivo pode misturar tributos estaduais fora do escopo de ICMS.
- `fonte local sem URL oficial no cabeçalho` indica que o texto pode ser aproveitado como acervo, mas precisa ser amarrado a link oficial antes de publicar.
