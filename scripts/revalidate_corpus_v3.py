#!/usr/bin/env python3
"""Fail-closed revalidation ledger for the RJC tax-card corpus.

This program never promotes a legacy record.  It rebuilds a decision ledger
for every card and quarantine item, detects inherited legal dates, and can
capture each referenced official URL anonymously.  Local captures are
explicitly labelled non-native, so they are useful evidence for remediation
but are insufficient to publish a legal rule.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import csv
import hashlib
import json
import mimetypes
import re
import ssl
import sys
import unicodedata
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
CROSSWALK = ROOT / "data" / "benefits_crosswalk.json"
QUARANTINE = ROOT / "data" / "benefits_quarantine.json"
DEFAULT_RUN = ROOT / "auditoria" / "execucoes" / "revalidacao-corpus-2026-07-16"
LEGAL_DATE_FIELDS = ("publicacao", "inicio_vigencia", "inicio_eficacia", "fim_vigencia")
MAX_HTTP_BODY_BYTES = 80 * 1024 * 1024
BENEFIT_RE = re.compile(
    r"\b(isencao|reducao de base|credito (?:presumido|outorgado)|diferimento|suspensao|aliquota zero|nao incidencia|imunidade|beneficio fiscal|incentivo fiscal)\b",
    re.I,
)


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def json_hash(value: object) -> str:
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def normalize(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = text.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", text)).strip()


def read_entries(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("entries") if isinstance(payload, dict) else None
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise ValueError(f"{path} não contém entries válidos")
    return rows


def inherited_dates(card: dict) -> list[str]:
    captured = str(card.get("captured_on") or "").strip()
    suspicious: list[str] = []
    for field in LEGAL_DATE_FIELDS:
        value = card.get(field)
        if value not in (None, "", "AUSENTE", "INDETERMINADO", "NÃO_APLICÁVEL") and str(value) == captured:
            suspicious.append(field)
    return suspicious


def crosswalk_decision(card: dict) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if not isinstance(card.get("field_provenance"), dict):
        reasons.append("field_provenance_ausente")
    if not card.get("verification_receipt_id"):
        reasons.append("recibo_de_verificacao_ausente")
    inherited = inherited_dates(card)
    if inherited:
        reasons.append("datas_juridicas_herdadas_da_captura:" + ",".join(inherited))
    if str(card.get("tax") or "").upper() == "ICMS":
        internalization = str(card.get("internalization") or "").upper()
        if internalization not in {"COMPROVADA", "DISPENSADA_COM_FUNDAMENTO"}:
            reasons.append("internalizacao_nao_comprovada")
        elif not isinstance(card.get("internalization_evidence"), dict):
            reasons.append("evidencia_de_internalizacao_ausente")
    if float(card.get("classification_confidence") or 0) < 0.80:
        reasons.append("confianca_inferior_a_080")
    if reasons:
        return "QUARENTENA_NAO_PUBLICA", reasons
    # This branch is intentionally terminal but still non-promotional until
    # native receipts and independent review are established by another gate.
    return "QUARENTENA_AGUARDANDO_REVISAO_INDEPENDENTE", ["promocao_exige_recibos_nativos_e_onda_independente"]


def quarantine_decision(item: dict) -> tuple[str, list[str]]:
    excerpt = normalize(item.get("legal_excerpt"))
    if not BENEFIT_RE.search(excerpt):
        return "DESCARTAR_NAO_BENEFICIO", ["sem_efeito_favorecido_literal_no_trecho"]
    return "QUARENTENA_REVALIDAR_BENEFICIO", ["potencial_beneficio_sem_prova_por_campo"]


def receipt_id(url: str) -> str:
    return "local-http-v3-" + sha256(url.encode("utf-8"))[:20]


def validate_capture_url(url: str) -> None:
    """Reject malformed and local-only targets before issuing a request."""

    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("esquema de URL não permitido")
    if not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("URL oficial sem host público válido")
    hostname = parsed.hostname.casefold()
    if hostname in {"localhost", "localhost.localdomain", "0.0.0.0", "::1"} or hostname.startswith("127."):
        raise ValueError("destino local não permitido")


class RedirectRecorder(urllib.request.HTTPRedirectHandler):
    """Preserve every redirect observed by urllib in the local receipt."""

    def __init__(self) -> None:
        super().__init__()
        self.redirects: list[dict[str, object]] = []

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        validate_capture_url(newurl)
        self.redirects.append({"from": req.full_url, "to": newurl, "status": int(code)})
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_one(url: str, raw_dir: Path, timeout: int, archive_bodies: bool) -> dict:
    started = now_iso()
    result: dict[str, object] = {
        "receipt_id": receipt_id(url),
        "receipt_kind": "LOCAL_REPRODUCIBLE_NOT_PLATFORM_NATIVE",
        "captured_at": started,
        "request": {
            "url": url,
            "method": "GET",
            "headers": {
                "User-Agent": "RJC-Corpus-Revalidator/3.0 (+https://mjrrafael.github.io/rjc-conhecimento/)",
                "Accept": "text/html,application/pdf,text/plain,application/xhtml+xml,*/*;q=0.5",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
            },
            "cookies": None,
            "authorization": None,
        },
        "redirects": [], "status": 0, "final_url": "", "response_headers": {},
        "mime": "", "bytes": 0, "body_sha256": "", "body_path": "", "error": "",
    }
    try:
        validate_capture_url(url)
        request = urllib.request.Request(url, headers=result["request"]["headers"], method="GET")
        redirects = RedirectRecorder()
        opener = urllib.request.build_opener(redirects, urllib.request.HTTPSHandler(context=ssl.create_default_context()))
        with opener.open(request, timeout=timeout) as response:
            raw = response.read(MAX_HTTP_BODY_BYTES + 1)
            if len(raw) > MAX_HTTP_BODY_BYTES:
                raise ValueError(f"corpo excede limite de {MAX_HTTP_BODY_BYTES} bytes")
            final_url = response.geturl()
            validate_capture_url(final_url)
            headers = {key.lower(): value for key, value in response.headers.items()}
            body_path = ""
            if archive_bodies:
                raw_dir.mkdir(parents=True, exist_ok=True)
                target = raw_dir / f"{sha256(url.encode('utf-8'))}.body"
                target.write_bytes(raw)
                body_path = target.relative_to(ROOT).as_posix()
            result.update(
                status=int(getattr(response, "status", 200)),
                final_url=final_url,
                redirects=redirects.redirects,
                response_headers=headers,
                mime=response.headers.get_content_type() or mimetypes.guess_type(final_url)[0] or "application/octet-stream",
                bytes=len(raw), body_sha256=sha256(raw), body_path=body_path,
            )
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        result.update(status=exc.code, final_url=exc.geturl(), bytes=len(raw), body_sha256=sha256(raw) if raw else "", error=f"HTTPError: {exc.reason}")
    except Exception as exc:  # intentionally material: every failed source remains non-public
        result["error"] = f"{type(exc).__name__}: {exc}"
    result["finished_at"] = now_iso()
    return result


def local_source_evidence(row: dict, cache: dict[str, tuple[str, str, str] | None]) -> tuple[bool, bool, bool, bool]:
    """Return path-present, recorded-hash-match and literal-excerpt-match.

    A local textual match is useful to locate a card in the captured source,
    but does not repair the legal-date or native-receipt deficits.
    """
    rel = str(row.get("source_path") or "")
    if rel not in cache:
        path = ROOT / rel
        if not rel or not path.is_file():
            cache[rel] = None
        else:
            raw = path.read_bytes()
            text = raw.decode("utf-8", errors="ignore")
            cache[rel] = (sha256(raw), text, normalize(text))
    stored = cache[rel]
    if stored is None:
        return False, False, False, False
    source_hash, source_text, normalized_source = stored
    excerpt = str(row.get("legal_excerpt") or "")
    normalized_excerpt = normalize(excerpt)
    literal_match = bool(excerpt and excerpt in source_text)
    normalized_match = bool(normalized_excerpt and normalized_excerpt in normalized_source)
    boundary_match = bool(
        len(normalized_excerpt) >= 160
        and normalized_excerpt[:120] in normalized_source
        and normalized_excerpt[-120:] in normalized_source
    )
    recorded_hash = str(row.get("sha256") or "").casefold()
    hash_known = bool(re.fullmatch(r"[0-9a-f]{64}", recorded_hash))
    return True, hash_known, source_hash == recorded_hash if hash_known else False, literal_match or normalized_match or boundary_match


def write_ledger(path: Path, cards: list[dict], quarantine: list[dict], receipts: dict[str, dict]) -> tuple[Counter, Counter]:
    counts: Counter = Counter()
    evidence_counts: Counter = Counter()
    seen: set[str] = set()
    source_cache: dict[str, tuple[str, str, str] | None] = {}
    with path.open("w", encoding="utf-8", newline="") as handle:
        fields = (
            "record_kind", "record_id", "input_sha256", "jurisdiction", "tax", "official_url", "source_file",
            "receipt_id", "http_status", "source_path_exists", "source_hash_known", "source_hash_match", "excerpt_local_match", "decision", "reasons",
        )
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for kind, rows in (("crosswalk", cards), ("quarantine", quarantine)):
            for row in rows:
                record_id = str(row.get("id") or "")
                if not record_id or record_id in seen:
                    raise ValueError(f"ID ausente ou duplicado: {record_id!r}")
                seen.add(record_id)
                decision, reasons = crosswalk_decision(row) if kind == "crosswalk" else quarantine_decision(row)
                url = str(row.get("official_url") or "")
                receipt = receipts.get(url, {})
                source_exists, source_hash_known, source_hash_match, excerpt_match = local_source_evidence(row, source_cache)
                evidence_counts["source_path_exists" if source_exists else "source_path_missing"] += 1
                if source_hash_known:
                    evidence_counts["source_hash_match" if source_hash_match else "source_hash_mismatch"] += 1
                else:
                    evidence_counts["source_hash_not_supplied"] += 1
                evidence_counts["excerpt_local_match" if excerpt_match else "excerpt_local_mismatch"] += 1
                if not source_exists:
                    reasons.append("arquivo_fonte_local_ausente")
                elif source_hash_known and not source_hash_match:
                    reasons.append("hash_da_fonte_local_diverge_do_registro")
                elif not source_hash_known:
                    reasons.append("hash_da_fonte_local_nao_fornecido_no_registro")
                if not excerpt_match:
                    reasons.append("trecho_nao_localizado_na_fonte_local")
                if url and receipt and int(receipt.get("status") or 0) != 200:
                    reasons.append("fonte_oficial_nao_confirmada_http200")
                if url and not receipt:
                    reasons.append("fonte_ainda_nao_recapturada")
                writer.writerow({
                    "record_kind": kind, "record_id": record_id, "input_sha256": json_hash(row),
                    "jurisdiction": row.get("jurisdiction", ""), "tax": row.get("tax", ""),
                    "official_url": url, "source_file": row.get("source_file", ""),
                    "receipt_id": receipt.get("receipt_id", ""), "http_status": receipt.get("status", ""),
                    "source_path_exists": source_exists, "source_hash_known": source_hash_known,
                    "source_hash_match": source_hash_match,
                    "excerpt_local_match": excerpt_match, "decision": decision,
                    "reasons": "|".join(sorted(set(reasons))),
                })
                counts[decision] += 1
    return counts, evidence_counts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--fetch", action="store_true", help="recaptura URLs oficiais anonimamente")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--no-archive-bodies", action="store_true")
    args = parser.parse_args()
    if args.workers < 1 or args.workers > 8:
        raise SystemExit("--workers deve estar entre 1 e 8")
    cards, quarantine = read_entries(CROSSWALK), read_entries(QUARANTINE)
    args.run_dir.mkdir(parents=True, exist_ok=True)
    urls = sorted({str(row.get("official_url") or "") for row in cards + quarantine if row.get("official_url")})
    receipts: dict[str, dict] = {}
    if args.fetch:
        raw_dir = args.run_dir / "raw_http"
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {pool.submit(fetch_one, url, raw_dir, args.timeout, not args.no_archive_bodies): url for url in urls}
            for future in concurrent.futures.as_completed(futures):
                url = futures[future]
                try:
                    receipts[url] = future.result()
                except Exception as exc:  # defensive, should be represented as an individual failed receipt
                    receipts[url] = {"receipt_id": receipt_id(url), "status": 0, "error": f"worker: {type(exc).__name__}: {exc}"}
        payload = {"schema": "rjc-local-http-receipts-v3", "native_platform_receipts": False, "receipts": [receipts[url] for url in urls]}
        (args.run_dir / "http_local_receipts.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        receipt_path = args.run_dir / "http_local_receipts.json"
        if receipt_path.exists():
            saved = json.loads(receipt_path.read_text(encoding="utf-8"))
            for receipt in saved.get("receipts", []) if isinstance(saved, dict) else []:
                request = receipt.get("request", {}) if isinstance(receipt, dict) else {}
                url = str(request.get("url") or "") if isinstance(request, dict) else ""
                if url:
                    receipts[url] = receipt
    counts, evidence_counts = write_ledger(args.run_dir / "ledger_cards.csv", cards, quarantine, receipts)
    summary = {
        "schema": "rjc-corpus-revalidation-v3", "generated_at": now_iso(),
        "input": {"crosswalk": len(cards), "quarantine": len(quarantine), "total": len(cards) + len(quarantine), "official_urls": len(urls)},
        "decisions": dict(sorted(counts.items())),
        "local_source_evidence": dict(sorted(evidence_counts.items())),
        "http": {"recaptured": len(receipts), "http_200": sum(1 for receipt in receipts.values() if receipt.get("status") == 200), "receipt_kind": "LOCAL_REPRODUCIBLE_NOT_PLATFORM_NATIVE" if receipts else "NOT_CAPTURED"},
        "publication": "BLOQUEADA: nenhuma decisão deste executor promove conteúdo público",
    }
    (args.run_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
