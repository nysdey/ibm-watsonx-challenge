# Security model

BobBee is a loopback-only local demo, not an internet-facing authentication system.

## Current controls

- The launcher binds to `127.0.0.1` only.
- Requests with a non-loopback `Host` are rejected.
- Cross-origin write requests are rejected.
- Identity is stored in Flask's signed, HTTP-only, SameSite session cookie.
- The demo password is validated for presence and immediately discarded.
- Generated state stays under the ignored `instance/` directory by default.
- Optional AI clients receive only the account context required for the requested
  narrative and fail closed to deterministic local content.
- Repository writes use atomic replacement, preventing partial JSON state.

## Trust boundaries

The packaged `name_match.xlsx` and deterministic generator are demo inputs. The UI must
still treat every account/contact field as untrusted data: Jinja autoescaping, `tojson`,
and the browser `esc()` helper must remain in place.

## Hosted deployment requirements

Do not expose the current local demo directly to a network. A hosted deployment needs:

- enterprise authentication and authorization;
- a production secret supplied outside source control;
- CSRF protection appropriate to the chosen auth mechanism;
- TLS and secure-cookie enforcement;
- durable per-user storage with access controls;
- rate limits and audit logs;
- a durable worker queue for long-running jobs;
- formal data-retention rules for customer and contact data.
