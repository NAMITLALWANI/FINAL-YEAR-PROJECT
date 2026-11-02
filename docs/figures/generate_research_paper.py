"""Generate figures and the styled PDF for docs/research-paper.md.

Requires Pillow and ReportLab. Run with a Python environment containing both:
    python docs/figures/generate_research_paper.py
"""
from __future__ import annotations

import html
import re
from pathlib import Path

from PIL import Image as PILImage, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageTemplate,
    PageBreak,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[2]
PAPER = ROOT / "docs" / "research-paper.md"
FIGURES = ROOT / "docs" / "figures"
OUTPUT = ROOT / "output" / "pdf" / "research-paper-final.pdf"

NAVY = "#16324F"
BLUE = "#246A9A"
TEAL = "#258A83"
GOLD = "#D39436"
INK = "#243746"
MUTED = "#637381"
PALE = "#EEF4F7"
WHITE = "#FFFFFF"

FONT_REG = "/System/Library/Fonts/Supplemental/Arial.ttf"
FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT_ITALIC = "/System/Library/Fonts/Supplemental/Arial Italic.ttf"


def pil_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size=size)


def draw_wrapped(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str,
                 font: ImageFont.FreeTypeFont, max_width: int,
                 fill: str = INK, spacing: int = 8, align: str = "left") -> int:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if current and draw.textbbox((0, 0), trial, font=font)[2] > max_width:
            lines.append(current)
            current = word
        else:
            current = trial
    if current:
        lines.append(current)
    x, y = xy
    for line in lines:
        width = draw.textbbox((0, 0), line, font=font)[2]
        dx = (max_width - width) // 2 if align == "center" else 0
        draw.text((x + dx, y), line, font=font, fill=fill)
        y += font.size + spacing
    return y


def rounded_node(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int],
                 title: str, subtitle: str = "", *, fill: str = WHITE,
                 outline: str = BLUE, title_color: str = NAVY,
                 title_size: int = 38, body_size: int = 29) -> None:
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, radius=24, fill=fill, outline=outline, width=5)
    title_font = pil_font(FONT_BOLD, title_size)
    body_font = pil_font(FONT_REG, body_size)
    title_lines = title.split("\n")
    subtitle_lines = subtitle.split("\n") if subtitle else []
    all_lines = [(line, title_font, title_color) for line in title_lines]
    all_lines += [(line, body_font, MUTED) for line in subtitle_lines]
    heights = [font.size + 8 for _, font, _ in all_lines]
    y = y0 + max(12, (y1 - y0 - sum(heights)) // 2)
    for line, font, color in all_lines:
        width = draw.textbbox((0, 0), line, font=font)[2]
        draw.text((x0 + (x1 - x0 - width) / 2, y), line, font=font, fill=color)
        y += font.size + 8


def arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int],
          color: str = BLUE, width: int = 7, dashed: bool = False) -> None:
    x1, y1 = start
    x2, y2 = end
    if dashed:
        import math
        length = math.hypot(x2 - x1, y2 - y1)
        if length:
            ux, uy = (x2 - x1) / length, (y2 - y1) / length
            pos = 0.0
            while pos < length - 28:
                stop = min(pos + 22, length - 28)
                draw.line((x1 + ux * pos, y1 + uy * pos,
                           x1 + ux * stop, y1 + uy * stop), fill=color, width=width)
                pos += 38
    else:
        draw.line((x1, y1, x2, y2), fill=color, width=width)
    import math
    angle = math.atan2(y2 - y1, x2 - x1)
    size = 26
    left = (x2 - size * math.cos(angle - math.pi / 6),
            y2 - size * math.sin(angle - math.pi / 6))
    right = (x2 - size * math.cos(angle + math.pi / 6),
             y2 - size * math.sin(angle + math.pi / 6))
    draw.polygon([(x2, y2), left, right], fill=color)


