from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

CANDIDATE = "074bff85c7c560386ca0ed7f0802d4e896534571"
ROOT = Path(r"C:\Users\rafae\Documents\Codex\2026-06-14\pesquisa-na-mem-ria-profunda-l\worktrees\rjc-monitor-2026-07-13-wave2-ia")
OUT = Path(r"C:\Users\rafae\AppData\Local\Temp\rjc-monitor-2026-07-13-wave2\ia")
PATHS = ["data", "assets", "scripts", ".github", "_config.yml", "index.html", "404.html", "robots.txt", "llms.txt"]


def tree_rows() -> list[dict]:
    raw = subprocess.check_output(
        ["git", "ls-tree", "-r", "-l", "-z", CANDIDATE, "--", *PATHS], cwd=ROOT
    )
    rows = []
    for entry in raw.split(b"\0"):
        if not entry:
            continue
        meta, path_raw = entry.split(b"\t", 1)
        mode, kind, blob, size = meta.decode("ascii").split()
        rows.append({"mode": mode, "kind": kind, "blob": blob, "git_size": int(size), "path": path_raw.decode("utf-8")})
    return rows


def canonical(raw: bytes) -> bytes:
    return raw if b"\0" in raw else raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def classify(path: str) -> str:
    if path.startswith("data/"):
        return "data"
    if path.startswith("assets/"):
        return "assets"
    if path.startswith("scripts/"):
        return "scripts"
    if path.startswith(".github/"):
        return "github"
    return "root_surface"


def extension(path: str) -> str:
    return Path(path).suffix.lower() or "[none]"


def duplicate_hook(counter: Counter):
    def hook(pairs):
        obj = {}
        for key, value in pairs:
            if key in obj:
                counter[key] += 1
            obj[key] = value
        return obj
    return hook


def walk(value, counters: dict, depth: int = 0):
    counters["max_depth"] = max(counters["max_depth"], depth)
    if isinstance(value, dict):
        counters["dicts"] += 1
        counters["keys"].update(value.keys())
        for key, child in value.items():
            if key == "publishable":
                counters["publishable"][str(child)] += 1
            if key in {"status", "validation_status", "audience_status", "validity_status", "internalization_status", "internalizacao_status"}:
                counters["statuses"][str(child)] += 1
            if key in {"id", "source_id"} and child not in (None, ""):
                counters["ids"].append(str(child))
            if key in {"official_url", "url", "final_url", "url_final"} and isinstance(child, str) and child.startswith(("http://", "https://")):
                counters["urls"].append(child)
            if key in {"field_provenance", "verification_receipt_id", "independent_http_receipt_ids", "internalization_evidence", "internalizacao_evidencia", "source_fingerprint"}:
                counters["proof_fields"][key] += 1
            walk(child, counters, depth + 1)
    elif isinstance(value, list):
        counters["lists"] += 1
        counters["list_items"] += len(value)
        for child in value:
            walk(child, counters, depth + 1)
    elif isinstance(value, str):
        counters["strings"] += 1
        counters["string_chars"] += len(value)
    elif value is None:
        counters["nulls"] += 1
    else:
        counters["scalars"] += 1


def new_counts():
    return {
        "dicts": 0, "lists": 0, "list_items": 0, "strings": 0, "string_chars": 0,
        "nulls": 0, "scalars": 0, "max_depth": 0, "keys": Counter(),
        "publishable": Counter(), "statuses": Counter(), "ids": [], "urls": [],
        "proof_fields": Counter(),
    }


def known_collection(payload):
    if not isinstance(payload, dict):
        return None, payload if isinstance(payload, list) else None
    for key in ("entries", "rows", "records", "documents", "sources", "ufs", "states", "products", "chapters"):
        if isinstance(payload.get(key), list):
            return key, payload[key]
    return None, None


