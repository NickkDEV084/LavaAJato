import { API_BASE_URL } from "../../core/config.js";
import { readJson, writeJson } from "../../core/storage.js";
import { getSession } from "../auth/auth-repository.js";
import { getActiveServices } from "../services/service-repository.js";

// Área do cliente: perfil, serviços e agendamentos vêm da API (/cliente/*).
// A conversão entre os nomes da API (português) e os do front fica nas funções "from/to Api" abaixo.
const SESSION_KEY = "lavaajato:demo:session:v1";
const OFFLINE_MESSAGE = "Não foi possível conectar ao servidor. Verifique sua conexão e tente novamente em instantes.";

export class ApiError extends Error {
  constructor(message, status, details = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

function currentCustomerId() {
  const session = getSession();
  if (!session?.user?.id) throw new Error("Entre na sua conta para acessar esta área.");
  return session.user.id;
}

async function apiRequest(path, { method = "GET", body } = {}) {
  const headers = { Accept: "application/json", "X-Usuario-Id": String(currentCustomerId()) };
  if (body !== undefined) headers["Content-Type"] = "application/json";

  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(OFFLINE_MESSAGE, 0);
  }

  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    const message = payload?.erro?.mensagem || "Não foi possível concluir a operação. Tente novamente.";
    throw new ApiError(message, response.status, payload?.erro?.detalhes ?? null);
  }
  return payload;
}

function toNumericId(value) {
  const id = Number(value);
  if (!Number.isInteger(id) || id <= 0) throw new Error("Este agendamento não está disponível nesta conta.");
  return id;
}

// --- Mapeamentos API <-> front ------------------------------------------------

function serviceFromApi(servico) {
  return {
    id: servico.id,
    name: servico.nome,
    description: servico.descricao || "",
    price: Number(servico.preco) || 0,
    duration: Number(servico.duracao_min) || 0,
  };
}

function profileFromApi(perfil) {
  return {
    id: perfil.id,
    name: perfil.nome || "",
    email: getSession()?.user?.email || "",
    phone: perfil.telefone || "",
    car: perfil.carro || "",
    brand: perfil.marca || "",
    plate: perfil.placa || "",
    createdAt: perfil.criado_em,
    updatedAt: perfil.atualizado_em,
  };
}

function profileToApi({ name, phone, car, brand, plate }) {
  return {
    nome: name,
    telefone: phone,
    carro: car,
    marca: brand,
    placa: plate,
  };
}

function appointmentFromApi(agendamento) {
  const cliente = agendamento.cliente || {};
  return {
    id: agendamento.id,
    customerId: cliente.id,
    customerName: cliente.nome || "",
    customerPhone: cliente.telefone || "",
    car: cliente.carro || "",
    brand: cliente.marca || "",
    plate: cliente.placa || "",
    serviceId: agendamento.servico_id,
    serviceName: agendamento.servico_nome,
    servicePrice: Number(agendamento.preco_snapshot) || 0,
    serviceDuration: Number(agendamento.duracao_snapshot_min) || 0,
    date: agendamento.data,
    time: agendamento.horario,
    status: agendamento.status,
    createdAt: agendamento.criado_em,
    updatedAt: agendamento.atualizado_em,
  };
}

function scheduleToApi({ date, time }) {
  return { data: date, horario: time };
}

function byDateTime(left, right) {
  return `${left.date}T${left.time}`.localeCompare(`${right.date}T${right.time}`);
}

// --- Área do cliente (API) ----------------------------------------------------

export async function getCustomerProfile() {
  try {
    return profileFromApi(await apiRequest("/cliente/perfil"));
  } catch (error) {
    if (!(error instanceof ApiError) || error.status !== 404) throw error;
    // Conta ainda sem perfil salvo no banco: parte dos dados da sessão de login.
    const user = getSession()?.user || {};
    return { id: null, name: user.name || "", email: user.email || "", phone: "", car: "", brand: "", plate: "" };
  }
}

export async function saveCustomerProfile({ name, phone, car, brand, plate }) {
  const customerId = currentCustomerId();
  const cleanName = String(name || "").trim().replace(/\s+/g, " ");
  if (cleanName.length < 2) throw new Error("Informe seu nome completo.");

  const profile = profileFromApi(await apiRequest("/cliente/perfil", {
    method: "PUT",
    body: profileToApi({
      name: cleanName,
      phone: String(phone || "").trim(),
      car: String(car || "").trim(),
      brand: String(brand || "").trim(),
      plate: String(plate || "").trim().toLocaleUpperCase("pt-BR"),
    }),
  }));

  // O e-mail continua reservado à autenticação; só o nome é sincronizado na sessão.
  const session = readJson(sessionStorage, SESSION_KEY, null);
  if (session?.user?.id === customerId) {
    session.user.name = profile.name;
    writeJson(sessionStorage, SESSION_KEY, session);
  }

  return profile;
}

export async function getAvailableServices() {
  const servicos = await apiRequest("/cliente/servicos");
  return servicos.map(serviceFromApi);
}

