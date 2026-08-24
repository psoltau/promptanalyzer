import { getProfile, saveArbeitsstand, startLauf, getCalls, getKeyStatus } from "./api.js";
import { zeigeCallDetail } from "./call_detail.js";

const SPEICHER_VERZOEGERUNG_MS = 800;
const POLL_INTERVALL_MS = 1000;
const API_KEY_STORAGE = "prompting_analyzer_api_key";
const KOSTEN_DEZIMALSTELLEN = 4;

const SPALTEN = [
  { key: "lauf_nummer", label: "Lauf" },
  { key: "modell_name", label: "Modell" },
  { key: "wiederholung_index", label: "#" },
  { key: "einstellungen", label: "Einstellungen" },
  { key: "status", label: "Status" },
  { key: "input_tokens", label: "Input" },
  { key: "cached_input_tokens", label: "Cached" },
  { key: "reasoning_tokens", label: "Reasoning" },
  { key: "output_tokens", label: "Output" },
  { key: "total_tokens", label: "Total" },
  { key: "kosten_usd", label: "Kosten (USD)" },
  { key: "dauer_ms", label: "Dauer (ms)" },
];

let speicherTimer = null;
let pollTimer = null;
let sortSpalte = null;
let sortAufsteigend = true;
let letzteLaeufe = [];
let letzteCalls = [];

export async function renderProfile(app, profilId) {
  stoppePolling();
  setzeSortierungZurueck();
  const [profil, keyStatus] = await Promise.all([getProfile(profilId), getKeyStatus()]);
  app.innerHTML = vorlage(profil);
  fuelleFormular(app, profil.arbeitsstand);
  bindeFormular(app, profilId, keyStatus);
  aktualisiereKeyQuelle(app, keyStatus);
  const laeuftNoch = await aktualisiereCalls(app, profilId);
  if (laeuftNoch) startePolling(app, profilId);
}

function setzeSortierungZurueck() {
  sortSpalte = null;
  sortAufsteigend = true;
}

function vorlage(profil) {
  return `
    <a href="#/">&larr; Profile</a>
    <h1>${escapeHtml(profil.name)}</h1>
    <p id="gespeichert-status">Arbeitsstand: ${profil.arbeitsstand_geaendert_am}</p>
    <form id="arbeitsstand-form">
      <label>System Prompt<br/><textarea id="system_prompt" rows="6" cols="80"></textarea></label><br/>
      <label>User Prompt<br/><textarea id="user_prompt" rows="6" cols="80"></textarea></label><br/>
      <label>Tool-Definitionen (JSON)<br/><textarea id="tools_json" rows="6" cols="80"></textarea></label>
      <p id="tools-json-fehler" class="feld-fehler"></p>
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
  app.querySelector("#tools_json").value = arbeitsstand.tools_json ?? "";
  app.querySelector("#modell").value = arbeitsstand.modelle[0] || "";
  app.querySelector("#max_output_tokens").value = arbeitsstand.max_output_tokens ?? "";
  app.querySelector("#reasoning_effort").value = arbeitsstand.reasoning_effort || "";
  app.querySelector("#api_key").value = window.localStorage.getItem(API_KEY_STORAGE) || "";
  pruefeToolsJson(app);
}

function bindeFormular(app, profilId, keyStatus) {
  const felder = ["system_prompt", "user_prompt", "tools_json", "modell", "max_output_tokens", "reasoning_effort"];
  felder.forEach((id) => {
    app.querySelector(`#${id}`).addEventListener("input", () => planeSpeichern(app, profilId));
  });
  app.querySelector("#tools_json").addEventListener("input", () => pruefeToolsJson(app));
  app.querySelector("#api_key").addEventListener("input", (event) => {
    window.localStorage.setItem(API_KEY_STORAGE, event.target.value);
    aktualisiereKeyQuelle(app, keyStatus);
  });
  app.querySelector("#arbeitsstand-form").addEventListener("submit", (event) => {
    event.preventDefault();
    ausfuehren(app, profilId);
  });
}

function pruefeToolsJson(app) {
  const wert = app.querySelector("#tools_json").value.trim();
  const anzeige = app.querySelector("#tools-json-fehler");
  if (!wert) {
    anzeige.textContent = "";
    return;
  }
  try {
    JSON.parse(wert);
    anzeige.textContent = "";
  } catch (fehler) {
    anzeige.textContent = `Ungültiges JSON: ${fehler.message}`;
  }
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
    tools_json: liesToolsJson(app),
    modelle: modell ? [modell] : [],
    max_output_tokens: maxTokens ? Number(maxTokens) : null,
    reasoning_effort: app.querySelector("#reasoning_effort").value || null,
    web_suche: false,
    search_context_size: null,
    wiederholungen: 1,
  };
}

