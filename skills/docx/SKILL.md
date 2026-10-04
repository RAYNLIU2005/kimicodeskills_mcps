---
name: docx
description: 读取和编辑 Word .docx：查看结构、查找替换、字体（含中文字体）、段落排版、样式、页面、页眉页脚、批注、修订。用户提到 Word、docx、字体、字号、排版、行距、批注、修订、页眉页脚时使用。
allowed-tools: Read Bash
---

# docx 编辑

所有操作用一个脚本完成，**不要解包或阅读 XML**，不要自己写 python-docx 代码。

```bash
PY=~/.kimi-code/venvs/docs/Scripts/python.exe; T=~/.kimi-code/skills/docx/scripts/docx_tool.py
$PY $T 文件.docx <子命令> [参数]        # 修改类默认另存为 文件_out.docx
$PY $T 文件.docx -o 新.docx <子命令>   # 指定输出；--inplace 覆盖原文件（先确认）
```

## 标准流程（通常 2～3 次调用）
1. `outline` 看段落编号、样式和开头文字（每段一行，约 100 B）。长文档用 `-p 0-80` 分段看。
2. 需要原文时用 `read -p 5-8` 或 `find 正则`，只读需要的部分。
3. 多项修改写进 ops 文件，用 `batch` 一次执行；最后跑 `validate`。

## 段落选择 `-p`
`all`（默认）｜`3`｜`2-5,8`｜`~子串`（包含该文字的段落）｜`s:标题1`（按样式）

## 子命令
| 任务 | 命令 |
|---|---|
| 结构 | `outline [-p ..] [-w 宽度] [--max 200]` |
| 读原文/表格 | `read -p 3-5`；`read --table 0` |
| 查找 | `find "正则"`（含表格） |
| 替换 | `replace 旧 新 [-p ..] [--all] [--track --author 名]`，可跨文字块，保留原格式 |
| 字体 | `font -p .. [-t 子串] --cn 宋体 --en "Times New Roman" --size 小四 --bold 1 --color FF0000` |
| 段落 | `para -p .. --align 两端 --line 1.5｜28pt｜>=20pt --before 0 --after 6 --indent 2 --left 0` |
| 样式 | `style 正文｜标题1｜Normal` 加字体和段落参数（全文统一格式时首选） |
| 页面 | `page --size A4 --orient 横 --margin 上,右,下,左`（单位 mm） |
| 页眉/页脚 | `header "文字"`；`footer "第 {PAGE} 页" --align 居中`（会替换原内容） |
| 批注 | `comment -p ~关键词 -t 锚定子串 --text 内容 --author 名`；`comment --list` |
| 修订 | `track list`；`track accept｜reject [--author 名]` |
| 校验 | `validate`（zip/XML/paraId/批注配对），输出 OK 即可 |
| 目视检查 | `topdf [--pdf 路径]`（Word 导出，90 秒超时自动结束） |
| 批量 | `batch ops.txt`，每行一条子命令，不写文件名，`#` 开头为注释 |

参数说明：`--name` 同时设置中西文字体；`--cn` 写入 eastAsia（中文字体必须用它，或用 `--name`）。`--indent 2` 表示 2 字符，`0.74cm` 表示厘米。`--line` 纯数字为倍数，带 pt 为固定值，`>=` 开头为最小值。

## 中文排版速查
字号：初号42 小初36 一号26 小一24 二号22 小二18 三号16 小三15 四号14 小四12 五号10.5 小五9（磅，`--size` 可直接写字号名）。
常见规范：正文宋体小四、1.5 倍行距、首行缩进 2 字符；公文（GB/T 9704）正文仿宋_GB2312 三号、固定值 28pt、页边距 37,26,35,28（上,右,下,左，按单位规范调整）。

## 注意
- 只改需要改的段落；格式统一优先改样式（`style`），比逐段设置更省调用。
- `replace` 只匹配单段内文本，不跨段。修订模式下用 `track list` 确认。
- 编号来自 `outline`；插入或删除段落后编号会变，要重新 `outline`。
- 有修订时，`outline`/`read`/`find` 显示的是"接受修订后"的文本（不含已删除文字）。
- 报错时只输出一行原因，按提示调整，不要重复尝试同一命令。
- 测试：`$PY ~/.kimi-code/skills/docx/tests/test_docx_tool.py [--word]`
