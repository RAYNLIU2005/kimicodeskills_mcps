#!/usr/bin/env bash
# pdf 技能一键测试：bash run_tests.sh
set -u
PY="C:/Users/raynl/.kimi-code/venvs/docs/Scripts/python.exe"
HERE="$(cd "$(dirname "$0")" && pwd)"
TOOL="$HERE/../scripts/pdf_tool.py"
VERIFY="$HERE/verify.py"
FIX="$HERE/fixtures"
TMP="$HERE/tmp"
export PYTHONIOENCODING=utf-8

PASS=0
FAIL=0
ok(){ echo "PASS  $1"; PASS=$((PASS+1)); }
bad(){ echo "FAIL  $1"; FAIL=$((FAIL+1)); }
pt(){ "$PY" "$TOOL" "$@"; }
runpt(){ local name="$1" out="$2"; shift 2
  if pt "$@" >"$out" 2>&1; then ok "$name"; else bad "$name"; sed 's/^/      /' "$out"; fi; }
runpy(){ local name="$1" out="$2"; shift 2
  if "$PY" "$VERIFY" "$@" >"$out" 2>&1; then ok "$name"; else bad "$name"; sed 's/^/      /' "$out"; fi; }
has(){ if grep -qF -- "$3" "$2"; then ok "$1"; else bad "$1（输出缺少: $3）"; sed 's/^/      /' "$2"; fi; }
hasnot(){ if grep -qF -- "$3" "$2"; then bad "$1（不应出现: $3）"; else ok "$1"; fi; }
expect_fail(){ local name="$1"; shift
  if "$@" >"$TMP/fail.txt" 2>&1; then bad "$name（本应失败）"; else ok "$name"; fi; }

rm -rf "$TMP"
mkdir -p "$TMP"

echo "== 生成 fixture =="
if "$PY" "$HERE/make_fixtures.py" >"$TMP/gen.txt" 2>&1; then ok "生成 fixture"; cat "$TMP/gen.txt"; else
  bad "生成 fixture"; sed 's/^/      /' "$TMP/gen.txt"
fi

echo "== info =="
runpt "info text_cn.pdf" "$TMP/o" info "$FIX/text_cn.pdf"
has "info 页数=3" "$TMP/o" "pages=3"
has "info enc=no" "$TMP/o" "enc=no"
has "info 每页文本量" "$TMP/o" "p1: text="

echo "== text =="
runpt "text 全文" "$TMP/o" text "$FIX/text_cn.pdf"
has "text 含中文关键词" "$TMP/o" "预算"
has "text 含英文" "$TMP/o" "Hello English"
has "text 有分页标记" "$TMP/o" "p3"
runpt "text -p 2" "$TMP/o" text -p 2 "$FIX/text_cn.pdf"
has "text -p 2 取第2页" "$TMP/o" "Page 2 English only"
hasnot "text -p 2 不含第1页" "$TMP/o" "预算总表"

echo "== search =="
runpt "search 预算" "$TMP/o" search 预算 "$FIX/text_cn.pdf"
has "search 命中页码" "$TMP/o" "p1:"
has "search 统计行" "$TMP/o" "matches="
runpt "search -i budget" "$TMP/o" search -i budget "$FIX/text_cn.pdf"
has "search -i 命中 p2" "$TMP/o" "p2:"
runpt "search 未命中" "$TMP/o" search zzzz "$FIX/text_cn.pdf"
has "search 未命中 matches=0" "$TMP/o" "matches=0"

echo "== tables =="
runpt "tables table.pdf" "$TMP/o" tables "$FIX/table.pdf"
has "tables 识别到表" "$TMP/o" "tables=1"
has "tables 含 1200" "$TMP/o" "1200"
has "tables 含 800" "$TMP/o" "800"

echo "== merge / split =="
runpt "merge" "$TMP/o" merge -o "$TMP/m.pdf" "$FIX/text_cn.pdf" "$FIX/multi.pdf"
runpy "merge 页数=9" "$TMP/o2" pages "$TMP/m.pdf" 9
has "merge 汇总行" "$TMP/o" "merged=2"
runpt "split" "$TMP/o" split -o "$TMP/split" "$FIX/multi.pdf"
n=$(ls "$TMP/split" | wc -l)
if [ "$n" -eq 6 ]; then ok "split 产出 6 个文件"; else bad "split 产出 $n 个文件（期望 6）"; fi
runpy "split 单页文件页数=1" "$TMP/o" pages "$TMP/split/multi_p3.pdf" 1
runpt "split --every 2" "$TMP/o" split -o "$TMP/split2" --every 2 "$FIX/multi.pdf"
runpy "split --every 2 首页数=2" "$TMP/o" pages "$TMP/split2/multi_p1-2.pdf" 2

