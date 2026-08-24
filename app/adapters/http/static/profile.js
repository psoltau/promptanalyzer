import { getProfile, saveArbeitsstand, startLauf, getCalls, getCall, getKeyStatus } from "./api.js";

const SPEICHER_VERZOEGERUNG_MS = 800;
const POLL_INTERVALL_MS = 1000;
const API_KEY_STORAGE = "prompting_analyzer_api_key";

let speicherTimer = null;
let pollTimer = null;

export async function renderProfile(app, profilId) {
  stoppePolling();
  const [profil, keyStatus] = await Promise.all([getProfile(profilId), getKeyStatus()]);
  app.innerHTML = vorlage(profil);
  fuelleFormular(app, profil.arbeitsstand);
  bindeFormular(app, profilId, keyStatus);
  aktualisiereKeyQuelle(app, keyStatus);
  await aktualisiereCalls(app, profilId);
}

function vorlage(profil) {
  return `
    <a href="#/">&larr; Profile</a>
    <h1>${escapeHtml(profil.name)}</h1>
    <p id="gespeichert-status">Arbeitsstand: ${profil.arbeitsstand_geaendert_am}</p>
    <form id="arbeitsstand-form">
      <label>System Prompt<br/><textarea id="system_prompt" rows="6" cols="80"></textarea></label><br/>
      <label>User Prompt<br/><textarea id="user_prompt" rows="6" cols="80"></textarea></label><br/>
      <label>Modell <input id="modell" type="text" placeholder="z.B. gpt-5" /></label><br/>
      <label>max_output_tokens <input id="max_output_tokens" type="number" min="1" /></label><br/>
      <label>reasoning_effort
        <select id="reasoning_effort">
          <option value="">(nicht gesetzt)</option>
          <option value="low">low</option>
          <option value="medium">medium</option>
          <option value="high">high</option>
        </select>
      </label><br/>
      <label>API-Key (optional, sonst OPENAI_API_KEY aus der Umgebung)
        <input id="api_key" type="password" />
      </label><br/>
      <p id="key-quelle"></p>
      <button type="submit">Ausführen</button>
    </form>
    <h2>Läufe</h2>
    <div id="calls"></div>
  `;
}

function fuelleFormular(app, arbeitsstand) {
  app.querySelector("#system_prompt").value = arbeitsstand.system_prompt;
  app.querySelector("#user_prompt").value = arbeitsstand.user_prompt;
  app.querySelector("#modell").value = arbeitsstand.modelle[0] || "";
  app.querySelector("#max_output_tokens").value = arbeitsstand.max_output_tokens ?? "";
  app.querySelector("#reasoning_effort").value = arbeitsstand.reasoning_effort || "";
  app.querySelector("#api_key").value = window.localStorage.getItem(API_KEY_STORAGE) || "";
}

function bindeFormular(app, profilId, keyStatus) {
  const felder = ["system_prompt", "user_prompt", "modell", "max_output_tokens", "reasoning_effort"];
  felder.forEach((id) => {
    app.querySelector(`#${id}`).addEventListener("input", () => planeSpeichern(app, profilId));
  });
  app.querySelector("#api_key").addEventListener("input", (event) => {
    window.localStorage.setItem(API_KEY_STORAGE, event.target.value);
    aktualisiereKeyQuelle(app, keyStatus);
  });
  app.querySelector("#arbeitsstand-form").addEventListener("submit", (event) => {
    event.preventDefault();
    ausfuehren(app, profilId);
  });
}

function aktualisiereKeyQuelle(app, keyStatus) {
  const eingetragen = app.querySelector("#api_key").value.trim();
  const anzeige = app.querySelector("#key-quelle");
  if (eingetragen) {
    anzeige.textContent = "Wirkender Key: eingetragenes Feld";
  } else if (keyStatus.umgebungs_key_vorhanden) {
    anzeige.textContent = "Wirkender Key: Umgebungsvariable OPENAI_API_KEY";
  } else {
    anzeige.textContent = "Wirkender Key: keiner (weder Feld noch Umgebung)";
  }
}

