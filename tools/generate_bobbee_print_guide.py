#!/usr/bin/env python3
"""Generate the print-ready, portrait BobBee technical guide."""

from collections import Counter
from pathlib import Path
from statistics import median
import json, shutil, zipfile

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "BobBee_Pitch.pdf"
FINAL_OUT = ROOT / "output/pdf/BobBee_Pitch.pdf"
STATE = ROOT / "instance/state.json"
SCREENS = ROOT / "tmp/pdfs/account-intelligence/screens"
FONT_ZIP = Path("/private/tmp/ibm-plex.zip")
FONT_DIR = ROOT / "tmp/pdfs/account-intelligence/fonts"
W, H = letter
M = 42

INK = colors.HexColor("#161616")
TEXT = colors.HexColor("#525252")
MUTED = colors.HexColor("#8D8D8D")
RULE = colors.HexColor("#DDE1E6")
BLUE = colors.HexColor("#0F62FE")
CYAN = colors.HexColor("#4589FF")
TEAL = colors.HexColor("#0043CE")
PURPLE = colors.HexColor("#8A3FFC")
MAGENTA = colors.HexColor("#A56EFF")
WHITE = colors.white


def fonts():
    FONT_DIR.mkdir(parents=True, exist_ok=True)
    faces = {"Plex":"IBMPlexSans-Regular.ttf", "Plex-Medium":"IBMPlexSans-Medium.ttf",
             "Plex-Semibold":"IBMPlexSans-SemiBold.ttf", "Plex-Bold":"IBMPlexSans-Bold.ttf"}
    with zipfile.ZipFile(FONT_ZIP) as z:
        names = {Path(n).name:n for n in z.namelist()}
        for face, fn in faces.items():
            target = FONT_DIR/fn
            if not target.exists(): target.write_bytes(z.read(names[fn]))
            pdfmetrics.registerFont(TTFont(face, str(target)))


def text(c, x, y, value, size=10, face="Plex", color=INK, width=None, leading=None):
    value = str(value)
    c.setFont(face, size); c.setFillColor(color)
    if width is None:
        c.drawString(x, y, value); return y
    words, lines, current = value.split(), [], ""
    for word in words:
        trial = (current + " " + word).strip()
        if not current or pdfmetrics.stringWidth(trial, face, size) <= width: current = trial
        else: lines.append(current); current = word
    if current: lines.append(current)
    lead = leading or size*1.35
    for i, line in enumerate(lines): c.drawString(x, y-i*lead, line)
    return y-(len(lines)-1)*lead


def line(c, x1, y, x2, color=RULE, stroke=.65):
    c.setStrokeColor(color); c.setLineWidth(stroke); c.line(x1,y,x2,y)


def page_header(c, section, title, deck, page):
    text(c, M, H-31, "IBM BobBee", 8.5, "Plex-Semibold")
    text(c, W-M-92, H-31, "Technical guide", 8, "Plex", MUTED)
    line(c, M, H-41, W-M, INK, .8)
    text(c, M, H-66, section, 8.5, "Plex-Semibold", BLUE)
    y = text(c, M, H-96, title, 22, "Plex-Semibold", INK, W-2*M, 26)
    if deck: text(c, M, y-23, deck, 10, "Plex", TEXT, W-2*M, 14)
    line(c, M, 34, W-M-18, RULE, .55)
    text(c, W-M-10, 25, str(page), 8, "Plex", MUTED)


def metric(c, x, y, value, label, width=145, color=BLUE):
    text(c, x, y, value, 25, "Plex-Semibold", color)
    line(c, x, y-8, x+width, RULE, .6)
    text(c, x, y-24, label, 8.5, "Plex", TEXT, width, 11)


def bar(c, x, y, width, label, value, maximum, color, value_text=None):
    text(c, x, y+3, label, 8.5, "Plex-Medium", TEXT, 118)
    bx=x+122; bw=width-158
    line(c, bx, y, bx+bw, RULE, 4)
    c.setStrokeColor(color); c.setLineWidth(7); c.line(bx,y,bx+bw*value/maximum,y)
    text(c, x+width-30, y-3, value_text or f"{value:,}", 8.5, "Plex-Semibold")


