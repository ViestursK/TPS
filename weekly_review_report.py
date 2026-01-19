#!/usr/bin/env python3
"""
Weekly Trustpilot Report - PDF Generator
Generates a professional PDF report from Trustpilot review data

This script takes JSON data from Trustpilot scraper and creates a formatted PDF report
with charts, tables, and analysis of the past week's reviews.
"""
import json
import datetime
from statistics import mean
import os
import tempfile

# ReportLab imports for PDF generation
from reportlab.platypus import (
    SimpleDocTemplate,  # Main document template
    Paragraph,          # Text paragraphs with styling
    Spacer,            # Vertical spacing between elements
    Table,             # Data tables
    TableStyle,        # Styling for tables
    PageBreak,         # Force new page
    Image              # Images (for logo)
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4  # Standard A4 page size
from reportlab.lib.colors import HexColor, white, black  # Color definitions
from reportlab.lib.units import cm  # Centimeter units for measurements
from reportlab.lib.enums import TA_CENTER, TA_LEFT  # Text alignment options

# Graphics imports for charts
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie

# For downloading the logo image from URL
import requests


# =============================
# BRAND COLORS
# =============================
# Define color scheme for the report
# Using HexColor allows us to use custom brand colors throughout the document
PRIMARY = HexColor("#1f3a5f")    # Dark blue for headers
ACCENT = HexColor("#00b67a")     # Trustpilot green for positive elements
DANGER = HexColor("#ff5b57")     # Red for negative elements
WARNING = HexColor("#f59e0b")    # Orange for neutral/warning elements
GREY = HexColor("#6b7280")       # Grey for secondary text
BG_LIGHT = HexColor("#f5f7fa")   # Light background for tables


# =============================
# LOGO DOWNLOAD HELPER
# =============================
def download_logo(logo_url):
    """
    Download the brand logo from a URL and save it to a temporary file
    
    Args:
        logo_url (str): The URL of the logo image
        
    Returns:
        str: Path to the downloaded logo file, or None if download fails
        
    How it works:
    1. Creates a temporary file to store the image
    2. Downloads the image from the URL using requests library
    3. Saves the binary content to the temp file
    4. Returns the file path so it can be used in the PDF
    """
    if not logo_url:
        return None
    
    try:
        # Make HTTP request to download the image
        # timeout=10 means we'll wait max 10 seconds for response
        response = requests.get(logo_url, timeout=10)
        
        # Check if download was successful (status code 200 means OK)
        if response.status_code == 200:
            # Create a temporary file that won't be auto-deleted
            # suffix='.png' ensures it has the right extension
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            
            # Write the binary image data to the file
            temp_file.write(response.content)
            temp_file.close()
            
            print(f"  [✓] Logo downloaded: {temp_file.name}")
            return temp_file.name
        else:
            print(f"  [!] Failed to download logo: HTTP {response.status_code}")
            return None
            
    except Exception as e:
        # If anything goes wrong (network error, invalid URL, etc.)
        print(f"  [!] Error downloading logo: {e}")
        return None


# =============================
# DATE HELPERS
# =============================
def parse_date(s):
    """
    Parse ISO format date string into Python datetime object
    
    Args:
        s (str): Date string in ISO format (e.g., "2025-12-28T16:29:21.484962Z")
        
    Returns:
        datetime: Parsed datetime object, or None if parsing fails
        
    Note: The "Z" suffix means UTC timezone, so we replace it with "+00:00"
    """
    if not s:
        return None
    return datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))


def week_range():
    """
    Get the date range for the past week (7 days)
    
    Returns:
        tuple: (start_date, end_date) where both are datetime objects
        
    Example: If today is Dec 28, this returns (Dec 21, Dec 28)
    """
    end = datetime.datetime.now(datetime.timezone.utc)
    start = end - datetime.timedelta(days=7)
    return start, end


def filter_week(reviews, start, end):
    """
    Filter reviews that fall within the given date range
    
    Args:
        reviews (list): List of review dictionaries
        start (datetime): Start of date range
        end (datetime): End of date range
        
    Returns:
        list: Reviews that were published within the date range
        
    How it works:
    - Loops through each review
    - Parses the publishedDate field
    - Checks if date falls between start and end
    - Only includes matching reviews in output
    """
    out = []
    for r in reviews:
        # Extract the publishedDate from the nested dates dictionary
        d = parse_date(r.get("dates", {}).get("publishedDate"))
        
        # Check if date exists and is within our range
        if d and start <= d <= end:
            out.append(r)
    return out


