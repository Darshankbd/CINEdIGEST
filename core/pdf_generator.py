import io
import re
from datetime import datetime
from typing import List, Dict, Any

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    HRFlowable
)


# ── Color Palette ──
CLR_PRIMARY = HexColor("#1a237e")      # Deep indigo
CLR_ACCENT = HexColor("#ff6f00")       # Amber accent
CLR_DARK = HexColor("#212121")         # Near black
CLR_GRAY = HexColor("#616161")         # Medium gray
CLR_LIGHT_BG = HexColor("#e8eaf6")    # Light indigo background
CLR_WHITE = HexColor("#ffffff")


def _format_time(seconds: float) -> str:
    """Convert seconds to HH:MM:SS format."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def _strip_markdown(text: str) -> str:
    """Strip markdown formatting markers and convert to clean text for PDF."""
    if not text:
        return ""
    # Remove markdown headers
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    # Convert bold **text** to <b>text</b> for reportlab
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    # Convert italic *text* to <i>text</i>
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
    # Remove markdown horizontal rules
    text = re.sub(r'^---+\s*$', '', text, flags=re.MULTILINE)
    # Remove emoji characters that might not render in PDF
    text = re.sub(r'[🎬👥🎭⏱️⭐📝📋📑🎯🔬⚙️🛡️📖📍📌🚀💬🧠🗄️📊📥🎧📜🧩💡🏆👍📚🎴🔄]', '', text)
    # Clean up extra whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _build_styles():
    """Create custom paragraph styles for the PDF."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name='CoverTitle',
        fontName='Helvetica-Bold',
        fontSize=28,
        textColor=CLR_PRIMARY,
        alignment=TA_CENTER,
        spaceAfter=20,
        leading=34
    ))

    styles.add(ParagraphStyle(
        name='CoverSubtitle',
        fontName='Helvetica',
        fontSize=14,
        textColor=CLR_GRAY,
        alignment=TA_CENTER,
        spaceAfter=10,
        leading=18
    ))

    styles.add(ParagraphStyle(
        name='SectionTitle',
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=CLR_PRIMARY,
        spaceBefore=20,
        spaceAfter=12,
        leading=22
    ))

    styles.add(ParagraphStyle(
        name='SubsectionTitle',
        fontName='Helvetica-Bold',
        fontSize=13,
        textColor=CLR_ACCENT,
        spaceBefore=14,
        spaceAfter=6,
        leading=16
    ))

    styles.add(ParagraphStyle(
        name='BodyText_Custom',
        fontName='Helvetica',
        fontSize=10,
        textColor=CLR_DARK,
        alignment=TA_JUSTIFY,
        spaceAfter=8,
        leading=14
    ))

    styles.add(ParagraphStyle(
        name='ChapterTitle',
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=CLR_PRIMARY,
        spaceBefore=10,
        spaceAfter=4,
        leading=15
    ))

    styles.add(ParagraphStyle(
        name='Timestamp',
        fontName='Helvetica',
        fontSize=9,
        textColor=CLR_GRAY,
        spaceAfter=4,
        leading=12
    ))

    styles.add(ParagraphStyle(
        name='TOC_Entry',
        fontName='Helvetica',
        fontSize=12,
        textColor=CLR_DARK,
        spaceBefore=6,
        spaceAfter=6,
        leading=16,
        leftIndent=20
    ))

    styles.add(ParagraphStyle(
        name='Footer',
        fontName='Helvetica',
        fontSize=8,
        textColor=CLR_GRAY,
        alignment=TA_CENTER
    ))

    return styles


def _add_page_number(canvas, doc):
    """Add page number footer to each page."""
    canvas.saveState()
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(CLR_GRAY)
    page_num = canvas.getPageNumber()
    canvas.drawCentredString(A4[0] / 2, 1.5 * cm, f"Page {page_num}  |  CineDigest Movie Report")
    canvas.restoreState()


