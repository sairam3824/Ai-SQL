# AI SQL Copilot

AI SQL Copilot is a full-stack MVP for natural-language analytics over PostgreSQL, SQLite, and DuckDB. It lets a user connect a database, inspect schema, ask questions in plain English, review generated SQL, execute it with read-only guardrails, visualize results, and inspect plan/index guidance.

This repository is built as a practical, extensible MVP:

- single-user by default
- local-first developer workflow
- OpenRouter for LLM access
- FastAPI backend for DB tooling and orchestration
- Next.js frontend for the dashboard and workspace

## What the app does

- Create and save database connections from the UI
- Support PostgreSQL, SQLite, and DuckDB
- Introspect tables, columns, primary keys, foreign keys, indexes, and estimated row counts
- Generate schema-aware SQL from natural language
- Show SQL, explanation, assumptions, and warnings
- Execute validated read-only SQL
- Show result tables, chart suggestions, and raw JSON
- Explain query plans
- Suggest conservative candidate indexes
- Persist chat history per connection

## Tech stack

### Frontend

- Next.js 15 App Router
- TypeScript
- Tailwind CSS
- Radix UI primitives / shadcn-style components
- TanStack Query
- Monaco Editor
- Recharts

### Backend

- FastAPI
- SQLAlchemy
- Pydantic v2
- `sqlglot` for SQL validation/parsing
- Native adapters:
  - `psycopg` for PostgreSQL
  - `sqlite3` for SQLite
  - `duckdb` for DuckDB
- OpenRouter via `httpx`

## Repository layout

```text
.
├── apps
│   ├── api
│   │   ├── app
│   │   │   ├── api
│   │   │   ├── core
│   │   │   ├── db
│   │   │   ├── models
│   │   │   ├── prompts
│   │   │   ├── repositories
│   │   │   ├── schemas
│   │   │   ├── services
│   │   │   └── tests
│   │   ├── scripts
│   │   └── Dockerfile
│   └── web
│       ├── src
│       │   ├── app
│       │   ├── components
│       │   └── lib
│       └── Dockerfile
├── packages
│   └── shared
├── docker-compose.yml
├── Makefile
└── .env.example
```

## Prerequisites

- Node.js 20+ recommended
- npm
- Python 3.13 recommended
- Docker Desktop optional
- OpenRouter API key for natural-language SQL generation

Notes:

- The backend setup prefers `python3.13`, then `python3.11`, then falls back to `python3`.
- OpenRouter is required for the NL-to-SQL flow. The SQL editor and execution flow still work if you type SQL manually.

## Environment

Create a local env file:

```bash
cp .env.example .env
```

Minimum recommended config:

```env
OPENROUTER_API_KEY=your_openrouter_key
OPENROUTER_MODEL=openai/gpt-4.1-mini
```

Important variables:

| Variable | Purpose |
|---|---|
| `OPENROUTER_API_KEY` | Enables SQL generation via OpenRouter |
| `OPENROUTER_MODEL` | Primary text-to-SQL model |
| `APP_DATABASE_URL` | Metadata DB for saved connections, chat sessions, schema cache |
| `APP_ENCRYPTION_KEY` | Optional secret for connection-config encryption |
| `APP_STORAGE_DIR` | Upload and local database storage directory |
| `QUERY_TIMEOUT_SECONDS` | Query timeout limit |
| `QUERY_DEFAULT_LIMIT` | Default applied limit for exploratory queries |
| `QUERY_MAX_ROWS` | Hard cap on returned rows |
| `WEB_PORT` / `API_PORT` / `APP_DB_PORT` | Docker host port overrides |

Credential storage note:

- If `APP_ENCRYPTION_KEY` is set, it is used to derive the Fernet key for stored connection configs.
- If it is not set, the backend creates a unique local key file under the backend storage directory instead of using a shared hardcoded fallback.
- For real deployments, you should set `APP_ENCRYPTION_KEY` explicitly.

## Local development

### 1. Install frontend dependencies

```bash
make install-web
```

### 2. Install backend dependencies

```bash
make install-api
```

Useful check:

```bash
make print-api-venv
```

### 3. Seed demo databases

```bash
make seed-demo
```

This creates:

- `apps/api/data/demo/sales_demo.sqlite`
- `apps/api/data/demo/sales_demo.duckdb`