# =============================
# ANALYSIS FUNCTIONS
# =============================
def sentiment(reviews):
    """
    Calculate sentiment distribution based on ratings
    
    Args:
        reviews (list): List of review dictionaries
        
    Returns:
        dict: Count of positive, neutral, and negative reviews
        
    Trustpilot rating system:
    - 4-5 stars = Positive
    - 3 stars = Neutral
    - 1-2 stars = Negative
    """
    s = dict(positive=0, neutral=0, negative=0)
    
    for r in reviews:
        rating = r["rating"]
        
        if rating >= 4:
            s["positive"] += 1
        elif rating == 3:
            s["neutral"] += 1
        else:  # rating is 1 or 2
            s["negative"] += 1
            
    return s


def analyze(reviews):
    """
    Perform comprehensive analysis of review data for the past week
    
    Args:
        reviews (list): All reviews from the JSON data
        
    Returns:
        dict: Analysis results including:
            - count: Number of reviews this week
            - avg: Average rating this week
            - sentiment: Sentiment distribution
            - range: Date range analyzed
            - reviews: The filtered review list
            
    This is the main analysis function that pulls together all the data
    we need for the report.
    """
    # Get the date range for the past week
    start, end = week_range()
    
    # Filter to only reviews from this week
    current = filter_week(reviews, start, end)

    # Calculate average rating (handle case where there are no reviews)
    avg = mean([r["rating"] for r in current]) if current else 0

    # Return all the analysis results in a dictionary
    return {
        "count": len(current),
        "avg": avg,
        "sentiment": sentiment(current),
        "range": (start, end),
        "reviews": current
    }


# =============================
# PDF STYLES
# =============================
def build_styles():
    """
    Create custom paragraph styles for different text elements
    
    Returns:
        StyleSheet: Collection of styles that can be applied to Paragraphs
        
    ReportLab uses "styles" to control how text looks. This function creates
    custom styles for different purposes (titles, headers, body text, etc.)
    
    Each ParagraphStyle has properties like:
    - fontSize: Size of the text
    - textColor: Color of the text
    - alignment: Left, center, or right alignment
    - fontName: Font family (Helvetica, Times, etc.)
    - spaceAfter/spaceBefore: Vertical spacing
    """
    # Get the default styles as a starting point
    s = getSampleStyleSheet()

    # Title style - Large, centered, bold text for main title
    s.add(ParagraphStyle(
        "RptTitle",                    # Name we'll use to reference this style
        fontSize=24,                   # Large font size
        textColor=PRIMARY,             # Use our primary color
        alignment=TA_CENTER,           # Center the text
        spaceAfter=8,                  # Add 8 points of space below
        fontName="Helvetica-Bold"      # Use bold Helvetica font
    ))

    # Subtitle style - Medium sized, centered text for secondary headers
    s.add(ParagraphStyle(
        "RptSubtitle",
        fontSize=16,
        textColor=GREY,                # Use grey for less emphasis
        alignment=TA_CENTER,
        spaceAfter=4,
        fontName="Helvetica"           # Regular (not bold) font
    ))

    # Section header style - Bold text for section titles
    s.add(ParagraphStyle(
        "RptHeader",
        fontSize=16,
        textColor=PRIMARY,
        fontName="Helvetica-Bold",
        spaceBefore=15,                # Add space above to separate from previous content
        spaceAfter=12
    ))

    # Small text style - For metadata and captions
    s.add(ParagraphStyle(
        "RptSmall",
        fontSize=10,
        textColor=GREY,
        alignment=TA_CENTER
    ))

    # Body text style - For normal paragraphs
    s.add(ParagraphStyle(
        "RptBody",
        fontSize=11,
        textColor=black,
        spaceAfter=6
    ))

    return s


