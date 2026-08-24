import {
  getProfile,
  saveArbeitsstand,
  startLauf,
  getCalls,
  getKeyStatus,
  getModelle,
  kostenNeuBerechnen,
  uebernehmeAusLauf,
} from "./api.js";
import { zeigeCallDetail } from "./call_detail.js";

const SPEICHER_VERZOEGERUNG_MS = 800;
const POLL_INTERVALL_MS = 1000;
const API_KEY_STORAGE = "prompting_analyzer_api_key";
const KOSTEN_DEZIMALSTELLEN = 4;
const CACHE_HINWEIS_TEXT =
  "Hinweis zur Spalte „Cached“: Prompt-Caching setzt bei der Responses API erst ab einem " +
  "gemeinsamen Prefix von etwa 1000 Tokens ein. Bei kurzen Testprompts bleibt der Wert deshalb " +
  "dauerhaft 0 — das liegt am Prompt, nicht am Modell oder am Werkzeug.";

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
  { key: "web_search_calls", label: "Suchanfragen" },
  { key: "kosten_usd", label: "Kosten (USD)" },
  { key: "dauer_ms", label: "Dauer (ms)" },
];

let speicherTimer = null;
let pollTimer = null;
let sortSpalte = null;
let sortAufsteigend = true;
let letzteLaeufe = [];
let letzteCalls = [];
let aktuellesProfilId = null;
let aktuelleModelle = [];

