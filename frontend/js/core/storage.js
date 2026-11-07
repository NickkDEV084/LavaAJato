/** Small JSON helpers. Keep storage access behind this module so it can be
 * replaced by an API repository without changing page code. */
export function readJson(storage, key, fallback = null) {
  try {
    const value = storage.getItem(key);
    return value === null ? fallback : JSON.parse(value);
  } catch {
    throw new Error("Não foi possível acessar os dados salvos neste navegador.");
  }
}

export function writeJson(storage, key, value) {
  try {
    storage.setItem(key, JSON.stringify(value));
  } catch {
    throw new Error("Não foi possível salvar os dados. Verifique o espaço disponível no navegador.");
  }
}

export function removeValue(storage, key) {
  try {
    storage.removeItem(key);
  } catch {
    throw new Error("Não foi possível encerrar a sessão neste navegador.");
  }
}
