import { getActiveServices } from "../services/service-repository.js";
import {
  createAppointmentForManagement,
  listAppointmentsForManagement,
  listCustomersForManagement,
  updateAppointmentStatusForManagement,
} from "./customer-service.js";

const APPOINTMENTS_KEY = "lavaajato:demo:customer-appointments:v1";
const USERS_KEY = "lavaajato:demo:users:v1";
const SERVICES_KEY = "lavaajato:demo:services:v1";
const labels = {
  agendado: "Agendado",
  confirmado: "Confirmado",
  "pronto-retirada": "Pronto para retirada",
  concluido: "Concluído",
  cancelado: "Cancelado",
};

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

export function initSchedulePage() {
  const form = document.querySelector("form.form-grid");
  const customerSelect = form.elements.cliente;
  const vehicleSelect = form.elements.veiculo;
  const serviceSelect = form.elements.servico;
  const dateInput = form.elements.data;
  const timeInput = form.elements.hora;
  const table = document.querySelector(".tabela-wrap table");
  const body = table.querySelector("tbody") || table.createTBody();
  const heading = table.querySelector("thead tr");
  const notice = document.createElement("p");
  notice.id = "schedule-notice";
  notice.setAttribute("role", "status");
  notice.hidden = true;
  form.after(notice);
  dateInput.min = localDateValue();

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

  function renderOptions() {
    const customers = listCustomersForManagement();
    const selectedCustomer = customerSelect.value;
    customerSelect.replaceChildren(new Option("Selecione", ""));
    customers.forEach((customer) => customerSelect.add(new Option(customer.name, customer.id)));
    if (customers.some((customer) => customer.id === selectedCustomer)) customerSelect.value = selectedCustomer;

    const services = getActiveServices();
    const selectedService = serviceSelect.value;
    serviceSelect.replaceChildren(new Option("Selecione", ""));
    services.forEach((service) => serviceSelect.add(new Option(service.name, service.id)));
    if (services.some((service) => service.id === selectedService)) serviceSelect.value = selectedService;
    renderVehicles();
  }

  function renderVehicles() {
    const customer = listCustomersForManagement().find((item) => item.id === customerSelect.value);
    vehicleSelect.replaceChildren(new Option(customer?.car || "Selecione", customer?.car || ""));
    if (customer?.brand && customer.car) {
      vehicleSelect.options[0].textContent = `${customer.brand} ${customer.car}${customer.plate ? ` · ${customer.plate}` : ""}`;
    }
  }

  function renderAppointments() {
    const appointments = listAppointmentsForManagement();
    body.replaceChildren();

    if (!appointments.length) {
      const row = document.createElement("tr");
      const cell = addCell(row, "Nenhum agendamento encontrado.");
      cell.colSpan = heading.cells.length;
      body.append(row);
      return;
    }

    appointments.forEach((appointment, index) => {
      const row = document.createElement("tr");
      addCell(row, String(index + 1));
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
        const button = document.createElement("button");
        button.type = "button";
        button.className = "btn btn-sec";
        button.textContent = nextStatus[1];
        button.addEventListener("click", () => {
          try {
            updateAppointmentStatusForManagement(appointment.id, nextStatus[0]);
            showNotice(`Status atualizado: ${labels[nextStatus[0]]}.`, "success");
            renderAppointments();
          } catch (error) {
            showNotice(error.message || "Não foi possível atualizar o agendamento.");
          }
        });
        actions.append(button);
      } else {
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

  customerSelect.addEventListener("change", renderVehicles);
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    try {
      createAppointmentForManagement({
        customerId: customerSelect.value,
        serviceId: serviceSelect.value,
        date: dateInput.value,
        time: timeInput.value,
      });
      form.reset();
      dateInput.min = localDateValue();
      renderVehicles();
      renderAppointments();
      showNotice("Agendamento criado para o cliente.", "success");
    } catch (error) {
      showNotice(error.message || "Não foi possível criar o agendamento.");
    }
  });

  window.addEventListener("storage", (event) => {
    if (event.key === APPOINTMENTS_KEY) renderAppointments();
    if (event.key === USERS_KEY || event.key === SERVICES_KEY) renderOptions();
  });

  try {
    renderOptions();
    renderAppointments();
  } catch (error) {
    showNotice(error.message || "Não foi possível carregar a agenda.");
  }
}
