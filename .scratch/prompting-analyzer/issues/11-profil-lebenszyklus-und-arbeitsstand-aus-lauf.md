# 11 — Profil-Lebenszyklus und Arbeitsstand aus Lauf zurückholen

**What to build:** Der Prompt-Optimierer benennt ein Profil um, wenn sich sein Verständnis der
Aufgabe geändert hat, und löscht Profile, deren Experimente nichts geworden sind, damit seine
Liste nicht zumüllt. In der Profil-Liste sieht er je Profil die Anzahl der Läufe und wann es
zuletzt benutzt wurde, damit er dort das Richtige findet. Er dupliziert ein Profil samt Historie,
um einen Prompt in eine zweite Richtung zu entwickeln, ohne den bisherigen Verlauf zu verlieren.

Aus einer Lauf-Zeile holt er den Prompt- und Einstellungsstand jenes Laufs in den Arbeitsstand
zurück, um von einer Variante weiterzuarbeiten, die besser war als sein aktueller Stand — und wird
vorher gewarnt, dass sein aktueller Arbeitsstand dabei überschrieben wird.

**Blocked by:** 04 — Call-Detail als aufklappbarer Bereich.

**Status:** ready-for-agent

- [ ] Profil umbenennen und löschen
- [ ] Profil-Liste zeigt je Profil Anzahl der Läufe und Zeitpunkt der letzten Benutzung
- [ ] Duplizieren erzeugt ein neues Profil mit vollständig übernommener Historie; das Original bleibt unverändert
- [ ] „Aus Lauf N übernehmen" kopiert den Schnappschuss des Laufs in den Arbeitsstand
- [ ] Vor dem Übernehmen wird gewarnt, dass der aktuelle Arbeitsstand überschrieben wird
- [ ] Der Lauf selbst bleibt dabei unverändert
- [ ] Erfüllt `standards/`; die Verifikationsschritte aus `standards/architecture_backend.md` §9 laufen grün
