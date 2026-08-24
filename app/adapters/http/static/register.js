import { getModelle, createModell, updateModell, deleteModell } from "./api.js";

export async function renderRegister(app) {
  app.innerHTML = registerMarkup();
  app.querySelector("#neues-modell").addEventListener("submit", (event) => {
    handleNeuesModell(event, app);
  });
  await ladeRegister(app);
}

function registerMarkup() {
  return `
    <h1>Modell-Register</h1>
    <p><a href="#/">Zurück zu den Profilen</a></p>
    <form id="neues-modell">
      <input id="neuer-modellname" type="text" placeholder="Modellname" required />
      <button type="submit">Anlegen</button>
    </form>
    <table>
      <thead>
        <tr>
          <th>Name</th>
          <th>Input ($/Mio. Tokens)</th>
          <th>Cached Input ($/Mio. Tokens)</th>
          <th>Output ($/Mio. Tokens)</th>
          <th>Suche ($/Anfrage)</th>
          <th>Kontextfenster</th>
          <th>reasoning_effort</th>
          <th>Web-Suche</th>
          <th>Prompt-Caching</th>
          <th></th>
        </tr>
      </thead>
      <tbody id="register-zeilen"></tbody>
    </table>
  `;
}

async function handleNeuesModell(event, app) {
  event.preventDefault();
  const eingabe = app.querySelector("#neuer-modellname");
  await createModell(eingabe.value.trim());
  eingabe.value = "";
  await ladeRegister(app);
}

async function ladeRegister(app) {
  const modelle = await getModelle();
  const koerper = app.querySelector("#register-zeilen");
  koerper.innerHTML = "";
  modelle.forEach((modell) => {
    koerper.insertAdjacentHTML("beforeend", modellZeile(modell));
    verdrahteZeile(app, koerper.lastElementChild, modell.name);
  });
}

function modellZeile(modell) {
  return `
    <tr>
      <td>${escapeHtml(modell.name)}</td>
      <td><input type="number" step="any" class="preis-input" value="${wertOderLeer(modell.preis_input)}" /></td>
      <td><input type="number" step="any" class="preis-cached-input" value="${wertOderLeer(modell.preis_cached_input)}" /></td>
      <td><input type="number" step="any" class="preis-output" value="${wertOderLeer(modell.preis_output)}" /></td>
      <td><input type="number" step="any" class="preis-suche" value="${wertOderLeer(modell.preis_suche)}" /></td>
      <td><input type="number" step="1" class="kontextfenster" value="${wertOderLeer(modell.kontextfenster)}" /></td>
      <td><input type="checkbox" class="erlaubt-reasoning-effort" ${checkedWenn(modell.erlaubt_reasoning_effort)} /></td>
      <td><input type="checkbox" class="erlaubt-web-suche" ${checkedWenn(modell.erlaubt_web_suche)} /></td>
      <td><input type="checkbox" class="unterstuetzt-prompt-caching" ${checkedWenn(modell.unterstuetzt_prompt_caching)} /></td>
      <td>
        <button type="button" class="speichern">Speichern</button>
        <button type="button" class="loeschen">Löschen</button>
      </td>
    </tr>
  `;
}

function verdrahteZeile(app, zeile, name) {
  zeile.querySelector(".speichern").addEventListener("click", async () => {
    await updateModell(name, zeileZuFeldern(zeile));
    await ladeRegister(app);
  });
  zeile.querySelector(".loeschen").addEventListener("click", async () => {
    await deleteModell(name);
    await ladeRegister(app);
  });
}

function zeileZuFeldern(zeile) {
  return {
    preis_input: leerZuNull(zeile.querySelector(".preis-input").value),
    preis_cached_input: leerZuNull(zeile.querySelector(".preis-cached-input").value),
    preis_output: leerZuNull(zeile.querySelector(".preis-output").value),
    preis_suche: leerZuNull(zeile.querySelector(".preis-suche").value),
    kontextfenster: leerZuNull(zeile.querySelector(".kontextfenster").value),
    erlaubt_reasoning_effort: zeile.querySelector(".erlaubt-reasoning-effort").checked,
    erlaubt_web_suche: zeile.querySelector(".erlaubt-web-suche").checked,
    unterstuetzt_prompt_caching: zeile.querySelector(".unterstuetzt-prompt-caching").checked,
  };
}

function leerZuNull(text) {
  return text === "" ? null : Number(text);
}

function wertOderLeer(wert) {
  return wert === null || wert === undefined ? "" : wert;
}

function checkedWenn(wert) {
  return wert ? "checked" : "";
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}
