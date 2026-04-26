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

  function scoreEntry(entry, queryTokens) {
    var title = normalize(entry.title);
    var summary = normalize(entry.summary);
    var tags = normalize(entry.tags);
    var haystack = [title, summary, tags].join(" ");
    var words = uniqueWords(haystack);
    var score = 0;
    for (var i = 0; i < queryTokens.length; i += 1) {
      var token = queryTokens[i];
      var partScore = tokenScore(token, haystack, words);
      if (!partScore) return 0;
      if (title.indexOf(token) >= 0) partScore += 8;
      if (tags.indexOf(token) >= 0) partScore += 3;
      score += partScore;
    }
    return score;
  }

  function matchesText(text, queryTokens) {
    var normalizedText = normalize(text);
    var words = uniqueWords(normalizedText);
    return queryTokens.every(function (token) {
      return tokenScore(token, normalizedText, words) > 0;
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

  function bindGlobalSearch() {
    var input = document.getElementById("globalSearch");
    var results = document.getElementById("searchResults");
    if (!input || !results || !window.RJC_SEARCH) return;

    var prefix = currentPrefix();

    function closeResults() {
      results.classList.remove("open");
      results.innerHTML = "";
    }

    input.addEventListener("input", function () {
      var queryTokens = tokens(input.value);
      if (!queryTokens.length) {
        closeResults();
        return;
      }

      var hits = window.RJC_SEARCH
        .map(function (entry) {
          return { entry: entry, score: scoreEntry(entry, queryTokens) };
        })
        .filter(function (hit) { return hit.score > 0; })
        .sort(function (a, b) { return b.score - a.score; })
        .slice(0, 12);

      if (!hits.length) {
        results.innerHTML = '<div class="search-result"><strong>Nenhum resultado direto</strong><span>Tente por pedaços do termo: veic, eletro, inform, cbenef, difal, presum.</span></div>';
        results.classList.add("open");
        return;
      }

      results.innerHTML = hits.map(function (hit) {
        var entry = hit.entry;
        return '<a class="search-result" href="' + prefix + entry.url + '">' +
          '<strong>' + escapeHtml(entry.title) + '</strong>' +
          '<span>' + escapeHtml(entry.summary) + '</span>' +
          '</a>';
      }).join("");
      results.classList.add("open");
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
      var queryTokens = tokens(input.value);
      if (!queryTokens.length) {
        cards.forEach(function (card) { card.classList.remove("is-hidden"); });
        return;
      }
      cards.forEach(function (card) {
        var haystack = card.getAttribute("data-search") || card.textContent;
        card.classList.toggle("is-hidden", !matchesText(haystack, queryTokens));
      });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    bindGlobalSearch();
    bindLocalCardFilter();
  });
})();
