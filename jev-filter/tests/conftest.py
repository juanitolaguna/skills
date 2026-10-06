import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def write_pdf(path: Path, pages: int) -> Path:
    """A PDF whose page n carries the marker PAGEnn and enough words to pass --min-words."""
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_font("Helvetica", size=11)
    for n in range(1, pages + 1):
        pdf.add_page()
        pdf.multi_cell(0, 6, f"PAGE{n:02d} " + "lorem ipsum dolor sit amet " * 10)
    pdf.output(str(path))
    return path


def page_markers(text: str) -> list[str]:
    import re

    return sorted(set(re.findall(r"PAGE\d\d", text)))
