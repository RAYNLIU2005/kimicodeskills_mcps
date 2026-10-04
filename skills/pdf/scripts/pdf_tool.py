#!/usr/bin/env python3
"""pdf_tool.py —— token 高效的 PDF 命令行工具（面向 agent，输出紧凑）。

约定：
  * 读命令把结果打到 stdout，按 --max-chars 截断（超出打 [truncated]）。
  * 写命令必须用 -o 指定输出文件；只有显式 --inplace 才会覆盖输入文件。
  * 出错写 stderr 并返回退出码 2。
用法：python pdf_tool.py <子命令> -h
"""
from __future__ import annotations

import argparse
import io
import os
import sys

DEFAULT_MAX_CHARS = 20000

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass


def die(msg, code=2):
    sys.stderr.write("error: %s\n" % msg)
    raise SystemExit(code)


class Budget:
    """限制文本类输出总字符数，超出后丢弃并追加 [truncated]。"""

    def __init__(self, limit):
        self.limit = int(limit)
        self.used = 0
        self.done = False

    def add(self, text):
        if self.done:
            return
        remain = self.limit - self.used
        if remain <= 0:
            self.done = True
            return
        if len(text) > remain:
            sys.stdout.write(text[:remain] + "\n")
            self.used += remain
            self.done = True
        else:
            sys.stdout.write(text)
            self.used += len(text)

    def line(self, text=""):
        self.add(text + "\n")

    def close(self):
        if self.done:
            sys.stdout.write("[truncated] 输出超过 --max-chars=%d，请用 -p 缩小页码范围\n" % self.limit)


def parse_pages(spec, total):
    """把 '1-3,5,8-' 解析为 0 基页索引列表（spec 为空表示全部）。"""
    if spec is None or str(spec).strip() == "":
        return list(range(total))
    out = []
    for part in str(spec).split(","):
        part = part.strip()
        if not part:
            continue
        try:
            if "-" in part:
                head, tail = part.split("-", 1)
                start = int(head) if head.strip() else 1
                end = int(tail) if tail.strip() else total
            else:
                start = end = int(part)
        except ValueError:
            die("非法页码范围 %r，示例: 1-3,5,8-" % part)
        if start < 1 or end > total or start > end:
            die("页码范围 %r 超出文档页数 %d" % (part, total))
        out.extend(range(start - 1, end))
    seen, uniq = set(), []
    for i in out:
        if i not in seen:
            seen.add(i)
            uniq.append(i)
    return uniq


def read_bytes(path):
    try:
        with open(path, "rb") as f:
            return f.read()
    except OSError as e:
        die("无法读取 %s: %s" % (path, e))


def open_pdf(path, password=None):
    """返回 (PdfReader, 原文件是否加密)。文件一次性读入内存，避免 Windows 文件锁。"""
    from pypdf import PdfReader

    data = read_bytes(path)
    try:
        reader = PdfReader(io.BytesIO(data))
    except Exception as e:
        die("%s 不是有效的 PDF: %s" % (path, e))
    encrypted = bool(reader.is_encrypted)
    if encrypted:
        ok = False
        try:
            ok = bool(reader.decrypt(password or ""))
        except Exception:
            ok = False
        if not ok:
            die("%s 已加密：密码错误或未提供（用 --password 指定）" % path)
    return reader, encrypted


def clone(reader):
    from pypdf import PdfWriter

    return PdfWriter(clone_from=reader)


def subset(reader, pages):
    """按页索引子集（list 或 (start, stop) 半开区间）新建 writer。"""
    from pypdf import PdfWriter

    w = PdfWriter()
    try:
        w.append(reader, pages=pages)
    except TypeError:
        idxs = range(pages[0], pages[1]) if isinstance(pages, tuple) else list(pages)
        for i in idxs:
            w.add_page(reader.pages[i])
    return w


def target(args, src):
    if getattr(args, "inplace", False):
        return src
    out = getattr(args, "out", None)
    if not out:
        die("写操作必须用 -o 指定输出文件（或显式加 --inplace 覆盖原文件）")
    return out


def save(writer, path):
    tmp = path + ".pdftmp"
    try:
        with open(tmp, "wb") as f:
            writer.write(f)
        os.replace(tmp, path)
    except OSError as e:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass
        die("无法写入 %s: %s" % (path, e))
    return path


def page_text(page):
    try:
        return page.extract_text() or ""
    except Exception:
        return ""


def page_images(page):
    try:
        return list(page.images)
    except Exception:
        return []


