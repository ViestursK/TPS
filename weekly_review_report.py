#!/usr/bin/env python3
"""
Weekly Trustpilot Report - PDF Generator
Generates a professional PDF report from Trustpilot review data
"""
import json
import datetime
from statistics import mean

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie


# =============================
# COLORS
# =============================
PRIMARY = HexColor("#1f3a5f")
ACCENT = HexColor("#00b67a")
DANGER = HexColor("#ff5b57")
WARNING = HexColor("#f59e0b")
GREY = HexColor("#6b7280")
BG_LIGHT = HexColor("#f5f7fa")


# =============================
# DATE HELPERS
# =============================
def parse_date(s):
    """Parse ISO format date string"""
    if not s:
        return None
    return datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))


def week_range():
    """Get the date range for the past week"""
    end = datetime.datetime.now(datetime.timezone.utc)
    start = end - datetime.timedelta(days=7)
    return start, end


def filter_week(reviews, start, end):
    """Filter reviews that fall within the given date range"""
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
    """Calculate sentiment distribution"""
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
    """Analyze review data for the past week"""
    start, end = week_range()
    current = filter_week(reviews, start, end)

    avg = mean([r["rating"] for r in current]) if current else 0

    return {
        "count": len(current),
        "avg": avg,
        "sentiment": sentiment(current),
        "range": (start, end),
        "reviews": current
    }


# =============================
# STYLES
# =============================
def build_styles():
    """Create custom paragraph styles"""
    s = getSampleStyleSheet()

    s.add(ParagraphStyle(
        "RptTitle",
        fontSize=24,
        textColor=PRIMARY,
        alignment=TA_CENTER,
        spaceAfter=8,
        fontName="Helvetica-Bold"
    ))

    s.add(ParagraphStyle(
        "RptSubtitle",
        fontSize=16,
        textColor=GREY,
        alignment=TA_CENTER,
        spaceAfter=4,
        fontName="Helvetica"
    ))

    s.add(ParagraphStyle(
        "RptHeader",
        fontSize=16,
        textColor=PRIMARY,
        fontName="Helvetica-Bold",
        spaceBefore=20,
        spaceAfter=12
    ))

    s.add(ParagraphStyle(
        "RptSmall",
        fontSize=10,
        textColor=GREY,
        alignment=TA_CENTER
    ))

    s.add(ParagraphStyle(
        "RptBody",
        fontSize=11,
        textColor=black,
        spaceAfter=6
    ))

    return s


# =============================
# CHARTS
# =============================
def sentiment_pie_chart(sent):
    """Create a pie chart for sentiment distribution"""
    d = Drawing(400, 200)
    
    pc = Pie()
    pc.x = 100
    pc.y = 20
    pc.width = 200
    pc.height = 200
    
    # Data
    total = sent["positive"] + sent["neutral"] + sent["negative"]
    if total > 0:
        pc.data = [sent["positive"], sent["neutral"], sent["negative"]]
        pc.labels = [
            f'Positive ({sent["positive"]})',
            f'Neutral ({sent["neutral"]})',
            f'Negative ({sent["negative"]})'
        ]
    else:
        pc.data = [1]
        pc.labels = ['No data']
    
    # Colors
    pc.slices[0].fillColor = ACCENT
    pc.slices[1].fillColor = WARNING
    if len(pc.slices) > 2:
        pc.slices[2].fillColor = DANGER
    
    # Style
    pc.slices.strokeWidth = 1
    pc.slices.strokeColor = white
    
    d.add(pc)
    return d


def rating_bar_chart(analysis):
    """Create a bar chart showing rating distribution"""
    d = Drawing(400, 200)
    
    # Count ratings
    rating_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for review in analysis["reviews"]:
        rating = review["rating"]
        if rating in rating_counts:
            rating_counts[rating] += 1
    
    chart = VerticalBarChart()
    chart.x = 40
    chart.y = 30
    chart.width = 320
    chart.height = 150
    
    chart.data = [[rating_counts[i] for i in range(1, 6)]]
    chart.categoryAxis.categoryNames = ['1★', '2★', '3★', '4★', '5★']
    
    chart.bars[0].fillColor = ACCENT
    chart.valueAxis.valueMin = 0
    chart.valueAxis.valueMax = max(rating_counts.values()) + 1 if rating_counts.values() else 5
    
    d.add(chart)
    return d