def figure_architecture(path: Path) -> None:
    w, h = 2400, 1460
    im = PILImage.new("RGB", (w, h), WHITE)
    d = ImageDraw.Draw(im)
    d.text((80, 48), "System architecture and decision boundary",
           font=pil_font(FONT_BOLD, 58), fill=NAVY)
    d.text((82, 122), "Relational storage is authoritative; retrieval provides review evidence.",
           font=pil_font(FONT_REG, 34), fill=MUTED)

    top_y0, top_y1 = 250, 500
    top_x = [70, 520, 970, 1420, 1870]
    top_titles = ["Source providers", "Normalize +\ndeduplicate", "Relational database", "Explicit index\nbuilder", "Persistent Chroma"]
    top_subs = ["OpenAlex / DBLP /\nCrossref / arXiv", "Canonical publication\nrecords", "Canonical data +\nsource provenance", "Rebuildable projection", "Semantic index"]
    for x, title, subtitle in zip(top_x, top_titles, top_subs):
        rounded_node(d, (x, top_y0, x + 390, top_y1), title, subtitle,
                     fill=PALE if title == "Relational database" else WHITE,
                     outline=TEAL if title == "Relational database" else BLUE,
                     title_size=34, body_size=27)
    for i in range(4):
        arrow(d, (top_x[i] + 398, 375), (top_x[i + 1] - 15, 375))

    d.text((78, 575), "IDENTITY DECISION PATH", font=pil_font(FONT_BOLD, 30), fill=TEAL)
    identity_x = [1870, 1420, 970, 520, 70]
    identity_titles = ["Author query", "Candidate generation", "Resolver V1", "Decision status", "Review interface"]
    identity_subs = ["Name + context", "OpenAlex profiles", "Deterministic evidence\nscoring", "Auto / manual /\nunresolved", "Human selection or\nunresolved outcome"]
    for x, title, subtitle in zip(identity_x, identity_titles, identity_subs):
        rounded_node(d, (x, 650, x + 390, 890), title, subtitle,
                     fill=PALE if title == "Resolver V1" else WHITE,
                     outline=TEAL if title == "Resolver V1" else BLUE,
                     title_size=32, body_size=26)
    for i in range(4):
        arrow(d, (identity_x[i] - 15, 770), (identity_x[i + 1] + 398, 770))

    d.text((78, 965), "EVIDENCE SUPPORT PATH - CONTEXT ONLY", font=pil_font(FONT_BOLD, 30), fill=GOLD)
    evidence_x = [1870, 1420, 970, 520, 70]
    evidence_titles = ["Semantic retrieval", "Gemini (optional)", "Citation-ID check", "Evidence context", "Review interface"]
    evidence_subs = ["Top-k + exact\nmetadata filters", "Bounded retrieved\nrecords", "Validated IDs or\ndeterministic fallback", "Evidence only; no\nidentity authority", "Reviewer sees both\npaths here"]
    for x, title, subtitle in zip(evidence_x, evidence_titles, evidence_subs):
        rounded_node(d, (x, 1040, x + 390, 1280), title, subtitle,
                     fill="#FFF8EB" if title == "Gemini (optional)" else WHITE,
                     outline=GOLD, title_size=31, body_size=25)
    for i in range(4):
        arrow(d, (evidence_x[i] - 15, 1160), (evidence_x[i + 1] + 398, 1160), color=GOLD)
    # Route the Chroma-to-retrieval edge around the decision lane so the
    # diagram makes the non-interference boundary visually explicit.
    d.line((2260, 375, 2350, 375, 2350, 1160), fill=GOLD, width=5)
    arrow(d, (2350, 1160), (2262, 1160), color=GOLD, width=5)
    d.text((1040, 1300), "Evidence path is separate from identity scoring and status decisions.",
           font=pil_font(FONT_BOLD, 30), fill=NAVY)
    im.save(path, dpi=(300, 300), optimize=True)


