# Lavender · Task Manager

A small, calm task manager with a soft lavender interface. Built with React, Flask and SQLite.

![Theme](https://img.shields.io/badge/theme-lavender-B69AE8) ![Backend](https://img.shields.io/badge/backend-Flask-8B6CCF) ![Database](https://img.shields.io/badge/database-SQLite-DCCCF7)

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
- Persistent local storage in SQLite
- Responsive layout with a minimal lavender theme

## Tech stack

| Layer    | Technology          |
| -------- | ------------------- |
| Frontend | React, Vite, CSS    |
| Backend  | Python, Flask       |
| Database | SQLite              |

## Project structure

```
task-manager/
├── frontend/
│   ├── src/
│   │   ├── components/      # Header, auth shell, password input, modals, icons
│   │   ├── hooks/           # Dialog behavior
│   │   ├── pages/           # Login, Register, Dashboard
│   │   ├── utils/           # Due-date formatting
│   │   ├── api.js           # API client (auth + tasks)
│   │   ├── App.jsx          # Session check and page switching
│   │   ├── main.jsx
│   │   └── styles.css
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── backend/
│   ├── app.py               # Flask app factory and frontend serving
│   ├── database.py          # SQLite connection, schema and migrations
│   ├── models.py            # User and Task models
│   ├── routes/
│   │   ├── auth.py          # Register, login, logout, session
│   │   └── tasks.py         # Protected task REST API
│   └── requirements.txt
└── README.md
```

## Getting started

Requires **Python 3.10+** and **Node.js 18+**.

### 1. Backend

```bash
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
python app.py
```

The API runs at `http://127.0.0.1:5055`. The SQLite database is created
automatically at `backend/instance/tasks.db`.

> The port can be changed with the `PORT` environment variable, e.g. `PORT=8000 python app.py`.
> If you change it, update the proxy target in `frontend/vite.config.js` too.

> **This workspace:** a ready-to-use virtual environment already exists at the project
> root (`venv/`). From the project root you can simply run
> `venv\Scripts\python.exe backend\app.py` and open `http://127.0.0.1:5055`.

On first launch you will see the login page. Choose **Create an account** to register.
If tasks already existed before authentication was added, they are automatically
assigned to the first account you register, so no saved work is lost.

### 2. Frontend (development)

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Vite proxies `/api` requests to the Flask server.

### 3. Production build

```bash
cd frontend
npm run build
cd ../backend
python app.py
```

Flask serves the built React app at `http://127.0.0.1:5055`, so a single server
runs the whole application.

### Frontend connection troubleshooting

The frontend calls `/api` (a relative URL) on purpose:

- **Development:** Vite proxies `/api` to `http://127.0.0.1:5055` (see `vite.config.js`).
- **Production build:** Flask serves both the React app and the API, so `/api` is same-origin.

If you see "Can't reach the server":

1. Make sure the Flask backend is running on port `5055`.
2. Start the frontend with `npm run dev` instead of opening `index.html` directly.
   Opening the file (or using a static server without a proxy) has no `/api` route.
3. If you must serve the frontend separately, copy `.env.example` to `.env.local`,
   keep the absolute URL, and restart Vite:

   ```env
   VITE_API_BASE_URL=http://127.0.0.1:5055/api
   ```

## Authentication

- Passwords are hashed with Werkzeug's scrypt implementation; plaintext passwords
  are never stored or returned by the API.
- Login uses a signed, HTTP-only session cookie (`SameSite=Lax`). With
  **Remember me** enabled the session lasts 30 days; otherwise it ends when the
  browser closes.
- The dashboard and all `/api/tasks` and `/api/stats` endpoints require a valid
  session. Unauthenticated requests receive `401`.
- Every task query is scoped to the logged-in user. Reading, editing or deleting
  another user's task returns `404`.
- The first account registered inherits any tasks created before authentication
  existed, preserving old data.

The session signing key is read from the `SECRET_KEY` environment variable, or
generated once at `backend/instance/secret_key`. Keep it stable so sessions survive
server restarts.

Environment options:

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY` | Session signing key (optional; a local key file is used otherwise) |
| `SESSION_COOKIE_SECURE` | Set to `1` when serving over HTTPS |
| `CORS_ORIGINS` | Comma-separated frontend origins for cross-origin dev |
| `TASKMATE_DATABASE` | Alternate SQLite database path |

## API reference

### Authentication

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/api/auth/register` | Create an account and start a session. |
| `POST` | `/api/auth/login` | Sign in with email and password. |
| `POST` | `/api/auth/logout` | End the current session. |
| `GET` | `/api/auth/me` | Return the signed-in user. |

Registration accepts `full_name`, `email` and `password` (minimum 8 characters).
Login accepts `email`, `password` and an optional `remember_me` boolean.

### Tasks (session required)

| Method   | Endpoint             | Description                                        |
| -------- | -------------------- | -------------------------------------------------- |
| `GET`    | `/api/tasks`         | List tasks. Optional `status` and `search` params. |
| `GET`    | `/api/tasks/<id>`    | Get one task.                                      |
| `POST`   | `/api/tasks`         | Create a task.                                     |
| `PATCH`  | `/api/tasks/<id>`    | Update selected fields.                            |
| `PUT`    | `/api/tasks/<id>`    | Replace task details.                              |
| `DELETE` | `/api/tasks/<id>`    | Delete a task.                                     |
| `GET`    | `/api/stats`         | Total, pending and completed counts.               |
| `GET`    | `/api/health`        | Health check (public).                             |

### Task payload

```json
{
  "title": "Review project brief",
  "description": "Check the lavender palette.",
  "due_date": "2026-11-20",
  "status": "pending"
}
```

- `title` — required, 1–120 characters
- `description` — optional, up to 500 characters
- `due_date` — optional, `YYYY-MM-DD`
- `status` — `pending` or `completed` (defaults to `pending`)

Validation failures return `422` with an `error` message and per-field `fields`.
Missing tasks return `404`.

## Database

```sql
users (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  full_name     TEXT NOT NULL,
  email         TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  created_at    TEXT NOT NULL,
  updated_at    TEXT NOT NULL
)

tasks (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id     INTEGER REFERENCES users (id) ON DELETE CASCADE,
  title       TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  due_date    TEXT,
  status      TEXT NOT NULL DEFAULT 'pending',
  created_at  TEXT NOT NULL,
  updated_at  TEXT NOT NULL
)
```

Existing databases are migrated in place: the `users` table and `tasks.user_id`
column are added without recreating or deleting the tasks table. To reset all data,
stop the server and delete `backend/instance/tasks.db`. It is recreated on the next
start.

## Testing the login system locally

Start the backend (and optionally the Vite dev server) as described above, then open
the app:

```powershell
.\venv\Scripts\python.exe backend\app.py
# http://127.0.0.1:5055

# optional live-reload frontend, second terminal
cd frontend
npm run dev
# http://localhost:5173
```

Manual checklist:

1. Open the app — the login page should appear and the dashboard must not be visible.
2. Click **Create an account**, submit empty fields and verify validation messages.
3. Register with a password mismatch — it should be rejected.
4. Register successfully — the dashboard opens, and any pre-auth task is visible.
5. Add, edit, complete and delete a task; logout and log back in to confirm persistence.
6. Log in with a wrong password — you should see "Incorrect email or password."
7. Log in with **Remember me**, reload the page, and confirm the session stays active.
8. Register a second account — it must start with an empty task list.
9. Log out and try opening `/api/tasks` directly — it should return `401`.

Optional API check with a cookie jar:

```powershell
curl.exe -i -c cookies.txt -X POST http://127.0.0.1:5055/api/auth/register `
  -H "Content-Type: application/json" `
  -d '{"full_name":"Test User","email":"test@example.com","password":"lavender123"}'

curl.exe -b cookies.txt http://127.0.0.1:5055/api/tasks

curl.exe -b cookies.txt -X POST http://127.0.0.1:5055/api/auth/logout
```

This creates a real local account. Use a temporary database via
`$env:TASKMATE_DATABASE` if you do not want it in your main data file.
