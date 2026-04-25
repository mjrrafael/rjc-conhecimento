#!/usr/bin/env python3
"""Build the static RJC open tax portal from the curated catalog."""

from __future__ import annotations

import json
import re
from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "portal_catalog.json"


def slug(value: str) -> str:
    value = value.lower()
    value = value.replace("ç", "c").replace("ã", "a").replace("á", "a")
    value = value.replace("â", "a").replace("é", "e").replace("ê", "e")
    value = value.replace("í", "i").replace("ó", "o").replace("ô", "o")
    value = value.replace("ú", "u")
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or "item"


def rel_prefix(path: str) -> str:
    depth = len(Path(path).parts) - 1
    return "../" * depth


def a(href: str, label: str, class_name: str = "") -> str:
    cls = f' class="{escape(class_name)}"' if class_name else ""
    return f'<a href="{escape(href)}"{cls}>{escape(label)}</a>'


def source_list(sources: list[dict[str, str]]) -> str:
    items = []
    for source in sources:
        items.append(
            f'<li><a href="{escape(source["url"])}" target="_blank" rel="noopener">'
            f'{escape(source["label"])}</a></li>'
        )
    return "<ul class=\"source-list\">" + "".join(items) + "</ul>"


def source_badge(topic: dict) -> str:
    return (
        '<div class="source-badge">'
        f'<span>Fonte legal conferida em {escape(topic["data_conferencia"])}</span>'
        f'<strong>{escape(topic["status_curadoria"])}</strong>'
        "</div>"
    )


def layout(path: str, title: str, subtitle: str, body: str, active: str = "") -> str:
    prefix = rel_prefix(path)
    nav = [
        ("index.html", "Inicio", "home"),
        ("estados/index.html", "Estados", "estados"),
        ("confaz/index.html", "CONFAZ", "confaz"),
        ("federal/index.html", "Federal", "federal"),
        ("folha-clt/index.html", "Folha e CLT", "folha"),
        ("biblioteca/index.html", "Biblioteca", "biblioteca")
    ]
    nav_html = "".join(
        f'<a href="{prefix}{href}" class="{ "active" if key == active else "" }">{label}</a>'
        for href, label, key in nav
    )
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escape(title)} | RJC Assessoria</title>
  <meta name="description" content="{escape(subtitle)}">
  <link rel="icon" href="{prefix}ico.png">
  <link rel="stylesheet" href="{prefix}assets/portal-tributario.css">
  <script defer src="{prefix}assets/portal-search.js"></script>
  <script defer src="{prefix}assets/portal-tributario.js"></script>
</head>
<body>
  <header class="site-header">
    <div class="topbar">
      <a class="brand" href="{prefix}index.html" aria-label="Portal RJC Tributario Aberto">
        <img src="{prefix}logo.png" alt="RJC Assessoria">
        <span>
          <strong>RJC Tributario Aberto</strong>
          <small>A Arte de Registrar o Patrimonio</small>
        </span>
      </a>
      <nav class="primary-nav" aria-label="Navegacao principal">
        {nav_html}
      </nav>
    </div>
    <div class="searchbar" role="search">
      <label for="globalSearch">Buscar no portal</label>
      <input id="globalSearch" type="search" placeholder="Ex.: cBenef Goias, DIRBI, Convênio ICMS, Lucro Real">
      <div id="searchResults" class="search-results" aria-live="polite"></div>
    </div>
  </header>
  <main>
    {body}
  </main>
  <footer class="site-footer">
    <div>
      <strong>Portal RJC Tributario Aberto</strong>
      <p>Conteudo educativo pautado em legislacao oficial. Nao substitui parecer individual para operacao concreta.</p>
    </div>
    <div>
      <span>Conferencia editorial: 25/04/2026</span>
      <a href="{prefix}biblioteca/index.html#metodo">Metodo e fontes</a>
    </div>
  </footer>
</body>
</html>
"""


def hero(title: str, subtitle: str, eyebrow: str = "Base legal aberta") -> str:
    return f"""
