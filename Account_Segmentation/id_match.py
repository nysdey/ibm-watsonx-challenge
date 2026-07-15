"""Deterministic account-key join for Segmentation.

The whole point of this module: map each IBM install row onto the right DEDUPED
account with **certainty**, not a fuzzy name guess. IBM spells the same company
differently across its source systems (ISC vs the Power export vs GTM/Cloud vs
CID/Storage), so name similarity is unreliable at scale and unauditable by hand.
But every one of those systems keys the account by an *exact* IBM identifier:

  1. client / buying-group hierarchy code  (GC…/DC…/GB…/DB…)  -- exact code
  2. IBM customer / CMR number             (via the ISC crosswalk)
  3. the ISC/Salesforce account name       (same system as the base -> identical)

We resolve each install row to an account key by trying those in order. A hit on
any of them is a guaranteed-correct link (equality, not similarity). A row that
resolves to nothing is genuinely not one of the selected accounts (verified: such
rows don't name-match the base either -- they're out-of-territory install-base).

`name_match` (fuzzy) remains only as an explicit last-resort fallback for a file
that exposes no id key at all, and is flagged as such.
"""
import re

import name_match

# IBM hierarchy code: two letters then 6 alphanumerics (GC2TT1CS, DC46JLHF,
# DB500LNP). Sentinels that fit the shape but aren't real accounts are excluded.
_CODE_RE = re.compile(r"^[A-Z]{2}[0-9A-Z]{6}$")
_CODE_JUNK = {"UNASSIGN", "UNKNOWN", "UNASSIGNED", "NONE", "MISSING", "PENDING", "DEFAULT"}


def codes_in(value):
    """All IBM hierarchy codes found in a value. Splits on non-alphanumerics so a
    compound key like Cloud's 'GC2TT1CS-T0016156-897' yields just its GC code
    (the CovID 'T0016156' starts letter+digit, so it can't be mistaken for one)."""
    out = []
    for tok in re.split(r"[^0-9A-Za-z]+", str(value or "").upper()):
        if tok and tok not in _CODE_JUNK and _CODE_RE.match(tok):
            out.append(tok)
    return out


def norm_cust(value):
    """Canonical IBM customer/CMR number: numeric part before any country-code
    suffix, leading zeros dropped. '0139800'->'139800', '5788184-897'->'5788184'.
    Must match dedup.build_crosswalk's normalization exactly."""
    s = str(value if value is not None else "").strip().split("-")[0]
    s = re.sub(r"\D", "", s).lstrip("0")
    return s if len(s) >= 5 else ""


class AccountResolver:
    """Resolve an install row's identifiers to a DEDUPED account key."""

    def __init__(self, base_keys, cust_to_key, name_to_key):
        self.base_keys = base_keys              # set of Account Number codes
        self.cust_to_key = cust_to_key          # customer-number -> key
        self.name_to_key = name_to_key          # normalized account name -> key

    def resolve(self, codes, custs, names):
        """Return (account_key, basis) or (None, None). basis in
        {'code','customer_number','name_exact'} -- all deterministic."""
        for c in codes:
            if c in self.base_keys:
                return c, "code"
        for cu in custs:
            n = norm_cust(cu)
            if n and n in self.cust_to_key:
                return self.cust_to_key[n], "customer_number"
        for nm in names:
            k = self.name_to_key.get(name_match.normalize(nm))
            if k:
                return k, "name_exact"
        return None, None


def build_resolver(base_headers, base_data, key_col, name_col, crosswalk):
    """Build an AccountResolver from the base table + the ISC customer crosswalk."""
    base_keys, name_to_key, name_dupes = set(), {}, set()
    for row in base_data:
        key = str(row[key_col]).strip() if key_col < len(row) and row[key_col] not in (None, "") else ""
        if not key:
            continue
        base_keys.add(key)
        nm = name_match.normalize(row[name_col]) if name_col < len(row) else ""
        if nm:
            if nm in name_to_key and name_to_key[nm] != key:
                name_dupes.add(nm)        # ambiguous name -> don't trust it
            else:
                name_to_key[nm] = key
    for nm in name_dupes:
        name_to_key.pop(nm, None)
    cust_to_key = (crosswalk or {}).get("cust_to_key", {})
    # Keep only crosswalk links that point at an account actually in this base.
    cust_to_key = {c: k for c, k in cust_to_key.items() if k in base_keys}
    return AccountResolver(base_keys, cust_to_key, name_to_key)


def extract_ids(row, header_index, spec):
    """(codes, custs, names) for one install row, per a config.ID_COLUMNS spec.
    header_index: {header -> column position}."""
    def col(h):
        i = header_index.get(h)
        return row[i] if i is not None and i < len(row) else None
    codes = []
    for h in spec.get("codes", []):
        codes.extend(codes_in(col(h)))
    custs = [col(h) for h in spec.get("custs", [])]
    names = [col(h) for h in spec.get("names", [])]
    return codes, [c for c in custs if c not in (None, "")], [n for n in names if n not in (None, "")]


class InstallKeyIndex:
    """Maps each DEDUPED account key -> the install rows that belong to it,
    resolved deterministically. Built once per install file."""

    def __init__(self, headers, data, spec, resolver):
        self.header_index = {h: i for i, h in enumerate(headers)}
        self.key_to_rows = {}       # account_key -> [row indices]
        self.row_basis = {}         # row index -> basis (for reporting)
        self.unmatched = 0
        self.basis_counts = {"code": 0, "customer_number": 0, "name_exact": 0}
        for r, row in enumerate(data):
            codes, custs, names = extract_ids(row, self.header_index, spec)
            key, basis = resolver.resolve(codes, custs, names)
            if key is None:
                self.unmatched += 1
                continue
            self.key_to_rows.setdefault(key, []).append(r)
            self.row_basis[r] = basis
            self.basis_counts[basis] += 1

    def rows_for(self, account_key):
        return self.key_to_rows.get(account_key, [])

    @property
    def matched_rows(self):
        return sum(len(v) for v in self.key_to_rows.values())

    @property
    def accounts_hit(self):
        return len(self.key_to_rows)
