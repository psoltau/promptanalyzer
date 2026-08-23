# 03 — Vergleichstabelle über die Profil-Historie

**What to build:** Der Prompt-Optimierer sieht im Profil unter dem Arbeitsstand alle Calls der
gesamten Profil-Geschichte in einer flachen Tabelle, chronologisch geliefert und im Frontend nach
jeder Spalte sortierbar: Modell, Einstellungen, Status, Input-, gecachte Input-, Reasoning- und
Output-Tokens in getrennten Spalten, Dauer. Damit lassen sich „welcher Lauf war am billigsten" und
„welcher am schnellsten" direkt beantworten, und die Reasoning-Kosten verschwinden nicht in der
Output-Summe.

Die Statusspalte ist laut: `complete`, `incomplete (max_output_tokens)` und `error` sind auf einen
Blick unterscheidbar, damit niemand Läufe vergleicht, die gar kein vergleichbares Ergebnis haben.

Derselbe Endpunkt ist der Fortschrittsanzeiger. Solange ein Lauf kein `beendet_am` hat, pollt das
Frontend im Sekundenrhythmus; Zeilen erscheinen, sobald der jeweilige Call fertig ist, und der
Prompt-Optimierer sieht, dass ein Lauf noch läuft und wie viele seiner Calls fertig sind. Er
ändert den Arbeitsstand, führt erneut aus, und die neue Zeile steht neben allen alten.

**Blocked by:** 01 — Tracer Bullet: Profil, Arbeitsstand, ein Lauf mit einem Call.

**Status:** ready-for-agent

- [ ] Ein Endpunkt liefert alle Calls eines Profils chronologisch, über Läufe hinweg
- [ ] Tabelle ist nach jeder Spalte sortierbar
- [ ] Input, gecachter Input, Reasoning und Output stehen in getrennten Spalten
- [ ] Statusspalte zeigt `complete`, `incomplete (max_output_tokens)` und `error` deutlich unterscheidbar
- [ ] Dauer je Call ist sichtbar
- [ ] Frontend pollt im Sekundenrhythmus, solange ein Lauf kein `beendet_am` hat, und stellt es danach ein
- [ ] Fortschritt eines laufenden Laufs ist sichtbar (fertige von erwarteten Calls)
- [ ] Zeilen früherer Läufe bleiben unverändert stehen, wenn ein neuer Lauf hinzukommt