function planeSpeichern(app, profilId) {
  clearTimeout(speicherTimer);
  speicherTimer = setTimeout(() => speichern(app, profilId), SPEICHER_VERZOEGERUNG_MS);
}

async function speichern(app, profilId) {
  const arbeitsstand = liesFormular(app);
  const antwort = await saveArbeitsstand(profilId, arbeitsstand);
  app.querySelector("#gespeichert-status").textContent =
    `Arbeitsstand: gespeichert um ${antwort.arbeitsstand_geaendert_am}`;
}

function liesFormular(app) {
  const modell = app.querySelector("#modell").value.trim();
  const maxTokens = app.querySelector("#max_output_tokens").value;
  return {
    system_prompt: app.querySelector("#system_prompt").value,
    user_prompt: app.querySelector("#user_prompt").value,
    tools_json: null,
    modelle: modell ? [modell] : [],
    max_output_tokens: maxTokens ? Number(maxTokens) : null,
    reasoning_effort: app.querySelector("#reasoning_effort").value || null,
    web_suche: false,
    search_context_size: null,
    wiederholungen: 1,
  };
}

async function ausfuehren(app, profilId) {
  await speichern(app, profilId);
  const apiKey = app.querySelector("#api_key").value.trim() || null;
  await startLauf(profilId, apiKey);
  await aktualisiereCalls(app, profilId);
  startePolling(app, profilId);
}

function startePolling(app, profilId) {
  stoppePolling();
  pollTimer = setInterval(async () => {
    const laeuftNoch = await aktualisiereCalls(app, profilId);
    if (!laeuftNoch) stoppePolling();
  }, POLL_INTERVALL_MS);
}

function stoppePolling() {
  if (pollTimer) clearInterval(pollTimer);
  pollTimer = null;
}

async function aktualisiereCalls(app, profilId) {
  const daten = await getCalls(profilId);
  app.querySelector("#calls").innerHTML = renderCallsTabelle(daten);
  bindeCallZeilen(app);
  return daten.laeufe.some((lauf) => lauf.beendet_am === null);
}

function renderCallsTabelle(daten) {
  if (daten.calls.length === 0) return "<p>Noch keine Läufe.</p>";
  const zeilen = daten.calls.map(callZeile).join("");
  return `
    <table>
      <thead>
        <tr>
          <th>Lauf</th><th>Modell</th><th>#</th><th>Status</th>
          <th>Input</th><th>Cached</th><th>Reasoning</th><th>Output</th><th>Total</th>
          <th>Dauer (ms)</th>
        </tr>
      </thead>
      <tbody>${zeilen}</tbody>
    </table>
  `;
}

function callZeile(call) {
  const status =
    call.status === "incomplete" ? `incomplete (${call.incomplete_grund})` : call.status;
  return `
    <tr class="call-zeile" data-call-id="${call.id}">
      <td>${call.lauf_nummer}</td>
      <td>${escapeHtml(call.modell_name)}</td>
      <td>${call.wiederholung_index}</td>
      <td>${status}</td>
      <td>${call.input_tokens ?? ""}</td>
      <td>${call.cached_input_tokens ?? ""}</td>
      <td>${call.reasoning_tokens ?? ""}</td>
      <td>${call.output_tokens ?? ""}</td>
      <td>${call.total_tokens ?? ""}</td>
      <td>${call.dauer_ms}</td>
    </tr>
    <tr class="call-detail" data-call-detail="${call.id}" hidden><td colspan="10"></td></tr>
  `;
}

function bindeCallZeilen(app) {
  app.querySelectorAll(".call-zeile").forEach((zeile) => {
    zeile.addEventListener("click", () => zeigeCallDetail(app, zeile.dataset.callId));
  });
}

async function zeigeCallDetail(app, callId) {
  const detailZeile = app.querySelector(`[data-call-detail="${callId}"]`);
  const sichtbar = !detailZeile.hidden;
  if (sichtbar) {
    detailZeile.hidden = true;
    return;
  }
  const call = await getCall(callId);
  const zelle = detailZeile.querySelector("td");
  zelle.textContent = call.fehlertext
    ? `Fehler: ${call.fehlertext}`
    : call.antwort_text || "(leere Antwort)";
  detailZeile.hidden = false;
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}
