#!/usr/bin/env python3
"""Capture exact legal-act URLs for field-level provenance.

Unlike the institutional matrix collector, this tool receives individual acts and
archives their complete bodies outside the repository. A local capture remains a
reproducibility record only; publication additionally requires a platform-native
receipt and an independent refetch.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener


ROOT = Path(__file__).resolve().parents[1]


class RedirectTrace(HTTPRedirectHandler):
    def __init__(self) -> None:
        super().__init__()
        self.chain: list[dict[str, object]] = []

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        self.chain.append({"from_url": req.full_url, "to_url": newurl, "status": code, "location": headers.get("Location", "")})
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def safe(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value)


def outside_repo(path: Path) -> bool:
    try:
        path.resolve().relative_to(ROOT.resolve())
    except ValueError:
        return True
    return False


def capture(source: dict[str, str], evidence_root: Path, timeout: int, max_bytes: int) -> dict[str, object]:
    now = datetime.now(timezone.utc)
    receipt_id = f"local-act-{safe(source['source_id'])}-{now.strftime('%Y%m%dT%H%M%S%fZ')}"
    trace = RedirectTrace()
    opener = build_opener(trace)  # no cookie handler: each request is stateless
    request_headers = {"Accept": "text/html,application/xhtml+xml,application/pdf;q=0.9,*/*;q=0.1", "User-Agent": "RJC-Portal-Proof-Research/1.0 (anonymous, no-cookie)"}
    receipt: dict[str, object] = {
        "receipt_id": receipt_id,
        "receipt_class": "LOCAL_REPRODUCIBLE_NOT_PLATFORM_NATIVE",
        "source_id": source["source_id"],
        "source_url": source["url"],
        "captured_at": now.isoformat().replace("+00:00", "Z"),
        "request_headers": request_headers,
        "cookies": "none",
        "redirect_chain": trace.chain,
        "result": "ERRO_DE_CAPTURA",
        "publication_authorization": "NAO",
    }
    try:
        response = opener.open(Request(source["url"], headers=request_headers, method="GET"), timeout=timeout)
        with response:
            body = response.read(max_bytes + 1)
            headers = {str(k): str(v) for k, v in response.headers.items()}
            receipt["response"] = {"url_final": response.geturl(), "status": response.status, "headers": headers, "mime": headers.get("Content-Type", "").split(";", 1)[0]}
            if len(body) > max_bytes:
                receipt["result"] = "CORPO_EXCEDE_LIMITE_NAO_ARQUIVADO"
                receipt["body"] = {"bytes_lidos": len(body), "limite": max_bytes}
            else:
                digest = hashlib.sha256(body).hexdigest()
                body_path = evidence_root / "bodies" / f"{safe(source['source_id'])}-{digest}.bin"
                body_path.parent.mkdir(parents=True, exist_ok=True)
                body_path.write_bytes(body)
                receipt["body"] = {"bytes": len(body), "sha256": digest, "path_externo": str(body_path)}
                receipt["result"] = "CAPTURADA_PENDENTE_DE_REFETCH"
    except HTTPError as exc:
        receipt["response"] = {"url_final": exc.geturl(), "status": exc.code, "headers": {str(k): str(v) for k, v in exc.headers.items()}}
        receipt["result"] = "HTTP_ERROR"
    except (URLError, TimeoutError, OSError) as exc:
        receipt["error"] = f"{type(exc).__name__}: {exc}"
        receipt["result"] = "ERRO_DE_REDE"
    except Exception as exc:  # a receipt must survive a truncated/invalid HTTP body
        receipt["error"] = f"{type(exc).__name__}: {exc}"
        receipt["result"] = "ERRO_INESPERADO"
    receipt["redirect_chain"] = trace.chain
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--max-bytes", type=int, default=25 * 1024 * 1024)
    args = parser.parse_args()
    if not outside_repo(args.evidence_root):
        raise SystemExit("O arquivo bruto da fonte deve permanecer fora do repositório.")
    sources = json.loads(args.sources.read_text(encoding="utf-8"))
    if not isinstance(sources, list) or not sources or any(not isinstance(x, dict) or set(("source_id", "url")) - set(x) for x in sources):
        raise SystemExit("--sources deve ser uma lista não vazia com source_id e url.")
    if len({str(item["source_id"]) for item in sources}) != len(sources):
        raise SystemExit("source_id duplicado.")
    args.evidence_root.mkdir(parents=True, exist_ok=True)
    receipts = [capture({"source_id": str(item["source_id"]), "url": str(item["url"])}, args.evidence_root, args.timeout, args.max_bytes) for item in sources]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    failed = [r for r in receipts if r["result"] != "CAPTURADA_PENDENTE_DE_REFETCH"]
    print(json.dumps({"total": len(receipts), "capturadas": len(receipts) - len(failed), "falhas": len(failed), "output": str(args.output)}, ensure_ascii=False))
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