def scan_structured(rows: list[dict]) -> tuple[list[dict], dict]:
    profiles = []
    global_result = {
        "parse_errors": [], "duplicate_json_keys": {}, "publishable": Counter(),
        "statuses": Counter(), "proof_fields": Counter(), "ids_total": 0,
        "ids_duplicate_occurrences": 0, "urls_total": 0,
    }
    for row in rows:
        rel = row["path"]
        suffix = Path(rel).suffix.lower()
        if suffix not in {".json", ".ndjson"}:
            continue
        p = ROOT / rel
        duplicate_keys = Counter()
        counts = new_counts()
        root_type = ""
        collection = None
        collection_count = None
        nonblank_lines = None
        try:
            if suffix == ".json":
                payload = json.loads(p.read_text(encoding="utf-8"), object_pairs_hook=duplicate_hook(duplicate_keys))
                root_type = type(payload).__name__
                collection, items = known_collection(payload)
                collection_count = len(items) if isinstance(items, list) else None
                walk(payload, counts)
                if rel == "assets/build-freshness.json":
                    pass
            else:
                nonblank_lines = 0
                payload = []
                with p.open(encoding="utf-8") as handle:
                    for line_no, line in enumerate(handle, 1):
                        if not line.strip():
                            continue
                        nonblank_lines += 1
                        item = json.loads(line, object_pairs_hook=duplicate_hook(duplicate_keys))
                        walk(item, counts)
                root_type = "ndjson"
                collection = "lines"
                collection_count = nonblank_lines
        except Exception as exc:
            global_result["parse_errors"].append({"path": rel, "error": f"{type(exc).__name__}: {exc}"})
        id_counts = Counter(counts["ids"])
        dup_ids = sum(value - 1 for value in id_counts.values() if value > 1)
        profiles.append({
            "path": rel, "format": suffix.lstrip("."), "root_type": root_type,
            "collection": collection or "", "collection_count": collection_count if collection_count is not None else "",
            "nonblank_lines": nonblank_lines if nonblank_lines is not None else "",
            "dicts": counts["dicts"], "lists": counts["lists"], "list_items": counts["list_items"],
            "strings": counts["strings"], "string_chars": counts["string_chars"], "max_depth": counts["max_depth"],
            "ids": len(counts["ids"]), "duplicate_id_occurrences": dup_ids,
            "urls": len(counts["urls"]), "duplicate_key_occurrences": sum(duplicate_keys.values()),
            "parse_status": "OK" if not any(e["path"] == rel for e in global_result["parse_errors"]) else "FAIL",
        })
        if duplicate_keys:
            global_result["duplicate_json_keys"][rel] = dict(duplicate_keys)
        global_result["publishable"].update(counts["publishable"])
        global_result["statuses"].update(counts["statuses"])
        global_result["proof_fields"].update(counts["proof_fields"])
        global_result["ids_total"] += len(counts["ids"])
        global_result["ids_duplicate_occurrences"] += dup_ids
        global_result["urls_total"] += len(counts["urls"])
    for key in ("publishable", "statuses", "proof_fields"):
        global_result[key] = dict(global_result[key])
    return profiles, global_result


