# Prompting Analyzer — Spezifikation v1

Vokabular durchgehend nach [CONTEXT.md](./CONTEXT.md). Entscheidungen mit Tragweite stehen in
[docs/adr/](./docs/adr/) und werden hier nicht neu begründet, nur angewandt.

## Problem Statement

Ich schreibe Prompts für die OpenAI Responses API und weiß nicht, was sie kosten und wie sie sich
über Modelle hinweg verhalten. Wenn ich einen System Prompt umbaue, kann ich nicht sagen, ob er
danach billiger oder teurer ist — ich sehe nur, dass eine Antwort kommt. Der Verbrauch steckt in
einem `usage`-Objekt, das ich im Playground nicht vollständig zu sehen bekomme, und die
interessanten Posten sind gerade die versteckten: gecachte Input-Tokens und Reasoning-Tokens, die
in der Output-Summe untergehen und bei Reasoning-Modellen den Preis dominieren. Erst recht
vergleichen kann ich nichts: die dritte Variante von gestern ist weg, sobald ich das Browsertab
geschlossen habe. Und wenn ein Lauf eine leere Antwort liefert, weiß ich nicht, ob der Prompt
schlecht war oder ob `max_output_tokens` zu klein war und das Modell sein gesamtes Budget in
Reasoning verbrannt hat — voll bezahlt, null Ertrag.

## Solution

Eine lokale Messbank. Ich lege pro zu optimierendem Prompt ein Profil an. Dort steht mein
Arbeitsstand: System Prompt, User Prompt, Tool-Definitionen und die Einstellungen. Ich wähle ein
oder mehrere Modelle und führe aus — daraus entsteht ein unveränderlicher Lauf mit einem Call pro
Modell und Wiederholung.

Das Profil zeigt danach eine flache, sortierbare Tabelle über alle Calls seiner gesamten
Geschichte: Modell, Einstellungen, Status, jeder einzelne Tokenposten getrennt, Anzahl der
Suchanfragen, Kosten und Dauer. Ich ändere den Arbeitsstand, führe erneut aus, und die neue Zeile
steht neben allen alten. Die Optimierung passiert in meinem Kopf; das Werkzeug liefert die Zahlen
und schweigt über Qualität ([ADR 0001](./docs/adr/0001-messbank-statt-optimierer.md)).

Preise pflege ich selbst in einem Register-Bildschirm
([ADR 0002](./docs/adr/0002-register-von-hand-gepflegt.md)), und einmal errechnete Kosten bleiben
für immer stehen ([ADR 0004](./docs/adr/0004-kosten-als-schnappschuss.md)).

## User Stories

Ein einziger Akteur: der **Prompt-Optimierer**, der das Werkzeug lokal für sich selbst startet.

### Profile

1. Als Prompt-Optimierer möchte ich beim Start eine Liste meiner Profile sehen, damit ich dort
   weitermache, wo ich aufgehört habe.
2. Als Prompt-Optimierer möchte ich ein neues Profil mit einem Namen anlegen, damit ich einen
   bestimmten Prompt über längere Zeit verfolgen kann.
3. Als Prompt-Optimierer möchte ich ein Profil umbenennen, damit sein Name noch passt, wenn sich
   mein Verständnis der Aufgabe geändert hat.
4. Als Prompt-Optimierer möchte ich ein Profil löschen, damit Experimente, die nichts geworden
   sind, meine Liste nicht zumüllen.
5. Als Prompt-Optimierer möchte ich sehen, wie viele Läufe ein Profil hat und wann es zuletzt
   benutzt wurde, damit ich in der Liste das Richtige finde.
6. Als Prompt-Optimierer möchte ich ein Profil samt Historie duplizieren, damit ich einen Prompt
   in eine zweite Richtung entwickeln kann, ohne den bisherigen Verlauf zu verlieren.

### Arbeitsstand

7. Als Prompt-Optimierer möchte ich System Prompt und User Prompt in getrennten, großen
   Textfeldern eingeben, damit ich lange Prompts überhaupt bearbeiten kann.
