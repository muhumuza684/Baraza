# Baraza — group-project contribution & trust engine (working prototype)

A working MVP: FastAPI backend + Postgres/SQLite + React frontend, implementing
the design from the mockup — RBAC, task lifecycle, signed submissions, peer/instructor
verification, and a trust score built from two layers:

- **Markov layer** — tracks each student's submission history
  (on_time / late / missed / disputed) and drives how often their work gets audited.
- **Bayesian layer** — a Beta(alpha, beta) posterior over "this student delivers
  reliably," updated on every verified/disputed outcome. Gives a mean trust score
  *and* an honest confidence width, not a single opaque number.

This is a prototype for a portfolio/reasoning piece, not a production system —
see "What's simplified" below before pitching it as more than that.

## Requirements

- Python 3.10+
- Node.js 18+
- Windows: PowerShell (setup.ps1 provided). Mac/Linux: run the equivalent commands manually (see below).

## Quick start (Windows / PowerShell)

```powershell
cd baraza
.\setup.ps1
```

Then, in two separate terminals:

```powershell
# Terminal 1 — backend
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload

# Terminal 2 — frontend
cd frontend
npm run dev
```

Open **http://localhost:5173**.

Demo logins (created by `seed.py`):
- Student: `bright@must.ac.ug` / `password123`
- Lecturer: `lecturer@must.ac.ug` / `password123`

The lecturer view needs a project ID — `seed.py` prints one when it runs; you can
also fetch it from `GET /projects/{id}/tasks` or query the DB directly.

## Quick start (Mac/Linux)

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python seed.py
uvicorn app.main:app --reload
```

```bash
cd frontend
npm install
npm run dev
```

## API overview

| Endpoint | Method | Role | Purpose |
|---|---|---|---|
| `/auth/register` | POST | any | Create an account |
| `/auth/login` | POST | any | Get a JWT |
| `/projects` | POST | lecturer/admin | Create a project |
| `/projects/{id}/tasks` | POST | lecturer/admin | Define a task/role |
| `/projects/{id}/tasks/{task_id}/join` | POST | student | Claim an unassigned role |
| `/submissions` | POST | student | Submit signed work for a task |
| `/submissions/mine` | GET | student | View own submission history |
| `/verifications` | POST | student/lecturer/admin | Verify or dispute a submission |
| `/dashboard/me` | GET | student | Own trust score |
| `/dashboard/project/{id}` | GET | lecturer/admin | Contribution-balance view |

Interactive API docs: **http://localhost:8000/docs** (FastAPI's built-in Swagger UI)
once the backend is running.

## What's simplified (be upfront about this in your writeup)

- **Database defaults to SQLite** for zero-friction local setup. Swap `DATABASE_URL`
  in `backend/.env` to a Postgres URL for anything beyond a demo — the code is
  already Postgres-compatible via SQLAlchemy.
- **Signing is HMAC-based**, not public-key cryptography — proves authorship
  server-side, but isn't independently verifiable by a third party the way a real
  keypair signature would be. Good enough to demonstrate the primitive; a real
  deployment would move to per-student keypairs.
- **No device fingerprinting / hard device binding**, by design — see the
  `ip_fingerprint` field on `Submission`. It's stored as a soft anomaly signal only,
  never used to block a submission. Identity is proven by login credentials, not
  device.
- **No frontend auth guard on role-specific views yet** — the "instructor view"
  tab is visible to anyone logged in; the *backend* correctly rejects non-lecturer
  calls to lecturer-only endpoints, but the frontend doesn't hide the tab yet.
  Worth fixing before showing this to anyone outside your own testing.
- **Grades are never touched.** This system produces trust *signals* for a lecturer
  to use at their discretion — it does not compute or submit a grade. Keep it that
  way; see the earlier discussion on why.

## Project structure

```
baraza/
  backend/
    app/
      main.py          FastAPI app, CORS, router registration
      models.py         SQLAlchemy models (User, Project, Task, Submission, Verification, TrustRecord, AuditLog)
      schemas.py         Pydantic request/response schemas
      security.py        Password hashing, JWT, content hashing + signing
      trust_engine.py    Markov state tracking + Bayesian trust scoring
      deps.py             Auth + RBAC dependencies
      routers/            auth, projects, submissions, verifications, dashboard
    seed.py               Demo data (1 lecturer, 3 students, 1 project, 3 tasks)
    requirements.txt
  frontend/
    src/
      api.js              Fetch wrapper + auth token handling
      App.jsx              Tab shell (student / instructor view)
      pages/               Login, StudentDashboard, InstructorDashboard
  setup.ps1               One-command Windows setup
```
