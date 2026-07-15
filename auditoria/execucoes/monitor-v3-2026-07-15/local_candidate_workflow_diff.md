# Diff observado — candidato local nao publicado

Comparacao: `5fd601925898042926cd9cd3d760ae8a033672d5..6d8dc9d7e811bb05938fc8c983d65ff25ce9d19a` em `.github/workflows/portal-audit.yml`.

O candidato local posterior substitui a auditoria Pages e a sequencia de gates v3 por um workflow que somente constroi `public/`, roda `audit_restored_portal.py`, executa um teste de restauracao e publica artefato Pages. Foram removidas as chamadas a `audit_v3_readiness.py`, `audit_field_provenance.py`, `audit_no_synthetic_legal_dates.py`, `audit_verification_receipts.py`, `audit_http_platform_receipts.py`, `audit_link_receipts.py`, `audit_internalization_evidence.py`, `audit_full_content_coverage.py`, `audit_canonical_source_scope.py`, `audit_public_set_algebra.py`, `audit_quarantine_fingerprints.py` e `audit_subagent_independence.py`.

Conclusao: os commits locais posteriores nao preservam o contrato v3 do candidato remoto e nao podem ser enviados ou usados para retomar a PR #26.
