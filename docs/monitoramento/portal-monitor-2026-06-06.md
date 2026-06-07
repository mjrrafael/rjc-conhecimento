# Auditoria Do Portal RJC Tributario Aberto

- Data: 2026-06-06 19:19:39
- Repo: `C:\Users\kris2\OneDrive\Documentos\Playbook\rjc-conhecimento`
- Base publica: https://mjrrafael.github.io/rjc-conhecimento

## Metricas

- `benefit_rows`: 12246
- `git_dirty_entries`: 1
- `html_pages`: 645
- `live:assets/llm-manifest.json`: 202790
- `live:beneficios/index.html`: 59564051
- `live:beneficios/ncm.html`: 30355838
- `live:confaz/ultimos-5-anos.html`: 128721
- `live:estados/index.html`: 33337
- `live:federal/index.html`: 10575
- `live:federal/legislacao/reforma-tributaria/index.html`: 41089
- `live:folha-clt/index.html`: 15279
- `live:index.html`: 14587
- `live:llms.txt`: 124004
- `live:robots.txt`: 308
- `live:sitemap.xml`: 146950
- `llm_manifest_entries`: 645
- `ncm_rows`: 7976
- `repo`: C:\Users\kris2\OneDrive\Documentos\Playbook\rjc-conhecimento
- `search_terms_missing`: 0
- `search_terms_tested`: 13
- `sitemap_urls`: 645
- `size:assets/llm-manifest.json`: 202790
- `size:assets/portal-search-full.json`: 51874156
- `size:assets/portal-search.js`: 311595
- `size:data/benefits_crosswalk.json`: 56194945
- `size:data/legal_sources_registry.json`: 268883
- `size:data/ncm_benefits_index.json`: 23204437
- `size:index.html`: 14587
- `size:llms.txt`: 124004
- `size:robots.txt`: 308
- `size:sitemap.txt`: 62345
- `size:sitemap.xml`: 146950

## CRITICO (0)

- Nenhum achado.

## ALTO (0)

- Nenhum achado.

## MEDIO (2)

- **git**: Worktree possui alteracoes locais.
  Evidencia: ?? docs/monitoramento/portal-monitor-2026-06-06.md
  Recomendacao: Separar alteracoes do usuario antes de corrigir e publicar.
- **performance**: Arquivo acima de 50 MB: data/benefits_crosswalk.json
  Evidencia: 56194945 bytes
  Recomendacao: Dividir pagina/dado em blocos menores para melhorar GitHub Pages e leitura por LLMs.

## BAIXO (0)

- Nenhum achado.

## INFO (1)

- **google**: Indexabilidade tecnica nao prova indexacao no Google.
  Evidencia: Confirmar indexacao real via Search Console, URL Inspection ou consulta site: em data absoluta.
  Recomendacao: Enviar sitemap no Search Console e solicitar indexacao das paginas principais.
