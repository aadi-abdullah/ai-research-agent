"""
utils/pdf_exporter.py – Professional PDF report export.

Uses only built-in core PDF fonts (Helvetica, Courier) — no TTF files
or external dependencies required beyond fpdf2 itself.

Install:
    pip install fpdf2
"""

import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from fpdf import FPDF

logger = logging.getLogger(__name__)

MARGIN_LEFT   = 20
MARGIN_RIGHT  = 20
MARGIN_TOP    = 25
MARGIN_BOTTOM = 20

COLOR_DARK    = (30,  30,  40)
COLOR_HEADING = (15,  15,  25)
COLOR_ACCENT  = (80,  60, 180)
COLOR_MUTED   = (120, 120, 135)
COLOR_RULE    = (210, 210, 220)


class ResearchPDF(FPDF):
    """A polished research-report PDF using only core fonts."""

    def __init__(self, title: str = "AI Research Report") -> None:
        super().__init__()
        self.report_title = title
        self.set_margins(MARGIN_LEFT, MARGIN_TOP, MARGIN_RIGHT)
        self.set_auto_page_break(auto=True, margin=MARGIN_BOTTOM)

    @staticmethod
    def _safe(text: str) -> str:
        """Sanitise to Latin-1 so core PDF fonts never crash on Unicode."""
        return text.encode("latin-1", errors="replace").decode("latin-1")

    def header(self) -> None:
        self.set_fill_color(*COLOR_ACCENT)
        self.rect(0, 0, self.w, 4, "F")
        self.set_y(8)
        self.set_font("Helvetica", size=8)
        self.set_text_color(*COLOR_MUTED)
        self.cell(0, 6, self._safe(self.report_title.upper()), align="C")
        self.set_draw_color(*COLOR_RULE)
        self.set_line_width(0.2)
        self.line(MARGIN_LEFT, 17, self.w - MARGIN_RIGHT, 17)
        self.ln(6)

    def footer(self) -> None:
        self.set_y(-15)
        self.set_draw_color(*COLOR_RULE)
        self.set_line_width(0.2)
        self.line(MARGIN_LEFT, self.get_y(), self.w - MARGIN_RIGHT, self.get_y())
        self.ln(2)
        self.set_font("Helvetica", size=7)
        self.set_text_color(*COLOR_MUTED)
        # Left: author watermark
        self.set_x(MARGIN_LEFT)
        self.cell(90, 6, "Built by Abdullah Shafique  |  github.com/aadi-abdullah", align="L")
        # Right: page number
        self.cell(0, 6, f"Page {self.page_no()}  |  {datetime.now().strftime('%Y-%m-%d')}", align="R")

    def add_cover(self, query: Optional[str] = None) -> None:
        self.add_page()
        self.ln(20)
        self.set_font("Helvetica", style="B", size=26)
        self.set_text_color(*COLOR_HEADING)
        self.multi_cell(0, 12, self._safe(self.report_title), align="C")
        cx = self.w / 2
        self.set_draw_color(*COLOR_ACCENT)
        self.set_line_width(1.2)
        self.line(cx - 25, self.get_y() + 3, cx + 25, self.get_y() + 3)
        self.ln(12)
        if query:
            self.set_font("Helvetica", style="I", size=11)
            self.set_text_color(*COLOR_MUTED)
            self.multi_cell(0, 7, self._safe(f'"{query}"'), align="C")
            self.ln(6)
        self.set_font("Helvetica", size=9)
        self.set_text_color(*COLOR_MUTED)
        self.cell(0, 6, datetime.now().strftime("%B %d, %Y"), align="C")

    def add_h1(self, text: str) -> None:
        self.ln(4)
        self.set_font("Helvetica", style="B", size=16)
        self.set_text_color(*COLOR_HEADING)
        self.multi_cell(0, 9, self._safe(text.strip()))
        self.set_draw_color(*COLOR_ACCENT)
        self.set_line_width(0.6)
        self.line(MARGIN_LEFT, self.get_y(), self.w - MARGIN_RIGHT, self.get_y())
        self.ln(4)

    def add_h2(self, text: str) -> None:
        self.ln(3)
        self.set_font("Helvetica", style="B", size=13)
        self.set_text_color(*COLOR_HEADING)
        self.multi_cell(0, 8, self._safe(text.strip()))
        self.ln(2)

    def add_h3(self, text: str) -> None:
        self.ln(2)
        self.set_font("Helvetica", style="B", size=11)
        self.set_text_color(*COLOR_HEADING)
        self.multi_cell(0, 7, self._safe(text.strip()))
        self.ln(1)

    def add_body(self, text: str) -> None:
        self.set_font("Helvetica", size=10)
        self.set_text_color(*COLOR_DARK)
        self.multi_cell(0, 6, self._safe(text.strip()))
        self.ln(2)

    def add_bullet(self, text: str, level: int = 0) -> None:
        indent = 5 + level * 4
        bullet = "-" if level == 0 else ">"
        self.set_font("Helvetica", size=10)
        self.set_text_color(*COLOR_DARK)
        self.set_x(MARGIN_LEFT + indent)
        self.cell(6, 6, bullet)
        self.set_x(MARGIN_LEFT + indent + 6)
        self.multi_cell(self.w - MARGIN_LEFT - MARGIN_RIGHT - indent - 6, 6, self._safe(text.strip()))
        self.ln(0.5)

    def add_horizontal_rule(self) -> None:
        self.ln(2)
        self.set_draw_color(*COLOR_RULE)
        self.set_line_width(0.2)
        self.line(MARGIN_LEFT, self.get_y(), self.w - MARGIN_RIGHT, self.get_y())
        self.ln(4)

    def add_source_list(self, sources: list[str]) -> None:
        self.add_page()
        self.add_h1("Sources & References")
        self.set_font("Courier", size=8)
        self.set_text_color(*COLOR_MUTED)
        for i, url in enumerate(sources, 1):
            self.set_x(MARGIN_LEFT)
            self.cell(10, 5.5, f"{i:02d}.")
            self.set_x(MARGIN_LEFT + 10)
            self.multi_cell(self.w - MARGIN_LEFT - MARGIN_RIGHT - 10, 5.5, self._safe(url))
            self.ln(0.5)