8. Als Prompt-Optimierer möchte ich, dass mein Arbeitsstand automatisch erhalten bleibt, damit ein
   halbfertiger Entwurf nicht verloren geht, wenn ich das Tab wechsle oder neu lade.
9. Als Prompt-Optimierer möchte ich sehen, wann der Arbeitsstand zuletzt gespeichert wurde, damit
   ich dem automatischen Speichern trauen kann.
10. Als Prompt-Optimierer möchte ich den Arbeitsstand aus einem früheren Lauf zurückholen, damit
    ich von einer Variante aus weiterarbeiten kann, die besser war als meine aktuelle.
11. Als Prompt-Optimierer möchte ich beim Zurückholen gewarnt werden, dass mein aktueller
    Arbeitsstand dabei überschrieben wird, damit ich ihn nicht versehentlich verliere.
12. Als Prompt-Optimierer möchte ich Tool-Definitionen als JSON einfügen, damit ich messen kann,
    was meine Werkzeugschemas an Input-Tokens kosten.
13. Als Prompt-Optimierer möchte ich sofort sehen, wenn mein Tool-JSON syntaktisch kaputt ist,
    damit ich das nicht erst durch einen fehlgeschlagenen API-Call erfahre.

### Einstellungen und Modellauswahl

14. Als Prompt-Optimierer möchte ich `max_output_tokens` setzen, damit ich das Kostenrisiko eines
    Testlaufs begrenzen kann.
15. Als Prompt-Optimierer möchte ich `reasoning_effort` setzen, damit ich messen kann, was
    Nachdenken kostet und ob es die Antwort verbessert.
16. Als Prompt-Optimierer möchte ich mehrere Modelle für einen Lauf auswählen, damit ich denselben
    Prompt nicht von Hand mehrfach abschicken muss.
17. Als Prompt-Optimierer möchte ich, dass Einstellungen, die das gewählte Modell nicht
    unterstützt, ausgegraut sind, damit ich keine Läufe produziere, die nur in API-Fehlern enden.
18. Als Prompt-Optimierer möchte ich bei der Modellauswahl sehen, für welche Modelle keine Preise
    gepflegt sind, damit mich leere Kostenspalten hinterher nicht überraschen.
19. Als Prompt-Optimierer möchte ich trotzdem ein Modell ohne gepflegte Preise ausführen können,
    damit ich Tokenverbrauch vergleichen kann, bevor ich Zahlen eintrage.
20. Als Prompt-Optimierer möchte ich Web-Suche für einen Lauf aktivieren, damit ich messen kann,
    was ein recherchierender Prompt kostet.
21. Als Prompt-Optimierer möchte ich `search_context_size` wählen, damit ich den einzigen Hebel
    testen kann, mit dem sich der Token-Anteil der Web-Suche beeinflussen lässt.
22. Als Prompt-Optimierer möchte ich, dass die Web-Such-Optionen nur erscheinen, wenn das gewählte
    Modell sie unterstützt, damit die Oberfläche nicht lügt.
23. Als Prompt-Optimierer möchte ich eine Wiederholungszahl angeben, damit ich sehen kann, wie sich
    gecachte Input-Tokens ab dem zweiten identischen Call verhalten.
24. Als Prompt-Optimierer möchte ich vor dem Ausführen sehen, wie viele Calls daraus entstehen
    (Modelle × Wiederholungen), damit ich nicht versehentlich achtzehn bezahlte Anfragen auslöse.

### API-Key

25. Als Prompt-Optimierer möchte ich meinen API-Key im Frontend eintragen, damit ich das Werkzeug
    ohne Umgebungsgefummel benutzen kann.
26. Als Prompt-Optimierer möchte ich, dass der eingetragene Key im Browser erhalten bleibt, damit
    ich ihn nicht bei jedem Reload neu einfüge.
27. Als Prompt-Optimierer möchte ich, dass ein in der Umgebung gesetzter Key automatisch genutzt
    wird, damit ich gar nichts eintragen muss, wenn er schon in meiner Shell steht.