<section class="hero-panel">
  <div>
    <span class="eyebrow">{escape(eyebrow)}</span>
    <h1>{escape(title)}</h1>
    <p>{escape(subtitle)}</p>
  </div>
  <aside class="hero-proof">
    <strong>Regra editorial</strong>
    <p>Lei primeiro. Comentario depois. Cada guia profundo exibe base legal, fonte oficial e data de conferencia.</p>
  </aside>
</section>
"""


def card_grid(cards: list[str], class_name: str = "") -> str:
    return f'<div class="card-grid {escape(class_name)}">' + "".join(cards) + "</div>"


def topic_card(topic: dict, prefix: str = "", extra_class: str = "") -> str:
    bases = ", ".join(topic.get("base_legal", [])[:3])
    return f"""
<a class="portal-card {escape(extra_class)} searchable-card" href="{escape(prefix + topic["path"])}"
   data-search="{escape(topic["titulo"] + " " + topic["tema"] + " " + topic["resumo"] + " " + bases)}">
  <span class="card-kicker">{escape(topic["jurisdicao"])} · {escape(topic["tipo"])}</span>
  <h3>{escape(topic["titulo"])}</h3>
  <p>{escape(topic["resumo"])}</p>
  <small>{escape(topic["status_curadoria"])}</small>
</a>
"""


def render_sections(topic: dict) -> str:
    blocks = []
    for section in topic.get("sections", []):
        paragraphs = "".join(f"<p>{escape(text)}</p>" for text in section.get("body", []))
        blocks.append(f'<section class="content-block"><h2>{escape(section["heading"])}</h2>{paragraphs}</section>')
    return "".join(blocks)


MATRIX_LABELS = [
    ("o_que_e", "O que e"),
    ("base_legal", "Base legal"),
    ("quem_pode_usar", "Quem pode usar"),
    ("condicoes", "Condicoes"),
    ("vedacoes", "Vedacoes"),
    ("como_aparece_no_documento", "Como aparece no documento"),
    ("prova_necessaria", "Prova necessaria"),
    ("risco_comum", "Risco comum"),
    ("fonte_oficial", "Fonte oficial")
]


def render_matrix(topic: dict) -> str:
    cards = []
    for item in topic.get("matriz", []):
        rows = []
        for key, label in MATRIX_LABELS:
            rows.append(f"<dt>{label}</dt><dd>{escape(item.get(key, ''))}</dd>")
        cards.append(
            f'<article class="matrix-card searchable-card" data-search="{escape(item["titulo"] + " " + " ".join(item.values()))}">'
            f'<h3>{escape(item["titulo"])}</h3><dl>{"".join(rows)}</dl></article>'
        )
    if not cards:
        return ""
    return '<section class="matrix-section"><h2>Matriz legal de aplicacao</h2><div class="matrix-grid">' + "".join(cards) + "</div></section>"


def related_links(topic: dict) -> str:
    links = topic.get("links_relacionados", [])
    if not links:
        return ""
    html = "".join(f'<a href="{escape(link["href"])}">{escape(link["label"])}</a>' for link in links)
    return f'<section class="continuity"><h2>Continuar a leitura</h2><div>{html}</div></section>'


def topic_page(topic: dict, active: str) -> str:
    intro = f"""
{hero(topic["titulo"], topic["resumo"], topic["tema"])}
<section class="law-ledger">
  {source_badge(topic)}
  <div>
    <h2>Base legal principal</h2>
    <p>{escape(", ".join(topic["base_legal"]))}</p>
  </div>
  <div>
    <h2>Fontes oficiais</h2>
    {source_list(topic["fonte_oficial"])}
  </div>
</section>
"""
    body = intro + render_sections(topic) + render_matrix(topic) + related_links(topic)
    return layout(topic["path"], topic["titulo"], topic["resumo"], body, active)


def home(data: dict) -> str:
    topics = data["topics"]
    states_link = "estados/index.html"
    cards = [
        f"""
<a class="portal-card featured searchable-card" href="{states_link}" data-search="ICMS por Estado beneficios fiscais Goias">
  <span class="card-kicker">Estados</span>
  <h3>ICMS por Estado</h3>
  <p>Arquitetura nacional por UF, com Goias publicado em profundidade e demais Estados prontos para curadoria.</p>
  <small>27 UFs estruturadas</small>
