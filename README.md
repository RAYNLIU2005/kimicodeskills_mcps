# Kimi Code Skills、系统提示词及MCP工具集合

这是一个完整的Kimi Code配置仓库，包含所有自定义skill、系统提示词和MCP工具配置。

## 📁 仓库结构

```
kimicodeskills_mcps/
├── skills/                    # 所有自定义skill脚本
│   ├── citation-management/   # 学术文献管理和引文检索
│   ├── docx/                  # Word文档编辑
│   ├── literature-review/     # 文献综述工具
│   ├── paper-lookup/          # 论文查询和检索
│   ├── pdf/                   # PDF处理
│   └── web-research/          # 网络研究
│
├── system-prompts/            # 系统级配置和提示词
│   ├── AGENTS.md              # 全局指令和系统提示词
│   ├── TOOLS.md               # 工具安装台账
│   ├── config.example.toml    # 配置模板（敏感信息脱敏）
│   └── config.toml            # 实际配置（需自行补充密钥）
│
├── mcp-config/                # MCP服务器配置
│   └── mcp.json               # MCP工具定义
│
└── docs/                      # 文档和使用说明
    └── SETUP.md               # 安装和使用指南
```

## 🚀 快速开始

### 1. 安装Skills

将 `skills/` 目录中的所有skill复制到你的Kimi Code配置目录：

```bash
# Windows
xcopy /E /I skills\* %USERPROFILE%\.kimi-code\skills\

# Linux/macOS
cp -r skills/* ~/.kimi-code/skills/
```

### 2. 配置系统提示词

1. 将 `system-prompts/AGENTS.md` 和 `TOOLS.md` 复制到 `~/.kimi-code/`
2. 根据 `system-prompts/config.example.toml` 创建你的 `config.toml`
3. 填入你的API密钥和endpoints

```bash
# 复制配置文件
cp system-prompts/AGENTS.md ~/.kimi-code/
cp system-prompts/TOOLS.md ~/.kimi-code/
cp system-prompts/config.example.toml ~/.kimi-code/config.toml
```

3. 编辑 `~/.kimi-code/config.toml` 填入实际的API密钥

### 3. 配置MCP工具

将 `mcp-config/mcp.json` 的内容合并到你的 `~/.kimi-code/mcp.json`：

```bash
# 查看当前MCP配置
cat ~/.kimi-code/mcp.json

# 或者直接复制（如果是新安装）
cp mcp-config/mcp.json ~/.kimi-code/
```

## 📚 Skills说明

### citation-management
学术文献管理和引文检索工具，支持多个学术数据库的查询。

### docx
Word文档编辑和处理能力，支持格式设置、字体、段落等编辑。

### literature-review
完整的文献综述工具，支持系统性、范围和叙述性文献综述。

### paper-lookup
跨越18个学术API的论文查询工具，包括PubMed、arXiv、OpenAlex等。

### pdf
PDF文件处理工具，支持读取、合并、拆分等操作。

### web-research
网络研究工具，用于高效的互联网搜索和信息检索。

## 🔧 系统配置说明

### AGENTS.md
包含全局指令、语言设置、token经济指南、工具安装指南和sub-agent规则。

### TOOLS.md
工具安装台账，记录所有已安装的开发工具、运行时和依赖的版本、安装方式和卸载命令。

### config.toml
Kimi Code主配置文件，包括：
- 默认模型设置
- 权限模式（yolo/manual/auto）
- 计划模式配置
- 多个API提供商配置（flow、deepseek等）
- 模型能力定义

## 🔐 安全性

- **敏感信息脱敏**：`config.toml` 中的API密钥已使用占位符替换
- **gitignore**：`.gitignore` 已配置以防止意外提交密钥
- **示例配置**：使用 `config.example.toml` 作为模板创建你的真实配置

## 📝 使用场景

这套配置特别适合：

- 📖 学术研究和文献综述
- 📄 文档处理（Word/PDF编辑）
- 🔍 学术文献查询和管理
- 🌐 网络信息研究
- 🤖 AI辅助开发和代码生成

## 🔄 更新维护

所有文件应与你的本地 `~/.kimi-code/` 配置保持同步。定期检查并更新：

1. Skills更新
2. 系统提示词改进
3. MCP工具版本更新

## 📞 反馈和贡献

如有任何问题或改进建议，欢迎提交Issue或Pull Request。

---

**最后更新**：2026-10-04
