#!/usr/bin/env python3
"""Narrative BobBee guide: manual workflow, system logic, then product screens."""

from collections import Counter
import json

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from generate_bobbee_print_guide import (
    ROOT, STATE, SCREENS, W, H, M, INK, TEXT, MUTED, RULE, BLUE, CYAN, TEAL,
    PURPLE, MAGENTA, WHITE, fonts, text, line, page_header, metric, bar, screenshot,
)
from generate_bobbee_concise_guide import manual_process, intelligence_flow, arrow

OUT = ROOT / "BobBee_Pitch.pdf"
LOGO = ROOT / "bobbee/static/logo.png"


def cover(c):
    c.setFillColor(INK); c.rect(0,0,W,H,fill=1,stroke=0); c.setFillColor(BLUE); c.rect(0,0,10,H,fill=1,stroke=0)
    text(c,48,H-52,"IBM BobBee",10,"Plex-Semibold",WHITE)
    text(c,48,H-172,"From manual research",31,"Plex-Semibold",WHITE)
    text(c,48,H-210,"to account intelligence",31,"Plex-Semibold",WHITE)
    text(c,48,H-246,"A technical walkthrough of the seller workflow",12,"Plex",colors.HexColor('#C6C6C6'))
    c.setStrokeColor(BLUE); c.setLineWidth(1.4); c.line(48,H-288,W-48,H-288)
    labels=["Manual process","Problem","BobBee overview","Intelligence","Seller workflow"]
    xs=[68,184,300,416,532]; y=342
    for i,(x,label) in enumerate(zip(xs,labels),1):
        col=colors.HexColor('#78A9FF') if i<4 else colors.HexColor('#BE95FF')
        c.setStrokeColor(col); c.circle(x,y,10,stroke=1,fill=0); text(c,x-3,y-3,str(i),7,"Plex-Semibold",col)
        text(c,x-40,y-28,label,7.5,"Plex-Medium",colors.HexColor('#C6C6C6'),80,9)
        if i<5: arrow(c,x+13,y,xs[i]-13,y,colors.HexColor('#6F6F6F'))
    text(c,48,76,"Developed by",8,"Plex-Semibold",colors.HexColor('#78A9FF'))
    text(c,48,54,"Sydney Chin / Tim Zhou / Patrick McBride",11,"Plex-Medium",WHITE)
    c.showPage()


def problem_page(c, total):
    page_header(c,"Problem statement","The seller has data, but not a connected decision process",
                "Install context, contacts, outreach, meetings and opportunity history must be assembled repeatedly for every account.",3)
    metric(c,58,610,f"{total:,}","accounts in the territory book",145)
    metric(c,226,610,"4+","research and engagement systems",145,BLUE)
    metric(c,394,610,"Daily","manual reconciliation cycle",145,PURPLE)
    text(c,58,508,"The central problem",9,"Plex-Semibold",BLUE)
    text(c,58,478,"The seller must turn fragmented evidence into four decisions:",16,"Plex-Medium",INK,496,21)
    decisions=[("Priority","Which accounts matter now?"),("Message","What does the installed environment imply?"),
               ("Person","Who is closest to the machine and decision?"),("Action","What should happen next, and when?")]
    yy=410
    for i,(title,detail) in enumerate(decisions,1):
        text(c,58,yy,f"{i:02d}",8,"Plex-Semibold",BLUE); text(c,94,yy,title,11,"Plex-Semibold")
        text(c,205,yy,detail,10,"Plex",TEXT,345,13); line(c,94,yy-14,550); yy-=58
    text(c,58,154,"Why the current process does not scale",9,"Plex-Semibold",PURPLE)
    text(c,58,126,"Research is fragmented, personalization is repetitive, and continuity depends on individual organization across tools.",12,"Plex-Medium",INK,496,17)
    c.showPage()


