# 安装和使用指南

## 前置要求

- Kimi Code 已安装
- Git 已安装
- 拥有必要的API密钥（Claude API、DeepSeek API等）

## 安装步骤

### 1. 克隆仓库

```bash
git clone https://github.com/RAYNLIU2005/kimicodeskills_mcps.git
cd kimicodeskills_mcps
```

### 2. 安装Skills

将skills复制到你的Kimi Code配置目录。

**Windows:**
```bash
xcopy /E /I skills\* %USERPROFILE%\.kimi-code\skills\
```

**Linux/macOS:**
```bash
cp -r skills/* ~/.kimi-code/skills/
```

### 3. 配置系统提示词

1. 复制文件到Kimi Code配置目录：
```bash
# Windows
copy system-prompts\AGENTS.md %USERPROFILE%\.kimi-code\
copy system-prompts\TOOLS.md %USERPROFILE%\.kimi-code\

# Linux/macOS
cp system-prompts/AGENTS.md ~/.kimi-code/
cp system-prompts/TOOLS.md ~/.kimi-code/
```

2. 创建配置文件：
```bash
# Windows
copy system-prompts\config.example.toml %USERPROFILE%\.kimi-code\config.toml

# Linux/macOS
cp system-prompts/config.example.toml ~/.kimi-code/config.toml
```

3. 编辑 `~/.kimi-code/config.toml`，替换以下占位符：
   - `https://your-api-endpoint` → 你的实际API endpoint
   - `sk-xxxxxxxxx-replace-with-your-key` → 你的实际API密钥

### 4. 配置MCP工具

查看 `mcp-config/mcp.json` 的内容，根据需要更新你的 `~/.kimi-code/mcp.json`：

```json
{
  "mcpServers": {
    "fetch": {
      "command": "npx",
      "args": ["-y", "@kazuph/mcp-fetch@1.6.3"]
    },
    "pubmed": {
      "command": "npx",
      "args": ["-y", "@cyanheads/pubmed-mcp-server@2.10.19"]
    },
    "openalex": {
      "command": "npx",
      "args": ["-y", "@cyanheads/openalex-mcp-server@0.8.0"]
    },
    "exa": {
      "command": "npx",
      "args": ["-y", "mcp-remote@0.14.3", "https://mcp.exa.ai/mcp"]
    }
  }
}
```

### 5. 重启Kimi Code

关闭并重新启动Kimi Code使配置生效。

## 验证安装

### 验证Skills已加载

在Kimi Code中运行命令查看可用skills：
```
/skill list
```

你应该看到以下skills：
- citation-management
- docx
- literature-review
- paper-lookup
- pdf
- web-research

### 验证MCP工具已连接

检查MCP服务器状态（可在Kimi Code的工具面板中查看）。

### 测试配置

创建新的chat会话，尝试使用一个skill：
```
使用 paper-lookup skill 搜索关于 machine learning 的论文
```

## 常见问题

### Q: Skills没有加载？
**A:** 确保：
1. Skills已复制到 `~/.kimi-code/skills/` 目录
2. Kimi Code已重启
3. 检查Kimi Code的日志文件是否有错误信息

### Q: API密钥错误？
**A:** 
1. 检查 `~/.kimi-code/config.toml` 中的密钥是否正确
2. 确保密钥没有多余的空格
3. 验证API endpoint URL是否正确

### Q: MCP工具无法连接？
**A:**
1. 确保 `mcp.json` 配置正确
2. 检查npm是否可用（运行 `npm --version`）
3. 尝试手动运行其中一个MCP服务器进行调试

### Q: 敏感信息被推送到GitHub了？
**A:** 立即：
1. 在GitHub上删除仓库
2. 重新创建仓库
3. 立即轮换所有已暴露的API密钥
4. 确认 `.gitignore` 配置正确

## 更新维护

### 更新Skills

从仓库拉取最新更改：
```bash
git pull origin main
xcopy /E /I skills\* %USERPROFILE%\.kimi-code\skills\
```

### 更新配置

比较你的配置与仓库中的示例：
```bash
diff ~/.kimi-code/AGENTS.md system-prompts/AGENTS.md
```

## 备份

建议定期备份你的Kimi Code配置：
```bash
# 创建备份
tar czf kimi-code-backup-$(date +%Y%m%d).tar.gz ~/.kimi-code/

# 或在Windows中：
# xcopy /E /I %USERPROFILE%\.kimi-code\ kimi-code-backup\
```

## 获取帮助

- 查看Kimi Code官方文档：https://docs.kimi-code.dev
- 检查仓库Issues：https://github.com/RAYNLIU2005/kimicodeskills_mcps/issues
- 查看skills的各自README文档

---

**最后更新**：2026-10-04