28. Als Prompt-Optimierer möchte ich, dass mein Key nie in der Datenbank landet, damit ich die
    SQLite-Datei weitergeben oder einchecken kann, ohne ein Geheimnis zu verteilen.
29. Als Prompt-Optimierer möchte ich sehen, welche Key-Quelle gerade wirkt (Feld oder Umgebung),
    damit ich bei einem Autorisierungsfehler weiß, welchen Key ich reparieren muss.

### Ausführen

30. Als Prompt-Optimierer möchte ich, dass die gewählten Modelle parallel angefragt werden, damit
    ich nicht sechsmal nacheinander warte.
31. Als Prompt-Optimierer möchte ich, dass Wiederholungen innerhalb eines Modells seriell laufen,
    damit der erste Call den Cache füllen kann und die folgenden ihn treffen können.
32. Als Prompt-Optimierer möchte ich Ergebniszeilen erscheinen sehen, sobald der jeweilige Call
    fertig ist, damit ich bei langsamen Reasoning-Modellen nicht auf ein leeres Bild starre.
33. Als Prompt-Optimierer möchte ich, dass ein fehlgeschlagener Call die übrigen Calls desselben
    Laufs nicht abbricht, damit ein nicht freigeschaltetes Modell mir nicht den ganzen Lauf ruiniert.
34. Als Prompt-Optimierer möchte ich sehen, dass ein Lauf noch läuft und wie viele seiner Calls
    fertig sind, damit ich weiß, ob ich warten muss.
35. Als Prompt-Optimierer möchte ich, dass ein Lauf nach dem Ausführen unveränderlich ist, damit
    ein Vergleich, den ich gestern gezogen habe, morgen noch dasselbe bedeutet.

### Vergleichen

36. Als Prompt-Optimierer möchte ich alle Calls eines Profils in einer flachen Tabelle sehen,
    damit ich die Entwicklung meines Prompts auf einen Blick habe.
37. Als Prompt-Optimierer möchte ich die Tabelle nach jeder Spalte sortieren, damit ich „welcher
    Lauf war am billigsten" und „welcher am schnellsten" direkt beantworten kann.
38. Als Prompt-Optimierer möchte ich Input-, gecachte Input-, Reasoning- und Output-Tokens in
    getrennten Spalten sehen, damit die Reasoning-Kosten nicht in der Output-Summe verschwinden.
39. Als Prompt-Optimierer möchte ich eine laute Statusspalte mit `complete`, `incomplete
    (max_output_tokens)` und `error` sehen, damit ich nicht Läufe vergleiche, die gar kein
    vergleichbares Ergebnis haben.
40. Als Prompt-Optimierer möchte ich die Anzahl der Suchanfragen als eigene Spalte sehen, damit ich
    verstehe, warum zwei sonst gleiche Läufe unterschiedlich teuer waren.
41. Als Prompt-Optimierer möchte ich die Kosten jedes Calls in USD sehen, damit ich Modelle mit
    unterschiedlichen Preisen überhaupt vergleichen kann.
42. Als Prompt-Optimierer möchte ich die Dauer jedes Calls sehen, damit ich Kosten gegen Latenz
    abwägen kann.
43. Als Prompt-Optimierer möchte ich pro Lauf eine Aggregatzeile sehen, damit ich einen Lauf mit
    achtzehn Calls als eine Zahl mit einem anderen Lauf vergleichen kann.
44. Als Prompt-Optimierer möchte ich eine Zeile aufklappen und den vollen Antworttext lesen, damit
    ich beurteilen kann, ob die billigere Variante inhaltlich noch taugt.
45. Als Prompt-Optimierer möchte ich im Detail den vollständigen Prompt-Stand des Laufs sehen,
    damit ich nachvollziehen kann, welche Formulierung zu welcher Zahl geführt hat.
46. Als Prompt-Optimierer möchte ich im Detail das rohe Request- und Response-JSON sehen, damit ich
    Dinge nachsehen kann, für die das Werkzeug keine Spalte hat.
