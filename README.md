# Lavender · Task Manager

A small, calm task manager with a soft lavender interface. React frontend,
Flask API, and PostgreSQL database.

## Features

- User registration and secure login (scrypt password hashing)
- Protected dashboard, logout, and persistent sessions ("Remember me")
- Each account has its own private task list
- Add, edit and delete tasks
- Mark tasks as completed or move them back to pending
- Set and change due dates (with Today / Tomorrow / Overdue labels)
- Filter by **All**, **Pending** or **Completed**
- Search tasks by title or description
- Compact dashboard with total, pending and completed counts
- Input validation and clear API error messages
- PostgreSQL storage with SQLAlchemy ORM and connection pooling
- Alembic migrations for safe schema changes
- Responsive layout with a minimal lavender theme

## Tech stack

| Layer | Technology |
| --- | --- |
| Frontend | React, Vite, CSS |
| Backend | Python, Flask |
| ORM | SQLAlchemy / Flask-SQLAlchemy |
| Database | PostgreSQL (psycopg 3) |
| Migrations | Flask-Migrate / Alembic |
| Deployment | Vercel (Python serverless) + external frontend |

## Project structure

```
task-manager/
├── frontend/                 # React app (unchanged UI)
├── backend/
│   ├── app.py                # Flask factory, CORS, sessions, health
│   ├── database.py           # SQLAlchemy + PostgreSQL pool configuration
│   ├── models.py             # User and Task models
│   ├── routes/
│   │   ├── auth.py           # Register / login / logout / session
│   │   └── tasks.py          # Protected task API
│   ├── migrations/           # Alembic migration scripts
│   ├── scripts/
│   │   └── migrate_sqlite_to_postgres.py
│   ├── instance/             # Local secrets / legacy SQLite source (ignored)
│   ├── .env.example
│   └── requirements.txt
├── api/index.py              # Vercel serverless entrypoint
├── vercel.json
├── requirements.txt          # Vercel dependency entrypoint
└── README.md
```

## Environment variables

Create `backend/.env` from `backend/.env.example` for local development.
Never commit real credentials.

| Variable | Required | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | Yes | PostgreSQL URL, e.g. `postgresql://user:pass@host:5432/db?sslmode=require` |
| `SECRET_KEY` | Yes (production) | Flask session signing key |
| `FRONTEND_URL` | Yes (Vercel) | Frontend origin(s), comma-separated |
| `SESSION_COOKIE_SECURE` | Production: `true` | Send cookies only over HTTPS |
| `SESSION_COOKIE_SAMESITE` | Optional | `None` for cross-site frontend/backend, `Lax` locally |
| `DB_POOL_SIZE` | Optional | SQLAlchemy pool size (default `2`) |
| `DB_MAX_OVERFLOW` | Optional | Extra pooled connections (default `3`) |
| `DB_POOL_RECYCLE` | Optional | Recycle connections after seconds (default `280`) |
| `DB_POOL_TIMEOUT` | Optional | Pool checkout timeout (default `10`) |
| `DB_CONNECT_TIMEOUT` | Optional | PostgreSQL connect timeout (default `5`) |
| `DB_DISABLE_PREPARED_STATEMENTS` | Optional | `true` for transaction-mode poolers (PgBouncer) |

`postgres://` URLs are normalized to `postgresql+psycopg://`. SQLite URLs are
rejected; there is no SQLite runtime fallback.

## Local development

Requires **Python 3.10+**, **Node.js 18+**, and a **PostgreSQL server**.

### 1. Start PostgreSQL

Use a hosted database (Neon, Supabase, Vercel Postgres) or Docker:

```bash
docker run -d --name lavender-pg \
  -e POSTGRES_USER=lavender \
  -e POSTGRES_PASSWORD=choose-a-password \
  -e POSTGRES_DB=lavender \
  -p 5432:5432 postgres:16-alpine
```

### 2. Backend setup

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt

Copy-Item backend\.env.example backend\.env
# Edit backend\.env and set DATABASE_URL, SECRET_KEY, FRONTEND_URL

cd backend
$env:FLASK_APP = "app.py"
..\venv\Scripts\flask.exe db upgrade
..\venv\Scripts\python.exe app.py
```

The API runs at `http://127.0.0.1:5055`. The database schema is **not** created
automatically; `flask db upgrade` is required.

> This workspace already has a virtual environment at the project root
> (`venv/`). Activate it or call `venv\Scripts\python.exe` directly.

### 3. Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Vite proxies `/api` to Flask on port `5055`.

### 4. Production build (single local server)

```powershell
cd frontend
npm run build
cd ..\backend
..\venv\Scripts\python.exe app.py
```

Flask serves the built React app and API at `http://127.0.0.1:5055`.

## Migrating existing SQLite data

The old database is **not deleted**. After the PostgreSQL schema exists:

```powershell
$env:DATABASE_URL = "postgresql://..."
.\venv\Scripts\python.exe backend\scripts\migrate_sqlite_to_postgres.py
```

Options:

```powershell
# custom source path
... migrate_sqlite_to_postgres.py --source C:\path\to\tasks.db
```

The script opens SQLite read-only, preserves IDs, timestamps, due dates,
password hashes and user ownership, and is idempotent (existing rows are
skipped). PostgreSQL sequences are synchronized afterwards.

## Authentication

Authentication remains **session-based** (signed Flask cookie, HTTP-only). The
project did not use Flask-Login or an RBAC/roles table; that architecture was
left unchanged rather than replaced. Authorization is enforced per user for all
task queries.

