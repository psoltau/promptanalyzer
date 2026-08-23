# 02 — Key-Handling und Key-Dichtheit

**What to build:** Der Prompt-Optimierer trägt seinen API-Key im Frontend ein und muss ihn nach
einem Reload nicht neu einfügen. Er sieht, welche Key-Quelle gerade wirkt — eingetragenes Feld
oder Prozessumgebung —, damit er bei einem Autorisierungsfehler weiß, welchen Key er reparieren
muss. Ein Statusendpunkt meldet dem Frontend, ob überhaupt ein Umgebungs-Key vorhanden ist.

Der Key landet nie in der Datenbank: er wird nur als Header entgegengenommen, ausschließlich an
den Responses-Client weitergegeben, und das gespeicherte `request_json` enthält den Anfragekörper
ohne Header. Zusätzlich läuft vor jedem Schreiben eine Bereinigung über den zu speichernden Text,
die Key-artige Zeichenketten entfernt — als Gürtel zum Hosenträger, weil der Nutzer seinen Key
auch in einen Prompt tippen kann. Danach kann die SQLite-Datei weitergegeben oder eingecheckt
werden, ohne ein Geheimnis zu verteilen.

**Blocked by:** 01 — Tracer Bullet: Profil, Arbeitsstand, ein Lauf mit einem Call.

**Status:** ready-for-agent

- [ ] Key-Feld im Frontend überlebt einen Reload
- [ ] Statusendpunkt meldet, ob ein Umgebungs-Key vorhanden ist; das Frontend zeigt die wirkende Quelle an
- [ ] Key reist nur im Header, nie im Body und nie in der URL
- [ ] Gespeichertes `request_json` enthält keine Header
- [ ] Bereinigung entfernt Key-artige Zeichenketten aus jedem zu speichernden Text vor dem Schreiben
- [ ] Key-Dichtheitstest: nach Läufen mit Key im Header und key-artigem Text im Prompt enthält keine Spalte irgendeiner Zeile die Key-Zeichenkette. Dieser Test darf nie gelöscht werden, ohne ihn zu ersetzen
