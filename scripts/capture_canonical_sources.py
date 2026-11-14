#!/usr/bin/env python3
"""Capture the institutional source matrix with reproducible, cookie-free receipts.

This collector deliberately does *not* grant publication approval. It records the
raw response and metadata needed for the next legal-reading/refetch phase. Native
platform call receipts and independent refetches remain separate requirements.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MATRIX = ROOT / "auditoria" / "execucoes" / "reconstrucao-provas-2026-07-16" / "matriz_fontes_canonicas.csv"
DEFAULT_OUTPUT = ROOT / "auditoria" / "execucoes" / "reconstrucao-provas-2026-07-16"
LOCK = threading.Lock()


class RedirectTrace(HTTPRedirectHandler):
    def __init__(self) -> None:
        super().__init__()
        self.chain: list[dict[str, Any]] = []

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        self.chain.append({
            "from_url": req.full_url,
            "to_url": newurl,
            "status": code,
            "location": headers.get("Location", ""),
        })
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def header_dict(headers: Any) -> dict[str, str]:
    return {str(key): str(value) for key, value in headers.items()}


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value)


def capture(row: dict[str, str], evidence_root: Path, max_bytes: int, timeout: int) -> dict[str, Any]:
    captured_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    receipt_id = f"local-{safe_name(row['source_id'])}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}"
    trace = RedirectTrace()
    # No HTTPCookieProcessor is configured. Each source opens a new, stateless opener.
    opener = build_opener(trace)
    request_headers = {
        "Accept": "text/html,application/xhtml+xml,application/pdf,application/json;q=0.9,*/*;q=0.1",
        "User-Agent": "RJC-Portal-Proof-Research/1.0 (anonymous, no-cookie)",
    }
    req = Request(row["url_inicial"], headers=request_headers, method="GET")
    receipt: dict[str, Any] = {
        "receipt_id": receipt_id,
        "receipt_class": "LOCAL_REPRODUCIBLE_NOT_PLATFORM_NATIVE",
        "source_id": row["source_id"],
        "captured_at": captured_at,
        "request": {"url": row["url_inicial"], "method": "GET", "headers": request_headers, "cookies": "none"},
        "redirect_chain": trace.chain,
        "response": {},
        "body": {},
        "result": "ERRO_DE_CAPTURA",
        "publication_authorization": "NAO",
    }
    try:
        with opener.open(req, timeout=timeout) as response:
            body = response.read(max_bytes + 1)
            response_headers = header_dict(response.headers)
            receipt["response"] = {
                "url_final": response.geturl(),
                "status": getattr(response, "status", response.getcode()),
                "headers": response_headers,
                "mime": response_headers.get("Content-Type", "").split(";", 1)[0].lower(),
            }
            if len(body) > max_bytes:
                receipt["result"] = "CORPO_EXCEDE_LIMITE_NAO_ARQUIVADO"
                receipt["body"] = {"bytes_lidos": len(body), "limite": max_bytes}
            else:
                digest = hashlib.sha256(body).hexdigest()
                body_path = evidence_root / "bodies" / f"{safe_name(row['source_id'])}-{digest}.bin"
                body_path.parent.mkdir(parents=True, exist_ok=True)
                body_path.write_bytes(body)
                receipt["body"] = {
                    "bytes": len(body),
                    "sha256": digest,
                    "path_externo": str(body_path),
                }
                receipt["result"] = "CAPTURADA_PENDENTE_DE_LEITURA_E_REFETCH"
    except HTTPError as exc:
        receipt["response"] = {
            "url_final": exc.geturl(),
            "status": exc.code,
            "headers": header_dict(exc.headers),
            "mime": exc.headers.get_content_type() if exc.headers else "",
        }
        receipt["result"] = "HTTP_ERROR"
    except (URLError, TimeoutError, OSError) as exc:
        receipt["error"] = f"{type(exc).__name__}: {exc}"
        receipt["result"] = "ERRO_DE_REDE"
    except Exception as exc:  # receipt must survive an unexpected source behavior
        receipt["error"] = f"{type(exc).__name__}: {exc}"
        receipt["result"] = "ERRO_INESPERADO"
    receipt["redirect_chain"] = trace.chain
    return receipt


def receipt_to_matrix(row: dict[str, str], receipt: dict[str, Any]) -> dict[str, str]:
    result = dict(row)
    response = receipt.get("response", {})
    body = receipt.get("body", {})
    result["url_final"] = str(response.get("url_final", ""))
    result["status_http"] = str(response.get("status", ""))
    result["sha256_corpo"] = str(body.get("sha256", ""))
    result["receipt_id"] = receipt["receipt_id"]
    result["status_prova"] = (
        "CAPTURA_LOCAL_PENDENTE_DE_LEITURA_E_REFETCH"
        if receipt["result"] == "CAPTURADA_PENDENTE_DE_LEITURA_E_REFETCH"
        else f"CAPTURA_FALHOU_{receipt['result']}"
    )
    return result


def is_outside_repo(path: Path) -> bool:
    try:
        path.resolve().relative_to(ROOT.resolve())
    except ValueError:
        return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--max-bytes", type=int, default=25 * 1024 * 1024)
    parser.add_argument("--source-id", action="append", default=[], help="Recaptura somente as fontes indicadas; preserva tentativas anteriores.")
    args = parser.parse_args()
    if not is_outside_repo(args.evidence_root):
        raise SystemExit("--evidence-root deve ficar fora do repositório para não publicar corpos brutos.")
    with args.matrix.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    state_rows = [row for row in rows if row.get("jurisdicao") != "BR"]
    required_state_ids = {
        f"{uf}::{source_class}"
        for uf in ("AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO")
        for source_class in ("SEFAZ_LEGISLACAO", "DOE", "ASSEMBLEIA_LEGISLATIVA")
    }
    actual_state_ids = {row["source_id"] for row in state_rows}
    if actual_state_ids != required_state_ids or len(rows) < 95:
        raise SystemExit("Matriz inesperada: exige as 81 linhas estaduais e ao menos 14 famílias federais.")
    if args.source_id:
        requested = set(args.source_id)
        known = {row["source_id"] for row in rows}
        unknown = requested - known
        if unknown:
            raise SystemExit(f"Fonte(s) não encontrada(s) na matriz: {sorted(unknown)}")
        rows = [row for row in rows if row["source_id"] in requested]
    args.evidence_root.mkdir(parents=True, exist_ok=True)
    receipts: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = {pool.submit(capture, row, args.evidence_root, args.max_bytes, args.timeout): row for row in rows}
        for future in as_completed(futures):
            receipt = future.result()
            with LOCK:
                receipts.append(receipt)
            print(f"{receipt['source_id']}: {receipt['result']}", file=sys.stderr)
    receipts.sort(key=lambda item: item["source_id"])
    receipt_by_id = {item["source_id"]: item for item in receipts}
    captured_rows = [receipt_to_matrix(row, receipt_by_id[row["source_id"]]) for row in rows]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "http_capture_receipts.json").write_text(
        json.dumps(receipts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    with (args.output_dir / "matriz_fontes_capturadas.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(captured_rows[0]))
        writer.writeheader()
        writer.writerows(captured_rows)
    summary = {
        "total": len(receipts),
        "capturadas": sum(item["result"] == "CAPTURADA_PENDENTE_DE_LEITURA_E_REFETCH" for item in receipts),
        "falhas": sum(item["result"] != "CAPTURADA_PENDENTE_DE_LEITURA_E_REFETCH" for item in receipts),
        "limite": "Nenhum recibo local autoriza publicação; falta leitura do ato, recibo nativo e refetch independente.",
    }
    (args.output_dir / "resumo_capturas.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