# =============================
# CHART FUNCTIONS
# =============================
def sentiment_pie_chart(sent):
    """
    Create a pie chart showing sentiment distribution
    
    Args:
        sent (dict): Sentiment data with positive, neutral, negative counts
        
    Returns:
        Drawing: A ReportLab Drawing object containing the pie chart
        
    How pie charts work in ReportLab:
    1. Create a Drawing (canvas for the chart)
    2. Create a Pie chart object
    3. Set position (x, y) and size (width, height)
    4. Provide data and labels
    5. Style the slices (colors, borders)
    6. Add the chart to the drawing
    """
    # Create a drawing canvas - like a rectangle to hold the chart
    d = Drawing(400, 200)  # 400 points wide, 200 points tall
    
    # Create the pie chart object
    pc = Pie()
    pc.x = 100         # X position within the drawing (from left edge)
    pc.y = 20          # Y position within the drawing (from bottom edge)
    pc.width = 200     # Width of the pie chart
    pc.height = 200    # Height of the pie chart
    
    # Calculate total for checking if we have data
    total = sent["positive"] + sent["neutral"] + sent["negative"]
    
    if total > 0:
        # We have data - create slices for each sentiment
        pc.data = [sent["positive"], sent["neutral"], sent["negative"]]
        
        # Labels that will appear next to each slice
        pc.labels = [
            f'Positive ({sent["positive"]})',
            f'Neutral ({sent["neutral"]})',
            f'Negative ({sent["negative"]})'
        ]
    else:
        # No data - show a placeholder
        pc.data = [1]
        pc.labels = ['No data']
    
    # Style each slice with colors
    # slices[0] = first slice (positive)
    pc.slices[0].fillColor = ACCENT    # Green for positive
    pc.slices[1].fillColor = WARNING   # Orange for neutral
    if len(pc.slices) > 2:
        pc.slices[2].fillColor = DANGER    # Red for negative
    
    # Add borders to slices
    pc.slices.strokeWidth = 1      # 1 point border
    pc.slices.strokeColor = white  # White border color
    
    # Add the pie chart to the drawing
    d.add(pc)
    return d


def rating_bar_chart(analysis):
    """
    Create a bar chart showing distribution of 1-5 star ratings
    
    Args:
        analysis (dict): Analysis data containing list of reviews
        
    Returns:
        Drawing: A ReportLab Drawing object containing the bar chart
        
    This chart shows how many reviews received each rating (1-5 stars),
    making it easy to see if most reviews are positive, negative, or mixed.
    """
    # Create drawing canvas
    d = Drawing(400, 200)
    
    # Count how many reviews have each rating
    # Initialize with 0 for each possible rating
    rating_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    
    # Loop through reviews and count each rating
    for review in analysis["reviews"]:
        rating = review["rating"]
        if rating in rating_counts:
            rating_counts[rating] += 1
    
    # Create the vertical bar chart
    chart = VerticalBarChart()
    chart.x = 40           # X position
    chart.y = 30           # Y position
    chart.width = 320      # Chart width
    chart.height = 150     # Chart height
    
    # Data must be in a list of lists format
    # [list of values for each bar]
    chart.data = [[rating_counts[i] for i in range(1, 6)]]
    
    # Labels for X axis (under each bar)
    chart.categoryAxis.categoryNames = ['1★', '2★', '3★', '4★', '5★']
    
    # Style the bars
    chart.bars[0].fillColor = ACCENT  # Color all bars green
    
    # Set Y axis range
    chart.valueAxis.valueMin = 0
    # Set max slightly above highest value for nice spacing
    max_count = max(rating_counts.values()) if rating_counts.values() else 5
    chart.valueAxis.valueMax = max_count + 1
    
    # Add chart to drawing
    d.add(chart)
    return d


# =============================
# HEADER FUNCTION
# =============================
def add_header(canvas, doc, logo_path, brand_name):
    """
    Add a header with logo and brand name to each page
    
    Args:
        canvas: ReportLab canvas object (what we draw on)
        doc: Document object
        logo_path (str): Path to the downloaded logo file
        brand_name (str): Name of the brand
        
    How headers work:
    - This function is called automatically for each page
    - We use canvas.saveState() and restoreState() to avoid affecting
      the rest of the page
    - We position elements using coordinates (x, y from bottom-left)
    """
    canvas.saveState()  # Save current canvas state
    
    # Draw logo if available
    if logo_path and os.path.exists(logo_path):
        try:
            # Create Image object from logo file
            # 2*cm is the width, preserveAspectRatio keeps proportions
            logo = Image(logo_path, width=2*cm, height=2*cm)
            
            # Position logo at top-left of page
            # A4[0] is page width, A4[1] is page height
            logo.drawOn(canvas, 2*cm, A4[1] - 3*cm)
        except Exception as e:
            # If logo fails to load, just skip it
            print(f"  [!] Could not add logo to header: {e}")
    
    # Add brand name next to logo
    canvas.setFont("Helvetica-Bold", 14)  # Set font and size
    canvas.setFillColor(PRIMARY)          # Set text color
    
    # Draw text at position (4.2cm from left, near top of page)
    canvas.drawString(4.2*cm, A4[1] - 2.1*cm, brand_name)
    
    canvas.restoreState()  # Restore canvas state