47. Als Prompt-Optimierer möchte ich bei einem fehlgeschlagenen Call die API-Fehlermeldung im
    Detail lesen, damit „Modell X akzeptiert diese Einstellung nicht" ein festgehaltenes Ergebnis
    ist und nicht eine Erinnerung.
48. Als Prompt-Optimierer möchte ich einen Hinweis sehen, dass gecachte Input-Tokens einen
    gemeinsamen Prefix von ungefähr tausend Tokens brauchen, damit ich eine Null dort nicht dem
    Modell anlaste.

### Modell-Register

49. Als Prompt-Optimierer möchte ich ein Register aller nutzbaren Modelle bearbeiten, damit ich
    nicht auf ein Update des Werkzeugs warten muss, um ein neues Modell zu testen.
50. Als Prompt-Optimierer möchte ich ein neues Modell nur mit seinem Namen anlegen können, damit
    ich ein gerade erschienenes Modell sofort ausprobieren kann.
51. Als Prompt-Optimierer möchte ich, dass ein neu angelegtes Modell zunächst alle Einstellungen
    erlaubt, damit ich nicht raten muss, bevor ich es überhaupt einmal angefragt habe.
52. Als Prompt-Optimierer möchte ich Input-, gecachten Input-, Output- und Suchpreis je Modell
    eintragen, damit die Kostenspalte stimmt.
53. Als Prompt-Optimierer möchte ich Preise in der Einheit eintragen, in der OpenAI sie ausweist
    (USD je Million Tokens), damit ich beim Abtippen nicht mit Nullen rechne.
54. Als Prompt-Optimierer möchte ich das Kontextfenster eines Modells eintragen, damit ich sehen
    kann, wie weit mein Prompt davon entfernt ist.
55. Als Prompt-Optimierer möchte ich je Modell schalten, ob es `reasoning_effort`, Web-Suche und
    Prompt-Caching unterstützt, damit die Oberfläche ungültige Einstellungen ausgrauen kann.
56. Als Prompt-Optimierer möchte ich ein Register mit Modellnamen und Fähigkeiten, aber leeren
    Preisfeldern ausgeliefert bekommen, damit ich beim ersten Start nicht eine halbe Stunde
    Formulare ausfülle — und keine mitgelieferte Zahl fälschlich für aktuell halte.
57. Als Prompt-Optimierer möchte ich ein Modell aus dem Register entfernen, damit meine
    Auswahlliste nicht aus vierzig Namen besteht.
58. Als Prompt-Optimierer möchte ich, dass das Entfernen eines Modells alte Calls nicht anrührt,
    damit meine Historie überlebt, wenn ich das Register aufräume.

### Kosten

59. Als Prompt-Optimierer möchte ich, dass gecachte Input-Tokens zum reduzierten Satz gerechnet
    werden, damit die Kostenzahl den Vorteil des Caches abbildet.
60. Als Prompt-Optimierer möchte ich, dass Reasoning-Tokens als Output-Tokens bepreist werden und
    nicht doppelt, damit die Kostenzahl stimmt.
61. Als Prompt-Optimierer möchte ich, dass die Kosten der Web-Suche enthalten sind, damit eine
    Kostenspalte nicht den größten Posten eines Suchlaufs verschweigt.
62. Als Prompt-Optimierer möchte ich, dass eine Preiskorrektur im Register alte Läufe nicht
    verändert, damit ein gestern gezogener Vergleich gültig bleibt.
63. Als Prompt-Optimierer möchte ich die tatsächlich verwendeten Preissätze im Detail eines Calls
    sehen, damit ich jede Kostenzahl nachrechnen kann.
64. Als Prompt-Optimierer möchte ich die Kosten eines Laufs auf ausdrückliche Anweisung neu
    berechnen können, damit ich einen echten Tippfehler im Register reparieren kann.
