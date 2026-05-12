"""
Render docs/listening_to_stars.md into the polished listening_to_stars.pdf
sitting in the project root.

Run from the project root:
    python docs/render_pdf.py
"""

import re
from pathlib import Path
from PIL import Image as PILImage

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Image,
    PageBreak, KeepTogether, Flowable, Preformatted,
)


# ── Paths ────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
MD_PATH  = ROOT / "docs" / "listening_to_stars.md"
PDF_PATH = ROOT / "listening_to_stars.pdf"

FONT_DIR = Path(
    "/var/lib/flatpak/runtime/org.kde.Platform/x86_64/6.8/"
    "e76835555fb61fabc9a3d4e80862bb1fdf3891baa1d1ab93d7f26219fa9f66d4/"
    "files/share/fonts/dejavu"
)
FONT_DIR_MONO = Path("/usr/share/fonts/TTF")  # fallback for mono


# ── Colours ──────────────────────────────────────────────────────────────────
DEEP_BLUE  = colors.HexColor("#1e3a5f")
RUST       = colors.HexColor("#8b3a1f")
SOFT_GREY  = colors.HexColor("#6b6b6b")
CREAM      = colors.HexColor("#f9f3e5")
LIGHT_GREY = colors.HexColor("#eeeeee")
INK        = colors.HexColor("#222222")
PALE_RULE  = colors.HexColor("#cccccc")


# ── Fonts ────────────────────────────────────────────────────────────────────
def register_fonts():
    pdfmetrics.registerFont(TTFont("Serif",       FONT_DIR / "DejaVuSerif.ttf"))
    pdfmetrics.registerFont(TTFont("Serif-B",     FONT_DIR / "DejaVuSerif-Bold.ttf"))
    pdfmetrics.registerFont(TTFont("Serif-I",     FONT_DIR / "DejaVuSerif-Italic.ttf"))
    pdfmetrics.registerFont(TTFont("Serif-BI",    FONT_DIR / "DejaVuSerif-BoldItalic.ttf"))
    pdfmetrics.registerFont(TTFont("Sans",        FONT_DIR / "DejaVuSans.ttf"))
    pdfmetrics.registerFont(TTFont("Sans-B",      FONT_DIR / "DejaVuSans-Bold.ttf"))
    pdfmetrics.registerFont(TTFont("Sans-I",      FONT_DIR / "DejaVuSans-Oblique.ttf"))
    pdfmetrics.registerFont(TTFont("Sans-BI",     FONT_DIR / "DejaVuSans-BoldOblique.ttf"))
    pdfmetrics.registerFont(TTFont("Mono",        FONT_DIR / "DejaVuSansMono.ttf"))
    pdfmetrics.registerFont(TTFont("Mono-B",      FONT_DIR / "DejaVuSansMono-Bold.ttf"))

    # Tell reportlab how to find italic/bold variants for inline <i>/<b> tags
    from reportlab.pdfbase.pdfmetrics import registerFontFamily
    registerFontFamily("Serif", normal="Serif", bold="Serif-B",
                       italic="Serif-I", boldItalic="Serif-BI")
    registerFontFamily("Sans", normal="Sans", bold="Sans-B",
                       italic="Sans-I", boldItalic="Sans-BI")
    registerFontFamily("Mono", normal="Mono", bold="Mono-B",
                       italic="Mono", boldItalic="Mono-B")


# ── Page geometry ────────────────────────────────────────────────────────────
PAGE_W, PAGE_H = A4
MARGIN = 2.2 * cm
FRAME_W = PAGE_W - 2 * MARGIN
FRAME_H = PAGE_H - 2 * MARGIN - 1.0 * cm  # leave room for header/footer


