const BASE = "/api/v1";

async function anfrage(pfad, optionen = {}) {
  const response = await fetch(BASE + pfad, {
    headers: { "Content-Type": "application/json", ...(optionen.headers || {}) },
    ...optionen,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const message = body && body.error ? body.error.message : `Fehler ${response.status}`;
    throw new Error(message);
  }
  if (response.status === 204) return null;
  return response.json();
}

export function getKeyStatus() {
  return anfrage("/key-status");
}

export function listProfiles() {
  return anfrage("/profile");
}

export function createProfile(name) {
  return anfrage("/profile", { method: "POST", body: JSON.stringify({ name }) });
}

export function getProfile(id) {
  return anfrage(`/profile/${id}`);
}

export function renameProfile(id, name) {
  return anfrage(`/profile/${id}`, { method: "PATCH", body: JSON.stringify({ name }) });
}

export function deleteProfile(id) {
  return anfrage(`/profile/${id}`, { method: "DELETE" });
}

export function duplicateProfile(id, name) {
  const body = name ? { name } : {};
  return anfrage(`/profile/${id}/duplikat`, { method: "POST", body: JSON.stringify(body) });
}

export function saveArbeitsstand(id, arbeitsstand) {
  return anfrage(`/profile/${id}/arbeitsstand`, {
    method: "PUT",
    body: JSON.stringify(arbeitsstand),
  });
}

export function uebernehmeAusLauf(profilId, laufId) {
  return anfrage(`/profile/${profilId}/arbeitsstand/aus-lauf/${laufId}`, { method: "POST" });
}

export function startLauf(id, apiKey) {
  const headers = apiKey ? { "X-OpenAI-Key": apiKey } : {};
  return anfrage(`/profile/${id}/laeufe`, { method: "POST", headers });
}

export function getCalls(profilId) {
  return anfrage(`/profile/${profilId}/calls`);
}

export function getCall(callId) {
  return anfrage(`/call/${callId}`);
}

export function kostenNeuBerechnen(laufId) {
  return anfrage(`/lauf/${laufId}/kosten-neuberechnung`, { method: "POST" });
}

export function getModelle() {
  return anfrage("/modelle");
}

export function createModell(name) {
  return anfrage("/modelle", { method: "POST", body: JSON.stringify({ name }) });
}

export function updateModell(name, felder) {
  return anfrage(`/modelle/${encodeURIComponent(name)}`, {
    method: "PUT",
    body: JSON.stringify(felder),
  });
}

export function deleteModell(name) {
  return anfrage(`/modelle/${encodeURIComponent(name)}`, { method: "DELETE" });
}