function liesToolsJson(app) {
  const wert = app.querySelector("#tools_json").value;
  return wert.trim() ? wert : null;
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
  letzteLaeufe = daten.laeufe;
  letzteCalls = daten.calls.map(anreichern);
  renderUndBindeCalls(app);
  return daten.laeufe.some((lauf) => lauf.beendet_am === null);
}

function renderUndBindeCalls(app) {
  const sortiert = sortiereCalls(letzteCalls, sortSpalte, sortAufsteigend);
  app.querySelector("#calls").innerHTML = renderCallsBereich(letzteLaeufe, sortiert);
  bindeCallZeilen(app);
  bindeSortierHeader(app);
}

function anreichern(call) {
  return { ...call, einstellungen: einstellungenText(call) };
}

function einstellungenText(call) {
  const teile = [`max=${call.max_output_tokens ?? "–"}`];
  if (call.reasoning_effort) teile.push(`reasoning=${call.reasoning_effort}`);
  if (call.web_suche) teile.push("web_suche");
  if (call.search_context_size) teile.push(`suchkontext=${call.search_context_size}`);
  return teile.join(", ");
}

function sortiereCalls(calls, spalte, aufsteigend) {
  if (!spalte) return calls;
  const kopie = [...calls];
  kopie.sort((a, b) => vergleiche(a[spalte], b[spalte]) * (aufsteigend ? 1 : -1));
  return kopie;
}

function vergleiche(a, b) {
  if (typeof a === "number" && typeof b === "number") return a - b;
  return String(a ?? "").localeCompare(String(b ?? ""));
}

function bindeSortierHeader(app) {
  app.querySelectorAll("th[data-sort-key]").forEach((th) => {
    th.addEventListener("click", () => sortiereNach(app, th.dataset.sortKey));
  });
}

function sortiereNach(app, spalte) {
  if (sortSpalte === spalte) {
    sortAufsteigend = !sortAufsteigend;
  } else {
    sortSpalte = spalte;
    sortAufsteigend = true;
  }
  renderUndBindeCalls(app);
}

function renderCallsBereich(laeufe, calls) {
  if (calls.length === 0) return "<p>Noch keine Läufe.</p>";
  return renderFortschritt(laeufe) + renderCallsTabelle(calls);
}

function renderFortschritt(laeufe) {
  const laufende = laeufe.filter((lauf) => lauf.beendet_am === null);
  if (laufende.length === 0) return "";
  const zeilen = laufende.map(fortschrittsZeile).join("");
  return `<div id="fortschritt">${zeilen}</div>`;
}

function fortschrittsZeile(lauf) {
  return `<p>Lauf ${lauf.nummer}: ${lauf.fertige_calls} von ${lauf.erwartete_calls} Calls fertig</p>`;
}

function renderCallsTabelle(calls) {
  const kopfzeile = SPALTEN.map(kopfZelle).join("");
  const zeilen = calls.map(callZeile).join("");
  return `<table><thead><tr>${kopfzeile}</tr></thead><tbody>${zeilen}</tbody></table>`;
}

function kopfZelle(spalte) {
  const pfeil = sortSpalte === spalte.key ? (sortAufsteigend ? " ▲" : " ▼") : "";
  return `<th data-sort-key="${spalte.key}" class="sortierbar">${spalte.label}${pfeil}</th>`;
}

function callZeile(call) {
  return `
    <tr class="call-zeile" data-call-id="${call.id}">
      <td>${call.lauf_nummer}</td>
      <td>${escapeHtml(call.modell_name)}</td>
      <td>${call.wiederholung_index}</td>
      <td>${escapeHtml(call.einstellungen)}</td>
      <td><span class="${statusKlasse(call.status)}">${statusText(call)}</span></td>
      <td>${call.input_tokens ?? ""}</td>
      <td>${call.cached_input_tokens ?? ""}</td>
      <td>${call.reasoning_tokens ?? ""}</td>
      <td>${call.output_tokens ?? ""}</td>
      <td>${call.total_tokens ?? ""}</td>
      <td>${formatKosten(call.kosten_usd)}</td>
      <td>${call.dauer_ms ?? ""}</td>
    </tr>
    <tr class="call-detail" data-call-detail="${call.id}" hidden><td colspan="${SPALTEN.length}"></td></tr>
  `;
}

function statusText(call) {
  if (call.status === "incomplete") return `incomplete (${call.incomplete_grund})`;
  return call.status;
}

function statusKlasse(status) {
  return `status-${status}`;
}

function formatKosten(kosten) {
  return kosten === null || kosten === undefined ? "" : kosten.toFixed(KOSTEN_DEZIMALSTELLEN);
}

function bindeCallZeilen(app) {
  app.querySelectorAll(".call-zeile").forEach((zeile) => {
    zeile.addEventListener("click", () => zeigeCallDetail(app, zeile.dataset.callId));
  });
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}
