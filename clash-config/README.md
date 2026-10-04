# Clash Verge Rev 配置文件

这个目录包含 Clash Verge Rev 的完整配置文件。

## 📁 目录结构

```
clash-config/
├── config.yaml           # Clash 核心配置文件
├── verge.yaml            # Clash Verge 客户端配置
├── dns_config.yaml       # DNS 配置
├── profiles.yaml         # 配置文件管理
├── profiles/             # 各个配置文件
│   ├── *.yaml           # 不同的配置（代理、规则、脚本等）
│   └── *.js             # JavaScript 脚本配置
└── ruleset/             # 规则集
    └── *.yaml           # 各类规则文件
```

## 📝 文件说明

### config.yaml
Clash 的核心配置，包含：
- 端口设置（mixed-port、socks-port、http-port）
- 日志级别和策略模式
- TUN 模式配置
- DNS 劫持设置
- 外部控制器配置

### verge.yaml
Clash Verge Rev 客户端的特定配置，包含：
- UI主题和语言设置
- 自启动和系统托盘设置
- 性能和内存设置
- 自动更新和备份设置
- 延迟测试配置
- PAC 代理配置

### dns_config.yaml
DNS 解析配置，包含：
- DNS 服务器列表
- Fake IP 设置
- DNS 策略和分流
- Hosts 配置

### profiles.yaml
配置文件的管理和组织：
- 当前激活的配置
- 配置文件列表（远程订阅、本地配置等）
- 配置之间的依赖关系

### profiles/ 目录
存储各类配置文件：
- **merge.yaml**: 本地配置合并
- **script.js**: JavaScript 脚本（用于规则引擎）
- **rules.yaml**: 分流规则
- **proxies.yaml**: 代理服务器配置
- **groups.yaml**: 代理组（策略组）
- **remote**: 远程订阅配置

### ruleset/ 目录
规则集文件，用于特定应用或站点的分流规则。

## 🚀 使用说明

### 导入配置

1. 打开 Clash Verge Rev
2. 进入 "Profiles" 标签
3. 点击 "导入本地配置"
4. 选择此目录中的相应配置文件

### 更新配置

修改配置后：
```bash
# 刷新配置
# 在 Clash Verge 中：菜单 > 刷新配置
# 或重启应用
```

### 备份配置

定期备份配置文件：
```bash
# Windows
xcopy /E /I clash-config\ %USERPROFILE%\Clash-Config-Backup\

# Linux/macOS
cp -r clash-config/ ~/Clash-Config-Backup/
```

## ⚙️ 常用配置调整

### 修改代理端口
编辑 `config.yaml`：
```yaml
mixed-port: 7897      # 混合代理端口
socks-port: 7898      # SOCKS5 端口
port: 7899            # HTTP 端口
```

### 添加新的代理分流规则
1. 在 `profiles/` 中创建新的 `rules.yaml`
2. 添加规则条目
3. 在 `profiles.yaml` 中引用新规则

### 配置 DNS
编辑 `dns_config.yaml`：
```yaml
nameserver:
  - 8.8.8.8
  - https://doh.pub/dns-query
```

### 启用 TUN 模式
编辑 `config.yaml`：
```yaml
tun:
  enable: true
  auto-detect-interface: true
  auto-route: true
```

## 🔍 调试

### 查看日志
- Clash Verge 中查看实时日志
- 日志保存在 `%APPDATA%\io.github.clash-verge-rev.clash-verge-rev\logs\`

### 测试连接延迟
1. 在 Clash Verge 中右键点击代理
2. 选择 "Test Latency"
3. 查看延迟结果

### 验证规则
```bash
# 测试 DNS 解析
nslookup example.com 127.0.0.1

# 测试代理连接
curl -x socks5://127.0.0.1:7898 https://www.google.com
```

## 📚 相关文档

- [Clash Verge Rev 官方仓库](https://github.com/clash-verge-rev/clash-verge-rev)
- [Clash 文档](https://clash.gitbook.io/)
- [Mihomo 文档](https://wiki.metacubex.one/)

## ⚠️ 注意事项

1. **私密信息**: 订阅链接和 token 是私人信息，如共享此配置请务必脱敏
2. **兼容性**: 不同版本的 Clash 可能配置格式略有不同
3. **性能**: TUN 模式会增加 CPU 使用率，根据需要启用
4. **更新**: 定期更新 Clash Verge 和规则库以获得最佳性能

---

**最后更新**：2026-10-04
