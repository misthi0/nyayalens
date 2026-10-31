from io import BytesIO
from xml.sax.saxutils import escape as esc

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

INK, SEAL, BRASS = colors.HexColor("#16254a"), colors.HexColor("#a3234b"), colors.HexColor("#f3e3a8")
RISK_COL = {3: "#a3234b", 2: "#a67c1f", 1: "#2f6b4f"}


def _banner(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(INK)
    canvas.rect(0, A4[1] - 14 * mm, A4[0], 14 * mm, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Times-Bold", 12)
    canvas.drawString(18 * mm, A4[1] - 9 * mm, "NyayaLens  |  Legal Document Analysis Report")
    canvas.setFillColor(colors.grey)
    canvas.setFont("Times-Roman", 8)
    canvas.drawString(18 * mm, 10 * mm, "Machine-generated summary. Not legal advice. Keep this report private.")
    canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f"Page {doc.page}")
    canvas.restoreState()


def build_pdf(r: dict) -> bytes:
    ss = getSampleStyleSheet()
    body = ParagraphStyle("b", parent=ss["Normal"], fontName="Times-Roman", fontSize=10.5, leading=15, textColor=INK)
    h1 = ParagraphStyle("h1", parent=body, fontName="Times-Bold", fontSize=22, leading=26, spaceAfter=6)
    h2 = ParagraphStyle("h2", parent=body, fontName="Times-Bold", fontSize=14, textColor=SEAL, spaceBefore=14, spaceAfter=6)
    small = ParagraphStyle("s", parent=body, fontSize=9, textColor=colors.HexColor("#56627f"))
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=24 * mm, bottomMargin=18 * mm,
                            title=f"NyayaLens - {r['doc_type']}")
    s = [Paragraph(esc(r["doc_type"]), h1),
         Paragraph(f"File: {esc(r['filename'])} &nbsp;|&nbsp; Confidence: {r['confidence']}% &nbsp;|&nbsp; "
                   f"Words read: {r['word_count']} &nbsp;|&nbsp; {esc(r['generated_at'])}", small)]
    if r["risk"]["level"] != "n/a":
        s.append(Paragraph(f"Risk level: <b>{r['risk']['level']}</b> ({r['risk']['score']}/100)", body))
    c = r.get("id_card")
    if c:
        rows = [(k, v) for k, v in [(f"{c['kind']} number", c["number"] or "Not detected"), ("Name", c["name"]), ("Father's name", c["father"]),
                                    ("Date of birth", c["dob"]), ("Gender", c["gender"]), ("VID", c["vid"])] if v]
        t = Table([[Paragraph(esc(k), body), Paragraph("<b>" + esc(v) + "</b>", body)] for k, v in rows], colWidths=[50 * mm, 120 * mm])
        t.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 1, SEAL), ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f6f8f1")),
                               ("LINEBELOW", (0, 0), (-1, -2), 0.3, colors.HexColor("#b9c6b0")), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
        s += [Paragraph("ID details", h2), t]
    s += [Paragraph("Summary", h2), Paragraph(esc(r["summary"]), body), Paragraph("Important words", h2),
          Paragraph("&nbsp; ".join(f'<font backColor="#f3e3a8">&nbsp;{esc(k["term"])}&nbsp;</font>' for k in r["keywords"]) or "None found", body)]
    s.append(Paragraph("Extracted details", h2))
    if r["entities"]:
        rows = [["Type", "Value"]] + [[Paragraph(esc(e["type"]), body), Paragraph(esc(e["value"]), body)] for e in r["entities"]]
        t = Table(rows, colWidths=[55 * mm, 115 * mm], repeatRows=1)
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), INK), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                               ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                               ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f4ec")]),
                               ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#b9c6b0"))]))
        s.append(t)
    else:
        s.append(Paragraph("No details found.", body))
    if r["clauses"]:
        s.append(Paragraph("Important clauses", h2))
        for c in r["clauses"]:
            col = RISK_COL.get(c["risk"], "#2f6b4f")
            s += [Paragraph(f'<font color="{col}"><b>{esc(c["name"])}</b></font> - {esc(c["explanation"])}', body),
                  Paragraph(f'"{esc(c["snippet"])}"', small), Spacer(1, 4)]
    s.append(Paragraph("Things to check", h2))
    s += [Paragraph("- " + esc(f), body) for f in (r["flags"] or ["Nothing risky detected."])]
    doc.build(s, onFirstPage=_banner, onLaterPages=_banner)
    return buf.getvalue()
