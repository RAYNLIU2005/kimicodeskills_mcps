# 工具安装台账

| 日期 | 工具 | 版本 | 安装方式 | 用途 | 卸载命令 |
|---|---|---|---|---|---|
| 预装 | Node.js | v22.13.1 | 用户自装 | npx 运行 MCP | - |
| 预装 | Git | 2.55.0 | 用户自装 | 版本控制 | - |
| 预装 | winget | v1.29.380 | 系统自带 | 包管理 | - |
| 2026-10-02 | skills: paper-lookup, literature-review, citation-management | K-Dense main | git 克隆复制 | 文献检索 | 删除 `~/.kimi-code/skills/<名称>` |
| 2026-10-02 | MCP: pubmed / openalex / exa | 2.10.19 / 0.8.0 / mcp-remote 0.14.3 | `mcp.json`（npx） | 文献、语义搜索 | 从 `mcp.json` 删除对应条目 |
| 2026-10-02 | uv | 0.12.22 | 官方脚本 `astral.sh/uv/0.12.22/install.ps1` → `~/.local/bin` | Python 版本/包管理 | 删除 `~/.local/bin/uv*.exe` |
| 2026-10-02 | Python | 3.12.15 | `uv python install 3.12` | 运行 skill 脚本 | `uv python uninstall 3.12` |
| 2026-10-02 | venv docs（python-docx 1.2.0, lxml 6.1.3, pypdf 6.19.0, pdfplumber 0.11.10, docx-mcp-server 0.7.4） | 见左 | `uv venv ~/.kimi-code/venvs/docs` + `uv pip install` | Word/PDF skill | 删除 `~/.kimi-code/venvs/docs` |
| 2026-10-02 | reportlab 4.4.2, pillow 12.3.0（venv docs） | 见左 | `uv pip install`（PDF 子 agent） | PDF 测试夹具生成 | `uv pip uninstall --python ~/.kimi-code/venvs/docs/Scripts/python.exe reportlab pillow` |
| 2026-10-02 | skills: docx（自研，复用 docx-mcp-server MIT）、pdf（自研） | - | `~/.kimi-code/skills/{docx,pdf}` | Word/PDF 编辑 | 删除对应目录 |