65. Als Prompt-Optimierer möchte ich, dass Kostenspalten leer bleiben statt Null zu zeigen, wenn
    kein Preis gepflegt ist, damit ich „kostenlos" nicht mit „unbekannt" verwechsle.

## Implementation Decisions

### Aufbau

- Ein einziger Python-Prozess: FastAPI hinter Uvicorn, SQLite über `sqlite3` aus der Standard-
  bibliothek, kein ORM, keine Migrationsbibliothek. Das Schema wird beim Start idempotent angelegt.
- Das Frontend ist eine statisch ausgelieferte Seite mit Vanilla JS ohne Build-Schritt. Kein npm,
  kein Bundler. Datenaustausch ausschließlich über die untenstehenden JSON-Endpunkte.
- Vier Bildschirme: Profil-Liste, Profil (Arbeitsstand oben, Vergleichstabelle unten),
  Call-Detail als aufklappbarer Bereich in der Tabelle, Register.
- Der Zugriff auf die Responses API liegt hinter **einer** schmalen Schnittstelle mit einer
  Operation. Sie ist der einzige Ort im System, der das Netz berührt, und der einzige Seam.

### Datenmodell

Vier Tabellen. Alle Zeitangaben als UTC-Zeitstempel, alle Geldbeträge als USD.

**`profil`** — `id`, `name`, `erstellt_am`, `arbeitsstand_geaendert_am`, dazu die Arbeitsstands-
felder: `system_prompt`, `user_prompt`, `tools_json`, `modelle` (Namensliste), `max_output_tokens`,
`reasoning_effort`, `web_suche`, `search_context_size`, `wiederholungen`.

**`lauf`** — `id`, `profil_id`, `nummer` (fortlaufend je Profil, das ist die im Frontend
angezeigte Lauf-Nummer), `gestartet_am`, `beendet_am`, plus derselbe Satz Prompt- und
Einstellungsfelder wie am Profil, hier als eingefrorener Schnappschuss. Nach dem Anlegen werden
diese Felder nie geschrieben.

**`call`** — `id`, `lauf_id`, `modell_name`, `wiederholung_index` (ab 1), `status`
(`complete` | `incomplete` | `error`), `incomplete_grund`, `fehlertext`, `dauer_ms`,
`input_tokens`, `cached_input_tokens`, `reasoning_tokens`, `output_tokens`, `total_tokens`,
`web_search_calls`, `antwort_text`, `request_json`, `response_json`, `erstellt_am`, sowie die vier
Preis-Schnappschüsse `preis_input`, `preis_cached_input`, `preis_output`, `preis_suche` und
`kosten_usd`. Alle Kosten- und Preisfelder sind nullbar; `null` bedeutet „unbekannt", nicht „null".

**`modell`** — `name` als Primärschlüssel, `preis_input`, `preis_cached_input`, `preis_output`,
`preis_suche` (alle nullbar, Einheit USD je Million Tokens bzw. USD je Suchanfrage),
`kontextfenster`, und die drei Fähigkeitsschalter `erlaubt_reasoning_effort`, `erlaubt_web_suche`,
`unterstuetzt_prompt_caching`. Beim ersten Start wird eine Saatliste von Modellnamen mit
Fähigkeitsschaltern eingefügt, Preisfelder leer. Ein neu angelegtes Modell hat alle drei Schalter
auf „erlaubt".

`call.modell_name` ist bewusst ein Textfeld ohne Fremdschlüssel auf `modell`: Historie muss ein
Aufräumen des Registers überleben.

### API-Vertrag

Konkrete Pfade, Payloads und Fehlercodes: [docs/api.md](./docs/api.md).

- Profile: auflisten, anlegen, lesen, umbenennen, löschen, duplizieren.
- Arbeitsstand: ganzheitlich schreiben (das Frontend speichert entprellt nach dem Tippen), und
  „aus Lauf N übernehmen", das den Schnappschuss eines Laufs in den Arbeitsstand kopiert.