# =============================
# FOOTER
# =============================
def footer(canvas, doc):
    """Add footer to each page"""
    canvas.saveState()
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(GREY)
    
    # Page number
    canvas.drawRightString(
        A4[0] - 2*cm,
        1.5*cm,
        f"Page {doc.page}"
    )
    
    # Generation timestamp
    canvas.drawString(
        2*cm,
        1.5*cm,
        f"Generated: {datetime.datetime.now():%Y-%m-%d %H:%M}"
    )
    
    canvas.restoreState()


# =============================
# PDF GENERATION
# =============================
def generate_pdf(data, output):
    """Generate the complete PDF report"""
    s = build_styles()
    analysis = analyze(data["reviews"])
    company = data["company"]

    doc = SimpleDocTemplate(
        output,
        pagesize=A4,
        leftMargin=2*cm,
        rightMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=3*cm
    )

    story = []

    # ===== COVER PAGE =====
    # story.append(Spacer(1, 1*cm))
    
    story.append(Paragraph(
        company["brand_name"],
        s["RptTitle"]
    ))
    
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph(
        "Weekly Trustpilot Report",
        s["RptSubtitle"]
    ))

    ws, we = analysis["range"]
    story.append(Spacer(1, 0.1*cm))
    story.append(Paragraph(
        f"{ws:%B %d, %Y} – {we:%B %d, %Y}",
        s["RptSmall"]
    ))

    # story.append(Spacer(1, 1*cm))
    
    # ===== AI SUMMARY =====
    if company.get("ai_summary"):
        story.append(Spacer(1, 1*cm))
        story.append(Paragraph("AI-Generated Insights", s["RptHeader"]))
        
        summary_text = company["ai_summary"]["summary"]
        # Split into paragraphs
        for para in summary_text.split("\n\n"):
            if para.strip():
                story.append(Paragraph(para.strip(), s["RptBody"]))
                story.append(Spacer(1, 0.3*cm))

    story.append(Spacer(1, 1*cm))

    # Summary box
    summary_data = [
        ["Trust Score", f"{company['trust_score']}/5"],
        ["Total Reviews", f"{company['total_reviews']:,}"],
        ["New This Week", f"{analysis['count']}"],
        ["Average Rating", f"{analysis['avg']:.2f}/5"]
    ]
    
    summary_table = Table(summary_data, colWidths=[8*cm, 8*cm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
        ('TEXTCOLOR', (0, 0), (-1, -1), PRIMARY),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, white)
    ]))
    
    story.append(summary_table)
    story.append(PageBreak())

    # ===== DETAILED ANALYSIS =====
    story.append(Paragraph("Sentiment Analysis", s["RptHeader"]))
    
    sent = analysis["sentiment"]
    total = sent["positive"] + sent["neutral"] + sent["negative"]
    
    if total > 0:
        story.append(Paragraph(
            f"<b>Positive:</b> {sent['positive']} ({sent['positive']/total*100:.1f}%)",
            s["RptBody"]
        ))
        story.append(Paragraph(
            f"<b>Neutral:</b> {sent['neutral']} ({sent['neutral']/total*100:.1f}%)",
            s["RptBody"]
        ))
        story.append(Paragraph(
            f"<b>Negative:</b> {sent['negative']} ({sent['negative']/total*100:.1f}%)",
            s["RptBody"]
        ))
    else:
        story.append(Paragraph("No reviews this week", s["RptBody"]))

    story.append(Spacer(1, 0.5*cm))
    story.append(sentiment_pie_chart(sent))

    # ===== RATING DISTRIBUTION =====
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph("Rating Distribution", s["RptHeader"]))
    story.append(rating_bar_chart(analysis))


    # ===== BUILD PDF =====
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(f"\n[✓] PDF generated successfully: {output}")
    print(f"    Reviews analyzed: {analysis['count']}")
    print(f"    Average rating: {analysis['avg']:.2f}/5")


# =============================
# MAIN
# =============================
def main():
    """Main entry point"""
    import sys
    
    input_file = "trustpilot_raw_data.json"
    output_file = "weekly_review_report.pdf"
    
    # Allow command line arguments
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    
    print("\n" + "="*70)
    print("TRUSTPILOT WEEKLY REPORT - PDF GENERATOR")
    print("="*70)
    print(f"\nInput:  {input_file}")
    print(f"Output: {output_file}\n")
    
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        generate_pdf(data, output_file)
        
        print("\n" + "="*70)
        print("PDF GENERATION COMPLETE")
        print("="*70 + "\n")
        
    except FileNotFoundError:
        print(f"\n[!] Error: File '{input_file}' not found")
        print("    Make sure you run mvp.py first to generate the data file")
        sys.exit(1)
    except Exception as e:
        print(f"\n[!] Error generating PDF: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()