# ── Styles ───────────────────────────────────────────────────────────────────
def make_styles():
    body = ParagraphStyle(
        "body", fontName="Serif", fontSize=11.5, leading=17,
        textColor=INK, alignment=TA_JUSTIFY, spaceAfter=8,
    )
    body_left = ParagraphStyle(
        "body_left", parent=body, alignment=TA_LEFT,
    )
    intro = ParagraphStyle(
        "intro", parent=body, fontName="Serif-I", textColor=colors.HexColor("#333333"),
    )
    h2_title = ParagraphStyle(
        "h2_title", fontName="Serif-B", fontSize=24, leading=30,
        textColor=DEEP_BLUE, alignment=TA_LEFT, spaceAfter=8,
    )
    h2_kicker = ParagraphStyle(
        "h2_kicker", fontName="Sans-B", fontSize=10, leading=12,
        textColor=RUST, alignment=TA_LEFT, spaceAfter=6,
    )
    h2_plain = ParagraphStyle(
        "h2_plain", fontName="Serif-B", fontSize=20, leading=26,
        textColor=DEEP_BLUE, alignment=TA_LEFT, spaceAfter=12, spaceBefore=8,
    )
    h3 = ParagraphStyle(
        "h3", fontName="Sans-B", fontSize=13, leading=18,
        textColor=DEEP_BLUE, alignment=TA_LEFT,
        spaceBefore=14, spaceAfter=6,
    )
    h3_dramatic = ParagraphStyle(
        "h3_dramatic", fontName="Serif-B", fontSize=22, leading=28,
        textColor=RUST, alignment=TA_CENTER,
        spaceBefore=10, spaceAfter=10,
    )
    pullquote = ParagraphStyle(
        "pullquote", fontName="Serif-I", fontSize=12.5, leading=19,
        textColor=DEEP_BLUE, alignment=TA_LEFT,
        leftIndent=16, rightIndent=16,
        spaceBefore=8, spaceAfter=10,
    )
    callout_body = ParagraphStyle(
        "callout_body", fontName="Serif", fontSize=10.5, leading=15.5,
        textColor=INK, alignment=TA_LEFT,
        spaceBefore=0, spaceAfter=0,
    )
    caption = ParagraphStyle(
        "caption", fontName="Sans-I", fontSize=8.8, leading=12.5,
        textColor=SOFT_GREY, alignment=TA_LEFT,
        spaceBefore=4, spaceAfter=12,
        leftIndent=8, rightIndent=8,
    )
    bullet = ParagraphStyle(
        "bullet", parent=body, leftIndent=16, bulletIndent=4,
        firstLineIndent=0, alignment=TA_LEFT,
        spaceAfter=3, leading=15,
    )
    bullet_glossary = ParagraphStyle(
        "bullet_glossary", parent=bullet, fontSize=10.5, leading=14.5,
    )
    code_style = ParagraphStyle(
        "code_style", fontName="Mono", fontSize=8.8, leading=12,
        textColor=INK, alignment=TA_LEFT,
        leftIndent=10, rightIndent=10,
        spaceBefore=4, spaceAfter=4,
        backColor=LIGHT_GREY,
        borderColor=PALE_RULE, borderWidth=0,
        borderPadding=8,
    )
    cover_title = ParagraphStyle(
        "cover_title", fontName="Serif-B", fontSize=46, leading=54,
        textColor=DEEP_BLUE, alignment=TA_CENTER, spaceAfter=10,
    )
    cover_subtitle = ParagraphStyle(
        "cover_subtitle", fontName="Serif-I", fontSize=18, leading=24,
        textColor=SOFT_GREY, alignment=TA_CENTER, spaceAfter=20,
    )
    cover_date = ParagraphStyle(
        "cover_date", fontName="Sans", fontSize=10, leading=14,
        textColor=SOFT_GREY, alignment=TA_CENTER,
    )
    return {
        "body": body, "body_left": body_left, "intro": intro,
        "h2_title": h2_title, "h2_kicker": h2_kicker, "h2_plain": h2_plain,
        "h3": h3, "h3_dramatic": h3_dramatic,
        "pullquote": pullquote, "callout_body": callout_body,
        "caption": caption, "bullet": bullet, "bullet_glossary": bullet_glossary,
        "code": code_style,
        "cover_title": cover_title, "cover_subtitle": cover_subtitle,
        "cover_date": cover_date,
    }


# ── Inline markdown → ReportLab inline tags ─────────────────────────────────
def inline_md_to_rl(text):
    """Convert a single line of inline markdown to ReportLab paragraph markup."""
    # Code spans first (so we don't mess up other formatting inside them)
    text = re.sub(r"`([^`]+)`",
                  r'<font face="Mono" size="10">\1</font>', text)
    # Bold (**) — non-greedy
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    # Italic (*) — must not match the leftover * inside <b>
    text = re.sub(r"(?<![*\w])\*([^*\n]+?)\*(?!\w)", r"<i>\1</i>", text)
    # DejaVu Serif lacks ℓ (U+2113, SCRIPT SMALL L). Render it from Sans so it
    # doesn't show as a missing-glyph box. Bold/italic survive because Sans has
    # a registered family with the same weight/slant mappings.
    text = text.replace("ℓ", '<font face="Sans">ℓ</font>')
    # Escape stray ampersands and angle brackets that aren't already a tag.
    # ReportLab is picky: turn naked '&' into '&amp;', but our existing tags
    # are <b>, <i>, <font ...>, </b>, </i>, </font>, <super>, <sub>.
    # Easier approach: encode & first, then re-encode the entities inside our tags.
    return text