export async function renderProfile(app, profilId) {
  stoppePolling();
  setzeSortierungZurueck();
  const [profil, keyStatus, modelle] = await Promise.all([
    getProfile(profilId),
    getKeyStatus(),
    getModelle(),
  ]);
  aktuelleModelle = modelle;
  app.innerHTML = vorlage(profil);
  fuelleFormular(app, profil.arbeitsstand, modelle);
  bindeFormular(app, profilId, { keyStatus, modelle });
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
      <fieldset id="modelle-feld">
        <legend>Modelle</legend>
        <div id="modelle-auswahl"></div>
      </fieldset>
      <label>Wiederholungen <input id="wiederholungen" type="number" min="1" value="1" /></label><br/>
      <p id="call-vorschau"></p>
      <label>max_output_tokens <input id="max_output_tokens" type="number" min="1" /></label><br/>
      <label>reasoning_effort
        <select id="reasoning_effort">
          <option value="">(nicht gesetzt)</option>
          <option value="low">low</option>
          <option value="medium">medium</option>
          <option value="high">high</option>
        </select>
      </label><br/>
      <label>Web-Suche <input id="web_suche" type="checkbox" /></label><br/>
      <label>search_context_size
        <select id="search_context_size">
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

function fuelleFormular(app, arbeitsstand, modelle) {
  app.querySelector("#system_prompt").value = arbeitsstand.system_prompt;
  app.querySelector("#user_prompt").value = arbeitsstand.user_prompt;
  app.querySelector("#tools_json").value = arbeitsstand.tools_json ?? "";
  fuelleModelleAuswahl(app, modelle, arbeitsstand.modelle);
  app.querySelector("#wiederholungen").value = arbeitsstand.wiederholungen ?? 1;
  app.querySelector("#max_output_tokens").value = arbeitsstand.max_output_tokens ?? "";
  app.querySelector("#reasoning_effort").value = arbeitsstand.reasoning_effort || "";
  app.querySelector("#web_suche").checked = arbeitsstand.web_suche;
  app.querySelector("#search_context_size").value = arbeitsstand.search_context_size || "";
  app.querySelector("#api_key").value = window.localStorage.getItem(API_KEY_STORAGE) || "";
  pruefeToolsJson(app);
  wendeGatingAn(app, modelle);
  aktualisiereVorschau(app);
}

function fuelleModelleAuswahl(app, modelle, ausgewaehlteNamen) {
  app.querySelector("#modelle-auswahl").innerHTML = modelleAuswahlMarkup(modelle, ausgewaehlteNamen);
}

function modelleAuswahlMarkup(modelle, ausgewaehlteNamen) {
  const bekannteNamen = modelle.map((modell) => modell.name);
  const boxen = modelle.map((modell) => modellCheckboxMarkup(modell, ausgewaehlteNamen.includes(modell.name)));
  const unbekannte = ausgewaehlteNamen
    .filter((name) => !bekannteNamen.includes(name))
    .map(unbekannteModellCheckboxMarkup);
  const alle = [...boxen, ...unbekannte].join("");
  return alle || "<p>Kein Modell im Register.</p>";
}

function modellCheckboxMarkup(modell, ausgewaehlt) {
  const hinweis = modell.preise_vollstaendig ? "" : " — keine Preise gepflegt";
  return modellCheckboxLabel(modell.name, ausgewaehlt, hinweis);
}

function unbekannteModellCheckboxMarkup(name) {
  return modellCheckboxLabel(name, true, " — nicht im Register");
}

function modellCheckboxLabel(name, ausgewaehlt, hinweis) {
  const attribut = ausgewaehlt ? "checked" : "";
  return `<label><input type="checkbox" class="modell-checkbox" value="${escapeHtml(name)}" ${attribut} /> ${escapeHtml(name)}${hinweis}</label><br/>`;
}

function liesAusgewaehlteModellNamen(app) {
  return Array.from(app.querySelectorAll(".modell-checkbox:checked")).map((box) => box.value);
}

function bindeFormular(app, profilId, kontext) {
  const felder = [
    "system_prompt",
    "user_prompt",
    "tools_json",
    "max_output_tokens",
    "reasoning_effort",
    "wiederholungen",
    "web_suche",
    "search_context_size",
  ];
  felder.forEach((id) => {
    app.querySelector(`#${id}`).addEventListener("input", () => planeSpeichern(app, profilId));
  });
  app.querySelector("#wiederholungen").addEventListener("input", () => aktualisiereVorschau(app));
  app.querySelector("#modelle-auswahl").addEventListener("change", () => {
    wendeGatingAn(app, kontext.modelle);
    aktualisiereVorschau(app);
    planeSpeichern(app, profilId);
  });
  app.querySelector("#tools_json").addEventListener("input", () => pruefeToolsJson(app));
  app.querySelector("#api_key").addEventListener("input", (event) => {
    window.localStorage.setItem(API_KEY_STORAGE, event.target.value);
    aktualisiereKeyQuelle(app, kontext.keyStatus);
  });
  app.querySelector("#arbeitsstand-form").addEventListener("submit", (event) => {
    event.preventDefault();
    ausfuehren(app, profilId);
  });
}

function wendeGatingAn(app, modelle) {
  const ausgewaehlteModelle = liesAusgewaehlteModellNamen(app).map((name) => findeModell(modelle, name));
  const reasoningErlaubt = ausgewaehlteModelle.every((modell) => istErlaubt(modell, "erlaubt_reasoning_effort"));
  const webSucheErlaubt = ausgewaehlteModelle.every((modell) => istErlaubt(modell, "erlaubt_web_suche"));
  setzeFeldGating(app.querySelector("#reasoning_effort"), reasoningErlaubt);
  setzeFeldGating(app.querySelector("#web_suche"), webSucheErlaubt);
  setzeFeldGating(app.querySelector("#search_context_size"), webSucheErlaubt);
}

function findeModell(modelle, name) {
  return modelle.find((modell) => modell.name === name) || null;
}

function istErlaubt(modell, faehigkeitsschalter) {
  return modell === null || modell[faehigkeitsschalter];
}

function setzeFeldGating(feld, erlaubt) {
  feld.disabled = !erlaubt;
  if (erlaubt) return;
  if (feld.type === "checkbox") {
    feld.checked = false;
  } else {
    feld.value = "";
  }
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
  const maxTokens = app.querySelector("#max_output_tokens").value;
  return {
    system_prompt: app.querySelector("#system_prompt").value,
    user_prompt: app.querySelector("#user_prompt").value,
    tools_json: liesToolsJson(app),
    modelle: liesAusgewaehlteModellNamen(app),
    max_output_tokens: maxTokens ? Number(maxTokens) : null,
    reasoning_effort: liesGegatetesFeld(app, "#reasoning_effort"),
    web_suche: liesGegatetesCheckbox(app, "#web_suche"),
    search_context_size: liesGegatetesFeld(app, "#search_context_size"),
    wiederholungen: liesWiederholungen(app),
  };
}

function liesWiederholungen(app) {
  const wert = Math.trunc(Number(app.querySelector("#wiederholungen").value));
  return Number.isFinite(wert) && wert >= 1 ? wert : 1;
}

function aktualisiereVorschau(app) {
  const anzahlModelle = liesAusgewaehlteModellNamen(app).length;
  const wiederholungen = liesWiederholungen(app);
  const anzahlCalls = anzahlModelle * wiederholungen;
  app.querySelector("#call-vorschau").textContent =
    `Vorschau: ${anzahlModelle} Modell(e) × ${wiederholungen} Wiederholung(en) = ${anzahlCalls} Call(s)`;
}

function liesGegatetesFeld(app, selector) {
  const feld = app.querySelector(selector);
  return feld.disabled ? null : feld.value || null;
}

function liesGegatetesCheckbox(app, selector) {
  const feld = app.querySelector(selector);
  return feld.disabled ? false : feld.checked;
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
  aktuellesProfilId = profilId;
  const daten = await getCalls(profilId);
  letzteLaeufe = daten.laeufe;
  letzteCalls = daten.calls.map(anreichern);
  renderUndBindeCalls(app, profilId);
  return daten.laeufe.some((lauf) => lauf.beendet_am === null);
}

function renderUndBindeCalls(app, profilId) {
  const sortiert = sortiereCalls(letzteCalls, sortSpalte, sortAufsteigend);
  app.querySelector("#calls").innerHTML = renderCallsBereich(letzteLaeufe, sortiert);
  bindeCallZeilen(app);
  bindeSortierHeader(app, profilId);
  bindeKostenNeuberechnenKnoepfe(app);
  bindeLaufUebernahme(app, profilId);
}

function bindeKostenNeuberechnenKnoepfe(app) {
  app.querySelectorAll(".kosten-neuberechnen").forEach((knopf) => {
    knopf.addEventListener("click", () => neuBerechnen(app, knopf.dataset.laufId));
  });
}

async function neuBerechnen(app, laufId) {
  await kostenNeuBerechnen(laufId);
  await aktualisiereCalls(app, aktuellesProfilId);
}

function bindeLaufUebernahme(app, profilId) {
  app.querySelectorAll(".aus-lauf-uebernehmen").forEach((button) => {
    button.addEventListener("click", () => {
      handhabeUebernahme(app, profilId, button.dataset.laufId, button.dataset.laufNummer);
    });
  });
}

async function handhabeUebernahme(app, profilId, laufId, laufNummer) {
  const warnung =
    `Der aktuelle Arbeitsstand wird durch den Stand aus Lauf ${laufNummer} überschrieben. ` +
    "Fortfahren?";
  if (!window.confirm(warnung)) return;
  await uebernehmeAusLauf(profilId, laufId);
  const profil = await getProfile(profilId);
  fuelleFormular(app, profil.arbeitsstand, aktuelleModelle);
  app.querySelector("#gespeichert-status").textContent =
    `Arbeitsstand: gespeichert um ${profil.arbeitsstand_geaendert_am}`;
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

function bindeSortierHeader(app, profilId) {
  app.querySelectorAll("th[data-sort-key]").forEach((th) => {
    th.addEventListener("click", () => sortiereNach(app, profilId, th.dataset.sortKey));
  });
}

function sortiereNach(app, profilId, spalte) {
  if (sortSpalte === spalte) {
    sortAufsteigend = !sortAufsteigend;
  } else {
    sortSpalte = spalte;
    sortAufsteigend = true;
  }
  renderUndBindeCalls(app, profilId);
}

function renderCallsBereich(laeufe, calls) {
  if (laeufe.length === 0) return "<p>Noch keine Läufe.</p>";
  return (
    renderFortschritt(laeufe) +
    renderLaufListe(laeufe) +
    renderCacheHinweis() +
    renderCallsTabelle(laeufe, calls)
  );
}

function renderCacheHinweis() {
  return `<p class="cache-hinweis">${escapeHtml(CACHE_HINWEIS_TEXT)}</p>`;
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

function renderLaufListe(laeufe) {
  const zeilen = [...laeufe].reverse().map(laufZeile).join("");
  return `
    <table class="lauf-liste">
      <thead><tr><th>Lauf</th><th>Gestartet</th><th>Beendet</th><th>Kosten (USD)</th><th></th></tr></thead>
      <tbody>${zeilen}</tbody>
    </table>
  `;
}

function laufZeile(lauf) {
  return `
    <tr>
      <td>${lauf.nummer}</td>
      <td>${escapeHtml(lauf.gestartet_am)}</td>
      <td>${escapeHtml(lauf.beendet_am ?? "läuft noch")}</td>
      <td>${formatKosten(lauf.aggregat.kosten_usd)}</td>
      <td>${kostenNeuberechnenKnopf(lauf)} ${ausLaufUebernehmenKnopf(lauf)}</td>
    </tr>
  `;
}

function kostenNeuberechnenKnopf(lauf) {
  if (lauf.beendet_am === null) return "";
  return `<button type="button" class="kosten-neuberechnen" data-lauf-id="${lauf.lauf_id}">Kosten neu berechnen</button>`;
}

function ausLaufUebernehmenKnopf(lauf) {
  return `<button type="button" class="aus-lauf-uebernehmen" data-lauf-id="${lauf.lauf_id}" data-lauf-nummer="${lauf.nummer}">Aus Lauf ${lauf.nummer} übernehmen</button>`;
}

function renderCallsTabelle(laeufe, calls) {
  const kopfzeile = SPALTEN.map(kopfZelle).join("");
  const aggregatZeilen = [...laeufe].reverse().map(laufAggregatZeile).join("");
  const zeilen = calls.map(callZeile).join("");
  return `<table><thead><tr>${kopfzeile}</tr></thead><tbody>${aggregatZeilen}${zeilen}</tbody></table>`;
}

function laufAggregatZeile(lauf) {
  const werte = aggregatWerte(lauf);
  const zellen = SPALTEN.map((spalte) => `<td>${aggregatZelleInhalt(spalte.key, werte)}</td>`).join("");
  return `<tr class="lauf-aggregat-zeile" data-lauf-id="${lauf.lauf_id}">${zellen}</tr>`;
}

function aggregatWerte(lauf) {
  const anzahlModelle = lauf.einstellungen.modelle.length;
  return {
    lauf_nummer: lauf.nummer,
    modell_name: `Aggregat (${lauf.aggregat.anzahl_calls} Call(s))`,
    wiederholung_index: "",
    einstellungen: `${anzahlModelle} Modell(e) × ${lauf.einstellungen.wiederholungen} Wiederholung(en)`,
    status: "",
    input_tokens: lauf.aggregat.input_tokens,
    cached_input_tokens: lauf.aggregat.cached_input_tokens,
    reasoning_tokens: lauf.aggregat.reasoning_tokens,
    output_tokens: lauf.aggregat.output_tokens,
    total_tokens: lauf.aggregat.total_tokens,
    kosten_usd: lauf.aggregat.kosten_usd,
    dauer_ms: lauf.aggregat.dauer_ms_mittel,
  };
}

function aggregatZelleInhalt(key, werte) {
  if (key === "kosten_usd") return formatKosten(werte.kosten_usd);
  const wert = werte[key];
  return wert === null || wert === undefined || wert === "" ? "" : escapeHtml(String(wert));
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
      <td>${call.web_search_calls ?? ""}</td>
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
