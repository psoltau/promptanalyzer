# 04 — Call-Detail als aufklappbarer Bereich

**What to build:** Der Prompt-Optimierer klappt eine Zeile der Vergleichstabelle auf und liest
dort alles, was keine Spalte hat: den vollen Antworttext, um zu beurteilen ob die billigere
Variante inhaltlich noch taugt; den vollständigen eingefrorenen Prompt-Stand des Laufs, um
nachzuvollziehen welche Formulierung zu welcher Zahl geführt hat; das rohe Request- und
Response-JSON für alles Übrige. Bei einem fehlgeschlagenen Call steht dort die API-Fehlermeldung,
damit „Modell X akzeptiert diese Einstellung nicht" ein festgehaltenes Ergebnis ist und nicht eine
Erinnerung.

Im Bereich der gecachten Input-Tokens steht ein Hinweis, dass Prompt-Caching erst ab einem
gemeinsamen Prefix von etwa tausend Tokens greift — damit eine dauerhafte Null bei kurzen
Testprompts nicht dem Modell oder dem Werkzeug angelastet wird.

**Blocked by:** 03 — Vergleichstabelle über die Profil-Historie.

**Status:** ready-for-agent

- [ ] Zeile aufklappen zeigt den vollen Antworttext
- [ ] Der Prompt- und Einstellungs-Schnappschuss des Laufs ist vollständig sichtbar
- [ ] Rohes Request- und Response-JSON sind sichtbar
- [ ] Bei Status `error` ist der Fehlertext lesbar
- [ ] Hinweis zu gecachten Input-Tokens (~1000 Tokens gemeinsamer Prefix) ist an der richtigen Stelle sichtbar
- [ ] Erfüllt `standards/`; die Verifikationsschritte aus `standards/architecture_backend.md` §9 laufen grün
