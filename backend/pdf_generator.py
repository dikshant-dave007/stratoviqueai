"""
backend/pdf_generator.py
Enterprise-grade ReportLab PDF for StratoviqueAI Marketing Strategy Reports.
"""

import re, io
from datetime import datetime

from reportlab.lib               import colors
from reportlab.lib.pagesizes     import A4
from reportlab.lib.styles        import ParagraphStyle
from reportlab.lib.units         import mm, cm
from reportlab.lib.enums         import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus          import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether, Preformatted
)

from backend.config import get_logger

logger = get_logger(__name__)

# ── Palette ───────────────────────────────────────────────────────────────────
GOLD       = colors.HexColor("#C9A84C")
GOLD_LIGHT = colors.HexColor("#FDF6E3")
DARK       = colors.HexColor("#12121A")
DARK_MID   = colors.HexColor("#1E1E28")
SLATE      = colors.HexColor("#4A4A5A")
MID_GREY   = colors.HexColor("#7A7A8A")
LIGHT_GREY = colors.HexColor("#F5F5F8")
RULE_CLR   = colors.HexColor("#E0E0E8")
WHITE      = colors.white
INK        = colors.HexColor("#1A1A24")
BODY_INK   = colors.HexColor("#2E2E3E")
GREEN      = colors.HexColor("#2D7A4F")
GREEN_LIGHT= colors.HexColor("#EAF5EF")

PAGE_W, PAGE_H = A4
ML = 2.4*cm; MR = 2.4*cm; MT = 2.8*cm; MB = 2.2*cm


# ── Style registry ────────────────────────────────────────────────────────────
def _styles():
    def S(n,**k): return ParagraphStyle(n,**k)
    return {
        "h1": S("h1", fontName="Helvetica-Bold", fontSize=22, textColor=INK,
                leading=28, spaceBefore=26, spaceAfter=6),
        "h2": S("h2", fontName="Helvetica-Bold", fontSize=15, textColor=INK,
                leading=20, spaceBefore=22, spaceAfter=6),
        "h3": S("h3", fontName="Helvetica-Bold", fontSize=11.5, textColor=SLATE,
                leading=16, spaceBefore=14, spaceAfter=4),
        "h4": S("h4", fontName="Helvetica-Bold", fontSize=10.5, textColor=INK,
                leading=15, spaceBefore=10, spaceAfter=3),
        "body": S("body", fontName="Helvetica", fontSize=10, textColor=BODY_INK,
                  leading=16, spaceAfter=5, alignment=TA_JUSTIFY),
        "bullet": S("bullet", fontName="Helvetica", fontSize=10, textColor=BODY_INK,
                    leading=15, spaceAfter=3, leftIndent=18, bulletIndent=6),
        "sub_bullet": S("sub_bullet", fontName="Helvetica", fontSize=9.5,
                        textColor=MID_GREY, leading=14, spaceAfter=2,
                        leftIndent=34, bulletIndent=22),
        "numbered": S("numbered", fontName="Helvetica", fontSize=10, textColor=BODY_INK,
                      leading=15, spaceAfter=3, leftIndent=20, bulletIndent=6),
        "code_block": S("code_block", fontName="Courier", fontSize=8.5,
                        textColor=colors.HexColor("#2D2D3D"), leading=13),
        "blockquote": S("blockquote", fontName="Helvetica-Oblique", fontSize=10,
                        textColor=SLATE, leading=16, spaceAfter=6,
                        leftIndent=18, rightIndent=10),
        "th": S("th", fontName="Helvetica-Bold", fontSize=8.5, textColor=WHITE,
                leading=12, alignment=TA_LEFT),
        "td": S("td", fontName="Helvetica", fontSize=9, textColor=INK,
                leading=13, alignment=TA_LEFT),
        "section_label": S("section_label", fontName="Helvetica-Bold", fontSize=7.5,
                           textColor=GOLD, leading=11, spaceBefore=0, spaceAfter=2),
        "meta_label": S("meta_label", fontName="Helvetica-Bold", fontSize=8.5,
                        textColor=MID_GREY, leading=13),
        "meta_val": S("meta_val", fontName="Helvetica", fontSize=10,
                      textColor=INK, leading=15),
        "insight": S("insight", fontName="Helvetica", fontSize=10, textColor=INK,
                     leading=16, spaceAfter=4, leftIndent=14),
    }