def overview_page(c):
    page_header(c,"BobBee overview","How BobBee works, in one picture",
                "Private account evidence and public momentum signals become an ordered, explainable seller workflow.",4)
    # Inputs: line-led blocks, no colored fills.
    text(c,58,606,"Private signals",13,"Plex-Semibold")
    line(c,58,593,220,BLUE,2)
    text(c,58,568,"IBM Sales Cloud and install base",9,"Plex-Medium",TEXT)
    text(c,58,548,"Spend and relationship history",9,"Plex",TEXT)
    text(c,58,528,"Known contacts and decision-makers",9,"Plex",TEXT)
    text(c,58,454,"Public signals",13,"Plex-Semibold")
    line(c,58,441,220,PURPLE,2)
    text(c,58,416,"Company news and funding",9,"Plex-Medium",TEXT)
    text(c,58,396,"Leadership and expansion events",9,"Plex",TEXT)
    text(c,58,376,"Competitive moves and risk signals",9,"Plex",TEXT)
    text(c,128,490,"+",18,"Plex-Semibold",MUTED)
    arrow(c,228,488,270,488,RULE,1)
    # Engine center.
    c.setStrokeColor(INK); c.setLineWidth(.9); c.rect(276,362,158,252,stroke=1,fill=0)
    logo=ImageReader(str(LOGO)); c.drawImage(logo,329,526,52,52,preserveAspectRatio=True,mask='auto')
    text(c,318,494,"BobBee",20,"Plex-Semibold")
    text(c,298,458,"Scores every account",10,"Plex-Medium",INK,114,14)
    text(c,298,428,"Routes accounts into cadences",9,"Plex",TEXT,114,13)
    text(c,298,392,"Schedules the next touch",9,"Plex",TEXT,114,13)
    arrow(c,442,488,474,488,RULE,1)
    # Outputs.
    outputs=[("Ranked daily plan","who to work, in order"),("Drafted emails","context ready to review"),
             ("Pre-call briefs","what to know before dialing"),("Morning brief","the day in one paragraph")]
    yy=568
    for title,detail in outputs:
        text(c,474,yy,"✓",12,"Plex-Semibold",BLUE)
        text(c,492,yy,title,10,"Plex-Semibold"); text(c,492,yy-17,detail,8.5,"Plex",TEXT,82,11); yy-=70
    text(c,58,270,"One operating principle",9,"Plex-Semibold",BLUE)
    text(c,58,240,"The deterministic engine decides priority and timing. Generative assistance adds language after the decision is made.",13,"Plex-Medium",INK,496,18)
    c.showPage()


def smarter_page(c, accounts):
    page_header(c,"Why it is smarter","Account intelligence separates comparison from decision gates",
                "A score alone does not determine the day. Eligibility, timing, capacity and seller review remain explicit.",6)
    families=[("IBM position","Spend, prior spend, trend and installed products"),("Whitespace","Missing cloud, power, storage and software footprint"),
              ("Company scale","Revenue, employees and industry"),("Engagement","Contacts and decision-maker availability"),
              ("Momentum","Funding, expansion, leadership and risk signals"),("Competitive posture","Incumbent platform and displacement opportunity")]
    yy=610
    for i,(title,detail) in enumerate(families,1):
        text(c,58,yy,f"{i:02d}",8,"Plex-Semibold",BLUE); text(c,94,yy,title,11,"Plex-Semibold")
        text(c,248,yy,detail,9,"Plex",TEXT,302,12); line(c,94,yy-14,550); yy-=56
    text(c,58,252,"Decision sequence",9,"Plex-Semibold")
    stages=[("Score","comparison"),("Contact","eligibility"),("Quarter","timing"),("Cadence","capacity"),("Seller","review")]
    xs=[78,187,296,405,514]; y=205
    for i,(x,(title,detail)) in enumerate(zip(xs,stages),1):
        col=BLUE if i<4 else PURPLE
        c.setStrokeColor(col); c.circle(x,y,10,stroke=1,fill=0); text(c,x-3,y-3,str(i),7.5,"Plex-Semibold",col)
        text(c,x-34,y-29,title,8.5,"Plex-Semibold",INK,68); text(c,x-34,y-43,detail,7.5,"Plex",TEXT,68,9)
        if i<5: arrow(c,x+13,y,xs[i]-13,y)
    text(c,58,115,"Result",8,"Plex-Semibold",PURPLE)
    text(c,105,115,"Each activated account has a reason, play, cadence, rank and dated sequence of touches.",10,"Plex-Medium",INK,445,14)
    c.showPage()


