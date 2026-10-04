// Clash Verge 订阅扩展脚本：移植 fastest_ig.conf 的分流（保留订阅节点）
function main(config, profileName) {
  const EX = "剩余流量|套餐到期|官网|重置";
  const region = (name, re, interval = 600) => ({ name, type: "url-test", "include-all": true, filter: re, "exclude-filter": EX, url: "http://www.gstatic.com/generate_204", interval, tolerance: 50, lazy: false });
  const regions = [
    region("🇯🇵 日本节点", "日本|JP|(?i)Japan"),
    region("🇸🇬 新加坡节点", "新加坡|狮城|SG|(?i)Singapore", 120),
    region("🇺🇸 美国节点", "美国|US|(?i)States", 120),
    region("🇨🇳 台湾节点", "台湾|TW|(?i)Taiwan"),
  ];
  const regionNames = regions.map(g => g.name);
  const sel = (name, first) => ({ name, type: "select", proxies: [...first, ...regionNames], "include-all": true, "exclude-filter": EX });

  config["proxy-groups"] = [
    { name: "🚀 策略选择", type: "select", proxies: ["🇺🇸 美国节点", "🇸🇬 新加坡节点", "♻️ ALL", ...regionNames.filter(n => !n.includes("美国") && !n.includes("新加坡"))], "include-all": true, "exclude-filter": EX },
    { name: "♻️ ALL", type: "url-test", "include-all": true, "exclude-filter": EX, url: "http://www.gstatic.com/generate_204", interval: 600, tolerance: 50 },
    { name: "🔍 Google", type: "select", "include-all": true, filter: "美国|日本|新加坡|台湾|(?i)US|JP|SG|TW", "exclude-filter": EX },
    sel("🤖️ 人工智能", ["🚀 策略选择"]),
    sel("📲 Telegram", ["🚀 策略选择"]),
    sel("📹 YouTube", ["🚀 策略选择"]),
    sel("🎥 Netflix", ["🚀 策略选择"]),
    { name: "🍎 苹果服务", type: "select", proxies: ["DIRECT", "🚀 策略选择"] },
    { name: "Ⓜ️ 微软服务", type: "select", proxies: ["DIRECT", "🚀 策略选择"] },
    ...regions,
  ];

  config["rule-providers"] = {
    Gemini: { type: "http", behavior: "classical", format: "yaml", interval: 86400, path: "./ruleset/Gemini.yaml",
      url: "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/Gemini/Gemini.yaml" },
  };

  config.rules = [
    "AND,((NETWORK,UDP),(DST-PORT,443)),REJECT",
    ...["101.126.58.201", "110.249.199.75", "111.225.147.191", "111.63.61.101", "220.243.141.0"]
      .map(ip => `AND,((IP-CIDR,${ip}/32,no-resolve),(DST-PORT,6443)),REJECT`),
    "AND,((OR,((DOMAIN-SUFFIX,bytegecko.com),(DOMAIN-SUFFIX,byteeffecttos.com))),(DOMAIN-KEYWORD,ncdn)),REJECT",
    "DOMAIN-SUFFIX,codeyu.shop,DIRECT",
    "GEOSITE,private,DIRECT",
    "GEOSITE,category-ads-all,REJECT",
    "RULE-SET,Gemini,🔍 Google",
    "GEOSITE,category-ai-!cn,🤖️ 人工智能",
    "GEOSITE,telegram,📲 Telegram",
    "GEOSITE,youtube,📹 YouTube",
    "GEOSITE,netflix,🎥 Netflix",
    "GEOSITE,google,🔍 Google",
    "GEOSITE,apple,🍎 苹果服务",
    "GEOSITE,microsoft,Ⓜ️ 微软服务",
    "GEOSITE,geolocation-!cn,🚀 策略选择",
    "GEOSITE,cn,DIRECT",
    "GEOIP,private,DIRECT,no-resolve",
    "GEOIP,telegram,📲 Telegram,no-resolve",
    "GEOIP,CN,DIRECT",
    "MATCH,🚀 策略选择",
  ];

  config.dns = {
    ...(config.dns || {}),
    enable: true,
    "default-nameserver": ["223.5.5.5", "119.29.29.29"],
    nameserver: ["https://dns.alidns.com/dns-query", "https://doh.pub/dns-query"],
    "proxy-server-nameserver": ["https://dns.alidns.com/dns-query", "https://doh.pub/dns-query"],
  };
  return config;
}
