(() => {
  "use strict";

  const { $ , api } = window.Atlas;

  function initLogin() {
    const form = $("#loginForm");
    if (!form) return;

    const password = $("#password");
    const passwordToggle = $("#passwordToggle");
    const loginEmail = $("#loginEmail");
    const message = $("#loginMessage");
    const remember = $("#remember");
    const forgotPassword = $("#forgotPassword");

    function showMessage(text, type = "error") {
      message.hidden = false;
      message.textContent = text;
      message.className = `login-message ${type}`;
    }

    function hideMessage() {
      message.hidden = true;
      message.textContent = "";
      message.className = "login-message";
    }

    passwordToggle?.addEventListener("click", () => {
      const showing = password.type === "text";
      password.type = showing ? "password" : "text";
      passwordToggle.textContent = showing ? "◉" : "○";
      const label = showing ? "Mostrar senha" : "Ocultar senha";
      passwordToggle.title = label;
      passwordToggle.setAttribute("aria-label", label);
    });

    const savedLogin = localStorage.getItem("atlas-login-email");
    if (savedLogin) {
      loginEmail.value = savedLogin;
      remember.checked = true;
    }

    form.addEventListener("submit", async event => {
      event.preventDefault();
      hideMessage();

      const email = loginEmail.value.trim();
      const pass = password.value;
      if (!email || !pass) {
        showMessage("Digite seu e-mail e sua senha.");
        return;
      }
      if (!loginEmail.validity.valid) {
        showMessage("Digite um endereço de e-mail válido.");
        return;
      }

      const button = $("#loginButton");
      button.disabled = true;

      try {
        const data = await api("/api/auth/login", {
          method: "POST",
          body: JSON.stringify({
            email,
            senha: pass,
            lembrar: remember.checked
          })
        });

        if (remember.checked) {
          localStorage.setItem("atlas-login-email", email);
        } else {
          localStorage.removeItem("atlas-login-email");
        }

        showMessage("Login realizado. Abrindo o painel...", "success");
        window.location.href = data.redirect;
      } catch (error) {
        showMessage(error.message);
      } finally {
        button.disabled = false;
      }
    });

    forgotPassword?.addEventListener("click", () => {
      showMessage("A recuperação de senha ainda não foi implementada no backend.", "success");
    });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initLogin);
  else initLogin();
})();
