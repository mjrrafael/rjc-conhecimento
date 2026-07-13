#!/usr/bin/env python3
"""Run every Portal v3 gate and persist complete, hashed logs without early exit."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from portal_v3_gates import RUN  # noqa: E402

PYTHON_GATES = [
    "audit_portal.py",
    "audit_master_coverage.py",
    "audit_benefit_cards.py",
    "audit_card_scope_visible.py",
    "audit_no_keyword_inference.py",
    "audit_temporal_consistency.py",
    "audit_link_health.py",
    "audit_index_freshness.py",
    "audit_quarantine_isolation.py",
    "audit_reforma_transition.py",
    "audit_divergence_html_json_search.py",
    "audit_editorial_date_per_card.py",
    "audit_state_source_quality.py",
    "audit_field_provenance.py",
    "audit_no_synthetic_legal_dates.py",
    "audit_verification_receipts.py",
    "audit_http_platform_receipts.py",
    "audit_link_receipts.py",
    "audit_internalization_evidence.py",
    "audit_full_content_coverage.py",
    "audit_canonical_source_scope.py",
    "audit_public_set_algebra.py",
    "audit_quarantine_fingerprints.py",
    "audit_subagent_independence.py",
    "audit_publication.py",
    "audit_public_http_hashes.py",
    "audit_v3_readiness.py",
]


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def run_command(name: str, command: list[str], timeout: int = 300) -> dict:
    started = datetime.now(ZoneInfo("America/Sao_Paulo"))
    try:
        process = subprocess.run(
            command,
            cwd=ROOT,
            text=False,
            capture_output=True,
            timeout=timeout,
            env={**os.environ, "PYTHONPYCACHEPREFIX": str(Path(os.environ.get("TEMP", str(RUN))) / "rjc-pycache-v3")},
        )
        stdout, stderr, exit_code, timed_out = process.stdout, process.stderr, process.returncode, False
    except subprocess.TimeoutExpired as exc:
        stdout, stderr, exit_code, timed_out = exc.stdout or b"", exc.stderr or b"", 124, True
    finished = datetime.now(ZoneInfo("America/Sao_Paulo"))
    body = (
        f"command={json.dumps(command, ensure_ascii=False)}\n"
        f"started_at={started.isoformat()}\nfinished_at={finished.isoformat()}\n"
        f"exit_code={exit_code}\ntimed_out={str(timed_out).lower()}\n\n[stdout]\n"
    ).encode("utf-8") + stdout + b"\n\n[stderr]\n" + stderr
    log_dir = RUN / "gate_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{name}.log"
    log_path.write_bytes(body)
    return {
        "name": name,
        "command": command,
        "started_at": started.isoformat(),
        "finished_at": finished.isoformat(),
        "exit_code": exit_code,
        "timed_out": timed_out,
        "log": log_path.relative_to(ROOT).as_posix(),
        "log_sha256": sha256(body),
        "stdout_sha256": sha256(stdout),
        "stderr_sha256": sha256(stderr),
    }


def main() -> int:
    results = [run_command("compileall", [sys.executable, "-m", "compileall", "-q", "scripts"])]
    for gate in PYTHON_GATES:
        results.append(run_command(Path(gate).stem, [sys.executable, "-B", f"scripts/{gate}"]))
    with tempfile.TemporaryDirectory(prefix="rjc-safe-pages-") as temp:
        site = Path(temp)
        for rel in ("index.html", "404.html", "robots.txt", "llms.txt"):
            shutil.copy2(ROOT / rel, site / rel)
        results.extend([
            run_command("safe_pages_projection", [sys.executable, "-B", "scripts/audit_safe_pages_projection.py", str(site)]),
            run_command("safe_pages_mutants", [sys.executable, "-B", "scripts/test_safe_pages_projection_gate.py", str(site)]),
        ])
    results.extend([
        run_command("validated_benefits_mutants", [sys.executable, "-B", "scripts/test_validated_benefits_fail_closed.py"]),
        run_command("git_diff_check", ["git", "diff", "--check"]),
        run_command("git_lfs_inventory", ["git", "lfs", "ls-files"]),
    ])
    payload = {
        "schema": "rjc-gate-run-ledger-v3",
        "run": RUN.relative_to(ROOT).as_posix(),
        "completed_at": datetime.now(ZoneInfo("America/Sao_Paulo")).isoformat(),
        "results": results,
        "summary": {
            "total": len(results),
            "passed": sum(item["exit_code"] == 0 for item in results),
            "failed": sum(item["exit_code"] != 0 for item in results),
            "timed_out": sum(item["timed_out"] for item in results),
        },
    }
    (RUN / "gate_runs.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["summary"], ensure_ascii=False))
    return 0 if payload["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
