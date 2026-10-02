(() => {
  "use strict";

  // Atalhos para selecionar um elemento ou uma lista de elementos no DOM.
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

  // Codifica caracteres especiais para evitar que valores sejam interpretados como HTML.
  function escapeHtml(value = "") {
    return String(value).replace(/[&<>'"]/g, c => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      "'": "&#039;",
      '"': "&quot;"
    })[c]);
  }

  // Envia requisições à API e trata respostas JSON e erros HTTP.
  async function api(path, options = {}) {
    const headers = new Headers(options.headers || {});
    if (options.body && !(options.body instanceof FormData) && !headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }

    const response = await fetch(path, {
      // Mantém os cookies da sessão nas chamadas feitas para este mesmo site.
      credentials: "same-origin",
      ...options,
      headers
    });

    let data = {};
    try {
      data = await response.json();
    } catch {
      data = {};
    }

    if (!response.ok) {
      const error = new Error(data.erro || data.mensagem || `Erro HTTP ${response.status}`);
      error.status = response.status;
      error.data = data;
      throw error;
    }

    return data;
  }

  // Acessa o armazenamento local sem interromper a página se ele estiver indisponível.
  function readStorage(key) {
    try { return localStorage.getItem(key); } catch { return null; }
  }

  function writeStorage(key, value) {
    try { localStorage.setItem(key, value); } catch {}
  }

  // Aplica o tema salvo e permite alternar entre claro e escuro.
  function initTheme() {
    const root = document.documentElement;
    const buttons = $$("#themeBtn, [data-theme-toggle]");
    const saved = readStorage("atlas-theme");

    if (saved === "light" || saved === "dark") root.dataset.theme = saved;
    else if (!root.dataset.theme) root.dataset.theme = "dark";

    const refresh = () => {
      const nextTheme = root.dataset.theme === "dark" ? "claro" : "escuro";
      const icon = root.dataset.theme === "dark" ? "☼" : "☾";
      buttons.forEach(button => {
        const iconNode = button.querySelector("[data-theme-icon]");
        const labelNode = button.querySelector("[data-theme-label]");
        if (iconNode) iconNode.textContent = icon;
        else button.textContent = icon;
        if (labelNode) labelNode.textContent = `Modo ${nextTheme}`;
        button.title = `Ativar modo ${nextTheme}`;
        button.setAttribute("aria-label", `Ativar modo ${nextTheme}`);
      });
    };

    buttons.forEach(button => button.addEventListener("click", () => {
      root.dataset.theme = root.dataset.theme === "dark" ? "light" : "dark";
      writeStorage("atlas-theme", root.dataset.theme);
      refresh();
    }));

    refresh();
  }

  // Abre o menu do perfil e fecha o menu ao clicar fora dele.
  function initProfileMenu() {
    const button = $("#profileBtn");
    const menu = $("#profileMenu");
    if (!button || !menu) return;

    button.addEventListener("click", event => {
      event.stopPropagation();
      menu.hidden = !menu.hidden;
      button.setAttribute("aria-expanded", String(!menu.hidden));
    });

    document.addEventListener("click", event => {
      if (!event.target.closest(".top-actions")) {
        menu.hidden = true;
        button.setAttribute("aria-expanded", "false");
      }
    });
  }

  // Gera até duas iniciais para exibir no avatar do usuário.
  function initials(name = "") {
    return name
      .trim()
      .split(/\s+/)
      .slice(0, 2)
      .map(part => part[0]?.toUpperCase() || "")
      .join("") || "AT";
  }

  // Atualiza nome, avatar e identificação do usuário na página atual.
  function applyUserToPage(user) {
    if (!user) return;

    const shortName = user.nome?.split(/\s+/)[0] || "Usuário";
    const avatar = $(".avatar");
    const profileName = $(".profile-name");
    const menuStrong = $(".profile-menu-head strong");
    const menuMeta = $(".profile-menu-head span");
    const welcomeTitle = $(".welcome-copy h1");

    if (avatar) avatar.textContent = initials(user.nome);
    if (profileName) profileName.textContent = shortName;
    if (menuStrong) menuStrong.textContent = user.nome || shortName;
    if (welcomeTitle) welcomeTitle.textContent = `Olá, ${shortName}.`;

    if (menuMeta) {
      if (user.papel === "aluno") menuMeta.textContent = user.turma ? `${user.turma} · CEEP` : "Aluno · CEEP";
      else if (user.papel === "professor") menuMeta.textContent = "Professor · CEEP";
      else if (user.papel === "adm") menuMeta.textContent = "Administração · CEEP";
    }
  }

  // Busca a sessão atual na API e, quando solicitado, redireciona se ela expirou.
  async function currentUser({ redirectOn401 = false } = {}) {
    try {
      const data = await api("/api/auth/me");
      applyUserToPage(data.usuario);
      return data.usuario;
    } catch (error) {
      if (redirectOn401 && error.status === 401) window.location.href = "/login";
      return null;
    }
  }

  // Encerra a sessão no servidor e volta à página de login.
  async function logout() {
    try {
      await api("/api/auth/logout", { method: "POST" });
    } finally {
      window.location.href = "/login";
    }
  }

  // Liga o botão de sair à função de encerramento da sessão.
  function initLogout() {
    $("#logoutBtn")?.addEventListener("click", logout);
  }

  // Liga o atalho da página ao formulário de login.
  function initProfileShortcut() {
    $("#loginPageBtn")?.addEventListener("click", () => {
      window.location.href = "/login";
    });
  }

  // Expõe funções compartilhadas para os demais scripts do frontend.
  window.Atlas = {
    $,
    $$,
    api,
    currentUser,
    applyUserToPage,
    escapeHtml,
    logout,
    initials
  };

  // Inicializa os recursos comuns usados pelas páginas.
  function init() {
    initTheme();
    initProfileMenu();
    initLogout();
    initProfileShortcut();
  }

  // Aguarda o DOM estar pronto antes de configurar os controles da página.
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
