# Single-Turn ist eine Grenze, keine Bequemlichkeit

Ein Lauf ist genau ein Request pro Call. Es gibt keinen Tool-Ausführungs-Loop, kein
`previous_response_id`, keine Konversationen. Das ist eine Scope-Grenze mit Begründung, keine
noch nicht erledigte Arbeit.

Innerhalb der Grenze liegen: **Tool-Definitionen**, die mitgesendet aber nie ausgeführt werden —
messbar ist, was sie an Input-Tokens kosten und ob das Modell sie wählen würde; und
**Web-Suche**, die OpenAI serverseitig ausführt und deren Ergebnis als Teil einer Antwort
zurückkommt. Außerhalb liegt alles, was einen zweiten Request desselben Gedankengangs braucht.

Die Grenze ist durch Web-Suche subtil geworden: dieses Werkzeug führt intern mehrere Schritte
aus, ohne dass das Werkzeug einen zweiten Request stellt. Das ist genau das Kriterium — nicht
„wie viele Schritte passieren", sondern „stellt die Messbank einen oder mehr Requests". Sie misst
einen Request, kein Gespräch. Ein Tool-Loop würde Datenmodell und Oberfläche verdoppeln, um eine
Frage zu beantworten, die bei Prompt-Optimierung selten gestellt wird.
