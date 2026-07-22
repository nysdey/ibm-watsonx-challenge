#!/usr/bin/env python3
"""Concise, process-led BobBee technical guide."""

from collections import Counter
from pathlib import Path
import json

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from generate_bobbee_print_guide import (
    ROOT, STATE, SCREENS, W, H, M, INK, TEXT, MUTED, RULE, BLUE, CYAN, TEAL,
    PURPLE, MAGENTA, WHITE, fonts, text, line, page_header, metric, bar, screenshot,
)

OUT = ROOT / "BobBee_Pitch.pdf"


def arrow(c, x1, y1, x2, y2, color=MUTED, width=.8):
    c.setStrokeColor(color); c.setLineWidth(width); c.line(x1,y1,x2,y2)
    if abs(x2-x1) >= abs(y2-y1):
        s = 1 if x2>x1 else -1
        c.line(x2-6*s,y2+4,x2,y2); c.line(x2-6*s,y2-4,x2,y2)
    else:
        s = 1 if y2>y1 else -1
        c.line(x2-4,y2-6*s,x2,y2); c.line(x2+4,y2-6*s,x2,y2)


def node(c, x, y, w, title, detail=None, color=INK, number=None):
    c.setStrokeColor(color); c.setLineWidth(1.1); c.line(x,y,x+w,y)
    if number:
        c.circle(x+10,y+15,9,stroke=1,fill=0)
        text(c,x+7,y+12,str(number),7.5,"Plex-Semibold",color)
        tx=x+26
    else: tx=x
    text(c,tx,y+11,title,9.5,"Plex-Semibold",INK,w-(tx-x),12)
    if detail: text(c,x,y-16,detail,7.8,"Plex",TEXT,w,10)


def decision(c, cx, cy, w, h, label, color=BLUE):
    pts=[(cx,cy+h/2),(cx+w/2,cy),(cx,cy-h/2),(cx-w/2,cy)]
    p=c.beginPath(); p.moveTo(*pts[0]); [p.lineTo(*q) for q in pts[1:]]; p.close()
    c.setStrokeColor(color); c.setLineWidth(1.1); c.drawPath(p,stroke=1,fill=0)
    text(c,cx-w*.31,cy-3,label,8,"Plex-Semibold",INK,w*.62)


def manual_process(c):
    # Patrick's workflow, simplified into a single operational loop.
    steps=[
        ("Interpret the install","Machine, software and OS level become category, urgency and message."),
        ("Find the right contacts","Caseviewer, ZoomInfo, Sales Navigator and prior ISC opportunities."),
        ("Personalize outreach","Adapt email, call and LinkedIn templates to the install and account."),
        ("Track every touch","Record who was contacted, when, and where coverage is still blank."),
        ("Prepare the meeting","Review install, company, people and history; form a hypothesis and questions."),
        ("Capture call context","Save transcript, environment details, next steps and coaching notes."),
        ("Progress the opportunity","Update ISC, review territory reports and coordinate with the business partner."),
    ]
    positions=[(58,596),(228,596),(398,596),(398,454),(228,454),(58,454),(228,312)]
    widths=[135,135,135,135,135,135,170]
    for i,((title,detail),(x,y),w) in enumerate(zip(steps,positions,widths),1):
        col=BLUE if i<=3 else PURPLE if i>=6 else INK
        node(c,x,y,w,title,detail,col,i)
    # Snake through the process from research to opportunity progression.
    arrow(c,193,596,218,596); arrow(c,363,596,388,596)
    arrow(c,465,573,465,477); arrow(c,398,454,373,454); arrow(c,228,454,193,454)
    arrow(c,125,431,275,330); arrow(c,313,312,360,312)
    text(c,398,323,"Repeat for every active account",7.5,"Plex-Medium",MUTED,135,10)

    text(c,58,245,"Manual friction",9,"Plex-Semibold",PURPLE)
    pains=[
        ("Research is fragmented","Install detail, contacts, company context and prior opportunities live in different tools."),
        ("Personalization is repetitive","Each install category needs relevant messaging, then account-level adjustment."),
        ("Continuity is fragile","Touches, meeting context, next steps and partner updates must stay synchronized by hand."),
    ]
    yy=211
    for i,(t,d) in enumerate(pains,1):
        text(c,58,yy,f"{i:02d}",8,"Plex-Semibold",PURPLE); text(c,92,yy,t,9.5,"Plex-Semibold")
        text(c,220,yy,d,8.3,"Plex",TEXT,330,11); line(c,92,yy-12,550); yy-=48