# =============================
# FOOTER FUNCTION
# =============================
def footer(canvas, doc, brand_name):
    """
    Add footer with brand name, page number, and generation time to each page
    
    Args:
        canvas: ReportLab canvas object
        doc: Document object (has page number in doc.page)
        brand_name (str): Name of the brand to display
        
    The footer appears at the bottom of every page and provides:
    - Brand name (left side)
    - Page number (right side)
    - Generation timestamp (center)
    """
    canvas.saveState()
    
    # Set font for footer text
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(GREY)  # Use grey color for subtle footer
    
    # Brand name - Left side
    # 2*cm from left edge, 1.5*cm from bottom
    canvas.drawString(2*cm, 1.5*cm, brand_name)
    
    # Page number - Right side
    # drawRightString aligns text to the right of the x position
    canvas.drawRightString(
        A4[0] - 2*cm,    # Page width minus 2cm margin
        1.5*cm,          # 1.5cm from bottom
        f"Page {doc.page}"
    )
    
    # Generation timestamp - Center
    # Format current time as "YYYY-MM-DD HH:MM"
    timestamp = f"Generated: {datetime.datetime.now():%Y-%m-%d %H:%M}"
    
    # Center the text by positioning at middle of page width
    canvas.drawString(2*cm, 1*cm, timestamp)

    
    canvas.restoreState()


