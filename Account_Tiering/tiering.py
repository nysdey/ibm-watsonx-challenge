"""Step 4 synthesis — Account Tiering.

LOGIC DESIGN (LLM-designed, 2026-07-10). The prior model was a generic 5-factor
weighted score that barely touched the IBM install intel that Account
Segmentation works so hard to join on. This rewrite makes the tier a function of
the signals a phone seller actually acts on, all of which now arrive on the row
from Segmentation:

  1. Relationship & momentum  - Technology Client Status + whether IBM spend is
                                growing, flat, or declining year over year.
  2. Deal size                - revenue + employee count, percentile-ranked
                                (log scale) within this run's own pool.
  3. IBM install footprint    - how much IBM is already installed (Power /
                                Storage / Cloud / Non-Infra). Depth here is the
                                expand-and-protect surface + hardware-refresh
                                surface.
  4. Competitive displacement - how much COMPETITOR gear is installed. A big
                                competitor footprint (especially with little IBM)
                                is a takeout opportunity.
  5. Vertical fit             - IBM's core verticals (FSS, Healthcare, Gov) score
                                highest.
  6. Buying signals           - funding / M&A / expansion etc. from the web
                                signal scrape.
  7. Contactability           - do we already have contacts to dial.

Each factor is scored 0-100 and blended by WEIGHTS into Tier_Score; tiers are
then cut by percentile within the pool (top 20% -> Tier 1, next 35% -> Tier 2).
On top of the number, every account gets a PRIMARY PLAY (Expand & Protect /
Displace Competitor / Hardware Refresh / Land New Logo / Win-Back / Nurture) and
a one-line SALES ANGLE — the two things a seller reads before dialing. Those are
deterministic here and optionally rewritten by a live Claude pass in run.py (see
../llm_advisor.py); the tier NUMBER stays deterministic and reproducible.
"""
import math
import statistics

# --- Relationship base, by Technology Client Status ------------------------
RELATIONSHIP_BASE_SCORE = {
    "Existing (Continued)": 100,
    "Existing": 80,
    "Existing (PY New Client)": 80,
    "Existing (PY-1 New Client)": 78,
    "Existing (PY-2 New Client)": 75,
    "Existing (PY-3 New Client)": 72,
    "New (Active)": 55,
    "New (Pending)": 45,
    "New (Whitespace)": 30,
    "New (Dormant)": 15,
}

# --- Vertical fit ----------------------------------------------------------
CORE_VERTICALS = {
    "Healthcare", "Government, Central/Federal", "Government, State/Provincial/Local",
    "Banking", "Financial Markets", "Insurance",
}
ADJACENT_VERTICALS = {
    "Telecommunications", "Life Sciences", "Computer Services",
    "Retail", "Manufacturing", "Energy & Utilities",
}

# --- Buying signals (web scrape) ------------------------------------------
SIGNAL_POINTS = {
    "Funding": 30, "M&A": 30, "Expansion": 25, "Regulatory_Compliance": 20,
    "Security_Incident": 20, "Leadership_Change": 15, "Partnership": 15,
    "Product_Launch": 15, "ESG_Commitment": 10, "Earnings_Financial": 10,
    "Layoffs_Restructuring": -10,
}

# --- IBM install footprint: points per brand present ----------------------
# Power & Storage are hardware (refresh cycles, high ASP) so they weigh more
# than a Non-Infra software line item.
FOOTPRINT_POINTS = {"Power": 34, "Storage": 30, "Cloud": 22, "NonInfra": 14}

WEIGHTS = {
    "relationship": 0.22,
    "size": 0.20,
    "footprint": 0.15,
    "displacement": 0.13,
    "vertical": 0.12,
    "signal": 0.10,
    "contactability": 0.08,
}

_INSTALL_BRANDS = ("Cloud", "Power", "Storage", "NonInfra", "Competitive")


def _num(value):
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _rows_for(row, brand):
    """Install-row count for a brand from Segmentation's {Brand}_Rows column,
    tolerating the flag-only {Brand}_Present when the count is absent."""
    n = _num(row.get(f"{brand}_Rows"))
    if n is not None:
        return int(n)
    return 1 if str(row.get(f"{brand}_Present", "")).strip().lower() in ("yes", "true", "1") else 0


# --------------------------------------------------------------------------
# Per-factor scorers
# --------------------------------------------------------------------------

