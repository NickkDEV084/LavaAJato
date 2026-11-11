import { deleteService, getServices, saveService } from "./service-repository.js";

const currency = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

export function initServicesPage() {
  const form = document.querySelector("#service-form");
  const body = document.querySelector("#services-list");
  const notice = document.querySelector("#services-notice");
  const submitButton = form.querySelector('[type="submit"]');

  function showError(message) {
    notice.textContent = message;
    notice.hidden = !message;
  }

  function render() {
    const services = getServices();
    body.replaceChildren();

    if (!services.length) {
      const row = document.createElement("tr");
      const cell = document.createElement("td");
      cell.colSpan = 5;
      cell.className = "empty-cell";
      cell.textContent = "Ainda não há serviços cadastrados.";
      row.append(cell);
      body.append(row);
      return;
    }

    services.forEach((service) => {
      const row = document.createElement("tr");
      const values = [service.name, service.description || "—", currency.format(Number(service.price) || 0), `${Number(service.duration) || 0} min`];
      values.forEach((value) => {
        const cell = document.createElement("td");
        cell.textContent = value;
        row.append(cell);
      });

      const actionsCell = document.createElement("td");
      const actions = document.createElement("div");
      actions.className = "service-actions";
      const edit = document.createElement("button");
      edit.type = "button";
      edit.className = "table-action";
      edit.textContent = "Editar";
      edit.addEventListener("click", () => {
        form.elements.id.value = service.id;
        form.elements.nome.value = service.name;
        form.elements.descricao.value = service.description || "";
        form.elements.preco.value = service.price;
        form.elements.duracao.value = service.duration;
        submitButton.textContent = "Salvar alterações";
        form.scrollIntoView({ behavior: "smooth", block: "start" });
        form.elements.nome.focus();
      });

      const remove = document.createElement("button");
      remove.type = "button";
      remove.className = "table-action table-action-danger";
      remove.textContent = "Remover";
      remove.addEventListener("click", () => {
        try {
          deleteService(service.id);
          showError("");
          render();
        } catch (error) {
          showError(error.message || "Não foi possível remover o serviço.");
        }
      });
      actions.append(edit, remove);
      actionsCell.append(actions);
      row.append(actionsCell);
      body.append(row);
    });
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    if (!form.reportValidity()) return;
    const data = new FormData(form);
    try {
      saveService({
        id: data.get("id"),
        name: data.get("nome"),
        description: data.get("descricao"),
        price: data.get("preco"),
        duration: data.get("duracao"),
      });
      form.reset();
      form.elements.id.value = "";
      submitButton.textContent = "Salvar serviço";
      showError("");
      render();
    } catch (error) {
      showError(error.message || "Não foi possível salvar o serviço.");
    }
  });

  form.addEventListener("reset", () => {
    window.setTimeout(() => {
      form.elements.id.value = "";
      submitButton.textContent = "Salvar serviço";
    });
  });

  window.addEventListener("storage", (event) => {
    if (event.key?.startsWith("lavaajato:demo:services:")) render();
  });

  try {
    render();
  } catch (error) {
    showError(error.message || "Não foi possível carregar os serviços.");
  }
}