# =============================
# PDF GENERATION
# =============================
def generate_pdf(data, output):
    """
    Generate the complete PDF report
    
    Args:
        data (dict): The full JSON data from Trustpilot scraper
        output (str): Path where PDF file should be saved
        
    This is the main function that:
    1. Downloads the logo
    2. Analyzes the review data
    3. Creates all the content (text, tables, charts)
    4. Assembles everything into a PDF document
    
    How ReportLab documents work:
    - Create a "story" (list of elements)
    - Add elements to story in order (title, text, table, chart, etc.)
    - Call doc.build(story) to generate the PDF
    """
    # Get company data and brand name
    company = data["company"]
    brand_name = company["brand_name"]
    
    print(f"\n[*] Generating PDF for: {brand_name}")
    
    # Download the brand logo
    logo_path = download_logo(company.get("logo_url"))
    
    # Get custom styles for text formatting
    s = build_styles()
    
    # Analyze the review data
    analysis = analyze(data["reviews"])
    print(f"  [*] Analyzed {analysis['count']} reviews from past week")

    # Create the PDF document
    # SimpleDocTemplate handles page layout, margins, etc.
    doc = SimpleDocTemplate(
        output,
        pagesize=A4,           # Standard A4 paper size
        leftMargin=2*cm,       # 2cm margin on left
        rightMargin=2*cm,      # 2cm margin on right
        topMargin=3.5*cm,      # 3.5cm margin on top (room for header)
        bottomMargin=3*cm      # 3cm margin on bottom (room for footer)
    )

    # Create the "story" - list of elements to include in PDF
    story = []

    # ===== COVER PAGE =====
    # Company name as main title
    story.append(Paragraph(brand_name, s["RptTitle"]))
    story.append(Spacer(1, 0.5*cm))  # Add 0.5cm vertical space

    # Report subtitle
    story.append(Paragraph("Weekly Trustpilot Report", s["RptSubtitle"]))

    # Date range
    ws, we = analysis["range"]  # Week start, week end
    story.append(Spacer(1, 0.1*cm))
    story.append(Paragraph(
        f"{ws:%B %d, %Y} – {we:%B %d, %Y}",  # Format: "December 21, 2025 – December 28, 2025"
        s["RptSmall"]
    ))

    # ===== AI SUMMARY SECTION =====
    # Only include if AI summary exists in data
    if company.get("ai_summary"):
        story.append(Spacer(1, 1*cm))
        story.append(Paragraph("AI-Generated Insights", s["RptHeader"]))
        
        # Get the summary text
        summary_text = company["ai_summary"]["summary"]
        
        # Split into paragraphs (separated by double newlines)
        # and add each paragraph to the story
        for para in summary_text.split("\n\n"):
            if para.strip():  # Only add non-empty paragraphs
                story.append(Paragraph(para.strip(), s["RptBody"]))
                story.append(Spacer(1, 0.3*cm))

    story.append(Spacer(1, 1*cm))

    # ===== SUMMARY TABLE =====
    # Create a table with key metrics
    # Each row is [label, value]
    summary_data = [
        ["Trust Score", f"{company['trust_score']}/5"],
        ["Total Reviews", f"{company['total_reviews']:,}"],  # :, adds comma separators
        ["New This Week", f"{analysis['count']}"],
        ["Average Rating", f"{analysis['avg']:.2f}/5"]  # :.2f formats to 2 decimal places
    ]
    
    # Create table with equal column widths (8cm each)
    summary_table = Table(summary_data, colWidths=[8*cm, 8*cm])
    
    # Apply styling to the table
    summary_table.setStyle(TableStyle([
        # Background color for all cells
        ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
        # Text color for all cells
        ('TEXTCOLOR', (0, 0), (-1, -1), PRIMARY),
        # Center align all cells
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        # Bold font for all cells
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        # Font size
        ('FONTSIZE', (0, 0), (-1, -1), 14),
        # Padding
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        # Grid lines (1 point, white color)
        ('GRID', (0, 0), (-1, -1), 1, white)
    ]))
    
    story.append(summary_table)
    story.append(PageBreak())  # Start new page

    # ===== SENTIMENT ANALYSIS SECTION =====
    story.append(Paragraph("Sentiment Analysis", s["RptHeader"]))
    
    # Get sentiment data
    sent = analysis["sentiment"]
    total = sent["positive"] + sent["neutral"] + sent["negative"]
    
    # Add text description of sentiment
    if total > 0:
        # Calculate percentages and add as paragraphs
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
    
    # Add the pie chart
    story.append(sentiment_pie_chart(sent))

    # ===== RATING DISTRIBUTION SECTION =====
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph("Rating Distribution", s["RptHeader"]))
    
    # Add the bar chart
    story.append(rating_bar_chart(analysis))

    # ===== BUILD THE PDF =====
    # This is where the magic happens!
    # build() processes the story and creates the actual PDF file
    
    # We use lambda functions to pass additional parameters to header/footer
    # onFirstPage = function called for first page
    # onLaterPages = function called for pages 2+
    doc.build(
        story,
        onFirstPage=lambda c, d: (
            add_header(c, d, logo_path, brand_name),
            footer(c, d, brand_name)
        ),
        onLaterPages=lambda c, d: (
            add_header(c, d, logo_path, brand_name),
            footer(c, d, brand_name)
        )
    )
    
    # Clean up: delete temporary logo file
    if logo_path and os.path.exists(logo_path):
        try:
            os.unlink(logo_path)
            print(f"  [✓] Cleaned up temporary logo file")
        except:
            pass  # If we can't delete it, that's okay
    
    # Print success message
    print(f"\n[✓] PDF generated successfully: {output}")
    print(f"    Reviews analyzed: {analysis['count']}")
    print(f"    Average rating: {analysis['avg']:.2f}/5")


# =============================
# MAIN ENTRY POINT
# =============================
def main():
    """
    Main entry point when script is run from command line
    
    Usage:
        python weekly_review_report.py [input_file] [output_file]
        
    If no arguments provided, uses default filenames.
    """
    import sys
    
    # Default filenames
    input_file = "trustpilot_raw_data.json"
    output_file = "weekly_review_report.pdf"
    
    # Allow overriding via command line arguments
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    
    # Print header
    print("\n" + "="*70)
    print("TRUSTPILOT WEEKLY REPORT - PDF GENERATOR")
    print("="*70)
    print(f"\nInput:  {input_file}")
    print(f"Output: {output_file}\n")
    
    try:
        # Load the JSON data
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Generate the PDF
        generate_pdf(data, output_file)
        
        # Print completion message
        print("\n" + "="*70)
        print("PDF GENERATION COMPLETE")
        print("="*70 + "\n")
        
    except FileNotFoundError:
        print(f"\n[!] Error: File '{input_file}' not found")
        print("    Make sure you run mvp.py first to generate the data file")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n[!] Error generating PDF: {e}")
        # Print full error traceback for debugging
        import traceback
        traceback.print_exc()
        sys.exit(1)


# This block only runs if the script is executed directly
# (not if it's imported as a module)
if __name__ == "__main__":
    main()