"""
Debate Document Analyzer
Extracts: offs, taglines, citations, and highlighted text from a .docx debate file.

Usage:
    python analyze_debate_doc.py <path_to_docx>

Requirements:
    pip install python-docx lxml
"""

import sys
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict

# -------------------------------------------------------------------
# DOCX XML helpers
# -------------------------------------------------------------------

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

def w(tag):
    return f"{{{W}}}{tag}"

def parse_docx_xml(docx_path: str) -> ET.Element:
    """Return the root element of word/document.xml inside the .docx."""
    with zipfile.ZipFile(docx_path) as z:
        with z.open("word/document.xml") as f:
            return ET.parse(f).getroot()

def get_style(p: ET.Element) -> str:
    pPr = p.find(w("pPr"))
    if pPr is not None:
        pStyle = pPr.find(w("pStyle"))
        if pStyle is not None:
            return pStyle.get(w("val"), "Normal")
    return "Normal"

def get_text(p: ET.Element) -> str:
    return "".join(t.text or "" for t in p.iter(w("t")))

def get_runs_with_props(p: ET.Element):
    """Yield (text, highlight_color, is_bold, font_size) for each run."""
    for r in p.iter(w("r")):
        t_el = r.find(w("t"))
        text = t_el.text or "" if t_el is not None else ""
        if not text:
            continue
        rPr = r.find(w("rPr"))
        highlight = None
        bold = False
        font_size = None
        if rPr is not None:
            h = rPr.find(w("highlight"))
            if h is not None:
                highlight = h.get(w("val"), "unknown")
            b = rPr.find(w("b"))
            if b is not None:
                bold = True
            sz = rPr.find(w("sz"))
            if sz is not None:
                v = sz.get(w("val"))
                if v:
                    font_size = int(v) // 2  # half-points → points
        yield text, highlight, bold, font_size

def get_highlighted_text(p: ET.Element) -> str:
    """Return only the highlighted characters from a paragraph."""
    return "".join(text for text, hl, _, _ in get_runs_with_props(p) if hl)


# -------------------------------------------------------------------
# Classification helpers
# -------------------------------------------------------------------

# Debate citation pattern: LastName '## [ ...
def classify_heading4(text: str):
    """Return 'off' or 'tagline' for a Heading4 paragraph."""
    stripped = text.strip()
    # Off names: short, no internal periods/commas, often end in colon
    has_sentence_chars = bool(re.search(r"[.,;]", stripped))
    is_short = len(stripped) < 50
    ends_colon = stripped.endswith(":")
    if ends_colon or (is_short and not has_sentence_chars):
        return "off"
    return "tagline"


# -------------------------------------------------------------------
# Main analysis
# -------------------------------------------------------------------

def analyze(docx_path: str) -> dict:
    root = parse_docx_xml(docx_path)
    # Only look at non-empty paragraphs
    all_paragraphs = list(root.iter(w("p")))
    paragraphs = [(p, get_style(p), get_text(p).strip()) for p in all_paragraphs]
    paragraphs = [(p, s, t) for p, s, t in paragraphs if t]  # drop blanks

    offs = []
    taglines = []
    citations = []
    highlighted_paragraphs = []

    for i, (p, style, text) in enumerate(paragraphs):

        # ---- offs & taglines ----
        if style == "Heading4":
            kind = classify_heading4(text)
            if kind == "off":
                offs.append(text)
            else:
                taglines.append(text)

        # ---- citations: structurally, the first Normal paragraph after a Heading4 ----
        elif style == "Normal":
            prev_style = paragraphs[i - 1][1] if i > 0 else None
            if prev_style == "Heading4":
                citations.append(text)

        # ---- highlights ----
        hl_text = get_highlighted_text(p)
        if hl_text.strip():
            highlighted_paragraphs.append({
                "style": style,
                "full_text": text,
                "highlighted": hl_text.strip(),
            })

    return {
        "offs": offs,
        "taglines": taglines,
        "citations": citations,
        "highlighted_paragraphs": highlighted_paragraphs,
    }


def print_report(results: dict, docx_path: str):
    offs = results["offs"]
    taglines = results["taglines"]
    citations = results["citations"]
    highlights = results["highlighted_paragraphs"]

    print("=" * 70)
    print(f"DEBATE DOCUMENT ANALYSIS")
    print(f"File: {Path(docx_path).name}")
    print("=" * 70)

    # ---- OFFS ----
    print(f"\n{'─'*70}")
    print(f"OFFS  ({len(offs)} total)")
    print(f"{'─'*70}")
    for i, o in enumerate(offs, 1):
        print(f"  {i:2d}. {o}")

    # ---- TAGLINES ----
    print(f"\n{'─'*70}")
    print(f"TAGLINES  ({len(taglines)} total)")
    print(f"{'─'*70}")
    for i, t in enumerate(taglines, 1):
        # wrap at 100 chars
        if len(t) > 100:
            print(f"  {i:2d}. {t[:97]}...")
        else:
            print(f"  {i:2d}. {t}")

    # ---- CITATIONS ----
    print(f"\n{'─'*70}")
    print(f"CITATIONS  ({len(citations)} total)")
    print(f"{'─'*70}")
    for i, c in enumerate(citations, 1):
        if len(c) > 120:
            print(f"  {i:2d}. {c[:117]}...")
        else:
            print(f"  {i:2d}. {c}")

    # ---- HIGHLIGHTED LINES ----
    print(f"\n{'─'*70}")
    print(f"HIGHLIGHTED TEXT  ({len(highlights)} paragraphs with highlighting)")
    print(f"  (cyan highlight = underlined/read text in debate)")
    print(f"{'─'*70}")
    for i, h in enumerate(highlights, 1):
        hl = h["highlighted"]
        if len(hl) > 120:
            hl = hl[:117] + "..."
        print(f"  {i:3d}. [{h['style']}] \"{hl}\"")

    # ---- SUMMARY ----
    print(f"\n{'═'*70}")
    print("SUMMARY")
    print(f"{'═'*70}")
    print(f"  Offs:                    {len(offs)}")
    print(f"  Taglines:                {len(taglines)}")
    print(f"  Citations:               {len(citations)}")
    print(f"  Paragraphs w/ highlights:{len(highlights)}")
    print()


# -------------------------------------------------------------------
# Entry point
# -------------------------------------------------------------------

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "document.docx"
    results = analyze(path)
    print_report(results, path)
