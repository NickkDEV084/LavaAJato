import {
  APPOINTMENT_STATUS_LABELS,
  listAllAppointments,
  updateAppointmentStatusForManagement,
} from "../customer/customer-service.js";

// Pedidos da gestão: a lista vem de GET /api/agendamentos e as mudanças de status vão para
// /gestao/agendamentos/{id}/... (com a chave da gestão). Nada é guardado no localStorage.
const currency = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const dateTime = new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" });

const NEXT_ACTIONS = {
  agendado: [["confirmado", "Confirmar", "btn-small"], ["cancelado", "Cancelar", "btn-small btn-small-muted"]],
  confirmado: [["pronto-retirada", "Pronto p/ retirada", "btn-small"], ["cancelado", "Cancelar", "btn-small btn-small-muted"]],
};

function addCell(row, value) {
  const cell = document.createElement("td");
  cell.textContent = value;
  row.append(cell);
  return cell;
}

function statusLabel(status) {
  return APPOINTMENT_STATUS_LABELS[status] || status;
}

function statusClass(status) {
  return `status-${statusLabel(status).toLocaleLowerCase("pt-BR").replaceAll(" ", "-")}`;
}

export function initOrdersPage() {
  const body = document.querySelector("#requests-list");
  const table = document.querySelector(".requests-table");
  const empty = document.querySelector("#requests-empty");
  const notice = document.querySelector("#orders-notice");
  const total = document.querySelector("#request-total");
  const pending = document.querySelector("#request-pending");

  function showError(message) {
    notice.textContent = message;
    notice.hidden = !message;
  }

  async function render() {
    const appointments = await listAllAppointments();
    body.replaceChildren();
    empty.hidden = appointments.length > 0;
    table.hidden = appointments.length === 0;
    total.textContent = String(appointments.length);
    pending.textContent = String(appointments.filter((item) => item.status === "agendado").length);

    appointments.forEach((item) => {
      const row = document.createElement("tr");
      addCell(row, item.customerName || "Cliente");
      const contact = addCell(row, item.customerPhone || "—");
      contact.classList.add("contact-cell");
      addCell(row, [[item.brand, item.car].filter(Boolean).join(" "), item.plate].filter(Boolean).join(" · ") || "—");
      addCell(row, `${item.serviceName || "Serviço"} · ${currency.format(Number(item.servicePrice) || 0)}`);
      addCell(row, dateTime.format(new Date(`${item.date}T${item.time}`)));

      const statusCell = addCell(row, "");
      const badge = document.createElement("span");
      badge.className = `request-status ${statusClass(item.status)}`;
      badge.textContent = statusLabel(item.status);
      statusCell.append(badge);

      const actionsCell = addCell(row, "");
      const actions = document.createElement("div");
      actions.className = "request-actions";
      const nextActions = NEXT_ACTIONS[item.status] || [];

      if (nextActions.length) {
        nextActions.forEach(([status, label, className]) => {
          const button = document.createElement("button");
          button.type = "button";
          button.className = className;
          button.textContent = label;
          button.addEventListener("click", async () => {
            button.disabled = true;
            try {
              await updateAppointmentStatusForManagement(item.id, status);
              showError("");
              await render();
            } catch (error) {
              showError(error.message || "Não foi possível atualizar a solicitação.");
              button.disabled = false;
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

  async function refresh() {
    try {
      await render();
    } catch (error) {
      table.hidden = true;
      showError(error.message || "Não foi possível carregar as solicitações.");
    }
  }

  // Ao voltar para a aba, recarrega da API (agendamentos feitos em outra aba ou aparelho).
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") refresh();
  });

  refresh();
}
