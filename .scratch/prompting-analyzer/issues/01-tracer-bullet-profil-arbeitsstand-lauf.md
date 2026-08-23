# 01 — Tracer Bullet: Profil, Arbeitsstand, ein Lauf mit einem Call

**What to build:** Der Prompt-Optimierer öffnet das Werkzeug, sieht eine Profil-Liste, legt ein
Profil mit Namen an, tippt System Prompt und User Prompt in getrennte große Textfelder, setzt
`max_output_tokens` und `reasoning_effort`, wählt ein Modell und führt aus. Sein Arbeitsstand wird
beim Tippen entprellt gespeichert und zeigt an, wann das zuletzt geschah — ein Reload oder
Tab-Wechsel verliert nichts.

Das Ausführen friert den Arbeitsstand als Lauf ein und blockiert die Oberfläche nicht: der Aufruf
kehrt sofort mit der Lauf-Nummer zurück, der Call läuft weiter, während der Prompt-Optimierer
zusehen kann. Ein Lauf ist danach unveränderlich — spätere Änderungen am Arbeitsstand berühren ihn
nicht.

Ist der Call fertig, sieht der Prompt-Optimierer die Tokenposten getrennt (Input, gecachter Input,
Reasoning, Output, Total), den Status (`complete` / `incomplete` mit Grund `max_output_tokens` /
`error` mit Fehlertext), die gemessene Dauer und den Antworttext. Ab hier ist das Werkzeug nützlich:
Prompt eingeben, ausführen, Verbrauch und Ergebnis sehen.

Sein API-Key reist als Header mit dem ausführenden Aufruf; hat er keinen eingetragen, greift
`OPENAI_API_KEY` aus der Umgebung, damit er bei einem Key in der Shell gar nichts eintragen muss.

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] Profil anlegen und auflisten
- [ ] Arbeitsstand wird beim Tippen entprellt gespeichert und überlebt einen Reload unverändert
- [ ] Der Zeitpunkt des letzten Speicherns ist sichtbar
- [ ] `max_output_tokens` und `reasoning_effort` sind Teil des Arbeitsstands
- [ ] Ausführen kehrt sofort mit der Lauf-Nummer zurück; der Call läuft danach weiter
- [ ] Ein Lauf friert Prompt-Texte und Einstellungen ein: nachträgliche Änderung des Arbeitsstands lässt die Lauf-Felder unberührt
- [ ] Input, gecachter Input, Reasoning, Output und Total werden getrennt gespeichert und angezeigt
- [ ] Statusableitung für alle drei Zustände, inklusive gespeichertem `incomplete`-Grund
- [ ] Dauer je Call ist gemessene Wanduhrzeit um den einen Aufruf; kein Streaming
- [ ] Antworttext ist lesbar
- [ ] Eingetragener Key wird verwendet; fehlt er, greift `OPENAI_API_KEY`; der eingetragene gewinnt, wenn beides da ist
- [ ] Tests beschreiben beobachtbares Verhalten, nicht Aufrufe
- [ ] Erfüllt `standards/`; die Verifikationsschritte aus `standards/architecture_backend.md` §9 laufen grün
