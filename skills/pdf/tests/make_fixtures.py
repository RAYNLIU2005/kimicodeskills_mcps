#!/usr/bin/env python3
"""生成 tests/fixtures/ 下的所有测试 PDF（可重复运行）。"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures")

CN_FONTS = [
    ("C:/Windows/Fonts/msyh.ttc", 0),
    ("C:/Windows/Fonts/simhei.ttf", None),
    ("C:/Windows/Fonts/simsun.ttc", 0),
]


def register_cn():
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    for path, idx in CN_FONTS:
        if not os.path.exists(path):
            continue
        try:
            pdfmetrics.registerFont(TTFont("cn", path) if idx is None
                                    else TTFont("cn", path, subfontIndex=idx))
            return "cn"
        except Exception:
            continue
    return "Helvetica"


def text_pdf(path):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    font = register_cn()
    pages = [
        ["这是中文测试 预算 报告", "预算总表 1200 元", "第二行中文内容用于检索"],
        ["Hello English text budget report", "Page 2 English only"],
        ["混合 mixed 页面：预算 2026", "mixed line with english words"],
    ]
    c = canvas.Canvas(path, pagesize=A4)
    for lines in pages:
        y = 780
        for ln in lines:
            c.setFont(font, 14)
            c.drawString(60, y, ln)
            y -= 24
        c.showPage()
    c.save()


def multi_pdf(path):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(path, pagesize=A4)
    for i in range(1, 7):
        c.setFont("Helvetica", 18)
        c.drawString(72, 720, "Page %d" % i)
        c.showPage()
    c.save()


def table_pdf(path):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.platypus import Table, TableStyle

    font = register_cn()
    data = [["项目", "金额", "备注"], ["预算", "1200", "元"], ["实际", "800", "元"]]
    t = Table(data, colWidths=[120, 120, 120])
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("FONTNAME", (0, 0), (-1, -1), font),
        ("FONTSIZE", (0, 0), (-1, -1), 12),
    ]))
    c = canvas.Canvas(path, pagesize=A4)
    t.wrapOn(c, 400, 400)
    t.drawOn(c, 60, 650)
    c.showPage()
    c.save()


def form_pdf(path):
    from pypdf import PdfWriter
    from pypdf.generic import (ArrayObject, BooleanObject, DictionaryObject,
                               NameObject, NumberObject, TextStringObject)

    w = PdfWriter()
    page = w.add_blank_page(width=595, height=842)
    refs = []
    for fname, y, val in (("name", 700, "Alice"), ("city", 660, "Beijing")):
        field = DictionaryObject()
        field[NameObject("/FT")] = NameObject("/Tx")
        field[NameObject("/T")] = TextStringObject(fname)
        field[NameObject("/V")] = TextStringObject(val)
        field[NameObject("/Type")] = NameObject("/Annot")
        field[NameObject("/Subtype")] = NameObject("/Widget")
        field[NameObject("/F")] = NumberObject(4)
        field[NameObject("/Rect")] = ArrayObject([
            NumberObject(150), NumberObject(y), NumberObject(420), NumberObject(y + 24)])
        ref = w._add_object(field)
        field[NameObject("/P")] = page.indirect_reference
        refs.append(ref)
    page[NameObject("/Annots")] = ArrayObject(refs)
    w._root_object[NameObject("/AcroForm")] = DictionaryObject({
        NameObject("/Fields"): ArrayObject(refs),
        NameObject("/NeedAppearances"): BooleanObject(True),
    })
    with open(path, "wb") as f:
        w.write(f)


def encrypted_pdf(path, src):
    from pypdf import PdfReader, PdfWriter

    w = PdfWriter(clone_from=PdfReader(src))
    w.encrypt(user_password="secret", owner_password="secret")
    with open(path, "wb") as f:
        w.write(f)


def scanned_pdf(path, src):
    import pypdfium2 as pdfium
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    doc = pdfium.PdfDocument(src)
    img = doc[0].render(scale=2).to_pil().convert("RGB")
    png = os.path.join(FIX, "_scan_tmp.png")
    img.save(png)
    c = canvas.Canvas(path, pagesize=A4)
    c.drawImage(png, 40, 380, width=img.width * 0.5, height=img.height * 0.5)
    c.showPage()
    c.save()
    os.remove(png)


def main():
    os.makedirs(FIX, exist_ok=True)
    jobs = [
        ("text_cn.pdf", lambda p: text_pdf(p)),
        ("multi.pdf", lambda p: multi_pdf(p)),
        ("table.pdf", lambda p: table_pdf(p)),
        ("form.pdf", lambda p: form_pdf(p)),
        ("encrypted.pdf", lambda p: encrypted_pdf(p, os.path.join(FIX, "multi.pdf"))),
        ("scanned.pdf", lambda p: scanned_pdf(p, os.path.join(FIX, "multi.pdf"))),
    ]
    for name, fn in jobs:
        path = os.path.join(FIX, name)
        fn(path)
        size = os.path.getsize(path)
        print("fixture %-14s %6d bytes" % (name, size))
        if size == 0:
            print("空文件: %s" % name, file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