- Lauf: anlegen und starten. Der Endpunkt friert den Arbeitsstand ein, legt die `lauf`-Zeile an und
  kehrt **sofort** mit `lauf_id` zurück; die Calls laufen in einer Hintergrundaufgabe. Grund: sechs
  Modelle × drei Wiederholungen gegen ein Reasoning-Modell überschreiten jede vernünftige
  Request-Zeit.
- Calls eines Profils: die flache Tabelle, chronologisch. Dieser Endpunkt ist gleichzeitig der
  Fortschrittsanzeiger — das Frontend pollt ihn im Sekundenrhythmus, solange ein Lauf kein
  `beendet_am` hat, und Zeilen erscheinen, wie sie fertig werden.
- Call-Detail: Antworttext, Prompt-Schnappschuss, Preis-Schnappschüsse, rohes Request- und
  Response-JSON, Fehlertext.
- Lauf: Kosten neu berechnen (ausdrücklich angestoßen, überschreibt Preis-Schnappschüsse und
  `kosten_usd` dieses Laufs aus dem aktuellen Register).
- Register: auflisten, Modell anlegen, Modell ändern, Modell löschen.
- Der API-Key reist als Header mit jedem ausführenden Request mit, nie im Body und nie in der URL.
  Fehlt er im Header, greift `OPENAI_API_KEY` aus der Prozessumgebung. Ein Statusendpunkt meldet,
  ob ein Umgebungs-Key vorhanden ist, damit das Frontend die wirkende Quelle anzeigen kann.

### Ausführungssemantik

- Ein Lauf erzeugt `Modelle × Wiederholungen` Calls. Über Modelle hinweg parallel, innerhalb eines
  Modells strikt seriell nach `wiederholung_index` — die Serialität ist die Voraussetzung dafür,
  dass Wiederholung 2 den vom ersten Call gefüllten Cache treffen kann.
- Jeder Call wird für sich abgeschlossen und geschrieben. Eine Ausnahme in einem Call erzeugt eine
  Zeile mit Status `error` und Fehlertext, ohne die übrigen Calls zu berühren.
- Statusableitung aus der Antwort: abgeschlossen → `complete`; unvollständig mit Grund
  `max_output_tokens` → `incomplete` mit gespeichertem Grund; Transport- oder API-Fehler → `error`.
- Tool-Definitionen gehen als `tools` mit und werden **nie** ausgeführt. Ein zurückgegebener
  Funktionsaufruf ist das Ergebnis des Laufs, nicht der Anfang eines Dialogs
  ([ADR 0003](./docs/adr/0003-single-turn-als-grenze.md)). Web-Suche wird als einziges Werkzeug
  serverseitig ausgeführt; das Werkzeug stellt weiterhin genau einen Request.
- `web_search_calls` wird als Anzahl der Web-Such-Einträge im `output`-Array der Antwort bestimmt.
- Kein Streaming. `dauer_ms` ist serverseitig gemessene Wanduhrzeit um den einen Request.

### Kostenformel

Die Rechnung läuft einmal beim Schreiben des Calls und wird als `kosten_usd` festgeschrieben, samt
der vier verwendeten Preissätze. Zwei Feinheiten, an denen sich sonst ein doppeltes Zählen
einschleicht:

- Die von der API gemeldeten Input-Tokens **enthalten** die gecachten. Zu bepreisen sind daher
  `input_tokens - cached_input_tokens` zum Input-Satz und `cached_input_tokens` zum reduzierten Satz.
- Die gemeldeten Output-Tokens **enthalten** die Reasoning-Tokens. Reasoning wird deshalb nicht
  gesondert bepreist; die eigene Spalte ist reine Sichtbarmachung.

Dazu `web_search_calls × Suchpreis`. Fehlt einer der benötigten Preise, bleibt `kosten_usd` `null`
und die Spalte leer.

### Umgang mit dem Key

Der Key wird nur als Header entgegengenommen und ausschließlich an den Responses-Client
weitergegeben. Das gespeicherte `request_json` enthält den Anfragekörper, nie Header. Zusätzlich
läuft vor jedem Schreiben eine Bereinigung über den zu speichernden Text, die Key-artige
Zeichenketten entfernt — als Gürtel zum Hosenträger, weil ein Nutzer seinen Key auch in einen
Prompt tippen kann.

