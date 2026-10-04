---
name: web-research
description: Token-efficient, authority-first internet search and research. Use when the user asks to search/look up/research online (搜索、查找、调研、联网查), needs current facts, versions, prices, docs, or wants sources compared and verified.
whenToUse: Any task needing web search or fetching web pages; skip for questions answerable from the local codebase.
---

# Web Research

Adapted from Anjos2/recursive-research (MIT) — source tiering and inversion check kept; heavy loop removed for token economy.

## 1. Scope first (no tool calls yet)
- Restate the question as 1–3 concrete sub-questions and the expected answer shape (fact, list, comparison, how-to).
- Pick depth: **quick** (1 search, ≤2 fetches) for single facts; **standard** (≤4 searches, ≤6 fetches); **deep** only when the user asks for research/调研.
- Ask the user only if the question is genuinely ambiguous.

## 2. Delegate heavy work
- For standard/deep depth, run searching and fetching in a sub-agent (`Agent`, type `explore`, default lightweight model). Independent sub-questions → parallel sub-agents.
- Tell the sub-agent: the sub-questions, the source tiers below, the budget, and "return only conclusions + source URLs + dates, no raw page dumps".
- Quick lookups: do them directly.

## 3. Query craft
- Use precise terms, product/version names, and the language of the best sources (English for tech docs; local language for local topics).
- Use operators: `site:` for official domains (e.g. `site:docs.python.org`, `site:github.com`), quotes for exact errors, year for recency.
- Go to the known primary source directly (official docs, repo raw files, RFC, changelog) instead of searching when you know where it lives.
- Don't repeat near-synonym queries; if 2 queries fail, change angle (different source type or language).

## 4. Source tiers
- **Tier 1**: official docs/specs/standards (RFC, W3C, ISO), vendor changelogs and release notes, primary repos/raw files, peer-reviewed papers, government/statistical data.
- **Tier 2**: maintainers' or recognized experts' blogs, reputable media, high-signal issue trackers, Wikipedia (as a pointer to its references).
- **Tier 3** (use with caution, corroborate): forums, Stack Overflow, Reddit, personal blogs that cite Tier 1/2.
- **Reject**: anonymous content, SEO/content farms, marketing without data, uncited AI-generated pages, stale mirrors.
- Prefer the newest source for fast-moving topics; check page date/version.

## 5. Verify
- Key claims need one Tier 1 source, or two independent Tier 2/3 sources.
- Verify links and files actually resolve (fetch them) before recommending.
- Inversion check before answering: what would make this wrong? Is there a contrary source, a newer version, a regional difference? Note real conflicts instead of hiding them.
- Never fill gaps from memory as fact; mark unverified items explicitly.

## 6. Token discipline
- Fetch only pages likely to answer; prefer raw/plain-text endpoints (raw.githubusercontent.com, `?plain=1`, API/JSON) over heavy HTML.
- Extract only relevant lines; use `curl ... | grep`/`head` for large files when shell is available.
- Stop when the sub-questions are answered with sufficient sources; don't chase completeness beyond the depth chosen.

## 7. Answer format
- Answer first, then brief support. Match the user's language.
- Cite sources inline or as a short list: title/domain + URL (+ date when relevant).
- State what was verified, what wasn't, and any caveats in one or two lines.