def intelligence_flow(c):
    # Main path and explicit exits. This mirrors the actual application stages.
    top=[("Unify evidence","ISC, ZoomInfo, Salesloft, installs and signals"),("Check contact","Require an IT decision-maker"),
         ("Score and tier","Compare spend, trend, whitespace, scale and momentum")]
    xs=[58,228,398]
    for i,((t,d),x) in enumerate(zip(top,xs),1): node(c,x,610,135,t,d,BLUE,i)
    arrow(c,193,610,218,610); arrow(c,363,610,388,610)
    decision(c,465,500,108,54,"Contact found?")
    arrow(c,465,587,465,528)
    node(c,58,482,135,"Hold: no contacts","Visible set-aside bucket",PURPLE)
    arrow(c,411,500,203,500); text(c,300,506,"No",7.5,"Plex-Semibold",MUTED)
    node(c,398,410,135,"Assign quarter","Route by signal timing",BLUE,4)
    arrow(c,465,473,465,428); text(c,474,451,"Yes",7.5,"Plex-Semibold",MUTED)
    decision(c,465,326,108,54,"Current quarter?")
    arrow(c,465,392,465,354)
    node(c,58,308,135,"Retain: future quarter","Account stays visible",PURPLE)
    arrow(c,411,326,203,326); text(c,300,332,"No",7.5,"Plex-Semibold",MUTED)
    node(c,398,236,135,"Match cadence","Choose play, then rank",BLUE,5)
    arrow(c,465,299,465,254); text(c,474,276,"Yes",7.5,"Plex-Semibold",MUTED)
    decision(c,306,154,118,54,"Capacity available?")
    arrow(c,465,218,348,176)
    node(c,58,136,135,"Retain: leftovers","Overflow returns next quarter",PURPLE)
    arrow(c,247,154,203,154); text(c,219,160,"No",7.5,"Plex-Semibold",MUTED)
    node(c,398,136,135,"Schedule touches","Dated emails and calls",PURPLE,6)
    arrow(c,365,154,388,154); text(c,370,160,"Yes",7.5,"Plex-Semibold",MUTED)
    text(c,58,74,"Result",9,"Plex-Semibold",BLUE)
    text(c,105,74,"Every activated account has a score, tier, reason, play, cadence, rank and dated sequence of touches.",9.5,"Plex-Medium",INK,440,13)


