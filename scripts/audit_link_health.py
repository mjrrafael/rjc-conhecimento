#!/usr/bin/env python3
"""Validate health of primary-source links for published benefit cards."""

from __future__ import annotations

import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

from audit_v2_helpers import benefit_entries


USER_AGENT = "RJC-Conhecimento/2.0"


def fetch_status(url: str) -> tuple[int | None, str]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return int(getattr(response, "status", 200) or 200), ""
    except urllib.error.HTTPError as exc:
        return exc.code, str(exc)
    except Exception as exc:  # transient network/source issues are soft
        return None, str(exc)


def main() -> int:
    urls = []
    seen: set[str] = set()
    for item in benefit_entries():
        url = str(item.get("official_url", "")).strip()
        if url and url not in seen:
            seen.add(url)
            urls.append(url)
    hard_errors: list[str] = []
    soft_warnings: list[str] = []
    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = {executor.submit(fetch_status, url): url for url in urls}
        for future in as_completed(futures):
            url = futures[future]
            status, detail = future.result()
            if status in {404, 410}:
                hard_errors.append(f"{status} -> {url}")
            elif status is None or (status is not None and status >= 500):
                soft_warnings.append(f"{status or 'erro'} -> {url} ({detail})")
            if len(hard_errors) >= 25:
                break
    if soft_warnings:
        print("Avisos de saúde de link (soft gate):")
        for warning in soft_warnings[:20]:
            print(f"- {warning}")
    if hard_errors:
        print("Falhas de link oficial (hard gate):")
        for error in hard_errors:
            print(f"- {error}")
        return 1
    print(f"Links oficiais verificados: {len(urls)} URLs únicas; nenhum 404/410 em benefício publicado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
