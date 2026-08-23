# JSON-Endpunkt-Spezifikation

Dies ist die in [standards/architecture_backend.md](../standards/architecture_backend.md) §5
verlangte Endpunkt-Spezifikation. Sie setzt den Prosa-API-Vertrag aus [SPEC.md](../SPEC.md) in
konkrete Pfade und Payloads um. Abweichungen von
[standards/api-design.md](../standards/api-design.md) sind in
[ADR 0007](./adr/0007-abweichungen-vom-api-standard.md) begründet.

## Konventionen

- Präfix `/api/v1/`. Pfadsegmente und Feldnamen in der Domänensprache aus
  [CONTEXT.md](../CONTEXT.md), `snake_case`.
- Alle IDs sind UUIDs. `lauf.nummer` ist die angezeigte, je Profil fortlaufende Lauf-Nummer und
  keine Identität.
- Alle Zeitstempel sind UTC in ISO 8601 mit `Z`, z. B. `2026-08-23T14:03:11Z`.
- Alle Geldbeträge in USD. `null` in einem Kosten- oder Preisfeld bedeutet **unbekannt**, nie
  „null Kosten". Das Frontend zeigt dafür eine leere Zelle.
- Angelegte Ressourcen antworten `201` mit `Location`. Löschen antwortet `204` ohne Körper.
- Fehler antworten mit `{ "error": { "code": ..., "message": ..., "traceId": ... } }`, `code` in
  `UPPER_SNAKE_CASE`.
- Keine Pagination, keine Sortierparameter (ADR 0007).
- Der API-Key reist ausschließlich im Header `X-OpenAI-Key`, nur bei ausführenden Aufrufen, nie
  im Körper und nie in der URL.

## Arbeitsstand-Körper

Dieselbe Feldmenge tritt an drei Stellen auf: als Arbeitsstand eines Profils, als eingefrorener
Schnappschuss eines Laufs, und als Eingabe beim Schreiben des Arbeitsstands.

```json
{
  "system_prompt": "Du bist …",
  "user_prompt": "Fasse zusammen: …",
  "tools_json": "[{\"type\":\"function\", …}]",
  "modelle": ["gpt-5", "o4-mini"],
  "max_output_tokens": 2048,
  "reasoning_effort": "medium",
  "web_suche": false,
  "search_context_size": null,
  "wiederholungen": 1
}
```

`tools_json` ist der rohe Text, wie der Nutzer ihn eingegeben hat, oder `null`.
`reasoning_effort` und `search_context_size` sind `null`, wenn nicht gesetzt.

## Profile

### `GET /api/v1/profile`

```json
[
  {
    "id": "3f0c…",
    "name": "Zusammenfasser",
    "erstellt_am": "2026-08-01T09:12:00Z",
    "arbeitsstand_geaendert_am": "2026-08-23T14:03:11Z",
    "anzahl_laeufe": 7,
    "zuletzt_benutzt_am": "2026-08-22T18:40:02Z"
  }
]
```

`zuletzt_benutzt_am` ist der Start des jüngsten Laufs, sonst `null`.

### `POST /api/v1/profile`

Körper `{ "name": "Zusammenfasser" }` → `201`, `Location: /api/v1/profile/{id}`, Körper wie
`GET /api/v1/profile/{id}`. Ein neues Profil hat einen leeren Arbeitsstand mit
`wiederholungen: 1`, `web_suche: false`, leerer `modelle`-Liste.

### `GET /api/v1/profile/{id}`

```json
{
  "id": "3f0c…",
  "name": "Zusammenfasser",
  "erstellt_am": "…",
  "arbeitsstand_geaendert_am": "…",
  "arbeitsstand": { "…": "Arbeitsstand-Körper" }
}
```

### `PATCH /api/v1/profile/{id}`

Körper `{ "name": "…" }` → `200` mit dem Profil. Umbenennen berührt keinen Lauf.

### `DELETE /api/v1/profile/{id}`

`204`. Läufe und Calls des Profils gehen mit.

### `POST /api/v1/profile/{id}/duplikat`

Körper optional `{ "name": "…" }`, sonst ein abgeleiteter Name. → `201`,
`Location: /api/v1/profile/{neue_id}`. Das Duplikat enthält Arbeitsstand **und** vollständige
Historie: Läufe mit ihren Nummern und Schnappschüssen, Calls mit allen Zahlen, Preis-Schnappschüssen
und rohem JSON. Das Original bleibt unverändert.

## Arbeitsstand

### `PUT /api/v1/profile/{id}/arbeitsstand`

