# AI Assistance Log — wk09

---

## [Agent-Tom] 2026-07-15 — Spend tracking design and implementation

**Task:** Design and implement a token spend tracking solution for a 4-person team with separate machines and individual API keys, covering both `analyse.py` API calls and Claude Code assistant usage.

**What AI Generated:**
- Option A (per-agent CSV files + aggregation script) selected after presenting three approaches
- `spend/` directory with `pricing.py`, `spend_logger.py`, `show_spend.py`, `log_claude_code_session.py`, `install_hook.sh`, `remove_hook.sh`, `plot_spend.py`, `dashboard.py`
- Stop hook auto-detecting purpose category from `last_assistant_message` keywords
- Streamlit interactive dashboard with cumulative timeline, groupby toggle, daily burn rate, and token efficiency plots

**What You Changed + Why:**
1. **Purpose taxonomy added to CLAUDE.md** — initial design used free-text purpose descriptions ("Claude Code — wk09 (session 2)"). You directed that purposes should be fixed categories to enable retrospective analysis of where effort went. Added 11-category table and updated the hook's auto-detection to match.
2. **CSV location moved to `spend/`** — scripts originally wrote CSVs to `solution/`. You pointed out all spend files should live together in `spend/`. Moved CSV and updated all path references from `parent.parent` to `parent`.

---

## [Agent-Tom] 2026-07-15 — Three bugs introduced by AI and corrected by human

**Task:** Ongoing — bugs introduced during the spend tracking implementation that required human correction.

**What AI Generated (incorrectly):**

1. **NameError: `cwd` not defined** in `log_claude_code_session.py`
   - When rewriting `main()` to use `last_assistant_message` for purpose inference, the `cwd = data.get("cwd", "")` line was dropped. The CWD guard added later still referenced `cwd`, causing a `NameError` at hook runtime.
   - You: reported the error. Fix: added the missing `cwd` assignment.

2. **Wrong settings filename: `settings.json` instead of `settings.local.json`**
   - `install_hook.sh` wrote to `wk09/.claude/settings.json`. Claude Code's convention is that `settings.local.json` is the per-machine project override (untracked), while `settings.json` is the shared project config (committable).
   - You: opened `settings.local.json` in the IDE and flagged the mismatch. Fix: updated both `install_hook.sh` and `remove_hook.sh` to target `settings.local.json`.

3. **Dashboard `ROOT` path pointed at `solution/` not `spend/`**
   - All scripts used `Path(__file__).parent.parent` (= `solution/`), but after CSVs were moved into `spend/` the glob found nothing. Also lacked `.resolve()`, making the path sensitive to the directory from which the script was launched.
   - You: reported "No spend logs found" from the running dashboard. Fix: changed all five scripts to `Path(__file__).resolve().parent`.