# ── Inline markdown ───────────────────────────────────────────────────────────
def _esc(t):
    return str(t).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def _inline(t):
    t = _esc(t)
    t = re.sub(r'\*\*\*(.+?)\*\*\*', r'<b><i>\1</i></b>', t)
    t = re.sub(r'\*\*(.+?)\*\*',     r'<b>\1</b>',        t)
    t = re.sub(r'\*(.+?)\*',         r'<i>\1</i>',        t)
    t = re.sub(r'(?<![\w])_([^_]+)_(?![\w])', r'<i>\1</i>', t)
    t = re.sub(r'`(.+?)`',
               r'<font name="Courier" size="9" color="#C9A84C">\1</font>', t)
    return t


# ── Pipe table → ReportLab Table ──────────────────────────────────────────────
def _md_table(lines, ST):
    rows = []
    for ln in lines:
        s = ln.strip()
        if re.match(r'^\|[-:| ]+\|$', s):
            continue
        cells = [c.strip() for c in s.strip('|').split('|')]
        rows.append(cells)
    if not rows: return None

    cols = max(len(r) for r in rows)
    rows = [r + ['']*(cols-len(r)) for r in rows]
    uw   = PAGE_W - ML - MR

    # Smart column widths: first col narrower if it looks like a label col
    if cols >= 2 and len(rows[0][0]) < 20:
        first_w = min(3.5*cm, uw * 0.28)
        rest_w  = (uw - first_w) / (cols - 1)
        cws     = [first_w] + [rest_w]*(cols-1)
    else:
        cws = [uw/cols]*cols

    data = []
    for i, row in enumerate(rows):
        st = ST["th"] if i == 0 else ST["td"]
        data.append([Paragraph(_inline(c), st) for c in row])

    ts = TableStyle([
        ('BACKGROUND',     (0,0), (-1,0),  DARK),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, LIGHT_GREY]),
        ('GRID',           (0,0), (-1,-1), 0.35, RULE_CLR),
        ('TOPPADDING',     (0,0), (-1,-1), 7),
        ('BOTTOMPADDING',  (0,0), (-1,-1), 7),
        ('LEFTPADDING',    (0,0), (-1,-1), 9),
        ('RIGHTPADDING',   (0,0), (-1,-1), 9),
        ('VALIGN',         (0,0), (-1,-1), 'TOP'),
        ('LINEBELOW',      (0,0), (-1,0),  1.5, GOLD),
    ])
    tbl = Table(data, colWidths=cws, repeatRows=1)
    tbl.setStyle(ts)
    return tbl