</a>
""",
        topic_card(next(t for t in topics if t["id"] == "goias-icms-beneficios")),
        topic_card(next(t for t in topics if t["id"] == "confaz-atos-beneficios")),
        f"""
<a class="portal-card searchable-card" href="federal/index.html" data-search="PIS Cofins IPI IRPJ CSLL Lucro Real Lucro Presumido Federal">
  <span class="card-kicker">Federal</span>
  <h3>Tributos federais</h3>
  <p>PIS, Cofins, IPI, IRPJ, CSLL, regimes, beneficios federais e DIRBI em leitura guiada.</p>
  <small>Guias profundos v1</small>
</a>
""",
        topic_card(next(t for t in topics if t["id"] == "folha-clt-previdencia")),
        f"""
<a class="portal-card searchable-card" href="biblioteca/index.html" data-search="manual fiscal financeiro DP RH transportadoras painel fiscal biblioteca">
  <span class="card-kicker">Biblioteca viva</span>
  <h3>Manuais e painel</h3>
  <p>Os materiais existentes continuam funcionando e entram como biblioteca avancada do portal.</p>
  <small>URLs preservadas</small>
</a>
"""
    ]
    federal_cards = [topic_card(t) for t in topics if t["path"].startswith("federal/")][:4]
    body = f"""
{hero(data["site"]["title"], data["site"]["subtitle"], "Portal publico de conhecimento")}
<section class="method-strip">
  <div><strong>Fonte oficial primeiro</strong><span>Planalto, Receita Federal, CONFAZ, SPED e portais estaduais.</span></div>
  <div><strong>BD_LEGISLACAO como acervo</strong><span>Usado para localizar temas, nunca para publicar sem reconferencia.</span></div>
  <div><strong>Prova documental</strong><span>Cada tema aponta documento, memoria de calculo e risco comum.</span></div>
</section>
<section class="section-wrap">
  <div class="section-heading">
    <span class="eyebrow">Comece por aqui</span>
    <h2>Portal, painel e fonte de conhecimento tributario</h2>
    <p>Uma estrutura aberta para ensinar a regra, mostrar a lei, apontar o documento fiscal e conectar a operacao ao fechamento.</p>
  </div>
  {card_grid(cards)}
</section>
<section class="guided-reading">
  <span class="eyebrow">Trilha sugerida</span>
  <h2>Da lei ao documento</h2>
  <div class="timeline">
    <a href="estados/goias.html"><strong>1. Estado</strong><span>Identifique ICMS, beneficio, condicionantes e cBenef.</span></a>
    <a href="confaz/index.html"><strong>2. CONFAZ</strong><span>Confira o lastro nacional de convenio, ajuste ou protocolo.</span></a>
    <a href="federal/pis-cofins.html"><strong>3. Federal</strong><span>Segregue PIS/Cofins, IPI, IRPJ, CSLL e regimes.</span></a>
    <a href="biblioteca/index.html"><strong>4. Prova</strong><span>Use manuais, painel fiscal e rotinas de fechamento.</span></a>
  </div>
</section>
<section class="section-wrap">
  <div class="section-heading">
    <span class="eyebrow">Federal v1</span>
    <h2>Guias profundos publicados</h2>
  </div>
  {card_grid(federal_cards)}
</section>
"""
    return layout("index.html", data["site"]["title"], data["site"]["subtitle"], body, "home")


def estados_index(data: dict) -> str:
    cards = []
    for state in data["states"]:
        href = "goias.html" if state["uf"] == "GO" else f'{state["uf"].lower()}.html'
        klass = "featured" if state["uf"] == "GO" else ""
        cards.append(f"""
<a class="state-card {klass} searchable-card" href="{escape(href)}"
   data-search="{escape(state["uf"] + " " + state["name"] + " ICMS beneficios fiscais")}">
  <strong>{escape(state["uf"])}</strong>
  <h3>{escape(state["name"])}</h3>
  <p>{escape(state["status"])}</p>
  <small>{escape(state["coverage"])}</small>
