"""docx_tool: compact CLI for reading/editing .docx (python-docx + docx-mcp-server, MIT)."""
from __future__ import annotations

import argparse, copy, json, os, random, re, shlex, shutil, subprocess, sys, tempfile, zipfile

import docx
from docx.enum.section import WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Mm, Pt, RGBColor
from docx.text.run import Run

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")
ZIHAO = {"初号": 42, "小初": 36, "一号": 26, "小一": 24, "二号": 22, "小二": 18, "三号": 16,
         "小三": 15, "四号": 14, "小四": 12, "五号": 10.5, "小五": 9, "六号": 7.5, "小六": 6.5}
ALIGN = {"left": "LEFT", "center": "CENTER", "right": "RIGHT", "justify": "JUSTIFY",
         "distribute": "DISTRIBUTE", "左": "LEFT", "中": "CENTER", "居中": "CENTER", "右": "RIGHT",
         "两端": "JUSTIFY", "分散": "DISTRIBUTE"}
STYLE_ALIAS = {"正文": "Normal", "标题": "Title"} | {f"标题{i}": f"Heading {i}" for i in range(1, 10)}
PAGE = {"A4": (210, 297), "A3": (297, 420), "A5": (148, 210), "B5": (176, 250), "LETTER": (215.9, 279.4)}
W14 = "http://schemas.microsoft.com/office/word/2010/wordml"


def short(t, n=40):
    t = t.replace("\n", "⏎").replace("\t", "→")
    return t if len(t) <= n else t[:n] + "…"


def size_pt(v):
    return float(ZIHAO.get(v, v))


def ptext(p):
    return "".join(t.text or "" for t in p._p.iter(qn("w:t")))


def rtext(p):
    return "".join(r.text for r in p.runs)


class State:
    def __init__(self, src):
        self.tmp = tempfile.mkdtemp(prefix="docxtool_")
        self.work = os.path.join(self.tmp, "w.docx")
        shutil.copy(src, self.work)
        self.doc = docx.Document(self.work)
        self.mut = False

    def paras(self):
        return self.doc.paragraphs

    def mcp(self, fn):
        """Run fn(DocxDocument, body_paragraph_elements) on the current doc via docx-mcp."""
        from docx_mcp.document import DocxDocument
        self.doc.save(self.work)
        x = DocxDocument(self.work)
        x.open()
        try:
            root = x._require("word/document.xml")
            used = {e.get(f"{{{W14}}}paraId") for e in root.iter() if e.get(f"{{{W14}}}paraId")}
            for p in root.iter(qn("w:p")):
                if not p.get(f"{{{W14}}}paraId"):
                    while (pid := "%08X" % random.randint(1, 0x7FFFFFFF)) in used:
                        pass
                    used.add(pid)
                    p.set(f"{{{W14}}}paraId", pid)
            x._mark("word/document.xml")
            res = fn(x, root.find(qn("w:body")).findall(qn("w:p")))
            x.save(backup=False)
        finally:
            x.close()
        self.doc = docx.Document(self.work)
        return res
def select(st, spec, text=None):
    """spec: all | 3 | 2-5,8 | ~子串 | s:样式名 ; text: also require containing text."""
    ps = st.paras()
    if spec in (None, "all"):
        idx = range(len(ps))
    elif spec.startswith("~"):
        idx = [i for i, p in enumerate(ps) if spec[1:] in p.text]
    elif spec.startswith("s:"):
        name = STYLE_ALIAS.get(spec[2:], spec[2:])
        idx = [i for i, p in enumerate(ps) if p.style is not None and p.style.name == name]
    else:
        idx = []
        for part in spec.split(","):
            a, _, b = part.partition("-")
            idx += range(int(a), int(b or a) + 1)
    out = [(i, ps[i]) for i in idx if 0 <= i < len(ps) and (not text or text in ps[i].text)]
    if not out:
        raise SystemExit(f"错误: 没有匹配的段落 (p={spec}, text={text})")
    return out


def split_run(run, off):
    """Split run at char offset; return the right-hand new run."""
    new = copy.deepcopy(run._element)
    run._element.addnext(new)
    r2 = Run(new, run._parent)
    t = run.text
    run.text, r2.text = t[:off], t[off:]
    return r2


