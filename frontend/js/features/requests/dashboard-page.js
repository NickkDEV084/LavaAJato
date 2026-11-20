import { APPOINTMENT_STATUS_LABELS, listAllAppointments } from "../customer/customer-service.js";

// Painel da gestão: os agendamentos vêm da API (GET /api/agendamentos), nunca do localStorage.
const dateTime = new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" });

function addCell(row, value) {
  const cell = document.createElement("td");
  cell.textContent = value;
  row.append(cell);
  return cell;
}

export function initRequestsDashboard() {
  const body = document.querySelector("#dashboard-requests-list");
  const empty = document.querySelector("#dashboard-requests-empty");
  const table = document.querySelector("#dashboard-requests-table");
  const pending = document.querySelector("#dashboard-pending");
  const emptyText = empty.innerHTML;

  async function render() {
    const appointments = await listAllAppointments();
    const latest = [...appointments]
      .sort((a, b) => String(b.createdAt || "").localeCompare(String(a.createdAt || "")))
      .slice(0, 5);
    pending.textContent = String(appointments.filter((item) => item.status === "agendado").length);
    body.replaceChildren();
    empty.innerHTML = emptyText;
    empty.hidden = latest.length > 0;
    table.hidden = latest.length === 0;

    latest.forEach((item) => {
      const row = document.createElement("tr");
      addCell(row, item.customerName || "Cliente");
      addCell(row, [[item.brand, item.car].filter(Boolean).join(" "), item.plate].filter(Boolean).join(" · ") || "—");
      addCell(row, item.serviceName || "Serviço");
      addCell(row, dateTime.format(new Date(`${item.date}T${item.time}`)));
      const label = APPOINTMENT_STATUS_LABELS[item.status] || item.status;
      const statusCell = addCell(row, "");
      const badge = document.createElement("span");
      badge.className = `request-status status-${label.toLocaleLowerCase("pt-BR").replaceAll(" ", "-")}`;
      badge.textContent = label;
      statusCell.append(badge);
      body.append(row);
    });
  }

  async function refresh() {
    try {
      await render();
    } catch (error) {
      table.hidden = true;
      empty.hidden = false;
      empty.textContent = error.message || "Não foi possível carregar as solicitações.";
    }
  }

  // Ao voltar para a aba, recarrega da API (agendamentos feitos em outra aba ou aparelho).
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") refresh();
  });

  refresh();
}