def screen_page(c, page, section, title, deck, filename, caption, role):
    page_header(c,section,title,deck,page)
    screenshot(c,SCREENS/filename,58,200,496,414,caption)
    text(c,58,145,"Role in the workflow",9,"Plex-Semibold",BLUE)
    text(c,58,118,role,11,"Plex-Medium",INK,496,16)
    c.showPage()


def governance_page(c, page):
    page_header(c,"Governance","Deterministic decisions, bounded generative assistance",
                "Model-generated language remains downstream from prioritization and scheduling.",page)
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
    c.showPage()


def build():
    fonts(); state=json.loads(STATE.read_text()); accounts=state["accounts"]
    c=canvas.Canvas(str(OUT),pagesize=letter,pageCompression=1)
    c.setTitle("IBM BobBee Seller Workflow and Account Intelligence")
    c.setAuthor("Sydney Chin, Tim Zhou, Patrick McBride")
    cover(c)
    page_header(c,"Current state","The manual seller process","Install analysis, contact research, outreach, meetings and opportunity progression form one continuous loop.",2)
    manual_process(c); c.showPage()
    problem_page(c,len(accounts))
    overview_page(c)
    page_header(c,"System logic","How account intelligence works","The engine applies explicit gates, comparisons and capacity rules before work reaches the seller.",5)
    intelligence_flow(c); c.showPage()
    smarter_page(c,accounts)
    screen_page(c,7,"Product workflow","Dashboard: start with today's work","The morning brief and ranked work queues compress the system into a clear starting point.","01-dashboard.png","Figure 1. BobBee dashboard.","Shows the seller what changed, which accounts to work, and the next email or call.")
    screen_page(c,8,"Product workflow","Accounts: inspect the territory book","Named buckets and signal filters keep every account visible for a defined reason.","02-account-book.png","Figure 2. BobBee account book.","Moves from portfolio state to account evidence without leaving the working surface.")
    screen_page(c,9,"Product workflow","Account detail: explain one decision","Commercial context, contacts, signals, recommendation and cadence position are joined in one view.","03-account-detail.png","Figure 3. BobBee account detail.","Explains why the account is active and gives the seller the context needed to act.")
    screen_page(c,10,"Product workflow","Cadences: manage outreach sequences","Accounts are grouped into explicit plays with visible activity and progress.","06-cadences.png","Figure 4. BobBee cadence view.","Makes sequence purpose, account volume and current progress inspectable.")
    screen_page(c,11,"Product workflow","Schedule: distribute the quarter","Cadence steps become a daily load of emails and calls across the quarter.","05-schedule.png","Figure 5. BobBee schedule.","Turns ranked accounts into a manageable calendar of dated touches.")
    screen_page(c,12,"Product workflow","Email: review personalized outreach","The day's scheduled contacts are organized by account, role, cadence and step.","07-email.png","Figure 6. BobBee email workspace.","Provides a controlled review point before personalized outreach is sent.")
    screen_page(c,13,"Product workflow","Call: prepare before dialing","Contacts and pre-call context sit beside the day's ordered call list.","08-call.png","Figure 7. BobBee call workspace.","Brings decision-maker details and account context into the call workflow.")
    governance_page(c,14)
    c.save(); print(OUT)


if __name__ == "__main__": build()
