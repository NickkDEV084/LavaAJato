import { API_BASE_URL } from "../../core/config.js";
import { readJson, writeJson } from "../../core/storage.js";
import { getSession } from "../auth/auth-repository.js";

// Área do cliente (/cliente/*) e agenda da gestão (/gestao/*): os dados vêm da API.
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

async function sendRequest(path, { method = "GET", body, headers: extraHeaders = {} } = {}) {
  const headers = { Accept: "application/json", ...extraHeaders };
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

function apiRequest(path, options = {}) {
  return sendRequest(path, { ...options, headers: { "X-Usuario-Id": String(currentCustomerId()) } });
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

// --- API REST pública (/api/agendamentos) -------------------------------------
// Leitura aberta (sem chave), usada pelo Painel e pelos Pedidos da gestão.

export const APPOINTMENT_STATUS_LABELS = {
  agendado: "Agendado",
  confirmado: "Confirmado",
  "pronto-retirada": "Pronto para retirada",
  concluido: "Concluído",
  cancelado: "Cancelado",
};

function appointmentFromRestApi(item) {
  return {
    id: item.id,
    customerId: item.cliente_id,
    customerName: item.nome_cliente || "",
    customerPhone: item.telefone_cliente || "",
    car: item.carro || "",
    brand: item.marca || "",
    plate: item.placa || "",
    serviceId: item.servico_id,
    serviceName: item.servico,
    servicePrice: Number(item.preco) || 0,
    serviceDuration: Number(item.duracao_min) || 0,
    date: item.data,
    time: item.horario,
    status: item.status,
    createdAt: item.criado_em,
    updatedAt: item.atualizado_em,
  };
}

export async function listAllAppointments() {
  const agendamentos = await sendRequest("/api/agendamentos");
  return agendamentos.map(appointmentFromRestApi).sort(byDateTime);
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

// --- Gestão (agenda.html, API /gestao/*) -------------------------------------
// A chave da gestão fica só no sessionStorage desta aba e vai no header X-Chave-Gestao.
// Nunca é gravada no localStorage nem registrada no console.
const MANAGEMENT_KEY_STORAGE = "lavaajato:gestao:chave";
const MISSING_KEY_MESSAGE = "A agenda da gestão precisa da chave de acesso. Informe a chave para continuar.";
const MANAGEMENT_STATUS_ROUTES = {
  confirmado: "confirmar",
  "pronto-retirada": "pronto-retirada",
  cancelado: "cancelar",
};

function readManagementKey() {
  try {
    return sessionStorage.getItem(MANAGEMENT_KEY_STORAGE) || "";
  } catch {
    return "";
  }
}

function forgetManagementKey() {
  try {
    sessionStorage.removeItem(MANAGEMENT_KEY_STORAGE);
  } catch {
    // Sem sessionStorage disponível, não há chave guardada para apagar.
  }
}

export function hasManagementKey() {
  return Boolean(readManagementKey());
}

/** Devolve a chave guardada ou pede ao usuário; cancelar o prompt gera um ApiError de chave ausente. */
function requireManagementKey() {
  const saved = readManagementKey();
  if (saved) return saved;

  const typed = (window.prompt("Informe a chave da gestão para acessar a agenda:") || "").trim();
  if (!typed) throw new ApiError(MISSING_KEY_MESSAGE, 401);
  try {
    sessionStorage.setItem(MANAGEMENT_KEY_STORAGE, typed);
  } catch {
    // Sem sessionStorage a chave vale só para esta chamada; será pedida de novo.
  }
  return typed;
}

async function managementRequest(path, options = {}) {
  const key = requireManagementKey();
  try {
    return await sendRequest(path, { ...options, headers: { "X-Chave-Gestao": key } });
  } catch (error) {
    // Chave ausente ou errada: descarta para pedir de novo na próxima ação. 503 não mexe na chave.
    if (error instanceof ApiError && (error.status === 401 || error.status === 403)) forgetManagementKey();
    throw error;
  }
}

function customerFromApi(cliente) {
  return {
    id: cliente.id,
    name: cliente.nome || "Cliente",
    phone: cliente.telefone || "",
    car: cliente.carro || "",
    brand: cliente.marca || "",
    plate: cliente.placa || "",
  };
}

function positiveId(value, message) {
  const id = Number(value);
  if (!Number.isInteger(id) || id <= 0) throw new Error(message);
  return id;
}

export async function listServicesForManagement() {
  const servicos = await managementRequest("/gestao/servicos");
  return servicos.map(serviceFromApi);
}

export async function listAppointmentsForManagement() {
  const agendamentos = await managementRequest("/gestao/agendamentos");
  return agendamentos.map(appointmentFromApi).sort(byDateTime);
}

export async function listCustomersForManagement() {
  const clientes = await managementRequest("/gestao/clientes");
  return clientes.map(customerFromApi);
}

export async function createAppointmentForManagement({ customerId, serviceId, date, time }) {
  const clienteId = positiveId(customerId, "Selecione um cliente cadastrado.");
  const servicoId = positiveId(serviceId, "Selecione um serviço disponível.");
  if (!date || !time) throw new Error("Escolha uma data e um horário.");

  return appointmentFromApi(await managementRequest("/gestao/agendamentos", {
    method: "POST",
    body: { cliente_id: clienteId, servico_id: servicoId, ...scheduleToApi({ date, time }) },
  }));
}

export async function updateAppointmentStatusForManagement(appointmentId, status) {
  const route = MANAGEMENT_STATUS_ROUTES[status];
  if (!route) throw new Error("Esta mudança de status não está disponível.");
  const id = positiveId(appointmentId, "Este agendamento não está mais disponível.");
  return appointmentFromApi(await managementRequest(`/gestao/agendamentos/${id}/${route}`, { method: "POST" }));
}
