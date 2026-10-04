---
name: pdf
description: 处理 PDF 文件：读取文本/表格、合并拆分、旋转、页面增删、表单、批注、元数据、加解密。当用户需要读取或操作 PDF 时使用。
allowed-tools: Read Bash
---

# pdf：PDF 读取与编辑

## 何时用 / 何时不用

- 用于：读取 PDF 文本/表格、合并拆分、旋转、增减页、表单、批注、元数据、加解密、导出图片。
- 不用于：扫描件 OCR（本工具只能提示"无文本层"，**不要循环重试提取**）；从零生成全新 PDF（用 reportlab 等）。

## 调用模板

技能目录不在工作目录内，必须用绝对路径并加双引号：

```bash
PYTHONIOENCODING=utf-8 "C:/Users/raynl/.kimi-code/venvs/docs/Scripts/python.exe" \
  "C:/Users/raynl/.kimi-code/skills/pdf/scripts/pdf_tool.py" <子命令> [参数]
```

`token 高效的 PDF 工具：读取、合并拆分、表格、表单、批注、元数据、加密。`

## 子命令

| 子命令 | 作用 |
| --- | --- |
| `info` | 概览：页数/尺寸/加密/每页文本与图片数量 |
| `text` | 提取文本（无文本层会提示扫描件） |
| `search` | 搜索文本，输出 `页码: 命中行` |
| `tables` | 提取表格（pdfplumber） |
| `merge` | 合并多个 PDF，`-o` 必填 |
| `split` | 拆分：`-o` 为输出目录 |
| `extract-pages` | 抽取指定页为新 PDF |
| `delete-pages` | 删除指定页 |
| `rotate` | 旋转页面（90 的倍数） |
| `form` | 列出表单字段；`--set k=v` 填充 |
| `annotate` | 添加文本批注 |
| `meta` | 读取/写入元数据 |
| `encrypt` | 加密（`--password` 为新密码） |
| `decrypt` | 解密（`--password` 为原密码） |
| `images` | 列出内嵌图片；`--export DIR` 导出 |

## 关键约定

- `info` 首行：`file=… pages=N size=WxHpt enc=yes|no`；每页 `pN: text=<n>c imgs=<m>`，扫描页追加 ` [无文本层/扫描页]`。
- 空文本页输出 `[本页无文本层：可能是扫描件，需要 OCR；不要循环重试提取]`。
- `--max-chars` 默认 20000，超限追加 `[truncated]`。
- 页码语法 `1-3,5,8-`（支持开区间 `8-`）。
- `search` 命中行前缀 `pN:`，末行 `matches=N`。
- 写操作无 `-o` 且无 `--inplace` → 退出码 2。
- 落盘先写 `.pdftmp` 再 `os.replace`；打开用 `BytesIO` 规避 Windows 文件锁。

## 坑

- Windows 路径含空格，**必须双引号**；技能目录用绝对路径。
- 输出中文须 `PYTHONIOENCODING=utf-8`。

## 跑测试

```bash
bash "C:/Users/raynl/.kimi-code/skills/pdf/tests/run_tests.sh"
```

脚本用 `dirname "$0"` 定位，工作目录无关。