## Testing Decisions

**Was ein guter Test hier ist.** Er spricht das System durch HTTP an, wie das Frontend es tut, und
prüft, was danach über HTTP wieder herauskommt. Er nennt keine Modul-, Klassen- oder Funktionsnamen
des Produktionscodes außer der App selbst und dem Attrappen-Client. Er prüft nie, dass eine
bestimmte Funktion aufgerufen wurde, sondern immer, dass das beobachtbare Ergebnis stimmt: welche
Zeilen erscheinen, welche Zahlen sie tragen, welchen Status. Dadurch kann die interne Aufteilung in
Module beliebig umgebaut werden, ohne einen Test anzufassen.

**Der einzige Seam** ist der Responses-Client. Die Attrappe wird beim Aufbau der Testanwendung
eingesetzt und liefert vorbereitete Antworten: vollständige Antworten mit frei wählbaren
`usage`-Werten inklusive gecachter und Reasoning-Tokens, unvollständige Antworten mit Grund
`max_output_tokens`, Antworten mit einer wählbaren Anzahl Web-Such-Einträge, und geworfene Fehler.
Sie protokolliert außerdem die empfangenen Anfragen und deren Reihenfolge, damit die
Ausführungsordnung prüfbar ist. Kein weiterer Mock: SQLite läuft als echte Datei in einem
Temp-Verzeichnis, die Kostenrechnung läuft echt.

**Was geprüft wird**, jeweils durch HTTP:

- Profil-Lebenszyklus: anlegen, umbenennen, löschen, duplizieren mitsamt Historie.
- Arbeitsstand überlebt, „aus Lauf übernehmen" kopiert den Schnappschuss.
- Ein Lauf friert seinen Prompt-Stand ein: nachträgliche Änderung des Arbeitsstands lässt die
  Lauf-Felder unberührt.
- Aus `Modelle × Wiederholungen` entsteht die richtige Anzahl Calls mit korrekten Indizes.
- **Reihenfolge:** Wiederholungen eines Modells erreichen die Attrappe streng nacheinander;
  verschiedene Modelle dürfen sich überlappen.
- **Fehlerisolation:** wirft die Attrappe für ein Modell, entsteht dafür eine `error`-Zeile mit
  Fehlertext, und die Calls der anderen Modelle sind vollständig vorhanden.
- Statusableitung für alle drei Zustände, inklusive gespeichertem `incomplete`-Grund.
- Kostenformel: gecachter Anteil zum reduzierten Satz; Reasoning nicht doppelt; Suchanfragen
  addiert; fehlender Preis führt zu `null` und nicht zu `0`.
- **Preis-Schnappschuss:** Preis im Register ändern und prüfen, dass Kosten und Preisfelder alter
  Calls unverändert sind — und dass die ausdrückliche Neuberechnung sie ändert.
- Register: Saatliste beim ersten Start vorhanden mit leeren Preisen; neues Modell erlaubt alles;
  Löschen eines Modells lässt bestehende Calls stehen.
- Anzahl der Suchanfragen wird aus der Antwortstruktur korrekt gezählt.
- **Key-Dichtheit:** nach Läufen mit einem Key im Header und einem key-artigen Text im Prompt
  enthält keine Spalte irgendeiner Zeile die Key-Zeichenkette. Dieser Test ist in
  [ADR-Nähe](./docs/adr/) und darf nie gelöscht werden, ohne ihn zu ersetzen.
- Umgebungs-Key greift, wenn der Header fehlt; Header gewinnt, wenn beides da ist.

**Prior Art:** keine — grünes Feld. Diese Tests *sind* das Prior Art. Der erste geschriebene Test
legt das Muster fest: Testanwendung mit Attrappe und Temp-Datenbank aufbauen, durch HTTP treiben,
über HTTP prüfen.

## Out of Scope

