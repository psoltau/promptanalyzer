# 07 — Gating der Einstellungen aus dem Register

**What to build:** Die Oberfläche lügt nicht mehr über das, was ein Modell kann. Einstellungen,
die das gewählte Modell nach dem Register nicht unterstützt, sind ausgegraut — damit der
Prompt-Optimierer keine Läufe produziert, die nur in API-Fehlern enden. Bei der Modellauswahl
sieht er, für welche Modelle keine Preise gepflegt sind, damit ihn leere Kostenspalten hinterher
nicht überraschen. Ausführen kann er ein solches Modell trotzdem: Tokenverbrauch vergleichen geht
auch, bevor Zahlen eingetragen sind.

**Blocked by:** 05 — Modell-Register.

**Status:** ready-for-agent

- [ ] Nicht unterstützte Einstellungen sind für das gewählte Modell ausgegraut
- [ ] Modelle ohne gepflegte Preise sind in der Auswahl als solche erkennbar
- [ ] Ein Modell ohne gepflegte Preise ist trotzdem ausführbar
- [ ] Das Gating folgt ausschließlich den Fähigkeitsschaltern des Registers, nicht einer fest verdrahteten Liste
- [ ] Erfüllt `standards/`; die Verifikationsschritte aus `standards/architecture_backend.md` §9 laufen grün
