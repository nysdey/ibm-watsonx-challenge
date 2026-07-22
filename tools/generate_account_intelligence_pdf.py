#!/usr/bin/env python3
"""Build the official BobBee Account Intelligence PDF from live demo state."""

from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import median
import json
import math
import zipfile

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "instance/state.json"
SCREENS = ROOT / "tmp/pdfs/account-intelligence/screens"
OUT = ROOT / "BobBee_Pitch.pdf"
FONT_ZIP = Path("/private/tmp/ibm-plex.zip")
FONT_DIR = ROOT / "tmp/pdfs/account-intelligence/fonts"

W, H = landscape(letter)
M = 42
BLACK = colors.HexColor("#161616")
GRAY = colors.HexColor("#525252")
MID = colors.HexColor("#8D8D8D")
LIGHT = colors.HexColor("#DDE1E6")
BLUE = colors.HexColor("#0F62FE")
BLUE2 = colors.HexColor("#4589FF")
CYAN = colors.HexColor("#1192E8")
TEAL = colors.HexColor("#009D9A")
PURPLE = colors.HexColor("#8A3FFC")
MAGENTA = colors.HexColor("#EE5396")
RED = colors.HexColor("#DA1E28")
GREEN = colors.HexColor("#198038")
WHITE = colors.white


def install_fonts():
    FONT_DIR.mkdir(parents=True, exist_ok=True)
    wanted = {
        "Plex": "IBMPlexSans-Regular.ttf",
        "Plex-Medium": "IBMPlexSans-Medium.ttf",
        "Plex-Semibold": "IBMPlexSans-SemiBold.ttf",
        "Plex-Bold": "IBMPlexSans-Bold.ttf",
    }
    with zipfile.ZipFile(FONT_ZIP) as zf:
        lookup = {Path(n).name: n for n in zf.namelist()}
        for face, filename in wanted.items():
            target = FONT_DIR / filename
            if not target.exists():
                target.write_bytes(zf.read(lookup[filename]))
            pdfmetrics.registerFont(TTFont(face, str(target)))


def txt(c, x, y, s, size=10, face="Plex", color=BLACK, maxw=None, leading=None):
    c.setFont(face, size)
    c.setFillColor(color)
    if maxw is None:
        c.drawString(x, y, str(s))
        return y
    words = str(s).split()
    lines, line = [], ""
    for word in words:
        test = f"{line} {word}".strip()
        if pdfmetrics.stringWidth(test, face, size) <= maxw or not line:
            line = test
        else:
            lines.append(line); line = word
    if line: lines.append(line)
    lead = leading or size * 1.35
    for i, line in enumerate(lines):
        c.drawString(x, y - i * lead, line)
    return y - (len(lines) - 1) * lead


def rule(c, x1, y, x2, color=LIGHT, width=.7):
    c.setStrokeColor(color); c.setLineWidth(width); c.line(x1, y, x2, y)


def header(c, kicker, title, deck=None, page=1):
    txt(c, M, H - 36, "IBM BobBee", 9, "Plex-Semibold")
    txt(c, W - M - 145, H - 36, "ACCOUNT INTELLIGENCE", 8, "Plex-Semibold", MID)
    rule(c, M, H - 46, W - M, BLACK, 1)
    txt(c, M, H - 72, kicker.upper(), 8, "Plex-Semibold", BLUE)
    txt(c, M, H - 103, title, 24, "Plex-Semibold")
    if deck:
        txt(c, M, H - 124, deck, 10.5, "Plex", GRAY, W - 2*M, 14)
    txt(c, W - M - 10, 24, f"{page:02d}", 8, "Plex-Medium", MID)
    rule(c, M, 34, W - M - 24, LIGHT, .6)


def metric(c, x, y, value, label, width=130, color=BLUE):
    txt(c, x, y, value, 28, "Plex-Semibold", color)
    rule(c, x, y - 9, x + width, LIGHT, .6)
    txt(c, x, y - 25, label, 9, "Plex-Medium", GRAY, width, 12)