def isolate(p, sub, nth=None):
    """Return runs covering each occurrence of sub (all, or the nth) in paragraph p."""
    res, start, k = [], 0, 0
    while True:
        full = rtext(p)
        pos = full.find(sub, start)
        if pos < 0:
            return res
        start = pos + len(sub)
        k += 1
        if nth and k != nth:
            continue
        end, acc, covered = pos + len(sub), 0, []
        for r in list(p.runs):
            a, b = acc, acc + len(r.text)
            acc = b
            if b <= pos or a >= end:
                continue
            if a < pos:
                r = split_run(r, pos - a)
                a = pos
            if b > end:
                split_run(r, end - a)
            covered.append(r)
        res.append(covered)
        if nth:
            return res


def font_apply(f, rpr_el, a):
    if a.name or a.cn or a.en:
        en, cn = a.en or a.name, a.cn or a.name
        if en:
            f.name = en
        rpr = rpr_el.get_or_add_rPr() if hasattr(rpr_el, "get_or_add_rPr") else rpr_el
        rf = rpr.find(qn("w:rFonts"))
        if rf is None:
            rf = OxmlElement("w:rFonts")
            rpr.insert(0, rf)
        if cn:
            rf.set(qn("w:eastAsia"), cn)
        if en:
            rf.set(qn("w:ascii"), en)
            rf.set(qn("w:hAnsi"), en)
    if a.size:
        f.size = Pt(size_pt(a.size))
    for k in ("bold", "italic", "underline"):
        v = getattr(a, k)
        if v is not None:
            setattr(f, k, v == "1")
    if a.color:
        f.color.rgb = RGBColor.from_string(a.color.lstrip("#"))


def para_apply(pf, ppr_owner, a):
    if a.align:
        pf.alignment = getattr(WD_ALIGN_PARAGRAPH, ALIGN[a.align])
    if a.line:
        v = a.line
        if v.endswith("pt"):
            exact = not v.startswith(">=")
            pf.line_spacing = Pt(float(v.lstrip(">=")[:-2]))
            pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY if exact else WD_LINE_SPACING.AT_LEAST
        else:
            pf.line_spacing = float(v)
    if a.before is not None:
        pf.space_before = Pt(float(a.before))
    if a.after is not None:
        pf.space_after = Pt(float(a.after))
    for key, attr in (("indent", "first_line"), ("left", "left")):
        v = getattr(a, key)
        if v is None:
            continue
        ind = ppr_owner.get_or_add_pPr().get_or_add_ind()
        if v.endswith("cm"):
            setattr(pf, attr + "_indent", Cm(float(v[:-2])))
        else:
            chars = str(int(float(v.rstrip("字符")) * 100))
            ind.set(qn("w:firstLineChars" if attr == "first_line" else "w:leftChars"), chars)
            ind.attrib.pop(qn("w:firstLine" if attr == "first_line" else "w:left"), None)
def c_outline(st, a):
    ps = st.paras()
    sel = select(st, a.p) if a.p else list(enumerate(ps))
    shown = 0
    for i, p in sel:
        if not ptext(p).strip() and not a.empty:
            continue
        s = p.style.name if p.style is not None else ""
        print(f"{i}|{s}|{short(ptext(p), a.w)}")
        shown += 1
        if shown >= a.max:
            print(f"…(已截断, 共{len(sel)}段, 用 -p 指定范围)")
            break
    tb = st.doc.tables
    print(f"段落{len(ps)} 表格{len(tb)} 节{len(st.doc.sections)} 批注{len(list(st.doc.comments))}")


def c_read(st, a):
    if a.table is not None:
        for row in st.doc.tables[a.table].rows:
            print("\t".join(c.text.replace("\n", "⏎") for c in row.cells))
        return
    for i, p in select(st, a.p):
        print(f"[{i}] {ptext(p)}")


def c_find(st, a):
    rx, n = re.compile(a.pattern), 0
    for i, p in enumerate(st.paras()):
        for m in rx.finditer(ptext(p)):
            s, e = max(0, m.start() - 15), m.end() + 15
            print(f"[{i}] …{ptext(p)[s:e]}…")
            n += 1
    for k, t in enumerate(st.doc.tables):
        for ri, row in enumerate(t.rows):
            for ci, c in enumerate(row.cells):
                if rx.search(c.text):
                    print(f"[表{k} r{ri}c{ci}] {short(c.text)}")
                    n += 1
    print(f"共 {n} 处")