def screenshot(c, path, x, y, width, height, caption):
    img=ImageReader(str(path)); iw,ih=img.getSize(); scale=min(width/iw,height/ih)
    dw,dh=iw*scale,ih*scale; ox=x+(width-dw)/2; oy=y+(height-dh)/2
    c.setStrokeColor(INK); c.setLineWidth(.6); c.rect(ox,oy,dw,dh,stroke=1,fill=0)
    c.drawImage(img,ox,oy,dw,dh,preserveAspectRatio=True,mask='auto')
    text(c,x,y-13,caption,7.5,"Plex",MUTED,width,10)


def iso_block(c, cx, cy, w, d, h, color=BLUE, label=None):
    # Carbon-colored isometric wireframe: no filled panels.
    top=[(cx,cy+h),(cx+w/2,cy+h+d/2),(cx,cy+h+d),(cx-w/2,cy+h+d/2)]
    bottom=[(cx,cy),(cx+w/2,cy+d/2),(cx,cy+d),(cx-w/2,cy+d/2)]
    c.setStrokeColor(color); c.setLineWidth(1.25)
    for pts in (top,bottom):
        p=c.beginPath(); p.moveTo(*pts[0]); [p.lineTo(*q) for q in pts[1:]]; p.close(); c.drawPath(p,stroke=1,fill=0)
    for a,b in zip(bottom,top): c.line(a[0],a[1],b[0],b[1])
    if label: text(c,cx-w/2,cy-15,label,7.5,"Plex-Medium",TEXT,w)


def iso_flow(c, y):
    xs=[112,306,500]; labels=["Evidence","Decision engine","Seller action"]
    cols=[BLUE,TEAL,PURPLE]
    for x,l,col in zip(xs,labels,cols): iso_block(c,x,y,90,36,55,col,l)
    c.setStrokeColor(MUTED); c.setLineWidth(.8)
    for x1,x2 in ((160,258),(354,452)):
        c.line(x1,y+46,x2,y+46); c.line(x2-7,y+50,x2,y+46); c.line(x2-7,y+42,x2,y+46)


def process_flow(c, x, y, labels, width, palette=None, label_width=86):
    """A compact, semantic Carbon process flow made from numbered nodes and arrows."""
    palette = palette or [BLUE, BLUE, PURPLE, PURPLE]
    count = len(labels)
    step = width / max(1, count - 1)
    for i, label in enumerate(labels):
        cx = x + i * step
        col = palette[i % len(palette)]
        c.setStrokeColor(col); c.setLineWidth(1.4); c.circle(cx, y, 10, stroke=1, fill=0)
        text(c, cx-3, y-3, str(i+1), 7.5, "Plex-Semibold", col)
        text(c, cx-label_width/2, y-29, label, 8, "Plex-Medium", TEXT, label_width, 10)
        if i < count-1:
            nx = x + (i+1)*step
            c.setStrokeColor(MUTED); c.setLineWidth(.8); c.line(cx+13,y,nx-13,y)
            c.line(nx-19,y+4,nx-13,y); c.line(nx-19,y-4,nx-13,y)


def cover_flow(c, x, y, width):
    labels = ["Evidence", "Decision", "Action"]
    cols = [colors.HexColor('#78A9FF'), colors.HexColor('#4589FF'), colors.HexColor('#BE95FF')]
    step = width/2
    for i, (label, col) in enumerate(zip(labels, cols)):
        cx=x+i*step
        c.setStrokeColor(col); c.setLineWidth(1.5); c.circle(cx,y,12,stroke=1,fill=0)
        text(c,cx-3,y-3,str(i+1),8,"Plex-Semibold",col)
        text(c,cx-28,y-30,label,8,"Plex-Medium",colors.HexColor('#C6C6C6'),56)
        if i<2:
            nx=x+(i+1)*step; c.setStrokeColor(colors.HexColor('#6F6F6F')); c.setLineWidth(.8)
            c.line(cx+15,y,nx-15,y); c.line(nx-21,y+4,nx-15,y); c.line(nx-21,y-4,nx-15,y)


