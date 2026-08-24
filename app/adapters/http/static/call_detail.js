import { getCall } from "./api.js";

export async function zeigeCallDetail(app, callId) {
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
