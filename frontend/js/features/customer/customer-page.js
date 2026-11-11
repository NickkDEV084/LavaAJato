import { signOut } from "../auth/auth-repository.js";
import {
  cancelCustomerAppointment,
  createCustomerAppointment,
  getAvailableServices,
  getCustomerAppointment,
  getCustomerProfile,
  listCustomerAppointments,
  rescheduleCustomerAppointment,
  saveCustomerProfile,
} from "./customer-service.js";

const currency = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const dateFormatter = new Intl.DateTimeFormat("pt-BR", { dateStyle: "long" });
const statusLabels = {
  agendado: "Agendado",
  cancelado: "Cancelado",
  concluido: "Concluído",
  "concluído": "Concluído",
};

function localDateValue(date = new Date()) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function formatDate(value) {
  return dateFormatter.format(new Date(`${value}T00:00:00`));
}

function createTextElement(tagName, className, text) {
  const element = document.createElement(tagName);
  if (className) element.className = className;
  element.textContent = text;
  return element;
}

export function initCustomerPage() {
  const notice = document.querySelector("#customer-notice");
  const profileForm = document.querySelector("#profile-form");
  const bookingForm = document.querySelector("#appointment-form");
  const appointmentsList = document.querySelector("#appointments-list");
  const appointmentsEmpty = document.querySelector("#appointments-empty");
  const serviceSelect = bookingForm.elements.serviceId;
  const servicesList = document.querySelector("#available-services-list");
  const detailsDialog = document.querySelector("#appointment-details-dialog");
  const rescheduleDialog = document.querySelector("#appointment-reschedule-dialog");
  const rescheduleForm = document.querySelector("#reschedule-form");

  let currentServices = [];

  function showNotice(message, type = "error") {
    notice.textContent = message;
    notice.dataset.type = type;
    notice.hidden = !message;
  }

  function loadProfile() {
    const profile = getCustomerProfile();
    profileForm.elements.name.value = profile.name;
    profileForm.elements.phone.value = profile.phone;
    profileForm.elements.car.value = profile.car;
    profileForm.elements.brand.value = profile.brand;
    profileForm.elements.plate.value = profile.plate;
    document.querySelector("#customer-welcome-name").textContent = profile.name.split(" ")[0] || "cliente";
  }

  function renderServices() {
    currentServices = getAvailableServices();
    serviceSelect.replaceChildren(new Option("Selecione um serviço", ""));
    servicesList.replaceChildren();

    currentServices.forEach((service) => {
      const option = new Option(`${service.name} — ${currency.format(service.price)}`, service.id);
      serviceSelect.append(option);

      const card = document.createElement("article");
      card.className = "customer-service-card";
      card.append(createTextElement("h3", "", service.name));
      card.append(createTextElement("p", "customer-service-description", service.description || "Serviço disponível para agendamento."));
      const details = document.createElement("div");
      details.className = "customer-service-details";
      details.append(createTextElement("strong", "", currency.format(service.price)));
      details.append(createTextElement("span", "", `${service.duration} min`));
      card.append(details);
      servicesList.append(card);
    });

    if (!currentServices.length) {
      servicesList.append(createTextElement("p", "customer-empty", "Não há serviços disponíveis para agendamento no momento."));
    }
  }

  function openDetails(appointmentId) {
    const appointment = getCustomerAppointment(appointmentId);
    document.querySelector("#details-service").textContent = appointment.serviceName;
    document.querySelector("#details-date").textContent = formatDate(appointment.date);
    document.querySelector("#details-time").textContent = appointment.time;
    document.querySelector("#details-status").textContent = statusLabels[appointment.status] || appointment.status;
    document.querySelector("#details-price").textContent = currency.format(Number(appointment.servicePrice) || 0);
    document.querySelector("#details-duration").textContent = `${Number(appointment.serviceDuration) || 0} min`;
    document.querySelector("#details-car").textContent = appointment.car || "—";
    document.querySelector("#details-brand").textContent = appointment.brand || "—";
    document.querySelector("#details-plate").textContent = appointment.plate || "—";
    detailsDialog.showModal();
  }

  function openReschedule(appointmentId) {
    const appointment = getCustomerAppointment(appointmentId);
    rescheduleForm.elements.appointmentId.value = appointment.id;
    rescheduleForm.elements.date.value = appointment.date;
    rescheduleForm.elements.time.value = appointment.time;
    rescheduleForm.elements.date.min = localDateValue();
    rescheduleDialog.showModal();
  }

  function renderAppointments() {
    const appointments = listCustomerAppointments();
    appointmentsList.replaceChildren();
    appointmentsEmpty.hidden = appointments.length > 0;

    appointments.forEach((appointment) => {
      const card = document.createElement("article");
      card.className = "appointment-card";

      const head = document.createElement("div");
      head.className = "appointment-card-head";
      head.append(createTextElement("h3", "", appointment.serviceName));
      const status = createTextElement(
        "span",
        `appointment-status status-${appointment.status}`,
        statusLabels[appointment.status] || appointment.status,
      );
      head.append(status);
      card.append(head);

      const summary = document.createElement("p");
      summary.className = "appointment-summary";
      summary.textContent = `${formatDate(appointment.date)} às ${appointment.time}`;
      card.append(summary);

      const actions = document.createElement("div");
      actions.className = "appointment-actions";
      const detailsButton = createTextElement("button", "customer-button customer-button-secondary", "Ver detalhes");
      detailsButton.type = "button";
      detailsButton.addEventListener("click", () => {
        try { openDetails(appointment.id); } catch (error) { showNotice(error.message); }
      });
      actions.append(detailsButton);

      if (appointment.status === "agendado") {
        const rescheduleButton = createTextElement("button", "customer-button customer-button-secondary", "Remarcar");
        rescheduleButton.type = "button";
        rescheduleButton.addEventListener("click", () => {
          try { openReschedule(appointment.id); } catch (error) { showNotice(error.message); }
        });
        actions.append(rescheduleButton);

        const cancelButton = createTextElement("button", "customer-button customer-button-danger", "Cancelar");
        cancelButton.type = "button";
        cancelButton.addEventListener("click", () => {
          if (!window.confirm("Deseja cancelar este agendamento?")) return;
          try {
            cancelCustomerAppointment(appointment.id);
            showNotice("Agendamento cancelado.", "success");
            renderAppointments();
          } catch (error) {
            showNotice(error.message);
          }
        });
        actions.append(cancelButton);
      }

      card.append(actions);
      appointmentsList.append(card);
    });
  }

  profileForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const data = new FormData(profileForm);
    try {
      const profile = saveCustomerProfile({
        name: data.get("name"),
        phone: data.get("phone"),
        car: data.get("car"),
        brand: data.get("brand"),
        plate: data.get("plate"),
      });
      document.querySelector("#customer-welcome-name").textContent = profile.name.split(" ")[0];
      showNotice("Perfil atualizado.", "success");
    } catch (error) {
      showNotice(error.message || "Não foi possível salvar o perfil.");
    }
  });

  bookingForm.elements.date.min = localDateValue();
  bookingForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const data = new FormData(bookingForm);
    try {
      createCustomerAppointment({
        serviceId: data.get("serviceId"),
        date: data.get("date"),
        time: data.get("time"),
      });
      bookingForm.reset();
      bookingForm.elements.date.min = localDateValue();
      showNotice("Agendamento criado.", "success");
      renderAppointments();
      document.querySelector("#appointments").scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (error) {
      showNotice(error.message || "Não foi possível criar o agendamento.");
    }
  });

  rescheduleForm.elements.date.min = localDateValue();
  rescheduleForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const data = new FormData(rescheduleForm);
    try {
      rescheduleCustomerAppointment(data.get("appointmentId"), {
        date: data.get("date"),
        time: data.get("time"),
      });
      rescheduleDialog.close();
      showNotice("Data e horário atualizados.", "success");
      renderAppointments();
    } catch (error) {
      showNotice(error.message || "Não foi possível remarcar o agendamento.");
    }
  });

  document.querySelectorAll("[data-close-dialog]").forEach((button) => {
    button.addEventListener("click", () => button.closest("dialog").close());
  });

  document.querySelector("#customer-sign-out").addEventListener("click", () => {
    signOut();
    window.location.replace("auth.html?next=cliente.html");
  });

  window.addEventListener("storage", (event) => {
    if (event.key === "lavaajato:demo:services:v1") renderServices();
    if (event.key === "lavaajato:demo:customer-appointments:v1") renderAppointments();
    if (event.key === "lavaajato:demo:users:v1") loadProfile();
  });

  try {
    loadProfile();
    renderServices();
    renderAppointments();
  } catch (error) {
    showNotice(error.message || "Não foi possível carregar sua área do cliente.");
  }
}
