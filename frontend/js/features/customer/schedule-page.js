import {
  createAppointmentForManagement,
  listAppointmentsForManagement,
  listCustomersForManagement,
  listServicesForManagement,
  updateAppointmentStatusForManagement,
} from "./customer-service.js";

const labels = {
  agendado: "Agendado",
  confirmado: "Confirmado",
  "pronto-retirada": "Pronto para retirada",
  concluido: "Concluído",
  cancelado: "Cancelado",
};
// Só estes status entram na fila (coluna "Posição").
const ACTIVE_STATUSES = new Set(["agendado", "confirmado"]);
const CANCELLABLE_STATUSES = new Set(["agendado", "confirmado"]);

function localDateValue() {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
}

function addCell(row, value) {
  const cell = document.createElement("td");
  cell.textContent = value;
  row.append(cell);
  return cell;
}

function sameId(left, right) {
  return String(left) === String(right);
}

export function initSchedulePage() {
  const form = document.querySelector("form.form-grid");
  const customerSelect = form.elements.cliente;
  const vehicleSelect = form.elements.veiculo;
  const serviceSelect = form.elements.servico;
  const dateInput = form.elements.data;
  const timeInput = form.elements.hora;
  const submitButton = form.querySelector('[type="submit"]');
  const table = document.querySelector(".tabela-wrap table");
  const body = table.querySelector("tbody") || table.createTBody();
  const heading = table.querySelector("thead tr");
  const notice = document.createElement("p");
  notice.id = "schedule-notice";
  notice.setAttribute("role", "status");
  notice.hidden = true;
  form.after(notice);
  dateInput.min = localDateValue();

  let customers = [];
  let busy = false;
  let loaded = false;

  if (![...heading.cells].some((cell) => cell.textContent.trim() === "Status")) {
    const statusHeading = document.createElement("th");
    statusHeading.textContent = "Status";
    heading.append(statusHeading);
  }

  function showNotice(message, type = "error") {
    notice.textContent = message;
    notice.dataset.type = type;
    notice.hidden = !message;
  }

  /** Desabilita o formulário e os botões da lista enquanto uma requisição está em andamento. */
  function setBusy(value) {
    busy = value;
    submitButton.disabled = value;
    form.toggleAttribute("aria-busy", value);
    body.querySelectorAll("button").forEach((button) => { button.disabled = value; });
  }

  function fillSelect(select, items, label) {
    const selected = select.value;
    select.replaceChildren(new Option("Selecione", ""));
    items.forEach((item) => select.add(new Option(label(item), String(item.id))));
    if (items.some((item) => sameId(item.id, selected))) select.value = selected;
  }

  function renderVehicles() {
    // Mostra só o carro do cliente escolhido; o valor não é enviado à API.
    const customer = customers.find((item) => sameId(item.id, customerSelect.value));
    const option = new Option(customer?.car || "Selecione", customer?.car || "");
    if (customer?.brand && customer.car) {
      option.textContent = `${customer.brand} ${customer.car}${customer.plate ? ` · ${customer.plate}` : ""}`;
    }
    vehicleSelect.replaceChildren(option);
  }

  function renderMessageRow(message) {
    const row = document.createElement("tr");
    const cell = addCell(row, message);
    cell.colSpan = heading.cells.length;
    body.replaceChildren(row);
  }

  function renderAppointments(appointments) {
    body.replaceChildren();

    if (!appointments.length) {
      renderMessageRow("Nenhum agendamento encontrado.");
      return;
    }

    let position = 0;
    appointments.forEach((appointment) => {
      const row = document.createElement("tr");
      addCell(row, ACTIVE_STATUSES.has(appointment.status) ? String(++position) : "—");
      addCell(row, appointment.customerName || "Cliente");
      addCell(row, appointment.serviceName || "Serviço");
      addCell(row, `${appointment.date.split("-").reverse().join("/")} ${appointment.time}`);

      const actionsCell = addCell(row, "");
      const actions = document.createElement("div");
      actions.className = "request-actions";
      const nextStatus = appointment.status === "agendado"
        ? ["confirmado", "Confirmar"]
        : appointment.status === "confirmado"
          ? ["pronto-retirada", "Pronto p/ retirada"]
          : null;

      if (nextStatus) {
        actions.append(actionButton(nextStatus[1], () => changeStatus(appointment, nextStatus[0])));
      }
      if (CANCELLABLE_STATUSES.has(appointment.status)) {
        actions.append(actionButton("Cancelar", () => {
          const when = `${appointment.date.split("-").reverse().join("/")} às ${appointment.time}`;
          if (!window.confirm(`Cancelar o agendamento de ${appointment.customerName || "cliente"} em ${when}?`)) return;
          changeStatus(appointment, "cancelado");
        }));
      }
      if (!actions.childElementCount) {
        actions.textContent = appointment.status === "pronto-retirada" ? "Aguardando pagamento" : "—";
      }
      actionsCell.append(actions);

      const statusCell = addCell(row, "");
      const badge = document.createElement("span");
      badge.className = `request-status status-${appointment.status}`;
      badge.textContent = labels[appointment.status] || appointment.status;
      statusCell.append(badge);
      body.append(row);
    });
  }

  function actionButton(text, onClick) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "btn btn-sec";
    button.textContent = text;
    button.disabled = busy;
    button.addEventListener("click", onClick);
    return button;
  }

  async function refreshAppointments() {
    renderAppointments(await listAppointmentsForManagement());
  }

  /** Recarrega clientes, serviços e agendamentos. */
  async function loadAll() {
    setBusy(true);
    try {
      const [loadedCustomers, services] = await Promise.all([
        listCustomersForManagement(),
        listServicesForManagement(),
      ]);
      customers = loadedCustomers;
      fillSelect(customerSelect, customers, (customer) => customer.name);
      fillSelect(serviceSelect, services, (service) => service.name);
      renderVehicles();
      await refreshAppointments();
      loaded = true;
      return true;
    } catch (error) {
      if (!loaded) renderMessageRow("Agenda indisponível no momento.");
      showNotice(error.message || "Não foi possível carregar a agenda.");
      return false;
    } finally {
      setBusy(false);
    }
  }

  async function changeStatus(appointment, status) {
    if (busy) return;
    setBusy(true);
    try {
      await updateAppointmentStatusForManagement(appointment.id, status);
      showNotice(`Status atualizado: ${labels[status]}.`, "success");
      await refreshAppointments();
    } catch (error) {
      showNotice(error.message || "Não foi possível atualizar o agendamento.");
    } finally {
      setBusy(false);
    }
  }

  customerSelect.addEventListener("change", renderVehicles);
  form.addEventListener("reset", () => {
    // O reset nativo roda depois deste evento; o veículo é redesenhado em seguida.
    setTimeout(renderVehicles);
  });
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (busy) return;
    // Se a agenda ainda não carregou (ex.: servidor fora do ar), a próxima ação é carregá-la.
    if (!loaded) {
      if (await loadAll()) showNotice("Agenda carregada. Preencha os campos e agende novamente.", "success");
      return;
    }
    setBusy(true);
    try {
      await createAppointmentForManagement({
        customerId: customerSelect.value,
        serviceId: serviceSelect.value,
        date: dateInput.value,
        time: timeInput.value,
      });
      form.reset();
      dateInput.min = localDateValue();
      renderVehicles();
      showNotice("Agendamento criado para o cliente.", "success");
      await refreshAppointments();
    } catch (error) {
      showNotice(error.message || "Não foi possível criar o agendamento.");
    } finally {
      setBusy(false);
    }
  });

  // Ao voltar para a aba, busca de novo no banco.
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState !== "visible" || busy) return;
    loadAll();
  });

  loadAll();
}
