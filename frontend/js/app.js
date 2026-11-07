import { initAuthPage } from "./features/auth/auth-page.js";
import { getSession } from "./features/auth/auth-repository.js";
import { initClientPage } from "./features/requests/client-page.js";

const page = document.body.dataset.page;

if (page === "auth") {
  if (getSession()) {
    window.location.replace("index.html");
  } else {
    initAuthPage();
  }
} else if (page === "client") {
  initClientPage();
}