import { readJson, writeJson } from "../../core/storage.js";
import { getSession } from "../auth/auth-repository.js";
import { getActiveServices } from "../services/service-repository.js";

// Perfil e agendamentos ficam isolados aqui para facilitar a troca por uma API.
const USERS_KEY = "lavaajato:demo:users:v1";
const SESSION_KEY = "lavaajato:demo:session:v1";
const APPOINTMENTS_KEY = "lavaajato:demo:customer-appointments:v1";

function currentCustomerId() {
  const session = getSession();
  if (!session?.user?.id) throw new Error("Entre na sua conta para acessar esta área.");
  return session.user.id;
}

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

export function getCustomerProfile() {
  const customerId = currentCustomerId();
  const user = readUsers().find((item) => item.id === customerId);
  if (!user) throw new Error("Não foi possível localizar o perfil desta conta.");

  return {
    id: user.id,
    name: user.name || "",
    email: user.email || "",
    phone: user.phone || "",
    car: user.car || "",
    brand: user.brand || "",
    plate: user.plate || "",
  };
}

export function saveCustomerProfile({ name, phone, car, brand, plate }) {
  const customerId = currentCustomerId();
  const users = readUsers();
  const user = users.find((item) => item.id === customerId);
  if (!user) throw new Error("Não foi possível localizar o perfil desta conta.");

  const cleanName = String(name || "").trim().replace(/\s+/g, " ");
  const cleanPhone = String(phone || "").trim();
  if (cleanName.length < 2) throw new Error("Informe seu nome completo.");

  Object.assign(user, {
    name: cleanName,
    phone: cleanPhone,
    car: String(car || "").trim(),
    brand: String(brand || "").trim(),
    plate: String(plate || "").trim().toLocaleUpperCase("pt-BR"),
    updatedAt: new Date().toISOString(),
  });
  writeJson(localStorage, USERS_KEY, users);

  // O e-mail continua reservado à autenticação; só o nome é sincronizado aqui.
  const session = readJson(sessionStorage, SESSION_KEY, null);
  if (session?.user?.id === customerId) {
    session.user.name = cleanName;
    writeJson(sessionStorage, SESSION_KEY, session);
  }

  return getCustomerProfile();
}

export function getAvailableServices() {
  return getActiveServices().map((service) => ({
    id: service.id,
    name: service.name,
    description: service.description || "",
    price: Number(service.price) || 0,
    duration: Number(service.duration) || 0,
  }));
}

export function listCustomerAppointments() {
  const customerId = currentCustomerId();
  return readAppointments()
    .filter((appointment) => appointment.customerId === customerId)
    .sort((left, right) => `${left.date}T${left.time}`.localeCompare(`${right.date}T${right.time}`));
}

export function getCustomerAppointment(appointmentId) {
  const customerId = currentCustomerId();
  const appointment = readAppointments().find((item) => item.id === appointmentId && item.customerId === customerId);
  if (!appointment) throw new Error("Este agendamento não está disponível nesta conta.");
  return appointment;
}

export function createCustomerAppointment({ serviceId, date, time }) {
  const customerId = currentCustomerId();
  const profile = getCustomerProfile();
  validateSchedule(date, time);
  const service = getAvailableServices().find((item) => item.id === serviceId);
  if (!service) throw new Error("Escolha um serviço disponível.");

  const appointments = readAppointments();
  const appointment = {
    id: createId(),
    customerId,
    customerName: profile.name,
    customerPhone: profile.phone,
    car: profile.car,
    brand: profile.brand,
    plate: profile.plate,
    serviceId: service.id,
    serviceName: service.name,
    servicePrice: service.price,
    serviceDuration: service.duration,
    date,
    time,
    status: "agendado",
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };
  writeJson(localStorage, APPOINTMENTS_KEY, [appointment, ...appointments]);
  return appointment;
}

export function rescheduleCustomerAppointment(appointmentId, { date, time }) {
  const customerId = currentCustomerId();
  validateSchedule(date, time);
  const appointments = readAppointments();
  const appointment = appointments.find((item) => item.id === appointmentId && item.customerId === customerId);
  if (!appointment) throw new Error("Este agendamento não está disponível nesta conta.");
  if (appointment.status !== "agendado") throw new Error("Somente agendamentos ativos podem ser remarcados.");

  appointment.date = date;
  appointment.time = time;
  appointment.updatedAt = new Date().toISOString();
  writeJson(localStorage, APPOINTMENTS_KEY, appointments);
  return appointment;
}

export function cancelCustomerAppointment(appointmentId) {
  const customerId = currentCustomerId();
  const appointments = readAppointments();
  const appointment = appointments.find((item) => item.id === appointmentId && item.customerId === customerId);
  if (!appointment) throw new Error("Este agendamento não está disponível nesta conta.");
  if (appointment.status !== "agendado") throw new Error("Este agendamento não pode mais ser cancelado.");

  appointment.status = "cancelado";
  appointment.cancelledAt = new Date().toISOString();
  appointment.updatedAt = appointment.cancelledAt;
  writeJson(localStorage, APPOINTMENTS_KEY, appointments);
  return appointment;
}
