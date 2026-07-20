"""Stable business vocabulary shared by scoring and presentation."""

DECISION_MAKER_TITLES = frozenset({
    "VP of Infrastructure",
    "Director of IT",
    "Chief Information Officer",
    "Head of Cloud Platform",
    "VP Engineering",
    "Director of Data & Analytics",
    "Chief Technology Officer",
    "Director of Information Security",
    "VP Digital Transformation",
})

PLAY_TO_CADENCE = {
    "Expand & Protect": "Enterprise Expansion Cadence",
    "Hardware Refresh": "Enterprise Expansion Cadence",
    "Displace Competitor": "Targeted Outreach Cadence 3",
    "Land New Logo": "Targeted Outreach Cadence 4",
    "Win-Back": "Whitespace Nurture Cadence",
    "Nurture": "Whitespace Nurture Cadence",
}

CADENCE_DESCRIPTIONS = {
    "Enterprise Expansion Cadence": "Protect and grow IBM revenue at established accounts with expansion or refresh potential.",
    "Targeted Outreach Cadence 3": "Displace an entrenched competitor with direct, proof-led outreach.",
    "Targeted Outreach Cadence 4": "Land a first IBM workload at a net-new account.",
    "Whitespace Nurture Cadence": "Re-engage a cold account or develop an early-stage opportunity.",
}

TERRITORIES = ("CA", "HI", "GU", "MP")
CADENCE_CAP = 60
STARTS_PER_DAY = 3