def build():
    fonts(); data=json.loads(STATE.read_text()); a=data["accounts"]; total=len(a)
    tiers=Counter(x["tier"] for x in a); buckets=Counter(x["bucket"] for x in a)
    plays=Counter(x["play"] for x in a); industries=Counter(x["industry"] for x in a)
    scores=[x["score"] for x in a]; current=[x for x in a if x["bucket"]=="cadence"]
    cadence=Counter(x["cadence"] for x in current); selected=next(x for x in a if x["name"]=="Vertex Municipal")
    no_dm=sum(not x.get("has_decision_maker") for x in a)
    whitespace=sum(any(t.startswith("Whitespace") for t in x.get("tags",[])) for x in a)
    at_risk=sum("At-risk spend" in x.get("tags",[]) for x in a)

    c=canvas.Canvas(str(OUT),pagesize=letter,pageCompression=1)
    c.setTitle("IBM BobBee Technical Guide"); c.setAuthor("Sydney Chin, Tim Zhou, Patrick McBride")

    # 1 - cover
    c.setFillColor(INK); c.rect(0,0,W,H,fill=1,stroke=0)
    c.setFillColor(BLUE); c.rect(0,0,10,H,fill=1,stroke=0)
    text(c,48,H-52,"IBM BobBee",10,"Plex-Semibold",WHITE)
    text(c,48,H-165,"BobBee",34,"Plex-Semibold",WHITE)
    text(c,48,H-205,"technical guide",34,"Plex-Semibold",WHITE)
    text(c,48,H-238,"Account intelligence and seller execution",12,"Plex",colors.HexColor('#C6C6C6'))
    c.setStrokeColor(BLUE); c.setLineWidth(1.5); c.line(48,H-280,W-48,H-280)
    text(c,48,H-312,"From 1,911 accounts to the next best seller action.",13,"Plex-Medium",WHITE)
    cover_flow(c,365,245,155)
    text(c,48,76,"Developed by",8,"Plex-Semibold",colors.HexColor('#78A9FF'))
    text(c,48,54,"Sydney Chin / Tim Zhou / Patrick McBride",11,"Plex-Medium",WHITE)
    c.showPage()

    # 2
    page_header(c,"Overview","A territory book becomes a finite action system",
                "BobBee turns fragmented account evidence into a ranked, explainable and actionable seller workflow.",2)
    metric(c,M,610,f"{total:,}","accounts normalized into one book",145)
    metric(c,220,610,f"{len(current):,}","accounts active this quarter",145,TEAL)
    metric(c,398,610,f"{no_dm}","withheld for missing decision-maker",145,MAGENTA)
    text(c,M,520,"What the system does",10,"Plex-Semibold")
    rows=[("Unify","Brings IBM position, company context, contacts and signals together."),
          ("Score","Creates an inspectable comparison layer across the territory."),
          ("Route","Assigns quarter, cadence, rank and dated sequence of touches."),
          ("Activate","Presents the next account, supporting evidence and ready action.")]
    yy=486
    for i,(t,d) in enumerate(rows,1):
        text(c,M,yy,f"{i:02d}",8,"Plex-Semibold",BLUE); text(c,82,yy,t,11,"Plex-Semibold")
        text(c,178,yy,d,9,"Plex",TEXT,350,12); line(c,82,yy-13,W-M,RULE,.5); yy-=51
    text(c,M,249,"Design principle",8,"Plex-Semibold",BLUE)
    text(c,M,222,"Rank first. Explain always. Generate only where language adds value.",16,"Plex-Medium",INK,W-2*M,21)
    text(c,M,151,"Guide flow",9,"Plex-Semibold")
    process_flow(c,84,112,["Seller problem","System design","Account intelligence","Seller action"],430,[INK,BLUE,BLUE,PURPLE],92)
    c.showPage()

    # 3
    page_header(c,"Seller problem","Prioritization is the first problem",
                "A seller owns roughly 1,900 accounts across several systems. The scarce resource is attention, not data.",3)
    metric(c,M,608,"~1,900","accounts in a Select Territory book",145)
    metric(c,220,608,"3","source systems reconciled by hand",145,PURPLE)
    metric(c,398,608,"~4 hrs","daily triage and drafting",145,MAGENTA)
    text(c,M,514,"Common failure modes",10,"Plex-Semibold")
    problems=[("Fragmented context","Spend, installs, contacts and activity are separated."),
              ("Uneven prioritization","The loudest account can displace the strongest evidence."),
              ("Planning consumes selling time","The morning is spent assembling context before action."),
              ("Unclear provenance","Facts and generated suggestions can look identical.")]
    yy=476
    for i,(t,d) in enumerate(problems,1):
        text(c,M,yy,f"{i:02d}",8,"Plex-Semibold",BLUE); text(c,82,yy,t,11,"Plex-Semibold")
        text(c,350,yy,d,8.5,"Plex",TEXT,190,11); line(c,82,yy-14,W-M); yy-=54
    text(c,M,224,"BobBee response",8,"Plex-Semibold",BLUE)
    text(c,M,194,"Convert the book into an ordered plan of work, then keep the evidence beside every decision.",16,"Plex-Medium",INK,W-2*M,21)
    iso_flow(c,85)
    c.showPage()

    # 4
    page_header(c,"System design","One intelligence chain, three responsibilities",
                "Carbon blue marks deterministic application logic; purple identifies model-generated language.",4)
    iso_flow(c,560)
    groups=[("Evidence",BLUE,["Territory and coverage","IBM spend and trend","Install base","Company scale","Decision-makers","Recent signals"]),
            ("Decision engine",TEAL,["Eligibility gate","Weighted score","Tier assignment","Quarter segmentation","Cadence match","Within-cadence rank"]),
            ("Seller experience",PURPLE,["Priority account book","Recommended play","Daily schedule","Account detail","Pre-call brief","Ask BobBee"])]
    xs=[M,218,394]
    for x,(title,col,items) in zip(xs,groups):
        text(c,x,480,title,9,"Plex-Semibold",col); line(c,x,468,x+150,col,1.2)
        yy=440
        for i,item in enumerate(items,1):
            text(c,x,yy,f"{i:02d}",7.5,"Plex-Semibold",MUTED); text(c,x+27,yy,item,9,"Plex-Medium")
            line(c,x+27,yy-10,x+150,RULE,.45); yy-=40
    text(c,M,174,"Control points",9,"Plex-Semibold")
    text(c,M,149,"No decision-maker: hold the account. No model response: use a deterministic fallback. No hidden ranking step.",10,"Plex-Medium",INK,W-2*M,14)
    c.showPage()

    # 5
    page_header(c,"Account intelligence","Evidence becomes a comparable account profile",
                "The intelligence layer normalizes commercial position, company context, momentum and activation readiness.",5)
    families=[("IBM position","Relationship, current and prior spend, spend trend and installed products."),
              ("Company context","Revenue, employee scale, industry and territory."),
              ("Engagement","Known contacts and verified IT decision-maker availability."),
              ("Momentum","Dated expansion, funding, leadership, security and risk signals."),
              ("Whitespace","Missing cloud, power, storage and software footprint."),
              ("Competitive posture","Incumbent technology and displacement opportunity.")]
    yy=622
    for i,(t,d) in enumerate(families,1):
        text(c,M,yy,f"{i:02d}",8,"Plex-Semibold",BLUE); text(c,82,yy,t,12,"Plex-Semibold")
        text(c,230,yy,d,9,"Plex",TEXT,310,12); line(c,82,yy-15,W-M); yy-=68
    text(c,M,194,"Resulting decision flow",9,"Plex-Semibold")
    process_flow(c,76,142,["Score and tier","Urgency and play","Cadence and rank","Scheduled touches"],456,[BLUE,BLUE,PURPLE,PURPLE],92)
    c.showPage()

    # 6
    page_header(c,"Portfolio shape","The active quarter is deliberately narrow",
                "Capacity is focused without discarding future value. Every account remains visible in a named bucket.",6)
    maxb=max(buckets.values()); yy=606
    colorset={"cadence":BLUE,"future":CYAN,"leftovers":PURPLE,"no_contacts":MAGENTA}
    labels={"cadence":"Current cadences","future":"Future quarters","leftovers":"Leftovers","no_contacts":"No contacts"}
    for k in ("cadence","future","leftovers","no_contacts"):
        bar(c,M,yy,500,labels[k],buckets[k],maxb,colorset[k]); yy-=43
    text(c,M,418,"Priority tiers",9,"Plex-Semibold")
    maxt=max(tiers.values()); yy=386
    for i,col in zip((1,2,3),(BLUE,TEAL,MUTED)):
        bar(c,M,yy,500,f"Tier {i}",tiers[i],maxt,col); yy-=43
    text(c,M,232,"Portfolio readout",9,"Plex-Semibold",BLUE)
    text(c,M,206,f"{buckets['cadence']/total:.1%} of the book enters live cadences this quarter. {buckets['future']/total:.1%} is preserved for later timing.",13,"Plex-Medium",INK,W-2*M,18)
    metric(c,M,126,f"{whitespace:,}","accounts with whitespace",145)
    metric(c,220,126,f"{at_risk:,}","accounts with at-risk spend",145,MAGENTA)
    metric(c,398,126,f"{len(current):,}","accounts activated now",145,TEAL)
    c.showPage()

    # 7
    page_header(c,"Scoring","The score is a lens, not an oracle",
                "Tiering creates a stable comparison before eligibility, timing, cadence fit and capacity complete the decision.",7)
    bins=[(0,25),(25,35),(35,45),(45,55),(55,65),(65,75),(75,101)]
    counts=[]
    for lo,hi in bins: counts.append((f"{lo}-{hi-1}",sum(lo<=s<hi for s in scores)))
    maximum=max(v for _,v in counts); yy=600
    for i,(label,v) in enumerate(counts):
        bar(c,M,yy,500,label,v,maximum,[MUTED,CYAN,BLUE,BLUE,TEAL,PURPLE,MAGENTA][i]); yy-=39
    metric(c,M,278,f"{median(scores):.1f}","median account score",145)
    metric(c,220,278,f"{max(scores):.1f}","highest account score",145,PURPLE)
    text(c,M,208,"How the score becomes work",9,"Plex-Semibold")
    process_flow(c,78,164,["Score","Eligibility","Quarter timing","Cadence capacity","Seller review"],452,[BLUE,INK,BLUE,PURPLE,INK],74)
    c.showPage()

    # 8
    page_header(c,"Application view","The prioritized account book keeps evidence at the point of choice",
                "Search, signal filters and named buckets keep the whole territory inspectable.",8)
    screenshot(c,SCREENS/"02-account-book.png",M,210,W-2*M,390,"Figure 1. Live BobBee account book after scoring and cadence assignment.")
    text(c,M,154,"What to notice",9,"Plex-Semibold",BLUE)
    text(c,M,129,"The seller can move from portfolio segment to account evidence without leaving the working surface.",11,"Plex-Medium",INK,W-2*M,16)
    c.showPage()

    # 9
    page_header(c,"Application view","An account explanation, not just a score",
                "The detail view joins recommendation, IBM context, company facts, contacts, cadence and recent signals.",9)
    screenshot(c,SCREENS/"03-account-detail.png",M,188,W-2*M,414,"Figure 2. Live account-detail view for Vertex Municipal.")
    text(c,M,133,"Provenance at a glance",9,"Plex-Semibold",PURPLE)
    text(c,M,108,"Deterministic facts remain visually distinct from the generated sales angle and pre-call guidance.",11,"Plex-Medium",INK,W-2*M,16)
    c.showPage()

    # 10
    page_header(c,"Account deep dive",selected["name"],f"{selected['industry']} / {selected['location']} / {selected['relationship']}",10)
    rev=f"${selected['revenue']/1e9:.1f}B" if selected['revenue']>=1e9 else f"${selected['revenue']/1e6:.1f}M"
    metric(c,M,600,f"{selected['score']:.1f}",f"score / tier {selected['tier']}",125)
    metric(c,195,600,rev,"annual revenue",125,TEAL)
    metric(c,390,600,f"#{selected['rank']}","rank in cadence",125,PURPLE)
    text(c,M,512,"Recommended play",9,"Plex-Semibold",BLUE)
    text(c,M,484,selected['play'],18,"Plex-Semibold")
    text(c,M,450,selected['angle'],11,"Plex-Medium",INK,W-2*M,16)
    text(c,M,382,"Why this account",9,"Plex-Semibold")
    reasons=[f"{selected['spend_trend']} IBM spend trend",f"{selected['contact_count']} known contacts and a decision-maker",
             f"{len(selected['signals'])} recent account signals",f"Assigned to {selected['cadence']}"]
    yy=350
    for i,r in enumerate(reasons,1):
        text(c,M,yy,f"{i:02d}",8,"Plex-Semibold",BLUE); text(c,82,yy,r,10,"Plex-Medium"); line(c,82,yy-12,W-M); yy-=45
    text(c,M,152,"Latest signals",9,"Plex-Semibold")
    yy=126
    for s in selected['signals'][:2]:
        text(c,M,yy,s['type'].replace('_',' ').title(),8.5,"Plex-Semibold",MAGENTA)
        text(c,165,yy,s['summary'],8,"Plex",TEXT,380,11); yy-=34
    c.showPage()

    # 11
    page_header(c,"Portfolio opportunities","Repeatable plays emerge across the book",
                "Play assignment turns individual evidence into a portfolio that leaders can inspect and rebalance.",11)
    text(c,M,628,"Recommended plays",9,"Plex-Semibold")
    maximum=max(plays.values()); yy=594
    for i,(name,v) in enumerate(plays.most_common()):
        bar(c,M,yy,500,name,v,maximum,[BLUE,CYAN,TEAL,PURPLE,MAGENTA,MUTED][i%6]); yy-=39
    text(c,M,326,"Largest industry books",9,"Plex-Semibold")
    maximum=max(industries.values()); yy=292
    for i,(name,v) in enumerate(industries.most_common(6)):
        bar(c,M,yy,500,name,v,maximum,[BLUE,CYAN,TEAL,PURPLE,MAGENTA,BLUE][i]); yy-=39
    text(c,M,61,"Portfolio views reveal where coverage, capacity and sales plays are out of balance.",9,"Plex-Medium",TEXT)
    c.showPage()

    # 12
    page_header(c,"Activation","Capacity becomes a visible design choice",
                "Each active cadence is capped, ranked and distributed. Overflow is retained rather than silently dropped.",12)
    maximum=max(cadence.values()); yy=600
    for i,(name,v) in enumerate(cadence.items()):
        bar(c,M,yy,500,name.replace(" Cadence",""),v,maximum,[BLUE,CYAN,TEAL,PURPLE][i]); yy-=47
    metric(c,M,384,f"{sum(cadence.values()):,}","scheduled in current-quarter cadences",150)
    metric(c,220,384,f"{buckets['leftovers']:,}","capacity overflow retained",150,PURPLE)
    metric(c,398,384,f"{buckets['no_contacts']:,}","held until a contact is found",150,MAGENTA)
    text(c,M,290,"Operational contract",9,"Plex-Semibold",BLUE)
    text(c,M,260,"Every activated account has a play, cadence, rank and dated sequence of touches.",16,"Plex-Medium",INK,W-2*M,21)
    process_flow(c,82,158,["Matched play","Cadence rank","Start date","Email and call steps"],440,[BLUE,BLUE,PURPLE,PURPLE],90)
    c.showPage()

    # 13
    page_header(c,"Seller workflow","Intelligence resolves into today's work",
                "The dashboard compresses the system into a morning brief, today's emails and calls, and optional review analytics.",13)
    screenshot(c,SCREENS/"01-dashboard.png",M,202,W-2*M,400,"Figure 3. Live BobBee dashboard after the territory book is activated.")
    text(c,M,147,"Experience principle",9,"Plex-Semibold",BLUE)
    text(c,M,121,"Action comes before analytics. Deeper detail is available, but it does not compete with the next step.",11,"Plex-Medium",INK,W-2*M,16)
    c.showPage()

    # 14
    page_header(c,"Trust and governance","Deterministic where it must be; generative where it helps",
                "Model-generated language stays downstream from ranking, cadence assignment and scheduling.",14)
    rows=[("Account eligibility","Deterministic","Decision-maker gate"),("Score and tier","Deterministic","Weighted application logic"),
          ("Quarter and cadence","Deterministic","Timing, fit and capacity"),("Email draft","Deterministic","Contextual templates"),
          ("Sales angle","watsonx.ai","Granite with deterministic fallback"),("Pre-call brief","watsonx.ai","Granite with deterministic fallback")]
    text(c,M,612,"Capability",8,"Plex-Semibold",MUTED); text(c,240,612,"Source",8,"Plex-Semibold",MUTED); text(c,370,612,"Control",8,"Plex-Semibold",MUTED)
    line(c,M,598,W-M,INK,.8); yy=570
    for cap,src,ctrl in rows:
        text(c,M,yy,cap,10,"Plex-Medium"); text(c,240,yy,src,9.5,"Plex-Semibold",PURPLE if src.startswith('watsonx') else BLUE)
        text(c,370,yy,ctrl,9,"Plex",TEXT,175,12); line(c,M,yy-15,W-M); yy-=56
    screenshot(c,SCREENS/"04-methodology.png",M,72,W-2*M,155,"Figure 4. Methodology remains available inside BobBee.")
    c.showPage()

    # 15
    page_header(c,"Production path","Access turns the demo into a connected seller workflow",
                "The demo proves the workflow with local substitutes. Production value depends on approved APIs, identities and data contracts.",15)
    text(c,M,620,"Access required",9,"Plex-Semibold",BLUE)
    rows=[("watsonx.ai","Project, service credentials and approved model","Grounded summaries, briefs and drafts"),
          ("Email and calendar","Delegated OAuth and application approval","Draft, schedule and send with user consent"),
          ("Slack","Approved app, scopes and workspace installation","Seller alerts and collaboration context"),
          ("CRM / Salesloft","API credentials and record-level permissions","Cadences, activity and outcome write-back"),
          ("ISC / install base","Data-owner approval and supported interface","IBM position, footprint and whitespace"),
          ("Case Viewer","Data-owner approval and supported interface","Relevant case context alongside the account"),
          ("CID","Data-owner approval and supported interface","Additional internal client intelligence")]
    text(c,M,594,"System",8,"Plex-Semibold",MUTED); text(c,160,594,"Production prerequisite",8,"Plex-Semibold",MUTED); text(c,390,594,"Value unlocked",8,"Plex-Semibold",MUTED)
    line(c,M,582,W-M,INK,.8); yy=555
    for system,access,value in rows:
        text(c,M,yy,system,8.7,"Plex-Semibold",INK,108,11)
        text(c,160,yy,access,8.2,"Plex",TEXT,210,10.5)
        text(c,390,yy,value,8.2,"Plex",TEXT,165,10.5)
        line(c,M,yy-21,W-M,RULE,.45); yy-=48
    text(c,M,194,"Deliberate demo boundary",9,"Plex-Semibold",PURPLE)
    text(c,M,166,"More enterprise software could strengthen BobBee, but each additional system adds access review, security scope and integration work. The challenge build keeps those dependencies local so the core seller workflow is easy to evaluate.",10,"Plex-Medium",INK,W-2*M,14)
    text(c,M,93,"Next action",8,"Plex-Semibold",BLUE)
    text(c,M,70,"Confirm system owners, supported APIs, least-privilege scopes, data retention and approval paths before replacing any demo adapter.",8.5,"Plex",TEXT,W-2*M,11)
    c.showPage()

    # 16
    page_header(c,"Deployment","Scale access in controlled stages",
                "Start with the developers, validate with a small seller cohort, then harden the service for organization-wide use.",16)
    stages=[
        ("01","Developer use now",BLUE,"3-5 builders","Run the containerized app in a protected development environment. Use synthetic or explicitly approved test data and one shared nonproduction AI project.",
         "Gate: stable workflow, evaluation set and no secrets in source control."),
        ("02","Small pilot",TEAL,"10-50 sellers","Deploy a managed staging service with corporate SSO, role and territory controls, PostgreSQL, audit logs and read-only integrations first.",
         "Gate: security review, support owner, quality targets and measured adoption."),
        ("03","Organization scale",PURPLE,"Broad workforce","Run redundant containers on the enterprise platform, isolate environments, centralize secrets, monitor cost and quality, and add approved write actions gradually.",
         "Gate: production SLOs, disaster recovery, governance and accountable business ownership.")]
    yy=610
    for num,title,col,scope,body,gate in stages:
        text(c,M,yy,num,9,"Plex-Semibold",col)
        text(c,82,yy,title,14,"Plex-Semibold",INK)
        text(c,430,yy,scope,8.5,"Plex-Semibold",col,120,11)
        line(c,82,yy-13,W-M,col,1.1)
        text(c,82,yy-43,body,9.5,"Plex",TEXT,458,13)
        text(c,82,yy-100,gate,8.5,"Plex-Semibold",INK,458,12)
        yy-=172
    text(c,M,104,"Target production shape",9,"Plex-Semibold",BLUE)
    process_flow(c,82,66,["Corporate SSO","BobBee service","Approved data APIs","AI gateway"],440,[INK,BLUE,TEAL,PURPLE],90)
    c.showPage()

    # 17
    page_header(c,"AI strategy","Choose the model through policy, evidence and cost",
                "Keep BobBee provider-neutral. Ranking and scheduling remain deterministic; models generate language and tool requests behind explicit controls.",17)
    options=[
        ("Preferred","watsonx.ai + Granite 4 H Small",PURPLE,"Best fit when IBM approval and project access are available. Enterprise-oriented RAG and tool use, IBM deployment alignment, governance and model choice through a gateway."),
        ("Free prototype","Gemini API free tier",BLUE,"Useful for developer experiments and small demonstrations. Rate limits apply, and free-tier content may be used to improve Google products; do not send confidential client or internal data."),
        ("Paid alternative","Claude API",TEAL,"Strong drafting and reasoning option, but Claude.ai subscriptions do not include application API usage. Treat it as a paid provider and evaluate it against the same test set."),
        ("No API bill","Self-hosted Granite",INK,"Open-weight deployment through Ollama or vLLM can remove per-token API charges. Hardware, operations, patching, security and availability still carry real cost.")]
    yy=610
    for label,name,col,desc in options:
        text(c,M,yy,label.upper(),7.5,"Plex-Semibold",col)
        text(c,142,yy,name,12,"Plex-Semibold",INK)
        text(c,142,yy-28,desc,9,"Plex",TEXT,400,12.5)
        line(c,M,yy-82,W-M,RULE,.55); yy-=118
    text(c,M,132,"Decision rule",9,"Plex-Semibold",BLUE)
    text(c,M,105,"Use watsonx when approved. Use a free provider only for nonconfidential prototyping. Keep a deterministic fallback and a provider adapter so model changes do not rewrite the product.",11,"Plex-Medium",INK,W-2*M,15)
    text(c,M,55,"References: IBM Granite and watsonx.ai model documentation; Google Gemini API pricing; Anthropic API billing guidance. Access, terms and pricing should be rechecked before deployment.",7.5,"Plex",MUTED,W-2*M,10)
    c.showPage()

    # 18
    page_header(c,"Impact and roadmap","Reclaimed capacity creates room for better seller judgment",
                "The near-term path secures access, validates a pilot and strengthens grounding without weakening the provenance model.",18)
    metric(c,M,606,"~3.25 hrs","reclaimed per seller, every day",150)
    metric(c,220,606,"~16 hrs","reclaimed per seller, every week",150,PURPLE)
    text(c,M,516,"Where the time moves",9,"Plex-Semibold")
    text(c,M,489,"From cross-system research and first-draft creation to account review, client judgment and direct engagement.",12,"Plex-Medium",INK,W-2*M,17)
    text(c,M,410,"Roadmap",9,"Plex-Semibold",BLUE)
    roadmap=[("Next","Access and approval","Secure watsonx and application API access; confirm owners for ISC, Case Viewer and CID."),
             ("Pilot","Connected workflow","Launch read-only integrations with a small seller cohort and measure quality, trust and time saved."),
             ("Scale","Governed action","Add approved write actions, proactive plays and organization-wide operations.")]
    yy=374
    for stage,title,desc in roadmap:
        text(c,M,yy,stage,8,"Plex-Semibold",PURPLE); text(c,96,yy,title,11,"Plex-Semibold")
        text(c,260,yy,desc,9,"Plex",TEXT,285,12); line(c,96,yy-14,W-M); yy-=59
    text(c,M,174,"Built with",9,"Plex-Semibold")
    text(c,M,149,"watsonx.ai / Granite / watsonx Assistant / Flask / Python / IBM Carbon / IBM Plex",9,"Plex-Medium",TEXT,W-2*M,13)
    text(c,M,97,"Developed by Sydney Chin, Tim Zhou, and Patrick McBride",10,"Plex-Semibold")
    text(c,M,72,"Source note: the demo uses deterministic synthetic account data and local representations of external systems.",8,"Plex",MUTED,W-2*M,11)
    c.save()
    FINAL_OUT.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(OUT, FINAL_OUT)
    print(FINAL_OUT)


if __name__ == "__main__": build()
