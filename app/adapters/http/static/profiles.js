import { listProfiles, createProfile, renameProfile, deleteProfile, duplicateProfile } from "./api.js";

export async function renderProfiles(app) {
  app.innerHTML = `
    <h1>Profile</h1>
    <p><a href="#/register">Modell-Register</a></p>
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
  liste.querySelectorAll("li").forEach((zeile) => verdrahteZeile(app, zeile));
}

function profilZeile(profil) {
  const zuletzt = profil.zuletzt_benutzt_am || "noch nie";
  return `
    <li data-profil-id="${profil.id}">
      <a href="#/profil/${profil.id}">${escapeHtml(profil.name)}</a>
      — ${profil.anzahl_laeufe} Läufe, zuletzt benutzt: ${zuletzt}
      <button type="button" class="umbenennen">Umbenennen</button>
      <button type="button" class="duplizieren">Duplizieren</button>
      <button type="button" class="loeschen">Löschen</button>
    </li>
  `;
}

function verdrahteZeile(app, zeile) {
  const profilId = zeile.dataset.profilId;
  zeile.querySelector(".umbenennen").addEventListener("click", () => umbenennen(app, zeile, profilId));
  zeile.querySelector(".duplizieren").addEventListener("click", () => duplizieren(profilId));
  zeile.querySelector(".loeschen").addEventListener("click", () => loeschen(app, profilId));
}

async function umbenennen(app, zeile, profilId) {
  const bisherigerName = zeile.querySelector("a").textContent;
  const neuerName = window.prompt("Neuer Name des Profils:", bisherigerName);
  if (neuerName === null || neuerName.trim() === "") return;
  await renameProfile(profilId, neuerName.trim());
  await ladeListe(app);
}

async function duplizieren(profilId) {
  const duplikat = await duplicateProfile(profilId);
  window.location.hash = `#/profil/${duplikat.id}`;
}

async function loeschen(app, profilId) {
  if (!window.confirm("Dieses Profil samt seiner gesamten Historie unwiderruflich löschen?")) return;
  await deleteProfile(profilId);
  await ladeListe(app);
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}