# ── Markdown → flowables ──────────────────────────────────────────────────────
def _md_flowables(md: str, ST: dict) -> list:
    if not md: return []
    fl    = []
    lines = md.split('\n')
    i     = 0

    while i < len(lines):
        raw = lines[i]
        s   = raw.strip()

        if not s:
            fl.append(Spacer(1, 3)); i += 1; continue

        # HR
        if re.match(r'^[-*_]{3,}\s*$', s):
            fl.append(HRFlowable(width="100%", thickness=0.5,
                                 color=RULE_CLR, spaceBefore=4, spaceAfter=4))
            i += 1; continue

        # H1
        if s.startswith('# ') and not s.startswith('## '):
            text = s[2:].strip()
            fl.append(Spacer(1, 8))
            fl.append(Paragraph(text.upper(), ST["section_label"]))
            fl.append(Paragraph(_inline(text), ST["h1"]))
            fl.append(HRFlowable(width="100%", thickness=2,
                                 color=GOLD, spaceAfter=10))
            i += 1; continue

        # H2
        if s.startswith('## ') and not s.startswith('### '):
            fl.append(Paragraph(_inline(s[3:]), ST["h2"]))
            fl.append(HRFlowable(width="100%", thickness=0.6,
                                 color=RULE_CLR, spaceAfter=6))
            i += 1; continue

        # H3
        if s.startswith('### ') and not s.startswith('#### '):
            fl.append(Paragraph(_inline(s[4:]), ST["h3"]))
            i += 1; continue

        # H4
        if s.startswith('#### '):
            fl.append(Paragraph(_inline(s[5:]), ST["h4"]))
            i += 1; continue

        # Blockquote
        if s.startswith('> '):
            fl.append(Paragraph(_inline(s[2:]), ST["blockquote"]))
            i += 1; continue

        # Pipe table
        if s.startswith('|') and s.endswith('|') and '|' in s[1:-1]:
            tbl_lines = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                tbl_lines.append(lines[i]); i += 1
            tbl = _md_table(tbl_lines, ST)
            if tbl:
                fl.append(Spacer(1, 6))
                fl.append(tbl)
                fl.append(Spacer(1, 8))
            continue

        # Code block
        if s.startswith('```'):
            i += 1
            code_lines = []
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i]); i += 1
            i += 1
            uw = PAGE_W - ML - MR
            code_tbl = Table(
                [[Preformatted(_esc('\n'.join(code_lines)), ST["code_block"])]],
                colWidths=[uw])
            code_tbl.setStyle(TableStyle([
                ('BACKGROUND',    (0,0),(-1,-1), colors.HexColor("#F0F0F5")),
                ('LEFTPADDING',   (0,0),(-1,-1), 12),
                ('RIGHTPADDING',  (0,0),(-1,-1), 12),
                ('TOPPADDING',    (0,0),(-1,-1), 10),
                ('BOTTOMPADDING', (0,0),(-1,-1), 10),
                ('BOX',           (0,0),(-1,-1), 0.5, RULE_CLR),
                ('LINEBEFORE',    (0,0),(0,-1),  3,   GOLD),
            ]))
            fl.append(Spacer(1, 4))
            fl.append(code_tbl)
            fl.append(Spacer(1, 6))
            continue

        # Sub-bullet
        if re.match(r'^  [-*+] ', raw):
            fl.append(Paragraph(
                f'<bullet color="#AAAAAA">◦</bullet>{_inline(raw.strip()[2:])}',
                ST["sub_bullet"]))
            i += 1; continue

        # Bullet
        if re.match(r'^[-*+] ', s):
            fl.append(Paragraph(
                f'<bullet color="#C9A84C">•</bullet>{_inline(s[2:])}',
                ST["bullet"]))
            i += 1; continue

        # Numbered list
        m = re.match(r'^(\d+)\. (.+)$', s)
        if m:
            fl.append(Paragraph(
                f'<bullet><b>{m.group(1)}.</b></bullet>{_inline(m.group(2))}',
                ST["numbered"]))
            i += 1; continue

        # Body paragraph
        fl.append(Paragraph(_inline(s), ST["body"]))
        i += 1

    return fl


# ── Page header / footer ──────────────────────────────────────────────────────
def _page_callbacks(company_name: str, session_id: str):
    def first(c, doc): pass

    def later(c, doc):
        w, h = c._pagesize
        # Top bar
        c.setFillColor(DARK)
        c.rect(0, h-13*mm, w, 13*mm, fill=1, stroke=0)
        c.setFillColor(GOLD)
        c.setFont("Helvetica-Bold", 8.5)
        c.drawString(ML, h-8.5*mm, "StratoviqueAI")
        c.setFillColor(colors.HexColor("#AAAAAA"))
        c.setFont("Helvetica", 7.5)
        c.drawRightString(w-MR, h-8.5*mm,
                          f"{company_name} — Marketing Strategy Report")
        # Bottom
        c.setStrokeColor(RULE_CLR)
        c.setLineWidth(0.4)
        c.line(ML, 13*mm, w-MR, 13*mm)
        c.setFillColor(MID_GREY)
        c.setFont("Helvetica", 7.5)
        c.drawCentredString(w/2, 8.5*mm, f"Page {doc.page}")
        c.drawString(ML, 8.5*mm, f"Session: {session_id[:8]}")
        c.drawRightString(w-MR, 8.5*mm,
                          datetime.now().strftime("%d %b %Y"))

    return first, later


