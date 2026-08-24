import { renderProfiles } from "./profiles.js";
import { renderProfile } from "./profile.js";
import { renderRegister } from "./register.js";

function route() {
  const hash = window.location.hash;
  const match = hash.match(/^#\/profil\/(.+)$/);
  const app = document.getElementById("app");
  if (hash === "#/register") {
    renderRegister(app);
  } else if (match) {
    renderProfile(app, match[1]);
  } else {
    renderProfiles(app);
  }
}

window.addEventListener("hashchange", route);
window.addEventListener("DOMContentLoaded", route);
