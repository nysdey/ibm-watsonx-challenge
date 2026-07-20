# IBM BobBee

BobBee is a local sales-planning web application for an IBM territory seller. It
turns a deterministic demo account book into ranked cadences, a quarterly outreach
schedule, daily email and call queues, account intelligence, and dashboard analytics.

The application is web-first. It does not launch scraper programs, automate browsers,
or pass Excel workbooks between pipeline folders. All demo data is normalized into one
document and accessed through explicit application services.

## Run

```bash
npm start
```

The first run creates `.venv`, installs the dependencies, and starts BobBee at
`http://localhost:5488`. Sign in with any email and password; the password is discarded.

The normal product flow is:

1. Accounts → Import accounts
2. Accounts → Sort accounts into cadences
3. Use Dashboard, Schedule, Cadences, Email, Call, and Profile

## Development

```bash
npm run check
```

This runs the Python test suite and syntax-checks every browser module.

The main entry points are:

- [`bobbee/app.py`](bobbee/app.py) — canonical Flask application factory
- [`bobbee/api/`](bobbee/api/) — HTTP blueprints and request validation
- [`bobbee/services/`](bobbee/services/) — application commands and UI read models
- [`bobbee/domain/`](bobbee/domain/) — pure scoring and scheduling rules
- [`bobbee/infrastructure/`](bobbee/infrastructure/) — atomic repository and deterministic demo-data adapter
- [`bobbee/integrations/`](bobbee/integrations/) — optional watsonx.ai and Assistant clients
- [`bobbee/templates/`](bobbee/templates/) — Jinja page templates
- [`bobbee/static/`](bobbee/static/) — design system, page CSS, browser feature modules, and images
- [`tests/`](tests/) — domain, API-flow, security-boundary, and architecture tests

Generated state is written to `instance/state.json` and is intentionally ignored by Git.
Set `BOBBEE_DATA_PATH` to place it elsewhere or `BOBBEE_ACCOUNT_COUNT` to change the
default 1,911-account demo book.

## Optional watsonx configuration

The deterministic application works without external services. To enable live Granite
writing, copy `.env.example` to `.env` and configure the `WATSONX_*` values. The AI
integration is fail-soft: scoring, tiers, cadence membership, and dates remain
deterministic if watsonx is unavailable.

See [Architecture](docs/ARCHITECTURE.md), [Development](docs/DEVELOPMENT.md), and
[Security](docs/SECURITY.md) for the maintained technical reference.
