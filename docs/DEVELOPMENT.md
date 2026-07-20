# Development

## Setup and run

```bash
npm run setup
npm start
```

Environment options:

| Variable | Purpose | Default |
|---|---|---|
| `BOBBEE_PORT` | Local HTTP port | `5488` |
| `BOBBEE_DATA_PATH` | Aggregate JSON location | `instance/state.json` |
| `BOBBEE_ACCOUNT_COUNT` | Generated territory size | `1911` |
| `BOBBEE_DEMO_DATE` | Pin server date (`YYYY-MM-DD` or `monday`) | system date |
| `BOBBEE_SECRET_KEY` | Flask session signing key | local-demo value |
| `WATSONX_*` | Optional Granite connection | unset/offline |
| `WXA_*` | Optional Assistant connection | unset/offline |

## Quality checks

```bash
npm run check
```

The Python suite covers:

- independent application factories and dependency containers;
- template compilation and packaged assets;
- removal of legacy architecture;
- deterministic scoring and clean schedule references;
- complete sign-in → import → strategize API behavior;
- agreement between Accounts, Dashboard, Book, Schedule, and Cadences read models;
- account-detail batching and AI fallback;
- loopback and cross-origin write guards.

Browser modules are syntax-checked with `node --check`. Changes that affect UI behavior
must additionally be exercised in a real browser because an HTTP 200 does not prove
that client-side behavior rendered correctly.

## Adding a feature

1. Put pure rules in `bobbee/domain`.
2. Add mutation orchestration or a read model in `bobbee/services`.
3. Expose the smallest required HTTP contract in `bobbee/api`.
4. Add browser behavior to the closest feature module under `bobbee/static/js`.
5. Reuse design tokens from `design-system.css`; do not introduce an ad-hoc type scale.
6. Add domain/API tests and browser-verify the visible path.

Do not add a subprocess, workbook handoff, global state dictionary, or new persistence
format for an ordinary web feature.

## Production evolution

BobBee currently uses Flask's development server and a JSON repository because it is a
local demo. For a hosted multi-user product:

1. implement the repository interface with PostgreSQL;
2. replace the in-process job runner with a durable queue;
3. use enterprise identity instead of the demo session route;
4. deploy `wsgi:app` under a production WSGI server;
5. add tenant/user ownership to every aggregate.

The current boundaries make those replacements local rather than application-wide.
