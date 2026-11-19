import { getRequests, updateRequestStatus } from "./request-repository.js";

const currency = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const dateTime = new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" });

function addCell(row, value) {
  const cell = document.createElement("td");
  cell.textContent = value;
  row.append(cell);
  return cell;
}

function statusClass(status) {
  return `status-${String(status || "Solicitado").toLocaleLowerCase("pt-BR").replaceAll(" ", "-")}`;
}

export function initOrdersPage() {
  const body = document.querySelector("#requests-list");
  const table = document.querySelector(".requests-table");
  const empty = document.querySelector("#requests-empty");
  const notice = document.querySelector("#orders-notice");
  const total = document.querySelector("#request-total");
  const pending = document.querySelector("#request-pending");

  function render() {
    const requests = getRequests().sort((a, b) => new Date(a.scheduledAt) - new Date(b.scheduledAt));
    body.replaceChildren();
    empty.hidden = requests.length > 0;
    table.hidden = requests.length === 0;
    total.textContent = String(requests.length);
    pending.textContent = String(requests.filter((request) => request.status === "Solicitado").length);

    requests.forEach((request) => {
      const row = document.createElement("tr");
      addCell(row, request.client?.name || "Cliente");
      const contact = addCell(row, `${request.client?.phone || "—"}\n${request.client?.email || ""}`);
      contact.classList.add("contact-cell");
      addCell(row, [request.vehicle?.model, request.vehicle?.plate].filter(Boolean).join(" · ") || "—");
      addCell(row, `${request.service?.name || "Serviço"} · ${currency.format(Number(request.service?.price) || 0)}`);
      addCell(row, dateTime.format(new Date(request.scheduledAt)));

      const statusCell = addCell(row, "");
      const badge = document.createElement("span");
      badge.className = `request-status ${statusClass(request.status)}`;
      badge.textContent = request.status || "Solicitado";
      statusCell.append(badge);

      const actionsCell = addCell(row, "");
      const actions = document.createElement("div");
      actions.className = "request-actions";
      const nextActions = request.status === "Solicitado"
        ? [["Confirmado", "Confirmar", "btn-small"], ["Cancelado", "Cancelar", "btn-small btn-small-muted"]]
        : request.status === "Confirmado"
          ? [["Pronto para retirada", "Pronto p/ retirada", "btn-small"], ["Cancelado", "Cancelar", "btn-small btn-small-muted"]]
          : [];

      if (nextActions.length) {
        nextActions.forEach(([status, label, className]) => {
          const button = document.createElement("button");
          button.type = "button";
          button.className = className;
          button.textContent = label;
          button.addEventListener("click", () => {
            try {
              updateRequestStatus(request.id, status);
              notice.hidden = true;
              render();
            } catch (error) {
              notice.textContent = error.message || "Não foi possível atualizar a solicitação.";
              notice.hidden = false;
            }
          });
          actions.append(button);
        });
      } else {
        actions.textContent = "—";
      }
      actionsCell.append(actions);
      body.append(row);
    });
  }

  window.addEventListener("storage", (event) => {
    if (event.key === "lavaajato:demo:service-requests:v1") render();
  });

  try {
    render();
  } catch (error) {
    notice.textContent = error.message || "Não foi possível carregar as solicitações.";
    notice.hidden = false;
  }
}
