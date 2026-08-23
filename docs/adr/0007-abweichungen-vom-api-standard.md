---
status: proposed
---

# Abweichungen vom API-Standard: keine Pagination, keine Sortier-Whitelist

[standards/api-design.md](../../standards/api-design.md) verlangt Pagination mit `MAX_PAGE_SIZE`
für *alle* Listen-Endpunkte und eine `ALLOWED_SORT_FIELDS`-Whitelist für Sortierfelder. Für
dieses Werkzeug gilt beides nicht; alles Übrige aus dem Standard gilt unverändert.

**Keine Pagination.** Der Endpunkt, der alle Calls eines Profils liefert, *ist* das Produkt: die
flache Tabelle über die gesamte Geschichte eines Prompts, aus der der Prompt-Optimierer die
Entwicklung abliest. Eine Seitengrenze würde genau die Vergleiche zerschneiden, für die das
Werkzeug existiert („welcher Lauf war am billigsten"), und derselbe Endpunkt dient als
Fortschrittsanzeiger für den laufenden Lauf. Dasselbe gilt für Profil-Liste und Register: beide
werden von Hand gepflegt und haben eine natürliche Obergrenze von einigen Dutzend Einträgen —
das Register wird ausdrücklich aufgeräumt, damit die Auswahlliste nicht aus vierzig Namen besteht.
Ein lokales Einbenutzer-Werkzeug hat hier kein Lastproblem, das eine Seitengrenze löst.

**Keine Sortier-Whitelist,** weil es keine serverseitige Sortierung gibt. Die Calls kommen
chronologisch, sortiert wird im Frontend auf den bereits geladenen Zeilen. Es existiert kein
Sortierparameter, gegen den eine Whitelist schützen könnte; entsteht später einer, greift die
Regel des Standards wieder.

**Unverändert übernommen:** `/api/v1/`-Präfix, UUIDs als Ressourcen-IDs, Fehler-Envelope
`{ error: { code, message, traceId } }`, `201` mit `Location` für angelegte Ressourcen,
parametrisiertes SQL, Eingabevalidierung am Rand mit Allow-List.

## Konsequenzen

- `profil.id`, `lauf.id` und `call.id` sind UUIDs. Die im Frontend angezeigte Lauf-Nummer ist
  davon unabhängig: `lauf.nummer` bleibt der fortlaufende Zähler je Profil und ist eine
  Anzeige-, keine Identitätsangabe.
- Die Antwort des Call-Endpunkts wächst mit der Geschichte eines Profils linear. Wird ein Profil
  unbenutzbar groß, ist die Antwort darauf ein neues Profil (oder ein Duplikat als Schnitt), nicht
  Pagination.
