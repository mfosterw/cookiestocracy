# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Democrasite is a Django web application that implements democratic voting on GitHub pull requests. Users vote on "bills" (proposals to merge PRs), and approved bills are automatically merged. Core functionality is protected by a "constitution" system that requires supermajority votes (66.67%) to modify protected files/line ranges, while normal bills need simple majority (>50%).

## Tech Stack

- **Python 3.13 / Django 5.x** with PostgreSQL, Redis, Celery
- **Docker Compose** for local development (all commands run inside containers)
- **Django REST Framework** with JWT auth and drf-spectacular for API docs
- **django-allauth** for GitHub/Google OAuth
- **Ruff** (linter/formatter), **mypy** (type checker), **djLint** (template linter), **pre-commit** hooks

## Common Commands

All development uses Docker. The `justfile` sets `COMPOSE_FILE=docker-compose.local.yml` automatically.

```bash
just build                    # Build Docker images
just up                       # Start all containers
just down                     # Stop containers
just test <args>              # Run pytest suite
just lint                     # Run pre-commit hooks
just typecheck                # Run mypy
just manage <args>            # Run manage.py (e.g., just manage makemigrations)
just migrate                  # makemigrations + migrate
just coverage                 # Run tests with coverage + open HTML report
just shell                    # Bash shell in django container
just pyshell                  # Django shell_plus (IPython)
just run <cmd>                # Execute arbitrary command in django container
just loaddata                 # Load fixtures (democrasite + social)
```

To run a single test:

```bash
just test democrasite/webiscite/tests/test_models.py::TestBill::test_method_name -v
```

For any `just` command, prefer running outside the sandbox to avoid `docker.sock`
permission errors. If `just` is not found, run `conda env democrasite` first.

Pytest is configured with `--ds=config.settings.test --reuse-db` in `pyproject.toml`.

## Architecture

### Django Apps

- **`democrasite/webiscite/`** — Core app. Models: `PullRequest`, `Bill`, `Vote`. Handles GitHub webhooks, voting logic, constitution enforcement, and Celery tasks for auto-merging.
- **`democrasite/users/`** — Custom `User` model (extends `AbstractUser` with single `name` field instead of first/last). OAuth integration.
- **`democrasite/social/`** — Social network for short notes. Models: `Person` (linked to User with keypair), `Follow`.

### Configuration

- **`config/settings/`** — Split settings: `base.py`, `local.py`, `production.py`, `test.py`
- **`config/urls.py`** — URL routing. Admin is only enabled in DEBUG mode.
- **`config/api_router.py`** — DRF router registering `UserViewSet` and `BillViewSet`
- **`config/celery_app.py`** — Celery configuration with Redis backend

### Key Patterns

- **Constitution system** (`webiscite/constitution.py`, `constitution.json`): Maps files to protected line ranges. PRs touching protected code become "constitutional" bills requiring supermajority. Line numbers auto-update after merges.
- **Bill lifecycle**: OPEN → APPROVED/REJECTED/FAILED/CLOSED. Each Bill has a OneToOne to a Celery `PeriodicTask` that runs `submit_bill()` at voting period end.
- **Webhook flow** (`webiscite/webhooks.py`): GitHub push events → HMAC validation → create/update `PullRequest` → create `Bill`.
- **Vote constraints**: One vote per user per bill (DB unique constraint). Votes can be changed.
- **Audit trail**: `django-simple-history` tracks changes on key models.

### API

- REST API at `/api/` with Swagger docs at `/api/docs/`
- Auth: session, token, JWT (`/api/token/refresh/`), GitHub OAuth (`/api/auth/github/`)

## Code Style

- **Ruff**: 88-char lines, force single-line imports, double quotes, spaces for indentation
- **djLint**: Django template profile, 119-char max line length, 2-space indent
- **mypy**: Strict-ish config with Django/DRF stubs, migrations ignored
- Env files live in `.envs/` (copied from `.envs.template/` on setup)
