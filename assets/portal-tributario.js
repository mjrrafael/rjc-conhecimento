(function () {
  function normalize(value) {
    return (value || "")
      .toString()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-zA-Z0-9]+/g, " ")
      .replace(/\s+/g, " ")
      .trim()
      .toLowerCase();
  }

  function tokens(value) {
    return normalize(value)
      .split(" ")
      .filter(function (part) { return part.length >= 2; });
  }

  var SEARCH_SYNONYMS = {
    aliquota: ["aliquotas", "carga", "percentual"],
    aliquotas: ["aliquota", "carga", "percentual"],
    beneficio: ["beneficios", "incentivo", "incentivos", "favor"],
    beneficios: ["beneficio", "incentivo", "incentivos", "favores"],
    cbenef: ["codigo beneficio", "codigo de beneficio", "beneficio fiscal"],
    cclass: ["cclasstrib", "classificacao tributaria"],
    cclasstrib: ["cclass", "classificacao tributaria"],
    ccredpres: ["credito presumido", "presumido"],
    cest: ["substituicao tributaria", "st", "segmento"],
    cfop: ["operacao fiscal", "natureza operacao"],
    clt: ["folha", "trabalhista", "empregado", "contrato trabalho"],
    cofins: ["pis cofins", "contribuicoes"],
    comex: ["comercio exterior", "importacao", "exportacao", "aduaneiro"],
    credito: ["creditos", "aproveitamento", "apropriacao"],
    creditos: ["credito", "aproveitamento", "apropriacao"],
    cst: ["codigo situacao tributaria", "tributacao"],
    difal: ["diferencial aliquotas", "consumidor final"],
    diferimento: ["diferido", "postergacao", "posterior"],
    dirbi: ["beneficio federal", "declaracao incentivos"],
    drawback: ["regime aduaneiro", "importacao", "exportacao", "suspensao"],
    efd: ["sped", "escrituracao", "arquivo digital"],
    exportacao: ["exterior", "imunidade", "fim especifico exportacao"],
    fgts: ["fgts digital", "folha"],
    ibs: ["reforma tributaria", "cbs", "imposto bens servicos"],
    importacao: ["importado", "aduaneiro", "desembaraco"],
    ii: ["imposto importacao", "aduaneiro", "importacao"],
    incentivo: ["beneficio", "beneficios", "regime especial"],
    informatica: ["eletronicos", "tecnologia", "computador"],
    ipi: ["tipi", "ripi", "industrializacao"],
    irpj: ["imposto renda pessoa juridica", "lucro real", "lucro presumido"],
    irpf: ["imposto renda pessoa fisica", "pessoa fisica", "ganho capital"],
    isencao: ["isento", "isenta", "beneficio", "dispensa"],
    lc160: ["lei complementar 160", "convenio 190", "confaz"],
    ncm: ["classificacao fiscal", "mercadoria", "produto"],
    nf: ["nfe", "nf e", "nota fiscal"],
    nfe: ["nf e", "nota fiscal eletronica", "xml"],
    pis: ["pis pasep", "cofins", "contribuicoes"],
    pf: ["pessoa fisica", "irpf", "cpf"],
    perdcomp: ["per dcomp", "compensacao", "ressarcimento", "restituicao"],
    presumido: ["lucro presumido", "credito presumido"],
    simples: ["simples nacional", "mei", "pgdas", "das"],
    reducao: ["base reduzida", "reducao de base", "carga efetiva"],
    regime: ["regime especial", "tratamento tributario"],
    sped: ["efd", "escrituracao", "arquivo digital"],
    st: ["substituicao tributaria", "cest", "mva"],
    suspensao: ["suspenso", "suspensa"],
    xml: ["nfe", "nf e", "documento fiscal"]
  };

  function uniqueList(values) {
    var seen = {};
    return values.map(normalize).filter(function (value) {
      if (!value || seen[value]) return false;
      seen[value] = true;
      return true;
    });
  }

  function queryGroups(value) {
    return tokens(value).map(function (token) {
      var related = [token];
      if (SEARCH_SYNONYMS[token]) related = related.concat(SEARCH_SYNONYMS[token]);
      Object.keys(SEARCH_SYNONYMS).forEach(function (key) {
        if (key.indexOf(token) === 0 || token.indexOf(key) === 0) {
          related.push(key);
          related = related.concat(SEARCH_SYNONYMS[key]);
        }
      });
      return uniqueList(related);
    });
  }

  function uniqueWords(value) {
    var seen = {};
    return normalize(value).split(" ").filter(function (word) {
      if (!word || seen[word]) return false;
      seen[word] = true;
      return true;
    });
  }

  function editDistanceAtMost(a, b, limit) {
    if (Math.abs(a.length - b.length) > limit) return false;
    var previous = [];
    var current = [];
    for (var j = 0; j <= b.length; j += 1) previous[j] = j;
    for (var i = 1; i <= a.length; i += 1) {
      current[0] = i;
      var rowMin = current[0];
      for (j = 1; j <= b.length; j += 1) {
        var cost = a.charAt(i - 1) === b.charAt(j - 1) ? 0 : 1;
        current[j] = Math.min(
          previous[j] + 1,
          current[j - 1] + 1,
          previous[j - 1] + cost
        );
        if (current[j] < rowMin) rowMin = current[j];
      }
      if (rowMin > limit) return false;
      var temp = previous;
      previous = current;
      current = temp;
    }
    return previous[b.length] <= limit;
  }

  function tokenScore(token, text, words) {
    if (!token) return 0;
    if (token.length <= 2) return words.indexOf(token) >= 0 ? 4 : 0;
    if (text.indexOf(token) >= 0) return token.length >= 4 ? 6 : 3;
    for (var i = 0; i < words.length; i += 1) {
      var word = words[i];
      if (word.indexOf(token) === 0) return 5;
      if (token.length >= 4 && word.indexOf(token) > 0) return 3;
      if (token.length >= 5 && editDistanceAtMost(token, word.slice(0, token.length), 1)) return 2;
      if (token.length >= 7 && editDistanceAtMost(token, word, 2)) return 1;
    }
    return 0;
  }

  function scoreEntry(entry, groups) {
    var title = normalize(entry.title);
    var summary = normalize(entry.summary);
    var tags = normalize(entry.tags);
    var body = normalize(entry.body || entry.terms || "");
    var url = normalize(entry.url);
    var scope = normalize([entry.kind, entry.jurisdiction, entry.tax, entry.theme].join(" "));
    var haystack = [title, summary, tags, body, url, scope].join(" ");
    var words = uniqueWords(haystack);
    var score = 0;
    for (var i = 0; i < groups.length; i += 1) {
      var bestScore = 0;
      for (var j = 0; j < groups[i].length; j += 1) {
        var token = groups[i][j];
        var partScore = tokenScore(token, haystack, words);
        if (!partScore) continue;
        if (title.indexOf(token) >= 0) partScore += 10;
        if (url.indexOf(token) >= 0) partScore += 5;
        if (tags.indexOf(token) >= 0) partScore += 4;
        if (summary.indexOf(token) >= 0) partScore += 3;
        if (body.indexOf(token) >= 0) partScore += 1;
        if (partScore > bestScore) bestScore = partScore;
      }
      if (!bestScore) return 0;
      score += bestScore;
    }
    return score;
  }

  function matchesText(text, groups) {
    var normalizedText = normalize(text);
    var words = uniqueWords(normalizedText);
    return groups.every(function (group) {
      return group.some(function (token) {
        return tokenScore(token, normalizedText, words) > 0;
      });
    });
  }

  function escapeHtml(value) {
    return (value || "").toString().replace(/[&<>"']/g, function (char) {
      return {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
      }[char];
    });
  }

  function currentPrefix() {
    var parts = window.location.pathname.split("/").filter(Boolean);
    var repoIndex = parts.indexOf("rjc-conhecimento");
    var depth = repoIndex >= 0 ? parts.length - repoIndex - 2 : parts.length - 1;
    if (depth < 0) depth = 0;
    return "../".repeat(depth);
  }

  var fullSearchState = {
    loaded: false,
    loading: false,
    failed: false,
    entries: []
  };

  function loadFullSearch(prefix, callback) {
    if (fullSearchState.loaded || fullSearchState.loading || fullSearchState.failed) {
      if (callback) callback();
      return;
    }
    if (!window.fetch) {
      fullSearchState.failed = true;
      if (callback) callback();
      return;
    }
    fullSearchState.loading = true;
    fetch(prefix + "assets/portal-search-full.json", { cache: "force-cache" })
      .then(function (response) {
        if (!response.ok) throw new Error("search index");
        return response.json();
      })
      .then(function (entries) {
        fullSearchState.entries = Array.isArray(entries) ? entries : [];
        fullSearchState.loaded = true;
      })
      .catch(function () {
        fullSearchState.failed = true;
      })
      .finally(function () {
        fullSearchState.loading = false;
        if (callback) callback();
      });
  }

  function rankedHits(entries, groups, limit) {
    var byUrl = {};
    entries.forEach(function (entry) {
      var score = scoreEntry(entry, groups);
      if (!score) return;
      var existing = byUrl[entry.url];
      if (!existing || score > existing.score) {
        byUrl[entry.url] = { entry: entry, score: score };
      }
    });
    return Object.keys(byUrl)
      .map(function (url) { return byUrl[url]; })
      .sort(function (a, b) { return b.score - a.score; })
      .slice(0, limit);
  }

  function bindGlobalSearch() {
    var input = document.getElementById("globalSearch");
    var results = document.getElementById("searchResults");
    if (!input || !results || !window.RJC_SEARCH) return;

    var prefix = currentPrefix();

    function closeResults() {
      results.classList.remove("open");
      results.innerHTML = "";
    }

    function renderFullSearch() {
      var groups = queryGroups(input.value);
      if (!groups.length) {
        closeResults();
        return;
      }

      if (input.value.trim().length >= 2 && !fullSearchState.loaded && !fullSearchState.loading && !fullSearchState.failed) {
        loadFullSearch(prefix, renderFullSearch);
      }

      var hits = rankedHits(window.RJC_SEARCH.concat(fullSearchState.entries), groups, 24);
      if (!hits.length) {
        results.innerHTML = fullSearchState.loading
          ? '<div class="search-result search-status"><strong>Buscando no texto integral</strong><span>Carregando o índice completo das leis, atos e capítulos publicados.</span></div>'
          : '<div class="search-result"><strong>Nenhum resultado direto</strong><span>Tente por pedaços do termo: veic, eletro, inform, cbenef, difal, presum, st, cst ou ncm.</span></div>';
        results.classList.add("open");
        return;
      }

      results.innerHTML = hits.map(function (hit) {
        var entry = hit.entry;
        return '<a class="search-result" href="' + prefix + entry.url + '">' +
          '<strong>' + escapeHtml(entry.title) + '</strong>' +
          '<span>' + escapeHtml(entry.summary) + '</span>' +
          '<small>' + escapeHtml(entry.url) + '</small>' +
          (entry.kind ? '<em>' + escapeHtml(entry.kind) + '</em>' : '') +
          '</a>';
      }).join("") + (fullSearchState.loading ? '<div class="search-result search-status"><strong>Ampliando busca</strong><span>Incluindo termos do texto integral da legislação.</span></div>' : '');
      results.classList.add("open");
    }

    input.addEventListener("input", function () {
      window.setTimeout(renderFullSearch, 0);
    });

    document.addEventListener("click", function (event) {
      if (!results.contains(event.target) && event.target !== input) {
        closeResults();
      }
    });

    input.addEventListener("keydown", function (event) {
      if (event.key === "Escape") closeResults();
    });
  }

  function bindLocalCardFilter() {
    var input = document.getElementById("globalSearch");
    var cards = Array.prototype.slice.call(document.querySelectorAll(".searchable-card"));
    if (!input || !cards.length) return;

    input.addEventListener("input", function () {
      var groups = queryGroups(input.value);
      if (!groups.length) {
        cards.forEach(function (card) { card.classList.remove("is-hidden"); });
        return;
      }
      cards.forEach(function (card) {
        var haystack = card.getAttribute("data-search") || card.textContent;
        card.classList.toggle("is-hidden", !matchesText(haystack, groups));
      });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    bindGlobalSearch();
    bindLocalCardFilter();
  });
})();