def escape_for_rl(text):
    """Pre-escape XML-special chars in raw text BEFORE we add markup tags."""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;"))


def md_line_to_rl(line):
    """Full inline conversion: escape, then re-introduce markup."""
    safe = escape_for_rl(line)
    return inline_md_to_rl(safe)


# ── Custom flowables ─────────────────────────────────────────────────────────
class HorizontalRule(Flowable):
    def __init__(self, width=80, thickness=1.0, color=RUST,
                 space_before=4, space_after=10):
        super().__init__()
        self.width = width
        self.thickness = thickness
        self.color = color
        self.space_before = space_before
        self.space_after = space_after

    def wrap(self, avail_w, avail_h):
        return self.width, self.thickness + self.space_before + self.space_after

    def draw(self):
        c = self.canv
        c.setStrokeColor(self.color)
        c.setLineWidth(self.thickness)
        y = self.space_after
        c.line(0, y, self.width, y)


class CalloutBox(Flowable):
    """Cream background, rust left border. Holds inner Paragraphs."""
    def __init__(self, paragraphs, frame_w, padding=10, border_w=3.5):
        super().__init__()
        self.paragraphs = paragraphs
        self.frame_w = frame_w
        self.padding = padding
        self.border_w = border_w
        self._wrapped_h = 0

    def wrap(self, avail_w, avail_h):
        inner_w = self.frame_w - 2 * self.padding - self.border_w
        h = 0
        for p in self.paragraphs:
            _, ph = p.wrap(inner_w, avail_h)
            h += ph
        self._wrapped_h = h + 2 * self.padding
        return self.frame_w, self._wrapped_h

    def draw(self):
        c = self.canv
        # Background
        c.setFillColor(CREAM)
        c.setStrokeColor(CREAM)
        c.rect(0, 0, self.frame_w, self._wrapped_h, fill=1, stroke=0)
        # Rust left border
        c.setFillColor(RUST)
        c.rect(0, 0, self.border_w, self._wrapped_h, fill=1, stroke=0)
        # Inner paragraphs, top down
        y = self._wrapped_h - self.padding
        x = self.border_w + self.padding
        inner_w = self.frame_w - 2 * self.padding - self.border_w
        for p in self.paragraphs:
            _, ph = p.wrap(inner_w, self._wrapped_h)
            y -= ph
            p.drawOn(c, x, y)


class PullQuote(Flowable):
    """Italic deep-blue text with rust left rule."""
    def __init__(self, paragraph, frame_w, padding_left=12, padding_right=8,
                 border_w=2):
        super().__init__()
        self.p = paragraph
        self.frame_w = frame_w
        self.pl = padding_left
        self.pr = padding_right
        self.bw = border_w
        self._h = 0

    def wrap(self, avail_w, avail_h):
        inner_w = self.frame_w - self.pl - self.pr - self.bw
        _, ph = self.p.wrap(inner_w, avail_h)
        self._h = ph + 12
        return self.frame_w, self._h

    def draw(self):
        c = self.canv
        c.setFillColor(RUST)
        c.rect(0, 6, self.bw, self._h - 6, fill=1, stroke=0)
        inner_w = self.frame_w - self.pl - self.pr - self.bw
        _, ph = self.p.wrap(inner_w, self._h)
        self.p.drawOn(c, self.bw + self.pl, self._h - 6 - ph)


# ── Page templates ───────────────────────────────────────────────────────────
def cover_page_canvas(canvas, doc):
    """Cover: nothing — no header, no footer, no page number."""
    pass


def body_page_canvas(canvas, doc):
    """Running header (top) and centred page number (bottom)."""
    canvas.saveState()
    # Header: left = LISTENING TO STARS, right = subtitle, with hairline rule
    canvas.setFont("Sans", 8)
    canvas.setFillColor(SOFT_GREY)
    header_y = PAGE_H - MARGIN + 12
    canvas.drawString(MARGIN, header_y, "LISTENING TO STARS")
    canvas.drawRightString(PAGE_W - MARGIN, header_y, "TESS amateur asteroseismology")
    canvas.setStrokeColor(PALE_RULE)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN, header_y - 4, PAGE_W - MARGIN, header_y - 4)

    # Footer: centred page number
    canvas.setFont("Sans", 9)
    canvas.setFillColor(SOFT_GREY)
    canvas.drawCentredString(PAGE_W / 2, MARGIN - 12, str(doc.page))
    canvas.restoreState()


