#!/usr/bin/env python3
import json
import datetime
from statistics import mean

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, white
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER

from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import StackedBarChart
from reportlab.graphics.charts.lineplots import LinePlot


# =============================
# COLORS
# =============================
PRIMARY = HexColor("#1f3a5f")
ACCENT = HexColor("#00b67a")
DANGER = HexColor("#ff5b57")
GREY = HexColor("#6b7280")
BG_LIGHT = HexColor("#f5f7fa")


# =============================
# DATE HELPERS
# =============================
def parse_date(s):
    if not s:
        return None
    return datetime.datetime.fromisoformat(s.replace("Z", ""))


def week_range():
    end = datetime.datetime.now(datetime.UTC)
    return end - datetime.timedelta(days=7), end


def filter_week(reviews, start, end):
    out = []
    for r in reviews:
        d = parse_date(r.get("dates", {}).get("publishedDate"))
        if d and start <= d <= end:
            out.append(r)
    return out


# =============================
# ANALYSIS
# =============================
def sentiment(reviews):
    s = dict(positive=0, neutral=0, negative=0)
    for r in reviews:
        if r["rating"] >= 4:
            s["positive"] += 1
        elif r["rating"] == 3:
            s["neutral"] += 1
        else:
            s["negative"] += 1
    return s


def analyze(reviews):
    start, end = week_range()
    current = filter_week(reviews, start, end)

    avg = mean([r["rating"] for r in current]) if current else 0

    return {
        "count": len(current),
        "avg": avg,
        "sentiment": sentiment(current),
        "range": (start, end),
    }


# =============================
# STYLES (SAFE NAMES)
# =============================
def build_styles():
    s = getSampleStyleSheet()

    s.add(ParagraphStyle(
        "RptTitle",
        fontSize=22,
        textColor=PRIMARY,
        alignment=TA_CENTER,
        spaceAfter=6,
        fontName="Helvetica-Bold"
    ))

    s.add(ParagraphStyle(
        "RptHeader",
        fontSize=15,
        textColor=PRIMARY,
        fontName="Helvetica-Bold",
        spaceBefore=16,
        spaceAfter=8
    ))

    s.add(ParagraphStyle(
        "RptSmall",
        fontSize=9,
        textColor=GREY
    ))

    return s


# =============================
# CHARTS
# =============================
def stacked_sentiment_chart(sent):
    d = Drawing(400, 220)

    chart = StackedBarChart()
    chart.x = 40
    chart.y = 30
    chart.width = 320
    chart.height = 150

    chart.data = [
        [sent["positive"]],
        [sent["neutral"]],
        [sent["negative"]],
    ]

    chart.categoryAxis.categoryNames = ["Reviews"]
    chart.valueAxis.visible = True

    chart.bars[0].fillColor = ACCENT
    chart.bars[1].fillColor = GREY
    chart.bars[2].fillColor = DANGER

    chart.barSpacing = 6
    chart.groupSpacing = 0

    d.add(chart)
    return d


def wow_trend_chart(values):
    d = Drawing(400, 160)
    lp = LinePlot()
    lp.x = 40
    lp.y = 30
    lp.height = 100
    lp.width = 300
    lp.data = [list(enumerate(values))]
    lp.lines[0].strokeColor = ACCENT
    lp.lines[0].strokeWidth = 2
    d.add(lp)
    return d


# =============================
# FOOTER
# =============================
def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(GREY)
    canvas.drawRightString(
        A4[0] - 2*cm,
        1.5*cm,
        f"Page {doc.page}"
    )
    canvas.restoreState()


# =============================
# PDF
# =============================
def generate_pdf(data, output):
    s = build_styles()
    analysis = analyze(data["reviews"])

    doc = SimpleDocTemplate(
        output,
        pagesize=A4,
        leftMargin=2*cm,
        rightMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=3*cm
    )

    story = []

    # LOGO HEADER (optional)
    if data["company"].get("logo_path"):
        logo = Image(data["company"]["logo_path"], width=4*cm, height=1.2*cm)
        story.append(logo)
        story.append(Spacer(1, 6))

    story.append(Paragraph(
        data["company"]["brand_name"],
        s["RptTitle"]
    ))

    story.append(Paragraph(
        "Weekly Trustpilot Report",
        s["RptTitle"]
    ))

    ws, we = analysis["range"]
    story.append(Paragraph(
        f"{ws:%B %d, %Y} – {we:%B %d, %Y}",
        s["RptSmall"]
    ))

    story.append(Spacer(1, 1*cm))

    # LINK
    story.append(Paragraph(
        '<link href="https://www.trustpilot.com">View on Trustpilot</link>',
        s["Normal"]
    ))

    story.append(Spacer(1, 0.8*cm))

    # METRICS
    story.append(Paragraph("Key Metrics", s["RptHeader"]))
    story.append(Paragraph(
        f"New reviews: <b>{analysis['count']}</b>",
        s["Normal"]
    ))
    story.append(Paragraph(
        f"Average rating: <b>{analysis['avg']:.2f}/5</b>",
        s["Normal"]
    ))

    story.append(Spacer(1, 0.6*cm))

    # SENTIMENT
    story.append(Paragraph("Sentiment Overview", s["RptHeader"]))
    story.append(stacked_sentiment_chart(analysis["sentiment"]))

    # TREND (placeholder example)
    story.append(Spacer(1, 0.8*cm))
    story.append(Paragraph("Weekly Rating Trend", s["RptHeader"]))
    story.append(wow_trend_chart([3.2, 2.8, 2.1, analysis["avg"]]))

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(f"[✓] PDF generated: {output}")


# =============================
# MAIN
# =============================
def main():
    with open("trustpilot_raw_data.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    generate_pdf(data, "weekly_review_report_enhanced.pdf")


if __name__ == "__main__":
    main()