def figure_inventory(path: Path) -> None:
    w, h = 2000, 950
    im = PILImage.new("RGB", (w, h), WHITE)
    d = ImageDraw.Draw(im)
    d.text((100, 55), "Local backend database inventory", font=pil_font(FONT_BOLD, 62), fill=NAVY)
    d.text((104, 140), "Read-only counts checked 15 October 2026 - not a benchmark or performance chart",
           font=pil_font(FONT_REG, 30), fill=MUTED)
    chart_x, chart_y, chart_w = 600, 300, 1240
    max_value = 2300
    for value in range(0, 2301, 500):
        x = chart_x + chart_w * value / max_value
        d.line((x, chart_y - 20, x, 770), fill="#DCE5EA", width=2)
        d.text((x - 20, 785), f"{value:,}", font=pil_font(FONT_REG, 24), fill=MUTED)
    labels = [("Canonical publications", 696, BLUE), ("Source-record rows", 2186, TEAL)]
    for i, (label, value, color) in enumerate(labels):
        y = 375 + i * 220
        d.text((100, y + 30), label, font=pil_font(FONT_BOLD, 36), fill=INK)
        bar_end = chart_x + chart_w * value / max_value
        d.rounded_rectangle((chart_x, y, bar_end, y + 100), radius=18, fill=color)
        d.text((bar_end + 20, y + 25), f"{value:,}", font=pil_font(FONT_BOLD, 34), fill=NAVY)
    d.rounded_rectangle((100, 850, 1900, 910), radius=18, fill=PALE)
    d.text((130, 862), "SQLite integrity: ok  |  Mutable application state  |  Independent labels: none",
           font=pil_font(FONT_BOLD, 27), fill=NAVY)
    im.save(path, dpi=(300, 300), optimize=True)


def figure_evaluation(path: Path) -> None:
    w, h = 2400, 1520
    im = PILImage.new("RGB", (w, h), WHITE)
    d = ImageDraw.Draw(im)
    d.text((80, 48), "Planned annotation and evaluation workflow",
           font=pil_font(FONT_BOLD, 58), fill=NAVY)
    d.text((82, 122), "Identity and retrieval judgments are collected separately, then evaluated on frozen snapshots.",
           font=pil_font(FONT_REG, 32), fill=MUTED)

    d.text((80, 230), "IDENTITY BENCHMARK", font=pil_font(FONT_BOLD, 31), fill=TEAL)
    ids = [70, 525, 980, 1435, 1890]
    titles = ["10-query pilot", "Two independent\nsource reviews", "Rubric refinement\n+ adjudication", "100+ queries\nsource-verified", "Identity-group\nsplit freeze"]
    subs = ["Protocol only;\nnot test data", "Confidence + evidence\nreferences", "Retain uncertain\ncases", "Resolved / unresolved /\nuncertain", "Variants stay in one\nsplit"]
    for x, title, sub in zip(ids, titles, subs):
        rounded_node(d, (x, 300, x + 390, 545), title, sub,
                     fill=PALE, outline=TEAL, title_size=31, body_size=24)
    for i in range(4):
        arrow(d, (ids[i] + 398, 422), (ids[i + 1] - 15, 422), color=TEAL)

    d.text((80, 650), "SEPARATE RETRIEVAL RELEVANCE SET", font=pil_font(FONT_BOLD, 31), fill=BLUE)
    rids = [70, 525, 980, 1435, 1890]
    rtitles = ["Retrieval queries", "Freeze publication\npool", "Blind dual grading", "Adjudicate and\ncomplete pool", "Relevance labels\n0 / 1 / 2"]
    rsubs = ["Separate from\nidentity labels", "Protocol + canonical\npublication IDs", "No system/rank\nattribution", "Every pooled pair\njudged", "Missing judgment is\nnot irrelevant"]
    for x, title, sub in zip(rids, rtitles, rsubs):
        rounded_node(d, (x, 720, x + 390, 965), title, sub,
                     fill="#F1F6FB", outline=BLUE, title_size=30, body_size=24)
    for i in range(4):
        arrow(d, (rids[i] + 398, 842), (rids[i + 1] - 15, 842), color=BLUE)

    d.text((80, 1070), "FROZEN, REPRODUCIBLE EXPERIMENT", font=pil_font(FONT_BOLD, 31), fill=GOLD)
    ex = [170, 700, 1230, 1760]
    et = ["Immutable DB + index\nsnapshots and manifest", "Read-only V1 replay\n+ retrieval capture", "Versioned predictions\nwith input hashes", "Fixed metrics, error\nanalysis, final test"]
    es = ["Candidate IDs + split\nfreeze validated", "No app DB writes;\nno test-set tuning", "Labels, snapshots,\ncode/config traceable", "Report negative and\ninconclusive outcomes"]
    for x, title, sub in zip(ex, et, es):
        rounded_node(d, (x, 1140, x + 430, 1370), title, sub,
                     fill="#FFF8EB", outline=GOLD, title_size=29, body_size=23)
    for i in range(3):
        arrow(d, (ex[i] + 438, 1255), (ex[i + 1] - 15, 1255), color=GOLD)
    d.text((80, 1430), "Current state: no real annotations, frozen manifest, or research predictions have been created.",
           font=pil_font(FONT_BOLD, 28), fill=NAVY)
    im.save(path, dpi=(300, 300), optimize=True)


