# 08 — Mehrere Modelle und Wiederholungen

**What to build:** Der Prompt-Optimierer wählt mehrere Modelle für einen Lauf und gibt eine
Wiederholungszahl an, damit er denselben Prompt nicht von Hand mehrfach abschicken muss und sehen
kann, wie sich gecachte Input-Tokens ab dem zweiten identischen Call verhalten. Vor dem Ausführen
sieht er, wie viele Calls daraus entstehen (Modelle × Wiederholungen), damit er nicht versehentlich
achtzehn bezahlte Anfragen auslöst.

Beim Ausführen werden die Modelle parallel angefragt, damit er nicht sechsmal nacheinander wartet;
die Wiederholungen innerhalb eines Modells laufen strikt seriell nach Index, weil nur so der erste
Call den Cache füllen und die folgenden ihn treffen können. Jeder Call wird für sich abgeschlossen
und geschrieben: schlägt einer fehl, entsteht dafür eine `error`-Zeile mit Fehlertext, und die
übrigen Calls des Laufs laufen unberührt weiter — ein nicht freigeschaltetes Modell ruiniert nicht
den ganzen Lauf.

In der Vergleichstabelle steht pro Lauf zusätzlich eine Aggregatzeile, damit ein Lauf mit achtzehn
Calls als eine Zahl mit einem anderen Lauf verglichen werden kann.

**Blocked by:** 03 — Vergleichstabelle über die Profil-Historie.

**Status:** ready-for-agent

- [ ] Mehrfach-Modellauswahl und Wiederholungszahl sind Teil des Arbeitsstands und werden mit dem Lauf eingefroren
- [ ] Vorschau der entstehenden Call-Anzahl vor dem Ausführen
- [ ] Aus Modelle × Wiederholungen entsteht die richtige Anzahl Calls mit korrekten `wiederholung_index` ab 1
- [ ] Wiederholungen eines Modells erreichen den Responses-Client streng nacheinander; verschiedene Modelle dürfen sich überlappen
- [ ] Fehlerisolation: ein geworfener Fehler für ein Modell erzeugt eine `error`-Zeile mit Fehlertext, die Calls der anderen Modelle sind vollständig vorhanden
- [ ] Aggregatzeile je Lauf in der Vergleichstabelle
