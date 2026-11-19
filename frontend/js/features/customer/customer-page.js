import { signOut } from "../auth/auth-repository.js";
import {
  cancelCustomerAppointment,
  completeCustomerAppointmentPayment,
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
  confirmado: "Confirmado",
  "pronto-retirada": "Pronto para retirada",
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

/** Desabilita o botão enquanto a requisição roda, evitando duplo clique. */
async function withBusyButton(button, task) {
  if (!button || button.disabled) return undefined;
  button.disabled = true;
  button.setAttribute("aria-busy", "true");
  try {
    return await task();
  } finally {
    button.disabled = false;
    button.removeAttribute("aria-busy");
  }
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
  const openedPaymentAppointments = new Set();
  const paymentDialog = document.createElement("dialog");
  paymentDialog.className = "customer-dialog";
  paymentDialog.setAttribute("aria-labelledby", "appointment-payment-title");
  const paymentHeading = createTextElement("h2", "", "Seu veículo está pronto");
  paymentHeading.id = "appointment-payment-title";
  const paymentDescription = createTextElement("p", "", "");
  const paymentAmount = createTextElement("strong", "", "");
  paymentAmount.style.display = "block";
  paymentAmount.style.fontSize = "1.5rem";
  paymentAmount.style.margin = "20px 0 8px";
  const paymentHint = createTextElement("p", "", "Pagamento de demonstração: nenhuma cobrança real será feita.");
  const confirmPaymentButton = createTextElement("button", "customer-button customer-button-primary", "Confirmar pagamento simulado");
  confirmPaymentButton.type = "button";
  const deferPaymentButton = createTextElement("button", "customer-button customer-button-secondary", "Pagar depois");
  deferPaymentButton.type = "button";
  paymentDialog.append(paymentHeading, paymentDescription, paymentAmount, paymentHint, confirmPaymentButton, deferPaymentButton);
  document.body.append(paymentDialog);

  let paymentAppointmentId = null;

  let currentServices = [];

  function showNotice(message, type = "error") {
    notice.textContent = message;
    notice.dataset.type = type;
    notice.hidden = !message;
  }

  function openPayment(appointment) {
    paymentAppointmentId = appointment.id;
    paymentDescription.textContent = `${appointment.serviceName} · ${formatDate(appointment.date)} às ${appointment.time}`;
    paymentAmount.textContent = currency.format(Number(appointment.servicePrice) || 0);
    if (!paymentDialog.open) paymentDialog.showModal();
  }

  deferPaymentButton.addEventListener("click", () => paymentDialog.close());
  confirmPaymentButton.addEventListener("click", () => withBusyButton(confirmPaymentButton, async () => {
    if (!paymentAppointmentId) return;
    try {
      await completeCustomerAppointmentPayment(paymentAppointmentId);
      paymentDialog.close();
      showNotice("Pagamento simulado confirmado. Agendamento concluído.", "success");
      await renderAppointments();
    } catch (error) {
      showNotice(error.message || "Não foi possível concluir o pagamento simulado.");
    }
  }));

  async function loadProfile() {
    const profile = await getCustomerProfile();
    profileForm.elements.name.value = profile.name;
    profileForm.elements.phone.value = profile.phone;
    profileForm.elements.car.value = profile.car;
    profileForm.elements.brand.value = profile.brand;
    profileForm.elements.plate.value = profile.plate;
    document.querySelector("#customer-welcome-name").textContent = profile.name.split(" ")[0] || "cliente";
  }

  async function renderServices() {
    currentServices = await getAvailableServices();
    serviceSelect.replaceChildren(new Option("Selecione um serviço", ""));
    servicesList.replaceChildren();

    currentServices.forEach((service) => {
      const option = new Option(`${service.name} — ${currency.format(service.price)}`, String(service.id));
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

  async function openDetails(appointmentId) {
    const appointment = await getCustomerAppointment(appointmentId);
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

  async function openReschedule(appointmentId) {
    const appointment = await getCustomerAppointment(appointmentId);
    rescheduleForm.elements.appointmentId.value = String(appointment.id);
    rescheduleForm.elements.date.value = appointment.date;
    rescheduleForm.elements.time.value = appointment.time;
    rescheduleForm.elements.date.min = localDateValue();
    rescheduleDialog.showModal();
  }

  async function renderAppointments() {
    const appointments = await listCustomerAppointments();
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
      detailsButton.addEventListener("click", () => withBusyButton(detailsButton, async () => {
        try { await openDetails(appointment.id); } catch (error) { showNotice(error.message); }
      }));
      actions.append(detailsButton);

      if (appointment.status === "agendado") {
        const rescheduleButton = createTextElement("button", "customer-button customer-button-secondary", "Remarcar");
        rescheduleButton.type = "button";
        rescheduleButton.addEventListener("click", () => withBusyButton(rescheduleButton, async () => {
          try { await openReschedule(appointment.id); } catch (error) { showNotice(error.message); }
        }));
        actions.append(rescheduleButton);

        const cancelButton = createTextElement("button", "customer-button customer-button-danger", "Cancelar");
        cancelButton.type = "button";
        cancelButton.addEventListener("click", () => {
          if (!window.confirm("Deseja cancelar este agendamento?")) return;
          withBusyButton(cancelButton, async () => {
            try {
              await cancelCustomerAppointment(appointment.id);
              showNotice("Agendamento cancelado.", "success");
              await renderAppointments();
            } catch (error) {
              showNotice(error.message);
            }
          });
        });
        actions.append(cancelButton);
      }

      if (appointment.status === "pronto-retirada") {
        const payButton = createTextElement("button", "customer-button customer-button-primary", "Abrir pagamento");
        payButton.type = "button";
        payButton.addEventListener("click", () => openPayment(appointment));
        actions.append(payButton);
      }

      card.append(actions);
      appointmentsList.append(card);
    });

    const readyAppointment = appointments.find((appointment) => appointment.status === "pronto-retirada");
    if (readyAppointment && !openedPaymentAppointments.has(readyAppointment.id)) {
      openedPaymentAppointments.add(readyAppointment.id);
      openPayment(readyAppointment);
    }
  }

  profileForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const data = new FormData(profileForm);
    withBusyButton(event.submitter || profileForm.querySelector("[type=submit]"), async () => {
      try {
        const profile = await saveCustomerProfile({
          name: data.get("name"),
          phone: data.get("phone"),
          car: data.get("car"),
          brand: data.get("brand"),
          plate: data.get("plate"),
        });
        profileForm.elements.plate.value = profile.plate;
        document.querySelector("#customer-welcome-name").textContent = profile.name.split(" ")[0];
        showNotice("Perfil atualizado.", "success");
      } catch (error) {
        showNotice(error.message || "Não foi possível salvar o perfil.");
      }
    });
  });

  bookingForm.elements.date.min = localDateValue();
  bookingForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const data = new FormData(bookingForm);
    withBusyButton(event.submitter || bookingForm.querySelector("[type=submit]"), async () => {
      try {
        await createCustomerAppointment({
          serviceId: data.get("serviceId"),
          date: data.get("date"),
          time: data.get("time"),
        });
        bookingForm.reset();
        bookingForm.elements.date.min = localDateValue();
        showNotice("Agendamento criado.", "success");
        await renderAppointments();
        document.querySelector("#appointments").scrollIntoView({ behavior: "smooth", block: "start" });
      } catch (error) {
        showNotice(error.message || "Não foi possível criar o agendamento.");
      }
    });
  });

  rescheduleForm.elements.date.min = localDateValue();
  rescheduleForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const data = new FormData(rescheduleForm);
    withBusyButton(event.submitter || rescheduleForm.querySelector("[type=submit]"), async () => {
      try {
        await rescheduleCustomerAppointment(data.get("appointmentId"), {
          date: data.get("date"),
          time: data.get("time"),
        });
        rescheduleDialog.close();
        showNotice("Data e horário atualizados.", "success");
        await renderAppointments();
      } catch (error) {
        showNotice(error.message || "Não foi possível remarcar o agendamento.");
      }
    });
  });

  document.querySelectorAll("[data-close-dialog]").forEach((button) => {
    button.addEventListener("click", () => button.closest("dialog").close());
  });

  document.querySelector("#customer-sign-out").addEventListener("click", () => {
    signOut();
    window.location.replace("auth.html?next=cliente.html");
  });

  Promise.allSettled([loadProfile(), renderServices(), renderAppointments()]).then((results) => {
    const failure = results.find((result) => result.status === "rejected");
    if (failure) showNotice(failure.reason?.message || "Não foi possível carregar sua área do cliente.");
  });
}
