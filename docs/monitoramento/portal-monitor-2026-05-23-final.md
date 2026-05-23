# Auditoria Do Portal RJC Tributario Aberto

- Data: 2026-05-23 18:34:56
- Repo: `C:\Users\kris2\OneDrive\Documentos\Playbook\rjc-conhecimento`
- Base publica: https://mjrrafael.github.io/rjc-conhecimento

## Metricas

- `benefit_rows`: 12223
- `git_dirty_entries`: 0
- `html_pages`: 644
- `live:assets/llm-manifest.json`: 202491
- `live:beneficios/index.html`: 59464099
- `live:beneficios/ncm.html`: 30224125
- `live:confaz/ultimos-5-anos.html`: 128721
- `live:estados/index.html`: 33337
- `live:federal/index.html`: 10575
- `live:federal/legislacao/reforma-tributaria/index.html`: 41089
- `live:folha-clt/index.html`: 15279
- `live:index.html`: 14587
- `live:llms.txt`: 123839
- `live:robots.txt`: 308
- `live:sitemap.xml`: 146714
- `llm_manifest_entries`: 644
- `ncm_rows`: 7942
- `repo`: C:\Users\kris2\OneDrive\Documentos\Playbook\rjc-conhecimento
- `search_terms_missing`: 0
- `search_terms_tested`: 13
- `sitemap_urls`: 644
- `size:assets/llm-manifest.json`: 202491
- `size:assets/portal-search-full.json`: 51767459
- `size:assets/portal-search.js`: 311187
- `size:data/benefits_crosswalk.json`: 56101124
- `size:data/legal_sources_registry.json`: 267717
- `size:data/ncm_benefits_index.json`: 23105136
- `size:index.html`: 14587
- `size:llms.txt`: 123839
- `size:robots.txt`: 308
- `size:sitemap.txt`: 62240
- `size:sitemap.xml`: 146714

## CRITICO (0)

- Nenhum achado.

## ALTO (0)

- Nenhum achado.

## MEDIO (1)

- **performance**: Arquivo acima de 50 MB: data/benefits_crosswalk.json
  Evidencia: 56101124 bytes
  Recomendacao: Dividir pagina/dado em blocos menores para melhorar GitHub Pages e leitura por LLMs.

## BAIXO (0)

- Nenhum achado.

## INFO (1)

- **google**: Indexabilidade tecnica nao prova indexacao no Google.
  Evidencia: Confirmar indexacao real via Search Console, URL Inspection ou consulta site: em data absoluta.
  Recomendacao: Enviar sitemap no Search Console e solicitar indexacao das paginas principais.