# ── Cover page ────────────────────────────────────────────────────────────────
def _cover(state: dict, ST: dict) -> list:
    fl  = []
    uw  = PAGE_W - ML - MR
    co  = state.get("company_name", "Unknown")
    ind = state.get("industry",     "—")
    bud = state.get("budget",       "—")
    goa = state.get("goals",        "—")
    aud = state.get("target_audience", "—")
    sid = state.get("session_id",   "")

    # ── Masthead ──────────────────────────────────────────────────
    mast_data = [[
        Paragraph(f'<font color="white"><b>{_esc(co)}</b></font>',
                  ParagraphStyle("_mh", fontName="Helvetica-Bold", fontSize=30,
                                 textColor=WHITE, leading=36)),
        Paragraph('<font color="#C9A84C">CONFIDENTIAL</font>',
                  ParagraphStyle("_cf", fontName="Helvetica-Bold", fontSize=8,
                                 textColor=GOLD, alignment=TA_RIGHT, leading=12)),
    ]]
    mast = Table(mast_data, colWidths=[uw*0.72, uw*0.28])
    mast.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), DARK),
        ('TOPPADDING',    (0,0),(-1,-1), 26),
        ('BOTTOMPADDING', (0,0),(-1,-1), 26),
        ('LEFTPADDING',   (0,0),(-1,-1), 22),
        ('RIGHTPADDING',  (0,0),(-1,-1), 22),
        ('VALIGN',        (0,0),(-1,-1), 'BOTTOM'),
    ]))
    fl.append(mast)

    # Gold rule + dark sub-band
    fl.append(HRFlowable(width="100%", thickness=4, color=GOLD, spaceAfter=0))
    sub_data = [[Paragraph(
        '<font color="#AAAAAA">AI Multi-Agent Marketing Strategy Engine</font>',
        ParagraphStyle("_sb", fontName="Helvetica", fontSize=11,
                       textColor=MID_GREY, leading=17))]]
    sub = Table(sub_data, colWidths=[uw])
    sub.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), DARK_MID),
        ('TOPPADDING',    (0,0),(-1,-1), 12),
        ('BOTTOMPADDING', (0,0),(-1,-1), 12),
        ('LEFTPADDING',   (0,0),(-1,-1), 22),
    ]))
    fl.append(sub)
    fl.append(Spacer(1, 22))

    # Document type heading
    fl.append(Paragraph("Marketing Strategy Report",
                        ParagraphStyle("_dt", fontName="Helvetica-Bold", fontSize=18,
                                       textColor=INK, leading=24, spaceAfter=6)))
    fl.append(Paragraph("Prepared by StratoviqueAI · 6-Agent Intelligence Pipeline",
                        ParagraphStyle("_ds", fontName="Helvetica", fontSize=11,
                                       textColor=SLATE, leading=17, spaceAfter=22)))
    fl.append(HRFlowable(width="100%", thickness=0.5, color=RULE_CLR, spaceAfter=18))

    # Metadata table
    meta = [
        ["COMPANY",         co],
        ["INDUSTRY",        ind],
        ["TARGET AUDIENCE", aud],
        ["MONTHLY BUDGET",  bud],
        ["PRIMARY GOAL",    goa],
        ["GENERATED ON",    datetime.now().strftime("%d %B %Y, %H:%M")],
        ["SESSION ID",      sid[:16] + "…" if len(sid) > 16 else sid],
    ]
    meta_data = [[Paragraph(k, ST["meta_label"]),
                  Paragraph(_esc(v), ST["meta_val"])] for k,v in meta]
    meta_tbl  = Table(meta_data, colWidths=[3.8*cm, uw-3.8*cm])
    meta_tbl.setStyle(TableStyle([
        ('ROWBACKGROUNDS', (0,0),(-1,-1), [WHITE, LIGHT_GREY]),
        ('TOPPADDING',     (0,0),(-1,-1), 8),
        ('BOTTOMPADDING',  (0,0),(-1,-1), 8),
        ('LEFTPADDING',    (0,0),(-1,-1), 10),
        ('RIGHTPADDING',   (0,0),(-1,-1), 10),
        ('GRID',           (0,0),(-1,-1), 0.3, RULE_CLR),
        ('LINEAFTER',      (0,0),(0,-1),  1.5, GOLD),
    ]))
    fl.append(meta_tbl)
    fl.append(Spacer(1, 26))

    # Disclaimer
    fl.append(HRFlowable(width="100%", thickness=0.4, color=RULE_CLR, spaceAfter=10))
    fl.append(Paragraph(
        "This report was generated by StratoviqueAI's multi-agent AI pipeline. "
        "All strategic recommendations should be reviewed by a qualified marketing "
        "professional before implementation. Market data is based on AI-synthesised "
        "research and should be independently verified for critical decisions.",
        ParagraphStyle("_disc", fontName="Helvetica-Oblique", fontSize=8.5,
                       textColor=MID_GREY, leading=13)))
    fl.append(PageBreak())
    return fl


