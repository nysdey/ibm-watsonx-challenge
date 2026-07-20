"""Resolve a signed-in seller's CovIDs from the Name Match workbook.

This replaces the ISC Scraper's old map/territory-picker step for choosing which
CovIDs to pull. Instead of the seller clicking states on a map, we look up their
identity from the email they signed in with and read every CovID assigned to
them directly out of "Name Match.xlsx".

Name Match.xlsx columns (row 1 is the header):
    Quota Account ID  -- the CovID, e.g. "T0018075"
    Quota Account Name
    Industry          -- FSS / PUB / C&D / IND
    BTSS Rep          -- the BTSS seller's full name
    TSS Rep           -- the TSS seller's full name

Each CovID row names two reps (a BTSS and a TSS) who SHARE that one CovID — that
is expected, not a duplicate. A given seller may be the BTSS rep on some rows and
the TSS rep on others; we return every CovID where they appear in EITHER column.

Identity is derived from the seller's IBM email. IBM emails usually carry the
first and last name (e.g. tim.zhou@ibm.com); if not, at least one of them. We
match the email against each distinct rep name and pick the best-scoring one,
then collect all of that rep's CovIDs.
"""
import os
import re
from pathlib import Path

DATA_ROOT = Path(__file__).resolve().parent.parent / "data"

# Overridable so the file can live elsewhere; defaults to the copy kept in-repo.
NAME_MATCH_XLSX = Path(
    os.environ.get("NAME_MATCH_XLSX", str(DATA_ROOT / "name_match.xlsx"))
).expanduser()

ID_COL, NAME_COL, INDUSTRY_COL, BTSS_COL, TSS_COL = (
    "Quota Account ID", "Quota Account Name", "Industry", "BTSS Rep", "TSS Rep",
)

_COVID_RE = re.compile(r"^T\d{4,}$", re.IGNORECASE)


def _alpha(s):
    """Lowercase, letters-only — used for forgiving substring name matching."""
    return re.sub(r"[^a-z]", "", str(s or "").lower())


def _email_local(email):
    """The part of an email before '@' (or the whole string if there's no '@')."""
    return str(email or "").split("@", 1)[0]


def _email_tokens(email):
    """Name-ish tokens from an email local part: split on separators/digits,
    lowercased, keeping only alphabetic pieces. 'tim.zhou' -> {'tim','zhou'}."""
    local = _email_local(email).lower()
    return {t for t in re.split(r"[^a-z]+", local) if t}


def _name_parts(name):
    toks = [t for t in re.split(r"\s+", str(name or "").strip()) if t]
    if not toks:
        return None, None, []
    return toks[0].lower(), toks[-1].lower(), [t.lower() for t in toks]


def _has_part(part, email_tokens, email_alpha):
    """Is a single name part present in the email? Exact token match always
    counts; a substring match counts only for parts >=3 chars (so a stray 2-char
    fragment can't accidentally match, but 'tim' still matches 'timothyzhouii')."""
    if not part:
        return False
    if part in email_tokens:
        return True
    return len(part) >= 3 and part in email_alpha


def _score_name(name, email_tokens, email_alpha):
    """How well a rep's full name matches the signed-in email.
        3 -> both first and last name present   (strong, unambiguous)
        2 -> last name present
        1 -> first name present
        0 -> no match
    'at least first OR last' still scores >0 so a partial email still resolves,
    while a full first+last email wins over any partial collision."""
    first, last, _ = _name_parts(name)
    has_first = _has_part(first, email_tokens, email_alpha)
    has_last = _has_part(last, email_tokens, email_alpha)
    if has_first and has_last:
        return 3
    if has_last:
        return 2
    if has_first:
        return 1
    return 0


def load_rows(path=None):
    """Read Name Match.xlsx into a list of {id, name, industry, btss, tss} dicts."""
    import openpyxl
    path = Path(path) if path else NAME_MATCH_XLSX
    if not path.exists():
        raise FileNotFoundError(f"Name Match workbook not found: {path}")
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    rows_iter = ws.iter_rows(values_only=True)
    header = [str(h).strip() if h is not None else h for h in next(rows_iter)]
    idx = {h: i for i, h in enumerate(header)}
    for req in (ID_COL, BTSS_COL, TSS_COL):
        if req not in idx:
            wb.close()
            raise ValueError(f"Name Match workbook missing '{req}' column (has: {header})")
    out = []
    for r in rows_iter:
        if not r:
            continue
        cov = str(r[idx[ID_COL]]).strip() if r[idx[ID_COL]] is not None else ""
        if not _COVID_RE.match(cov):
            continue
        out.append({
            "id": cov,
            "name": r[idx[NAME_COL]] if NAME_COL in idx else "",
            "industry": r[idx[INDUSTRY_COL]] if INDUSTRY_COL in idx else "",
            "btss": (str(r[idx[BTSS_COL]]).strip() if r[idx[BTSS_COL]] else ""),
            "tss": (str(r[idx[TSS_COL]]).strip() if r[idx[TSS_COL]] else ""),
        })
    wb.close()
    return out


def resolve_seller(email, path=None):
    """Map a signed-in email -> that seller's name -> all of their CovIDs.

    Returns a dict:
        {
          "email": <input>,
          "matched": bool,
          "seller_name": <best-matching rep name or None>,
          "match_score": 0..3,
          "covids": [order-preserving, de-duplicated CovIDs],
          "roles": {"btss": [covids where they're BTSS], "tss": [...]},
          "industries": {industry: count},
        }
    Never raises on a no-match — the caller decides how to surface "we couldn't
    find any territories for you".
    """
    rows = load_rows(path)
    email_tokens = _email_tokens(email)
    email_alpha = _alpha(_email_local(email))

    # Every distinct rep name across both columns, and how many CovIDs each owns
    # (used only to break ties between equally-scoring names).
    name_covid_count = {}
    for row in rows:
        for who in (row["btss"], row["tss"]):
            if who:
                name_covid_count.setdefault(who, set()).add(row["id"])

    best_name, best_score, best_count = None, 0, -1
    for name, covids in name_covid_count.items():
        score = _score_name(name, email_tokens, email_alpha)
        if score == 0:
            continue
        n = len(covids)
        if score > best_score or (score == best_score and n > best_count):
            best_name, best_score, best_count = name, score, n

    result = {
        "email": email, "matched": best_name is not None,
        "seller_name": best_name, "match_score": best_score,
        "covids": [], "roles": {"btss": [], "tss": []}, "industries": {},
    }
    if not best_name:
        return result

    seen = set()
    industries = {}
    for row in rows:
        is_btss = row["btss"] == best_name
        is_tss = row["tss"] == best_name
        if not (is_btss or is_tss):
            continue
        cov = row["id"]
        if is_btss:
            result["roles"]["btss"].append(cov)
        if is_tss:
            result["roles"]["tss"].append(cov)
        if cov not in seen:
            seen.add(cov)
            result["covids"].append(cov)
            ind = str(row["industry"] or "").strip() or "—"
            industries[ind] = industries.get(ind, 0) + 1
    result["industries"] = industries
    return result


if __name__ == "__main__":
    import json
    import sys
    email = sys.argv[1] if len(sys.argv) > 1 else "tim.zhou@ibm.com"
    print(json.dumps(resolve_seller(email), indent=2))
