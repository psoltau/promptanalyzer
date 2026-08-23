# 09 — Tool-Definitionen

**What to build:** Der Prompt-Optimierer fügt Tool-Definitionen als JSON in den Arbeitsstand ein,
um zu messen, was seine Werkzeugschemas an Input-Tokens kosten und ob das Modell sie wählen würde.
Ist das JSON syntaktisch kaputt, sagt es ihm die Oberfläche sofort — er erfährt das nicht erst
durch einen fehlgeschlagenen API-Call.

Die Definitionen gehen als `tools` mit dem Request mit und werden nie ausgeführt. Ein
zurückgegebener Funktionsaufruf ist das Ergebnis des Laufs, nicht der Anfang eines Dialogs: das
Werkzeug stellt weiterhin genau einen Request pro Call, und der Funktionsaufruf ist im Call-Detail
im Response-JSON nachlesbar.

**Blocked by:** 01 — Tracer Bullet: Profil, Arbeitsstand, ein Lauf mit einem Call.

**Status:** ready-for-agent

- [ ] Tool-JSON ist Teil des Arbeitsstands, wird gespeichert und mit dem Lauf eingefroren
- [ ] Syntaktisch kaputtes JSON wird im Frontend sofort gemeldet
- [ ] Tool-Definitionen gehen als `tools` an die API und werden nie ausgeführt
- [ ] Ein zurückgegebener Funktionsaufruf beendet den Call als Ergebnis; es entsteht kein zweiter Request
- [ ] Erfüllt `standards/`; die Verifikationsschritte aus `standards/architecture_backend.md` §9 laufen grün
