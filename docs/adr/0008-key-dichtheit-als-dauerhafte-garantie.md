---
status: accepted
---

# Key-Dichtheit als dauerhafte Garantie

Der API-Key reist architektonisch nur im Header und ausschließlich zum Responses-Client
(SPEC.md, "Umgang mit dem Key"). Das allein schützt nicht vollständig: ein Nutzer kann seinen
Key auch versehentlich in einen System- oder User-Prompt tippen, und dieser Text landet über
`request_json`, den Arbeitsstand-Schnappschuss eines Laufs und die Antwort in der Datenbank.

**Entscheidung:** Zusätzlich zur architektonischen Trennung läuft vor jedem Schreiben einer
Text-Spalte eine Bereinigung (`app/domain/key_sanitizer.py`), die key-artige Zeichenketten
(`sk-…`) durch einen Platzhalter ersetzt — Gürtel zum Hosenträger. Der Choke Point liegt in den
SQLite-Adaptern: `arbeitsstand_to_params` für Profil und Lauf, `_call_to_params` für Call. Beide
Repositories laufen unter `.importlinter`s `core-is-clean`-Kontrakt nicht — der Sanitizer selbst
liegt aber bewusst in `domain/`, weil er reine, framework-freie String-Logik ist und von den
Adaptern importiert werden darf (`adapters → application → domain`).

Der HTTP-Test, der das im Zusammenspiel prüft — ein Lauf mit Key im Header und einem
key-artigen Text im Prompt, danach keine Spalte irgendeiner Zeile mit der Key-Zeichenkette
(SPEC.md, Testing Decisions) — ist die einzige Absicherung dieser Garantie. Er darf nie
ersatzlos gelöscht werden.

## Konsequenzen

- Wer den Sanitizer entfernt, verschiebt oder seinen Choke Point ändert, muss den
  Key-Dichtheitstest weiterhin grün halten oder durch einen gleichwertigen Test ersetzen.
- Die Bereinigung ist irreversibel und läuft blind auf jedem Text, der in `profil`, `lauf` oder
  `call` geschrieben wird — auch auf harmlosem Text, der zufällig auf `sk-` passt. Das ist der
  bewusst gezahlte Preis für Zero-Leakage statt Precision.
- Eine künftige Änderung des Musters (z. B. weitere Anbieter-Präfixe) ändert nur
  `key_sanitizer.py`, nicht die Aufrufstellen in den Repositories.
