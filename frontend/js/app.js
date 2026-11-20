import { initAuthPage } from "./features/auth/auth-page.js";
import { getPostAuthDestination } from "./features/auth/auth-navigation.js";
import { getSession, signOut } from "./features/auth/auth-repository.js";
import { initClientPage } from "./features/requests/client-page.js";
import { initCustomerPage } from "./features/customer/customer-page.js";
import { initRequestsDashboard } from "./features/requests/dashboard-page.js";
import { initOrdersPage } from "./features/requests/orders-page.js";
import { initServicesPage } from "./features/services/services-page.js";
import { initSchedulePage } from "./features/customer/schedule-page.js";
import { initManagerNavigation } from "./features/navigation/manager-navigation.js";

const page = document.body.dataset.page;

if (page === "auth") {
  if (getSession()) {
    window.location.replace(getPostAuthDestination());
  } else {
    initAuthPage();
  }
} else if (page === "client") {
  initClientPage();
} else if (page === "customer-area") {
  if (!getSession()) {
    window.location.replace("auth?next=cliente");
  } else {
    initCustomerPage();
  }
} else {
  // Todas as páginas de gestão compartilham a sessão de demonstração existente.
  const session = getSession();
  if (!session) {
    window.location.replace("auth");
  } else {
    const header = document.querySelector(".topo");
    if (header) {
      header.classList.add("topo-com-sessao");
      const account = document.createElement("div");
      account.className = "sessao-usuario";
      account.innerHTML = '<span class="sessao-status" aria-hidden="true"></span><span class="sessao-nome"></span><button class="sessao-sair" type="button">Sair</button>';
      account.querySelector(".sessao-nome").textContent = session.user.name;
      account.querySelector(".sessao-sair").addEventListener("click", () => {
        signOut();
        window.location.replace("auth");
      });
      header.append(account);
    }

    // Inicializa somente as funções já implementadas nas telas anexadas.
    if (page === "orders") initOrdersPage();
    if (page === "schedule") initSchedulePage();
    if (page === "services") initServicesPage();
    if (page === "dashboard") initRequestsDashboard();

    initManagerNavigation(page);
  }
}
