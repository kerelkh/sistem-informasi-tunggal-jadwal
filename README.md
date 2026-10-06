# SITUNG — Sistem Informasi Tunggal Jadwal

Shared meeting schedule for a unit or ministry: everyone keeps their own meetings,
sees them on a month/week calendar in their own local time, checks whether colleagues are free, and invites them.

The interface, validation messages and notifications are in Indonesian. API field
values (`online`, `pending`, …) stay as English codes; the UI translates them.

- **Backend:** FastAPI + SQLModel + Alembic + PostgreSQL (`backend/`)
- **Frontend:** SvelteKit (adapter-node) + shadcn-svelte, preset `b1hE74GNqi` (`frontend/`)

Same stack and layout as kerel.dev; the meeting module is ported from there and made multi-user.

## Run it

```sh
cp .env.example .env        # then set real passwords/secrets
docker compose up --build
```

Open http://localhost:3100. On a fresh database you're sent to a one-time setup page that
creates the **first administrator**. After that there is no self-registration.

`POSTGRES_PASSWORD` and `JWT_SECRET_KEY` are required; compose won't start without them.
Both ports are bound to 127.0.0.1, so nothing is reachable from other machines.

### Deploying on Coolify

Create a **Docker Compose** resource from this repository, then:

1. Set the environment variables: `POSTGRES_PASSWORD`, `JWT_SECRET_KEY` (`openssl rand -hex 32`),
   `ORIGIN=https://<your domain>` and `ADDRESS_HEADER=X-Forwarded-For`.
2. Give the **frontend** service your domain on port 3000. The backend and database get no domain.
3. Deploy, open the domain straight away and create the first administrator. Until
   someone does, whoever opens the site first gets that account.
4. Turn on scheduled backups for the `db` service.

## Roles

| | Administrator | User |
|---|---|---|
| Create / edit / delete units | ✓ | |
| Create users, assign unit & role, deactivate, reset passwords | ✓ | |
| Own meetings, invite, check availability, answer invitations | ✓ | ✓ |

A regular user must belong to a unit; an administrator may or may not.

## How meetings work

- **Every meeting has an organizer** (whoever created it). The organizer is stored as a
  participant too — always "accepted" — so "my calendar" is simply every meeting I'm
  accepted into.
- **Inviting**: the organizer searches people (by name, email, position, or unit) and sees
  who is free for the meeting's scheduled time. Only people who are free can be invited —
  the backend enforces this too (HTTP 409 with the names of whoever is busy).
- **Invitees** get a notification and can **accept** (the meeting joins their calendar,
  marked "Invited", not "Organizer"), **decline**, or later **cancel** their attendance.
  Declining/cancelling can include a reason, which the organizer receives.
- **The organizer** can edit (invitees are notified if the title, time, or place changes),
  remove an invitee, re-invite someone who declined, **cancel** the meeting (kept, marked
  cancelled, everyone notified), or delete it.
- **Takehome pay** is tracked per person, not per meeting — each participant marks their own.

### What "busy" means

Same rules as the kerel.dev tracker, now applied across people:

- Only **formal** meetings the person has **accepted** (or organises) make them busy.
- Informal meetings and unanswered invitations are shown but don't block.
- A meeting with no end time is assumed to run to the end of its day.
- Intervals are half-open: a meeting ending at 12:00 doesn't clash with one starting at 12:00.
- Uses **scheduled** times, not actual execution times.

### Time: instants, shown on each viewer's clock

Times are stored and sent as **absolute instants in UTC** (the same thing a Unix
timestamp counts). Nobody's timezone is special: a meeting at `02:00Z` shows as
09.00 WIB in Jakarta, 10.00 WITA in Makassar and 11.00 WIT in Jayapura — each browser
converts to its own zone.

- The API sends `2026-10-01T02:00:00Z` and only accepts times that carry a zone
  (`…Z` or `…+07:00`). A bare `09:00` is refused: whose nine o'clock?
- Each meeting stores the organizer's zone (`timezone`, e.g. `Asia/Jakarta`). It
  decides where "the end of the day" is for a meeting with no end time, and the
  meeting page shows the organizer's local time when it differs from yours.
- Notifications carry the moment they're about (`event_at`) rather than a
  formatted time, so each reader sees it on their own clock.
- The dashboard renders in the browser (`ssr = false`), because only the browser
  knows the viewer's timezone.

## Local development without Docker

```sh
# Backend
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env                       # SQLite by default; or point DATABASE_URL at Postgres
.venv/bin/alembic upgrade head
.venv/bin/uvicorn app.main:app --reload --port 4100
.venv/bin/pip install pytest && .venv/bin/pytest    # tests

# Frontend (needs Node 24)
cd frontend
cp .env.example .env
npm install
npm run dev
```

## API sketch

All under `/api/v1`, bearer token from `POST /auth/login`.

| Endpoint | Who |
|---|---|
| `GET/POST /units`, `PUT/DELETE /units/{id}` | read: everyone · write: admin |
| `GET/POST /users`, `PUT /users/{id}`, `POST /users/{id}/reset-password` | admin |
| `GET /meetings` (mine), `POST /meetings` (with optional `invitee_ids`) | everyone |
| `GET/PUT/DELETE /meetings/{id}`, `POST /meetings/{id}/cancel` | participants read · organizer writes |
| `POST /meetings/{id}/participants`, `DELETE /meetings/{id}/participants/{user_id}` | organizer |
| `POST /meetings/{id}/respond` `{action: accept\|decline\|cancel, note?}` | invitee |
| `PUT /meetings/{id}/my-pay` | any accepted participant |
| `GET /availability?start&end&q&unit_id&user_ids&exclude_meeting_id` | everyone |
| `GET /notifications`, … | own only |
