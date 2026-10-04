# Global instructions

## Language
- Always reply in Simplified Chinese (keep code, commands, paths, identifiers as-is).

## Token economy
- Keep replies concise; no filler or restating.
- Delegate high-token read-only work (web search, multi-page fetch, broad exploration, large files/logs, batch checks) to sub-agents on the default lightweight model.
- Sub-agents return condensed conclusions (facts, paths, URLs), never raw dumps.
- Run independent sub-agents in parallel; don't redo their work.
- Do single directed lookups (one file, one grep) yourself.

## Installing tools (pre-authorized)
- Install dev tools/runtimes as tasks need (Python, Java, Docker, Node, uv…) without asking. Still confirm system-level/risky changes (registry, security settings, uninstalling existing tools).
- Check first (`where`/`which`, `--version`); reuse working versions.
- Use `winget` (preferred) or `scoop`; Python via `uv`, Node via `npm`/`fnm`, Java via winget Temurin. Pin versions; official sources only.
- Project deps go in isolated envs (`.venv`, `node_modules`), not global.
- Read `C:/Users/raynl/.kimi-code/TOOLS.md` before installing; after any install/upgrade/uninstall append: date, tool, version, method, purpose, uninstall command.
- Verify with `--version` and tell the user what was installed.

## Sub-agent rules
Lesson: a docx sub-agent hung ~30 min on Word COM and kept rewriting one script, burning 960k output tokens with nothing delivered.
- Good to delegate: search, research, reading large files, batch checks, running tests — anything whose result compresses well.
- Split work into small steps; give each sub-agent the steps and expected outcome, and have it report results back.
- Every delegation states: step cap (e.g. ≤15 tool calls) and time cap (e.g. ≤5 min); deliverables and acceptance command; core first with passing tests, extras later; no whole-file rewrites (patch locally); same error fails twice → stop and report.
- External programs (Office COM, browser, GUI): separate subprocess, hard timeout ≤45 s, dialogs off, always quit; on timeout kill only processes this automation started. GUI clicking: ask the user to do it, don't use an agent.
- Check background sub-agents ~every 10 min via deliverable file mtimes; no progress for 10 min → inspect hung processes, stop it or finish yourself.
- Don't trust sub-agent reports: rerun tests yourself, verify what it installed/changed, log installs in TOOLS.md.