</a>
""")
    body = f"""
{hero("ICMS por Estado", "Arquitetura nacional para organizar beneficios fiscais, RICMS, cBenef, aliquotas, regimes e prova por UF.", "Estados")}
<section class="law-ledger">
  <div>
    <h2>Estado publicado em profundidade</h2>
    <p>Goias esta publicado na v1 com matriz de beneficios, cBenef, Anexo IX, programas e riscos documentais.</p>
  </div>
  <div>
    <h2>Demais UFs</h2>
    <p>As demais paginas ja existem para preservar a arquitetura e registrar o status de curadoria antes da publicacao profunda.</p>
  </div>
</section>
<section class="section-wrap">
  <div class="section-heading">
    <span class="eyebrow">Mapa nacional</span>
    <h2>Estados estruturados</h2>
  </div>
  {card_grid(cards, "states-grid")}
</section>
"""
    return layout("estados/index.html", "ICMS por Estado", "Mapa nacional de ICMS e beneficios fiscais por UF.", body, "estados")


def state_page(state: dict, data: dict) -> str:
    if state["uf"] == "GO":
        topic = next(t for t in data["topics"] if t["id"] == "goias-icms-beneficios")
        return topic_page(topic, "estados")
    path = f'estados/{state["uf"].lower()}.html'
    body = f"""
{hero(f'{state["name"]}: ICMS e beneficios fiscais', 'Pagina estrutural para curadoria oficial de ICMS, RICMS, beneficios, aliquotas e prova documental.', state["uf"])}
<section class="law-ledger">
  <div>
    <h2>Status de curadoria</h2>
    <p>{escape(state["status"])}. {escape(state["coverage"])}.</p>
  </div>
  <div>
    <h2>Regra de publicacao</h2>
    <p>Esta pagina so recebera tese ou beneficio apos conferencia em portal oficial da UF, CONFAZ ou Planalto, com data de conferencia e fonte aberta.</p>
  </div>
</section>
<section class="matrix-section">
  <h2>Estrutura que sera preenchida</h2>
  <div class="matrix-grid">
    <article class="matrix-card"><h3>ICMS material</h3><p>Fato gerador, contribuinte, base, aliquotas, diferimento, ST e obrigacoes.</p></article>
    <article class="matrix-card"><h3>Beneficios fiscais</h3><p>Isencao, reducao, credito outorgado, regimes especiais, condicionantes e prova.</p></article>
    <article class="matrix-card"><h3>Documento e SPED</h3><p>NF-e, CT-e, MDF-e, cBenef quando houver, EFD e memoria de calculo.</p></article>
  </div>
</section>
<section class="continuity">
  <h2>Enquanto isso</h2>
  <div>
    <a href="goias.html">Ver modelo publicado de Goias</a>
    <a href="../confaz/index.html">Entender CONFAZ e beneficios</a>
    <a href="../biblioteca/index.html">Consultar manuais avancados</a>
  </div>
</section>
"""
    return layout(path, f'{state["name"]}: ICMS e beneficios fiscais', "Pagina estrutural por UF.", body, "estados")


def federal_index(data: dict) -> str:
    topics = [t for t in data["topics"] if t["path"].startswith("federal/")]
    cards = []
    for topic in topics:
        local_topic = dict(topic)
        local_topic["path"] = Path(topic["path"]).name
        cards.append(topic_card(local_topic))
    body = f"""
{hero("Tributos federais", "PIS, Cofins, IPI, IRPJ, CSLL, regimes tributarios, beneficios federais e DIRBI com fonte oficial.", "Federal")}
<section class="law-ledger">
  <div>
    <h2>Como navegar</h2>
    <p>Comece pelo tributo, depois confirme o regime da empresa, o tratamento especial e a obrigacao acessoria.</p>
  </div>
  <div>
    <h2>Fontes base</h2>
    <p>Planalto, Receita Federal, SPED, DOU e atos normativos federais vigentes.</p>
  </div>
</section>
<section class="section-wrap">
  <div class="section-heading">
    <span class="eyebrow">Guias publicados</span>
    <h2>Federal em profundidade</h2>
  </div>
  {card_grid(cards)}
</section>
"""
    return layout("federal/index.html", "Tributos federais", "Guias federais profundos.", body, "federal")


def biblioteca(data: dict) -> str:
    cards = []
    for item in data["library"]:
        cards.append(f"""
