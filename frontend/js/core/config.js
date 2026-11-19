/**
 * Configuração do front-end: endereço base da API.
 *
 * - Dev (front aberto pelo `python -m http.server 5500`): a API roda à parte em 127.0.0.1:8000.
 * - Qualquer outro caso (ex.: Render, ou o front servido pelo próprio FastAPI): a API está
 *   na mesma origem da página, então usamos caminho relativo ("" + "/cliente/...").
 */
const PORTA_FRONT_DEV = "5500";
const API_DEV = "http://127.0.0.1:8000";

export const API_BASE_URL = window.location.port === PORTA_FRONT_DEV ? API_DEV : "";
