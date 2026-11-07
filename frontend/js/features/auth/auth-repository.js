import { readJson, removeValue, writeJson } from "../../core/storage.js";
import { normalizeEmail } from "../../core/validation.js";

const USERS_KEY = "lavaajato:demo:users:v1";
const SESSION_KEY = "lavaajato:demo:session:v1";
const HASH_ITERATIONS = 210_000;

function bytesToBase64(bytes) {
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary);
}

function base64ToBytes(value) {
  return Uint8Array.from(atob(value), (char) => char.charCodeAt(0));
}

function equalBytes(left, right) {
  if (left.length !== right.length) return false;
  let mismatch = 0;
  for (let index = 0; index < left.length; index += 1) mismatch |= left[index] ^ right[index];
  return mismatch === 0;
}

async function hashPassword(password, salt) {
  if (!globalThis.crypto?.subtle || !globalThis.crypto?.getRandomValues) {
    throw new Error("Abra o projeto pelo Live Server para habilitar a autenticação de demonstração.");
  }

  const key = await crypto.subtle.importKey("raw", new TextEncoder().encode(password), "PBKDF2", false, ["deriveBits"]);
  const digest = await crypto.subtle.deriveBits(
    { name: "PBKDF2", hash: "SHA-256", salt, iterations: HASH_ITERATIONS },
    key,
    256,
  );
  return new Uint8Array(digest);
}

function getUsers() {
  const users = readJson(localStorage, USERS_KEY, []);
  if (!Array.isArray(users)) throw new Error("Os dados de demonstração estão inválidos. Limpe os dados do site e tente novamente.");
  return users;
}

async function makePasswordRecord(password) {
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const hash = await hashPassword(password, salt);
  return { salt: bytesToBase64(salt), hash: bytesToBase64(hash), iterations: HASH_ITERATIONS };
}

async function verifyPassword(password, record) {
  try {
    const actual = await hashPassword(password, base64ToBytes(record.salt));
    return equalBytes(actual, base64ToBytes(record.hash));
  } catch {
    return false;
  }
}

function startSession(user) {
  const session = {
    user: { id: user.id, name: user.name, email: user.email },
    createdAt: new Date().toISOString(),
  };
  writeJson(sessionStorage, SESSION_KEY, session);
  return session;
}

export async function createAccount({ name, email, phone, password }) {
  const normalizedEmail = normalizeEmail(email);
  const users = getUsers();
  if (users.some((user) => normalizeEmail(user.email) === normalizedEmail)) {
    throw new Error("Já existe uma conta de demonstração com este e-mail.");
  }

  const passwordRecord = await makePasswordRecord(password);
  const user = {
    id: crypto.randomUUID(),
    name: name.trim().replace(/\s+/g, " "),
    email: normalizedEmail,
    phone: phone.trim(),
    password: passwordRecord,
    createdAt: new Date().toISOString(),
  };

  writeJson(localStorage, USERS_KEY, [...users, user]);
  return startSession(user);
}

export async function signIn({ email, password }) {
  const normalizedEmail = normalizeEmail(email);
  const user = getUsers().find((item) => normalizeEmail(item.email) === normalizedEmail);
  if (!user || !(await verifyPassword(password, user.password))) {
    throw new Error("E-mail ou senha incorretos.");
  }
  return startSession(user);
}

export function getSession() {
  const session = readJson(sessionStorage, SESSION_KEY, null);
  return session?.user?.id && session?.user?.name ? session : null;
}

export function signOut() {
  removeValue(sessionStorage, SESSION_KEY);
}
