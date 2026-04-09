import docx

doc_path = r"c:\Users\Vyacheslav\PandaPal\docs\diploma_and_presentation\diplom_project(PandaPal)_fixed.docx"
doc = docx.Document(doc_path)

with open(r"c:\Users\Vyacheslav\PandaPal\tmp_find.txt", "w", encoding="utf-8") as f:
    for i, p in enumerate(doc.paragraphs):
        if (
            "Схема" in p.text
            or "схем" in p.text.lower()
            or "Рисунок" in p.text
            or "рисун" in p.text.lower()
            or "pic" in p._p.xml.lower()
        ):
            f.write(f"[{i}] {p.text}\n")