def c_replace(st, a):
    targets = select(st, a.p, a.old)
    if a.track:
        idxs = [i for i, _ in targets]

        def fn(x, body):
            n = 0
            for i in idxs:
                pid = body[i].get(f"{{{W14}}}paraId")
                cnt = "".join(t.text or "" for t in body[i].iter(qn("w:t"))).count(a.old)
                for _ in range(cnt if a.all else min(cnt, 1)):
                    x.replace_text(pid, find=a.old, replace=a.new, author=a.author, tracked=True)
                    n += 1
                if n and not a.all:
                    return n
            return n
        n = st.mcp(fn)
    else:
        n = 0
        for _, p in targets:
            for runs in isolate(p, a.old, None if a.all else 1):
                runs[0].text = a.new
                for r in runs[1:]:
                    r._element.getparent().remove(r._element)
                n += 1
                if not a.all:
                    break
            if n and not a.all:
                break
    st.mut = True
    print(f"已替换 {n} 处{'(修订)' if a.track else ''}")


def c_font(st, a):
    n = 0
    for _, p in select(st, a.p, a.t):
        groups = isolate(p, a.t) if a.t else [p.runs]
        for runs in groups:
            for r in runs:
                font_apply(r.font, r._r, a)
                n += 1
    st.mut = True
    print(f"已设置 {n} 个文字块")


def c_para(st, a):
    sel = select(st, a.p)
    for _, p in sel:
        para_apply(p.paragraph_format, p._p, a)
    st.mut = True
    print(f"已设置 {len(sel)} 段")


def c_style(st, a):
    name = STYLE_ALIAS.get(a.name, a.name)
    s = st.doc.styles[name]
    font_apply(s.font, s.element, a)
    para_apply(s.paragraph_format, s.element, a)
    st.mut = True
    print(f"已修改样式 {name}")


def c_page(st, a):
    for sec in st.doc.sections:
        if a.size:
            w, h = PAGE[a.size.upper()]
            sec.page_width, sec.page_height = Mm(w), Mm(h)
        if a.orient:
            land = a.orient.startswith("l") or a.orient == "横"
            w, h = sorted((sec.page_width, sec.page_height))
            sec.orientation = WD_ORIENT.LANDSCAPE if land else WD_ORIENT.PORTRAIT
            sec.page_width, sec.page_height = (h, w) if land else (w, h)
        if a.margin:
            v = [float(x) for x in a.margin.split(",")]
            t, r, b, l = (v * 4)[:4] if len(v) == 1 else (v + v)[:4] if len(v) == 2 else v
            sec.top_margin, sec.right_margin, sec.bottom_margin, sec.left_margin = Mm(t), Mm(r), Mm(b), Mm(l)
    st.mut = True
    print(f"已设置 {len(st.doc.sections)} 节页面")


def add_page_field(p, fmt):
    pre, _, post = fmt.partition("{PAGE}")
    if pre:
        p.add_run(pre)
    r = p.add_run()
    for kind, txt in (("begin", None), (None, " PAGE "), ("separate", None), (None, "1"), ("end", None)):
        if kind:
            e = OxmlElement("w:fldChar")
            e.set(qn("w:fldCharType"), kind)
        else:
            e = OxmlElement("w:instrText" if txt == " PAGE " else "w:t")
            e.set(qn("xml:space"), "preserve")
            e.text = txt
        r._r.append(e)
    if post:
        p.add_run(post)


def c_hf(st, a):
    for sec in st.doc.sections:
        hf = sec.header if a.cmd == "header" else sec.footer
        hf.is_linked_to_previous = False
        p = hf.paragraphs[0]
        for r in list(p.runs):
            r._r.getparent().remove(r._r)
        for extra in hf.paragraphs[1:]:
            extra._p.getparent().remove(extra._p)
        if "{PAGE}" in a.text:
            add_page_field(p, a.text)
        else:
            p.add_run(a.text)
        if a.align:
            p.alignment = getattr(WD_ALIGN_PARAGRAPH, ALIGN[a.align])
        if a.name or a.cn or a.en or a.size:
            for r in p.runs:
                font_apply(r.font, r._r, a)
    st.mut = True
    print(f"已设置{'页眉' if a.cmd == 'header' else '页脚'}: {short(a.text)}")
