(() => {
  "use strict";

  const { $ , api } = window.Atlas;

  function initLogin() {
    const form = $("#loginForm");
    if (!form) return;

    const password = $("#password");
    const passwordToggle = $("#passwordToggle");
    const loginUser = $("#loginUser");
    const studentOption = $("#studentOption");
    const teamOption = $("#adminOption");
    const loginButtonText = $("#loginButtonText");
    const userLabel = $("#userLabel");
    const message = $("#loginMessage");
    const remember = $("#remember");
    const forgotPassword = $("#forgotPassword");

    let selectedRole = localStorage.getItem("atlas-login-role") === "equipe" ? "equipe" : "aluno";

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

    function selectRole(role) {
      selectedRole = role;
      studentOption?.classList.toggle("active", role === "aluno");
      teamOption?.classList.toggle("active", role === "equipe");

      if (role === "aluno") {
        userLabel.textContent = "CGM";
        loginUser.placeholder = "Digite seu CGM";
        loginUser.inputMode = "numeric";
        loginButtonText.textContent = "Entrar como aluno";
      } else {
        userLabel.textContent = "Usuário da equipe";
        loginUser.placeholder = "Digite seu usuário";
        loginUser.inputMode = "text";
        loginButtonText.textContent = "Entrar como equipe";
      }
      hideMessage();
    }

    studentOption?.addEventListener("click", () => selectRole("aluno"));
    teamOption?.addEventListener("click", () => selectRole("equipe"));

    passwordToggle?.addEventListener("click", () => {
      const showing = password.type === "text";
      password.type = showing ? "password" : "text";
      passwordToggle.textContent = showing ? "◉" : "○";
      const label = showing ? "Mostrar senha" : "Ocultar senha";
      passwordToggle.title = label;
      passwordToggle.setAttribute("aria-label", label);
    });

    const savedLogin = localStorage.getItem("atlas-login-user");
    if (savedLogin) {
      loginUser.value = savedLogin;
      remember.checked = true;
    }

    selectRole(selectedRole);

    form.addEventListener("submit", async event => {
      event.preventDefault();
      hideMessage();

      const user = loginUser.value.trim();
      const pass = password.value;
      if (!user || !pass) {
        showMessage(selectedRole === "aluno" ? "Digite seu CGM e sua senha." : "Digite seu usuário e sua senha.");
        return;
      }
      if (selectedRole === "aluno" && !/^\d+$/.test(user)) {
        showMessage("O CGM deve conter apenas números.");
        return;
      }

      const button = $("#loginButton");
      button.disabled = true;

      try {
        const data = await api("/api/auth/login", {
          method: "POST",
          body: JSON.stringify({
            login: user,
            senha: pass,
            tipo: selectedRole,
            lembrar: remember.checked
          })
        });

        if (remember.checked) {
          localStorage.setItem("atlas-login-user", user);
          localStorage.setItem("atlas-login-role", selectedRole);
        } else {
          localStorage.removeItem("atlas-login-user");
          localStorage.removeItem("atlas-login-role");
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
