from __future__ import annotations

import csv
import json
import os
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

OUT = Path(r"C:\Users\rafae\AppData\Local\Temp\rjc-monitor-2026-07-13-wave2\ia")
ROOT = Path(r"C:\Users\rafae\Documents\Codex\2026-06-14\pesquisa-na-mem-ria-profunda-l\worktrees\rjc-monitor-2026-07-13-wave2-ia")
os.environ["RJC_MONITOR_RUN"] = str(OUT)
sys.path.insert(0, str(ROOT / "scripts"))
import portal_v3_gates as g

H1 = "1" * 64
H2 = "2" * 64
URL = "https://www.gov.br/receitafederal/pt-br/assuntos/norma-123"
results = []


@contextmanager
def patch(**items):
    old = {k: getattr(g, k) for k in items}
    try:
        for k, v in items.items():
            setattr(g, k, v)
        yield
    finally:
        for k, v in old.items():
            setattr(g, k, v)


def record(gate, name, errors, expect_fail=True):
    detected = bool(errors) if expect_fail else not bool(errors)
    results.append({"gate": gate, "mutant": name, "expected": "FAIL" if expect_fail else "PASS", "detected": detected, "errors": errors[:5]})


def provenance_card():
    return {"id": "card-abcdef12", "publishable": True, "publicacao": "2026-01-02", "field_provenance": {"publicacao": {
        "card_id": "card-abcdef12", "field": "publicacao", "value": "2026-01-02", "final_url": URL,
        "http_status": "200", "mime": "text/html", "body_sha256": H1, "literal_excerpt": "Publicada em 2 de janeiro de 2026.",
        "locator": "artigo 1 pagina 1", "normalization_rule": "data literal para ISO",
    }}}


def native(receipt_id):
    return {"native_call_id": receipt_id, "tool": "http", "timestamp": "2026-07-13T00:00:00-03:00", "request": {"url": URL},
            "redirects": [], "response": {}, "status": "200", "mime": "text/html", "bytes": 100, "body_sha256": H1,
            "act_identity": {"type_number": "Lei 1", "authority": "RFB", "jurisdiction": "BR", "date_locator": "art. 1", "supporting_excerpt": "texto legal material"},
            "title": "Lei 1", "body_markers": "artigo primeiro"}