def cmd_info(args):
    reader, encrypted = open_pdf(args.file, args.password)
    box = reader.pages[0].mediabox
    print("file=%s pages=%d size=%dx%dpt enc=%s" % (
        os.path.basename(args.file), len(reader.pages),
        round(float(box.width)), round(float(box.height)),
        "yes" if encrypted else "no"))
    b = Budget(args.max_chars)
    for i, page in enumerate(reader.pages, 1):
        text = page_text(page)
        imgs = len(page_images(page))
        tag = " [无文本层/扫描页]" if not text.strip() and imgs else ""
        b.line("p%d: text=%dc imgs=%d%s" % (i, len(text), imgs, tag))
    b.close()


def cmd_text(args):
    reader, _ = open_pdf(args.file, args.password)
    pages = parse_pages(args.pages, len(reader.pages))
    b = Budget(args.max_chars)
    for i in pages:
        b.line("p%d" % (i + 1))
        t = page_text(reader.pages[i]).strip()
        if t:
            b.line(t)
        else:
            b.line("[本页无文本层：可能是扫描件，需要 OCR；不要循环重试提取]")
    b.close()


def cmd_search(args):
    reader, _ = open_pdf(args.file, args.password)
    pages = parse_pages(args.pages, len(reader.pages))
    needle = args.pattern.lower() if args.ignore_case else args.pattern
    hits = 0
    b = Budget(args.max_chars)
    for i in pages:
        for line in page_text(reader.pages[i]).splitlines():
            hay = line.lower() if args.ignore_case else line
            if needle and needle in hay:
                hits += 1
                b.line("p%d: %s" % (i + 1, line.strip()))
    b.line("matches=%d" % hits)
    b.close()
    return 0


def cmd_tables(args):
    try:
        import pdfplumber
    except ImportError:
        die("tables 需要 pdfplumber：uv pip install pdfplumber")
    data = read_bytes(args.file)
    kwargs = {"password": args.password} if args.password else {}
    b = Budget(args.max_chars)
    try:
        with pdfplumber.open(io.BytesIO(data), **kwargs) as pdf:
            pages = parse_pages(args.pages, len(pdf.pages))
            for i in pages:
                try:
                    tables = pdf.pages[i].extract_tables() or []
                except Exception:
                    tables = []
                b.line("p%d tables=%d" % (i + 1, len(tables)))
                for tb in tables:
                    for row in tb:
                        cells = ["" if c is None else str(c).replace("\n", " ") for c in row]
                        b.line("  " + " | ".join(cells))
    except Exception as e:
        die("解析表格失败: %s" % e)
    b.close()


def cmd_merge(args):
    writer = None
    for f in args.files:
        reader, _ = open_pdf(f, args.password)
        if writer is None:
            from pypdf import PdfWriter
            writer = PdfWriter()
        writer.append(reader)
    save(writer, args.out)
    print("merged=%d -> %s pages=%d" % (len(args.files), args.out, len(writer.pages)))


def cmd_split(args):
    reader, _ = open_pdf(args.file, args.password)
    total = len(reader.pages)
    try:
        step = max(1, int(args.every))
    except ValueError:
        die("--every 需要正整数")
    os.makedirs(args.out, exist_ok=True)
    stem = os.path.splitext(os.path.basename(args.file))[0]
    made = []
    for start in range(0, total, step):
        end = min(start + step, total)
        name = "%s_p%d.pdf" % (stem, start + 1) if end - start == 1 else "%s_p%d-%d.pdf" % (stem, start + 1, end)
        path = os.path.join(args.out, name)
        save(subset(reader, list(range(start, end))), path)
        made.append(name)
    for n in made:
        print(n)
    print("created=%d dir=%s" % (len(made), args.out))


def cmd_extract_pages(args):
    reader, _ = open_pdf(args.file, args.password)
    pages = parse_pages(args.pages, len(reader.pages))
    out = target(args, args.file)
    save(subset(reader, pages), out)
    print("extracted=%d pages=%d -> %s" % (len(pages), len(pages), out))


def cmd_delete_pages(args):
    reader, _ = open_pdf(args.file, args.password)
    total = len(reader.pages)
    drop = set(parse_pages(args.pages, total))
    keep = [i for i in range(total) if i not in drop]
    if not keep:
        die("不能删除全部页面")
    out = target(args, args.file)
    save(subset(reader, keep), out)
    print("deleted=%d kept=%d -> %s" % (len(drop), len(keep), out))


def cmd_rotate(args):
    if args.angle % 90:
        die("旋转角度必须是 90 的倍数")
    reader, _ = open_pdf(args.file, args.password)
    pages = parse_pages(args.pages, len(reader.pages))
    writer = clone(reader)
    for i in pages:
        page = writer.pages[i]
        if hasattr(page, "rotate"):
            page.rotate(args.angle)
        else:
            page.rotate_clockwise(args.angle)
    out = target(args, args.file)
    save(writer, out)
    print("rotated=%s angle=%d -> %s" % (args.pages or "all", args.angle, out))