def compute_spend_trend(row):
    """('label', yoy_adjustment) — the seller-facing Spend_Trend string plus a
    relationship-score nudge. Compares IBM spend current vs prior year, falling
    back to PY-1 when prior year is blank."""
    cy = _num(row.get("IBM Spend Current Year"))
    py = _num(row.get("IBM Spend Prior Year"))
    baseline = py if py is not None else _num(row.get("IBM Spend Prior Year - 1"))
    if cy is None and baseline is None:
        return "Unknown", 0
    if baseline in (None, 0):
        return ("New" if cy and cy > 0 else "Unknown"), (8 if cy and cy > 0 else 0)
    if cy is None:
        return "Lapsed", -12
    if cy >= baseline * 1.10:
        return "Growing", 12
    if cy <= baseline * 0.90:
        return "Declining", -12
    return "Flat", 0


def score_relationship(row, trend_adj):
    status = row.get("Technology Client Status")
    base = RELATIONSHIP_BASE_SCORE.get(status, 25)  # unknown status treated cold, not crashing
    return max(0, min(100, base + trend_adj)), status


def score_vertical(row):
    industry = row.get("Industry")
    if industry in CORE_VERTICALS:
        return 100
    if industry in ADJACENT_VERTICALS:
        return 70
    return 45


def score_signal(signals):
    total = 0
    for sig in signals:
        total += SIGNAL_POINTS.get(sig.get("Type"), 0)
    return max(0, min(100, total))


def score_footprint(row):
    """IBM install depth = expand/protect surface. Presence of each IBM brand
    scores its FOOTPRINT_POINTS; a deep install (many rows) adds a small bonus."""
    raw = 0
    for brand in ("Cloud", "Power", "Storage", "NonInfra"):
        if _rows_for(row, brand) > 0:
            raw += FOOTPRINT_POINTS[brand]
    depth = _rows_for(row, "Power") + _rows_for(row, "Storage") + _rows_for(row, "NonInfra")
    if depth >= 10:
        raw += 10
    elif depth >= 3:
        raw += 5
    return max(0, min(100, raw))


def _log_scale(value, ceiling):
    """0-100 log-scaled score for a count that spans orders of magnitude."""
    if not value or value <= 0:
        return 0.0
    return min(100.0, 100.0 * math.log10(value + 1) / math.log10(ceiling + 1))


def score_displacement(row):
    """Competitor footprint = takeout opportunity. Log-scaled on the competitive
    install-row count, boosted when IBM's own footprint is thin (pure-competitor
    accounts are the cleanest greenfield takeouts)."""
    comp = _rows_for(row, "Competitive")
    if comp <= 0:
        return 0.0
    base = _log_scale(comp, 500)
    ibm_depth = sum(_rows_for(row, b) for b in ("Cloud", "Power", "Storage", "NonInfra"))
    if ibm_depth == 0:
        base = min(100.0, base * 1.25)   # competitor-only: clean displacement play
    return base


def _percentile_scores(values):
    """Log-scale then percentile-rank (0-100) within the present values. None is
    excluded and median-filled by the caller — blank must not read as zero."""
    present = sorted(v for v in values if v is not None)
    if not present:
        return {}
    logged = [math.log10(v + 1) for v in present]
    lo, hi = min(logged), max(logged)
    span = hi - lo
    ranks = {}
    for original, log_v in zip(present, logged):
        ranks[original] = 100.0 if span == 0 else (log_v - lo) / span * 100.0
    return ranks


# --------------------------------------------------------------------------
# Seller-facing narrative
# --------------------------------------------------------------------------

def install_summary(row):
    parts = []
    for brand in ("Power", "Storage", "Cloud", "NonInfra"):
        n = _rows_for(row, brand)
        if n > 0:
            label = "Non-Infra" if brand == "NonInfra" else brand
            parts.append(f"{label}×{n}")
    return " · ".join(parts) if parts else "No IBM installs"


def competitive_summary(row):
    comp = _rows_for(row, "Competitive")
    return f"Yes ({comp} competitor products)" if comp > 0 else "No"


