"""
Fix remaining alignment: force ALL paragraphs with box-drawing chars to CENTER.
Also fix LEFT-aligned flow diagram lines.
"""
import docx
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

doc_path = r"c:\Users\Vyacheslav\PandaPal\docs\diploma_and_presentation\diplom_project(PandaPal)_final.docx"
doc = docx.Document(doc_path)

fixed = 0

for p in doc.paragraphs:
    text = p.text.strip()

    # ALL paragraphs with box-drawing chars → CENTER
    has_box = any(c in text for c in "┌│└├─┐┘┤┬┴┼▼▲╔╗╚╝╠╣╦╩╬═║")

    if has_box and p.alignment != WD_ALIGN_PARAGRAPH.CENTER:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.first_line_indent = Pt(0)
        p.paragraph_format.left_indent = Pt(0)
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = Pt(10)

        for run in p.runs:
            run.font.name = 'Courier New'
            run.font.size = Pt(8)
            r_elem = run._r
            rPr = r_elem.find(qn('w:rPr'))
            if rPr is None:
                rPr = parse_xml(f'<w:rPr {nsdecls("w")}></w:rPr>')
                r_elem.insert(0, rPr)
            rFonts = rPr.find(qn('w:rFonts'))
            if rFonts is None:
                rFonts = parse_xml(f'<w:rFonts {nsdecls("w")} w:ascii="Courier New" w:hAnsi="Courier New" w:cs="Courier New" w:eastAsia="Courier New"/>')
                rPr.insert(0, rFonts)
            else:
                rFonts.set(qn('w:ascii'), 'Courier New')
                rFonts.set(qn('w:hAnsi'), 'Courier New')
                rFonts.set(qn('w:cs'), 'Courier New')
                rFonts.set(qn('w:eastAsia'), 'Courier New')

        fixed += 1

    # Arrow lines center
    if text in ("↓", "→", "↑", "←") and p.alignment != WD_ALIGN_PARAGRAPH.CENTER:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.first_line_indent = Pt(0)
        p.paragraph_format.left_indent = Pt(0)
        fixed += 1

    # Code block lines with "→" (flow diagrams) that are short
    if "→" in text and len(text) < 90 and not text.endswith("."):
        if "bot/" in text or "Пользователь" in text or "Отправка" in text:
            if p.alignment != WD_ALIGN_PARAGRAPH.CENTER:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.paragraph_format.first_line_indent = Pt(0)
                p.paragraph_format.left_indent = Pt(0)
                for run in p.runs:
                    run.font.name = 'Courier New'
                    run.font.size = Pt(9)
                fixed += 1

    # Frontend structure tree lines
    if ("├──" in text or "└──" in text or text.startswith("frontend/src/")):
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.first_line_indent = Pt(0)
        p.paragraph_format.left_indent = Pt(0)
        for run in p.runs:
            run.font.name = 'Courier New'
            run.font.size = Pt(9)

logger.info(f"Fixed {fixed} paragraphs alignment to CENTER")
doc.save(doc_path)
logger.info("Saved!")
