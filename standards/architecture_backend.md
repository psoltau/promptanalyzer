# Architecture Rules

Onion/hexagonal. One process: FastAPI + Uvicorn, stdlib `sqlite3`, no ORM, no migrations,
static vanilla JS. These rules are binding. When a rule blocks a task, stop and ask — do not
work around it.

## 1. Layout

```
app/
  domain/            # entities, value objects, domain errors. stdlib only.
  application/       # use cases + ports (Protocols). imports domain only.
  adapters/
    http/            # FastAPI routers, Pydantic schemas, static/
    sqlite/          # connection, schema, repositories
    responses/       # the one network adapter
  main.py            # composition root: builds the object graph, wires FastAPI
tests/
.importlinter
```

No other top-level packages. No `utils/`, no `common/`, no `helpers/`.

## 2. The dependency rule

`adapters → application → domain`. Never the other way, never sideways between adapters.
`main.py` is the only module allowed to import from more than one adapter.

Core (`domain`, `application`) is framework-free: no `fastapi`, no `sqlite3`, no `pydantic`,
no HTTP client. If the core needs something from the outside, it declares a `Protocol` in
`application/ports.py` and an adapter implements it.

**`.importlinter` is frozen.** Never edit, weaken, or delete a contract. A failing contract
means the code is wrong.

```ini
[importlinter]
root_package = app

[importlinter:contract:layers]
name = Onion layers
type = layers
layers =
    app.main
    app.adapters
    app.application
    app.domain

[importlinter:contract:core-is-clean]
name = Core has no framework imports
type = forbidden
source_modules =
    app.domain
    app.application
forbidden_modules =
    fastapi
    starlette
    pydantic
    sqlite3
    httpx
    requests
    openai

[importlinter:contract:adapters-isolated]
name = Adapters do not know each other
type = independence
modules =
    app.adapters.http
    app.adapters.sqlite
    app.adapters.responses
```

## 3. Data types

- `domain/`: `@dataclass(frozen=True)`. Validate in `__post_init__`, raise domain errors.
- `adapters/http/schemas.py`: Pydantic, request/response shapes only.
- Mapping between them lives in `adapters/http/mappers.py`. A Pydantic model never crosses
  into `application/`; a domain dataclass is never returned from a route.
- Same rule for SQL: repositories map `sqlite3.Row` → domain dataclass. A `Row` never leaves
  `adapters/sqlite/`.

Optionality is a domain decision. If a field is required by the domain, it is required in the
dataclass even when the API accepts it as missing — the mapper rejects or defaults it.

## 4. The seam

Exactly one port for the Responses API, exactly one operation:

```python
# app/application/ports.py
class ModelGateway(Protocol):
    def run(self, request: ModelRequest) -> ModelResult: ...
```

- `app/adapters/responses/` is the **only** module in the repo that opens a socket.
- Do not add a second operation. Widen `ModelRequest`/`ModelResult` instead.
- A fake lives in `tests/fakes.py`. Every test uses the fake. Zero tests hit the network.
- Prompt text, model names, and API-shape details stay inside the adapter. The core does not
  know it is talking to an LLM.

## 5. HTTP edge

- Route handlers do four things: take dependencies, map request → use-case input, call **one**
  use case, map result → response. No branching on business conditions, no SQL, no `try`
  around business rules.
- Domain errors → HTTP status in **one** place: exception handlers registered in `main.py`.
  Never raise `HTTPException` outside `adapters/http/`.
- Endpoint paths and payloads come from the JSON endpoint spec. That spec was not included
  with these rules — ask for it before inventing an endpoint.

## 6. Persistence

- Schema in `adapters/sqlite/schema.py`, `CREATE TABLE IF NOT EXISTS` only, run from the
  FastAPI lifespan. Idempotent: starting twice against an existing file is a no-op.
- Never `DROP`, never destructive `ALTER`, never delete the db file.
- On every connection: `PRAGMA foreign_keys = ON`, `PRAGMA journal_mode = WAL`.
- Connection per request, provided as a FastAPI dependency. Commit once at the end of a
  successful request, rollback on exception. Use cases never call `commit()`.
- Parameterised SQL only. No f-strings, no `%`, no `.format()` in a query — ever.
- SQL string literals appear only under `adapters/sqlite/`.

## 7. Frontend

- Served with `StaticFiles` from `app/adapters/http/static/`. No npm, no bundler, no build
  step, no CDN `<script>` tags. ES modules via `<script type="module">`.
- One module per screen: `profiles.js`, `profile.js`, `call_detail.js`, `register.js`.
- `api.js` is the only file containing `fetch(`. Screens call functions from it.
- No framework, no reactive layer, no state library. Read the DOM, write the DOM.

## 8. Tests

- Use cases are tested against fakes for all ports — no FastAPI, no disk, no network.
- Repositories are tested against an in-memory SQLite (`:memory:`) with the real schema.
- Route tests use `TestClient` with fake ports injected via dependency override.
- A test may not import from `adapters/responses/`.

## 9. Verification — run before reporting any task done

```bash
lint-imports              # all contracts pass
pytest -q                 # all green
grep -rn "fetch(" app/adapters/http/static --include=*.js | grep -v "static/api.js"
grep -rniE "select |insert |update |delete " app --include=*.py | grep -v "adapters/sqlite/"
```

The last two must return nothing. Do not report success on a task if any of the four fails,
and do not disable, skip, or `# noqa` your way past a failure.

## 10. Forbidden

- Adding a dependency not already in `pyproject.toml` without asking.
- An ORM, a migration tool, Alembic, SQLAlchemy.
- A second network call site.
- `Any` in a public signature in `domain/` or `application/`.
- Editing `.importlinter`, deleting a test, or loosening an assertion to get green.
- Silent `except Exception: pass`.