def classify_play(row, trend):
    """Rule-based Primary Play from the dominant driver. Order matters — the
    first matching rule wins, most actionable first."""
    status = row.get("Technology Client Status") or ""
    comp = _rows_for(row, "Competitive")
    ibm_depth = sum(_rows_for(row, b) for b in ("Cloud", "Power", "Storage", "NonInfra"))
    hw = _rows_for(row, "Power") + _rows_for(row, "Storage")

    if status.startswith("New (Whitespace)") or (status.startswith("New") and ibm_depth == 0):
        return "Land New Logo"
    if trend in ("Declining", "Lapsed"):
        return "Win-Back"
    if comp >= 20 and comp > ibm_depth:
        return "Displace Competitor"
    if hw > 0:
        return "Hardware Refresh"
    if ibm_depth > 0 or trend in ("Growing", "New"):
        return "Expand & Protect"
    return "Nurture"


def build_sales_angle(row, play, trend):
    """Deterministic one-liner reason-to-call. Overwritten by the live Claude
    pass when available (see run.py), but always present so the column is never
    blank."""
    name_bits = []
    comp = _rows_for(row, "Competitive")
    ibm_depth = sum(_rows_for(row, b) for b in ("Cloud", "Power", "Storage", "NonInfra"))
    inst = install_summary(row)
    industry = row.get("Industry") or "this account"
    core = " core" if row.get("Industry") in CORE_VERTICALS else ""

    if play == "Displace Competitor":
        if ibm_depth == 0:
            name_bits.append(f"{comp} competitor products and no IBM footprint — clean takeout in {industry}")
        else:
            name_bits.append(f"{comp} competitor products dwarf the IBM base ({inst}) — displace the incumbent in {industry}")
    elif play == "Hardware Refresh":
        name_bits.append(f"Active IBM hardware ({inst}) — lead with a refresh / support-renewal conversation")
    elif play == "Expand & Protect":
        t = "spend growing YoY" if trend == "Growing" else "established IBM footprint"
        name_bits.append(f"{t} ({inst}) — protect the base and cross-sell adjacent brands")
    elif play == "Land New Logo":
        name_bits.append(f"Whitespace in a{core} {industry} account — no IBM yet, land the first workload")
    elif play == "Win-Back":
        name_bits.append(f"IBM spend is {trend.lower()} — re-engage before the account goes fully cold")
    else:
        name_bits.append(f"{industry} account — qualify fit and warm for a later play")

    signals = row.get("_signal_types_found") or []
    if signals:
        name_bits.append(f"recent signal: {', '.join(signals[:2])}")
    return "; ".join(name_bits)


def llm_intel(rows):
    """Compact per-account intel for the optional live-Claude pass. Only the
    signals that inform a call — never the 600 raw install-detail columns."""
    out = []
    for r in rows:
        out.append({
            "account": r.get("Account Name"),
            "tier": r.get("Tier"),
            "industry": r.get("Industry"),
            "relationship": r.get("Technology Client Status"),
            "spend_trend": r.get("Spend_Trend"),
            "ibm_spend_current": r.get("IBM Spend Current Year"),
            "ibm_install": r.get("Install_Summary"),
            "competitor_footprint": r.get("Competitive_Displacement"),
            "revenue": r.get("ZI_Revenue_USD") or r.get("Location Annual Revenue"),
            "employees": r.get("ZI_Employee_Count") or r.get("Employee Count"),
            "contacts": r.get("Contact Count"),
            "signals": r.get("_signal_types_found") or [],
            "deterministic_play": r.get("Primary_Play"),
        })
    return out


def apply_llm_advice(rows, advice):
    """Overwrite Primary_Play / Sales_Angle with the live-Claude judgment where
    the model returned something for that account. No-op for accounts the model
    skipped, so a partial reply degrades gracefully."""
    if not advice:
        return 0
    applied = 0
    for r in rows:
        a = advice.get(r.get("Account Name"))
        if not a:
            continue
        if a.get("angle"):
            r["Sales_Angle"] = a["angle"]
            r["_angle_source"] = "claude"
        if a.get("play"):
            r["Primary_Play"] = a["play"]
        applied += 1
    for r in rows:
        r.pop("_angle_source", None)
    return applied


# --------------------------------------------------------------------------
# Main entry point
# --------------------------------------------------------------------------