Ganzheitliches Schreiben; das Frontend ruft entprellt nach dem Tippen. Körper ist der
Arbeitsstand-Körper. → `200 { "arbeitsstand_geaendert_am": "…" }`.

Ein syntaktisch kaputtes `tools_json` wird **nicht** abgewiesen — ein halbfertiger Entwurf muss
speicherbar sein. Die Syntaxprüfung passiert im Frontend beim Tippen und im Lauf-Endpunkt beim
Ausführen.

### `POST /api/v1/profile/{id}/arbeitsstand/aus-lauf/{lauf_id}`

Kopiert den Schnappschuss des Laufs in den Arbeitsstand und überschreibt ihn dabei. → `200` mit
dem neuen Arbeitsstand. Der Lauf selbst bleibt unverändert. Die Warnung vor dem Überschreiben
zeigt das Frontend vor dem Aufruf.

## Läufe

### `POST /api/v1/profile/{id}/laeufe`

Header `X-OpenAI-Key` optional. Kein Körper — ausgeführt wird immer der gespeicherte
Arbeitsstand. Der Endpunkt friert den Arbeitsstand als Lauf ein, legt die Lauf-Zeile an und kehrt
**sofort** zurück; die Calls laufen in einer Hintergrundaufgabe.

→ `201`, `Location: /api/v1/lauf/{lauf_id}`

```json
{
  "lauf_id": "9ab1…",
  "nummer": 8,
  "erwartete_calls": 6,
  "gestartet_am": "2026-08-23T14:05:00Z"
}
```

Abweisungen vor dem Anlegen: leere `modelle`-Liste → `KEIN_MODELL_GEWAEHLT`; kaputtes
`tools_json` → `TOOLS_JSON_UNGUELTIG`; weder Header noch `OPENAI_API_KEY` → `KEY_FEHLT`;
`wiederholungen < 1` → `WIEDERHOLUNGEN_UNGUELTIG`. Ein Modell ohne gepflegte Preise ist **kein**
Fehler.

### `POST /api/v1/lauf/{id}/kosten-neuberechnung`

Nur auf ausdrückliche Anweisung. Überschreibt Preis-Schnappschüsse und `kosten_usd` aller Calls
dieses Laufs aus dem aktuellen Register. → `200 { "geaenderte_calls": 6 }`. Ein noch nicht
beendeter Lauf antwortet `LAUF_LAEUFT_NOCH`.

## Vergleichstabelle

### `GET /api/v1/profile/{id}/calls`

Die flache Tabelle über die gesamte Geschichte des Profils, chronologisch aufsteigend, plus je
Lauf eine Aggregatzeile. Gleichzeitig der Fortschrittsanzeiger: das Frontend ruft im
Sekundenrhythmus, solange ein Lauf `beendet_am: null` hat.

```json
{
  "laeufe": [
    {
      "lauf_id": "9ab1…",
      "nummer": 8,
      "gestartet_am": "…",
      "beendet_am": null,
      "erwartete_calls": 6,
      "fertige_calls": 4,
      "einstellungen": { "…": "Arbeitsstand-Körper ohne Prompt-Texte und tools_json" },
      "aggregat": {
        "anzahl_calls": 4,
        "input_tokens": 4120,
        "cached_input_tokens": 0,
        "reasoning_tokens": 2304,
        "output_tokens": 3010,
        "total_tokens": 7130,
        "web_search_calls": 0,
        "kosten_usd": 0.0421,
        "dauer_ms_mittel": 8140
      }
    }
  ],
  "calls": [
    {
      "id": "c771…",
      "lauf_id": "9ab1…",
      "lauf_nummer": 8,
      "modell_name": "gpt-5",
      "wiederholung_index": 1,
      "status": "complete",
      "incomplete_grund": null,
      "hat_fehler": false,
      "max_output_tokens": 2048,
      "reasoning_effort": "medium",
      "web_suche": false,
      "search_context_size": null,
      "input_tokens": 1030,
      "cached_input_tokens": 0,
      "reasoning_tokens": 576,
      "output_tokens": 812,
      "total_tokens": 1842,
      "web_search_calls": 0,
      "kosten_usd": 0.0105,
      "dauer_ms": 8140,
      "erstellt_am": "…"
    }
  ]
}
```

`status` ist `complete` | `incomplete` | `error`. Das Frontend setzt daraus die laute Statusspalte
zusammen, bei `incomplete` mit dem Grund in Klammern. `kosten_usd` ist `null`, wenn ein benötigter
Preis fehlte. Ein Aggregat summiert nur, was vorliegt; fehlt bei einem Call `kosten_usd`, ist auch
die Aggregatkosten `null` (sonst behauptete die Summe eine Vollständigkeit, die sie nicht hat).

