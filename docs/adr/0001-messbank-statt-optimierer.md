# Messbank statt Optimierer

Das Werkzeug heißt *Prompting Analyzer* und der Auftrag lautete „Prompts optimieren" — trotzdem
schreibt es keine Prompts um und bewertet keine Qualität. Es führt einen Prompt-Stand gegen
gewählte Modelle aus, protokolliert Tokenverbrauch, Kosten und Dauer und stellt die Läufe eines
Profils vergleichbar nebeneinander; die Optimierung macht ein Mensch, der diese Zahlen liest.

Der Grund: Optimieren setzt eine Zielfunktion voraus. Für Kosten gibt es sie (messbar), für
Qualität nicht (es existiert kein Bewertungssignal, kein Regressionsdatensatz, kein Judge). Ein
Optimierer ohne Qualitätssignal würde Prompts billiger machen und dabei unbemerkt schlechter.
Die Messbank erzeugt erst die Datenbasis, auf der eine automatische Kostenoptimierung später
überhaupt beurteilbar wäre.

## Konsequenzen

- Es gibt kein Feld für Qualitätsurteile, keine Bewertung und keine Notizen an einem Lauf. Die
  Entwicklung eines Profils ist damit ausschließlich als Kosten- und Verbrauchsentwicklung
  sichtbar, nicht als Qualitätsentwicklung.
- Eine automatische Kostenoptimierung als Ausbaustufe braucht zuerst ein Qualitätssignal. Das
  bedeutet, diese ADR und die Entscheidung gegen Bewertungsfelder gemeinsam neu zu bewerten.