# ── Markdown parser ─────────────────────────────────────────────────────────
def parse_markdown_to_blocks(text):
    """
    Returns a list of (kind, payload) tuples.

    kinds:
      "cover_title", "cover_subtitle"
      "h2_part" (kicker, title)
      "h2_plain" (title)
      "h3" (text)
      "h3_dramatic" (text)
      "para" (text)
      "list" (list of items)
      "code" (text)
      "figure" (path, caption)
      "pullquote" (text)
      "callout" (list of paragraph texts)
      "hrule" (none)
    """
    lines = text.splitlines()
    blocks = []
    i = 0
    n = len(lines)

    # Strip trailing/leading blank lines
    while lines and not lines[0].strip():
        lines.pop(0); n -= 1

    seen_top_title = False
    seen_top_subtitle = False

    while i < n:
        line = lines[i]
        stripped = line.strip()

        # Blank — skip
        if not stripped:
            i += 1
            continue

        # Top-level title (only first one is the cover title)
        if stripped.startswith("# ") and not seen_top_title:
            blocks.append(("cover_title", stripped[2:].strip()))
            seen_top_title = True
            i += 1
            continue

        # H2: distinguish "Part N: ..." from plain "## Title"
        if stripped.startswith("## "):
            heading = stripped[3:].strip()
            # Cover subtitle: the first H2 after the cover title, before the first ---
            if seen_top_title and not seen_top_subtitle and not heading.startswith("Part "):
                # Check if it precedes the first --- (cover separator)
                # We treat the FIRST H2 after the title as the subtitle.
                # Then any H2 right after the first --- block is a regular plain section.
                blocks.append(("cover_subtitle", heading))
                seen_top_subtitle = True
                i += 1
                continue

            m = re.match(r"^Part (\d+):\s+(.+)$", heading)
            if m:
                blocks.append(("h2_part", (f"PART {m.group(1)}", m.group(2))))
            else:
                blocks.append(("h2_plain", heading))
            i += 1
            continue

        # H3
        if stripped.startswith("### "):
            heading = stripped[4:].strip()
            # Detect "### **K0III**" dramatic
            m = re.fullmatch(r"\*\*(.+?)\*\*", heading)
            if m and len(m.group(1)) <= 20:
                blocks.append(("h3_dramatic", m.group(1)))
            else:
                blocks.append(("h3", heading))
            i += 1
            continue

        # Horizontal rule
        if stripped == "---":
            blocks.append(("hrule", None))
            i += 1
            continue

        # Code fence
        if stripped.startswith("```"):
            lang = stripped[3:].strip()  # noqa
            j = i + 1
            buf = []
            while j < n and not lines[j].strip().startswith("```"):
                buf.append(lines[j])
                j += 1
            blocks.append(("code", "\n".join(buf)))
            i = j + 1
            continue

        # Block quote — collect contiguous lines starting with '>'
        if stripped.startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                # Strip leading "> " (handle blank-line-with-just-> too)
                stripped_line = lines[i].strip()
                if stripped_line == ">":
                    buf.append("")
                else:
                    buf.append(stripped_line[1:].lstrip())
                i += 1
            # Decide pullquote vs callout
            joined = "\n".join(buf).strip()
            # Find leading bold token: **WORD.**
            m = re.match(r"^\*\*([^*]+?)\*\*", joined)
            is_callout = False
            if m:
                lead = m.group(1)
                # All-caps OR matches HD\d+ OR ASTEROSEISMIC
                if (re.fullmatch(r"[A-Z0-9 ./'’-]+\.?", lead)
                        or re.match(r"HD\s*\d+", lead)
                        or "ASTEROSEISMIC" in lead.upper()):
                    is_callout = True
            if is_callout:
                # Split callout into paragraphs by blank lines
                paras = [p.strip() for p in re.split(r"\n\s*\n", joined) if p.strip()]
                # If only one paragraph but it has internal newlines, treat each
                # newline-separated chunk as a separate paragraph for spacing.
                if len(paras) == 1 and "\n" in paras[0]:
                    paras = [p.strip() for p in paras[0].split("\n") if p.strip()]
                blocks.append(("callout", paras))
            else:
                # Pull-quote: collapse newlines to spaces (single italic block)
                pq_text = re.sub(r"\s+", " ", joined)
                blocks.append(("pullquote", pq_text))
            continue

        # Figure marker: [FIGURE: path]
        m = re.match(r"^\[FIGURE:\s*(.+?)\]\s*$", stripped)
        if m:
            fig_path = m.group(1).strip()
            # Next non-blank line should be the italic caption
            j = i + 1
            while j < n and not lines[j].strip():
                j += 1
            cap = ""
            if j < n:
                cap_line = lines[j].strip()
                m2 = re.match(r"^\*(.+)\*$", cap_line)
                if m2:
                    cap = m2.group(1).strip()
                    j += 1
            blocks.append(("figure", (fig_path, cap)))
            i = j
            continue

        # Bullet list
        if stripped.startswith("- "):
            items = []
            while i < n and lines[i].lstrip().startswith("- "):
                items.append(lines[i].lstrip()[2:])
                i += 1
            blocks.append(("list", items))
            continue

        # Numbered list (1. 2. 3.)
        if re.match(r"^\d+\.\s+", stripped):
            items = []
            while i < n and re.match(r"^\s*\d+\.\s+", lines[i]):
                m = re.match(r"^\s*\d+\.\s+(.*)$", lines[i])
                items.append(m.group(1))
                i += 1
            blocks.append(("numlist", items))
            continue

        # Default: paragraph (collect contiguous non-blank lines)
        buf = [line]
        i += 1
        while i < n and lines[i].strip() and not _starts_block(lines[i]):
            buf.append(lines[i])
            i += 1
        para_text = " ".join(s.strip() for s in buf)
        blocks.append(("para", para_text))

    return blocks


