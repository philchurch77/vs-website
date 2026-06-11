# CLAUDE.md — Cambridgeshire Virtual School Platform

## What this project is

This is the web platform for **Cambridgeshire Virtual School**, a service that supports children in care (looked-after children) by equipping the teachers and school staff who work with them.

The Virtual School runs training for teachers. This platform extends that training beyond the classroom — giving staff tools they can return to, resources they can reference, and AI-assisted guidance they can use in the moment.

The intended users are **teachers and school staff** — not children directly.

### Current apps

| App | Purpose |
|---|---|
| `posts` | Blog and news articles from the Virtual School |
| `resources` | Library of documents, links, and materials shared after training |
| `flashcards` | AI-powered toolkit to help teachers respond to trauma-affected pupils in the moment |
| `evaluation` | AI chatbot that guides staff through reflecting on their training |
| `tolerance` | Window of Tolerance mapping tool — weekly pupil behaviour observation grid |
| `sdq` | Strengths & Difficulties Questionnaire — a scored assessment tool |
| `training` | Training request submission form |
| `users` | User registration, login, logout |
| `core` | Shared infrastructure: the `ChatTurn` model (used by both AI chat tools, discriminated by a `tool` field), the agent streaming helper, session-id helper, and slug utility |

### Planned future apps

- **Literacy tools** — to support teachers working with pupils who have reading/writing difficulties as a result of trauma or disrupted schooling

---

## Tech stack

- **Python 3.13.3** / **Django 5.2** — language and web framework
- **SQLite** — database (local dev and Azure production)
- **OpenAI GPT-4.1** — LLM for the flashcards and evaluation agents, via `openai-agents` framework
- **django-allauth** — authentication including Microsoft OAuth (for staff SSO)
- **django-taggit** — tagging on posts and resources
- **WhiteNoise** — static file serving
- **Gunicorn** — WSGI server in production
- **Azure App Service** — hosting platform

---

## Running locally

```bash
python manage.py migrate
python manage.py runserver
```

Required environment variables (in `.env`):

```
OPENAI_API_KEY=...
SECRET_KEY=...             # required in production; auto-generated in dev
DEBUG=True                 # dev only
```

Optional:

```
ALLOWED_HOSTS_EXTRA=...
MICROSOFT_CLIENT_ID=...
MICROSOFT_CLIENT_SECRET=...
```

---

## Verifying work

### Tests

Each app has a `tests.py` file. They are currently empty stubs. Before adding new behaviour, write a test for it; before handing work back, confirm existing tests still pass:

```bash
python manage.py test
```

There is no linting or formatting tool configured yet. If one is added (e.g. `ruff`), document the command here and run it before finishing any task.

Until tests exist, the minimum bar for handing back a change is: the dev server starts, the affected page loads, and the core workflow completes without an error.

---

## Data protection

**This platform handles sensitive personal data about children in care. Read this section before touching any model, view, or feature that involves pupils.**

### What data this platform holds

- `Observation` (tolerance app) — pupil name, emotional/arousal state, observed behaviours, adult responses. This is **special category data** under UK GDPR Article 9 (data concerning health and wellbeing).
- `WeeklyMap` — pupil name, class/year group, key adults, support plan.
- `SDQResponse` — scored assessment data linked to a session (currently not persisted to DB, but treat any change to that carefully).
- `ChatTurn` (`core` app, shared by evaluation/flashcards via a `tool` field) — staff reflection and training notes; may contain indirect references to named pupils.

### Rules

- **Never log pupil names, states, or behaviours** to the console, error logs, or any external service. Logging is for system errors, not data content.
- **Never expose pupil data in URLs** (e.g. no `?pupil_name=` query strings). Use PKs and enforce ownership checks in views.
- **Filter by user/school at the queryset level**, not in templates. A user must never be able to retrieve another school's pupil data by guessing a URL or PK.
- **Data minimisation** — only collect what is needed for the specific tool. Don't add new pupil-identifying fields without a clear purpose.
- **AI tools** — do not send pupil names or identifying details to the OpenAI API. The flashcards and evaluation agents receive scenario descriptions and staff reflections only. Keep it that way.
- **Any new feature that records, infers, or displays information about a child's health, behaviour, or wellbeing** is likely to involve Article 9 special category data. **Flag this to the developer for a human DPIA check before it ships** — do not implement it speculatively.

### When to slow down

If a task involves any of the following, pause and flag it rather than proceeding silently:

- Adding a new field to `Observation`, `WeeklyMap`, or any model that links to a named pupil
- Storing AI outputs that reference individual pupils
- Changing who can access the tolerance or SDQ apps
- Sharing or exporting pupil data to a third-party service
- Adding analytics or tracking to pages that display pupil information

---

## Project structure

