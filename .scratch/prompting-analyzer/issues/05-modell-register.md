# 05 — Modell-Register

**What to build:** Ein eigener Register-Bildschirm, in dem der Prompt-Optimierer die nutzbaren
Modelle selbst pflegt, damit er nicht auf ein Update des Werkzeugs warten muss, um ein gerade
erschienenes Modell zu testen. Beim ersten Start ist eine Saatliste von Modellnamen mit
Fähigkeitsschaltern vorhanden, die Preisfelder leer — damit keine mitgelieferte Zahl fälschlich
für aktuell gehalten wird und der erste Start nicht eine halbe Stunde Formulare bedeutet.

Er legt ein neues Modell nur mit dem Namen an; ein neues Modell erlaubt zunächst alle
Einstellungen. Er trägt Input-, gecachten Input-, Output- und Suchpreis ein, in der Einheit in der
OpenAI sie ausweist (USD je Million Tokens bzw. USD je Suchanfrage), dazu das Kontextfenster, und
schaltet je Modell `reasoning_effort`, Web-Suche und Prompt-Caching. Er entfernt ein Modell, wenn
die Auswahlliste zu lang wird — und seine Historie überlebt das: bestehende Calls bleiben
unverändert stehen.

Es gibt keinen Abruf von außen, in keiner Form.

**Blocked by:** 01 — Tracer Bullet: Profil, Arbeitsstand, ein Lauf mit einem Call.

**Status:** ready-for-agent

- [ ] Register auflisten, Modell anlegen, ändern, löschen — über HTTP und im Register-Bildschirm
- [ ] Beim ersten Start ist die Saatliste mit Fähigkeitsschaltern vorhanden und alle Preisfelder sind leer
- [ ] Ein neu angelegtes Modell braucht nur einen Namen und hat alle drei Fähigkeitsschalter auf „erlaubt"
- [ ] Preise werden in USD je Million Tokens eingetragen, Suchpreis in USD je Suchanfrage
- [ ] Kontextfenster und die drei Fähigkeitsschalter sind pflegbar
- [ ] Löschen eines Modells lässt bestehende Calls unverändert stehen
- [ ] Kein Netzzugriff zur Preisermittlung, weder beim Start noch später
