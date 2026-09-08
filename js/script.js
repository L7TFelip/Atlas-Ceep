/* Atlas CEEP — interações */
(function () {
  var root = document.documentElement;

  /* ---------- Ícones (Lucide) ---------- */
  function renderIcons() {
    if (window.lucide && window.lucide.createIcons) window.lucide.createIcons();
  }

  /* ---------- Tema claro / escuro ---------- */
  var saved = localStorage.getItem("atlas-theme") || "dark";
  root.setAttribute("data-theme", saved);

  function paintToggles() {
    var dark = root.getAttribute("data-theme") === "dark";
    document.querySelectorAll("[data-theme-toggle] .knob").forEach(function (k) {
      k.innerHTML = '<i data-lucide="' + (dark ? "moon" : "sun") + '" width="13" height="13"></i>';
    });
    renderIcons();
  }

  function toggleTheme() {
    var dark = root.getAttribute("data-theme") === "dark";
    root.setAttribute("data-theme", dark ? "light" : "dark");
    localStorage.setItem("atlas-theme", dark ? "light" : "dark");
    paintToggles();
  }

  document.querySelectorAll("[data-theme-toggle]").forEach(function (el) {
    el.addEventListener("click", toggleTheme);
    el.addEventListener("keydown", function (e) {
      if (e.key === "Enter") toggleTheme();
    });
  });

  /* ---------- Navbar com sombra ao rolar ---------- */
  var header = document.getElementById("site-header");
  function onScroll() {
    header.classList.toggle("scrolled", window.scrollY > 30);
  }
  window.addEventListener("scroll", onScroll);
  onScroll();

  /* ---------- Menu mobile ---------- */
  var menu = document.querySelector("[data-mobile-menu]");
  var overlay = document.querySelector("[data-overlay]");
  var burger = document.querySelector("[data-burger]");

  function setMenu(open) {
    menu.classList.toggle("open", open);
    overlay.classList.toggle("open", open);
  }
  burger.addEventListener("click", function () {
    setMenu(true);
  });
  burger.addEventListener("keydown", function (e) {
    if (e.key === "Enter") setMenu(true);
  });
  overlay.addEventListener("click", function () {
    setMenu(false);
  });
  menu.querySelectorAll("a").forEach(function (a) {
    a.addEventListener("click", function () {
      setMenu(false);
    });
  });

  /* ---------- Animação de entrada (reveal) ---------- */
  var revealObserver = new IntersectionObserver(
    function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) e.target.classList.add("in");
      });
    },
    { threshold: 0.15 }
  );
  document.querySelectorAll(".reveal").forEach(function (el) {
    revealObserver.observe(el);
  });

  /* ---------- Contadores das estatísticas ---------- */
  var countObserver = new IntersectionObserver(
    function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var el = entry.target;
        countObserver.unobserve(el);
        var target = parseInt(el.getAttribute("data-count"), 10);
        var suffix = el.getAttribute("data-suffix") || "";
        var current = 0;
        var step = Math.max(1, Math.ceil(target / 60));
        (function tick() {
          current += step;
          if (current >= target) {
            el.textContent = target + suffix;
          } else {
            el.textContent = String(current);
            requestAnimationFrame(tick);
          }
        })();
      });
    },
    { threshold: 0.4 }
  );
  document.querySelectorAll("[data-count]").forEach(function (el) {
    countObserver.observe(el);
  });

  /* ---------- Formulário de contato ---------- */
  var form = document.getElementById("contact-form");
  if (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      form.reset();
      document.getElementById("form-ok").style.display = "block";
    });
  }

  /* ---------- Inicialização ---------- */
  renderIcons();
  paintToggles();
})();