def ascii_dashes(text: str) -> str:
    for char in ("\u2010", "\u2011", "\u2012", "\u2013", "\u2014", "\u2212"):
        text = text.replace(char, "-")
    return text


def inline_markup(text: str) -> str:
    text = ascii_dashes(text)
    token = re.compile(r"\[([^\]]+)\]\(([^)]+)\)|\*\*(.+?)\*\*|`([^`]+)`|\*(.+?)\*")
    out: list[str] = []
    pos = 0
    for match in token.finditer(text):
        out.append(html.escape(text[pos:match.start()]))
        if match.group(1) is not None:
            label = html.escape(match.group(1))
            url = html.escape(ascii_dashes(match.group(2)), quote=True)
            out.append(f'<link href="{url}" color="#246A9A">{label}</link>')
        elif match.group(3) is not None:
            out.append(f"<b>{html.escape(match.group(3))}</b>")
        elif match.group(4) is not None:
            out.append(f'<font name="Arial" color="#34495E">{html.escape(match.group(4))}</font>')
        else:
            out.append(f"<i>{html.escape(match.group(5))}</i>")
        pos = match.end()
    out.append(html.escape(text[pos:]))
    return "".join(out)


def make_styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("PaperTitle", parent=base["Title"], fontName="Arial-Bold",
                                fontSize=24, leading=29, textColor=colors.HexColor(NAVY),
                                alignment=TA_CENTER, spaceAfter=14),
        "meta": ParagraphStyle("Meta", parent=base["Normal"], fontName="Arial",
                               fontSize=9.5, leading=13, textColor=colors.HexColor(MUTED),
                               alignment=TA_CENTER, spaceAfter=8),
        "abstract_head": ParagraphStyle("AbstractHead", parent=base["Heading2"],
                                        fontName="Arial-Bold", fontSize=13, leading=16,
                                        textColor=colors.HexColor(TEAL), spaceBefore=10, spaceAfter=7),
        "abstract": ParagraphStyle("Abstract", parent=base["BodyText"], fontName="Arial",
                                    fontSize=9.5, leading=13.5, alignment=TA_JUSTIFY,
                                    textColor=colors.HexColor(INK), spaceAfter=10),
        "keywords": ParagraphStyle("Keywords", parent=base["BodyText"], fontName="Arial",
                                   fontSize=9, leading=12, textColor=colors.HexColor(MUTED),
                                   spaceBefore=3),
        "h1": ParagraphStyle("Section", parent=base["Heading1"], fontName="Arial-Bold",
                             fontSize=15, leading=19, textColor=colors.HexColor(NAVY),
                             spaceBefore=16, spaceAfter=7, keepWithNext=True),
        "h2": ParagraphStyle("Subsection", parent=base["Heading2"], fontName="Arial-Bold",
                             fontSize=11.5, leading=14, textColor=colors.HexColor(TEAL),
                             spaceBefore=11, spaceAfter=5, keepWithNext=True),
        "h3": ParagraphStyle("Subsubsection", parent=base["Heading3"], fontName="Arial-Bold",
                             fontSize=10.5, leading=13, textColor=colors.HexColor(BLUE),
                             spaceBefore=8, spaceAfter=4, keepWithNext=True),
        "body": ParagraphStyle("Body", parent=base["BodyText"], fontName="Arial",
                               fontSize=9.3, leading=13.2, alignment=TA_JUSTIFY,
                               textColor=colors.HexColor(INK), spaceAfter=7),
        "list": ParagraphStyle("List", parent=base["BodyText"], fontName="Arial",
                               fontSize=9.1, leading=12.5, alignment=TA_LEFT,
                               textColor=colors.HexColor(INK), spaceAfter=3),
        "bullet": ParagraphStyle("Bullet", parent=base["BodyText"], fontName="Arial",
                                  fontSize=9.1, leading=12.5, alignment=TA_LEFT,
                                  leftIndent=14, firstLineIndent=-10,
                                  textColor=colors.HexColor(INK), spaceAfter=3),
        "caption": ParagraphStyle("Caption", parent=base["BodyText"], fontName="Arial-Italic",
                                  fontSize=8.3, leading=10.5, alignment=TA_CENTER,
                                  textColor=colors.HexColor(MUTED), spaceBefore=3, spaceAfter=10),
        "table_head": ParagraphStyle("TableHead", parent=base["BodyText"], fontName="Arial-Bold",
                                      fontSize=8, leading=10, textColor=colors.white),
        "table": ParagraphStyle("Table", parent=base["BodyText"], fontName="Arial",
                                fontSize=7.7, leading=9.7, textColor=colors.HexColor(INK)),
        "ref": ParagraphStyle("Reference", parent=base["BodyText"], fontName="Arial",
                              fontSize=8.5, leading=11.2, leftIndent=16, firstLineIndent=-16,
                              textColor=colors.HexColor(INK), spaceAfter=5),
    }


