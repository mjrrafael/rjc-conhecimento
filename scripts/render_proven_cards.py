#!/usr/bin/env python3
"""Render the same card registry for a person and for an AI consumer.

Public mode fails closed: only cards explicitly approved after native receipts and
blind review can be emitted into the site. Preview mode remains inside the audit
directory and is not a deployment artifact.
"""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CARDS = ROOT / "data" / "prova_material" / "cards_em_reconstrucao.json"
PREVIEW = ROOT / "auditoria" / "execucoes" / "reconstrucao-provas-2026-07-16" / "preview"


def html_card(card: dict) -> str:
    rule = card["regra_estruturada"]
    temporal = card["temporal"]
    rows = "".join(
        f"<dt>{html.escape(label)}</dt><dd>{html.escape(value['valor'] or value['status'])}{('<br><small>' + html.escape(value['justificativa']) + '</small>') if value.get('justificativa') else ''}</dd>"
        for label, value in (("Publicação", temporal["publicacao"]), ("Vigência", temporal["inicio_vigencia"]), ("Eficácia", temporal["inicio_eficacia"]), ("Fim", temporal["fim_vigencia"]))
    )
    details = "".join(
        f"<li><b>{html.escape(key.replace('_', ' ').capitalize())}:</b> {html.escape(', '.join(value) if isinstance(value, list) else str(value))}</li>"
        for key, value in rule.items()
    )
    sources = "".join(
        f"<li><a href=\"{html.escape(source['url_final'])}\">{html.escape(source['identificacao_humana'])}</a><br><small>{html.escape(source['papel'])} · HTTP {source['http_status']} · SHA-256 <code>{html.escape(source['sha256_corpo_bruto'])}</code></small></li>"
        for source in card["fontes"]
    )
    ato = card["ato"]
    return f"""<article id=\"{html.escape(card['id'])}\"><h2>{html.escape(card['titulo_humano'])}</h2>
<p>{html.escape(card['resumo_humano'])}</p><h3>Regra e limites</h3><ul>{details}</ul>
<p><b>Orientação de uso:</b> {html.escape(card['orientacao_editorial'])}</p>
<h3>Ato</h3><p>{html.escape(ato['tipo'])} nº {html.escape(ato['numero'])}, de {html.escape(ato['data'])} · {html.escape(ato['autoridade_emissora'])} · Jurisdição: {html.escape(card['jurisdicao'])}</p>
<h3>Tempo jurídico</h3><dl>{rows}</dl>
<h3>Fontes oficiais conferidas</h3><ul>{sources}</ul></article>"""


def page(cards: list[dict], preview: bool) -> str:
    banner = "<p class=notice>Prévia de auditoria: não é artefato público.</p>" if preview else ""
    return f"""<!doctype html><html lang=\"pt-BR\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"><meta name=\"description\" content=\"Normas tributárias com ato, datas jurídicas, fontes e prova por campo.\"><title>Normas tributárias com prova material</title><style>body{{font:17px/1.55 system-ui,sans-serif;max-width:960px;margin:auto;padding:2rem;color:#152d36}}article{{border-top:1px solid #d7e1e4;padding:1.2rem 0}}h1,h2,h3{{line-height:1.2}}dl{{display:grid;grid-template-columns:max-content 1fr;gap:.3rem 1rem}}dt{{font-weight:700}}.notice{{background:#fff5c7;padding:1rem;border-radius:.4rem}}small{{color:#4b5d63}}code{{overflow-wrap:anywhere}}</style></head><body><main><h1>Normas tributárias com prova material</h1>{banner}<p>Leitura humana e dados estruturados para IA vêm do mesmo registro. Cada resumo aponta ao ato, às datas jurídicas e às fontes; a explicação não substitui a leitura do dispositivo nem a análise do caso concreto.</p>{''.join(html_card(card) for card in cards)}</main></body></html>"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cards", type=Path, default=CARDS)
    parser.add_argument("--output-dir", type=Path, default=PREVIEW)
    parser.add_argument("--public", action="store_true")
    args = parser.parse_args()
    data = json.loads(args.cards.read_text(encoding="utf-8"))
    all_cards = data["cards"]
    cards = all_cards if not args.public else [card for card in all_cards if card["estado_publicacao"] == "APROVADA_PARA_PUBLICACAO"]
    if args.public and len(cards) != len(all_cards):
        raise SystemExit("Recusada emissão pública: há card sem recibo nativo e revisão cega.")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "index.html").write_text(page(cards, not args.public), encoding="utf-8")
    ai_payload = {"schema": "rjc-prova-material-ai-v1", "cards": cards, "surface": "preview" if not args.public else "public"}
    (args.output_dir / "normas-ia.json").write_text(json.dumps(ai_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Renderizados {len(cards)} cards em {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
