# Gates executados

| Gate | Resultado | Evidência material |
| --- | --- | --- |
| `compileall` | OK | exit 0 |
| `audit_v3_readiness.py` | BLOQUEADO | exit 1: 13 gates ausentes, duas raízes não comprovadas e 94 linhas canônicas sem recibo/hash |
| `audit_master_coverage.py` | OK | conjunto de benefícios explicitamente fail-closed aceito; 27 UFs estruturais e 7.050 NCM lidos, sem autorização de publicação |
| `audit_editorial_date_per_card.py` | OK | regra editorial não aplicável ao conjunto explicitamente vazio e bloqueado |
| `audit_index_freshness.py` | OK | checksums do crosswalk e `llms.txt` reconciliados |
| `audit_benefit_dataset_sanitization.py` | OK | zero entradas materiais em crosswalk/quarentena públicos |
| `audit_quarantine_isolation.py` | OK | zero IDs no dataset de quarentena público |
| `audit_divergence_html_json_search.py` | OK | convergência da projeção de benefícios vazia |
| `audit_portal.py` | BLOQUEADO | exit 1 em 658 HTML legados; eles permanecem no Git Raw e não podem ser reativados |
| mutante matriz vazia sem estado fail-closed | OK | gate retornou 1 |
| mutante editorial vazio sem estado fail-closed | OK | gate retornou 1 |

O ambiente não tem Ruby/Jekyll local; a execução exata de Pages no SHA `4caecc1c61e98e76a6c4a4eedaf10ada9e1d4e5f` foi verde no GitHub Actions (`portal-audit` 29516745669; Pages 29516744667). Isso não certifica o candidato desta vigília.