def _starts_block(line):
    s = line.strip()
    return (
        s.startswith("# ") or s.startswith("## ") or s.startswith("### ")
        or s.startswith(">") or s.startswith("- ") or s == "---"
        or s.startswith("```") or s.startswith("[FIGURE:")
        or re.match(r"^\d+\.\s+", s)
    )


# ── Block → flowable ─────────────────────────────────────────────────────────
def figure_flowable(rel_path, caption_text, styles):
    """Build a (figure + caption) KeepTogether flowable."""
    abs_path = ROOT / rel_path
    if not abs_path.exists():
        # Render a placeholder so missing assets are visible, not silently dropped
        warn = Paragraph(
            f"<b>[missing figure: {rel_path}]</b>",
            ParagraphStyle("missing", parent=styles["caption"], textColor=RUST),
        )
        return KeepTogether([warn])

    # Compute display size: cap width at frame width, scale aspect ratio
    with PILImage.open(abs_path) as im:
        iw, ih = im.size
    max_w = FRAME_W
    max_h = FRAME_H * 0.62  # never let a single figure dominate the page
    aspect = ih / iw
    disp_w = max_w
    disp_h = disp_w * aspect
    if disp_h > max_h:
        disp_h = max_h
        disp_w = disp_h / aspect
    img = Image(str(abs_path), width=disp_w, height=disp_h)
    img.hAlign = "CENTER"

    parts = [img]
    if caption_text:
        cap_p = Paragraph(inline_md_to_rl(escape_for_rl(caption_text)), styles["caption"])
        parts.append(cap_p)
    return KeepTogether(parts)


