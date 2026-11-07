import { readJson, writeJson } from "../../core/storage.js";

const SERVICES_KEY = "lavaajato:demo:services:v1";
const STARTER_SERVICES = [
  {
    id: "service-simple",
    name: "Lavagem simples",
    description: "Lavagem externa e aspiração interna.",
    price: 30,
    duration: 30,
    active: true,
  },
];

function createId() {
  return globalThis.crypto?.randomUUID?.() ?? `servico-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export function getServices() {
  const services = readJson(localStorage, SERVICES_KEY, null);
  if (services === null) {
    writeJson(localStorage, SERVICES_KEY, STARTER_SERVICES);
    return STARTER_SERVICES;
  }
  if (!Array.isArray(services)) {
    throw new Error("A lista de serviços salva está inválida. Limpe os dados de demonstração e tente novamente.");
  }
  return services;
}

export function getActiveServices() {
  return getServices().filter((service) => service.active !== false);
}

export function saveService({ id, name, description, price, duration }) {
  const services = getServices();
  const service = {
    id: id || createId(),
    name: name.trim().replace(/\s+/g, " "),
    description: description.trim(),
    price: Number(price),
    duration: Number(duration),
    active: true,
  };
  const existingIndex = services.findIndex((item) => item.id === service.id);
  if (existingIndex >= 0) services.splice(existingIndex, 1, service);
  else services.unshift(service);
  writeJson(localStorage, SERVICES_KEY, services);
  return service;
}

export function deleteService(id) {
  writeJson(localStorage, SERVICES_KEY, getServices().filter((service) => service.id !== id));
}
