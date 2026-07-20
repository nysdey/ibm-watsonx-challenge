"""Deterministic synthetic source data for the local BobBee demo.

Every random stream is seeded with a stable digest, so the same territory always
produces the same account identities, company facts, contacts, signals, and cadence
definitions. The module performs no network or filesystem I/O.
"""
import hashlib
import random
from datetime import date, datetime, timedelta

# ── Deterministic RNG ─────────────────────────────────────────────────────────
# Built-in hash() is randomized per process (PYTHONHASHSEED), which would make the
# "same CovIDs -> same accounts" contract silently break across restarts. md5 of a
# stable string is reproducible forever.


def _rng(*parts):
    key = "|".join(str(p) for p in parts)
    digest = hashlib.md5(key.encode("utf-8")).hexdigest()
    return random.Random(int(digest, 16))


# ── Word banks for procedural, believable company names ───────────────────────
_PREFIXES = [
    "Meridian", "Cascade", "Summit", "Pinnacle", "Vanguard", "Keystone", "Horizon",
    "Atlas", "Beacon", "Sterling", "Granite", "Vertex", "Cardinal", "Sentinel",
    "Apex", "Redwood", "Northwind", "Bluepeak", "Ironwood", "Copperline", "Silverline",
    "Evergreen", "Highland", "Riverstone", "Fairview", "Brightwater", "Clearfield",
    "Oakmont", "Westbridge", "Kingsford", "Lakeshore", "Stonegate", "Ridgeline",
    "Harborview", "Crestwood", "Monarch", "Liberty", "Frontier", "Pacific", "Atlantic",
    "Continental", "Premier", "Allied", "Sunrise", "Trilliant", "Amberton", "Foxglove",
    "Grandview", "Templeton", "Wexford",
]

# (industry, weight, [sub-industries], [industry nouns]). Industry strings match the
# Values align with the domain scorer's vertical vocabulary.
_INDUSTRIES = [
    ("Healthcare", 3, ["Hospital Systems", "Providers", "Payers"],
     ["Health", "Healthcare", "Medical", "Care", "Wellness"]),
    ("Banking", 3, ["Retail Banking", "Commercial Banking"],
     ["Bank", "Financial", "Bancorp", "Savings", "Trust"]),
    ("Insurance", 2, ["Property & Casualty", "Life", "Health Plans"],
     ["Insurance", "Mutual", "Assurance", "Casualty"]),
    ("Financial Markets", 2, ["Asset Management", "Capital Markets"],
     ["Capital", "Securities", "Asset Management", "Investments", "Advisors"]),
    ("Government, State/Provincial/Local", 2, ["State Agency", "Municipal"],
     ["County", "State", "Municipal", "Regional Authority", "Water District"]),
    ("Government, Central/Federal", 1, ["Federal Agency"],
     ["Federal Services", "National Bureau"]),
    ("Telecommunications", 2, ["Wireless", "Broadband"],
     ["Telecom", "Communications", "Networks", "Wireless", "Broadband"]),
    ("Life Sciences", 2, ["Pharmaceuticals", "Biotech"],
     ["Biosciences", "Pharma", "Therapeutics", "Labs", "Biotech"]),
    ("Retail", 2, ["Specialty Retail", "Grocery"],
     ["Retail", "Markets", "Stores", "Brands"]),
    ("Manufacturing", 3, ["Industrial", "Discrete"],
     ["Manufacturing", "Industries", "Fabrication", "Works"]),
    ("Energy & Utilities", 2, ["Utilities", "Oil & Gas"],
     ["Energy", "Power", "Utilities", "Resources"]),
    ("Transportation", 1, ["Logistics", "Airlines"],
     ["Logistics", "Freight", "Transport", "Cargo"]),
    ("Consumer Products", 1, ["CPG"],
     ["Consumer", "Products", "Goods"]),
    ("Media & Entertainment", 1, ["Broadcast", "Publishing"],
     ["Media", "Broadcasting", "Entertainment", "Publishing"]),
    ("Automotive", 1, ["OEM", "Parts"],
     ["Motors", "Automotive", "Mobility"]),
    ("Education", 1, ["Higher Education"],
     ["University", "College", "Academy"]),
]

_SUFFIXES = ["Holdings", "Group", "Corporation", "Inc.", "Systems", "Partners",
             "LLC", "Company", "Industries", "Enterprises", "Services", "", ""]

# A whitespace-heavy relationship mix keeps the tier distribution realistic.
_TECH_STATUS = [
    ("Existing (Continued)", 22), ("Existing", 14), ("Existing (PY New Client)", 8),
    ("New (Active)", 12), ("New (Pending)", 10), ("New (Whitespace)", 24),
    ("New (Dormant)", 10),
]

