// As mesmas seções alimentam o menu móvel e a indicação da página atual.
const sections = [
  { page: "dashboard", href: "gestao.html", label: "Painel", icon: "dashboard" },
  { page: "services", href: "servicos.html", label: "Serviços e preços", icon: "services" },
  { page: "schedule", href: "agenda.html", label: "Agenda e fila", icon: "calendar" },
  { page: "orders", href: "pedidos.html", label: "Pedidos e pagamentos", icon: "orders" },
  { page: "inventory", href: "produtos.html", label: "Produtos e estoque", icon: "inventory" },
  { page: "service-status", href: "status.html", label: "Status do serviço", icon: "status" },
  { page: "cancellations", href: "cancelamentos.html", label: "Cancelamentos", icon: "cancel" },
  { page: "reports", href: "relatorios.html", label: "Relatórios", icon: "reports" },
];

const quickSectionPages = new Set(["dashboard", "schedule", "orders", "reports"]);

const iconMarkup = {
  dashboard: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
  services: '<path d="M4 7h16M4 12h16M4 17h10"/><circle cx="7" cy="7" r="1"/><circle cx="17" cy="12" r="1"/>',
  calendar: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M7 3v4m10-4v4M3 10h18M7 14h3m-3 3h6"/>',
  orders: '<path d="M7 4H5a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2h-2M8 3h8v4H8zM7 12h10m-10 4h7"/>',
  inventory: '<path d="m3 7 9-4 9 4-9 4-9-4Zm0 0v10l9 4 9-4V7M12 11v10"/>',
  status: '<path d="m5 12 4 4L19 6"/><circle cx="12" cy="12" r="9"/>',
  cancel: '<circle cx="12" cy="12" r="9"/><path d="m9 9 6 6m0-6-6 6"/>',
  reports: '<path d="M4 20V11m8 9V4m8 16v-7"/><path d="M2 20h20"/>',
  client: '<path d="M14 4h6v6m0-6-9 9"/><path d="M18 13v5a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h5"/>',
  more: '<circle cx="5" cy="12" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/>',
};

function createIcon(name) {
  const icon = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  icon.setAttribute("viewBox", "0 0 24 24");
  icon.setAttribute("aria-hidden", "true");
  icon.setAttribute("focusable", "false");
  icon.innerHTML = iconMarkup[name] || iconMarkup.dashboard;
  return icon;
}

function createSectionLink(section, currentPage, className = "") {
  const link = document.createElement("a");
  link.className = `manager-nav-link ${className}`.trim();
  link.href = section.href;
  link.append(createIcon(section.icon));

  const label = document.createElement("span");
  label.textContent = section.label;
  link.append(label);

  if (section.page === currentPage) {
    link.classList.add("is-active");
    link.setAttribute("aria-current", "page");
  }

  return link;
}

// No celular, os quatro destinos mais usados ficam em um toque; os demais
// ficam no menu expansível, alcançável em dois toques a partir de qualquer tela.
export function initManagerNavigation(currentPage) {
  const backdrop = document.createElement("button");
  backdrop.className = "manager-menu-backdrop";
  backdrop.type = "button";
  backdrop.setAttribute("aria-label", "Fechar menu da gestão");
  backdrop.hidden = true;

  const panel = document.createElement("section");
  panel.id = "manager-navigation-menu";
  panel.className = "manager-menu-panel";
  panel.setAttribute("aria-label", "Seções da gestão");
  panel.hidden = true;

  const heading = document.createElement("h2");
  heading.className = "manager-menu-heading";
  heading.textContent = "Seções da gestão";
  panel.append(heading);

  const sectionList = document.createElement("nav");
  sectionList.className = "manager-menu-list";
  sectionList.setAttribute("aria-label", "Todas as seções");
  sections.forEach((section) => sectionList.append(createSectionLink(section, currentPage)));
  panel.append(sectionList);
  panel.append(createSectionLink(
    { href: "index.html", label: "Área do cliente", icon: "client" },
    currentPage,
    "manager-client-link",
  ));

  const bar = document.createElement("nav");
  bar.className = "manager-bottom-nav";
  bar.setAttribute("aria-label", "Navegação da gestão");
  const barItems = document.createElement("div");
  barItems.className = "manager-bottom-nav-items";

  sections.filter((section) => quickSectionPages.has(section.page)).forEach((section) => {
    barItems.append(createSectionLink(section, currentPage, "manager-bottom-nav-link"));
  });

  const moreButton = document.createElement("button");
  moreButton.className = "manager-nav-link manager-bottom-nav-link manager-nav-more";
  moreButton.type = "button";
  moreButton.setAttribute("aria-controls", panel.id);
  moreButton.setAttribute("aria-expanded", "false");
  moreButton.append(createIcon("more"));
  const moreLabel = document.createElement("span");
  moreLabel.textContent = "Menu";
  moreButton.append(moreLabel);
  if (!quickSectionPages.has(currentPage)) moreButton.classList.add("is-active");
  barItems.append(moreButton);
  bar.append(barItems);

  function closeMenu() {
    panel.hidden = true;
    backdrop.hidden = true;
    moreButton.setAttribute("aria-expanded", "false");
  }

  function toggleMenu() {
    const isOpen = moreButton.getAttribute("aria-expanded") === "true";
    panel.hidden = isOpen;
    backdrop.hidden = isOpen;
    moreButton.setAttribute("aria-expanded", String(!isOpen));
    if (!isOpen) panel.querySelector("a")?.focus();
  }

  moreButton.addEventListener("click", toggleMenu);
  backdrop.addEventListener("click", closeMenu);
  panel.addEventListener("click", (event) => {
    if (event.target.closest("a")) closeMenu();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape" || moreButton.getAttribute("aria-expanded") !== "true") return;
    closeMenu();
    moreButton.focus();
  });

  document.body.append(backdrop, panel, bar);
  addResponsiveTableLabels();
}

// No celular, transforma cada tabela em cartões rotulados, sem rolagem lateral.
function addResponsiveTableLabels() {
  document.querySelectorAll("table").forEach((table) => {
    const headers = [...table.querySelectorAll("thead th")].map((header) => header.textContent.trim());
    const labelRows = () => {
      table.querySelectorAll("tbody tr").forEach((row) => {
        [...row.cells].forEach((cell, index) => {
          if (!cell.hasAttribute("colspan") && headers[index]) cell.dataset.label = headers[index];
        });
      });
    };

    labelRows();
    const body = table.querySelector("tbody");
    if (body) new MutationObserver(labelRows).observe(body, { childList: true, subtree: true });
  });
}