```
myproject/
  settings/         # Django settings (settings.py, wsgi.py, asgi.py, urls.py)
  users/            # Auth: register, login, logout
  posts/            # Blog posts with tags
  evaluation/       # AI chat — training reflection agent
  flashcards/       # AI chat — trauma-responsive toolkit agent
  training/         # Training request form
  sdq/              # SDQ assessment tool
  resources/        # Resource library
  tolerance/        # Window of Tolerance weekly observation grid
  templates/        # Base layout and shared partials
  static/           # CSS, JS, images
  media/            # User-uploaded files
```

---

## Adding a new app

1. Create the app: `python manage.py startapp <name>` inside `myproject/`
2. Add it to `INSTALLED_APPS` in `myproject/settings/settings.py`
3. Create a `urls.py` in the new app and include it in `myproject/urls.py` with a path prefix
4. Run `python manage.py makemigrations <name>` after defining models, then `migrate`
5. Register models in `admin.py` so they're accessible in the Django admin
6. Add templates in `templates/<name>/` following the existing app folder convention

Keep each app focused on one domain. If an app's `views.py` or `models.py` starts covering unrelated concerns, it's a signal to split.

---

## Key patterns

**Streaming AI responses** — both `evaluation` and `flashcards` stream via the shared `core/streaming.py` helper (`stream_agent_deltas`), which wraps `Runner.run_streamed()` for `StreamingHttpResponse`. Do not change these to synchronous responses.

**Dynamic agent instructions** — the flashcards agent builds its system prompt at runtime by injecting all `Flashcard` and `Scenario` content from the database. This is intentional.

**Session + DB chat history** — chat turns are stored in both Django sessions (for active use) and the `ChatTurn` model (for history retrieval).

**AJAX observation grid** — the tolerance app uses POST endpoints at `/api/observation/` and `/api/support-plan/` for interactive cell saving. No full page reloads.

**Slug auto-generation** — `Post`, `Topic` (resources), and `TrainingRequest` generate slugs via the shared `core/slugs.py` utility, which handles duplicates with a counter suffix.

**Azure detection** — `settings.py` checks for `WEBSITE_HOSTNAME` to switch to production paths (media at `/home/site/wwwroot/media`, SQLite at `/home/site/data/db.sqlite3`).

---

## Deployment

Production is on **Azure App Service**. `startup.sh` is called by Oryx and runs:

```bash
python manage.py migrate
python manage.py collectstatic --noinput
gunicorn myproject.wsgi:application --bind=0.0.0.0:8000
```

Do not remove or alter `startup.sh` without checking the Azure App Service configuration.

---

## Domain context

**Window of Tolerance** — a model from trauma-informed practice. Green = regulated. Red = hyperaroused (fight/flight). Blue = hypoaroused (shutdown). The tolerance app maps pupils against these states across the school day.

**Flashcards** — practical, quick-reference strategies for teachers. Scenarios describe real classroom situations. The AI agent matches the teacher's situation to relevant flashcards and provides guidance.

**Children in care** — the end beneficiaries of all tools. These are looked-after children, often with histories of trauma, abuse, or neglect. The platform exists to help the adults who support them do so more effectively.

---

## Agents and reviewers

This project has a team of specialist Claude agents in `.claude/agents/`:

| Agent | When to use |
|---|---|
| `ada` | **Before building** — design phase only. Review proposed model design, new app structure, or architectural decisions before any code is written. Ada designs what hasn't been built yet; Les simplifies what already exists. |
| `vera` | After completing a feature or fix — end-to-end QA from a real user's perspective before handing work back |
| `les` | When **existing code** is getting messy — oversized views, duplicated logic, hard-to-follow models. Les simplifies what's already written; Ada designs what hasn't been built yet. |
| `theo` | When starting something non-trivial — plan the approach, think through requirements, flag risks before writing code |
| `tess` | When `tests.py` is empty or a new view/model needs tests — writes Django TestCase tests focused on permissions, ownership, and cross-user data isolation |
| `stella` | When templates or CSS need review — visual hierarchy, spacing, usability, and teacher-friendly layout |
| `victor` | Before any change that touches permissions, authentication, data access, or sensitive fields — security and GDPR audit |
| `juno` | When you want a review of the agent/command setup itself — coverage gaps, overlaps, and workflow recommendations |

### Workflow commands

Three slash commands chain agents together for common end-to-end workflows:

| Command | When to use |
|---|---|
| `/build` | New feature from scratch — runs Theo (plan) → Ada if needed → implement → Les (tidy) → Vera (QA) |
| `/gauntlet` | **Mandatory** before shipping any change to `tolerance`, `sdq`, `flashcards`, or `evaluation` — runs Victor (GDPR audit) → Vera (QA) |
| `/wheels-up` | Pre-deploy check — runs Les (final tidy) → deployment checklist → commit message draft |