Bewusst nicht in v1, jeweils mit dem Grund:

- **Automatisches Umschreiben von Prompts.** Es fehlt die Zielfunktion
  ([ADR 0001](./docs/adr/0001-messbank-statt-optimierer.md)).
- **Qualitätsbewertung, Notizen, Sterne, LLM-Judge.** Ausdrücklich verworfen. Folge: das Profil
  zeigt Kosten- und Verbrauchsentwicklung, nicht Qualitätsentwicklung.
- **Multi-Turn, `previous_response_id`, Konversationen, Tool-Ausführungs-Loop**
  ([ADR 0003](./docs/adr/0003-single-turn-als-grenze.md)).
- **Andere Werkzeuge als Web-Suche** — kein `file_search`, kein `code_interpreter`, keine
  MCP-Anbindung.
- **Structured Outputs** und andere Formatvorgaben.
- **Streaming** und damit Zeit-bis-erstes-Token. Nachrüstbar, ohne das Schema anzufassen.
- **Export.** Die SQLite-Datei liegt daneben, die Tabelle lässt sich markieren und kopieren.
- **Nutzerverwaltung, Authentifizierung, Mehrbenutzerbetrieb.** Ein lokales Werkzeug für eine Person.
- **Automatischer Preisabruf**, in jeder Form — externe Datensätze und Crawlen inklusive
  ([ADR 0002](./docs/adr/0002-register-von-hand-gepflegt.md)).
- **Andere Anbieter als OpenAI** und andere OpenAI-Endpunkte als die Responses API.
- **Sonderbehandlung von Läufen mit Web-Suche.** Ausdrücklich verworfen; siehe Risiko unten.
- **Batch- und Flex-Tarife.** Das Register kennt einen Preissatz je Posten, nicht vier Tarifstufen.

## Further Notes

### Umsetzungsreihenfolge

Jeder Schritt endet mit etwas Benutzbarem.

1. Ein Profil, ein Modell, ein Call, ein Lauf. Kein Register, keine Kosten, keine Wiederholungen.
   Prompt eingeben, ausführen, `usage`-Werte und Antworttext sehen. Ab hier ist das Werkzeug
   nützlich.
2. Vergleichstabelle und Profil-Historie: mehrere Läufe, flache Tabelle, Sortierung, Call-Detail,
   Statusspalte.
3. Register mit Preisen und Fähigkeitsschaltern, Kostenspalte samt Snapshot, Gating der
   Einstellungen.
4. Mehrfach-Modellauswahl mit parallelen Modellen, serielle Wiederholungen, Aggregatzeile.
5. Tool-Definitionen und Web-Suche mit `search_context_size` und Suchkosten.
6. Profil duplizieren, „aus Lauf übernehmen", Umbenennen und Löschen.

### Bekannte Risiken

- **Gecachte Input-Tokens bleiben oft bei null.** Prompt-Caching greift erst ab einem gemeinsamen
  Prefix von etwa tausend Tokens. Bei kurzen Testprompts zeigt die Spalte dauerhaft null — das ist
  richtig, sieht aber nach einem Fehler aus. Deshalb der Hinweis in der Oberfläche (Story 48).
- **Läufe mit Web-Suche sind nicht reproduzierbar** und ihre Cache-Quote liegt nahe null, weil sich
  der Prefix mit jedem Suchergebnis ändert. Auf eine Kennzeichnung wurde bewusst verzichtet; die
  Aggregatzeile zeigt Mittelwerte, die bei Suchläufen eine Streuung verdecken, die es gibt.
- **Das Register altert durch Nichtstun.** Gewollt, aber es heißt: eine Kostenzahl ist nur so gut
  wie der letzte Tag, an dem jemand Preise nachgetragen hat.
- **Der Antworttext ist das einzige Qualitätsurteil**, und er wird gelesen, nicht gespeichert. Wer
  in zwei Monaten wissen will, welche Variante inhaltlich die beste war, findet dazu keine Angabe —
  nur den Text zum Nachlesen.