class PaperDoc(BaseDocTemplate):
    def __init__(self, filename: str, **kwargs):
        super().__init__(filename, pagesize=letter, leftMargin=58, rightMargin=58,
                         topMargin=58, bottomMargin=52, title="Hybrid Academic Metadata Aggregator and Evidence-Guided Author Entity Resolution System",
                         author="Research-in-progress draft", **kwargs)
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height,
                      leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, id="body")
        self.addPageTemplates([PageTemplate(id="paper", frames=[frame], onPage=self._decorate)])

    def _decorate(self, canvas, doc):
        canvas.saveState()
        if doc.page > 1:
            canvas.setStrokeColor(colors.HexColor("#D9E3E8"))
            canvas.setLineWidth(0.5)
            canvas.line(self.leftMargin, letter[1] - 39, letter[0] - self.rightMargin, letter[1] - 39)
            canvas.setFont("Arial", 7.5)
            canvas.setFillColor(colors.HexColor(MUTED))
            canvas.drawString(self.leftMargin, letter[1] - 31, "SCHOLARLY METADATA AND EVIDENCE-GUIDED AUTHOR REVIEW")
        canvas.setStrokeColor(colors.HexColor("#D9E3E8"))
        canvas.setLineWidth(0.5)
        canvas.line(self.leftMargin, 38, letter[0] - self.rightMargin, 38)
        canvas.setFont("Arial", 7.5)
        canvas.setFillColor(colors.HexColor(MUTED))
        canvas.drawString(self.leftMargin, 25, "Research-in-progress draft | 15 October 2026")
        canvas.drawRightString(letter[0] - self.rightMargin, 25, f"Page {doc.page}")
        canvas.restoreState()


