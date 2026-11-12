// Thème clair/sombre mémorisé dans le navigateur
(function () {
  const root = document.documentElement;
  try { const t = localStorage.getItem("breche-theme"); if (t) root.dataset.theme = t; } catch (e) {}
  document.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-theme-toggle]");
    if (!btn) return;
    const cur = root.dataset.theme || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    root.dataset.theme = cur === "dark" ? "light" : "dark";
    try { localStorage.setItem("breche-theme", root.dataset.theme); } catch (e) {}
  });
})();

// Filtres de la page Défis (catégorie, statut, recherche)
document.addEventListener("DOMContentLoaded", () => {
  const grid = document.getElementById("challenge-grid");
  if (!grid) return;
  const cards = [...grid.querySelectorAll(".card")];
  const search = document.getElementById("challenge-search");
  const empty = document.getElementById("challenge-empty");
  let cat = "all", status = "all";
  function apply() {
    const q = (search.value || "").trim().toLowerCase();
    let shown = 0;
    cards.forEach((c) => {
      const ok = (cat === "all" || c.dataset.cat === cat)
        && (status === "all" || (status === "todo") === (c.dataset.solved === "0"))
        && (!q || c.dataset.title.includes(q));
      c.hidden = !ok; if (ok) shown++;
    });
    empty.hidden = shown > 0;
  }
  document.querySelectorAll("[data-filter-cat]").forEach((b) => b.addEventListener("click", () => {
    cat = b.dataset.filterCat;
    document.querySelectorAll("[data-filter-cat]").forEach((x) => x.setAttribute("aria-pressed", x === b));
    apply();
  }));
  document.querySelectorAll("[data-filter-status]").forEach((b) => b.addEventListener("click", () => {
    status = b.dataset.filterStatus;
    document.querySelectorAll("[data-filter-status]").forEach((x) => x.setAttribute("aria-pressed", x === b));
    apply();
  }));
  search.addEventListener("input", apply);
});

// Bouton « copier »
document.addEventListener("click", async (e) => {
  const b = e.target.closest("[data-copy]");
  if (!b) return;
  try { await navigator.clipboard.writeText(b.dataset.copy); b.textContent = "Copié"; }
  catch (err) { b.textContent = b.dataset.copy; }
});
