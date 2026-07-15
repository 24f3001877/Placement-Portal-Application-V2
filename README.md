# RecruitRadar — Placement Portal

> App Dev II College Project  
> Stack: Flask · Vue 3 (CDN) · Bootstrap 5 · SQLite · Redis · Celery · Mailpit

---

## Project Structure

```
RecruitRadar/              ← run everything from here
├── app.py                 ← Flask app (entry point)
├── init_db.py             ← Creates DB + seeds admin (run once)
├── requirements.txt
├── .env.example
│
├── backend/
│   ├── config.py          ← All configuration (RR_ prefixed)
│   ├── extensions.py      ← db, jwt, mail, cors, redis_client
│   ├── models.py          ← All SQLAlchemy models
│   ├── cache.py           ← Redis helpers (rr_cache: prefix)
│   ├── tasks.py           ← Celery tasks (rr_task prefix)
│   ├── celery_worker.py   ← Celery worker entry point
│   ├── uploads/           ← Resumes + generated files (rr_export_ prefix)
│   └── routes/
│       ├── auth.py        ← /api/auth/
│       ├── admin.py       ← /api/admin/
│       ├── company.py     ← /api/company/
│       └── student.py     ← /api/student/  (includes ATS checker)
│
└── frontend/
    ├── index.html         ← Jinja2 entry point (mounts #app only)
    └── src/
        ├── main.js, router.js, store.js, api.js
        ├── components/    ← NavBar.js, AlertMsg.js
        └── pages/         ← One .js file per page
```

---

## Setup (Two Commands — Same as Last Project)

### Step 1 — Create and activate virtual environment

```bash
cd RecruitRadar
python -m venv venv

# Windows (VSCode terminal):
venv\Scripts\activate

# Mac / Linux / WSL:
source venv/bin/activate
```

### Step 2 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 3 — Create database and seed admin

```bash
python init_db.py
```

Output:
```
RecruitRadar — Initialising database...
  ✓ All tables created successfully.
  ✓ Admin user created: admin@recruitradar.com
  ✓ Password          : Admin@1234
```

### Step 4 — Run the app

```bash
python app.py
# Open: http://localhost:5000
```

---

## For Full Features (Redis + Celery + Mailpit)

Open additional terminals, activate venv in each:

```bash
# WSL terminal — Redis
sudo service redis-server start

# Terminal 2 — Celery worker (handles CSV export jobs)
celery -A backend.celery_worker.celery worker --loglevel=info --pool=solo

# Terminal 3 — Celery Beat (handles scheduled email reminders)
celery -A backend.celery_worker.celery beat --loglevel=info

# Terminal 4 — Mailpit (catches all emails, view at http://localhost:8025)
mailpit
```

**Note:** The app works without Redis/Celery/Mailpit — caching is silently
disabled and background jobs won't fire, but all UI features work normally.

---

## Default Credentials

| Role  | Email                   | Password   |
|-------|-------------------------|------------|
| Admin | admin@recruitradar.com  | Admin@1234 |

Students and companies register via the frontend at `/login`.

---

## Milestones Checklist

| # | Milestone | Done |
|---|-----------|------|
| 1 | Database Models & Schema (7 models) | ✅ |
| 2 | Authentication & Role-Based Access (JWT) | ✅ |
| 3 | Admin Dashboard & Management | ✅ |
| 4 | Company Dashboard & Drive/Application Management | ✅ |
| 5 | Student Dashboard & Job Application System | ✅ |
| 6 | Application History & Status Tracking | ✅ |
| 7 | Backend Jobs — Reminders, Reports, CSV Export | ✅ |
| 8 | API Caching with Redis (rr_cache prefix) | ✅ |
| Optional | Public Landing Page with stats | ✅ |
| Optional | Offer Letter PDF Generator | ✅ |
| Optional | ATS Resume Checker (keyword matching) | ✅ |

---

## Key Design Decisions (for viva)

| Decision | Reason |
|----------|--------|
| Vue 3 via CDN, no CLI | Spec says CLI "not necessary"; no build step, easier to demo |
| `sys.path` in app.py | `app.py` at root, `backend/` as package — clean separation |
| `init_db.py` instead of `flask seed` | No env variable needed; identical to previous project pattern |
| `extensions.py` pattern | Prevents circular imports between app.py and models.py |
| Mailpit for email | Local testing, no Gmail credentials, works offline, great for viva demo |
| `rr_cache:` prefix on Redis keys | Namespaces all RecruitRadar cache entries |
| `rr_task` prefix on Celery tasks | All tasks identifiable in Celery worker logs |
| `rr_export_` prefix on files | All generated files (CSV, offer letters) are identifiable |
| Unique constraint (student_id, drive_id) | Duplicate application prevention enforced at DB level |
| Keyword matching for ATS | Transparent, explainable, no ML black box — every result is justifiable |
