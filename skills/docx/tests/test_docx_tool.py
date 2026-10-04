"""Run: ~/.kimi-code/venvs/docs/Scripts/python.exe tests/test_docx_tool.py [--word]"""
import os, subprocess, sys, tempfile, zipfile

import docx
sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.join(HERE, "..", "scripts", "docx_tool.py")
D = tempfile.mkdtemp(prefix="docxtest_")
SRC = os.path.join(D, "src.docx")
OUT = os.path.join(D, "out.docx")
ok = fail = 0


def run(*args, f=None):
    r = subprocess.run([sys.executable, TOOL, f or OUT, *args], capture_output=True, text=True,
                       encoding="utf-8", timeout=120)
    return r.returncode, r.stdout + r.stderr


def check(name, cond, info=""):
    global ok, fail
    ok, fail = (ok + 1, fail) if cond else (ok, fail + 1)
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else f"  -> {info[:300]}"))


def xml(part="word/document.xml", f=OUT):
    with zipfile.ZipFile(f) as z:
        return z.read(part).decode("utf-8") if part in z.namelist() else ""


d = docx.Document()
d.add_heading("测试标题 Test", 1)
p = d.add_paragraph("第一段：中文与")
p.add_run("English").bold = True
p.add_run("混排正文。")
d.add_paragraph("第二段：需要修改的文本在这里，修改的文本。")
for i in range(47):
    d.add_paragraph(f"填充段落{i}：这是一段用于测量输出大小的中文正文内容 lorem ipsum。")
t = d.add_table(rows=2, cols=2)
t.cell(0, 0).text = "单元格A"
d.sections[0].header.paragraphs[0].text = "旧页眉"
d.save(SRC)

rc, o = run("outline", f=SRC)
check("outline", rc == 0 and "1|Normal|第一段" in o and "表格1" in o, o)
print(f"  outline 输出 {len(o.encode('utf-8'))} B / {len(d.paragraphs)} 段")
rc, o = run("find", "修改的", f=SRC)
check("find", "共 2 处" in o, o)
rc, o = run("read", "--table", "0", f=SRC)
check("read table", "单元格A" in o, o)

rc, o = run("-o", OUT, "replace", "中文与English", "中文和English", f=SRC)
check("replace 跨文字块", rc == 0 and "已替换 1 处" in o and "第一段：中文和English混排" in docx.Document(OUT).paragraphs[1].text, o)
rc, o = run("--inplace", "font", "-p", "1", "-t", "English", "--en", "Arial", "--size", "小四", "--color", "FF0000")
x = xml()
check("font 子串", 'w:ascii="Arial"' in x and 'w:val="FF0000"' in x and 'w:sz w:val="24"' in x, o)
rc, o = run("--inplace", "font", "-p", "0", "--cn", "黑体", "--size", "三号", "--bold", "1")
check("font eastAsia", 'w:eastAsia="黑体"' in xml() and 'w:sz w:val="32"' in xml(), o)
rc, o = run("--inplace", "para", "-p", "1-2", "--align", "两端", "--line", "28pt", "--indent", "2", "--after", "0")
x = xml()
check("para", 'w:jc w:val="both"' in x and 'w:line="560"' in x and 'w:lineRule="exact"' in x and 'w:firstLineChars="200"' in x, o)
rc, o = run("--inplace", "style", "正文", "--cn", "宋体", "--en", "Times New Roman", "--size", "小四", "--line", "1.5")
s = xml("word/styles.xml")
check("style 正文", 'w:eastAsia="宋体"' in s and 'w:ascii="Times New Roman"' in s, o)
rc, o = run("--inplace", "page", "--size", "A4", "--margin", "37,28,35,26")
check("page", 'w:top="2098"' in xml() and 'w:w="11906"' in xml(), o)
rc, o = run("--inplace", "header", "新页眉", "--align", "居中", "--cn", "宋体", "--size", "小五")
check("header", "新页眉" in xml("word/header1.xml") and "旧页眉" not in xml("word/header1.xml"), o)
rc, o = run("--inplace", "footer", "第 {PAGE} 页", "--align", "center")
fx = "".join(xml(n) for n in zipfile.ZipFile(OUT).namelist() if "footer" in n)
check("footer 页码域", "PAGE" in fx and 'fldCharType="begin"' in fx, o)
rc, o = run("--inplace", "comment", "-p", "~第二段", "-t", "需要修改", "--text", "请核实", "--author", "审稿人")
x = xml()
check("comment 子串锚定", "commentRangeStart" in x and "请核实" in xml("word/comments.xml"), o)
rc, o = run("comment", "--list")
check("comment list", "审稿人" in o, o)
rc, o = run("--inplace", "replace", "这里", "此处", "-p", "~第二段", "--track", "--author", "张三")
x = xml()
check("replace 修订", "<w:ins " in x and "<w:delText" in x and 'w:author="张三"' in x, o)
rc, o = run("track", "list")
check("track list", "插入|张三" in o and "删除|张三" in o, o)
rc, o = run("-o", os.path.join(D, "acc.docx"), "track", "accept", "--author", "张三")
acc = os.path.join(D, "acc.docx")
check("track accept", "<w:ins " not in xml(f=acc) and "此处" in docx.Document(acc).paragraphs[2].text, o)
rc, o = run("validate")
check("validate", rc == 0 and o.strip().startswith("OK"), o)
ops = os.path.join(D, "ops.txt")
open(ops, "w", encoding="utf-8").write("font -p 3 --cn 仿宋\npara -p 3 --align right\n")
rc, o = run("--inplace", "batch", ops)
check("batch", rc == 0 and "#2" in o and 'w:eastAsia="仿宋"' in xml(), o)
rc, o = run("font", "-p", "999", "--cn", "宋体")
check("错误提示简洁", rc != 0 and "没有匹配的段落" in o and "Traceback" not in o, o)

if "--word" in sys.argv:
    rc, o = run("topdf", "--pdf", os.path.join(D, "out.pdf"))
    check("Word 打开并导出 PDF", rc == 0 and "PDF:" in o, o)

print(f"PASS={ok} FAIL={fail}")
import shutil; shutil.rmtree(D, ignore_errors=True)
sys.exit(1 if fail else 0)
