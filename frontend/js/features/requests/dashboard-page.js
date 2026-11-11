import { getRequests } from "./request-repository.js";

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

  function render() {
    const requests = getRequests();
    const latest = [...requests].sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt)).slice(0, 5);
    pending.textContent = String(requests.filter((request) => request.status === "Solicitado").length);
    body.replaceChildren();
    empty.hidden = latest.length > 0;
    table.hidden = latest.length === 0;

    latest.forEach((request) => {
      const row = document.createElement("tr");
      addCell(row, request.client?.name || "Cliente");
      addCell(row, [request.vehicle?.model, request.vehicle?.plate].filter(Boolean).join(" · ") || "—");
      addCell(row, request.service?.name || "Serviço");
      addCell(row, dateTime.format(new Date(request.scheduledAt)));
      const statusCell = addCell(row, "");
      const badge = document.createElement("span");
      badge.className = `request-status status-${String(request.status || "Solicitado").toLocaleLowerCase("pt-BR").replaceAll(" ", "-")}`;
      badge.textContent = request.status || "Solicitado";
      statusCell.append(badge);
      body.append(row);
    });
  }

  window.addEventListener("storage", (event) => {
    if (event.key === "lavaajato:demo:service-requests:v1") render();
  });

  try {
    render();
  } catch (error) {
    empty.hidden = false;
    empty.textContent = error.message || "Não foi possível carregar as solicitações.";
  }
}
