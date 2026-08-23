import { listProfiles, createProfile } from "./api.js";

export async function renderProfiles(app) {
  app.innerHTML = `
    <h1>Profile</h1>
    <form id="neues-profil">
      <input id="neuer-name" type="text" placeholder="Name des Profils" required />
      <button type="submit">Anlegen</button>
    </form>
    <ul id="profil-liste"></ul>
  `;

  app.querySelector("#neues-profil").addEventListener("submit", async (event) => {
    event.preventDefault();
    const eingabe = app.querySelector("#neuer-name");
    const profil = await createProfile(eingabe.value.trim());
    window.location.hash = `#/profil/${profil.id}`;
  });

  await ladeListe(app);
}

async function ladeListe(app) {
  const profile = await listProfiles();
  const liste = app.querySelector("#profil-liste");
  liste.innerHTML = profile.map(profilZeile).join("");
}

function profilZeile(profil) {
  const zuletzt = profil.zuletzt_benutzt_am || "noch nie";
  return `
    <li>
      <a href="#/profil/${profil.id}">${escapeHtml(profil.name)}</a>
      — ${profil.anzahl_laeufe} Läufe, zuletzt benutzt: ${zuletzt}
    </li>
  `;
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}