def render_blocks(blocks, styles):
    story = []
    cover_done = False
    just_after_cover = False  # used to skip the FIRST page break after the cover

    for idx, (kind, payload) in enumerate(blocks):
        if kind == "cover_title":
            story.append(Spacer(1, 5 * cm))
            story.append(Paragraph(escape_for_rl(payload), styles["cover_title"]))
            continue

        if kind == "cover_subtitle":
            story.append(Spacer(1, 0.5 * cm))
            story.append(Paragraph(escape_for_rl(payload), styles["cover_subtitle"]))
            # Push the "May 2026" date toward the bottom of the cover.
            story.append(Spacer(1, 12 * cm))
            story.append(Paragraph("May 2026", styles["cover_date"]))
            # Switch the next page to the body template and break out of the
            # cover. The flag below tells the first h2 to skip its own
            # PageBreak so we don't waste a blank page in between.
            story.append(NextPageTemplate("body"))
            story.append(PageBreak())
            cover_done = True
            just_after_cover = True
            continue

        if kind == "hrule":
            # Skip the cover separator (right after subtitle) — already handled
            if not cover_done:
                continue
            # Otherwise: just a thin pale rule for in-body section separators
            # We use it sparingly — most of the spacing comes from H2 page breaks.
            story.append(Spacer(1, 4))
            continue

        if kind == "h2_part":
            kicker, title = payload
            if just_after_cover:
                just_after_cover = False
            else:
                story.append(PageBreak())
            story.append(Spacer(1, 0.4 * cm))
            story.append(Paragraph(kicker, styles["h2_kicker"]))
            story.append(Paragraph(escape_for_rl(title), styles["h2_title"]))
            story.append(HorizontalRule(width=70, color=RUST,
                                        thickness=1.2,
                                        space_before=0, space_after=10))
            continue

        if kind == "h2_plain":
            if just_after_cover:
                just_after_cover = False
            else:
                story.append(PageBreak())
            story.append(Spacer(1, 0.4 * cm))
            story.append(Paragraph(escape_for_rl(payload), styles["h2_plain"]))
            story.append(HorizontalRule(width=70, color=RUST,
                                        thickness=1.2,
                                        space_before=0, space_after=10))
            continue

        if kind == "h3":
            story.append(Paragraph(md_line_to_rl(payload), styles["h3"]))
            continue

        if kind == "h3_dramatic":
            story.append(Spacer(1, 6))
            story.append(Paragraph(escape_for_rl(payload), styles["h3_dramatic"]))
            story.append(Spacer(1, 4))
            continue

        if kind == "para":
            story.append(Paragraph(md_line_to_rl(payload), styles["body"]))
            continue

        if kind == "pullquote":
            p = Paragraph(md_line_to_rl(payload), styles["pullquote"])
            story.append(PullQuote(p, FRAME_W))
            continue

        if kind == "callout":
            paras = []
            for ptxt in payload:
                paras.append(Paragraph(md_line_to_rl(ptxt), styles["callout_body"]))
                paras.append(Spacer(1, 4))
            if paras and isinstance(paras[-1], Spacer):
                paras.pop()
            story.append(CalloutBox(paras, FRAME_W))
            story.append(Spacer(1, 6))
            continue

        if kind == "list":
            # In glossary section, items often use **term** bold leading.
            # We render with a simple bullet.
            for item in payload:
                story.append(Paragraph(
                    "• " + md_line_to_rl(item),
                    styles["bullet_glossary"],
                ))
            story.append(Spacer(1, 4))
            continue

        if kind == "numlist":
            for n, item in enumerate(payload, 1):
                story.append(Paragraph(
                    f"<b>{n}.</b> " + md_line_to_rl(item),
                    styles["bullet"],
                ))
            story.append(Spacer(1, 4))
            continue

        if kind == "code":
            # Use a Preformatted block so newlines and indents survive.
            # ReportLab's Preformatted respects whitespace and sets background
            # via its style. Wrap in a Paragraph-like style.
            story.append(Preformatted(payload, styles["code"]))
            continue

        if kind == "figure":
            rel_path, cap = payload
            story.append(figure_flowable(rel_path, cap, styles))
            continue

    return story


# ── DocTemplate with two page templates: cover (no decoration) + body ────────
from reportlab.platypus.doctemplate import NextPageTemplate


def build_pdf():
    register_fonts()
    styles = make_styles()

    md_text = MD_PATH.read_text(encoding="utf-8")
    blocks = parse_markdown_to_blocks(md_text)

    doc = BaseDocTemplate(
        str(PDF_PATH),
        pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN,
        title="Listening to Stars",
        author="",
    )

    cover_frame = Frame(MARGIN, MARGIN, FRAME_W, PAGE_H - 2 * MARGIN,
                        id="cover", showBoundary=0,
                        leftPadding=0, rightPadding=0,
                        topPadding=0, bottomPadding=0)
    body_frame = Frame(MARGIN, MARGIN, FRAME_W, PAGE_H - 2 * MARGIN - 0.5 * cm,
                       id="body", showBoundary=0,
                       leftPadding=0, rightPadding=0,
                       topPadding=0, bottomPadding=0)

    doc.addPageTemplates([
        PageTemplate(id="cover", frames=[cover_frame], onPage=cover_page_canvas),
        PageTemplate(id="body",  frames=[body_frame],  onPage=body_page_canvas),
    ])

    story = render_blocks(blocks, styles)
    doc.build(story)
    print(f"Wrote {PDF_PATH}  ({PDF_PATH.stat().st_size/1024:.1f} KB)")


if __name__ == "__main__":
    build_pdf()
