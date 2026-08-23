# Modell-Register wird von Hand im Werkzeug gepflegt

Preise, Kontextfenster und Parametergültigkeit der Modelle werden in einem Register-Bildschirm
des Werkzeugs eingetragen und in der Datenbank gehalten. Es gibt keinen Abruf von außen, weder
beim Start noch später.

Der naheliegende Weg wäre ein automatischer Abruf, und es gibt Quellen dafür — deshalb steht
diese Entscheidung hier: sonst wird in einigen Monaten ein Preis-Fetcher „nachgerüstet".

## Verworfene Alternativen

- **`model_prices_and_context_window.json` aus dem LiteLLM-Repo.** Technisch der beste Kandidat:
  ~3200 Einträge, liefert Input-, Cached-Input-, Output- und Suchpreise, Kontextfenster und
  Fähigkeitsflags in einem stabilen Schema. Verworfen, weil community-gepflegt — die Datei kann
  still veralten oder lückenhaft sein (geprüft: `o4-mini` führt `/v1/responses` nicht in
  `supported_endpoints`, obwohl es dort funktioniert). Eine falsche Zahl, die aussieht als käme
  sie aus einer offiziellen Quelle, ist schlechter als ein leeres Feld.
- **Crawlen von `platform.openai.com/docs/pricing`.** Ist möglich (HTTP 200, serverseitig
  gerendertes HTML, `robots.txt` erlaubt `/docs/`), liefert aber pro Modell acht und mehr Zahlen
  über vier Tarifstufen ohne IDs oder Schema. Ein Redesign bricht den Parser still, mit falschen
  Werten als Ergebnis statt mit einem Fehler. Kontextfenster und Parametergültigkeit stehen dort
  ohnehin nicht.
- **`/v1/models` der OpenAI-API.** Liefert nur Namen — keine Preise, keine Limits, keine
  Fähigkeiten. Als Preisquelle unbrauchbar.

## Konsequenzen

- Das Register wird mit Modellnamen und Fähigkeitsflags ausgeliefert, die Preisfelder sind leer.
- Ein Modell ohne gepflegte Preise ist ausführbar. Die Modellauswahl weist darauf hin, die
  Kostenspalten bleiben leer.
- Preise altern durch Nichtstun. Das ist sichtbar (leere oder erkennbar alte Werte) statt still.