def parse_markdown(markdown: str, styles: dict, content_width: float):
    lines = markdown.splitlines()
    story = []
    i = 0
    in_references = False
    while i < len(lines):
        raw = lines[i].strip()
        if not raw:
            i += 1
            continue
        if raw.startswith("## References"):
            in_references = True
            story.append(PageBreak())
        if raw.startswith("# "):
            style = styles["h1"]
            story.append(Paragraph(inline_markup(raw[2:]), style))
            i += 1
            continue
        if raw.startswith("### "):
            story.append(Paragraph(inline_markup(raw[4:]), styles["h3"]))
            i += 1
            continue
        if raw.startswith("## "):
            story.append(Paragraph(inline_markup(raw[3:]), styles["h1"]))
            i += 1
            continue
        image_match = re.match(r"!\[(.*?)\]\((.*?)\)$", raw)
        if image_match:
            alt, relative = image_match.groups()
            image_path = (PAPER.parent / relative).resolve()
            if not image_path.exists():
                raise FileNotFoundError(image_path)
            img = PILImage.open(image_path)
            iw, ih = img.size
            draw_width = min(content_width, 500)
            draw_height = draw_width * ih / iw
            picture = Image(str(image_path), width=draw_width, height=draw_height)
            caption = Paragraph(inline_markup(alt), styles["caption"])
            story.append(KeepTogether([Spacer(1, 4), picture, caption]))
            i += 1
            continue
        if raw.startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            rows = []
            for row in table_lines:
                cells = [cell.strip() for cell in row.strip("|").split("|")]
                if cells and all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells):
                    continue
                rows.append(cells)
            if rows:
                columns = max(map(len, rows))
                data = []
                for r, row in enumerate(rows):
                    padded = row + [""] * (columns - len(row))
                    table_style = styles["table_head"] if r == 0 else styles["table"]
                    data.append([Paragraph(inline_markup(cell), table_style) for cell in padded])
                widths = [120, 119, content_width - 239] if columns == 3 else [content_width / columns] * columns
                table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT", splitByRow=1)
                table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(NAVY)),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F5F8FA")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F7F9")]),
                    ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CAD6DD")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]))
                story.extend([Spacer(1, 3), table, Spacer(1, 9)])
            continue
        if raw.startswith("- ") or re.match(r"\d+\. ", raw):
            ordered = bool(re.match(r"\d+\. ", raw))
            items = []
            item_texts = []
            while i < len(lines):
                item = lines[i].strip()
                if ordered and re.match(r"\d+\. ", item):
                    item = re.sub(r"^\d+\. ", "", item)
                elif not ordered and item.startswith("- "):
                    item = item[2:]
                else:
                    break
                item_texts.append(item)
                items.append(ListItem(Paragraph(inline_markup(item), styles["list"]), leftIndent=12))
                i += 1
            if in_references and ordered:
                for j, item_text in enumerate(item_texts, 1):
                    story.append(Paragraph(f"{j}. {inline_markup(item_text)}", styles["ref"]))
            elif not ordered:
                for item_text in item_texts:
                    story.append(Paragraph(f"â¢ {inline_markup(item_text)}", styles["bullet"]))
            else:
                story.append(ListFlowable(items, bulletType="1", start="1",
                                          leftIndent=19, bulletFontName="Arial-Bold",
                                          bulletFontSize=8, bulletColor=colors.HexColor(TEAL),
                                          spaceAfter=7))
            continue
        if raw.startswith("**Research-in-progress draft"):
            story.append(Paragraph(inline_markup(raw), styles["meta"]))
            i += 1
            continue
        if raw.startswith("**Author(s):**"):
            story.append(Paragraph(inline_markup(raw), styles["meta"]))
            i += 1
            continue
        if raw.startswith("**Keywords:**"):
            story.append(Paragraph(inline_markup(raw), styles["keywords"]))
            i += 1
            continue
        if raw.startswith("**Figure "):
            story.append(Paragraph(inline_markup(raw), styles["caption"]))
            i += 1
            continue

        paragraph_lines = [raw]
        i += 1
        while i < len(lines):
            next_line = lines[i].strip()
            if (not next_line or next_line.startswith(("#", "|", "![", "```", "- ", "**Figure "))
                    or re.match(r"\d+\. ", next_line)):
                break
            paragraph_lines.append(next_line)
            i += 1
        text = " ".join(paragraph_lines)
        if text.startswith("**Abstract:**"):
            text = text.replace("**Abstract:**", "<b>Abstract:</b>", 1)
        story.append(Paragraph(inline_markup(text), styles["body"]))
    return story