### `GET /api/v1/call/{id}`

```json
{
  "id": "c771…",
  "lauf_id": "9ab1…",
  "lauf_nummer": 8,
  "modell_name": "gpt-5",
  "wiederholung_index": 1,
  "status": "complete",
  "incomplete_grund": null,
  "fehlertext": null,
  "antwort_text": "…",
  "schnappschuss": { "…": "Arbeitsstand-Körper des Laufs" },
  "preise": {
    "preis_input": 1.25,
    "preis_cached_input": 0.125,
    "preis_output": 10.0,
    "preis_suche": null
  },
  "request_json": { "…": "Anfragekörper, nie Header" },
  "response_json": { "…": "rohe Antwort" }
}
```

Die Preise sind die zum Ausführungszeitpunkt gültigen Sätze in USD je Million Tokens
(`preis_suche` in USD je Suchanfrage), damit jede Kostenzahl nachrechenbar ist.

## Register

### `GET /api/v1/modelle`

```json
[
  {
    "name": "gpt-5",
    "preis_input": 1.25,
    "preis_cached_input": 0.125,
    "preis_output": 10.0,
    "preis_suche": null,
    "kontextfenster": 400000,
    "erlaubt_reasoning_effort": true,
    "erlaubt_web_suche": true,
    "unterstuetzt_prompt_caching": true,
    "preise_vollstaendig": false
  }
]
```

`preise_vollstaendig` ist abgeleitet und sagt dem Frontend, für welche Modelle es in der
Modellauswahl auf leere Kostenspalten hinweist. Ein Modell mit `false` bleibt ausführbar.

### `POST /api/v1/modelle`

Körper `{ "name": "gpt-5.1" }`; alle übrigen Felder optional. → `201`,
`Location: /api/v1/modelle/{name}`. Ein neu angelegtes Modell hat leere Preise, `kontextfenster:
null` und alle drei Fähigkeitsschalter auf `true`. Ein vergebener Name antwortet
`MODELL_NAME_VERGEBEN`.

### `PUT /api/v1/modelle/{name}`

Ganzheitliches Schreiben aller Preis-, Kontextfenster- und Fähigkeitsfelder. → `200`. Preise
werden in der Einheit eingetragen, in der OpenAI sie ausweist: USD je Million Tokens, Suchpreis
USD je Suchanfrage. Eine Preisänderung berührt bestehende Calls nicht
([ADR 0004](./adr/0004-kosten-als-schnappschuss.md)).

### `DELETE /api/v1/modelle/{name}`

`204`. Bestehende Calls bleiben unverändert — `call.modell_name` ist Text ohne Fremdschlüssel.

## Key-Status

### `GET /api/v1/key-status`

```json
{ "umgebungs_key_vorhanden": true }
```

Meldet nur die Existenz, nie den Key oder einen Teil davon. Das Frontend leitet daraus mit dem
eigenen Feld die wirkende Quelle ab: eingetragenes Feld gewinnt, sonst Umgebung, sonst keine.

## Fehlercodes

| `code` | HTTP | Bedeutung |
| --- | --- | --- |
| `PROFIL_NICHT_GEFUNDEN` | 404 | Unbekannte Profil-ID |
| `LAUF_NICHT_GEFUNDEN` | 404 | Unbekannte Lauf-ID, oder Lauf gehört nicht zum Profil |
| `CALL_NICHT_GEFUNDEN` | 404 | Unbekannte Call-ID |
| `MODELL_NICHT_GEFUNDEN` | 404 | Unbekannter Modellname im Register |
| `NAME_LEER` | 422 | Profilname leer oder nur Leerraum |
| `KEIN_MODELL_GEWAEHLT` | 422 | Arbeitsstand hat keine Modelle |
| `WIEDERHOLUNGEN_UNGUELTIG` | 422 | `wiederholungen < 1` |
| `TOOLS_JSON_UNGUELTIG` | 422 | `tools_json` ist kein gültiges JSON (nur beim Ausführen) |
| `MODELL_NAME_VERGEBEN` | 409 | Registereintrag existiert schon |
| `LAUF_LAEUFT_NOCH` | 409 | Neuberechnung auf einem unbeendeten Lauf |
| `KEY_FEHLT` | 400 | Kein Key im Header und keiner in der Umgebung |

Fehler des Modellanbieters sind **keine** HTTP-Fehler dieses Werkzeugs: sie landen als Call mit
Status `error` und `fehlertext` in der Tabelle.
