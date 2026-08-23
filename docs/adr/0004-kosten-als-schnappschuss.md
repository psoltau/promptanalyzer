# Kosten sind Schnappschüsse, keine Ableitung

Jeder Call speichert die vier zum Ausführungszeitpunkt gültigen Preissätze mit und dazu die
errechneten Kosten. Kosten werden bei der Anzeige nie neu aus dem Register gerechnet.

Das sieht nach unnötiger Redundanz aus und wird deshalb hier festgehalten. Der Grund ist die
Kombination zweier anderer Entscheidungen: Läufe sind unveränderlich, und Preise sind von Hand
editierbar (siehe [ADR 0002](./0002-register-von-hand-gepflegt.md)). Würden Kosten abgeleitet,
wäre ein Lauf nicht mehr unveränderlich — eine Preiskorrektur würde die gesamte Historie
rückwirkend umschreiben, und die Aussage „Variante C war 30 % billiger als A" würde still falsch,
ohne dass irgendetwas darauf hinweist.

Die gespeicherten Preissätze mitzuführen (statt nur des Endbetrags) macht jede Zahl nachrechenbar.
Für den Fall eines echten Tippfehlers im Register gibt es einen ausdrücklichen
„Kosten neu berechnen"-Knopf im Detail eines Laufs — auf Ansage, nie automatisch.