def load(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def semantic_checks(tree: list[dict]) -> dict:
    checks = {}
    benefits = load("data/benefits_crosswalk.json")
    entries = benefits["entries"]
    quarantine = load("data/benefits_quarantine.json")
    qentries = quarantine["entries"]
    ncm = load("data/ncm_benefits_index.json")
    ncm_rows = ncm["rows"]
    pis = load("data/pis-cofins/ncm-index.json")
    pis_rows = pis["records"]
    search_full = load("assets/portal-search-full.json")
    manifest = load("assets/llm-manifest.json")
    freshness = load("assets/build-freshness.json")
    tree_map = {row["path"]: row for row in tree}

    def count_field(rows, key, predicate=lambda x: bool(x)):
        return sum(1 for item in rows if predicate(item.get(key)))

    checks["benefits"] = {
        "entries": len(entries), "summary_entries": benefits.get("summary", {}).get("entries"),
        "unique_ids": len({str(x.get("id")) for x in entries}),
        "publishable_true": count_field(entries, "publishable", lambda x: x is True),
        "field_provenance_present": count_field(entries, "field_provenance"),
        "verification_receipt_id_present": count_field(entries, "verification_receipt_id"),
        "independent_http_receipt_ids_two_plus": count_field(entries, "independent_http_receipt_ids", lambda x: isinstance(x, list) and len(set(map(str, x))) >= 2),
        "internalization_evidence_present": sum(1 for x in entries if x.get("internalization_evidence") or x.get("internalizacao_evidencia")),
        "publication_equals_capture": sum(1 for x in entries if x.get("publicacao") and x.get("publicacao") == x.get("captured_on")),
        "validity_start_equals_capture": sum(1 for x in entries if x.get("validity_start") and x.get("validity_start") == x.get("captured_on")),
        "inicio_vigencia_equals_capture": sum(1 for x in entries if x.get("inicio_vigencia") and x.get("inicio_vigencia") == x.get("captured_on")),
        "internalizado_uf_true": sum(1 for x in entries if isinstance(x.get("prova_documental"), dict) and x["prova_documental"].get("internalizado_uf") is True),
        "unsafe_states": dict(Counter(str(x.get("status")) for x in entries)),
    }
    checks["quarantine"] = {
        "entries": len(qentries), "summary_entries": quarantine.get("summary", {}).get("entries"),
        "unique_ids": len({str(x.get("id")) for x in qentries}),
        "source_fingerprint_present": count_field(qentries, "source_fingerprint"),
        "sha256_present": count_field(qentries, "sha256"),
        "source_files": len({str(x.get("source_file")) for x in qentries}),
        "audience_status": dict(Counter(str(x.get("audience_status")) for x in qentries)),
        "validation_status": dict(Counter(str(x.get("validation_status")) for x in qentries)),
    }
    checks["ncm"] = {
        "rows": len(ncm_rows), "summary_rows": ncm.get("summary", {}).get("rows"),
        "unique_ids": len({str(x.get("id")) for x in ncm_rows}),
        "unique_ncm_rederived": len({str(x.get("ncm_digits")) for x in ncm_rows}),
        "summary_unique_ncm": ncm.get("summary", {}).get("unique_ncm"),
        "jurisdictions_rederived": len({str(x.get("jurisdiction")) for x in ncm_rows}),
        "summary_jurisdictions": ncm.get("summary", {}).get("jurisdictions"),
        "bad_ncm_digits": sum(1 for x in ncm_rows if not re.fullmatch(r"\d{4}|\d{6}|\d{8}", str(x.get("ncm_digits", "")))),
    }
    checks["pis_cofins"] = {
        "records": len(pis_rows), "summary_published_rows": pis.get("summary", {}).get("published_rows"),
        "unique_ids": len({str(x.get("id")) for x in pis_rows}),
    }
    manifest_paths = [str(x.get("path")) for x in manifest]
    manifest_urls = [str(x.get("url")) for x in manifest]
    search_urls = [str(x.get("url")) for x in search_full]
    js_raw = (ROOT / "assets/portal-search.js").read_text(encoding="utf-8").strip()
    prefix = "window.RJC_SEARCH = "
    js_entries = json.loads(js_raw[len(prefix):].rstrip(";")) if js_raw.startswith(prefix) else []
    checks["search_manifest"] = {
        "manifest_rows": len(manifest), "manifest_unique_paths": len(set(manifest_paths)),
        "manifest_unique_urls": len(set(manifest_urls)), "manifest_bad_base_urls": sum(1 for x in manifest_urls if not x.startswith("https://mjrrafael.github.io/rjc-conhecimento/")),
        "search_full_rows": len(search_full), "search_full_unique_urls": len(set(search_urls)),
        "search_js_rows": len(js_entries), "search_js_unique_urls": len({str(x.get("url")) for x in js_entries}),
        "manifest_urls_absent_from_search_full": len(set(manifest_urls) - set(search_urls)),
        "search_full_urls_absent_from_manifest": len(set(search_urls) - set(manifest_urls)),
        "duplicate_search_full_url_occurrences": len(search_urls) - len(set(search_urls)),
    }
    stale = []
    for rel, item in freshness.get("artifacts", {}).items():
        tree_item = tree_map.get(rel)
        if tree_item:
            raw = (ROOT / rel).read_bytes()
            actual_hash = hashlib.sha256(canonical(raw)).hexdigest()
            actual_bytes = tree_item["git_size"]
            match = actual_hash == item.get("sha256") and actual_bytes == item.get("bytes")
            if not match:
                stale.append({"path": rel, "declared_sha256": item.get("sha256"), "actual_sha256": actual_hash, "declared_bytes": item.get("bytes"), "actual_bytes": actual_bytes})
        else:
            stale.append({"path": rel, "reason": "fora do universo local autorizado/não presente no ls-tree permitido", "declared_sha256": item.get("sha256"), "declared_bytes": item.get("bytes")})
    checks["freshness"] = {
        "generated_at": freshness.get("generated_at"), "artifact_count": len(freshness.get("artifacts", {})),
        "mismatch_or_unverifiable_count": len(stale), "details": stale,
    }
    ufs = set("AC AL AM AP BA CE DF ES GO MA MG MS MT PA PB PE PI PR RJ RN RO RR RS SC SE SP TO".split())
    registry = load("data/corpus-local/legal_sources_registry.json")
    sealing = load("data/corpus-local/uf-sealing-plan.json")
    coverage = load("data/master_source_coverage.json")
    catalog = load("data/portal_catalog.json")
    source_audit = load("data/state_source_audit.json")
    curadoria = load("data/state_curadoria.json")
    checks["uf_sets"] = {
        "fixed_count": len(ufs),
        "registry_ufs_missing": sorted(ufs - {str(x.get("uf")) for x in registry.get("entries", [])}),
        "sealing_ufs_missing": sorted(ufs - {str(x.get("uf")) for x in sealing.get("ufs", [])}),
        "coverage_ufs_missing": sorted(ufs - {str(x.get("uf")) for x in coverage.get("states", [])}),
        "catalog_ufs_missing": sorted(ufs - {str(x.get("uf")) for x in catalog.get("states", [])}),
        "source_audit_ufs_missing": sorted(ufs - set(source_audit.get("states", {}))),
        "curadoria_ufs_missing": sorted(ufs - set(curadoria.get("statuses", {}))),
    }
    return checks


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    tree = tree_rows()
    inv = []
    for row in tree:
        raw = (ROOT / row["path"]).read_bytes()
        canon = canonical(raw)
        inv.append({
            "path": row["path"], "surface": classify(row["path"]), "extension": extension(row["path"]),
            "git_mode": row["mode"], "git_blob": row["blob"], "git_size": row["git_size"],
            "worktree_size": len(raw), "sha256_canonical": hashlib.sha256(canon).hexdigest(),
            "present": True, "status": "OK" if len(canon) == row["git_size"] else "OK_CRLF_NORMALIZED",
        })
    profiles, global_result = scan_structured(tree)
    checks = semantic_checks(tree)
    result = {
        "candidate": CANDIDATE,
        "inventory_count": len(inv),
        "inventory_bytes_git": sum(x["git_size"] for x in inv),
        "inventory_by_surface": dict(Counter(x["surface"] for x in inv)),
        "inventory_by_extension": dict(Counter(x["extension"] for x in inv)),
        "structured_profiles": profiles,
        "structured_global": global_result,
        "semantic_checks": checks,
    }
    (OUT / "scan_results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (OUT / "inventario.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(inv[0]))
        writer.writeheader(); writer.writerows(inv)
    print(json.dumps({
        "inventory": len(inv), "bytes": result["inventory_bytes_git"],
        "json_ndjson": len(profiles), "parse_errors": len(global_result["parse_errors"]),
        "duplicate_key_files": len(global_result["duplicate_json_keys"]),
        "publishable": global_result["publishable"],
        "proof_fields": global_result["proof_fields"],
        "benefits": checks["benefits"], "quarantine": checks["quarantine"],
        "freshness_mismatch": checks["freshness"]["mismatch_or_unverifiable_count"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
