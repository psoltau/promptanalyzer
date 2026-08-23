# Prompting Analyzer

- **`standards/`** — bindende Architektur-, API-, Test-, Fehler-, Sicherheits- und
  Qualitätsregeln. Vor jeder Implementierung lesen. Blockiert eine Regel eine Aufgabe:
  anhalten und fragen, nicht umgehen. `.importlinter` ist eingefroren.
- **`CONTEXT.md`** — das Vokabular der Domäne. Profil, Arbeitsstand, Lauf, Call,
  Tool-Definition, Web-Suche, Wiederholung, Modell-Register. Nur diese Begriffe verwenden,
  auch in Code, Bezeichnern und Tests; die dort unter _Avoid_ genannten nie.
- **`docs/adr/`** — getroffene Entscheidungen samt Begründung. Nicht neu verhandeln, nicht
  „reparieren". Wer eine davon umstoßen will, ändert zuerst die ADR.
- **`SPEC.md`** — was gebaut wird: Problem, User Stories, Datenmodell, API-Vertrag,
  Ausführungssemantik, Kostenformel, Out of Scope.
- **`.scratch/prompting-analyzer/issues/`** — die Tickets, in Abhängigkeitsreihenfolge
  nummeriert. Sie beschreiben Verhalten, keine Technik; die Technik steht in `standards/`.
