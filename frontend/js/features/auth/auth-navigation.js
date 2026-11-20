// Only allow the customer-area destination; all existing manager entry points
// continue to land on the management dashboard. "cliente.html" is still accepted
// so that old links (auth.html?next=cliente.html) keep working.
const CUSTOMER_AREA_NEXT = new Set(["cliente", "cliente.html"]);

export function getPostAuthDestination() {
  const next = new URLSearchParams(window.location.search).get("next");
  return CUSTOMER_AREA_NEXT.has(next) ? "cliente" : "gestao";
}
