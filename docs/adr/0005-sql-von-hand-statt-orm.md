# SQL von Hand statt ORM

Persistenz läuft über `sqlite3` aus der Standardbibliothek mit handgeschriebenem,
parametrisiertem SQL. Kein ORM, kein SQLAlchemy, keine Migrationsbibliothek; das Schema wird
beim Start idempotent mit `CREATE TABLE IF NOT EXISTS` angelegt. Die Regel steht bindend in
[standards/architecture_backend.md](../../standards/architecture_backend.md); hier steht, warum
— damit sie nicht als vergessene Arbeit missverstanden und später „nachgerüstet" wird.

Der Grund ist die Kleinheit und Form des Datenmodells: vier Tabellen ohne Objektgraph, ein
Nutzer, eine Datei, ein DBMS. Wovon ein ORM lebt — Identity Map, Lazy Loading, Beziehungen
über mehrere Ebenen, Portabilität über Datenbanken hinweg — kommt hier nicht vor. Was
stattdessen vorkommt, hilft ihm nicht: rohe JSON-Blobs (`request_json`, `response_json`),
nullbare Preisfelder, deren `null` „unbekannt" bedeutet, ein bewusst fremdschlüsselloses
`call.modell_name` und eingefrorene Schnappschussfelder, die nach dem Anlegen nie wieder
geschrieben werden. Dagegen steht der Preis eines ORM: eine Laufzeitabhängigkeit für etwas, das
die Standardbibliothek kann, ein Mapping-Layer über einer Onion-Architektur, die SQL schon in
`adapters/sqlite/` einsperrt, und ein Migrationswerkzeug, dessen Versionsstände einem
idempotenten Schema beim Start widersprechen.

## Konsequenzen

- Schemaänderungen sind Handarbeit in `adapters/sqlite/schema.py`. Es gibt keine
  Versionsstände, kein `alembic upgrade`, und destruktive Änderungen sind ausgeschlossen —
  eine Spalte wird hinzugefügt, nicht umgebaut.
- Repositories mappen `sqlite3.Row` selbst auf Domänen-Dataclasses. Dieser Mapping-Code ist
  Absicht, keine fehlende Abstraktion.
- Wächst das Datenmodell über die vier Tabellen deutlich hinaus oder kommt ein zweites DBMS
  ins Spiel, ist diese ADR neu zu bewerten — nicht stillschweigend zu umgehen.
