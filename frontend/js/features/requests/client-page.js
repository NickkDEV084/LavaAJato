import { getActiveServices } from "../services/service-repository.js";
import { createRequest, getRequests } from "./request-repository.js";

const currency = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const dateTime = new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" });

function normalizeEmail(value) {
  return String(value || "").trim().toLocaleLowerCase("pt-BR");
}

function addTextCell(row, value) {
  const cell = document.createElement("span");
  cell.textContent = value;
  row.append(cell);
}

export function initClientPage() {
  const form = document.querySelector("#request-form");
  const serviceSelect = form.elements.servico;
  const serviceCards = document.querySelector("#client-services");
  const quote = document.querySelector("#request-quote");
  const notice = document.querySelector("#request-notice");
  const history = document.querySelector("#request-history");
  const emailInput = form.elements.email;
  const dateInput = form.elements.data;

  dateInput.min = new Date(Date.now() - new Date().getTimezoneOffset() * 60_000).toISOString().slice(0, 10);

  function showNotice(message, type = "error") {
    notice.textContent = message;
    notice.dataset.type = type;
    notice.hidden = !message;
  }

  function renderServices() {
    const currentValue = serviceSelect.value;
    const services = getActiveServices();
    serviceSelect.replaceChildren(new Option("Escolha um serviço", ""));
    serviceCards.replaceChildren();

    services.forEach((service) => {
      const option = new Option(`${service.name} · ${currency.format(Number(service.price) || 0)}`, service.id);
      serviceSelect.add(option);

      const card = document.createElement("article");
      card.className = "client-service-card";
      const title = document.createElement("h3");
      title.textContent = service.name;
      const description = document.createElement("p");
      description.textContent = service.description || "Um cuidado especial para o seu veículo.";
      const details = document.createElement("div");
      details.className = "client-service-details";
      const price = document.createElement("strong");
      price.textContent = currency.format(Number(service.price) || 0);
      const duration = document.createElement("span");
      duration.textContent = `${Number(service.duration) || 0} min`;
      details.append(price, duration);
      card.append(title, description, details);
      serviceCards.append(card);
    });

    if (services.some((service) => service.id === currentValue)) serviceSelect.value = currentValue;
    updateQuote();
    if (!services.length) {
      const empty = document.createElement("p");
      empty.className = "client-empty-services";
      empty.textContent = "Ainda não há serviços disponíveis. Tente novamente mais tarde.";
      serviceCards.append(empty);
    }
  }

  function updateQuote() {
    const service = getActiveServices().find((item) => item.id === serviceSelect.value);
    quote.textContent = service ? `${currency.format(Number(service.price) || 0)} · ${Number(service.duration) || 0} min` : "Selecione um serviço para ver o valor";
  }

  function renderHistory() {
    const email = normalizeEmail(emailInput.value);
    history.replaceChildren();
    if (!email) {
      const message = document.createElement("p");
      message.className = "history-hint";
      message.textContent = "Informe seu e-mail no formulário para consultar suas solicitações neste dispositivo.";
      history.append(message);
      return;
    }

    const requests = getRequests().filter((request) => normalizeEmail(request.client?.email) === email);
    if (!requests.length) {
      const message = document.createElement("p");
      message.className = "history-hint";
      message.textContent = "Nenhuma solicitação encontrada para este e-mail neste dispositivo.";
      history.append(message);
      return;
    }

    requests.forEach((request) => {
      const item = document.createElement("article");
      item.className = "history-item";
      const main = document.createElement("div");
      main.className = "history-item-main";
      addTextCell(main, request.service?.name || "Serviço");
      addTextCell(main, dateTime.format(new Date(request.scheduledAt)));
      const status = document.createElement("span");
      status.className = `request-status status-${(request.status || "Solicitado").toLocaleLowerCase("pt-BR").replaceAll(" ", "-")}`;
      status.textContent = request.status || "Solicitado";
      const number = document.createElement("small");
      number.textContent = `Pedido ${request.id.slice(-6).toUpperCase()}`;
      item.append(main, status, number);
      history.append(item);
    });
  }

  serviceSelect.addEventListener("change", updateQuote);
  emailInput.addEventListener("input", () => {
    try { renderHistory(); } catch (error) { showNotice(error.message); }
  });

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    if (!form.reportValidity()) return;

    try {
      const services = getActiveServices();
      const service = services.find((item) => item.id === serviceSelect.value);
      if (!service) {
        showNotice("Esse serviço não está mais disponível. Atualize a página e escolha outro.");
        renderServices();
        return;
      }

      const data = new FormData(form);
      const scheduledAt = new Date(`${data.get("data")}T${data.get("hora")}:00`);
      if (Number.isNaN(scheduledAt.getTime()) || scheduledAt.getTime() < Date.now()) {
        showNotice("Escolha uma data e horário futuros para solicitar o atendimento.");
        return;
      }

      const request = createRequest({
        client: {
          name: String(data.get("nome")).trim(),
          phone: String(data.get("telefone")).trim(),
          email: normalizeEmail(data.get("email")),
        },
        vehicle: {
          model: String(data.get("veiculo")).trim(),
          plate: String(data.get("placa")).trim().toLocaleUpperCase("pt-BR"),
        },
        service: {
          id: service.id,
          name: service.name,
          price: Number(service.price),
          duration: Number(service.duration),
        },
        scheduledAt: scheduledAt.toISOString(),
        notes: String(data.get("observacoes")).trim(),
      });

      const submittedEmail = request.client.email;
      showNotice(`Solicitação enviada! O código do seu pedido é ${request.id.slice(-6).toUpperCase()}. Acompanhe a confirmação nesta página.`, "success");
      form.reset();
      emailInput.value = submittedEmail;
      renderServices();
      renderHistory();
      history.scrollIntoView({ behavior: "smooth", block: "center" });
    } catch (error) {
      showNotice(error.message || "Não foi possível enviar sua solicitação. Tente novamente.");
    }
  });

  window.addEventListener("storage", (event) => {
    if (event.key === "lavaajato:demo:services:v1") {
      try { renderServices(); } catch (error) { showNotice(error.message); }
    }
    if (event.key === "lavaajato:demo:service-requests:v1") {
      try { renderHistory(); } catch (error) { showNotice(error.message); }
    }
  });

  try {
    renderServices();
    renderHistory();
  } catch (error) {
    showNotice(error.message || "Não foi possível carregar os dados da página.");
  }
}