def hbar(c, x, y, width, rows, maxv=None, row_h=28, value_fmt=lambda v: str(v)):
    maxv = maxv or max(v for _, v, _ in rows) or 1
    for i, (label, value, color) in enumerate(rows):
        yy = y - i * row_h
        txt(c, x, yy + 5, label, 8.5, "Plex-Medium", GRAY, 120)
        bx = x + 125
        bw = width - 165
        rule(c, bx, yy + 2, bx + bw, LIGHT, 4)
        c.setStrokeColor(color); c.setLineWidth(8); c.line(bx, yy + 2, bx + bw * value / maxv, yy + 2)
        txt(c, x + width - 34, yy - 1, value_fmt(value), 8.5, "Plex-Semibold", BLACK)


def donut(c, cx, cy, radius, parts, center_top, center_bottom):
    total = sum(v for _, v, _ in parts) or 1
    start = 90
    c.setLineWidth(15)
    for _, v, color in parts:
        extent = 360 * v / total
        c.setStrokeColor(color)
        c.arc(cx-radius, cy-radius, cx+radius, cy+radius, startAng=start, extent=-extent)
        start -= extent
    txt(c, cx - 22, cy + 2, center_top, 16, "Plex-Semibold")
    txt(c, cx - 23, cy - 14, center_bottom, 7.5, "Plex-Medium", MID)


def legend(c, x, y, parts, gap=18):
    yy = y
    for label, value, color in parts:
        c.setFillColor(color); c.rect(x, yy-3, 7, 7, stroke=0, fill=1)
        txt(c, x+13, yy-2, f"{label}  {value:,}", 8.5, "Plex-Medium", GRAY)
        yy -= gap


def image_frame(c, path, x, y, w, h, caption):
    img = ImageReader(str(path)); iw, ih = img.getSize()
    scale = min(w/iw, h/ih)
    dw, dh = iw*scale, ih*scale
    ox, oy = x+(w-dw)/2, y+(h-dh)/2
    c.setStrokeColor(BLACK); c.setLineWidth(.8); c.rect(ox, oy, dw, dh, stroke=1, fill=0)
    c.drawImage(img, ox, oy, dw, dh, preserveAspectRatio=True, mask='auto')
    txt(c, x, y-15, caption, 7.8, "Plex", MID, w)


def page_cover(c, data):
    c.setFillColor(BLACK); c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(BLUE); c.rect(0, 0, 14, H, fill=1, stroke=0)
    txt(c, 54, H-54, "IBM BobBee", 11, "Plex-Semibold", WHITE)
    txt(c, 54, H-162, "BobBee", 39, "Plex-Semibold", WHITE)
    txt(c, 54, H-208, "technical guide", 39, "Plex-Semibold", WHITE)
    txt(c, 54, H-243, "Account intelligence and seller execution", 13, "Plex", colors.HexColor('#C6C6C6'))
    c.setStrokeColor(BLUE2); c.setLineWidth(2); c.line(54, H-286, W-70, H-286)
    txt(c, 54, H-322, "From 1,911 accounts to the next best seller action.", 13, "Plex-Medium", WHITE)
    txt(c, 54, 89, "Developed by", 8, "Plex-Semibold", BLUE2)
    txt(c, 54, 66, "Sydney Chin  /  Tim Zhou  /  Patrick McBride", 12, "Plex-Medium", WHITE)
    txt(c, W-160, 28, "JULY 2026", 8, "Plex-Semibold", colors.HexColor('#A8A8A8'))
    c.showPage()


