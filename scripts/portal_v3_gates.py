#!/usr/bin/env python3
"""Material, fail-closed gates for the Portal RJC v3 publication contract."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
UFS = set("AC AL AM AP BA CE DF ES GO MA MG MS MT PA PB PE PI PR RJ RN RO RR RS SC SE SP TO".split())
STATE_CLASSES = {"SEFAZ_LEGISLACAO", "DOE", "ASSEMBLEIA_LEGISLATIVA"}
FEDERAL_CLASSES = {
    "PLANALTO", "DOU_IMPRENSA_NACIONAL", "RFB_SIJUT_NORMAS", "PGFN",
    "CONFAZ_CONVENIOS", "CONFAZ_PROTOCOLOS", "CONFAZ_AJUSTES_SINIEF",
    "CONFAZ_ATOS_COTEPE", "CGIBS_PORTAL_NACIONAL_TCS", "SENADO", "STF", "STJ", "CARF",
}
LEGAL_FIELDS = {
    "publicacao", "inicio_vigencia", "inicio_eficacia", "fim_vigencia", "ato", "ato_oficial",
    "beneficio", "benefit_type", "scope_summary", "legal_basis", "legal_excerpt", "conditions",
    "condicao", "prova_documental", "transicao_rt", "internalizacao_status",
}
DATE_FIELDS = {"publicacao", "inicio_vigencia", "inicio_eficacia", "fim_vigencia"}
SAFE_SURFACE = {"index.html", "404.html", "robots.txt", "llms.txt"}


def resolve_run() -> Path:
    configured = os.environ.get("RJC_MONITOR_RUN", "").strip()
    if configured:
        path = Path(configured)
        return path if path.is_absolute() else ROOT / path
    candidates = sorted(path for path in (ROOT / "auditoria" / "execucoes").glob("monitor-v3-*") if path.is_dir())
    if not candidates:
        raise RuntimeError("nenhuma execução monitor-v3 encontrada")
    return candidates[-1]


RUN = resolve_run()


def canonical_sha(path: Path) -> str:
    raw = path.read_bytes()
    if b"\x00" not in raw:
        raw = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(raw).hexdigest()


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_json_documents() -> list[tuple[Path, object]]:
    documents: list[tuple[Path, object]] = []
    for base in (ROOT / "data", ROOT / "assets"):
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.json")):
            try:
                documents.append((path, load_json(path)))
            except (OSError, json.JSONDecodeError):
                continue
        for path in sorted(base.rglob("*.ndjson")):
            try:
                rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
            except (OSError, json.JSONDecodeError):
                continue
            documents.append((path, rows))
    return documents


def walk_dicts(value: object, locator: str = "$"):
    if isinstance(value, dict):
        yield locator, value
        for key, child in value.items():
            yield from walk_dicts(child, f"{locator}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk_dicts(child, f"{locator}[{index}]")


def public_cards():
    for path, payload in iter_json_documents():
        for locator, item in walk_dicts(payload):
            if item.get("publishable") is True:
                yield path, locator, item


def provenance_items(card: dict) -> dict[str, dict]:
    raw = card.get("field_provenance")
    if isinstance(raw, dict):
        return {str(key): value for key, value in raw.items() if isinstance(value, dict)}
    if isinstance(raw, list):
        return {str(item.get("field", "")): item for item in raw if isinstance(item, dict)}
    return {}


def official_url(value: object) -> bool:
    try:
        parsed = urlparse(str(value))
    except ValueError:
        return False
    host = (parsed.hostname or "").lower()
    return parsed.scheme == "https" and bool(host) and (
        host.endswith(".gov.br") or host.endswith(".leg.br") or host.endswith(".jus.br")
    )


def material_hash(value: object) -> bool:
    return bool(re.fullmatch(r"[0-9a-fA-F]{64}", str(value or "")))


def add_limited(errors: list[str], message: str, limit: int = 40) -> None:
    if len(errors) < limit:
        errors.append(message)


def gate_field_provenance() -> list[str]:
    errors: list[str] = []
    count = 0
    for path, locator, card in public_cards():
        count += 1
        provenance = provenance_items(card)
        card_id = str(card.get("id") or f"{path.relative_to(ROOT)}:{locator}")
        for field in sorted(LEGAL_FIELDS & card.keys()):
            value = card.get(field)
            if value in (None, "", [], {}):
                continue
            proof = provenance.get(field)
            required = {"card_id", "field", "value", "final_url", "http_status", "mime", "body_sha256", "literal_excerpt", "locator", "normalization_rule"}
            if not proof or required - set(proof):
                add_limited(errors, f"{card_id}: proveniência incompleta para {field}")
                continue
            if str(proof.get("card_id")) != card_id or proof.get("value") != value:
                add_limited(errors, f"{card_id}: proveniência não vincula valor de {field}")
            if not official_url(proof.get("final_url")) or str(proof.get("http_status")) != "200" or not material_hash(proof.get("body_sha256")):
                add_limited(errors, f"{card_id}: captura oficial inválida para {field}")
            if len(str(proof.get("literal_excerpt", "")).strip()) < 16 or len(str(proof.get("locator", "")).strip()) < 4:
                add_limited(errors, f"{card_id}: trecho/localizador não material para {field}")
    if count and errors:
        errors.append(f"total de cards publishable auditados={count}; falhas mostradas até o limite")
    return errors


def gate_no_synthetic_legal_dates() -> list[str]:
    errors: list[str] = []
    suspicious_source = {
        'iso_date(source.get("captured_on")) or TODAY': "captured_on/TODAY",
        'source.get("validity_start", source.get("captured_on"': "fallback captured_on",
        '"verificado_em": TODAY': "verificado_em=TODAY",
    }
    for path in sorted((ROOT / "scripts").glob("*.py")):
        if path.name.startswith(("audit_", "test_", "portal_v3_", "run_")):
            continue
        raw = path.read_text(encoding="utf-8", errors="ignore")
        for needle, label in suspicious_source.items():
            if needle in raw:
                add_limited(errors, f"{path.name}: padrão sintético proibido ({label})")
    for path, locator, card in public_cards():
        provenance = provenance_items(card)
        card_id = str(card.get("id") or f"{path.relative_to(ROOT)}:{locator}")
        for field in DATE_FIELDS:
            value = card.get(field)
            if value in (None, "", "AUSENTE", "INDETERMINADO", "NÃO_APLICÁVEL"):
                continue
            proof = provenance.get(field)
            if not proof or proof.get("value") != value or not proof.get("literal_excerpt") or not proof.get("locator"):
                add_limited(errors, f"{card_id}: data {field} sem prova literal vinculante")
    return errors


def verification_receipts() -> dict[str, dict]:
    result: dict[str, dict] = {}
    directory = RUN / "verification_receipts"
    if directory.exists():
        for path in directory.glob("*.json"):
            try:
                item = load_json(path)
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(item, dict) and item.get("id"):
                result[str(item["id"])] = item
    return result


def gate_verification_receipts() -> list[str]:
    errors: list[str] = []
    receipts = verification_receipts()
    used: dict[str, str] = {}
    for path, locator, card in public_cards():
        card_id = str(card.get("id") or f"{path.relative_to(ROOT)}:{locator}")
        receipt_id = str(card.get("verification_receipt_id") or "")
        receipt = receipts.get(receipt_id)
        if not receipt:
            add_limited(errors, f"{card_id}: recibo de verificação ausente")
            continue
        if receipt_id in used:
            add_limited(errors, f"{card_id}: recibo {receipt_id} reutilizado por {used[receipt_id]}")
        used[receipt_id] = card_id
        required = {"previous_card_sha256", "final_card_sha256", "http_receipt_ids", "fields_checked", "result", "reviewer"}
        if required - set(receipt) or receipt.get("result") != "PASS":
            add_limited(errors, f"{card_id}: recibo material incompleto/reprovado")
        if not material_hash(receipt.get("previous_card_sha256")) or not material_hash(receipt.get("final_card_sha256")):
            add_limited(errors, f"{card_id}: hashes anterior/final inválidos")
        ids = receipt.get("http_receipt_ids")
        if not isinstance(ids, list) or len(set(map(str, ids))) < 2:
            add_limited(errors, f"{card_id}: menos de duas capturas independentes")
    orphan = set(receipts) - set(used)
    if orphan:
        add_limited(errors, f"recibos sem card correspondente={len(orphan)}")
    return errors


def load_receipt_bundle() -> dict:
    path = RUN / "http_platform_receipts.json"
    if not path.exists():
        return {}
    payload = load_json(path)
    return payload if isinstance(payload, dict) else {}


def gate_http_platform_receipts() -> list[str]:
    errors: list[str] = []
    bundle = load_receipt_bundle()
    if bundle.get("native_receipt_status") != "AVAILABLE":
        return ["recibos HTTP nativos confrontáveis indisponíveis"]
    receipts = bundle.get("receipts")
    if not isinstance(receipts, list) or not receipts:
        return ["lista de recibos HTTP nativos vazia"]
    seen: set[str] = set()
    for item in receipts:
        if not isinstance(item, dict):
            add_limited(errors, "recibo HTTP não é objeto")
            continue
        required = {"native_call_id", "tool", "timestamp", "request", "redirects", "response", "status", "mime", "bytes", "body_sha256"}
        if required - set(item):
            add_limited(errors, "recibo HTTP incompleto")
            continue
        receipt_id = str(item.get("native_call_id"))
        if not receipt_id or receipt_id in seen:
            add_limited(errors, "ID nativo HTTP ausente/duplicado")
        seen.add(receipt_id)
        if str(item.get("status")) != "200" or not material_hash(item.get("body_sha256")):
            add_limited(errors, f"{receipt_id}: HTTP/hash inválido")
        request = item.get("request")
        if not isinstance(request, dict) or request.get("cookies") or request.get("authorization"):
            add_limited(errors, f"{receipt_id}: captura não anônima")
    return errors


def native_receipts_by_id() -> dict[str, dict]:
    receipts = load_receipt_bundle().get("receipts", [])
    return {str(item.get("native_call_id")): item for item in receipts if isinstance(item, dict) and item.get("native_call_id")}


def gate_link_receipts() -> list[str]:
    errors: list[str] = []
    receipts = native_receipts_by_id()
    negative = re.compile(r"login|challenge|access denied|soft.?404|página inicial|homepage", re.I)
    for path, locator, card in public_cards():
        card_id = str(card.get("id") or f"{path.relative_to(ROOT)}:{locator}")
        ids = card.get("independent_http_receipt_ids")
        if not isinstance(ids, list) or len(set(map(str, ids))) < 2:
            add_limited(errors, f"{card_id}: capturas independentes ausentes")
            continue
        for receipt_id in ids:
            receipt = receipts.get(str(receipt_id))
            if not receipt:
                add_limited(errors, f"{card_id}: recibo nativo {receipt_id} não encontrado")
                continue
            identity = receipt.get("act_identity")
            if not isinstance(identity, dict) or not all(identity.get(k) for k in ("type_number", "authority", "jurisdiction", "date_locator", "supporting_excerpt")):
                add_limited(errors, f"{card_id}: identidade material do ato incompleta")
            title = str(receipt.get("title", "")) + " " + str(receipt.get("body_markers", ""))
            if negative.search(title):
                add_limited(errors, f"{card_id}: homepage/login/challenge/soft-404")
    return errors


def gate_internalization_evidence() -> list[str]:
    errors: list[str] = []
    for path, locator, card in public_cards():
        jurisdiction = str(card.get("jurisdiction") or card.get("ente_uf") or "").upper()
        tax = str(card.get("tax") or "").upper()
        if jurisdiction not in UFS or tax != "ICMS":
            continue
        card_id = str(card.get("id") or f"{path.relative_to(ROOT)}:{locator}")
        status = card.get("internalization_status") or card.get("internalizacao_status")
        if status not in {"COMPROVADA", "DISPENSADA_COM_FUNDAMENTO"}:
            add_limited(errors, f"{card_id}: internalização não comprovada")
            continue
        evidence = card.get("internalization_evidence") or card.get("internalizacao_evidencia")
        required = {"act", "authority", "jurisdiction", "benefit", "final_url", "body_sha256", "locator"}
        if not isinstance(evidence, dict) or required - set(evidence):
            add_limited(errors, f"{card_id}: prova específica de internalização incompleta")
            continue
        if str(evidence.get("jurisdiction", "")).upper() != jurisdiction or not official_url(evidence.get("final_url")) or not material_hash(evidence.get("body_sha256")):
            add_limited(errors, f"{card_id}: prova de internalização não vincula UF/ato/hash")
    return errors


def git_files() -> set[str]:
    output = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", "HEAD"], cwd=ROOT, text=True, encoding="utf-8")
    return {line.strip().replace("\\", "/") for line in output.splitlines() if line.strip()}


def filesystem_files() -> set[str]:
    files: set[str] = set()
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel == ".git" or rel.startswith(".git/") or rel.startswith("_site/"):
            continue
        files.add(rel)
    return files


def gate_full_content_coverage() -> list[str]:
    errors: list[str] = []
    tracked, filesystem = git_files(), filesystem_files()
    if tracked != filesystem:
        errors.append(f"Git/filesystem divergentes: faltam={len(tracked-filesystem)} sobram={len(filesystem-tracked)}")
    inventory_path = RUN / "inventario_integral.csv"
    if not inventory_path.exists():
        return errors + ["inventario_integral.csv ausente"]
    rows = list(csv.DictReader(inventory_path.open(encoding="utf-8")))
    inventory = {row.get("caminho_ou_id", "") for row in rows}
    if inventory != filesystem:
        errors.append(f"inventário/filesystem divergentes: faltam={len(filesystem-inventory)} sobram={len(inventory-filesystem)}")
    unsafe_status = [row for row in rows if row.get("status") not in {"OK", "CORRIGIDO", "QUARENTENA"}]
    if unsafe_status:
        errors.append(f"itens sem estado terminal seguro={len(unsafe_status)}")
    for rel in ("_config.yml", "index.html", "404.html", "robots.txt", "llms.txt"):
        if rel not in filesystem:
            errors.append(f"superfície obrigatória ausente: {rel}")
    return errors


def matrix_rows() -> list[dict]:
    path = RUN / "matriz_fontes_canonicas.csv"
    if not path.exists():
        return []
    return list(csv.DictReader(path.open(encoding="utf-8")))


def gate_canonical_source_scope() -> list[str]:
    errors: list[str] = []
    rows = matrix_rows()
    state = {(row.get("jurisdicao"), row.get("classe")) for row in rows if row.get("jurisdicao") in UFS}
    expected = {(uf, cls) for uf in UFS for cls in STATE_CLASSES}
    if state != expected:
        errors.append(f"matriz estadual divergente: faltam={len(expected-state)} sobram={len(state-expected)}")
    federal = {row.get("classe") for row in rows if row.get("jurisdicao") == "BR"}
    if federal != FEDERAL_CLASSES:
        errors.append(f"matriz federal divergente: faltam={len(FEDERAL_CLASSES-federal)} sobram={len(federal-FEDERAL_CLASSES)}")
    required = ("url_inicial", "url_final", "dominio", "http_receipt_id", "status_http", "sha256_corpo")
    incomplete = [row for row in rows if any(not str(row.get(field, "")).strip() for field in required)]
    if incomplete:
        errors.append(f"linhas canônicas/referenciadas sem URL/recibo/hash material={len(incomplete)}")
    return errors


def emitted_surface() -> dict[str, str]:
    site = Path(os.environ.get("RJC_PORTAL_SITE", "")) if os.environ.get("RJC_PORTAL_SITE") else None
    base = site if site and site.exists() else ROOT
    result: dict[str, str] = {}
    for rel in SAFE_SURFACE:
        path = base / rel
        if path.is_file():
            result[rel] = path.read_text(encoding="utf-8", errors="ignore")
    return result


def gate_public_set_algebra() -> list[str]:
    errors: list[str] = []
    surface = emitted_surface()
    if set(surface) != SAFE_SURFACE:
        errors.append(f"superfície segura divergente: {sorted(set(surface) ^ SAFE_SURFACE)}")
    joined = "\n".join(surface.values()).casefold()
    cards = list(public_cards())
    ids = {str(card.get("id", "")).casefold() for _, _, card in cards if card.get("id")}
    visible = {card_id for card_id in ids if card_id in joined}
    if visible != ids:
        errors.append(f"projeção publishable divergente: autorizados={len(ids)} visíveis={len(visible)}")
    if re.search(r"\bA_VALIDAR\b|\bA_REVALIDAR\b|\bBLOQUEADO\b", joined, re.I):
        errors.append("estado inseguro exposto como fato público")
    return errors


def normalized_words(value: object) -> list[str]:
    return re.findall(r"[a-z0-9]+", str(value).casefold())


def quarantine_records():
    for path, payload in iter_json_documents():
        path_text = path.as_posix().casefold()
        for locator, item in walk_dicts(payload):
            status = str(item.get("validation_status") or item.get("status") or item.get("audience_status") or "").casefold()
            if "quarant" in path_text or "a_validar" in status or "nao-publicar" in status or "não-publicar" in status:
                yield path, locator, item


def gate_quarantine_fingerprints() -> list[str]:
    errors: list[str] = []
    tracked = git_files()
    tracked_quarantine = [rel for rel in tracked if "quarant" in rel.casefold()]
    if tracked_quarantine:
        errors.append(f"quarentena está em repositório público rastreado: {len(tracked_quarantine)} arquivo(s)")
    joined = "\n".join(emitted_surface().values()).casefold()
    public_words = normalized_words(joined)
    public_shingles = {tuple(public_words[i:i+8]) for i in range(max(0, len(public_words)-7))}
    for path, locator, item in quarantine_records():
        for field in ("id", "sha256", "source_fingerprint"):
            token = str(item.get(field, "")).strip().casefold()
            if len(token) >= 8 and token in joined:
                add_limited(errors, f"{path.relative_to(ROOT)}:{locator}: token de quarentena vazou")
                break
        for field in ("legal_excerpt", "scope_summary", "product_or_operation", "conditions"):
            words = normalized_words(item.get(field, ""))
            if len(words) >= 8 and any(tuple(words[i:i+8]) in public_shingles for i in range(len(words)-7)):
                add_limited(errors, f"{path.relative_to(ROOT)}:{locator}: shingle de quarentena vazou")
                break
    return errors


def gate_subagent_independence() -> list[str]:
    path = RUN / "subagents_platform_receipts.json"
    if not path.exists():
        return ["subagents_platform_receipts.json ausente"]
    payload = load_json(path)
    errors: list[str] = []
    if not isinstance(payload, dict) or payload.get("native_receipt_status") != "AVAILABLE":
        return ["recibos nativos/export bruto de subagentes indisponíveis"]
    for wave in ("wave1", "wave2"):
        tasks = payload.get(wave)
        if not isinstance(tasks, list) or len({str(item.get("canonical_task_id")) for item in tasks if isinstance(item, dict)}) < 3:
            errors.append(f"{wave}: menos de três tasks nativas distintas")
        for item in tasks or []:
            if not isinstance(item, dict) or item.get("fork_turns") != "none" or not item.get("prompt_hash") or not item.get("session_export"):
                add_limited(errors, f"{wave}: recibo incompleto")
    if payload.get("negative_access_proof") is not True:
        errors.append("prova negativa de leitura entre ondas ausente")
    return errors


def gate_publication() -> list[str]:
    path = RUN / "publication_proof.json"
    if not path.exists():
        return ["publication_proof.json ausente"]
    proof = load_json(path)
    required = {"pr", "candidate_sha", "ci_run", "ci_conclusion", "merge_sha", "pages_run", "pages_conclusion", "production_checked_at"}
    errors = ["prova de publicação incompleta"] if not isinstance(proof, dict) or required - set(proof) else []
    if isinstance(proof, dict):
        if proof.get("ci_conclusion") != "success" or proof.get("pages_conclusion") != "success":
            errors.append("CI/Pages não verdes")
        if not material_hash(proof.get("candidate_sha")) or not material_hash(proof.get("merge_sha")):
            errors.append("SHA candidato/merge inválido")
    return errors


def gate_public_http_hashes() -> list[str]:
    path = RUN / "public_http_hashes.json"
    if not path.exists():
        return ["public_http_hashes.json ausente"]
    payload = load_json(path)
    if not isinstance(payload, dict):
        return ["public_http_hashes.json inválido"]
    errors: list[str] = []
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        return ["nenhum artefato HTTP público comprovado"]
    for item in artifacts:
        if not isinstance(item, dict) or str(item.get("status")) != "200" or not material_hash(item.get("http_sha256")) or item.get("http_sha256") != item.get("merge_sha256"):
            add_limited(errors, "artefato público diverge do merge/HTTP 200")
    if payload.get("all_public_official_sources_refetched") is not True:
        errors.append("refetch pós-deploy das fontes oficiais públicas incompleto")
    return errors


GATES = {
    "audit_field_provenance": gate_field_provenance,
    "audit_no_synthetic_legal_dates": gate_no_synthetic_legal_dates,
    "audit_verification_receipts": gate_verification_receipts,
    "audit_http_platform_receipts": gate_http_platform_receipts,
    "audit_link_receipts": gate_link_receipts,
    "audit_internalization_evidence": gate_internalization_evidence,
    "audit_full_content_coverage": gate_full_content_coverage,
    "audit_canonical_source_scope": gate_canonical_source_scope,
    "audit_public_set_algebra": gate_public_set_algebra,
    "audit_quarantine_fingerprints": gate_quarantine_fingerprints,
    "audit_subagent_independence": gate_subagent_independence,
    "audit_publication": gate_publication,
    "audit_public_http_hashes": gate_public_http_hashes,
}


def run_named_gate(name: str) -> int:
    try:
        errors = GATES[name]()
    except Exception as exc:  # fail closed, including malformed evidence
        errors = [f"exceção fail-closed: {type(exc).__name__}: {exc}"]
    if errors:
        print(f"{name}: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"{name}: PASS")
    return 0


def main() -> int:
    name = Path(sys.argv[0]).stem
    if len(sys.argv) > 1:
        name = sys.argv[1]
    if name not in GATES:
        print("gate desconhecido: " + name)
        return 2
    return run_named_gate(name)


if __name__ == "__main__":
    raise SystemExit(main())
