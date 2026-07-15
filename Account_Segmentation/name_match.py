"""Company-name normalization + fuzzy matching for the Segmentation join.

The same real account shows up under slightly different names across files
("John's Hospital" vs "JOHNS HOSPITAL" vs "Johns Hospital Inc."). We normalize
(uppercase, strip punctuation, drop legal suffixes) and then fuzzy-match above a
similarity threshold, flagging borderline matches for review rather than guessing.
Stdlib only (difflib) -- no external fuzzy-match dependency.
"""
import difflib
import re

# Legal/entity suffixes and filler tokens that shouldn't drive a name match.
_STOP_TOKENS = {
    "INC", "INCORPORATED", "LLC", "LLP", "LP", "LTD", "LIMITED", "CORP",
    "CORPORATION", "CO", "COMPANY", "PLC", "GROUP", "HOLDINGS", "HOLDING",
    "THE", "AND", "OF", "GMBH", "SA", "AG", "NV", "BV", "PTE", "PVT",
}

# Auto-accept at/above AUTO; flag as "review" between REVIEW and AUTO; below
# REVIEW is treated as no match.
AUTO_THRESHOLD = 0.90
REVIEW_THRESHOLD = 0.82


def normalize(value):
    """Canonical form for comparison: uppercase, '&'->'AND', punctuation
    stripped, legal suffixes/filler removed, whitespace collapsed."""
    s = str(value if value is not None else "").upper()
    # Strip apostrophes WITHOUT inserting a space, so a possessive collapses
    # ("JOHN'S" -> "JOHNS", "O'REILLY" -> "OREILLY") rather than splitting into
    # a stray "S" token. This is the canonical case (John's Hospital ≈ JOHNS
    # HOSPITAL) the whole fuzzy join exists for.
    s = s.replace("'", "").replace("’", "").replace("‘", "")
    s = s.replace("&", " AND ")
    s = re.sub(r"[^A-Z0-9 ]", " ", s)          # remaining punctuation -> space
    tokens = [t for t in s.split() if t and t not in _STOP_TOKENS]
    return " ".join(tokens)


def _tokens(norm):
    return set(norm.split())


def similarity(a_norm, b_norm):
    """0..1 similarity between two ALREADY-NORMALIZED names. Combines a raw
    sequence ratio, a token-sorted ratio (order-insensitive), and token Jaccard
    so 'JOHNS HOSPITAL' and 'HOSPITAL JOHNS' still score high."""
    if not a_norm or not b_norm:
        return 0.0
    if a_norm == b_norm:
        return 1.0
    seq = difflib.SequenceMatcher(None, a_norm, b_norm).ratio()
    ta, tb = _tokens(a_norm), _tokens(b_norm)
    sorted_ratio = difflib.SequenceMatcher(
        None, " ".join(sorted(ta)), " ".join(sorted(tb))
    ).ratio()
    jacc = len(ta & tb) / len(ta | tb) if (ta | tb) else 0.0
    return max(seq, sorted_ratio, jacc)


def classify(score):
    if score >= AUTO_THRESHOLD:
        return "matched"
    if score >= REVIEW_THRESHOLD:
        return "review"
    return "none"


class NameIndex:
    """Index of an install file's names for fast matching against base accounts.

    exact_map: normalized name -> list of source row indices (0-based into the
    install file's data rows). unique_norms: distinct normalized names for the
    fuzzy fallback scan.
    """

    def __init__(self):
        self.exact_map = {}
        self.unique_norms = []

    def add(self, raw_name, row_index):
        norm = normalize(raw_name)
        if not norm:
            return
        if norm not in self.exact_map:
            self.exact_map[norm] = []
            self.unique_norms.append(norm)
        self.exact_map[norm].append(row_index)

    def match(self, base_name):
        """Return (norm_matched, score, quality, row_indices) or (None, 0, 'none', [])."""
        base_norm = normalize(base_name)
        if not base_norm:
            return None, 0.0, "none", []
        # Exact normalized hit.
        if base_norm in self.exact_map:
            return base_norm, 1.0, "matched", self.exact_map[base_norm]
        # Fuzzy fallback: best over distinct install names.
        best_norm, best_score = None, 0.0
        for cand in self.unique_norms:
            sc = similarity(base_norm, cand)
            if sc > best_score:
                best_norm, best_score = cand, sc
                if best_score == 1.0:
                    break
        quality = classify(best_score)
        if quality == "none":
            return None, best_score, "none", []
        return best_norm, best_score, quality, self.exact_map[best_norm]
