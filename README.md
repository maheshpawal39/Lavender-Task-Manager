# Lavender · Task Manager

A small, calm task manager with a soft lavender interface. Built with React, Flask and SQLite.

![Theme](https://img.shields.io/badge/theme-lavender-B69AE8) ![Backend](https://img.shields.io/badge/backend-Flask-8B6CCF) ![Database](https://img.shields.io/badge/database-SQLite-DCCCF7)

## Features

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
│   │   ├── components/      # Header, stats, toolbar, task card, modals, icons
│   │   ├── hooks/           # Dialog behavior
│   │   ├── pages/           # Dashboard
│   │   ├── utils/           # Due-date formatting
│   │   ├── api.js           # API client
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── styles.css
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── backend/
│   ├── app.py               # Flask app factory and frontend serving
│   ├── database.py          # SQLite connection and schema
│   ├── models.py            # Task model and queries
│   ├── routes/
│   │   └── tasks.py         # REST API and validation
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

## API reference

| Method   | Endpoint             | Description                                        |
| -------- | -------------------- | -------------------------------------------------- |
| `GET`    | `/api/tasks`         | List tasks. Optional `status` and `search` params. |
| `GET`    | `/api/tasks/<id>`    | Get one task.                                      |
| `POST`   | `/api/tasks`         | Create a task.                                     |
| `PATCH`  | `/api/tasks/<id>`    | Update selected fields.                            |
| `PUT`    | `/api/tasks/<id>`    | Replace task details.                              |
| `DELETE` | `/api/tasks/<id>`    | Delete a task.                                     |
| `GET`    | `/api/stats`         | Total, pending and completed counts.               |
| `GET`    | `/api/health`        | Health check.                                      |

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
tasks (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  title       TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  due_date    TEXT,
  status      TEXT NOT NULL DEFAULT 'pending',
  created_at  TEXT NOT NULL,
  updated_at  TEXT NOT NULL
)
```

To reset all data, stop the server and delete `backend/instance/tasks.db`. It is
recreated on the next start.
