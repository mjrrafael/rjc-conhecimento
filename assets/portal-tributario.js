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
      .filter(function (part) { return part.length >= 2 && !QUERY_STOPWORDS[part]; });
  }

  var QUERY_STOPWORDS = {
    a: true, ao: true, aos: true, as: true, com: true, da: true, das: true,
    de: true, do: true, dos: true, e: true, em: true, na: true, nas: true,
    no: true, nos: true, o: true, os: true, ou: true, para: true, pela: true,
    pelas: true, pelo: true, pelos: true, por: true, sobre: true, um: true,
    uma: true, uns: true, umas: true
  };

  var QUERY_INTENT_TOKENS = {
    beneficio: true, beneficios: true, beneficiado: true, favorecido: true,
    fiscal: true, fiscais: true, tributario: true, tributaria: true,
    tributarios: true, tributarias: true, tratamento: true, tratamentos: true,
    tributacao: true, regime: true, regimes: true, especial: true, especiais: true,
    especifico: true, especificos: true, diferenciado: true, diferenciados: true,
    regra: true, regras: true, legal: true, legais: true, legislacao: true,
    imposto: true, impostos: true, tributo: true, tributos: true
  };

  var SEARCH_SYNONYMS = {
    aliquota: ["aliquotas", "carga", "percentual"],
    aliquotas: ["aliquota", "carga", "percentual"],
    agro: ["agropecuario", "rural", "produtor rural", "insumo agropecuario"],
    agropecuario: ["agro", "rural", "produtor rural", "atividade rural"],
    alimento: ["alimentos", "cesta basica", "produto alimenticio", "genero alimenticio"],
    alimentos: ["alimento", "cesta basica", "produtos alimenticios", "generos alimenticios"],
    arroz: ["1006", "arroz em casca", "arroz descascado", "arroz beneficiado", "arroz semibranqueado", "arroz branqueado", "arroz polido", "arroz quebrado"],
    beneficio: ["beneficios", "incentivo", "incentivos", "favor", "tratamento tributario", "tratamento fiscal", "regime diferenciado", "regime especial", "isencao", "reducao", "credito presumido", "credito outorgado"],
    beneficios: ["beneficio", "incentivo", "incentivos", "favores", "tratamento tributario", "tratamento fiscal", "regime diferenciado", "regime especial", "isencao", "reducao", "credito presumido", "credito outorgado"],
    cbenef: ["codigo beneficio", "codigo de beneficio", "beneficio fiscal"],
    cclass: ["cclasstrib", "classificacao tributaria"],
    cclasstrib: ["cclass", "classificacao tributaria"],
    ccredpres: ["credito presumido", "presumido"],
    cest: ["substituicao tributaria", "st", "segmento"],
    cesta: ["cesta basica", "alimento", "alimentos", "generos alimenticios"],
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
    franca: ["zona franca", "zona franca de manaus", "zfm", "area de livre comercio"],
    francas: ["zonas francas", "zona franca", "zfm", "areas de livre comercio"],
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
    monofasia: ["monofasico", "tributacao concentrada", "aliquota concentrada", "pis cofins monofasico"],
    monofasico: ["monofasia", "tributacao concentrada", "aliquota concentrada", "pis cofins monofasico"],
    ncm: ["classificacao fiscal", "mercadoria", "produto"],
    nf: ["nfe", "nf e", "nota fiscal"],
    nfe: ["nf e", "nota fiscal eletronica", "xml"],
    pis: ["pis pasep", "cofins", "contribuicoes"],
    pf: ["pessoa fisica", "irpf", "cpf"],
    perdcomp: ["per dcomp", "compensacao", "ressarcimento", "restituicao"],
    presumido: ["lucro presumido", "credito presumido"],
    simples: ["simples nacional", "mei", "pgdas", "das"],
    reducao: ["base reduzida", "reducao de base", "carga efetiva", "beneficio fiscal"],
    regime: ["regime especial", "tratamento tributario", "tratamento fiscal", "regime diferenciado", "regime especifico"],
    especial: ["regime especial", "tratamento especial", "tratamento diferenciado", "regime especifico"],
    diferenciado: ["regime diferenciado", "tratamento diferenciado", "regime especial", "regime especifico"],
    tratamento: ["tratamento tributario", "tratamento fiscal", "beneficio fiscal", "regime especial", "regime diferenciado", "tributacao"],
    tributario: ["fiscal", "tributacao", "imposto", "beneficio fiscal", "tratamento tributario"],
    tributaria: ["fiscal", "tributacao", "imposto", "beneficio fiscal", "tratamento tributario"],
    sped: ["efd", "escrituracao", "arquivo digital"],
    st: ["substituicao tributaria", "cest", "mva"],
    suspensao: ["suspenso", "suspensa"],
    xml: ["nfe", "nf e", "documento fiscal"],
    zfm: ["zona franca", "zona franca de manaus", "amazonia ocidental", "area de livre comercio"],
    zona: ["zona franca", "zfm", "area de livre comercio"],
    zonas: ["zonas francas", "zona franca", "zfm", "areas de livre comercio"]
  };

  function uniqueList(values) {
    var seen = {};
    return values.map(normalize).filter(function (value) {
      if (!value || seen[value]) return false;
      seen[value] = true;
      return true;
    });
  }

  function expandedGroup(token) {
      var related = [token];
      if (SEARCH_SYNONYMS[token]) related = related.concat(SEARCH_SYNONYMS[token]);
      Object.keys(SEARCH_SYNONYMS).forEach(function (key) {
        if (key.indexOf(token) === 0 || token.indexOf(key) === 0) {
          related.push(key);
          related = related.concat(SEARCH_SYNONYMS[key]);
        }
      });
      return uniqueList(related);
  }

  function queryPlan(value) {
    var hard = [];
    var soft = [];
    tokens(value).forEach(function (token) {
      var group = expandedGroup(token);
      if (QUERY_INTENT_TOKENS[token]) {
        soft.push(group);
      } else {
        hard.push(group);
      }
    });
    if (!hard.length && soft.length) {
      hard = soft;
      soft = [];
    }
    return {
      hard: hard,
      soft: soft,
      groups: hard.concat(soft),
      hasTerms: hard.length > 0 || soft.length > 0
    };
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

  function bestGroupScore(group, haystack, words, title, summary, tags, body, url) {
    var bestScore = 0;
    for (var j = 0; j < group.length; j += 1) {
      var token = group[j];
      var partScore = tokenScore(token, haystack, words);
      if (!partScore) continue;
      if (title.indexOf(token) >= 0) partScore += 10;
      if (url.indexOf(token) >= 0) partScore += 5;
      if (tags.indexOf(token) >= 0) partScore += 4;
      if (summary.indexOf(token) >= 0) partScore += 3;
      if (body.indexOf(token) >= 0) partScore += 1;
      if (partScore > bestScore) bestScore = partScore;
    }
    return bestScore;
  }

  function groupAppearsIn(group, text) {
    return group.some(function (token) {
      return text.indexOf(token) >= 0;
    });
  }

  function scoreEntry(entry, plan) {
    var title = normalize(entry.title);
    var summary = normalize(entry.summary);
    var tags = normalize(entry.tags);
    var body = normalize([entry.body, entry.terms, entry.semantic, entry.product, entry.legal_basis].join(" "));
    var rawUrl = (entry.url || "").toString();
    var url = normalize(rawUrl.split("#")[0]);
    if (normalize(rawUrl).indexOf("backup") >= 0 || title.indexOf("backup") >= 0) return 0;
    var scope = normalize([entry.kind, entry.jurisdiction, entry.tax, entry.theme].join(" "));
    var haystack = [title, summary, tags, body, url, scope].join(" ");
    var words = uniqueWords(haystack);
    var score = 0;
    var directHardMatch = false;
    for (var i = 0; i < plan.hard.length; i += 1) {
      var hardScore = bestGroupScore(plan.hard[i], haystack, words, title, summary, tags, body, url);
      if (!hardScore) return 0;
      score += hardScore * 2;
      if (groupAppearsIn(plan.hard[i], [title, tags, summary, url].join(" "))) {
        score += 25;
        directHardMatch = true;
      }
    }
    if (plan.soft.length && url.indexOf("beneficios ncm html") >= 0 && !directHardMatch) return 0;
    if (plan.hard.length && plan.soft.length && url.indexOf("beneficios ncm html") >= 0) score += 20;
    var softTotal = 0;
    for (i = 0; i < plan.soft.length; i += 1) {
      var softScore = bestGroupScore(plan.soft[i], haystack, words, title, summary, tags, body, url);
      if (softScore) softTotal += Math.min(softScore, 14);
    }
    score += Math.min(softTotal, 40);
    return score;
  }

  function matchesText(text, plan) {
    var normalizedText = normalize(text);
    var words = uniqueWords(normalizedText);
    return plan.hard.every(function (group) {
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

  function rankedHits(entries, plan, limit) {
    var byUrl = {};
    entries.forEach(function (entry) {
      var score = scoreEntry(entry, plan);
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
      var plan = queryPlan(input.value);
      if (!plan.hasTerms) {
        closeResults();
        return;
      }

      if (input.value.trim().length >= 2 && !fullSearchState.loaded && !fullSearchState.loading && !fullSearchState.failed) {
        loadFullSearch(prefix, renderFullSearch);
      }

      var hits = rankedHits(window.RJC_SEARCH.concat(fullSearchState.entries), plan, 80);
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
      var plan = queryPlan(input.value);
      if (!plan.hasTerms) {
        cards.forEach(function (card) { card.classList.remove("is-hidden"); });
        return;
      }
      cards.forEach(function (card) {
        var haystack = card.getAttribute("data-search") || card.textContent;
        card.classList.toggle("is-hidden", !matchesText(haystack, plan));
      });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    bindGlobalSearch();
    bindLocalCardFilter();
  });
})();