<a class="portal-card searchable-card" href="../{escape(item["href"])}"
   data-search="{escape(item["title"] + " " + item["summary"] + " " + item["type"])}">
  <span class="card-kicker">{escape(item["type"])}</span>
  <h3>{escape(item["title"])}</h3>
  <p>{escape(item["summary"])}</p>
  <small>URL preservada</small>
</a>
""")
    body = f"""
{hero("Biblioteca viva", "Manuais, painel e materiais avancados preservados como camada de aprofundamento do portal.", "Biblioteca")}
<section id="metodo" class="law-ledger">
  <div>
    <h2>Metodo editorial</h2>
    <p>{escape(data["site"]["source_policy"])}</p>
  </div>
  <div>
    <h2>Data de conferencia</h2>
    <p>Conteudos profundos v1 conferidos em {escape(data["site"]["verified_on"])}. Paginas estruturais indicam quando ainda aguardam curadoria oficial.</p>
  </div>
</section>
<section class="section-wrap">
  <div class="section-heading">
    <span class="eyebrow">Acervo RJC</span>
    <h2>Manuais e painel preservados</h2>
  </div>
  {card_grid(cards)}
</section>
"""
    return layout("biblioteca/index.html", "Biblioteca viva", "Manuais e painel preservados.", body, "biblioteca")


def search_index(data: dict) -> str:
    entries = [
        {"title": data["site"]["title"], "url": "index.html", "summary": data["site"]["subtitle"], "tags": "portal tributario aberto"}
    ]
    entries += [
        {
            "title": topic["titulo"],
            "url": topic["path"],
            "summary": topic["resumo"],
            "tags": " ".join([topic["jurisdicao"], topic["tema"], topic["tipo"], " ".join(topic["base_legal"])])
        }
        for topic in data["topics"]
    ]
    entries += [
        {
            "title": f'{state["name"]}: ICMS e beneficios fiscais',
            "url": "estados/goias.html" if state["uf"] == "GO" else f'estados/{state["uf"].lower()}.html',
            "summary": state["status"],
            "tags": f'{state["uf"]} {state["name"]} ICMS beneficios fiscais RICMS'
        }
        for state in data["states"]
    ]
    entries += [
        {
            "title": item["title"],
            "url": item["href"],
            "summary": item["summary"],
            "tags": item["type"]
        }
        for item in data["library"]
    ]
    payload = json.dumps(entries, ensure_ascii=False, indent=2)
    return "window.RJC_SEARCH = " + payload + ";\n"


def write(path: str, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    clean = "\n".join(line.rstrip() for line in content.splitlines()) + "\n"
    target.write_text(clean, encoding="utf-8", newline="\n")


def audit(data: dict) -> None:
    required = ["titulo", "jurisdicao", "tema", "tipo", "resumo", "base_legal", "fonte_oficial", "data_conferencia", "status_curadoria", "links_relacionados"]
    errors = []
    for topic in data["topics"]:
        for key in required:
            if not topic.get(key):
                errors.append(f'{topic.get("id", "?")}: missing {key}')
        for source in topic.get("fonte_oficial", []):
            if not source.get("url", "").startswith("https://"):
                errors.append(f'{topic["id"]}: source is not https: {source}')
    if errors:
        raise SystemExit("\n".join(errors))


def main() -> None:
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    audit(data)
    write("index.html", home(data))
    write("estados/index.html", estados_index(data))
    for state in data["states"]:
        write("estados/goias.html" if state["uf"] == "GO" else f'estados/{state["uf"].lower()}.html', state_page(state, data))
    write("federal/index.html", federal_index(data))
    for topic in data["topics"]:
        if topic["path"] in {"estados/goias.html", "confaz/index.html", "folha-clt/index.html"}:
            continue
        if topic["path"].startswith("federal/"):
            write(topic["path"], topic_page(topic, "federal"))
    write("confaz/index.html", topic_page(next(t for t in data["topics"] if t["id"] == "confaz-atos-beneficios"), "confaz"))
    write("folha-clt/index.html", topic_page(next(t for t in data["topics"] if t["id"] == "folha-clt-previdencia"), "folha"))
    write("biblioteca/index.html", biblioteca(data))
    write("assets/portal-search.js", search_index(data))
    print("Portal generated successfully.")


if __name__ == "__main__":
    main()