def c_comment(st, a):
    if a.list:
        for c in st.doc.comments:
            print(f"{c.comment_id}|{c.author}|{short(c.text, 60)}")
        return
    (i, p), = select(st, a.p, a.t)[:1]
    runs = isolate(p, a.t, 1)[0] if a.t else (p.runs or [p.add_run("")])
    st.doc.add_comment(runs, text=a.text, author=a.author, initials=a.author[:2])
    st.mut = True
    print(f"已在段{i}添加批注: {short(a.text)}")


def c_track(st, a):
    if a.action == "list":
        n = 0
        for e in st.doc.element.body.iter(qn("w:ins"), qn("w:del")):
            txt = "".join(t.text or "" for t in e.iter(qn("w:t"), qn("w:delText")))
            print(f"{'插入' if e.tag == qn('w:ins') else '删除'}|{e.get(qn('w:author'))}|{short(txt)}")
            n += 1
        print(f"共 {n} 处修订")
        return
    fn = "accept_changes" if a.action == "accept" else "reject_changes"
    r = st.mcp(lambda x, b: getattr(x, fn)(author=a.author))
    st.mut = True
    print(f"{'接受' if a.action == 'accept' else '拒绝'}: {r}")


def c_validate(st, a):
    from lxml import etree
    st.doc.save(st.work)
    errs, ids = [], {}
    with zipfile.ZipFile(st.work) as z:
        if z.testzip():
            errs.append("zip 损坏")
        for n in z.namelist():
            if n.endswith((".xml", ".rels")):
                try:
                    root = etree.fromstring(z.read(n))
                except etree.XMLSyntaxError as e:
                    errs.append(f"{n}: {e}")
                    continue
                for el in root.iter():
                    pid = el.get(f"{{{W14}}}paraId")
                    if pid:
                        ids[pid] = ids.get(pid, 0) + 1
        body = z.read("word/document.xml").decode("utf-8")
    dup = [k for k, v in ids.items() if v > 1]
    if dup:
        errs.append(f"重复 paraId {len(dup)} 个")
    starts = set(re.findall(r'commentRangeStart w:id="(\d+)"', body))
    ends = set(re.findall(r'commentRangeEnd w:id="(\d+)"', body))
    if starts != ends:
        errs.append(f"批注范围不配对: {starts ^ ends}")
    print("OK" if not errs else "问题:\n" + "\n".join(errs))
    return 1 if errs else 0


PS_PDF = r"""$ErrorActionPreference='Stop';$w=New-Object -ComObject Word.Application;$w.Visible=$false;$w.DisplayAlerts=0
try{$d=$w.Documents.Open('%s',$false,$true,$false);$d.ExportAsFixedFormat('%s',17);$d.Close([ref]0)}finally{$w.Quit([ref]0)}"""
PS_KILL = ("Get-CimInstance Win32_Process -Filter \"Name='WINWORD.EXE'\" | ?{$_.CommandLine -like '*/Automation*'}"
           " | %{Stop-Process -Id $_.ProcessId -Force}")


def c_topdf(st, a):
    st.doc.save(st.work)
    out = os.path.abspath(a.pdf or os.path.splitext(a.file)[0] + ".pdf")
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command", PS_PDF % (st.work, out)],
                           capture_output=True, text=True, timeout=a.timeout)
    except subprocess.TimeoutExpired:
        subprocess.run(["powershell", "-NoProfile", "-Command", PS_KILL], timeout=30)
        raise SystemExit(f"错误: Word 超时 {a.timeout}s，已结束自动化 Word 进程")
    subprocess.run(["powershell", "-NoProfile", "-Command", PS_KILL], timeout=30)
    if r.returncode or not os.path.exists(out):
        raise SystemExit("错误: 导出失败 " + short(r.stderr, 200))
    print(f"PDF: {out} ({os.path.getsize(out)} B)")


def c_batch(st, a, parser):
    with open(a.script, encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip() and not l.lstrip().startswith("#")]
    for k, line in enumerate(lines, 1):
        sub = parser.parse_args([a.file] + shlex.split(line))
        print(f"#{k} ", end="")
        if sub.func(st, sub):
            return 1
def font_opts(sp):
    sp.add_argument("--name", help="中英文同一字体")
    sp.add_argument("--cn", help="中文字体(eastAsia)")
    sp.add_argument("--en", help="西文字体(ascii/hAnsi)")
    sp.add_argument("--size", help="磅值或字号名, 如 12 / 小四")
    sp.add_argument("--bold", choices="01")
    sp.add_argument("--italic", choices="01")
    sp.add_argument("--underline", choices="01")
    sp.add_argument("--color", help="RRGGBB")


