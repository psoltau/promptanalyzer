# 10 — Web-Suche

**What to build:** Der Prompt-Optimierer aktiviert Web-Suche für einen Lauf und wählt
`search_context_size`, um den einzigen Hebel zu testen, mit dem sich der Token-Anteil der Web-Suche
beeinflussen lässt. Die Web-Such-Optionen erscheinen nur, wenn das gewählte Modell sie nach dem
Register unterstützt, damit die Oberfläche nicht lügt.

Die Vergleichstabelle bekommt eine eigene Spalte mit der Anzahl der Suchanfragen, bestimmt als
Anzahl der Web-Such-Einträge im `output`-Array der Antwort — damit erklärbar wird, warum zwei sonst
gleiche Läufe unterschiedlich teuer waren. Die Suchkosten (Suchanfragen × Suchpreis) sind Teil der
Kostenzahl, damit die Kostenspalte nicht den größten Posten eines Suchlaufs verschweigt.

Web-Suche ist das einzige serverseitig ausgeführte Werkzeug; das Werkzeug stellt weiterhin genau
einen Request pro Call. Eine Sonderbehandlung oder Kennzeichnung von Suchläufen gibt es bewusst
nicht.

**Blocked by:** 06 — Kosten als Schnappschuss; 07 — Gating der Einstellungen aus dem Register.

**Status:** ready-for-agent

- [ ] Web-Suche und `search_context_size` sind Teil des Arbeitsstands und werden mit dem Lauf eingefroren
- [ ] Die Optionen erscheinen nur für Modelle, deren Register-Schalter Web-Suche erlaubt
- [ ] Spalte „Suchanfragen" wird korrekt aus der Antwortstruktur gezählt
- [ ] Suchkosten sind in der Kostenzahl enthalten; fehlender Suchpreis lässt die Kostenspalte leer
- [ ] Es entsteht weiterhin genau ein Request pro Call
- [ ] Erfüllt `standards/`; die Verifikationsschritte aus `standards/architecture_backend.md` §9 laufen grün
