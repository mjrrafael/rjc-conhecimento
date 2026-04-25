(function () {
  function normalize(value) {
    return (value || "")
      .toString()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase();
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
      var query = normalize(input.value);
      if (query.length < 2) {
        closeResults();
        return;
      }

      var hits = window.RJC_SEARCH
        .map(function (entry) {
          var haystack = normalize([entry.title, entry.summary, entry.tags].join(" "));
          return { entry: entry, score: haystack.indexOf(query) >= 0 ? 1 : 0 };
        })
        .filter(function (hit) { return hit.score > 0; })
        .slice(0, 8);

      if (!hits.length) {
        results.innerHTML = '<div class="search-result"><strong>Nenhum resultado direto</strong><span>Tente buscar por tributo, Estado, beneficio ou documento.</span></div>';
        results.classList.add("open");
        return;
      }

      results.innerHTML = hits.map(function (hit) {
        var entry = hit.entry;
        return '<a class="search-result" href="' + prefix + entry.url + '">' +
          '<strong>' + entry.title + '</strong>' +
          '<span>' + entry.summary + '</span>' +
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
      var query = normalize(input.value);
      if (query.length < 2) {
        cards.forEach(function (card) { card.classList.remove("is-hidden"); });
        return;
      }
      cards.forEach(function (card) {
        var haystack = normalize(card.getAttribute("data-search") || card.textContent);
        card.classList.toggle("is-hidden", haystack.indexOf(query) === -1);
      });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    bindGlobalSearch();
    bindLocalCardFilter();
  });
})();