def para_opts(sp):
    sp.add_argument("--align", help="left/center/right/justify/distribute 或 左/居中/右/两端/分散")
    sp.add_argument("--line", help="倍数如 1.5；固定值 28pt；最小值 >=20pt")
    sp.add_argument("--before", help="段前 pt")
    sp.add_argument("--after", help="段后 pt")
    sp.add_argument("--indent", help="首行缩进: 2(字符) 或 0.74cm")
    sp.add_argument("--left", help="左缩进: 字符数 或 Ncm")


def build():
    ap = argparse.ArgumentParser(prog="docx_tool")
    ap.add_argument("file")
    ap.add_argument("-o", "--out")
    ap.add_argument("--inplace", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)
    P = "段落选择: all | 3 | 2-5,8 | ~子串 | s:样式名"

    s = sub.add_parser("outline"); s.add_argument("-p", help=P); s.add_argument("-w", type=int, default=40)
    s.add_argument("--max", type=int, default=200); s.add_argument("--empty", action="store_true"); s.set_defaults(func=c_outline)
    s = sub.add_parser("read"); s.add_argument("-p", default="all", help=P); s.add_argument("--table", type=int); s.set_defaults(func=c_read)
    s = sub.add_parser("find"); s.add_argument("pattern", help="正则"); s.set_defaults(func=c_find)
    s = sub.add_parser("replace"); s.add_argument("old"); s.add_argument("new"); s.add_argument("-p", default="all", help=P)
    s.add_argument("--all", action="store_true"); s.add_argument("--track", action="store_true")
    s.add_argument("--author", default="AI"); s.set_defaults(func=c_replace)
    s = sub.add_parser("font"); s.add_argument("-p", default="all", help=P); s.add_argument("-t", help="仅此子串")
    font_opts(s); s.set_defaults(func=c_font)
    s = sub.add_parser("para"); s.add_argument("-p", default="all", help=P); para_opts(s); s.set_defaults(func=c_para)
    s = sub.add_parser("style"); s.add_argument("name", help="样式名, 如 正文 / 标题1 / Normal")
    font_opts(s); para_opts(s); s.set_defaults(func=c_style)
    s = sub.add_parser("page"); s.add_argument("--size", help="A4/A3/A5/B5/LETTER")
    s.add_argument("--orient", help="portrait/landscape 或 竖/横"); s.add_argument("--margin", help="mm: 全部 | 上下,左右 | 上,右,下,左")
    s.set_defaults(func=c_page)
    for name in ("header", "footer"):
        s = sub.add_parser(name); s.add_argument("text", help="可含 {PAGE} 页码域"); s.add_argument("--align")
        font_opts(s); s.set_defaults(func=c_hf)
    s = sub.add_parser("comment"); s.add_argument("--list", action="store_true"); s.add_argument("-p", default="all", help=P)
    s.add_argument("-t", help="锚定子串(默认整段)"); s.add_argument("--text", default=""); s.add_argument("--author", default="AI")
    s.set_defaults(func=c_comment)
    s = sub.add_parser("track"); s.add_argument("action", choices=["list", "accept", "reject"]); s.add_argument("--author")
    s.set_defaults(func=c_track)
    s = sub.add_parser("validate"); s.set_defaults(func=c_validate)
    s = sub.add_parser("topdf"); s.add_argument("--pdf"); s.add_argument("--timeout", type=int, default=90); s.set_defaults(func=c_topdf)
    s = sub.add_parser("batch", help="每行一条子命令(不含文件名)"); s.add_argument("script"); s.set_defaults(func=None)
    return ap


def main(argv=None):
    ap = build()
    a = ap.parse_args(argv)
    if not os.path.exists(a.file):
        raise SystemExit(f"错误: 文件不存在 {a.file}")
    st = State(a.file)
    try:
        rc = c_batch(st, a, ap) if a.cmd == "batch" else a.func(st, a)
        if st.mut and not rc:
            out = a.file if a.inplace else (a.out or os.path.splitext(a.file)[0] + "_out.docx")
            st.doc.save(out)
            print(f"已保存: {out}")
        return rc or 0
    finally:
        shutil.rmtree(st.tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