echo "== extract-pages / delete-pages =="
runpt "extract-pages" "$TMP/o" extract-pages -p 2-3 -o "$TMP/ex.pdf" "$FIX/multi.pdf"
runpy "extract-pages 页数=2" "$TMP/o" pages "$TMP/ex.pdf" 2
runpt "extract-pages 内容" "$TMP/o" text "$TMP/ex.pdf"
has "extract-pages 含 Page 2" "$TMP/o" "Page 2"
has "extract-pages 含 Page 3" "$TMP/o" "Page 3"
runpt "delete-pages" "$TMP/o" delete-pages -p 1-4 -o "$TMP/del.pdf" "$FIX/multi.pdf"
runpy "delete-pages 页数=2" "$TMP/o" pages "$TMP/del.pdf" 2
runpt "delete-pages 内容" "$TMP/o" text "$TMP/del.pdf"
has "delete-pages 剩下 Page 5" "$TMP/o" "Page 5"

echo "== rotate =="
runpt "rotate" "$TMP/o" rotate -p 1 --angle 90 -o "$TMP/rot.pdf" "$FIX/multi.pdf"
runpy "rotate /Rotate=90" "$TMP/o" rotate "$TMP/rot.pdf" 1 90
runpy "rotate 页数不变" "$TMP/o" pages "$TMP/rot.pdf" 6

echo "== form =="
runpt "form 读取" "$TMP/o" form "$FIX/form.pdf"
has "form 字段数=2" "$TMP/o" "fields=2"
has "form 预填值 name=Alice" "$TMP/o" "name=Alice"
runpt "form 填充" "$TMP/o" form --set name=Bob --set city=Shanghai -o "$TMP/form.pdf" "$FIX/form.pdf"
runpy "form 回读 name=Bob" "$TMP/o" field "$TMP/form.pdf" name Bob
runpy "form 回读 city=Shanghai" "$TMP/o" field "$TMP/form.pdf" city Shanghai

echo "== annotate =="
runpt "annotate" "$TMP/o" annotate -p 2 -t "审核通过" -o "$TMP/ann.pdf" "$FIX/multi.pdf"
runpy "annotate 回读内容" "$TMP/o" annot "$TMP/ann.pdf" "审核通过"

echo "== meta =="
runpt "meta 读取" "$TMP/o" meta "$FIX/multi.pdf"
has "meta 有 title 行" "$TMP/o" "title="
runpt "meta 写入" "$TMP/o" meta --title T1 --author A1 -o "$TMP/meta.pdf" "$FIX/multi.pdf"
runpy "meta 回读 title=T1" "$TMP/o" meta "$TMP/meta.pdf" title T1

echo "== encrypt / decrypt =="
runpt "encrypt" "$TMP/o" encrypt --password pw123 -o "$TMP/enc.pdf" "$FIX/multi.pdf"
runpy "encrypt 已加密" "$TMP/o" encrypted "$TMP/enc.pdf" yes
runpy "encrypt 无密码不可读" "$TMP/o" need-password "$TMP/enc.pdf"
expect_fail "encrypt 无密码时 info 报错" pt info "$TMP/enc.pdf"
runpt "decrypt" "$TMP/o" decrypt --password pw123 -o "$TMP/dec.pdf" "$TMP/enc.pdf"
runpy "decrypt 未加密" "$TMP/o" encrypted "$TMP/dec.pdf" no
runpy "decrypt 页数=6" "$TMP/o" pages "$TMP/dec.pdf" 6

echo "== images / 扫描件 =="
runpt "images 列表" "$TMP/o" images "$FIX/scanned.pdf"
has "images 计数=1" "$TMP/o" "images=1"
runpt "images 导出" "$TMP/o" images --export "$TMP/img" "$FIX/scanned.pdf"
ni=$(ls "$TMP/img" 2>/dev/null | wc -l)
if [ "$ni" -ge 1 ]; then ok "images --export 产出 $ni 个文件"; else bad "images --export 无产出"; fi
runpt "info scanned" "$TMP/o" info "$FIX/scanned.pdf"
has "scanned 无文本层 text=0" "$TMP/o" "text=0"
has "scanned 标记扫描页" "$TMP/o" "扫描页"
runpt "text scanned 提示" "$TMP/o" text "$FIX/scanned.pdf"
has "text 扫描件提示" "$TMP/o" "扫描件"

echo "== 安全：不覆盖输入 =="
expect_fail "缺 -o 时 rotate 报错" pt rotate -p 1 --angle 90 "$FIX/multi.pdf"
if [ ! -e "$TMP/never.pdf" ]; then ok "缺 -o 未写出任何文件"; else bad "缺 -o 却写出了文件"; fi
runpy "缺 -o 未改动原文件" "$TMP/o" pages "$FIX/multi.pdf" 6
expect_fail "越界页码报错" pt text -p 99 "$FIX/text_cn.pdf"
expect_fail "非 90 倍数角度报错" pt rotate --angle 45 -o "$TMP/x.pdf" "$FIX/multi.pdf"
cp "$FIX/text_cn.pdf" "$TMP/inplace.pdf"
runpt "--inplace 覆盖" "$TMP/o" rotate -p 1 --angle 90 --inplace "$TMP/inplace.pdf"
runpy "--inplace 生效" "$TMP/o" rotate "$TMP/inplace.pdf" 1 90
runpy "--inplace 页数不变" "$TMP/o" pages "$TMP/inplace.pdf" 3

echo "----------------------------------------"
echo "PASS=$PASS FAIL=$FAIL"
rm -rf "$TMP"
[ "$FAIL" -eq 0 ]
