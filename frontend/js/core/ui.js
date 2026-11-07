export function showNotice(element, message, type = "error") {
  element.textContent = message;
  element.dataset.type = type;
  element.hidden = false;
}

export function clearNotice(element) {
  element.textContent = "";
  element.hidden = true;
  delete element.dataset.type;
}

export function setFormBusy(form, busy, busyLabel = "Aguarde...") {
  const button = form.querySelector('[type="submit"]');
  if (!button) return;

  if (busy) {
    button.dataset.originalLabel = button.textContent;
    button.textContent = busyLabel;
    button.disabled = true;
    form.setAttribute("aria-busy", "true");
    return;
  }

  button.textContent = button.dataset.originalLabel || button.textContent;
  delete button.dataset.originalLabel;
  button.disabled = false;
  form.removeAttribute("aria-busy");
}
