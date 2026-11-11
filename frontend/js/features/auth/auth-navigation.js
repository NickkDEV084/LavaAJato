// Only allow the customer-area destination; all existing manager entry points
// continue to land on the management dashboard.
export function getPostAuthDestination() {
  const next = new URLSearchParams(window.location.search).get("next");
  return next === "cliente.html" ? next : "gestao.html";
}
