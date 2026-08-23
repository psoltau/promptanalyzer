---
status: accepted
---

# Tests laufen durch HTTP, nicht gegen Schichten

`SPEC.md` (Testing Decisions) und
[standards/architecture_backend.md](../../standards/architecture_backend.md) §8 beschreiben zwei
verschiedene Testpyramiden für dasselbe Projekt. SPEC fordert: das System wird ausschließlich
durch HTTP angesprochen und über HTTP geprüft, kein Test nennt einen Modul-, Klassen- oder
Funktionsnamen des Produktionscodes außer der App selbst und der Attrappe, SQLite läuft als echte
Datei in einem Temp-Verzeichnis. §8 fordert: Use Cases gegen Fakes für alle Ports, Repositories
gegen `:memory:` mit echtem Schema, Routes mit `TestClient` und überschriebenen Ports. Beides
gleichzeitig geht nicht — Use-Case- und Repository-Tests müssen Produktionsnamen nennen, genau
was SPEC verbietet.

**Entscheidung: SPEC gewinnt.** Die Verhaltenssuite durch HTTP ist die verbindliche Ebene und das
einzige Sicherheitsnetz, auf das sich eine Änderung verlassen darf. Der Grund ist der Zustand des
Projekts: grünes Feld ohne Prior Art, in dem die Aufteilung in Module noch mehrfach umgebaut wird.
Tests, die Use Cases und Repositories einzeln festnageln, zementieren eine Struktur, die noch
niemand kennt, und müssten bei jedem Umbau mitwandern — während die HTTP-Suite denselben Umbau
unverändert übersteht. Die fachlichen Aussagen dieses Werkzeugs sind ohnehin
Ende-zu-Ende-Aussagen: *welche Zeilen erscheinen, welche Zahlen sie tragen, welchen Status* — und
gerade die Ausführungsordnung (parallel über Modelle, seriell über Wiederholungen) und die
Fehlerisolation sind auf Schichtebene überhaupt nicht prüfbar.

Was von §8 bestehen bleibt, weil es nicht im Widerspruch steht: der Responses-Client ist der
einzige Seam und die einzige Attrappe, kein Test berührt das Netz, und kein Test importiert aus
`adapters/responses/`. Was aus `standards/testing.md` bestehen bleibt: Testnamen beschreiben
beobachtbares Verhalten, Testzustand wird zwischen Tests zurückgesetzt, Tests entstehen vor oder
mit dem Code. Die dort geforderten ≥ 90 % Zeilenabdeckung der Fachlogik werden über die
Gesamtsuite gemessen, nicht je Schicht.

## Konsequenzen

- §8 ist damit für dieses Projekt außer Kraft. Wer später Schichttests hinzufügt, ändert zuerst
  diese ADR — sonst entstehen zwei Suiten mit gegenläufigen Regeln.
- Ein Test darf einen Fehlerfall nur auslösen, wie ein Nutzer ihn auslösen kann: über die Attrappe
  oder über eine Eingabe. Ist ein Zweig so nicht erreichbar, ist das ein Hinweis auf toten Code,
  nicht auf eine Lücke in der Teststrategie.
- Kombinatorik-lastige Fälle (Kostenformel über gecachte, Reasoning- und Suchposten) werden über
  HTTP mit vorbereiteten `usage`-Werten der Attrappe durchgespielt. Das ist etwas mehr Aufbau je
  Fall als ein Unittest der Formel — der bewusst gezahlte Preis.
- SQLite läuft in Tests als echte Datei in einem Temp-Verzeichnis, nicht als `:memory:`.
