(() => {
  "use strict";

  const { $ , api } = window.Atlas;

  function initCadastro() {
    const form = $("#registerForm");
    if (!form) return;

    const nome = $("#fullName");
    const cgm = $("#cgm");
    const email = $("#email");
    const senha = $("#password");
    const confirmarSenha = $("#confirmPassword");
    const mensagem = $("#registerMessage");
    const botao = $("#registerButton");

    function mostrarMensagem(texto, tipo = "error") {
      mensagem.hidden = false;
      mensagem.textContent = texto;
      mensagem.className = `login-message ${tipo}`;
    }

    $("#passwordToggle")?.addEventListener("click", event => {
      const controle = event.currentTarget;
      const mostrar = senha.type === "password";
      senha.type = mostrar ? "text" : "password";
      controle.textContent = mostrar ? "○" : "◉";
      controle.setAttribute("aria-label", mostrar ? "Ocultar senha" : "Mostrar senha");
      controle.title = mostrar ? "Ocultar senha" : "Mostrar senha";
    });

    form.addEventListener("submit", async event => {
      event.preventDefault();
      mensagem.hidden = true;

      if (!form.reportValidity()) return;
      if (senha.value !== confirmarSenha.value) {
        mostrarMensagem("As senhas não coincidem.");
        confirmarSenha.focus();
        return;
      }

      botao.disabled = true;
      try {
        await api("/api/auth/cadastro", {
          method: "POST",
          body: JSON.stringify({
            nome: nome.value.trim(),
            cgm: cgm.value.trim(),
            email: email.value.trim(),
            senha: senha.value
          })
        });
        mostrarMensagem("Conta criada com sucesso. Redirecionando para o login...", "success");
        window.setTimeout(() => { window.location.href = "/login"; }, 1200);
      } catch (error) {
        mostrarMensagem(error.message);
      } finally {
        botao.disabled = false;
      }
    });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initCadastro);
  else initCadastro();
})();