- Passwords: Werkzeug scrypt hashes (compatible with existing hashes)
- Sessions: signed cookie, 30 days with **Remember me**
- `SESSION_COOKIE_SECURE=true` behind HTTPS
- `SESSION_COOKIE_SAMESITE=None` when frontend/backend are cross-site
- Protected endpoints return `401`; other users' tasks return `404`

## API reference

### Authentication

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/api/auth/register` | Create an account and start a session |
| `POST` | `/api/auth/login` | Sign in (`email`, `password`, optional `remember_me`) |
| `POST` | `/api/auth/logout` | End the current session |
| `GET` | `/api/auth/me` | Return the signed-in user |

### Tasks (session required)

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/tasks` | List own tasks (`status`, `search` params) |
| `GET` | `/api/tasks/<id>` | Get one own task |
| `POST` | `/api/tasks` | Create a task |
| `PATCH` | `/api/tasks/<id>` | Update selected fields |
| `PUT` | `/api/tasks/<id>` | Replace task details |
| `DELETE` | `/api/tasks/<id>` | Delete a task |
| `GET` | `/api/stats` | Total, pending and completed counts |
| `GET` | `/api/health` | API + database health check |

## Database schema

```sql
users (
  id            SERIAL PRIMARY KEY,
  full_name     VARCHAR(80) NOT NULL,
  email         VARCHAR(254) NOT NULL,
  password_hash TEXT NOT NULL,
  created_at    TIMESTAMPTZ NOT NULL,
  updated_at    TIMESTAMPTZ NOT NULL,
  CONSTRAINT uq_users_email UNIQUE (email)
)

tasks (
  id          SERIAL PRIMARY KEY,
  user_id     INTEGER NULL REFERENCES users(id) ON DELETE CASCADE,
  title       VARCHAR(120) NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  due_date    DATE NULL,
  status      VARCHAR(20) NOT NULL DEFAULT 'pending'
              CHECK (status IN ('pending', 'completed')),
  created_at  TIMESTAMPTZ NOT NULL,
  updated_at  TIMESTAMPTZ NOT NULL
)
```

Indexes: `ix_tasks_user_id`, `ix_tasks_status`, `ix_tasks_due_date`.

## Migrations

Versioned Alembic migrations live in `backend/migrations`.

```powershell
cd backend
$env:FLASK_APP = "app.py"
..\venv\Scripts\flask.exe db upgrade      # apply
..\venv\Scripts\flask.exe db current      # check revision
```

To create a new migration after a model change:

```powershell
..\venv\Scripts\flask.exe db migrate -m "describe change"
# review the generated file before applying
..\venv\Scripts\flask.exe db upgrade
```

Never use `db.create_all()` or automatic table recreation in production.

## Deploying the backend to Vercel

1. Create a PostgreSQL database and copy its connection string.
2. Apply migrations from your machine/CI using the **direct** database URL:

   ```powershell
   $env:DATABASE_URL = "postgresql://direct-connection..."
   $env:FLASK_APP = "app.py"
   cd backend
   ..\venv\Scripts\flask.exe db upgrade
   ```

3. Migrate legacy data once, if needed (run from the repository root):

   ```powershell
   .\venv\Scripts\python.exe backend\scripts\migrate_sqlite_to_postgres.py --source backend\instance\tasks.db
   ```

4. Import this repository into Vercel and set environment variables:

   ```
   DATABASE_URL=postgresql://...        (runtime/pooled URL; sslmode=require)
   SECRET_KEY=<long-random-value>
   FRONTEND_URL=https://your-frontend.vercel.app
   SESSION_COOKIE_SECURE=true
   SESSION_COOKIE_SAMESITE=None
   DB_DISABLE_PREPARED_STATEMENTS=true  (when using a PgBouncer pooler)
   ```

5. Deploy. `api/index.py` exposes the Flask app and `vercel.json` routes all
   requests to it. Dependencies are installed from the root `requirements.txt`.

6. Deploy the frontend separately and use its exact HTTPS origin in
   `FRONTEND_URL`. Set the frontend build-time API URL to the backend domain,
   for example in `frontend/.env.production`:

   ```env
   VITE_API_BASE_URL=https://your-backend.vercel.app/api
   ```

   CORS allows credentials for that frontend origin, and sessions use
   `SameSite=None; Secure` across domains.

7. Do not deploy `backend/instance/` (legacy DB/secrets); it is excluded by
   `.vercelignore`. Vercel builds are read-only, so schema changes must be run
   through migrations, not at function startup.

## Testing the login system locally

Start the backend and frontend, then:

1. Open the app — login page appears; dashboard is hidden.
2. Register; the dashboard opens.
3. Add, edit, complete and delete a task; reload to confirm persistence.
4. Log out; wrong password is rejected; correct login works.
5. Enable **Remember me** and reload — session persists.
6. Register a second account — it must have an empty task list and cannot access
   the first account's tasks.
7. Call `/api/tasks` without a session — expect `401`.
8. Check `/api/health` — expect `{"status":"ok","database":"ok"}`.

## Frontend connection troubleshooting

The frontend calls `/api` relatively:

- Development: Vite proxies `/api` to `http://127.0.0.1:5055`.
- Production: Flask serves the build locally; on Vercel the frontend calls the
  backend domain configured in the frontend deployment.

If the API is unreachable, confirm `DATABASE_URL` is valid, migrations have been
applied, and Flask is running on port `5055`.
