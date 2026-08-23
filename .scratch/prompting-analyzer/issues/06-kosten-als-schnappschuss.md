# 06 — Kosten als Schnappschuss

**What to build:** Jeder Call trägt in der Vergleichstabelle seine Kosten in USD, damit Modelle
mit unterschiedlichen Preisen überhaupt vergleichbar sind. Die Rechnung läuft einmal beim
Schreiben des Calls und wird festgeschrieben, samt der vier verwendeten Preissätze — die im
Call-Detail sichtbar sind, damit jede Kostenzahl nachrechenbar ist.

Zwei Feinheiten entscheiden über die Richtigkeit: die von der API gemeldeten Input-Tokens
enthalten die gecachten, also wird `input_tokens - cached_input_tokens` zum Input-Satz und
`cached_input_tokens` zum reduzierten Satz bepreist; und die gemeldeten Output-Tokens enthalten
die Reasoning-Tokens, also wird Reasoning nicht gesondert bepreist — die eigene Spalte ist reine
Sichtbarmachung. Fehlt ein benötigter Preis, bleibt die Kostenspalte leer statt null zu zeigen,
damit „kostenlos" nicht mit „unbekannt" verwechselt wird.

Eine Preiskorrektur im Register verändert alte Läufe nicht: ein gestern gezogener Vergleich bleibt
gültig. Für den Fall eines echten Tippfehlers im Register gibt es einen ausdrücklichen „Kosten neu
berechnen"-Knopf am Lauf, der Preis-Schnappschüsse und Kosten dieses Laufs aus dem aktuellen
Register überschreibt — auf Ansage, nie automatisch.

**Blocked by:** 03 — Vergleichstabelle über die Profil-Historie; 05 — Modell-Register.

**Status:** ready-for-agent

- [ ] Kostenspalte je Call in USD in der Vergleichstabelle
- [ ] Gecachter Anteil wird zum reduzierten Satz gerechnet, der Rest zum Input-Satz
- [ ] Reasoning-Tokens werden nicht doppelt bepreist
- [ ] Fehlender Preis führt zu leerer Spalte, nicht zu `0`
- [ ] Die vier verwendeten Preissätze sind je Call gespeichert und im Detail sichtbar
- [ ] Preisänderung im Register lässt Kosten und Preisfelder alter Calls unverändert
- [ ] „Kosten neu berechnen" am Lauf überschreibt dessen Preis-Schnappschüsse und Kosten aus dem aktuellen Register