def build():
    fonts(); state=json.loads(STATE.read_text()); accounts=state["accounts"]
    total=len(accounts); buckets=Counter(a["bucket"] for a in accounts); tiers=Counter(a["tier"] for a in accounts)
    current=[a for a in accounts if a["bucket"]=="cadence"]
    selected=next(a for a in accounts if a["name"]=="Vertex Municipal")

    c=canvas.Canvas(str(OUT),pagesize=letter,pageCompression=1)
    c.setTitle("IBM BobBee Account Intelligence"); c.setAuthor("Sydney Chin, Tim Zhou, Patrick McBride")

    # 1
    c.setFillColor(INK); c.rect(0,0,W,H,fill=1,stroke=0); c.setFillColor(BLUE); c.rect(0,0,10,H,fill=1,stroke=0)
    text(c,48,H-52,"IBM BobBee",10,"Plex-Semibold",WHITE)
    text(c,48,H-172,"Account intelligence",32,"Plex-Semibold",WHITE)
    text(c,48,H-211,"Technical overview",32,"Plex-Semibold",WHITE)
    text(c,48,H-247,"How a territory book becomes an explainable daily plan",12,"Plex",colors.HexColor('#C6C6C6'))
    c.setStrokeColor(BLUE); c.setLineWidth(1.4); c.line(48,H-290,W-48,H-290)
    # Cover uses the same four-stage flow that structures the document.
    labels=["Manual process","Account intelligence","Account decision","Daily work"]
    xs=[70,222,374,526]; y=350
    for i,(x,label) in enumerate(zip(xs,labels),1):
        col=colors.HexColor('#78A9FF') if i<3 else colors.HexColor('#BE95FF')
        c.setStrokeColor(col); c.circle(x,y,11,stroke=1,fill=0); text(c,x-3,y-3,str(i),7.5,"Plex-Semibold",col)
        text(c,x-43,y-30,label,8,"Plex-Medium",colors.HexColor('#C6C6C6'),86,10)
        if i<4: arrow(c,x+14,y,xs[i]-14,y,colors.HexColor('#6F6F6F'))
    text(c,48,76,"Developed by",8,"Plex-Semibold",colors.HexColor('#78A9FF'))
    text(c,48,54,"Sydney Chin / Tim Zhou / Patrick McBride",11,"Plex-Medium",WHITE)
    c.showPage()

    # 2
    page_header(c,"Current state","The manual seller process", "Install analysis, contact research, outreach, meetings and opportunity progression form one continuous loop.",2)
    manual_process(c); c.showPage()

    # 3
    page_header(c,"System logic","How account intelligence works", "The engine applies explicit gates, comparisons and capacity rules before work reaches the seller.",3)
    intelligence_flow(c); c.showPage()

    # 4
    page_header(c,"Decision model","What is scored, and what is not", "The score supports comparison. Contact eligibility, quarter timing and cadence capacity remain separate decisions.",4)
    families=[("IBM position","Spend, prior spend, trend and installed products"),("Whitespace","Missing cloud, power, storage and software footprint"),
              ("Company scale","Revenue, employees and industry"),("Engagement","Contacts and decision-maker availability"),
              ("Momentum","Dated funding, expansion, leadership and risk signals"),("Competitive posture","Incumbent platform and displacement opportunity")]
    yy=610
    for i,(t,d) in enumerate(families,1):
        text(c,58,yy,f"{i:02d}",8,"Plex-Semibold",BLUE); text(c,94,yy,t,11,"Plex-Semibold")
        text(c,250,yy,d,9,"Plex",TEXT,300,12); line(c,94,yy-15,550); yy-=61
    text(c,58,224,"Decision sequence",9,"Plex-Semibold")
    seq=[("Score","Stable comparison"),("Eligibility","Decision-maker gate"),("Timing","Current quarter"),("Capacity","Cadence space"),("Review","Seller judgment")]
    xs=[78,187,296,405,514]; y=176
    for i,(x,(title,detail)) in enumerate(zip(xs,seq),1):
        col=BLUE if i in (1,3) else PURPLE if i==4 else INK
        c.setStrokeColor(col); c.circle(x,y,10,stroke=1,fill=0); text(c,x-3,y-3,str(i),7.5,"Plex-Semibold",col)
        text(c,x-37,y-29,title,8.5,"Plex-Semibold",INK,74); text(c,x-41,y-43,detail,7,"Plex",TEXT,82,9)
        if i<5: arrow(c,x+13,y,xs[i]-13,y)
    text(c,58,91,"Principle",8,"Plex-Semibold",BLUE)
    text(c,111,91,"No single score silently determines the seller's day.",10,"Plex-Medium")
    c.showPage()

    # 5
    page_header(c,"Portfolio result","A focused quarter, with every account retained", "The output is a named portfolio state rather than a hidden filter.",5)
    maximum=max(buckets.values()); yy=610
    colorset={"cadence":BLUE,"future":CYAN,"leftovers":PURPLE,"no_contacts":MAGENTA}
    labels={"cadence":"Current cadences","future":"Future quarters","leftovers":"Leftovers","no_contacts":"No contacts"}
    for key in ("cadence","future","leftovers","no_contacts"):
        bar(c,58,yy,500,labels[key],buckets[key],maximum,colorset[key]); yy-=52
    text(c,58,378,"Priority tiers",9,"Plex-Semibold")
    maximum=max(tiers.values()); yy=342
    for tier,col in zip((1,2,3),(BLUE,TEAL,MUTED)):
        bar(c,58,yy,500,f"Tier {tier}",tiers[tier],maximum,col); yy-=48
    metric(c,58,178,f"{total:,}","accounts normalized",135)
    metric(c,226,178,f"{len(current):,}","activated this quarter",135,BLUE)
    metric(c,394,178,f"{buckets['no_contacts']:,}","held for missing contacts",135,PURPLE)
    text(c,58,91,"Interpretation",8,"Plex-Semibold",BLUE)
    text(c,126,91,f"{len(current)/total:.1%} of the territory enters active cadences; the remainder stays visible for a defined reason.",9.5,"Plex-Medium",INK,424,13)
    c.showPage()

    # 6
    page_header(c,"Account explanation","The seller can inspect one decision end to end", "Vertex Municipal shows the evidence, recommendation and activation state in one view.",6)
    screenshot(c,SCREENS/"03-account-detail.png",58,274,496,350,"Figure 1. Live account-detail view from BobBee.")
    rev=f"${selected['revenue']/1e9:.1f}B" if selected['revenue']>=1e9 else f"${selected['revenue']/1e6:.1f}M"
    metric(c,58,224,f"{selected['score']:.1f}",f"score / tier {selected['tier']}",125)
    metric(c,210,224,rev,"annual revenue",125,BLUE)
    metric(c,362,224,f"#{selected['rank']}","rank in cadence",125,PURPLE)
    text(c,58,143,"Why it was activated",9,"Plex-Semibold")
    reason=f"{selected['spend_trend']} IBM spend, a verified decision-maker, {len(selected['signals'])} recent signals and available cadence capacity."
    text(c,58,118,reason,10,"Plex-Medium",INK,496,14)
    c.showPage()

    # 7
    page_header(c,"Seller output","Account intelligence resolves into today's work", "The daily surface presents ordered actions; deeper analytics stay secondary.",7)
    screenshot(c,SCREENS/"01-dashboard.png",58,282,496,330,"Figure 2. Live BobBee dashboard after account intelligence is applied.")
    text(c,58,225,"Daily output",9,"Plex-Semibold",BLUE)
    items=[("Morning brief","What changed and where to begin"),("Ranked accounts","Who to work and in what order"),
           ("Email and calls","The next dated touch for each account"),("Account context","Why the account is active now")]
    yy=193
    for i,(t,d) in enumerate(items,1):
        text(c,58,yy,f"{i:02d}",8,"Plex-Semibold",BLUE); text(c,92,yy,t,9.5,"Plex-Semibold")
        text(c,230,yy,d,8.5,"Plex",TEXT,320,11); line(c,92,yy-11,550); yy-=37
    c.showPage()

    # 8
    page_header(c,"Governance","Deterministic decisions, bounded generative assistance", "Model-generated language remains downstream from prioritization and scheduling.",8)
    rows=[("Eligibility, scoring and tiering","Deterministic"),("Quarter, cadence, rank and schedule","Deterministic"),
          ("Email draft","Deterministic template"),("Sales angle","watsonx.ai with fallback"),("Pre-call brief","watsonx.ai with fallback")]
    text(c,58,604,"Capability",8,"Plex-Semibold",MUTED); text(c,350,604,"Source",8,"Plex-Semibold",MUTED); line(c,58,590,550,INK,.8)
    yy=559
    for cap,src in rows:
        text(c,58,yy,cap,10,"Plex-Medium"); text(c,350,yy,src,9.5,"Plex-Semibold",PURPLE if src.startswith("watsonx") else BLUE)
        line(c,58,yy-16,550); yy-=58
    text(c,58,238,"Implementation",9,"Plex-Semibold")
    text(c,58,211,"Flask / Python / deterministic domain layer / watsonx.ai / watsonx Assistant / IBM Carbon / IBM Plex",9,"Plex-Medium",TEXT,496,13)
    text(c,58,151,"Source note",8,"Plex-Semibold",BLUE)
    text(c,58,127,"The demo uses deterministic synthetic account data and local representations of external systems.",8.5,"Plex",TEXT,496,12)
    text(c,58,79,"Developed by Sydney Chin, Tim Zhou, and Patrick McBride",10,"Plex-Semibold")
    c.save(); print(OUT)


if __name__ == "__main__": build()
