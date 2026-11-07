import { isValidEmail, validateName, validatePassword } from "../../core/validation.js";
import { createAccount, signIn } from "./auth-repository.js";

export async function registerAccount(formData) {
  if (!validateName(formData.name)) throw new Error("Informe seu nome completo.");
  if (!isValidEmail(formData.email)) throw new Error("Informe um e-mail válido.");
  if (!formData.phone.trim()) throw new Error("Informe seu telefone.");

  const passwordError = validatePassword(formData.password);
  if (passwordError) throw new Error(passwordError);
  if (formData.password !== formData.confirmPassword) throw new Error("As senhas não conferem.");
  if (!formData.acceptTerms) throw new Error("Aceite os termos para continuar.");

  return createAccount(formData);
}

export async function loginAccount(formData) {
  if (!isValidEmail(formData.email)) throw new Error("Informe um e-mail válido.");
  if (!formData.password) throw new Error("Informe sua senha.");
  return signIn(formData);
}
