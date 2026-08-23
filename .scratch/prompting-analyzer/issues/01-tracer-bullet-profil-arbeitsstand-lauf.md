# 01 — Tracer Bullet: Profil, Arbeitsstand, ein Lauf mit einem Call

**What to build:** Das Werkzeug startet als ein einziger Prozess und legt sein Schema beim Start
idempotent an. Der Prompt-Optimierer öffnet die Profil-Liste, legt ein Profil mit Namen an, tippt
System Prompt und User Prompt in getrennte große Textfelder, setzt `max_output_tokens` und
`reasoning_effort`, wählt ein Modell und führt aus. Der Arbeitsstand wird beim Tippen entprellt
ganzheitlich gespeichert und zeigt an, wann das zuletzt geschah — ein Reload verliert nichts.

Das Ausführen friert den Arbeitsstand als Lauf ein und kehrt sofort mit der Lauf-Nummer zurück; der
Call läuft in einer Hintergrundaufgabe. Danach sieht der Prompt-Optimierer für diesen Call die
Tokenposten getrennt (Input, gecachter Input, Reasoning, Output, Total), den Status
(`complete` / `incomplete` mit Grund `max_output_tokens` / `error` mit Fehlertext), die
serverseitig gemessene Dauer und den Antworttext. Ab hier ist das Werkzeug nützlich.

Der API-Key reist als Header mit dem ausführenden Request; fehlt er, greift `OPENAI_API_KEY` aus
der Prozessumgebung. Der Zugriff auf die Responses API liegt hinter einer schmalen Schnittstelle
mit einer Operation — dem einzigen Ort, der das Netz berührt, und dem einzigen Seam.

Dieses Ticket legt das Testmuster für alles Weitere fest: Testanwendung mit eingesetzter Attrappe
des Responses-Clients und echter SQLite-Datei in einem Temp-Verzeichnis aufbauen, durch HTTP
treiben, über HTTP prüfen. Die Attrappe liefert wählbare `usage`-Werte, unvollständige Antworten
und geworfene Fehler und protokolliert die empfangenen Anfragen samt Reihenfolge.

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] Ein Prozess: FastAPI hinter Uvicorn, SQLite über `sqlite3`, kein ORM, keine Migrationsbibliothek; Schema wird beim Start idempotent angelegt
- [ ] Frontend ist eine statisch ausgelieferte Seite mit Vanilla JS ohne Build-Schritt; Datenaustausch nur über JSON-Endpunkte
- [ ] Profil anlegen und auflisten funktioniert über HTTP
- [ ] Arbeitsstand ganzheitlich schreiben; Reload zeigt ihn unverändert; Zeitpunkt des letzten Speicherns ist sichtbar
- [ ] Lauf anlegen kehrt sofort mit `lauf_id` zurück, der Call läuft in einer Hintergrundaufgabe
- [ ] Ein Lauf friert seinen Prompt- und Einstellungsstand ein: nachträgliche Änderung des Arbeitsstands lässt die Lauf-Felder unberührt
- [ ] Alle vier Tabellen (`profil`, `lauf`, `call`, `modell`) existieren wie spezifiziert; `call.modell_name` ist Text ohne Fremdschlüssel
- [ ] Tokenposten werden getrennt gespeichert und angezeigt, inklusive gecachter und Reasoning-Tokens
- [ ] Statusableitung für alle drei Zustände, inklusive gespeichertem `incomplete`-Grund
- [ ] `dauer_ms` ist serverseitig gemessene Wanduhrzeit um den einen Request; kein Streaming
- [ ] Key aus dem Header wird verwendet; fehlt der Header, greift `OPENAI_API_KEY`; Header gewinnt, wenn beides da ist
- [ ] Tests sprechen ausschließlich über HTTP, nennen keine Produktions-Modul- oder Funktionsnamen außer App und Attrappe, und prüfen beobachtbare Ergebnisse statt Aufrufe
