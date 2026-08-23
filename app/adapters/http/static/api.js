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

export function listProfiles() {
  return anfrage("/profile");
}

export function createProfile(name) {
  return anfrage("/profile", { method: "POST", body: JSON.stringify({ name }) });
}

export function getProfile(id) {
  return anfrage(`/profile/${id}`);
}

export function saveArbeitsstand(id, arbeitsstand) {
  return anfrage(`/profile/${id}/arbeitsstand`, {
    method: "PUT",
    body: JSON.stringify(arbeitsstand),
  });
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