# Tim's actual coverage: CA / HI / GU / MP (California, Hawaii, Guam, Northern
# Mariana Islands). Weighted — California is the overwhelming bulk of a Select
# Territory book, with the Pacific islands a long tail — so the territory map
# shows a realistic distribution instead of an even four-way split.
_STATES = ["CA"] * 12 + ["HI"] * 4 + ["GU"] * 2 + ["MP"]
# Real-ish population centres inside those four territories.
_CITIES_BY_STATE = {
    "CA": ["San Jose", "Sacramento", "Fresno", "Irvine", "Oakland", "San Diego",
           "Long Beach", "Pasadena", "Riverside", "Santa Clara", "Anaheim", "Berkeley"],
    "HI": ["Honolulu", "Pearl City", "Hilo", "Kailua", "Kapolei"],
    "GU": ["Hagåtña", "Dededo", "Tamuning"],
    "MP": ["Saipan", "Garapan"],
}


def state_for_account(name):
    """The account's territory (CA/HI/GU/MP), derived from its name alone.

    Kept on a dedicated RNG stream (not the shared per-account one) so callers
    can recover it from just the account name.
    """
    return _rng("state", name).choice(_STATES)


def city_for_account(name):
    """The account's city, consistent with its territory. Name-derived, same
    reasoning as state_for_account."""
    st = state_for_account(name)
    return _rng("city", name).choice(_CITIES_BY_STATE[st])


def location_for_account(name):
    """'City, ST' for display in the accounts table."""
    return f"{city_for_account(name)}, {state_for_account(name)}"


def _weighted_choice(rng, pairs):
    total = sum(w for _, w in pairs)
    x = rng.uniform(0, total)
    upto = 0
    for item, w in pairs:
        upto += w
        if x <= upto:
            return item
    return pairs[-1][0]


def _hierarchy_code(name):
    """IBM client/buying-group hierarchy code: 2 letters + 6 base36 chars, matching
    the application's ``^[A-Z]{2}[0-9A-Z]{6}$`` format. Stable per account name.
    """
    r = _rng("code", name)
    alphabet = "0123456789ABCDEFGHIJKLMNPQRSTUVWXYZ"
    return r.choice(["GC", "DC", "GB", "DB"]) + "".join(r.choice(alphabet) for _ in range(6))


def _customer_number(name):
    """IBM customer / CMR number (numeric, >=5 digits). Stable per account name."""
    return str(_rng("cust", name).randint(100000, 9999999))


def _employees(r):
    return int(10 ** r.uniform(1.8, 5.3))


def _revenue(r, employees):
    if employees:
        return float(round(employees * r.uniform(90_000, 460_000), -3))
    return float(round(10 ** r.uniform(6.6, 10.4), -3))


def _domain(name):
    core = "".join(ch for ch in name.lower() if ch.isalnum())[:18]
    return f"{core}.com" if core else ""


def _make_account(name, industry, sub_industry):
    """Full, stable account identity derived from the name and industry."""
    r = _rng("account", name)
    status = _weighted_choice(r, _TECH_STATUS)
    is_existing = status.startswith("Existing")
    employees = None if r.random() < 0.16 else _employees(r)
    location_rev = None if r.random() < 0.16 else _revenue(r, employees or _employees(_rng("emp2", name)))
    base_rev = location_rev or _revenue(r, employees or 500)
    global_rev = float(round(base_rev * r.uniform(1.0, 2.6), -3))
    total_it = float(round(base_rev * r.uniform(0.02, 0.09), -3))
    cloud_spend = float(round(total_it * r.uniform(0.1, 0.5), -3))

    # IBM spend: existing clients carry real spend with a trend; whitespace/dormant ~0.
    if status.startswith("New (Whitespace)") or status.startswith("New (Dormant)"):
        cur = 0.0
        prior = prior1 = prior2 = 0.0
    else:
        cur = float(round((0.0006 if is_existing else 0.0002) * base_rev * r.uniform(0.4, 2.4), -2))
        trend = r.choice([1.25, 1.1, 1.0, 0.85, 0.7])   # up / flat / down
        prior = float(round(cur / trend, -2)) if cur else 0.0
        prior1 = float(round(prior * r.uniform(0.75, 1.15), -2))
        prior2 = float(round(prior1 * r.uniform(0.75, 1.15), -2))

    st = state_for_account(name)
    return {
        "name": name,
        "account_name": name,
        "account_number": _hierarchy_code(name),
        "customer_number": _customer_number(name),
        "industry": industry,
        "sub_industry": sub_industry,
        "country": "United States",
        "state": st,
        "city": city_for_account(name),
        "headquarters": r.choice(["Yes", "Yes", "No", "Unknown"]),
        "headquarters_country": "United States",
        "employees": employees,
        "location_revenue": location_rev,
        "global_revenue": global_rev,
        "total_it_spend": total_it,
        "cloud_spend": cloud_spend,
        "contact_count": r.randint(1, 42),
        "tech_client_status": status,
        "ibm_spend_current": cur,
        "ibm_spend_prior": prior,
        "ibm_spend_prior1": prior1,
        "ibm_spend_prior2": prior2,
        "linkedin": f"https://www.linkedin.com/company/{_domain(name).split('.')[0]}" if name else "",
        "distinct_locations": r.randint(1, 7),
        "coverage_ids": [],   # filled by accounts_for_covids
    }