export async function listCustomerAppointments() {
  const agendamentos = await apiRequest("/cliente/agendamentos");
  return agendamentos.map(appointmentFromApi).sort(byDateTime);
}

export async function getCustomerAppointment(appointmentId) {
  return appointmentFromApi(await apiRequest(`/cliente/agendamentos/${toNumericId(appointmentId)}`));
}

export async function createCustomerAppointment({ serviceId, date, time }) {
  const servicoId = Number(serviceId);
  if (!Number.isInteger(servicoId) || servicoId <= 0) throw new Error("Escolha um serviço disponível.");
  if (!date || !time) throw new Error("Escolha uma data e um horário.");

  return appointmentFromApi(await apiRequest("/cliente/agendamentos", {
    method: "POST",
    body: { servico_id: servicoId, ...scheduleToApi({ date, time }) },
  }));
}

export async function rescheduleCustomerAppointment(appointmentId, { date, time }) {
  if (!date || !time) throw new Error("Escolha uma data e um horário.");
  return appointmentFromApi(await apiRequest(`/cliente/agendamentos/${toNumericId(appointmentId)}`, {
    method: "PATCH",
    body: scheduleToApi({ date, time }),
  }));
}

export async function cancelCustomerAppointment(appointmentId) {
  return appointmentFromApi(await apiRequest(`/cliente/agendamentos/${toNumericId(appointmentId)}/cancelar`, {
    method: "POST",
  }));
}

export async function completeCustomerAppointmentPayment(appointmentId) {
  return appointmentFromApi(await apiRequest(`/cliente/agendamentos/${toNumericId(appointmentId)}/pagar`, {
    method: "POST",
  }));
}

// --- Gestão (agenda.html) -----------------------------------------------------
// A API ainda não tem rotas de gestão; estas funções continuam no armazenamento local
// de demonstração para não quebrar schedule-page.js. Migrar quando houver /gestao/*.
const USERS_KEY = "lavaajato:demo:users:v1";
const APPOINTMENTS_KEY = "lavaajato:demo:customer-appointments:v1";

function readUsers() {
  const users = readJson(localStorage, USERS_KEY, []);
  if (!Array.isArray(users)) throw new Error("Não foi possível carregar os perfis salvos.");
  return users;
}

function readAppointments() {
  const appointments = readJson(localStorage, APPOINTMENTS_KEY, []);
  if (!Array.isArray(appointments)) throw new Error("Não foi possível carregar os agendamentos salvos.");
  return appointments;
}

function createId() {
  return globalThis.crypto?.randomUUID?.() ?? `agendamento-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function validateSchedule(date, time) {
  if (!date || !time) throw new Error("Escolha uma data e um horário.");
  const selected = new Date(`${date}T${time}`);
  if (Number.isNaN(selected.getTime())) throw new Error("A data ou o horário não são válidos.");
  if (selected < new Date()) throw new Error("Escolha uma data e um horário futuros.");
}

function localActiveServices() {
  return getActiveServices().map((service) => ({
    id: service.id,
    name: service.name,
    price: Number(service.price) || 0,
    duration: Number(service.duration) || 0,
  }));
}

export function listAppointmentsForManagement() {
  return readAppointments().sort(byDateTime);
}

export function listCustomersForManagement() {
  return readUsers().map((user) => ({
    id: user.id,
    name: user.name || "Cliente",
    phone: user.phone || "",
    car: user.car || "",
    brand: user.brand || "",
    plate: user.plate || "",
  }));
}

export function createAppointmentForManagement({ customerId, serviceId, date, time }) {
  validateSchedule(date, time);
  const customer = listCustomersForManagement().find((user) => user.id === customerId);
  if (!customer) throw new Error("Selecione um cliente cadastrado.");
  const service = localActiveServices().find((item) => item.id === serviceId);
  if (!service) throw new Error("Selecione um serviço disponível.");

  const now = new Date().toISOString();
  const appointment = {
    id: createId(),
    customerId: customer.id,
    customerName: customer.name,
    customerPhone: customer.phone,
    car: customer.car,
    brand: customer.brand,
    plate: customer.plate,
    serviceId: service.id,
    serviceName: service.name,
    servicePrice: service.price,
    serviceDuration: service.duration,
    date,
    time,
    status: "agendado",
    createdAt: now,
    updatedAt: now,
  };
  writeJson(localStorage, APPOINTMENTS_KEY, [appointment, ...readAppointments()]);
  return appointment;
}

export function updateAppointmentStatusForManagement(appointmentId, status) {
  const appointments = readAppointments();
  const appointment = appointments.find((item) => item.id === appointmentId);
  if (!appointment) throw new Error("Este agendamento não está mais disponível.");

  const allowedTransitions = {
    agendado: ["confirmado", "cancelado"],
    confirmado: ["pronto-retirada", "cancelado"],
  };
  if (!allowedTransitions[appointment.status]?.includes(status)) {
    throw new Error("Esta mudança de status não está disponível.");
  }

  appointment.status = status;
  appointment.updatedAt = new Date().toISOString();
  writeJson(localStorage, APPOINTMENTS_KEY, appointments);
  return appointment;
}