_RE_H1     = re.compile(r"^#{1}\s+(.*)")
_RE_H2     = re.compile(r"^#{2}\s+(.*)")
_RE_H3     = re.compile(r"^#{3,}\s+(.*)")
_RE_BULLET = re.compile(r"^(\s*)[-*+]\s+(.*)")
_RE_HR     = re.compile(r"^[-*_]{3,}\s*$")
_RE_BOLD   = re.compile(r"\*\*(.*?)\*\*")
_RE_ITALIC = re.compile(r"\*(.*?)\*")


def _strip_inline_md(text: str) -> str:
    text = _RE_BOLD.sub(r"\1", text)
    text = _RE_ITALIC.sub(r"\1", text)
    return text


def _render_markdown(pdf: ResearchPDF, report: str) -> None:
    for para in report.split("\n\n"):
        para = para.strip()
        if not para:
            continue
        for line in para.splitlines():
            line_stripped = line.strip()
            if not line_stripped:
                continue
            if m := _RE_H1.match(line_stripped):
                heading_text = _strip_inline_md(m.group(1))
                if "source" in heading_text.lower():
                    pdf.add_page()
                pdf.add_h1(heading_text)
            elif m := _RE_H2.match(line_stripped):
                heading_text = _strip_inline_md(m.group(1))
                if "source" in heading_text.lower():
                    pdf.add_page()
                pdf.add_h2(heading_text)
            elif m := _RE_H3.match(line_stripped):
                pdf.add_h3(_strip_inline_md(m.group(1)))
            elif m := _RE_BULLET.match(line):
                pdf.add_bullet(_strip_inline_md(m.group(2)), level=len(m.group(1)) // 2)
            elif _RE_HR.match(line_stripped):
                pdf.add_horizontal_rule()
            else:
                pdf.add_body(_strip_inline_md(line_stripped))


def export_pdf(
    report: str,
    filename: str = "research_report.pdf",
    query:   Optional[str] = None,
    sources: Optional[list[str]] = None,
    title:   str = "AI Research Report",
) -> bool:
    """
    Export *report* as a formatted PDF using only built-in core fonts.
    No TTF files or font installation required.
    """
    if not report or not report.strip():
        logger.error("export_pdf called with empty report.")
        return False

    Path(filename).parent.mkdir(parents=True, exist_ok=True)

    try:
        pdf = ResearchPDF(title=title)
        pdf.add_cover(query=query)
        pdf.add_page()
        _render_markdown(pdf, report)
        if sources:
            pdf.add_source_list(sources)
        pdf.output(filename)
        logger.info("PDF saved -> %s", filename)
        print(f"  PDF saved -> {filename}")
        return True

    except Exception as exc:
        logger.exception("Failed to export PDF.")
        print(f"  PDF export error: {exc}")
        return False