def build():
    install_fonts(); OUT.parent.mkdir(parents=True, exist_ok=True)
    data = json.loads(STATE.read_text())
    accts = data["accounts"]
    strategy = data["strategy"]
    total = len(accts)
    tiers = Counter(a["tier"] for a in accts)
    buckets = Counter(a["bucket"] for a in accts)
    plays = Counter(a["play"] for a in accts)
    industries = Counter(a["industry"] for a in accts)
    states = Counter(a["state"] for a in accts)
    signals = Counter(s["type"] for a in accts for s in a.get("signals", []))
    scored = [a["score"] for a in accts]
    current = [a for a in accts if a["bucket"] == "cadence"]
    selected = next((a for a in accts if a["name"] == "Vertex Municipal"), current[0])
    cadence_counts = Counter(a["cadence"] for a in current)
    no_dm = sum(not a.get("has_decision_maker") for a in accts)
    whitespace = sum(any(t.startswith("Whitespace") for t in a.get("tags", [])) for a in accts)
    at_risk = sum("At-risk spend" in a.get("tags", []) for a in accts)
    growing = sum("Growing spend" in a.get("tags", []) for a in accts)

    c = canvas.Canvas(str(OUT), pagesize=(W, H), pageCompression=1)
    c.setTitle("IBM BobBee Technical Guide")
    c.setAuthor("Sydney Chin, Tim Zhou, Patrick McBride")
    page_cover(c, data)

    header(c, "Executive view", "A territory book becomes a finite action system",
           "BobBee separates evidence, deterministic decisions, and generative assistance so sellers can trust the ranking and act on it.", 2)
    metric(c, M, 414, f"{total:,}", "accounts normalized into one territory book")
    metric(c, 190, 414, f"{len(current):,}", "accounts activated in current-quarter cadences", color=TEAL)
    metric(c, 357, 414, f"{len(strategy['cadences'])}", "purpose-built outreach motions", color=PURPLE)
    metric(c, 524, 414, f"{no_dm:,}", "accounts withheld for missing decision-maker", color=MAGENTA)
    txt(c, M, 324, "THE DECISION LOOP", 8, "Plex-Semibold", MID)
    steps = [("01", "Unify", "ISC, ZoomInfo, Salesloft, install base and signals"),
             ("02", "Score", "Fit, momentum, whitespace and urgency become an inspectable score"),
             ("03", "Route", "Quarter, cadence, rank and start date turn the score into work"),
             ("04", "Activate", "Daily email, call and pre-call context meet the seller in flow")]
    x = M
    for n, title, desc in steps:
        txt(c, x, 288, n, 8, "Plex-Semibold", BLUE)
        rule(c, x, 278, x+155, BLACK, 1)
        txt(c, x, 257, title, 13, "Plex-Semibold")
        txt(c, x, 236, desc, 8.5, "Plex", GRAY, 150, 11)
        x += 173
    txt(c, M, 134, "Design principle", 9, "Plex-Semibold", BLUE)
    txt(c, M, 113, "Rank first. Explain always. Generate only where language adds value.", 18, "Plex-Medium", BLACK, W-2*M)
    c.showPage()

    header(c, "The seller problem", "A large account book makes prioritization the first problem",
           "A Select Territory seller owns roughly 1,900 accounts across several source systems. The scarce resource is not data; it is attention.", 3)
    metric(c, M, 404, "~1,900", "accounts in a Select Territory book", 155)
    metric(c, 240, 404, "3", "source systems reconciled by hand", 145, PURPLE)
    metric(c, 430, 404, "~4 hrs", "daily triage and drafting before BobBee", 160, MAGENTA)
    txt(c, M, 307, "THE FAILURE MODE", 8, "Plex-Semibold", MID)
    problems = [("01", "Fragmented context", "Spend, installs, contacts and activity live in different systems."),
                ("02", "Uneven prioritization", "The loudest account can displace the account with the strongest evidence."),
                ("03", "Planning consumes selling time", "A seller spends the morning assembling context before taking action."),
                ("04", "AI without provenance", "Generated language is difficult to trust when facts and suggestions look identical.")]
    yy = 270
    for n, title, desc in problems:
        txt(c, M, yy, n, 8, "Plex-Semibold", BLUE)
        txt(c, M+38, yy, title, 11, "Plex-Semibold")
        txt(c, 285, yy, desc, 9, "Plex", GRAY, 430, 12)
        rule(c, M+38, yy-14, W-M, LIGHT, .5)
        yy -= 47
    txt(c, M, 72, "BobBee does not add another dashboard to interpret. It converts the book into an ordered plan of work.", 13, "Plex-Medium", BLACK)
    c.showPage()

    header(c, "Product experience", "A decision, its evidence, and a ready next step",
           "The seller starts with a ranked day. Account context and language support are available at the moment of action, not in another workflow.", 4)
    outputs = [("Morning brief", "A plain-language summary of the day and where to begin."),
               ("Ranked daily plan", "Who to work, in what order, and why the account is urgent now."),
               ("Email draft", "Contextual outreach prepared for review, edit and send."),
               ("Pre-call brief", "Relationship, signal, likely objection and recommended angle before dialing."),
               ("Ask BobBee", "Natural-language access to the same governed account context.")]
    yy = 405
    for i, (title, desc) in enumerate(outputs, 1):
        txt(c, M, yy, f"{i:02d}", 8, "Plex-Semibold", PURPLE if i in (4,5) else BLUE)
        txt(c, 86, yy, title, 12, "Plex-Semibold")
        txt(c, 255, yy, desc, 9.5, "Plex", GRAY, 460, 13)
        rule(c, 86, yy-15, W-M, LIGHT, .5)
        yy -= 53
    txt(c, M, 112, "Example seller instruction", 8, "Plex-Semibold", BLUE)
    txt(c, M, 87, "Start with Vertex Municipal: earnings momentum is strong, IBM spend is growing, and the account ranks #8 in its cadence.", 14, "Plex-Medium", BLACK, W-2*M, 18)
    c.showPage()

    header(c, "Productivity impact", "Four hours of planning becomes forty-five minutes of doing",
           "The value is reclaimed seller capacity: less manual assembly, more time reviewing high-confidence work and engaging clients.", 5)
    txt(c, M, 394, "BEFORE BOBBEE", 8, "Plex-Semibold", MID)
    txt(c, W-M-72, 394, "~4.0 HRS", 9, "Plex-Semibold", BLACK)
    rule(c, M, 367, W-M, colors.HexColor('#A8A8A8'), 20)
    txt(c, M, 319, "WITH BOBBEE", 8, "Plex-Semibold", MID)
    txt(c, W-M-76, 319, "~0.75 HRS", 9, "Plex-Semibold", BLACK)
    rule(c, M, 292, W-M, LIGHT, 20)
    c.setStrokeColor(BLUE); c.setLineWidth(20); c.line(M, 292, M+(W-2*M)*.1875, 292)
    metric(c, M, 224, "~3.25 hrs", "reclaimed per seller, every day", 190, BLUE)
    metric(c, 295, 224, "~16 hrs", "reclaimed per seller, every week", 190, PURPLE)
    txt(c, M, 128, "Where the time moves", 8, "Plex-Semibold", MID)
    txt(c, M, 104, "From cross-system research and first-draft creation to account review, client judgment and direct engagement.", 13, "Plex-Medium", BLACK, W-2*M, 17)
    c.showPage()

    header(c, "System architecture", "One intelligence chain, three distinct responsibilities",
           "Blue is deterministic product logic. Purple is watsonx-generated language. The boundary is explicit by design.", 6)
    columns = [
        (M, "EVIDENCE", BLUE, ["Territory and coverage", "IBM spend and trend", "Install base", "Company scale", "Decision-makers", "Recent buying signals"]),
        (282, "DECISION ENGINE", TEAL, ["Eligibility gate", "Weighted score", "Tier assignment", "Quarter segmentation", "Cadence match", "Within-cadence rank"]),
        (522, "SELLER EXPERIENCE", PURPLE, ["Priority account book", "Recommended play", "Daily schedule", "Account detail", "Pre-call brief", "Ask BobBee"]),
    ]
    for x, title, color, items in columns:
        txt(c, x, 408, title, 8, "Plex-Semibold", color)
        rule(c, x, 395, x+190, color, 2)
        yy = 365
        for i, item in enumerate(items, 1):
            txt(c, x, yy, f"{i:02d}", 8, "Plex-Semibold", MID)
            txt(c, x+28, yy, item, 11, "Plex-Medium", BLACK)
            rule(c, x+28, yy-10, x+190, LIGHT, .5)
            yy -= 42
    txt(c, M, 95, "Control point", 8, "Plex-Semibold", MAGENTA)
    txt(c, M+88, 95, "No decision-maker -> held out. No model response -> deterministic fallback. No hidden ranking step.", 10, "Plex-Medium")
    c.showPage()

    header(c, "Portfolio shape", "The book is broad; the active quarter is deliberately narrow",
           "The engine focuses capacity without discarding future value. Every account remains visible in a named bucket.", 7)
    bucket_parts = [("Current cadences", buckets["cadence"], BLUE), ("Future quarters", buckets["future"], CYAN),
                    ("Leftovers", buckets["leftovers"], PURPLE), ("No contacts", buckets["no_contacts"], MAGENTA)]
    donut(c, 145, 280, 82, bucket_parts, f"{total:,}", "ACCOUNTS")
    legend(c, 245, 328, bucket_parts)
    tier_parts = [("Tier 1", tiers[1], BLUE), ("Tier 2", tiers[2], TEAL), ("Tier 3", tiers[3], MID)]
    txt(c, 410, 390, "PRIORITY TIERS", 8, "Plex-Semibold", MID)
    hbar(c, 410, 350, 310, tier_parts, max(tiers.values()), value_fmt=lambda v:f"{v:,}")
    txt(c, 410, 238, "GEOGRAPHIC COVERAGE", 8, "Plex-Semibold", MID)
    geo = [(k, v, [BLUE, CYAN, TEAL, PURPLE][i]) for i,(k,v) in enumerate(states.most_common())]
    hbar(c, 410, 202, 310, geo, max(states.values()), value_fmt=lambda v:f"{v:,}")
    txt(c, M, 91, "Readout", 8, "Plex-Semibold", BLUE)
    txt(c, M+63, 91, f"{buckets['cadence']/total:.1%} of the book enters live cadences this quarter; {buckets['future']/total:.1%} is preserved for later timing.", 10, "Plex-Medium")
    c.showPage()

    header(c, "Scoring anatomy", "The score is a lens, not an oracle",
           "The account score combines commercial evidence and observable momentum. Tiering provides a stable comparison layer before timing and capacity are applied.", 8)
    bins = [0, 25, 35, 45, 55, 65, 75, 101]
    hist = Counter()
    for score in scored:
        for lo, hi in zip(bins[:-1], bins[1:]):
            if lo <= score < hi: hist[f"{lo}-{hi-1}"] += 1; break
    ordered_bins = [f"{lo}-{hi-1}" for lo, hi in zip(bins[:-1], bins[1:])]
    rows = [(k, hist[k], [MID, CYAN, BLUE2, BLUE, TEAL, PURPLE, MAGENTA][i]) for i,k in enumerate(ordered_bins)]
    txt(c, M, 405, "SCORE DISTRIBUTION", 8, "Plex-Semibold", MID)
    hbar(c, M, 370, 360, rows, max(hist.values()), value_fmt=lambda v:f"{v:,}")
    metric(c, 450, 376, f"{median(scored):.1f}", "median account score", 110)
    metric(c, 590, 376, f"{max(scored):.1f}", "highest account score", 115, PURPLE)
    factors = [("IBM position", "Current spend, prior spend and trend"), ("Whitespace", "Missing cloud, power, storage and software footprint"),
               ("Market scale", "Revenue and employee scale"), ("Engagement", "Decision-maker availability and contact depth"),
               ("Momentum", "Recent expansion, funding, leadership and risk signals"), ("Competitive posture", "Incumbent platform and displacement opportunity")]
    txt(c, 450, 278, "EVIDENCE FAMILIES", 8, "Plex-Semibold", MID)
    for i, (title, desc) in enumerate(factors):
        col, row = i % 2, i // 2
        x, yy = 450 + col * 145, 248 - row * 62
        txt(c, x, yy, title, 8.8, "Plex-Semibold")
        txt(c, x, yy-17, desc, 7.5, "Plex", GRAY, 132, 9)
        rule(c, x, yy-43, x+132, LIGHT, .4)
    txt(c, M, 60, "The score is never the final action. Eligibility, quarter timing, cadence fit and capacity complete the decision.", 8.5, "Plex-Medium", GRAY)
    c.showPage()

    header(c, "Application view", "The prioritized account book keeps evidence at the point of choice",
           "Sellers can search, filter by signal, move between named buckets, and open any row to inspect the underlying account intelligence.", 9)
    image_frame(c, SCREENS/"02-account-book.png", M, 92, W-2*M, 350, "Figure 1. Live BobBee account book after scoring and cadence assignment. Captured from the application.")
    c.showPage()

    header(c, "Application view", "An account explanation, not just a score",
           "The detail view brings together the recommendation, IBM commercial context, external company facts, contacts, cadence position and recent signals.", 10)
    image_frame(c, SCREENS/"03-account-detail.png", M, 82, W-2*M, 360, f"Figure 2. Live account-detail view for {selected['name']}. Captured from the application.")
    c.showPage()

    header(c, "Account deep dive", selected["name"],
           f"{selected['industry']}  /  {selected['location']}  /  {selected['relationship']}", 11)
    metric(c, M, 407, f"{selected['score']:.1f}", f"score / tier {selected['tier']}", 110)
    revenue_label = f"${selected['revenue']/1e9:.1f}B" if selected['revenue'] >= 1e9 else f"${selected['revenue']/1e6:.1f}M"
    metric(c, 185, 407, revenue_label, "annual revenue", 125, TEAL)
    metric(c, 350, 407, f"{selected['employees']:,}", "employees", 110, CYAN)
    metric(c, 500, 407, f"#{selected['rank']}", "rank in cadence", 110, PURPLE)
    txt(c, M, 318, "RECOMMENDED PLAY", 8, "Plex-Semibold", MID)
    txt(c, M, 292, selected['play'], 19, "Plex-Semibold", BLUE)
    txt(c, M, 255, selected['angle'], 11, "Plex-Medium", BLACK, 330, 15)
    txt(c, 430, 318, "WHY THIS ACCOUNT", 8, "Plex-Semibold", MID)
    reasons = [f"{selected['spend_trend']} IBM spend trend", f"{selected['contact_count']} known contacts; decision-maker available",
               f"{len(selected['signals'])} recent signal(s)", f"Assigned to {selected['cadence']}"]
    yy=290
    for i, reason in enumerate(reasons,1):
        txt(c, 430, yy, f"{i:02d}", 8, "Plex-Semibold", BLUE)
        txt(c, 460, yy, reason, 10, "Plex-Medium"); rule(c, 460, yy-10, 725, LIGHT, .5); yy-=39
    txt(c, M, 139, "SIGNALS", 8, "Plex-Semibold", MID)
    for i,s in enumerate(selected['signals'][:3]):
        x=M+i*230
        txt(c, x, 112, s['type'].replace('_',' '), 9, "Plex-Semibold", MAGENTA)
        txt(c, x, 94, s['summary'], 7.8, "Plex", GRAY, 210, 10)
    c.showPage()

    header(c, "Portfolio opportunities", "The intelligence layer reveals repeatable plays across the book",
           "Play assignment turns individual account evidence into an operating portfolio that sales leaders can inspect and rebalance.", 12)
    play_rows = [(k, v, [BLUE, CYAN, TEAL, PURPLE, MAGENTA, MID][i%6]) for i,(k,v) in enumerate(plays.most_common())]
    txt(c, M, 398, "RECOMMENDED PLAYS", 8, "Plex-Semibold", MID)
    hbar(c, M, 362, 360, play_rows, max(plays.values()), value_fmt=lambda v:f"{v:,}")
    ind_rows = [(k, v, [BLUE, CYAN, TEAL, PURPLE, MAGENTA][i%5]) for i,(k,v) in enumerate(industries.most_common(7))]
    txt(c, 430, 398, "LARGEST INDUSTRY BOOKS", 8, "Plex-Semibold", MID)
    hbar(c, 430, 362, 310, ind_rows, max(industries.values()), value_fmt=lambda v:f"{v:,}")
    metric(c, M, 105, f"{whitespace:,}", "accounts with at least one whitespace tag", 175, BLUE)
    metric(c, 285, 105, f"{at_risk:,}", "accounts showing at-risk spend", 155, MAGENTA)
    metric(c, 520, 105, f"{growing:,}", "accounts showing growing spend", 155, TEAL)
    c.showPage()

    header(c, "Activation mechanics", "Capacity becomes a visible design choice",
           "Each active cadence is capped, ranked and distributed across weekdays. Overflow is named and retained rather than silently dropped.", 13)
    cad_rows = [(k.replace(" Cadence", ""), v, [BLUE, CYAN, TEAL, PURPLE][i]) for i,(k,v) in enumerate(cadence_counts.items())]
    txt(c, M, 397, "CURRENT-QUARTER CADENCES", 8, "Plex-Semibold", MID)
    hbar(c, M, 356, 410, cad_rows, max(cadence_counts.values()), value_fmt=lambda v:f"{v:,}")
    metric(c, 520, 361, f"{sum(cadence_counts.values()):,}", "scheduled into current-quarter cadences", 175)
    metric(c, 520, 270, f"{buckets['leftovers']:,}", "capacity overflow retained for future work", 175, PURPLE)
    metric(c, 520, 179, f"{buckets['no_contacts']:,}", "withheld until a decision-maker is found", 175, MAGENTA)
    txt(c, M, 146, "Operational contract", 8, "Plex-Semibold", BLUE)
    txt(c, M, 122, "Every activated account has a play, cadence, rank and dated sequence of touches.", 15, "Plex-Medium", BLACK)
    c.showPage()

    header(c, "Seller workflow", "Intelligence resolves into today’s work",
           "The dashboard is the final compression layer: a morning brief, today’s emails and calls, and access to deeper analytics when needed.", 14)
    image_frame(c, SCREENS/"01-dashboard.png", M, 92, W-2*M, 350, "Figure 3. Live BobBee dashboard after the territory book is activated. Captured from the application.")
    c.showPage()

    header(c, "Trust and governance", "Deterministic where it must be; generative where it helps",
           "BobBee keeps model-generated language downstream from the ranking so a model outage cannot change account priority, cadence assignment or schedule.", 15)
    rows = [("Account eligibility", "Deterministic", "Decision-maker gate"), ("Score and tier", "Deterministic", "Weighted application logic"),
            ("Quarter and cadence", "Deterministic", "Timing, fit and capacity"), ("Email draft", "Deterministic", "Contextual templates"),
            ("Sales angle", "watsonx.ai", "Granite with deterministic fallback"), ("Pre-call brief", "watsonx.ai", "Granite with deterministic fallback")]
    txt(c, M, 402, "CAPABILITY", 8, "Plex-Semibold", MID); txt(c, 300, 402, "SOURCE", 8, "Plex-Semibold", MID); txt(c, 470, 402, "CONTROL", 8, "Plex-Semibold", MID)
    rule(c, M, 390, W-M, BLACK, 1)
    yy=363
    for capability, source, control in rows:
        txt(c, M, yy, capability, 10, "Plex-Medium")
        txt(c, 300, yy, source, 10, "Plex-Semibold", PURPLE if source.startswith('watsonx') else BLUE)
        txt(c, 470, yy, control, 9, "Plex", GRAY)
        rule(c, M, yy-14, W-M, LIGHT, .5); yy-=45
    txt(c, M, 78, "Source note: all account and activity data in this demo is deterministic synthetic data; external systems are represented locally.", 8, "Plex", MID)
    c.showPage()

    header(c, "Methodology in product", "The explanation is available inside BobBee",
           "Methodology is not buried in a technical appendix. Sellers can revisit the five stages from Profile > Settings > How account intelligence works.", 16)
    image_frame(c, SCREENS/"04-methodology.png", M, 92, W-2*M, 350, "Figure 4. Live in-product account-intelligence methodology. Captured from the application.")
    c.showPage()

    header(c, "Field guide", "What a seller can inspect on every account", None, 17)
    fields = [("Identity", "Account, coverage ID, industry and location"), ("IBM position", "Relationship, current/prior spend, trend and installs"),
              ("Company context", "Revenue, employees and known contacts"), ("Momentum", "Dated signals and news summaries"),
              ("Decision", "Score, tier, urgency, recommended play and angle"), ("Activation", "Cadence, within-cadence rank and scheduled touches")]
    yy=407
    for i,(name,desc) in enumerate(fields,1):
        txt(c, M, yy, f"{i:02d}", 9, "Plex-Semibold", BLUE)
        txt(c, M+42, yy, name, 14, "Plex-Semibold")
        txt(c, 245, yy, desc, 10, "Plex", GRAY, 475, 13)
        rule(c, M+42, yy-17, W-M, LIGHT, .6); yy-=57
    txt(c, M, 70, "Developed by Sydney Chin, Tim Zhou, and Patrick McBride", 9, "Plex-Semibold", BLACK)
    c.save()
    print(OUT)


if __name__ == "__main__":
    build()