def tier_accounts(rows, signals_by_account):
    """rows: list of dicts (Segmentation columns + ZI_* merged in).
    signals_by_account: {Account Name: [signal dicts]}.
    Mutates each row, adding Score_*, Tier_Score, Tier, Spend_Trend,
    Install_Summary, Competitive_Displacement, Primary_Play, Sales_Angle,
    Tier_Reasoning. Returns rows."""
    revenue_values = [_num(r.get("ZI_Revenue_USD")) or _num(r.get("Location Annual Revenue")) for r in rows]
    employee_values = [_num(r.get("ZI_Employee_Count")) or _num(r.get("Employee Count")) for r in rows]
    revenue_ranks = _percentile_scores(revenue_values)
    employee_ranks = _percentile_scores(employee_values)
    revenue_median = statistics.median(revenue_ranks.values()) if revenue_ranks else 50.0
    employee_median = statistics.median(employee_ranks.values()) if employee_ranks else 50.0

    for row, rev_raw, emp_raw in zip(rows, revenue_values, employee_values):
        signals = signals_by_account.get(row.get("Account Name"), [])
        row["_signal_types_found"] = [s["Type"] for s in signals]

        trend, trend_adj = compute_spend_trend(row)
        rel_score, status = score_relationship(row, trend_adj)
        vert_score = score_vertical(row)
        sig_score = score_signal(signals)
        footprint_score = score_footprint(row)
        displacement_score = score_displacement(row)

        rev_missing = rev_raw is None
        emp_missing = emp_raw is None
        rev_score = revenue_ranks.get(rev_raw, revenue_median)
        emp_score = employee_ranks.get(emp_raw, employee_median)
        size_score = 0.6 * rev_score + 0.4 * emp_score

        contacts = _num(row.get("Contact Count")) or 0
        contact_score = 20.0 if contacts <= 0 else _log_scale(contacts, 5000)

        tier_score = (
            WEIGHTS["relationship"] * rel_score
            + WEIGHTS["size"] * size_score
            + WEIGHTS["footprint"] * footprint_score
            + WEIGHTS["displacement"] * displacement_score
            + WEIGHTS["vertical"] * vert_score
            + WEIGHTS["signal"] * sig_score
            + WEIGHTS["contactability"] * contact_score
        )

        row["Score_Relationship"] = round(rel_score, 1)
        row["Score_Size"] = round(size_score, 1)
        row["Score_Footprint"] = round(footprint_score, 1)
        row["Score_Displacement"] = round(displacement_score, 1)
        row["Score_Vertical"] = round(vert_score, 1)
        row["Score_Signal"] = round(sig_score, 1)
        row["Score_Contactability"] = round(contact_score, 1)
        row["Tier_Score"] = round(tier_score, 1)

        row["Spend_Trend"] = trend
        row["Install_Summary"] = install_summary(row)
        row["Competitive_Displacement"] = competitive_summary(row)
        row["_relationship_status"] = status
        row["_revenue_missing"] = rev_missing
        row["_employees_missing"] = emp_missing

    # Percentile tier cutoffs within this pool.
    sorted_rows = sorted(rows, key=lambda r: r["Tier_Score"], reverse=True)
    n = len(sorted_rows)
    tier1_cut = math.ceil(n * 0.20)
    tier2_cut = tier1_cut + math.ceil(n * 0.35)
    for i, row in enumerate(sorted_rows):
        row["Tier"] = 1 if i < tier1_cut else (2 if i < tier2_cut else 3)
        play = classify_play(row, row["Spend_Trend"])
        row["Primary_Play"] = play
        row["Sales_Angle"] = build_sales_angle(row, play, row["Spend_Trend"])
        row["Tier_Reasoning"] = _build_reasoning(row)

    for row in rows:
        for k in ("_relationship_status", "_revenue_missing", "_employees_missing"):
            row.pop(k, None)
    return rows


def _build_reasoning(row):
    parts = [f"Tier {row['Tier']} (score {row['Tier_Score']})", f"play: {row['Primary_Play']}"]
    parts.append(f"relationship: {row['_relationship_status'] or 'unknown'} / spend {row['Spend_Trend'].lower()}")
    parts.append(f"vertical: {row.get('Industry') or 'unknown'} ({row['Score_Vertical']}/100)")
    parts.append(f"IBM install: {row['Install_Summary']}")
    if row["Competitive_Displacement"] != "No":
        parts.append(f"competitive: {row['Competitive_Displacement']}")
    sig = row.get("_signal_types_found") or []
    parts.append(f"{len(sig)} signal(s): {', '.join(sig)}" if sig else "no signals found")
    if row["_revenue_missing"]:
        parts.append("revenue median-filled")
    if row["_employees_missing"]:
        parts.append("employees median-filled")
    return "; ".join(parts)