# ── Table of contents ─────────────────────────────────────────────────────────
def _toc(sections: list, ST: dict) -> list:
    fl  = []
    uw  = PAGE_W - ML - MR
    fl.append(Paragraph("TABLE OF CONTENTS", ST["section_label"]))
    fl.append(Spacer(1, 4))
    fl.append(HRFlowable(width="100%", thickness=2, color=GOLD, spaceAfter=14))

    num_s = ParagraphStyle("_tn", fontName="Helvetica-Bold", fontSize=9,
                           textColor=GOLD, leading=13)
    ttl_s = ParagraphStyle("_tt", fontName="Helvetica", fontSize=10,
                           textColor=INK, leading=13)

    for num, title in sections:
        row = Table([[Paragraph(num, num_s), Paragraph(title, ttl_s)]],
                    colWidths=[1.0*cm, uw-1.0*cm])
        row.setStyle(TableStyle([
            ('TOPPADDING',    (0,0),(-1,-1), 6),
            ('BOTTOMPADDING', (0,0),(-1,-1), 6),
            ('LEFTPADDING',   (0,0),(-1,-1), 6),
            ('LINEBELOW',     (0,0),(-1,-1), 0.3, RULE_CLR),
        ]))
        fl.append(row)

    fl.append(PageBreak())
    return fl


# ── Section divider band ──────────────────────────────────────────────────────
def _divider(num: str, title: str) -> list:
    uw = PAGE_W - ML - MR
    num_s  = ParagraphStyle("_dn", fontName="Helvetica-Bold", fontSize=9,
                            textColor=GOLD, leading=13)
    ttl_s  = ParagraphStyle("_dt", fontName="Helvetica-Bold", fontSize=13,
                            textColor=WHITE, leading=18)
    data = [[Paragraph(num, num_s), Paragraph(title, ttl_s)]]
    tbl  = Table(data, colWidths=[1.4*cm, uw-1.4*cm])
    tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), DARK_MID),
        ('TOPPADDING',    (0,0),(-1,-1), 11),
        ('BOTTOMPADDING', (0,0),(-1,-1), 11),
        ('LEFTPADDING',   (0,0),(-1,-1), 14),
        ('LINEBELOW',     (0,0),(-1,-1), 2.5, GOLD),
    ]))
    return [Spacer(1, 14), tbl, Spacer(1, 10)]


