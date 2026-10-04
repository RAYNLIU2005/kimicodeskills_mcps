#!/usr/bin/env python3
"""tests/verify.py —— 重新读取输出 PDF 并断言，退出码 0 表示通过。

用法：python verify.py <check> <file> [args...]
  pages FILE N                 页数等于 N
  encrypted FILE yes|no        是否加密
  need-password FILE           加密文件无密码不可读
  rotate FILE PAGENO ANGLE     第 PAGENO 页 /Rotate == ANGLE
  field FILE NAME VALUE        表单字段值等于 VALUE
  annot FILE SUBSTR            存在含 SUBSTR 的批注
  meta FILE KEY VALUE          元数据 KEY 等于 VALUE
  images FILE N                内嵌图片数量等于 N
  textcontains FILE SUBSTR     全文包含 SUBSTR
"""
import sys

from pypdf import PdfReader


def fail(msg):
    sys.stderr.write(msg + "\n")
    sys.exit(1)


def all_text(reader):
    return "\n".join((p.extract_text() or "") for p in reader.pages)


def main():
    a = sys.argv[1:]
    if not a:
        fail("用法: verify.py <check> <file> [args...]")
    kind = a[0]

    if kind == "pages":
        r = PdfReader(a[1])
        got = len(r.pages)
        if got != int(a[2]):
            fail("pages=%d 期望 %s" % (got, a[2]))
        print("ok pages=%d" % got)
    elif kind == "encrypted":
        r = PdfReader(a[1])
        got = "yes" if r.is_encrypted else "no"
        if got != a[2]:
            fail("encrypted=%s 期望 %s" % (got, a[2]))
        print("ok encrypted=%s" % got)
    elif kind == "need-password":
        r = PdfReader(a[1])
        if not r.is_encrypted:
            fail("文件未加密，无法验证密码保护")
        try:
            r.pages[0].extract_text()
        except Exception:
            print("ok 无密码读取被拒绝")
            return
        fail("无密码竟然读到了内容")
    elif kind == "rotate":
        r = PdfReader(a[1])
        got = r.pages[int(a[2]) - 1].get("/Rotate")
        if got is None or int(got) != int(a[3]):
            fail("第 %s 页 /Rotate=%s 期望 %s" % (a[2], got, a[3]))
        print("ok rotate=%s" % got)
    elif kind == "field":
        r = PdfReader(a[1])
        fields = r.get_fields() or {}
        got = fields.get(a[2], {}).get("/V")
        if str(got) != a[3]:
            fail("字段 %s=%r 期望 %r" % (a[2], got, a[3]))
        print("ok field %s=%s" % (a[2], got))
    elif kind == "annot":
        r = PdfReader(a[1])
        found = []
        for page in r.pages:
            annots = page.get("/Annots") or []
            for an in annots:
                try:
                    obj = an.get_object()
                    found.append(str(obj.get("/Contents") or ""))
                except Exception:
                    continue
        if not any(a[2] in s for s in found):
            fail("未找到含 %r 的批注，现有: %r" % (a[2], found))
        print("ok annot=%d 条" % len(found))
    elif kind == "meta":
        r = PdfReader(a[1])
        got = (r.metadata or {}).get("/" + a[2].capitalize())
        if str(got) != a[3]:
            fail("元数据 /%s=%r 期望 %r" % (a[2], got, a[3]))
        print("ok meta %s=%s" % (a[2], got))
    elif kind == "images":
        r = PdfReader(a[1])
        got = sum(len(list(p.images)) for p in r.pages)
        if got != int(a[2]):
            fail("images=%d 期望 %s" % (got, a[2]))
        print("ok images=%d" % got)
    elif kind == "textcontains":
        r = PdfReader(a[1])
        if a[2] not in all_text(r):
            fail("全文未包含 %r" % a[2])
        print("ok 包含 %s" % a[2])
    else:
        fail("未知检查: %s" % kind)


if __name__ == "__main__":
    main()
