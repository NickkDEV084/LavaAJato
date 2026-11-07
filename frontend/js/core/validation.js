export function normalizeEmail(email) {
  return email.trim().toLocaleLowerCase("pt-BR");
}

export function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(normalizeEmail(email));
}

export function validatePassword(password) {
  if (password.length < 8) return "Use pelo menos 8 caracteres.";
  if (!/[A-Za-zÀ-ÿ]/.test(password) || !/\d/.test(password)) {
    return "Inclua pelo menos uma letra e um número.";
  }
  return "";
}

export function validateName(name) {
  return name.trim().replace(/\s+/g, " ").length >= 2;
}
