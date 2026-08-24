import { getCall } from "./api.js";

const SCHNAPPSCHUSS_FELDER = [
  { key: "system_prompt", label: "System Prompt", mehrzeilig: true },
  { key: "user_prompt", label: "User Prompt", mehrzeilig: true },
  { key: "tools_json", label: "Tool-Definitionen", mehrzeilig: true },
  { key: "modelle", label: "Modelle" },
  { key: "max_output_tokens", label: "max_output_tokens" },
  { key: "reasoning_effort", label: "reasoning_effort" },
  { key: "web_suche", label: "Web-Suche" },
  { key: "search_context_size", label: "search_context_size" },
  { key: "wiederholungen", label: "Wiederholungen" },
];

export async function zeigeCallDetail(app, callId) {
  const detailZeile = app.querySelector(`[data-call-detail="${callId}"]`);
  const sichtbar = !detailZeile.hidden;
  if (sichtbar) {
    detailZeile.hidden = true;
    return;
  }
  const call = await getCall(callId);
  const zelle = detailZeile.querySelector("td");
  zelle.innerHTML = renderCallDetail(call);
  detailZeile.hidden = false;
}

function renderCallDetail(call) {
  const abschnitte = [
    call.status === "error" ? renderFehler(call) : "",
    renderAntwort(call),
    renderSchnappschuss(call.schnappschuss),
    renderRohesJson("Request-JSON", call.request_json),
    renderRohesJson("Response-JSON", call.response_json),
  ];
  return `<div class="call-detail-inhalt">${abschnitte.join("")}</div>`;
}

function renderFehler(call) {
  return abschnitt(
    "Fehler",
    `<pre class="call-detail-fehler">${escapeHtml(call.fehlertext || "(kein Fehlertext)")}</pre>`
  );
}

function renderAntwort(call) {
  const text = call.antwort_text || (call.status === "error" ? "(kein Call abgeschlossen)" : "(leere Antwort)");
  return abschnitt("Antwort", `<pre>${escapeHtml(text)}</pre>`);
}

function renderSchnappschuss(schnappschuss) {
  const zeilen = SCHNAPPSCHUSS_FELDER.map((feld) => schnappschussZeile(feld, schnappschuss)).join("");
  return abschnitt(
    "Prompt- und Einstellungs-Schnappschuss",
    `<dl class="call-detail-schnappschuss">${zeilen}</dl>`
  );
}

function schnappschussZeile(feld, schnappschuss) {
  const wert = formatSchnappschussWert(feld, schnappschuss[feld.key]);
  const inhalt = feld.mehrzeilig ? `<pre>${wert}</pre>` : wert;
  return `<dt>${escapeHtml(feld.label)}</dt><dd>${inhalt}</dd>`;
}

function formatSchnappschussWert(feld, wert) {
  if (feld.key === "modelle") return escapeHtml(wert.join(", ") || "(keine)");
  if (feld.key === "web_suche") return wert ? "an" : "aus";
  if (wert === null || wert === undefined || wert === "") return escapeHtml("–");
  return escapeHtml(String(wert));
}

function renderRohesJson(titel, wert) {
  const text = wert === null || wert === undefined ? "(nicht vorhanden)" : JSON.stringify(wert, null, 2);
  return abschnitt(titel, `<pre class="call-detail-json">${escapeHtml(text)}</pre>`);
}

function abschnitt(titel, inhaltHtml) {
  return `<section class="call-detail-abschnitt"><h3>${escapeHtml(titel)}</h3>${inhaltHtml}</section>`;
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}