def run():
    # 1 field provenance
    base = provenance_card()
    with patch(public_cards=lambda: iter([(ROOT / "data/benefits_crosswalk.json", "$[0]", base)])):
        record("audit_field_provenance", "baseline", g.gate_field_provenance(), False)
        x = json.loads(json.dumps(base)); del x["field_provenance"]["publicacao"]["body_sha256"]
        with patch(public_cards=lambda: iter([(ROOT / "data/benefits_crosswalk.json", "$[0]", x)])):
            record("audit_field_provenance", "missing_body_hash", g.gate_field_provenance())
        x = json.loads(json.dumps(base)); x["field_provenance"]["publicacao"]["final_url"] = "https://example.com/fake"
        with patch(public_cards=lambda: iter([(ROOT / "data/benefits_crosswalk.json", "$[0]", x)])):
            record("audit_field_provenance", "nonofficial_url", g.gate_field_provenance())

    # 2 no synthetic dates
    with patch(public_cards=lambda: iter([(ROOT / "data/benefits_crosswalk.json", "$[0]", base)])):
        record("audit_no_synthetic_legal_dates", "baseline", g.gate_no_synthetic_legal_dates(), False)
    x = json.loads(json.dumps(base)); x["field_provenance"].pop("publicacao")
    with patch(public_cards=lambda: iter([(ROOT / "data/benefits_crosswalk.json", "$[0]", x)])):
        record("audit_no_synthetic_legal_dates", "missing_date_proof", g.gate_no_synthetic_legal_dates())
    x = json.loads(json.dumps(base)); x["field_provenance"]["publicacao"]["value"] = "2026-01-03"
    with patch(public_cards=lambda: iter([(ROOT / "data/benefits_crosswalk.json", "$[0]", x)])):
        record("audit_no_synthetic_legal_dates", "mismatched_date_value", g.gate_no_synthetic_legal_dates())

    # 3 verification receipts
    c = {"id": "card-a", "publishable": True, "verification_receipt_id": "vr-abcdef12"}
    vr = {"id": "vr-abcdef12", "previous_card_sha256": H1, "final_card_sha256": H2,
          "http_receipt_ids": ["http-a123", "http-b123"], "fields_checked": ["publicacao"], "result": "PASS", "reviewer": "reviewer-a"}
    with patch(public_cards=lambda: iter([(ROOT / "data/benefits_crosswalk.json", "$[0]", c)]), verification_receipts=lambda: {"vr-abcdef12": vr}):
        record("audit_verification_receipts", "baseline", g.gate_verification_receipts(), False)
        bad = dict(vr); bad["http_receipt_ids"] = ["http-a123"]
        with patch(verification_receipts=lambda: {"vr-abcdef12": bad}):
            record("audit_verification_receipts", "single_http_capture", g.gate_verification_receipts())
    c2 = dict(c); c2["id"] = "card-b"
    with patch(public_cards=lambda: iter([(ROOT / "data/benefits_crosswalk.json", "$[0]", c), (ROOT / "data/benefits_crosswalk.json", "$[1]", c2)]), verification_receipts=lambda: {"vr-abcdef12": vr}):
        record("audit_verification_receipts", "reused_receipt", g.gate_verification_receipts())

    # 4 HTTP native receipts
    bundle = {"native_receipt_status": "AVAILABLE", "receipts": [native("http-a123")]}
    with patch(load_receipt_bundle=lambda: bundle): record("audit_http_platform_receipts", "baseline", g.gate_http_platform_receipts(), False)
    with patch(load_receipt_bundle=lambda: {"native_receipt_status": "UNAVAILABLE"}): record("audit_http_platform_receipts", "native_unavailable", g.gate_http_platform_receipts())
    bad = json.loads(json.dumps(bundle)); bad["receipts"][0]["request"]["cookies"] = "secret"
    with patch(load_receipt_bundle=lambda: bad): record("audit_http_platform_receipts", "authenticated_capture", g.gate_http_platform_receipts())

    # 5 link receipts
    lc = {"id": "card-link", "publishable": True, "independent_http_receipt_ids": ["http-a123", "http-b123"]}
    receipts = {"http-a123": native("http-a123"), "http-b123": native("http-b123")}
    with patch(public_cards=lambda: iter([(ROOT / "data/benefits_crosswalk.json", "$[0]", lc)]), native_receipts_by_id=lambda: receipts):
        record("audit_link_receipts", "baseline", g.gate_link_receipts(), False)
    badc = dict(lc); badc["independent_http_receipt_ids"] = ["http-a123"]
    with patch(public_cards=lambda: iter([(ROOT / "data/benefits_crosswalk.json", "$[0]", badc)]), native_receipts_by_id=lambda: receipts):
        record("audit_link_receipts", "single_link_receipt", g.gate_link_receipts())
    badr = json.loads(json.dumps(receipts)); badr["http-b123"]["title"] = "Access denied challenge"
    with patch(public_cards=lambda: iter([(ROOT / "data/benefits_crosswalk.json", "$[0]", lc)]), native_receipts_by_id=lambda: badr):
        record("audit_link_receipts", "challenge_body", g.gate_link_receipts())

    # 6 internalization
    ic = {"id": "card-icms", "publishable": True, "jurisdiction": "SP", "tax": "ICMS", "internalization_status": "COMPROVADA",
          "internalization_evidence": {"act": "Decreto 1", "authority": "SEFAZ", "jurisdiction": "SP", "benefit": "isenção",
                                       "final_url": "https://legislacao.fazenda.sp.gov.br/x", "body_sha256": H1, "locator": "art. 1"}}
    with patch(public_cards=lambda: iter([(ROOT / "data/benefits_crosswalk.json", "$[0]", ic)])): record("audit_internalization_evidence", "baseline", g.gate_internalization_evidence(), False)
    x = dict(ic); x["internalization_status"] = "NÃO_COMPROVADA"
    with patch(public_cards=lambda: iter([(ROOT / "data/benefits_crosswalk.json", "$[0]", x)])): record("audit_internalization_evidence", "not_proven", g.gate_internalization_evidence())
    x = json.loads(json.dumps(ic)); x["internalization_evidence"]["body_sha256"] = "bad"
    with patch(public_cards=lambda: iter([(ROOT / "data/benefits_crosswalk.json", "$[0]", x)])): record("audit_internalization_evidence", "bad_internalization_hash", g.gate_internalization_evidence())

    # temp run for gates backed by files
    temp = Path(tempfile.mkdtemp(prefix="gates-", dir=OUT))
    g.RUN = temp

    # 7 full content coverage
    fs = {"_config.yml", "index.html", "404.html", "robots.txt", "llms.txt"}
    inv = temp / "inventario_integral.csv"
    def write_inv(status="OK", files=fs):
        with inv.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["caminho_ou_id", "status"]); w.writeheader();
            for rel in sorted(files): w.writerow({"caminho_ou_id": rel, "status": status if rel == "index.html" else "OK"})
    write_inv()
    with patch(git_files=lambda: set(fs), filesystem_files=lambda: set(fs)): record("audit_full_content_coverage", "baseline", g.gate_full_content_coverage(), False)
    write_inv("A_VALIDAR")
    with patch(git_files=lambda: set(fs), filesystem_files=lambda: set(fs)): record("audit_full_content_coverage", "unsafe_inventory_status", g.gate_full_content_coverage())
    write_inv(files=fs - {"robots.txt"})
    with patch(git_files=lambda: set(fs - {"robots.txt"}), filesystem_files=lambda: set(fs - {"robots.txt"})): record("audit_full_content_coverage", "missing_root_surface", g.gate_full_content_coverage())

    # 8 canonical source scope
    def matrix():
        rows = []
        common = {"url_inicial": URL, "url_final": URL, "dominio": "gov.br", "http_receipt_id": "http-a123", "status_http": "200", "sha256_corpo": H1}
        for uf in g.UFS:
            for cls in g.STATE_CLASSES: rows.append({"jurisdicao": uf, "classe": cls, **common})
        for cls in g.FEDERAL_CLASSES: rows.append({"jurisdicao": "BR", "classe": cls, **common})
        return rows
    goodm = matrix()
    with patch(matrix_rows=lambda: goodm): record("audit_canonical_source_scope", "baseline", g.gate_canonical_source_scope(), False)
    with patch(matrix_rows=lambda: goodm[:-1]): record("audit_canonical_source_scope", "missing_federal_family", g.gate_canonical_source_scope())
    badm = json.loads(json.dumps(goodm)); badm[0]["sha256_corpo"] = ""
    with patch(matrix_rows=lambda: badm): record("audit_canonical_source_scope", "blank_body_hash", g.gate_canonical_source_scope())

    # 9 public set algebra
    surf = {x: "card-visible" if x == "index.html" else "safe" for x in g.SAFE_SURFACE}
    pc = lambda: iter([(ROOT / "data/benefits_crosswalk.json", "$[0]", {"id": "card-visible", "publishable": True})])
    with patch(emitted_surface=lambda: surf, public_cards=pc): record("audit_public_set_algebra", "baseline", g.gate_public_set_algebra(), False)
    with patch(emitted_surface=lambda: {k:v for k,v in surf.items() if k != "robots.txt"}, public_cards=pc): record("audit_public_set_algebra", "missing_surface", g.gate_public_set_algebra())
    badsurf = dict(surf); badsurf["index.html"] += " BLOQUEADO"
    with patch(emitted_surface=lambda: badsurf, public_cards=pc): record("audit_public_set_algebra", "unsafe_status_leak", g.gate_public_set_algebra())

    # 10 quarantine fingerprints
    with patch(git_files=lambda: set(fs), emitted_surface=lambda: surf, quarantine_records=lambda: iter([])): record("audit_quarantine_fingerprints", "baseline", g.gate_quarantine_fingerprints(), False)
    with patch(git_files=lambda: set(fs) | {"data/quarantine.json"}, emitted_surface=lambda: surf, quarantine_records=lambda: iter([])): record("audit_quarantine_fingerprints", "tracked_quarantine_path", g.gate_quarantine_fingerprints())
    qitem = {"id": "quarantine-token-123", "legal_excerpt": "oito palavras materiais muito específicas desta regra tributária isolada agora"}
    leaksurf = dict(surf); leaksurf["index.html"] += " quarantine-token-123"
    with patch(git_files=lambda: set(fs), emitted_surface=lambda: leaksurf, quarantine_records=lambda: iter([(ROOT / "data/benefits_quarantine.json", "$[0]", qitem)])):
        record("audit_quarantine_fingerprints", "token_leak", g.gate_quarantine_fingerprints())

    # 11 subagent independence
    sub = {"native_receipt_status": "AVAILABLE", "negative_access_proof": True}
    for wave in ("wave1", "wave2"):
        sub[wave] = [{"canonical_task_id": f"{wave}-{i}", "fork_turns": "none", "prompt_hash": H1, "session_export": f"s{i}"} for i in range(3)]
    (temp / "subagents_platform_receipts.json").write_text(json.dumps(sub), encoding="utf-8")
    record("audit_subagent_independence", "baseline", g.gate_subagent_independence(), False)
    bad = json.loads(json.dumps(sub)); bad["wave1"] = bad["wave1"][:2]
    (temp / "subagents_platform_receipts.json").write_text(json.dumps(bad), encoding="utf-8")
    record("audit_subagent_independence", "two_tasks_only", g.gate_subagent_independence())
    bad = json.loads(json.dumps(sub)); bad["negative_access_proof"] = False
    (temp / "subagents_platform_receipts.json").write_text(json.dumps(bad), encoding="utf-8")
    record("audit_subagent_independence", "negative_access_missing", g.gate_subagent_independence())

    # 12 publication
    pub = {"pr": "1", "candidate_sha": H1, "ci_run": "1", "ci_conclusion": "success", "merge_sha": H2,
           "pages_run": "2", "pages_conclusion": "success", "production_checked_at": "2026-07-13"}
    (temp / "publication_proof.json").write_text(json.dumps(pub), encoding="utf-8")
    record("audit_publication", "baseline", g.gate_publication(), False)
    bad = dict(pub); bad["ci_conclusion"] = "failure"; (temp / "publication_proof.json").write_text(json.dumps(bad), encoding="utf-8")
    record("audit_publication", "ci_failure", g.gate_publication())
    bad = dict(pub); bad["merge_sha"] = "bad"; (temp / "publication_proof.json").write_text(json.dumps(bad), encoding="utf-8")
    record("audit_publication", "invalid_merge_sha", g.gate_publication())

    # 13 public HTTP hashes
    hp = {"artifacts": [{"status": "200", "http_sha256": H1, "merge_sha256": H1}], "all_public_official_sources_refetched": True}
    (temp / "public_http_hashes.json").write_text(json.dumps(hp), encoding="utf-8")
    record("audit_public_http_hashes", "baseline", g.gate_public_http_hashes(), False)
    bad = json.loads(json.dumps(hp)); bad["artifacts"][0]["merge_sha256"] = H2; (temp / "public_http_hashes.json").write_text(json.dumps(bad), encoding="utf-8")
    record("audit_public_http_hashes", "http_merge_mismatch", g.gate_public_http_hashes())
    bad = json.loads(json.dumps(hp)); bad["all_public_official_sources_refetched"] = False; (temp / "public_http_hashes.json").write_text(json.dumps(bad), encoding="utf-8")
    record("audit_public_http_hashes", "refetch_incomplete", g.gate_public_http_hashes())

    payload = {"temp_root": str(temp), "results": results,
               "summary": {"tests": len(results), "baselines": sum(x["mutant"] == "baseline" for x in results),
                           "mutants": sum(x["mutant"] != "baseline" for x in results),
                           "detected": sum(x["detected"] for x in results),
                           "undetected": sum(not x["detected"] for x in results)}}
    (OUT / "gate_mutation_results_ia.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["summary"], ensure_ascii=False))


if __name__ == "__main__":
    run()