def cmd_form(args):
    reader, _ = open_pdf(args.file, args.password)
    data = {}
    for kv in args.set or []:
        if "=" not in kv:
            die("--set 需要 name=value 格式，收到 %r" % kv)
        k, v = kv.split("=", 1)
        data[k] = v
    if not data:
        fields = reader.get_fields() or {}
        print("fields=%d" % len(fields))
        for name, f in fields.items():
            try:
                ft = str(f.get("/FT")).lstrip("/")
                val = f.get("/V")
            except Exception:
                ft, val = "?", ""
            print("  %s=%s type=%s" % (name, "" if val is None else val, ft))
        return 0
    writer = clone(reader)
    try:
        for page in writer.pages:
            writer.update_page_form_field_values(page, data)
    except Exception as e:
        die("填充表单失败（字段名需与 form 列表一致）: %s" % e)
    hook = getattr(writer, "set_need_appearances_writer", None)
    if hook:
        try:
            hook(True)
        except Exception:
            pass
    out = target(args, args.file)
    save(writer, out)
    print("set=%s -> %s" % (",".join(sorted(data)), out))


def cmd_annotate(args):
    from pypdf.generic import (ArrayObject, DictionaryObject, FloatObject,
                               NameObject, NumberObject, TextStringObject)

    reader, _ = open_pdf(args.file, args.password)
    writer = clone(reader)
    pages = parse_pages(args.pages, len(writer.pages))
    for i in pages:
        page = writer.pages[i]
        annot = DictionaryObject()
        annot[NameObject("/Type")] = NameObject("/Annot")
        annot[NameObject("/Subtype")] = NameObject("/Text")
        annot[NameObject("/Contents")] = TextStringObject(args.text)
        annot[NameObject("/Rect")] = ArrayObject([
            FloatObject(args.x), FloatObject(args.y),
            FloatObject(args.x + 20), FloatObject(args.y + 20)])
        annot[NameObject("/F")] = NumberObject(4)
        ref = writer._add_object(annot)
        annots = page.get("/Annots")
        if annots is None:
            page[NameObject("/Annots")] = ArrayObject([ref])
        else:
            annots.append(ref)
    out = target(args, args.file)
    save(writer, out)
    print("annotated pages=%s -> %s" % (args.pages or "all", out))


META_KEYS = [("title", "/Title"), ("author", "/Author"), ("subject", "/Subject"),
             ("keywords", "/Keywords"), ("creator", "/Creator"), ("producer", "/Producer")]


def cmd_meta(args):
    reader, _ = open_pdf(args.file, args.password)
    values = {k: getattr(args, k) for k, _ in META_KEYS}
    sets = {pdfkey: values[k] for k, pdfkey in META_KEYS if values[k] is not None}
    if not sets:
        md = reader.metadata or {}
        for k, pdfkey in META_KEYS:
            try:
                v = md.get(pdfkey)
            except Exception:
                v = None
            print("%s=%s" % (k, "" if v is None else v))
        return 0
    writer = clone(reader)
    writer.add_metadata(sets)
    out = target(args, args.file)
    save(writer, out)
    print("updated=%s -> %s" % (",".join(sorted(sets)), out))


def cmd_encrypt(args):
    if not args.password:
        die("encrypt 需要 --password 指定新密码")
    reader, _ = open_pdf(args.file, args.password)
    writer = clone(reader)
    writer.encrypt(user_password=args.password,
                   owner_password=args.owner_password or args.password)
    out = target(args, args.file)
    save(writer, out)
    print("encrypted -> %s（打开需密码）" % out)


def cmd_decrypt(args):
    reader, encrypted = open_pdf(args.file, args.password)
    if not encrypted:
        die("%s 未加密，无需 decrypt" % args.file)
    out = target(args, args.file)
    save(clone(reader), out)
    print("decrypted pages=%d -> %s" % (len(reader.pages), out))


def cmd_images(args):
    reader, _ = open_pdf(args.file, args.password)
    pages = parse_pages(args.pages, len(reader.pages))
    if args.export:
        os.makedirs(args.export, exist_ok=True)
    b = Budget(args.max_chars)
    total = 0
    for i in pages:
        for im in page_images(reader.pages[i]):
            total += 1
            try:
                w, h = im.image.size
            except Exception:
                w = h = 0
            b.line("p%d name=%s size=%dx%d" % (i + 1, im.name, w, h))
            if args.export:
                with open(os.path.join(args.export, "p%d_%s" % (i + 1, im.name)), "wb") as f:
                    f.write(im.data)
    b.line("images=%d" % total)
    b.close()


