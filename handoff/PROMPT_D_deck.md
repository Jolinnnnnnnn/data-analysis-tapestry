# PROMPT D: build the 5-8 slide deck, and retire the "How it was built" tab

You are working in `/Users/dereksun/code/jolin/data-analysis-tapestry`, the TYLY take-home for a Consumer Intelligence & Analytics role.
Deliverable D1 (the dashboard) is live at https://data-analysis-tapestry.vercel.app/.
Your job is deliverable D2, the deck, plus one site change: the deck becomes the single home for "how it was built", so the dashboard's "How it was built" tab is removed and the few things on it that a business user still needs move to the screens they belong on.
You stop once, at the checkpoint in section 0.5: after reading, summarise the user's process back to them and wait for a go-ahead before building anything.
After that, nobody will answer questions while you work.
When something is ambiguous, pick the most defensible option, record it in `DECISIONS.md`, and keep going.

## 0. Orient first
Read, in this order:
1. `~/.claude/CLAUDE.md` (the user's global rules; they beat any tool default).
2. `CLAUDE.md` (project memory: structure, pipeline, conventions, learnings).
3. `take_home_brief.pdf` (the exercise; section 1 below restates the deck part).
4. `NOTES.md`, then `HISTORY.md` in full (Iterations 1-19 are the real record of the work), then `DECISIONS.md` and `PROMPTS.md`.
5. `FINDINGS.md` (F1-F15 and R1-R3), `outputs/tables/09_sensitivity.md`, `10_sizing.md`, `14_findings_audit.md`, `17_number_trace.md`.
6. `web/README.md`, `web/src/components/HowBuilt.tsx`, `web/src/components/LikeForLike.tsx`, `web/src/lib/vocabulary.json`, `data/dashboard/build_stats.json`.

Rules that matter most here:
- Never use the em dash or en dash characters in anything you write (slides, notes, docs, code comments); use a plain "-".
  Generated data contains en dashes (for example `meta.partial_week_days`); leave data alone, but don't copy them into new text.
- Commit and push only when the user asks, and never add a `Co-Authored-By` or any agent-name trailer.
- Never modify `data/raw/`; every number comes from a saved, numbered script; the web front end does no arithmetic.
- Long Markdown: one full sentence per physical line.
- Next free numbers: D27 (DECISIONS), Iteration 20 (HISTORY), P22 (PROMPTS), script `19_*`.
- Another session may have uncommitted edits in the main checkout (at the time of writing: `web/src/components/Briefing.tsx`, `Explore.tsx`, `Header.tsx`, a shorter summary view).
  Run `git status` there first.
  Work in your own git worktree on a new branch from `origin/main` (for example `deck-and-how-removal`), do the deck first, and do the site change (section 5) last, rebasing on `origin/main` before you start it so you build on whatever has landed.
  Don't revert or rewrite another session's changes; if you must touch the same lines, keep their intent.

## 0.5 Checkpoint: summarise the process and ask to proceed
Before you create a branch, write a file or build anything, read section 3 and check it against `HISTORY.md`, `PROMPTS.md`, `DECISIONS.md` and `git log --oneline --all`.
Then reply to the user with a summary of their process, as you will present it on the "how it was built" slides, and stop.

The summary should:
- Follow the order in section 3: analysis, the discarded first dashboard, design with Claude Design, build and deploy, user QA, the strict review and the two parallel fixes, the production bug.
- Give one or two plain sentences per step: what was done, which tool, and what the user decided or caught (their judgment is the point, not just the tool use).
- Quote the two or three user prompts you plan to put on the slides, word for word.
- List the tools you will name.
- End with a short list of anything you could not confirm from the repo, anything in section 3 that the repo contradicts, and any gap you noticed (a step with no record, a number that disagrees).
- Stay under about 300 words, with no em or en dashes.

Finish with one question: whether the summary is accurate and you should proceed, or what to change.
Do not start sections 4-5 until the user says to proceed.
If they correct something, update your understanding (and section 3 of this file, if they ask) before building.

## 1. What the deck must cover (from the brief)
A short deck, 5 to 8 slides, covering:
- the key findings;
- the top 2 to 3 recommendations, ranked by priority, each with the reason, the expected impact, and any data wanted that is not in the file;
- how it was built: the AI tools and key prompts used, how the AI's output was checked, and how the AI feature keeps its answers accurate.

Also from the brief: "If something in the data surprises you, tell us", "correct, decision-ready insight matters more than the number of charts", about half a day of work and "polish is not what we're looking for".
In the follow-up the candidate presents the deck and then walks through the dashboard, so the deck tells the story and the dashboard is the proof.

## 2. The story (confirm every figure in FINDINGS.md and metrics.json before using it)
Basis: like-for-like period to date, FY26 W23-W30 (W30 is Sun-Wed, data ends 2026-08-19) vs FY25 on the same weeks and weekdays.
Counts are sample-scale, so shares and ratios are the robust read.
- F1: demand +12.8% YoY like-for-like, from more customers rather than bigger baskets.
- F2 (surprise): a naive all-rows comparison shows +7.5%, because LY W30 has three more days.
- F3: W29 fell -18.8% vs W28, but that is a W28 basket spike, not lost traffic.
- F4, F5 (surprise): Gen Z new customers +122% and about 97% of new-customer growth; Gen Z share of new customers rose from 33% (W23) to 47% (W29) and 56% (W30 so far).
- F6, F7: returning customers flat and returning Gen Z down; only 17% of new Gen Z join Insider vs 23% of Millennials, with the gap concentrated in some channels and regions.
- F8: new Gen Z enter through the Tabby franchise, mostly full price, in stores.
- F9, F10: Tabby + Pillow Tabby are 85% of demand growth; Halo apparel and Rogue are the drag.
- F11, F12 (surprise): the winners have under 2 weeks of supply while slow apparel holds 16-21 weeks; Tabby received only 28% of what it sold (95% LY), so replenishment stopped following demand.
- F13, F14 (surprises): the TY W30 stock snapshot is dated after the last sale; every transaction is one line and CUST_ID behaves like a random number, so no basket or cohort analysis is possible.
- R1 protect and chase the Tabby franchise now; R2 move open-to-buy from Halo apparel to Hero and clear the overhang; R3 turn the Gen Z wave into repeat customers (Insider at first purchase plus a Tabby-led second purchase).
  Impacts and missing data per recommendation are in `FINDINGS.md` and `outputs/tables/10_sizing.md`.

Week labels matter: FINDINGS quotes some "latest position" values from the W30 snapshot (for example Tabby 1.9 weeks of supply) while the dashboard defaults to W29 (Tabby 2.1).
Every number on a slide must either match the dashboard view that slide links to, or say which week it is and why it differs.

## 3. How the work was actually done (ground the "how it was built" slides in this, not in generic AI talk)
Use this timeline; the details are in `HISTORY.md`, `PROMPTS.md`, `DECISIONS.md` and the git log.
Quote the user's own prompts where marked; they show judgment, not just tool use.

1. **Analysis (HISTORY 1-13).**
   Claude Code (Claude Opus) worked as an autonomous analyst in this repo from one master instruction built on the brief, in a loop: orient, plan, act with a numbered script, verify with a second method, record, reflect.
   Memory lived on disk (`NOTES.md`, `HISTORY.md`, `DECISIONS.md`, `FINDINGS.md`, later `CLAUDE.md`), so work survived context resets.
   Guardrails: raw file read-only (chmod 444), every number from a saved script, `run_all.sh --clean` rebuilds everything byte-identically, and `14_verify_findings.py` re-derives all 30 headline numbers.
   Moments where the AI added judgment beyond the brief: the CUST_ID random-collision test (P4), the implied-receipts scale check (P8), the adversarial challenge that downgraded a finding (P9), the full-window guard on the anomaly rules (P12).
2. **A first dashboard, thrown away.**
   A Streamlit dashboard was built from a written spec (`handoff/PROMPT_C_dashboard.md`), merged as PR #1, then reverted by the user's choice to design something better rather than copy the earlier design.
   Present this honestly as iteration, in one line.
3. **Design with Claude Design.**
   The user asked for a design prompt and set the bar: "modern and colorful, with cool visuals and animations ... but i dont want it to have meaningless animations that dont add to the dashboard" (user prompt).
   Together they picked motion that encodes information: M1 a season playhead that reveals events through time, M3 a click-to-zoom growth drill-down, M5 LY-to-TY morphs, M6 a naive vs like-for-like switch, and M8 the validator replaying its check.
   They chose precomputed data over live computation.
   Claude Design went through about 9 rounds ("Briefing directions", neon vs pastel) to the final "TYLY Dashboard"; the user picked a single theme.
   Every placeholder number in the design mock was replaced by real data, and several mock values were wrong (DECISIONS D20).
4. **Build and deploy (HISTORY 14-16).**
   Python pipeline scripts 15-18 (facts, AI texts, validator, export), a Vite + React app, Vercel deploy (PR #2).
   Real deploy mistakes worth one line: the Vercel root directory was wrong at first (404, and the raw data was briefly downloadable), fixed by serving only `web/`.
5. **User QA caught things the AI missed.**
   The user noticed the G4 LY/TY toggle had no object persistence; the cause was the Mac's Reduce motion setting, which the app respects, so an opt-in Animations toggle was added and motion was verified in headless Chrome.
   The user also enforced their own writing and attribution rules (no agent co-author on commits, no em dashes), which led to a git history rewrite and the `CLAUDE.md` learnings log.
6. **A strict self-review, then two fixes in parallel (HISTORY 17-18).**
   The user asked: "check this and the initial prompt ... how is the dashboard state compared to this. be strict and give useful feedback" (user prompt), then pushed back: "is your criticism valid still" given the brief does not require a live model (user prompt).
   That narrowed the review to accuracy: Ask gave correct numbers to the wrong question, and the validator only checked that a number existed.
   A handoff prompt (`handoff/PROMPT_E_validator.md`) sent the validator work to a second Claude Code session in its own git worktree, while the first session built live Ask; both were merged (PR #4).
7. **A production bug, reproduced before fixing (HISTORY 19).**
   Live Ask returned a bare 500; it was reproduced with a local `vercel build`, traced to a working-directory-relative file read, fixed with a regression test, and shipped (PR #5).
   The user chose not to spend API credits on a live test and confirmed it on the site.

Tools to name: Claude Code (Claude Opus), Claude Design, the Claude API (`claude-opus-5-5`, funded by Claude Max API credits) for live Ask routing, Python (pandas, matplotlib, z-tests, bootstrap and permutation tests), Vite + React + TypeScript, Vercel, GitHub, headless Chrome for visual and motion checks.

## 4. Slides
5 to 8 slides, one message each, with an action title that states the takeaway as a full sentence.
Suggested shape (merge or split as the story needs, but stay within 8):
1. **Executive summary:** +12.8% like-for-like from more customers; the three-part story (Gen Z engine, leaky bucket, the winner running out of stock); R1-R3 in one line each.
2. **Performance and the surprise in the basis (F1-F3):** weekly TY vs LY, the decomposition, and the naive +7.5% vs like-for-like +12.8%.
3. **Gen Z acquisition and retention, the top-priority goal (F4-F8):** share of new customers by week, the Insider gap, the retention-proxy caveat.
4. **Winning products and stock in the wrong place (F9-F12, F15 watch list):** Tabby's share of growth vs its weeks of supply and receipts, apparel overhang.
5. **Recommendations, ranked (R1-R3):** reason (finding IDs), expected impact with its assumptions, data wanted that is not in the file.
6. **How it was built:** the section 3 workflow as a compact timeline, tools, two or three key prompts (the user's own words), and how output was checked (second-method checks, findings audit 30/30, byte-identical rebuilds, user QA).
7. **How the AI feature keeps answers accurate:** briefing texts cite fact keys as placeholders and six checks run in Python and in the browser (citation, metric, subject, period, direction, comparison), a failing text is held back and the build fails, a 51-case adversarial corpus, and the claim types still unchecked (from `vocabulary.json`); Ask has Claude pick one of 12 query templates and never write a number, code refuses entities it can't honour and checks premises, with a keyword fallback.
   Use concrete before/after examples from DECISIONS D25 ("W29 transactions -1.8%" used to pass; it was the AOV change).
8. *(Optional)* **Appendix:** definitions (moved from the site, see 5b) and a walkthrough map: which dashboard link answers which question.

Every findings slide links to the matching dashboard view with a deep link (all state is in the URL hash, for example `#/explore/g4?wk=29`, `#/briefing?wk=29&demo=metric`).
Add presenter notes per slide: what to say in two or three sentences and which link to click during the walkthrough.

**Look.**
Match the dashboard: Sapphire `#266DD3`, Charcoal `#344055`, chrome `#232B3C`, Thistle `#DFC2F2`, page `#F6F3FA`, goal hues G1 `#266DD3`, G2 `#8A5CC9`, G3 `#344055`, G4 `#B0739F`, Archivo for headings and Space Mono for data.
Red, amber and green are for status only; one highlighted series (TY) with LY as a muted ghost; direct labels, no legends where avoidable.
A short source footnote per slide (script or file, basis, "sample extract").
Prefer screenshots of the live dashboard views (taken at a fixed viewport, checked for mid-animation artifacts) or the existing `outputs/figures/*.png`; redraw a chart only in a saved script, and log it.

**Format.**
Build it as a Slides artifact if this environment offers one (it exports to PowerPoint and PDF), otherwise as `deck/TYLY_deck.pptx` plus a PDF.
Keep the source of the slide text in the repo (`deck/`), so the deck can be rebuilt.

**Numbers in the deck get the same treatment as the AI texts.**
- Write `scripts/19_deck_numbers.py`: it reads `metrics.json`, `anomalies.json`, `build_stats.json` and the analysis tables and writes `deck/deck_facts.json`, one key per number a slide may show, with its upstream source.
- Write slide text as placeholder sources (`{fact key|format}`), render them with 17's `render()`, and run the six-check validator on every text block; any FLAGGED block fails the script.
- Keep wording within what the checks can verify (one number per clause, its metric word and subject next to it); reword honest sentences rather than loosening rules.
- Add the script to `run_all.sh`, so `./run_all.sh --clean` rebuilds the deck facts and re-checks the deck text.
- Render every slide to an image and inspect it for overflow, overlap, clipped labels and stale numbers; fix what you find.

## 5. Retire the "How it was built" tab
Do this after the deck exists, on a rebased branch (see section 0).

**5a. Inventory first.**
List every section of `HowBuilt.tsx` (build stats, pipeline tiles, "What the validator checks" with the unchecked claims, "What surprised us" with the M6 basis switch, the AI system prompts, definitions, the Ask paragraph) and every reference to the tab: `App.tsx` (route), `Header.tsx` (nav item and the hero block for `screen === "how"`), `core.ts` (`Screen` type and the screen parser), any `setUrl({ screen: "how" })` link, and the docs (`CLAUDE.md`, `README.md`, `web/README.md`, `DECISIONS.md`).
Write the inventory into the HISTORY entry with a destination for each item.

**5b. Move what a business user still needs; let the deck carry the rest.**
- Unchecked claim types: DECISIONS D25 promises they are disclosed in the product, so show them where the checks are visible, in the Briefing's "Facts used" panel (a short line or disclosure read from `vocabulary.json`), not only in the deck.
- Definitions (`meta.basis`, `meta.definitions`, `meta.ratio_rule`): keep them reachable in the app (for example a compact "Definitions" disclosure in the footer or next to the like-for-like strip), and also put them in the deck appendix.
- The M6 naive vs like-for-like switch already lives in the like-for-like strip's pop-over; confirm it still works and needs nothing from HowBuilt.
- Build stats, pipeline tiles, validator checks, surprises, system prompts and the Ask paragraph move to slides 6-7 and the appendix.
- The Briefing's own "Try a wrong text" demos stay; they are the in-product proof of the validator.

**5c. Remove it.**
- Delete `web/src/components/HowBuilt.tsx`, its route in `App.tsx`, its nav item and hero block in `Header.tsx`, and `"how"` from `Screen` and the screen parser in `core.ts`.
- An old link to `#/how` must land on the Briefing without an error (the parser already falls back to `briefing` for unknown screens; confirm it).
- Remove now-dead code and exports (anything only HowBuilt used, for example `CHECK_INFO` if nothing else reads it), and run TypeScript with no unused-import leftovers.
- `app.json` fields that only HowBuilt read (for example `build.system_prompts`) may stop being exported by `18_export_web.py` only if nothing else reads them; they stay in `data/dashboard/build_stats.json` for the deck.
  If you change the export, rerun the pipeline and confirm parity and the Ask tests still pass.
- Update the docs that mention the How page.
  Record the move in a new DECISIONS entry (D27) instead of editing D25's history.

**5d. Verify like a user.**
- `npm --prefix web run verify` (parity, corpus, Ask tests) and the production build pass; `./run_all.sh --clean` twice is byte-identical, raw md5 unchanged.
- In the browser preview (`.claude/launch.json` config `web`, port 5199; use another port with `--strictPort` if it's taken, and don't commit that launch entry): the nav shows Briefing, Explore and Ask only; `#/how` lands on the Briefing; the unchecked-claims line and the definitions are reachable; the like-for-like pop-over works; no console errors; no horizontal scroll at 375 px.
- Be picky about the UI: fix anything that looks off where the tab used to be (nav spacing, the header hero, the footer).

## 6. Done when
- The deck has 5 to 8 slides covering findings, ranked recommendations with reason, impact and missing data, and how it was built (workflow, tools, key prompts, output checks, accuracy design), with presenter notes and deep links.
- `scripts/19_deck_numbers.py` passes: every number in the deck renders from `deck/deck_facts.json` and passes the six checks, and `./run_all.sh --clean` rebuilds it.
- The "How it was built" tab is gone, nothing a business user needs was lost, and the site checks in 5d pass.
- Docs updated: DECISIONS D27, HISTORY Iteration 20 (including the 5a inventory), PROMPTS P22, NOTES current state, `CLAUDE.md` (repo structure, How components work, next numbers, any new Learnings), `README.md`, `web/README.md`; `handoff/PROMPT_D_deck.md` marked done in `CLAUDE.md`.

## 7. Report back
Give the deck link or path, a one-line summary per slide, any number that differs between deck and dashboard and why, what moved where from the How tab, and anything you dropped.
Do not commit or push until the user asks.