# ── Insight highlight box ─────────────────────────────────────────────────────
def _highlight_box(text: str, ST: dict) -> list:
    """Gold-accented callout box for key insights."""
    uw   = PAGE_W - ML - MR
    s    = ParagraphStyle("_hb", fontName="Helvetica", fontSize=10,
                          textColor=INK, leading=16)
    data = [[Paragraph(_inline(text), s)]]
    tbl  = Table(data, colWidths=[uw])
    tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), GOLD_LIGHT),
        ('TOPPADDING',    (0,0),(-1,-1), 12),
        ('BOTTOMPADDING', (0,0),(-1,-1), 12),
        ('LEFTPADDING',   (0,0),(-1,-1), 16),
        ('RIGHTPADDING',  (0,0),(-1,-1), 14),
        ('LINEBEFORE',    (0,0),(0,-1),  4, GOLD),
    ]))
    return [tbl, Spacer(1, 8)]


# ── Main entry point ──────────────────────────────────────────────────────────
def generate_pdf(state: dict) -> bytes:
    """
    Generate enterprise-grade strategy PDF from MarketingState dict.
    Returns raw PDF bytes.
    """
    company_name = state.get("company_name", "Strategy Report")
    session_id   = state.get("session_id", "")
    
    logger.info(f"[Session {session_id}] Starting PDF generation for {company_name}")
    
    try:
        buf = io.BytesIO()
        ST  = _styles()

        on1, on      = _page_callbacks(company_name, session_id)

        logger.debug(f"[Session {session_id}] Creating PDF document structure")
        doc = SimpleDocTemplate(
            buf, pagesize=A4,
            leftMargin=ML, rightMargin=MR,
            topMargin=MT+10*mm, bottomMargin=MB+8*mm,
            title   = f"{company_name} — Marketing Strategy Report",
            author  = "StratoviqueAI",
            subject = "AI-Generated Marketing Strategy",
        )

        story = []

        # ── Cover ─────────────────────────────────────────────────────
        logger.debug(f"[Session {session_id}] Building PDF cover")
        story += _cover(state, ST)

        # ── Table of Contents ─────────────────────────────────────────
        toc_sections = []
        section_num  = 1

        final_report     = state.get("final_report")
        market_research  = state.get("market_research")
        audience_profile = state.get("audience_profile")
        channel_strategy = state.get("channel_strategy")
        content_strategy = state.get("content_strategy")

        if final_report:
            toc_sections.append((f"0{section_num}", "Executive Strategy Report"))
            section_num += 1
        for _, title, content in [
            ("", "Market Research",   market_research),
            ("", "Audience Profile",  audience_profile),
            ("", "Channel Strategy",  channel_strategy),
            ("", "Content Strategy",  content_strategy),
        ]:
            if content:
                toc_sections.append((f"0{section_num}", title))
                section_num += 1

        logger.debug(f"[Session {session_id}] Building table of contents with {len(toc_sections)} sections")
        story += _toc(toc_sections, ST)

        # ── Final Report (main) ───────────────────────────────────────
        sec = 1
        if final_report:
            logger.debug(f"[Session {session_id}] Adding executive strategy report section")
            story += _divider(f"0{sec}", "Executive Strategy Report")
            story += _md_flowables(final_report, ST)
            story.append(PageBreak())
            sec += 1

        # ── Supporting agent outputs ──────────────────────────────────
        agent_sections = [
            ("Market Research",   market_research),
            ("Audience Profile",  audience_profile),
            ("Channel Strategy",  channel_strategy),
            ("Content Strategy",  content_strategy),
        ]

        for title, content in agent_sections:
            if not content:
                continue
            logger.debug(f"[Session {session_id}] Adding {title} section")
            num = f"0{sec}" if sec < 10 else str(sec)
            story += _divider(num, title)
            story += _md_flowables(content, ST)
            story.append(Spacer(1, 12))
            sec += 1

        # ── Build ─────────────────────────────────────────────────────
        logger.debug(f"[Session {session_id}] Building PDF document with {len(story)} story elements")
        doc.build(story, onFirstPage=on1, onLaterPages=on)
        buf.seek(0)
        pdf_bytes = buf.read()
        
        logger.info(f"[Session {session_id}] PDF generation completed successfully | Size: {len(pdf_bytes)} bytes")
        return pdf_bytes
    
    except Exception as e:
        logger.error(f"[Session {session_id}] PDF generation failed: {str(e)}", exc_info=True)
        raise