def build_parser():
    p = argparse.ArgumentParser(
        prog="pdf_tool.py",
        description="token 高效的 PDF 工具：读取、合并拆分、表格、表单、批注、元数据、加密。")
    pg = argparse.ArgumentParser(add_help=False)
    pg.add_argument("--password", default=None, help="加密文件的打开密码")
    pg.add_argument("-p", "--pages", default=None, help="页码范围，如 1-3,5,8-；默认全部")
    pg.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS, help="文本输出上限字符数")
    pw = argparse.ArgumentParser(add_help=False)
    pw.add_argument("--password", default=None, help="加密文件的打开密码")
    ow = argparse.ArgumentParser(add_help=False)
    ow.add_argument("-o", "--out", default=None, help="输出文件")
    ow.add_argument("--inplace", action="store_true", help="直接覆盖输入文件")

    sp = p.add_subparsers(dest="cmd", required=True)

    s = sp.add_parser("info", parents=[pg], help="概览：页数/尺寸/加密/每页文本与图片数量")
    s.add_argument("file")
    s.set_defaults(func=cmd_info)

    s = sp.add_parser("text", parents=[pg], help="提取文本（无文本层会提示扫描件）")
    s.add_argument("file")
    s.set_defaults(func=cmd_text)

    s = sp.add_parser("search", parents=[pg], help="搜索文本，输出 页码: 命中行")
    s.add_argument("pattern")
    s.add_argument("file")
    s.add_argument("-i", "--ignore-case", action="store_true")
    s.set_defaults(func=cmd_search)

    s = sp.add_parser("tables", parents=[pg], help="提取表格（pdfplumber）")
    s.add_argument("file")
    s.set_defaults(func=cmd_tables)

    s = sp.add_parser("merge", parents=[pw], help="合并多个 PDF，-o 必填")
    s.add_argument("-o", "--out", required=True, help="输出文件（必填）")
    s.add_argument("files", nargs="+")
    s.set_defaults(func=cmd_merge)

    s = sp.add_parser("split", parents=[pg], help="拆分：-o 为输出目录")
    s.add_argument("-o", "--out", required=True, help="输出目录（必填）")
    s.add_argument("--every", default="1", help="每 N 页一个文件，默认 1")
    s.add_argument("file")
    s.set_defaults(func=cmd_split)

    s = sp.add_parser("extract-pages", parents=[pg, ow], help="抽取指定页为新 PDF")
    s.add_argument("file")
    s.set_defaults(func=cmd_extract_pages)

    s = sp.add_parser("delete-pages", parents=[pg, ow], help="删除指定页")
    s.add_argument("file")
    s.set_defaults(func=cmd_delete_pages)

    s = sp.add_parser("rotate", parents=[pg, ow], help="旋转页面（90 的倍数）")
    s.add_argument("--angle", type=int, default=90)
    s.add_argument("file")
    s.set_defaults(func=cmd_rotate)

    s = sp.add_parser("form", parents=[pg, ow], help="列出表单字段；--set k=v 填充")
    s.add_argument("--set", action="append", metavar="K=V")
    s.add_argument("file")
    s.set_defaults(func=cmd_form)

    s = sp.add_parser("annotate", parents=[pg, ow], help="添加文本批注")
    s.add_argument("-t", "--text", required=True, help="批注内容")
    s.add_argument("--x", type=float, default=72.0)
    s.add_argument("--y", type=float, default=720.0)
    s.add_argument("file")
    s.set_defaults(func=cmd_annotate)

    s = sp.add_parser("meta", parents=[pg, ow], help="读取/写入元数据")
    for k in ("title", "author", "subject", "keywords", "creator", "producer"):
        s.add_argument("--" + k, default=None)
    s.add_argument("file")
    s.set_defaults(func=cmd_meta)

    s = sp.add_parser("encrypt", parents=[pg, ow], help="加密（--password 为新密码）")
    s.add_argument("--owner-password", default=None)
    s.add_argument("file")
    s.set_defaults(func=cmd_encrypt)

    s = sp.add_parser("decrypt", parents=[pg, ow], help="解密（--password 为原密码）")
    s.add_argument("file")
    s.set_defaults(func=cmd_decrypt)

    s = sp.add_parser("images", parents=[pg], help="列出内嵌图片；--export DIR 导出")
    s.add_argument("--export", default=None, metavar="DIR")
    s.add_argument("file")
    s.set_defaults(func=cmd_images)

    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        return args.func(args) or 0
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 2
    except BrokenPipeError:
        return 0
    except Exception as e:
        sys.stderr.write("error: %s\n" % e)
        return 2


if __name__ == "__main__":
    sys.exit(main())
