import { readJson, writeJson } from "../../core/storage.js";

const REQUESTS_KEY = "lavaajato:demo:service-requests:v1";

function createId() {
  return globalThis.crypto?.randomUUID?.() ?? `solicitacao-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export function getRequests() {
  const requests = readJson(localStorage, REQUESTS_KEY, []);
  if (!Array.isArray(requests)) {
    throw new Error("A lista de solicitações salva está inválida. Limpe os dados de demonstração e tente novamente.");
  }
  return requests;
}

export function createRequest(data) {
  const request = {
    ...data,
    id: createId(),
    status: "Solicitado",
    createdAt: new Date().toISOString(),
  };
  writeJson(localStorage, REQUESTS_KEY, [request, ...getRequests()]);
  return request;
}

export function updateRequestStatus(id, status) {
  const requests = getRequests();
  const index = requests.findIndex((request) => request.id === id);
  if (index === -1) throw new Error("Esta solicitação não está mais disponível.");
  requests[index] = { ...requests[index], status, updatedAt: new Date().toISOString() };
  writeJson(localStorage, REQUESTS_KEY, requests);
}
