# Architecture

## Design goals

BobBee is a local, single-user demo application. Its architecture is intentionally
smaller than a production multi-tenant sales platform while still following the same
separation of concerns:

- HTTP code validates requests and serializes responses.
- Application services coordinate use cases.
- Domain modules own deterministic business rules.
- Infrastructure modules own persistence and synthetic data generation.
- Optional integrations are isolated and fail soft.
- The browser consumes stable JSON read models and owns only interaction state.

## Runtime flow

```text
Browser
  │  GET/POST JSON
  ▼
bobbee/api
  │  calls
  ▼
bobbee/services
  ├── commands ──▶ bobbee/domain ──▶ JsonRepository
  └── queries  ──▶ JsonRepository ──▶ UI-specific read models
                         │
                         ▼
                  instance/state.json
```

`bobbee.create_app()` is the only application-construction path. It creates the
repository, job runner, command service, and query services, stores that explicit
container in `app.extensions`, and registers five blueprints.

## Package responsibilities

| Package | Responsibility | Must not contain |
|---|---|---|
| `api` | Routes, HTTP validation, status codes | scoring, filesystem writes, process launches |
| `services` | Import/strategize commands and browser read models | Flask globals in business logic |
| `domain` | Scoring, cadence assignment, scheduling, date rules | Flask, filesystem, network |
| `infrastructure` | Atomic JSON repository, deterministic demo source, territory reference reader | route handlers |
| `integrations` | watsonx.ai and Assistant clients | core scoring decisions |
| `templates` / `static` | Browser presentation and interaction | server persistence logic |

## State model

The repository persists one versioned aggregate:

```text
seller
accounts[]
  ├── identity, territory, company size
  ├── IBM relationship/spend/install footprint
  ├── buying signals
  └── tier, score, play, tags, cadence, rank
strategy
  ├── cadence membership
  ├── no-contact and leftover sets
  └── future-quarter sets
schedule
  └── date → email/call activities
```

`JsonRepository` uses an in-memory, mtime-aware cache for reads and an atomic
temporary-file replacement for writes. This is appropriate for a local single-process
demo. A future multi-user deployment can implement the same repository interface with
PostgreSQL without changing domain rules or route contracts.

## Background work

Import and strategize run through a bounded `ThreadPoolExecutor`. `JobManager` owns
their explicit state (`active`, `phase`, `message`, `error`, `counts`) and prevents
duplicate runs. Slow work never blocks a Flask request, and there are no ambient global
process dictionaries or subprocess log parsers.

## Front end

The UI remains a server-rendered single-page shell:

- `design-system.css` owns colors, type, spacing, control, and tab tokens.
- `dashboard.css` owns application layouts and feature components.
- Feature-oriented JavaScript files own shell, accounts, schedule, dashboard,
  assistant, contextual panels, and outreach workflows.
- The account table paginates in the browser, limiting each render to 75 rows
  instead of mounting the complete 1,911-account book into the DOM.
- Import and strategize poll their job status only while active; the idle app
  does not run a global background polling loop.
- Server values are serialized with Jinja `tojson`; external JavaScript contains no
  template syntax.

There is deliberately no Node build framework. The application has no bundling or
hydration requirement, so native browser modules keep the development and runtime
surface small.

## Removed architecture

The former scraper folders, seven-step subprocess registry, Excel file handoffs,
checkpoint folders, Playwright session management, Bobby bolt-on, embedded Python
templates, and dynamic route registry were deleted. Git history remains the recovery
mechanism; none of those systems participate in the current application.