def make_title_page(markdown: str, styles: dict):
    lines = markdown.splitlines()
    title = next(line[2:].strip() for line in lines if line.startswith("# "))
    status = next(line.strip("* ") for line in lines if line.startswith("**Research-in-progress draft"))
    authors = next(line for line in lines if line.startswith("**Author(s):**"))
    abstract_start = lines.index("## Abstract") + 1
    abstract_lines = []
    i = abstract_start
    while i < len(lines) and not lines[i].startswith("**Keywords:**"):
        if lines[i].strip():
            abstract_lines.append(lines[i].strip())
        i += 1
    keywords = next(line for line in lines if line.startswith("**Keywords:**"))
    return [
        Spacer(1, 0.35 * inch),
        Paragraph(inline_markup(title), styles["title"]),
        Spacer(1, 6),
        Paragraph(inline_markup(status), styles["meta"]),
        Paragraph(inline_markup(authors), styles["meta"]),
        Spacer(1, 10),
        Table([[""]], colWidths=[100], rowHeights=[3], hAlign="CENTER",
              style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(TEAL))])),
        Spacer(1, 16),
        Paragraph("Abstract", styles["abstract_head"]),
        Paragraph(inline_markup(" ".join(abstract_lines)), styles["abstract"]),
        Paragraph(inline_markup(keywords), styles["keywords"]),
        Spacer(1, 16),
        Paragraph("Research status", styles["abstract_head"]),
        Paragraph("This manuscript reports a functioning application and evaluation infrastructure. The independently labelled identity and retrieval datasets have not yet been completed; no controlled research result is claimed.", styles["abstract"]),
        PageBreak(),
    ]


def build_pdf() -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    (ROOT / "output" / "pdf").mkdir(parents=True, exist_ok=True)
    figure_architecture(FIGURES / "system-architecture.png")
    figure_inventory(FIGURES / "database-inventory.png")
    figure_evaluation(FIGURES / "evaluation-workflow.png")

    pdfmetrics.registerFont(TTFont("Arial", FONT_REG))
    pdfmetrics.registerFont(TTFont("Arial-Bold", FONT_BOLD))
    pdfmetrics.registerFont(TTFont("Arial-Italic", FONT_ITALIC))
    pdfmetrics.registerFont(TTFont("Arial-BoldItalic", "/System/Library/Fonts/Supplemental/Arial Bold Italic.ttf"))
    pdfmetrics.registerFontFamily("Arial", normal="Arial", bold="Arial-Bold",
                                  italic="Arial-Italic", boldItalic="Arial-BoldItalic")

    markdown = PAPER.read_text(encoding="utf-8")
    styles = make_styles()
    story = make_title_page(markdown, styles)
    section_start = markdown.index("## 1. Introduction")
    story.extend(parse_markdown(markdown[section_start:], styles, letter[0] - 116))
    doc = PaperDoc(str(OUTPUT))
    doc.build(story)
    print(f"Created {OUTPUT}")
    for name in ("system-architecture.png", "database-inventory.png", "evaluation-workflow.png"):
        print(f"Created {FIGURES / name}")


if __name__ == "__main__":
    build_pdf()