### 4. Run the backend

For normal development:

```bash
make dev-api
```

For a more stable non-reload run:

```bash
make start-api
```

Backend URLs:

- API: [http://localhost:8000](http://localhost:8000)
- Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### 5. Run the frontend

```bash
make dev-web
```

Frontend URL:

- App: [http://localhost:3000](http://localhost:3000)

## Demo flow

Once both servers are running:

1. Open the dashboard
2. Click `New Connection`
3. Choose one of:
   - `SQLite` and upload `apps/api/data/demo/sales_demo.sqlite`
   - `DuckDB` and upload `apps/api/data/demo/sales_demo.duckdb`
4. Open the workspace
5. Try one of these prompts:
   - `Show monthly revenue for the last 12 months`
   - `Who are the top 5 customers by total spend?`
   - `Which products had the biggest drop in sales month over month?`
   - `Explain why this query is slow`
   - `Suggest indexes for this query`

## Docker

### Default run

```bash
docker compose up --build
```

Services:

- frontend: `http://localhost:3000`
- backend API: `http://localhost:8000`
- app metadata PostgreSQL: `localhost:5433`

### If ports are already in use

Stop the old stack first:

```bash
docker compose down --remove-orphans
```

If your machine already has something on `3000`, `8000`, or `5433`, override ports:

```bash
WEB_PORT=3002 API_PORT=8001 APP_DB_PORT=5434 docker compose up --build
```

### Stop containers

```bash
docker compose down
```

Remove volumes too:

```bash
docker compose down -v
```

## Runtime behavior and safety model

### SQL execution

- Only read-only SQL is permitted in the main execution path
- Mutating statements like `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, and similar commands are rejected
- Multiple statements are rejected
- Query limits and caps are enforced server-side
- Explain and index analysis validate the SQL for safety without rewriting it first

### Prompt safety

- The app treats schema content as untrusted prompt context
- Prompts instruct the LLM not to obey schema/data names as instructions
- SQL generation is constrained to the discovered schema summary

### Credentials

- Connection configs are stored server-side only
- Passwords are redacted from frontend responses
- Stored configs are encrypted with Fernet-backed secret material

## Main API routes

### Health

- `GET /health`

### Connections

- `POST /connections/test`
- `POST /connections`
- `GET /connections`
- `GET /connections/{id}`
- `DELETE /connections/{id}`

### Schema

- `GET /connections/{id}/schema`
- `POST /connections/{id}/schema/refresh`

### Chat / SQL

- `POST /connections/{id}/generate-sql`
- `POST /connections/{id}/execute`
- `POST /connections/{id}/explain`
- `POST /connections/{id}/advise-indexes`

### History

- `GET /connections/{id}/sessions`
- `POST /connections/{id}/sessions`
- `GET /sessions/{id}`

## Testing and verification

Run backend tests:

```bash
make test-api
```

Frontend production build:

```bash
npm --workspace apps/web run build
```

The current project has already been verified with:

- backend pytest suite
- Next.js production build
- production web Docker image build

## Troubleshooting

### `duckdb` or `uvicorn` not found in `make` commands

Your backend venv is incomplete or stale. Recreate it:

```bash
make install-api
```

You can confirm which backend venv is being used:

```bash
make print-api-venv
```

### Docker says a port is already allocated

Something else on your machine is already publishing that host port.

Fix options:

```bash
docker compose down --remove-orphans
```

or:

```bash
WEB_PORT=3002 API_PORT=8001 APP_DB_PORT=5434 docker compose up --build
```

### SQL generation returns 503

`OPENROUTER_API_KEY` is not configured, or the backend cannot reach OpenRouter.

### Frontend loads but the API calls fail

Check:

- backend is running
- `NEXT_PUBLIC_API_BASE_URL` is correct for local dev
- Docker port overrides match the URL you are using

## Production notes

This repository is a strong MVP, not a complete enterprise deployment template.

Still recommended before real production:

- authentication and per-user/project isolation
- secret manager integration
- structured logging and request correlation
- monitoring and alerting
- DB migrations workflow
- reverse proxy / HTTPS / domain setup
- backup and retention policy for uploaded DB files and metadata

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

---
*Done with Google Antigravity*
