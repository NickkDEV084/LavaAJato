import { clearNotice, setFormBusy, showNotice } from "../../core/ui.js";
import { getPostAuthDestination } from "./auth-navigation.js";
import { loginAccount, registerAccount } from "./auth-service.js";

export function initAuthPage() {
  const tabs = [...document.querySelectorAll('[role="tab"][data-auth-tab]')];
  const panels = [...document.querySelectorAll("[data-auth-panel]")];
  const loginForm = document.querySelector("#login-form");
  const registerForm = document.querySelector("#register-form");

  function selectPanel(name) {
    document.querySelector(".auth-main").classList.toggle("is-register", name === "register");
    tabs.forEach((tab) => {
      const selected = tab.dataset.authTab === name;
      tab.setAttribute("aria-selected", String(selected));
      tab.tabIndex = selected ? 0 : -1;
    });
    panels.forEach((panel) => {
      panel.hidden = panel.dataset.authPanel !== name;
    });
    clearNotice(document.querySelector("#auth-notice"));
  }

  tabs.forEach((tab) => tab.addEventListener("click", () => selectPanel(tab.dataset.authTab)));
  document.querySelectorAll('.auth-switch [data-auth-tab]').forEach((button) => {
    button.addEventListener("click", () => selectPanel(button.dataset.authTab));
  });

  tabs.forEach((tab, index) => tab.addEventListener("keydown", (event) => {
    if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
    event.preventDefault();
    const nextIndex = event.key === "Home" ? 0
      : event.key === "End" ? tabs.length - 1
        : (index + (event.key === "ArrowRight" ? 1 : -1) + tabs.length) % tabs.length;
    tabs[nextIndex].focus();
    selectPanel(tabs[nextIndex].dataset.authTab);
  }));

  document.querySelectorAll("[data-toggle-password]").forEach((button) => {
    button.addEventListener("click", () => {
      const input = document.getElementById(button.dataset.togglePassword);
      const reveal = input.type === "password";
      input.type = reveal ? "text" : "password";
      button.setAttribute("aria-label", reveal ? "Ocultar senha" : "Mostrar senha");
    });
  });

  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const notice = document.querySelector("#auth-notice");
    clearNotice(notice);
    setFormBusy(loginForm, true, "Entrando...");
    const formData = new FormData(loginForm);

    try {
      await loginAccount({ email: formData.get("email"), password: formData.get("password") });
      window.location.assign(getPostAuthDestination());
    } catch (error) {
      showNotice(notice, error.message || "Não foi possível entrar. Tente novamente.");
      setFormBusy(loginForm, false);
    }
  });

  registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const notice = document.querySelector("#auth-notice");
    clearNotice(notice);
    setFormBusy(registerForm, true, "Criando conta...");
    const formData = new FormData(registerForm);

    try {
      await registerAccount({
        name: formData.get("name"),
        email: formData.get("email"),
        phone: formData.get("phone"),
        password: formData.get("password"),
        confirmPassword: formData.get("confirmPassword"),
        acceptTerms: formData.get("acceptTerms") === "on",
      });
      window.location.assign(getPostAuthDestination());
    } catch (error) {
      showNotice(notice, error.message || "Não foi possível criar a conta. Tente novamente.");
      setFormBusy(registerForm, false);
    }
  });

  selectPanel("login");
}