def _gen_name(rng):
    """Pick a company (name, industry, sub_industry) using the covid-seeded rng."""
    industry, _w, subs, nouns = _weighted_choice(
        rng, [((ind, w, subs, nouns), w) for ind, w, subs, nouns in _INDUSTRIES])
    prefix = rng.choice(_PREFIXES)
    noun = rng.choice(nouns)
    suffix = rng.choice(_SUFFIXES)
    name = " ".join(p for p in (prefix, noun, suffix) if p).strip()
    return name, industry, rng.choice(subs)


# ── The account pool ──────────────────────────────────────────────────────────

def demo_covids_for_email(email):
    """A stable demo territory (set of CovIDs) for any signed-in email, so the demo
    never dead-ends when the email isn't a real rep in Name Match.xlsx. Deterministic
    per email — the same person always gets the same territory."""
    r = _rng("demo_covids", (email or "demo").strip().lower())
    covids = set()
    while len(covids) < r.randint(11, 17):
        covids.add(f"T{r.randint(10000, 99999):05d}")
    return sorted(covids)


# A Select Territory seller carries a book in the low thousands, not a couple
# hundred — the earlier per-CovID range produced ~217, which made every list and
# chart in the app read like a toy. Sized to a realistic book instead.
TERRITORY_ACCOUNT_TARGET = 1911


def accounts_for_covids(covids, target=None):
    """Deterministic list of account dicts for a set of CovIDs. A company that falls
    in more than one CovID's territory appears once, with every CovID accumulated in
    ``coverage_ids``.

    Generates exactly ``target`` unique accounts, dealt round-robin across the
    CovIDs so every territory carries a share. The name space is ~42k
    combinations, so collisions just retry; the attempt cap is a safety net
    against a shrunken word list silently looping forever.
    """
    target = TERRITORY_ACCOUNT_TARGET if target is None else target
    covids = list(dict.fromkeys(str(c).strip() for c in covids if str(c).strip()))
    if not covids:
        return []

    rngs = {c: _rng("covid", c) for c in covids}
    by_name, order = {}, []
    attempts, max_attempts = 0, target * 60
    while len(order) < target and attempts < max_attempts:
        for covid in covids:
            if len(order) >= target:
                break
            attempts += 1
            rng = rngs[covid]
            name, industry, sub = _gen_name(rng)
            if name in by_name:
                if covid not in by_name[name]["coverage_ids"]:
                    by_name[name]["coverage_ids"].append(covid)
                continue
            acct = _make_account(name, industry, sub)
            acct["coverage_ids"] = [covid]
            by_name[name] = acct
            order.append(name)
    return [by_name[n] for n in order]


# ── Company enrichment ───────────────────────────────────────────────────────

def zoominfo_enrichment(account_name):
    """Stand-in for a ZoomInfo company-profile lookup. Deterministic per name."""
    r = _rng("zi", account_name)
    x = r.random()
    if x < 0.07:
        return {"ZI_Match_Status": "Unmatched", "ZI_Match_Method": "name", "ZI_Domain": "",
                "ZI_Revenue_USD": None, "ZI_Employee_Count": None,
                "ZI_Lookup_Timestamp": datetime.now().isoformat()}
    if x < 0.14:
        return {"ZI_Match_Status": "Ambiguous", "ZI_Match_Method": "name", "ZI_Domain": "",
                "ZI_Revenue_USD": None, "ZI_Employee_Count": None,
                "ZI_Lookup_Timestamp": datetime.now().isoformat()}
    employees = _employees(r)
    return {
        "ZI_Match_Status": "Matched", "ZI_Match_Method": "name",
        "ZI_Domain": _domain(account_name),
        "ZI_Revenue_USD": _revenue(r, employees),
        "ZI_Employee_Count": employees,
        "ZI_Lookup_Timestamp": datetime.now().isoformat(),
    }


# ── Buying signals ───────────────────────────────────────────────────────────
_SIGNAL_TEMPLATES = [
    ("M&A", "{name} to acquire regional competitor in ${n}M deal"),
    ("Funding", "{name} secures ${n}M growth investment"),
    ("Leadership_Change", "{name} names new Chief Information Officer"),
    ("Expansion", "{name} opens new operations center, adding {n} roles"),
    ("Earnings_Financial", "{name} reports Q{q} revenue up {n}% year over year"),
    ("Partnership", "{name} announces strategic partnership on cloud modernization"),
    ("Product_Launch", "{name} unveils new digital customer platform"),
    ("Layoffs_Restructuring", "{name} restructuring to cut {n}00 jobs"),
    ("Security_Incident", "{name} discloses data security incident under review"),
    ("Regulatory_Compliance", "{name} reaches ${n}M regulatory settlement"),
    ("ESG_Commitment", "{name} commits to carbon-neutral operations by 2030"),
]