def generate_movie_pdf(movie_data: Dict[str, Any]) -> bytes:
    """
    Generate a professional PDF report from movie analysis data.

    Args:
        movie_data: Dictionary with keys:
            - title (str): Movie filename/title
            - duration (float): Duration in seconds
            - transcript_segments (list): List of transcript dicts
            - chapters (list): List of chapter dicts
            - notes (str): Full notes text
            - review (str): Full review text
            - summary (str): Executive summary text

    Returns:
        bytes: PDF file content
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
        title=f"CineDigest Report - {movie_data.get('title', 'Movie')}",
        author="CineDigest AI Platform"
    )

    styles = _build_styles()
    story = []

    title = movie_data.get("title", "Unknown Movie")
    duration = movie_data.get("duration", 0)
    chapters = movie_data.get("chapters", [])
    transcript_segments = movie_data.get("transcript_segments", [])
    notes = movie_data.get("notes", "")
    review = movie_data.get("review", "")
    summary = movie_data.get("summary", "")

    hrs = int(duration // 3600)
    mins = int((duration % 3600) // 60)

    # ═══════════════════════════════════════════════════════
    # TITLE PAGE
    # ═══════════════════════════════════════════════════════
    story.append(Spacer(1, 3 * cm))
    story.append(Paragraph("CINEDIGEST", styles['CoverTitle']))
    story.append(Paragraph("Movie Review &amp; Summary Report", styles['CoverSubtitle']))
    story.append(Spacer(1, 1.5 * cm))
    story.append(HRFlowable(width="60%", thickness=2, color=CLR_PRIMARY))
    story.append(Spacer(1, 1 * cm))

    clean_title = re.sub(r'\.[^.]+$', '', title).replace("_", " ").replace("-", " ")
    story.append(Paragraph(clean_title, styles['CoverTitle']))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(f"Runtime: {hrs}h {mins}m  |  Chapters: {len(chapters)}", styles['CoverSubtitle']))
    story.append(Paragraph(f"Transcript Segments: {len(transcript_segments)}", styles['CoverSubtitle']))
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(
        f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
        styles['CoverSubtitle']
    ))
    story.append(Paragraph("Powered by CineDigest AI Platform", styles['CoverSubtitle']))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════
    # TABLE OF CONTENTS
    # ═══════════════════════════════════════════════════════
    story.append(Paragraph("Table of Contents", styles['SectionTitle']))
    story.append(HRFlowable(width="100%", thickness=1, color=CLR_PRIMARY))
    story.append(Spacer(1, 0.5 * cm))

    toc_items = [
        "1. Executive Summary",
        "2. Story Chapters",
        "3. Detailed Scene Notes",
        "4. Movie Review &amp; Analysis",
        "5. Full Transcript"
    ]
    for item in toc_items:
        story.append(Paragraph(item, styles['TOC_Entry']))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════
    # SECTION 1: EXECUTIVE SUMMARY
    # ═══════════════════════════════════════════════════════
    story.append(Paragraph("1. Executive Summary", styles['SectionTitle']))
    story.append(HRFlowable(width="100%", thickness=1, color=CLR_PRIMARY))
    story.append(Spacer(1, 0.3 * cm))

    summary_clean = _strip_markdown(summary)
    for para in summary_clean.split("\n\n"):
        para = para.strip()
        if para:
            story.append(Paragraph(para, styles['BodyText_Custom']))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════
    # SECTION 2: STORY CHAPTERS
    # ═══════════════════════════════════════════════════════
    story.append(Paragraph("2. Story Chapters", styles['SectionTitle']))
    story.append(HRFlowable(width="100%", thickness=1, color=CLR_PRIMARY))
    story.append(Spacer(1, 0.3 * cm))

    for ch in chapters:
        ch_num = ch.get("chapter_num", 0)
        ch_title = ch.get("title", f"Chapter {ch_num}")
        start = ch.get("start_time", 0)
        end = ch.get("end_time", 0)
        ch_summary = ch.get("summary", "")
        characters = ch.get("characters", "")

        story.append(Paragraph(
            f"Chapter {ch_num}: {_strip_markdown(ch_title)}",
            styles['ChapterTitle']
        ))
        story.append(Paragraph(
            f"Timestamp: {_format_time(start)} - {_format_time(end)}  |  Characters: {characters}",
            styles['Timestamp']
        ))
        story.append(Paragraph(_strip_markdown(ch_summary), styles['BodyText_Custom']))
        story.append(Spacer(1, 0.3 * cm))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════
    # SECTION 3: DETAILED NOTES
    # ═══════════════════════════════════════════════════════
    story.append(Paragraph("3. Detailed Scene Notes", styles['SectionTitle']))
    story.append(HRFlowable(width="100%", thickness=1, color=CLR_PRIMARY))
    story.append(Spacer(1, 0.3 * cm))

    notes_clean = _strip_markdown(notes)
    for para in notes_clean.split("\n\n"):
        para = para.strip()
        if not para:
            continue
        # Check if it looks like a heading (starts with uppercase, short line)
        if len(para) < 80 and not para.endswith('.'):
            story.append(Paragraph(para, styles['SubsectionTitle']))
        else:
            story.append(Paragraph(para, styles['BodyText_Custom']))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════
    # SECTION 4: MOVIE REVIEW
    # ═══════════════════════════════════════════════════════
    story.append(Paragraph("4. Movie Review &amp; Analysis", styles['SectionTitle']))
    story.append(HRFlowable(width="100%", thickness=1, color=CLR_PRIMARY))
    story.append(Spacer(1, 0.3 * cm))

    review_clean = _strip_markdown(review)
    for para in review_clean.split("\n\n"):
        para = para.strip()
        if not para:
            continue
        if len(para) < 80 and not para.endswith('.'):
            story.append(Paragraph(para, styles['SubsectionTitle']))
        else:
            story.append(Paragraph(para, styles['BodyText_Custom']))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════
    # SECTION 5: FULL TRANSCRIPT
    # ═══════════════════════════════════════════════════════
    story.append(Paragraph("5. Full Transcript", styles['SectionTitle']))
    story.append(HRFlowable(width="100%", thickness=1, color=CLR_PRIMARY))
    story.append(Spacer(1, 0.3 * cm))

    for seg in transcript_segments:
        ts_start = _format_time(seg.get("start", 0))
        ts_end = _format_time(seg.get("end", 0))
        speaker = seg.get("speaker", "Speaker")
        text = seg.get("text", "")

        story.append(Paragraph(
            f"[{ts_start} - {ts_end}] <b>{speaker}</b>",
            styles['Timestamp']
        ))
        story.append(Paragraph(text, styles['BodyText_Custom']))

    # ═══════════════════════════════════════════════════════
    # BUILD PDF
    # ═══════════════════════════════════════════════════════
    doc.build(story, onFirstPage=_add_page_number, onLaterPages=_add_page_number)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
