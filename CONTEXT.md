# Prompting Analyzer

Ein lokales Werkzeug, um Prompts für die OpenAI Responses API manuell zu verbessern. Es misst
und protokolliert, was ein Prompt kostet und liefert — es optimiert selbst nichts.

## Language

**Profil**:
Ein benannter Optimierungsverlauf für genau einen zu verbessernden Prompt. Enthält die
Historie aller Läufe zu diesem Prompt und ist die Einheit, in der Entwicklung sichtbar wird.
_Avoid_: Projekt, Session, Experiment, Workspace

**Arbeitsstand**:
Der aktuell bearbeitete, noch nicht ausgeführte Stand aus Prompt-Texten und Einstellungen eines
Profils. Überlebt einen Reload und wird durch Ausführen zu einem Lauf.
_Avoid_: Draft, Entwurf, Formular, Working Copy

**Lauf**:
Eine Ausführung innerhalb eines Profils mit einem eingefrorenen Stand aus Prompt-Texten und
Einstellungen. Ein Lauf ist unveränderlich, sobald er ausgeführt ist.
_Avoid_: Run, Test, Durchgang, Iteration

**Call**:
Eine einzelne Anfrage an die Responses API und deren Antwort. Ein Lauf besteht aus einem oder
mehreren Calls.
_Avoid_: Request, Anfrage, Aufruf

**Tool-Definition**:
Ein Funktionsschema, das einem Lauf mitgegeben wird, damit messbar ist, was es an Input-Tokens
kostet und ob das Modell es wählen würde. Wird nie ausgeführt.
_Avoid_: Function, Tool, Schema, Werkzeug

**Web-Suche**:
Das einzige serverseitig ausgeführte Werkzeug, das ein Lauf aktivieren kann. Verursacht Kosten
je Suchanfrage zusätzlich zu den Tokens des zurückgelieferten Inhalts.
_Avoid_: web_search, Websuche, Recherche, Suchtool

**Wiederholung**:
Eine der mehreren aufeinanderfolgenden, identischen Anfragen eines Laufs an dasselbe Modell.
Jede Wiederholung ist ein eigener Call mit fortlaufendem Index.
_Avoid_: Retry, Repeat, Durchlauf

**Modell-Register**:
Die im Werkzeug selbst gepflegte Tabelle der nutzbaren Modelle mit ihren Preisen, Kontextfenstern und
erlaubten Einstellungen. Sie entscheidet, welche Einstellung für welches Modell gültig ist.
_Avoid_: Modell-Liste, Model Config, Katalog

**Einstellungen**:
Die pro Lauf gewählten API-Parameter neben den Prompt-Texten — derzeit Modell,
`max_output_tokens` und `reasoning_effort`.
_Avoid_: Optionen, Config, Parameter-Set

**System Prompt**:
Der Anweisungstext eines Laufs; geht als `instructions` an die API.
_Avoid_: Instructions, Systemnachricht, Developer Message

**User Prompt**:
Der Eingabetext eines Laufs; geht als `input` an die API.
_Avoid_: Input, Nutzernachricht, Query

**Messbank**:
Die Rolle, die dieses Werkzeug einnimmt: Zahlen und Ausgaben sichtbar machen, damit ein
Mensch entscheidet. Abgrenzung zum Optimierer, der Prompts selbst umschreibt.
_Avoid_: Playground, Optimierer