def signals_for(account_name):
    """0-3 recent buying signals per account, deterministic. Shape matches the real
    integration: {Type, Date, Summary, Source_URL}."""
    r = _rng("signals", account_name)
    k = _weighted_choice(r, [(0, 34), (1, 30), (2, 22), (3, 14)])
    if not k:
        return []
    picks = r.sample(_SIGNAL_TEMPLATES, k)
    core = account_name.split(" Holdings")[0].split(" Group")[0].strip()
    out = []
    for sig_type, tmpl in picks:
        d = date.today() - timedelta(days=r.randint(3, 175))
        summary = tmpl.format(name=core, n=r.randint(2, 850), q=r.randint(1, 4))
        slug = "".join(ch for ch in core.lower() if ch.isalnum())[:20]
        out.append({
            "Type": sig_type,
            "Date": d.isoformat(),
            "Summary": summary[:300],
            "Source_URL": f"https://news.example.com/{slug}/{d.isoformat()}",
        })
    out.sort(key=lambda s: s["Date"], reverse=True)
    return out


# ── Buyer contacts ───────────────────────────────────────────────────────────
_TITLES = [
    "VP of Infrastructure", "Director of IT", "Chief Information Officer",
    "Head of Cloud Platform", "VP Engineering", "Director of Data & Analytics",
    "Enterprise Architect", "IT Operations Manager", "Chief Technology Officer",
    "Director of Information Security", "VP Digital Transformation",
    "Senior Infrastructure Engineer",
]
_FIRST = ["James", "Maria", "David", "Priya", "Michael", "Sarah", "Chen", "Aisha",
          "Robert", "Emily", "Carlos", "Fatima", "Daniel", "Grace", "Omar", "Laura"]
_LAST = ["Anderson", "Patel", "Nguyen", "Okafor", "Rivera", "Kim", "Johnson", "Silva",
         "Cohen", "Murphy", "Zhang", "Ali", "Brooks", "Ferrari", "Novak", "Reed"]


def _fake_phone(r):
    """Generate a plausible US direct-dial number deterministically."""
    area = r.choice([212, 312, 415, 512, 617, 713, 206, 404, 303, 214])
    return f"+1 ({area}) {r.randint(200,999)}-{r.randint(1000,9999)}"


def contacts_for_accounts(account_names, per_account=(2, 5)):
    """Buyer-group contacts a ZoomInfo 'Infra Outbound' filter would surface. Returns
    dicts with a 'raw' text blob (name / title / company), mirroring the real step
    which captures row innerText, not parsed emails (those cost ZoomInfo credits).
    Also includes direct_phone and work_email for the call/email UI."""
    out = []
    for name in account_names:
        r = _rng("contacts", name)
        for _ in range(r.randint(*per_account)):
            fn, ln, title = r.choice(_FIRST), r.choice(_LAST), r.choice(_TITLES)
            out.append({
                "first_name": fn, "last_name": ln, "title": title, "company": name,
                "raw": f"{fn} {ln}  {title}  {name}",
                "direct_phone": _fake_phone(r),
                "work_email": f"{fn.lower()}.{ln.lower()}@{_domain(name)}",
            })
    return out


# ── Cadence definitions ──────────────────────────────────────────────────────
SALESLOFT_CADENCES = [
    "Targeted Outreach Cadence 3", "Targeted Outreach Cadence 4",
    "Enterprise Expansion Cadence", "Whitespace Nurture Cadence",
]
# Step layout per cadence: (day, type, name). Real Salesloft cadences interleave
# Realistic email / phone / other step layout.
_CADENCE_STEP_LAYOUT = [
    (1, "email", "Intro email"),
    (1, "phone", "Call — first attempt"),
    (3, "email", "Value follow-up"),
    (5, "phone", "Call — second attempt"),
    (5, "other", "LinkedIn touch"),
    (8, "email", "Case-study share"),
    (12, "email", "Break-up email"),
]


def salesloft_cadence_steps(cadence):
    """List of step dicts: {id, step_number, day, type, name}. Deterministic."""
    r = _rng("cadence", cadence)
    steps = []
    for i, (day, stype, sname) in enumerate(_CADENCE_STEP_LAYOUT, start=1):
        steps.append({"id": r.randint(100000, 999999) + i, "step_number": i,
                      "day": day, "type": stype, "name": sname})
    return steps
