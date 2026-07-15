"""Single source of truth for every site the Seller Dashboard logs into, and how.

Every part of the dashboard — the Outbound pipeline steps, the login-capture tool,
and the embedded Meetings live-call assistant — reads its session locations and login
method from THIS registry, so there is exactly one place that describes "how do we get
into site X and where does its session live". Add a site here once and it's available
to the whole platform.

## The two credential concepts

1. **A saved password** (`credential_key`) — an email + password stored in the macOS
   Keychain (see `credential_store.py`). Every IBM-federated site shares the single
   `w3id` credential, because they all bounce to IBM W3ID SSO. Used only to *auto-fill*
   the SSO prompt during a capture.

2. **A captured session** (`auth_path`) — a Playwright `storage_state` JSON (cookies +
   localStorage) written once by a human logging in through a visible browser
   (`login_capture.py`), then re-injected into headless scrapes. This is what actually
   authorizes a scrape. `storage_state` is browser-engine-agnostic: a session captured
   with Firefox (login_capture) is reused by Chromium (the Meetings scrapers) without
   issue — it's just cookies.

## Fields per service

- `label`          — human name shown in the Details/Access panel.
- `base_url`       — where `login_capture.py` navigates to drive/verify the login.
- `valid_host`     — substring that must appear in the settled URL for the session to
                     count as live. An expired session instead bounces to a login host
                     (see `LOGIN_URL_MARKERS` in `login_capture.py`).
- `auth_path`      — where the captured `storage_state` JSON lives (absolute, `~`-based).
                     These paths are also read directly by the individual step programs
                     (ISC scraper, Account Tiering, the Meetings scrapers), so they are a
                     stable contract — do not rename casually.
- `credential_key` — logical Keychain credential used to auto-fill SSO (usually `w3id`).
- `engine`         — Playwright engine used to *capture* (`firefox`, matching
                     login_capture.py).
- `used_by`        — which dashboard surfaces consume this session.
- `method`         — one-line description of the login flow.
"""

# NOTE: auth_path values are the long-standing on-disk contract. `isc` lives under
# ~/.isc_scraper (the ISC scraper's own dir); everything else under ~/.orum_pipeline.
SERVICES = {
    "isc": {
        "label": "ISC",
        "base_url": "https://ibmsc.lightning.force.com/lightning/n/TerritoryProspecting",
        "valid_host": "ibmsc.lightning.force.com",
        "auth_path": "~/.isc_scraper/auth_state.json",
        "credential_key": "w3id",
        "engine": "firefox",
        "used_by": ["outbound"],
        "method": "IBM W3ID SSO + MFA into Salesforce Lightning (ISC). Captured via a "
                  "visible Firefox window; storage_state reused headlessly.",
    },
    "zoominfo": {
        "label": "ZoomInfo",
        "base_url": "https://app.zoominfo.com",
        "valid_host": "app.zoominfo.com",
        "auth_path": "~/.orum_pipeline/zoominfo_auth_state.json",
        "credential_key": "w3id",
        "engine": "firefox",
        "used_by": ["outbound"],
        "method": "ZoomInfo login → 'Single Sign-On (SSO)' → IBM W3ID SSO. Same "
                  "capture/reuse pattern as ISC.",
    },
    "salesloft": {
        "label": "Salesloft",
        "base_url": "https://app.salesloft.com/app",
        "valid_host": "app.salesloft.com",
        "auth_path": "~/.orum_pipeline/salesloft_auth_state.json",
        "credential_key": "w3id",
        "engine": "firefox",
        # Shared: the Outbound flow (ZoomInfo→Salesloft, Bobby) AND the Meetings
        # live-call assistant (reverse-email person lookup) both use this one session.
        "used_by": ["outbound", "meetings"],
        "method": "Salesloft → IBM W3ID SSO on email entry (no separate Salesloft "
                  "password). One captured session serves Outbound and Meetings.",
    },
    # CID = IBM Client Insights Dashboard (Storage install source for the IBM Scraper).
    "cid": {
        "label": "CID",
        "base_url": "https://cid.ibm.com",
        "valid_host": "cid.ibm.com",
        "auth_path": "~/.orum_pipeline/cid_auth_state.json",
        "credential_key": "w3id",
        "engine": "firefox",
        "used_by": ["outbound"],
        "method": "IBM W3ID SSO into cid.ibm.com (Client Insights Dashboard).",
    },
    # GTM Navigator (Cloud install source for the IBM Scraper).
    "gtmnav": {
        "label": "GTM Navigator",
        "base_url": "https://w3.ibm.com/sales/gtm-navigator/login/app",
        "valid_host": "w3.ibm.com",
        "auth_path": "~/.orum_pipeline/gtmnav_auth_state.json",
        "credential_key": "w3id",
        "engine": "firefox",
        "used_by": ["outbound"],
        "method": "IBM W3ID SSO into GTM Navigator (w3.ibm.com/sales/gtm-navigator).",
    },
    # Outlook Web calendar — the Meetings tab's calendar source. IBM's Microsoft 365
    # tenant federates to IBM W3ID SSO, so the same saved w3id password auto-fills it.
    # valid_host is "outlook." so it matches BOTH the classic host (outlook.office.com)
    # and new Outlook (outlook.cloud.microsoft); neither login host contains "outlook.".
    "outlook": {
        "label": "Outlook",
        "base_url": "https://outlook.office.com/calendar/view/week",
        "valid_host": "outlook.",
        "auth_path": "~/.orum_pipeline/outlook_auth_state.json",
        "credential_key": "w3id",
        "engine": "firefox",
        "used_by": ["meetings"],
        "method": "Microsoft 365 (IBM tenant) → federates to IBM W3ID SSO. Captured via "
                  "visible Firefox; storage_state reused headlessly by the Meetings "
                  "Outlook calendar scraper (Chromium).",
    },
}


def all_services():
    """Every registered service key, in registry order."""
    return list(SERVICES.keys())


def services_for(surface):
    """Service keys consumed by a given dashboard surface ('outbound' | 'meetings')."""
    return [k for k, v in SERVICES.items() if surface in v.get("used_by", [])]


def get(service):
    """The config dict for a service, or None."""
    return SERVICES.get(service)


def credential_key(service):
    """Logical Keychain credential used to auto-fill this service's SSO (e.g. 'w3id')."""
    return SERVICES.get(service, {}).get("credential_key", service)
