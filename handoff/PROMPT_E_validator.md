# PROMPT E: make the AI-text validator check meaning, not just existence

You are working in `/Users/dereksun/code/jolin/data-analysis-tapestry`, the TYLY take-home (deliverable D1: a dashboard with a weekly AI briefing, judged on design and on how its answers are kept accurate).
Live site: https://data-analysis-tapestry.vercel.app/ (pushing to `main` deploys production).

## 0. Orient first
Read, in this order, before touching anything:
1. `~/.claude/CLAUDE.md` (the user's global rules; they beat any tool default).
2. `CLAUDE.md` (project memory: pipeline, conventions, learnings).
3. `NOTES.md`, the tail of `HISTORY.md`, and `DECISIONS.md` D14-D24.
4. `scripts/15_build_facts.py`, `scripts/16_generate_summaries.py`, `scripts/17_validate_summaries.py`, `scripts/18_export_web.py`.
5. `web/src/lib/validator.js`, `web/scripts/parity.mjs`, and how `web/src/components/Briefing.tsx` and `Header.tsx` use `annotate`, `validateText`, `injectError` and `nearestFact`.
6. `ai/session_texts.json` (keys `_about`, `summaries`, `cards`, `headlines`).

Rules that matter most here:
- Never use the em dash or en dash characters in anything you write; use a plain "-".
- Commit and push only when the user asks, and never add a `Co-Authored-By` or agent-name trailer.
- Never modify `data/raw/`.
- The front end does no arithmetic, and every number comes from a numbered script.
- Long Markdown files: one full sentence per physical line.
- Python is the 3.9 venv: `.venv/bin/python -W ignore scripts/NN_x.py`; install with `.venv/bin/python -m pip`.
- Another session may be working on the Ask feature (`web/src/components/Ask.tsx`, a new `web/api/` function) at the same time.
  Work in your own git worktree on a new branch (for example `validator-semantic`), do not edit `Ask.tsx` or `web/api/`, and keep `validateText(text, facts)` exported with a compatible return shape so other code keeps working.

## 1. The problem
The validator (Python `17` and its JS port `validator.js`, kept identical by `parity.mjs`) asks only one question per printed number: does any number in this text's facts match it within half a unit of its printed precision?
It never asks whether the sentence is about that fact.
That catches invented numbers well (only 17 of 399 random 1-dp percentages pass against W29 facts), but it passes misstatements.

Reproduce this first, end to end, with the real W29 facts (`app.weeks_ai["29"].facts` in `web/src/data/app.json`).
All four sentences below currently PASS:

| Sentence | Should be | Why |
|---|---|---|
| "W29 demand $71.3K, +12.7% YoY." | PASS | Correct (`l1w_sales_ty`, `l1w_sales_yoy_pct`). |
| "W29 transactions −1.8% YoY." | FLAGGED | −1.8% is `l1w_aov_yoy_pct`; transactions were +14.7% (`l1w_txns_yoy_pct`). |
| "W29 demand fell 12.7% YoY." | FLAGGED | Demand rose; unsigned numbers are compared to absolute values and "fell" is never read. |
| "Gen Z demand was $71.3K in W29." | FLAGGED | $71.3K is total demand, not Gen Z. |

Also note the real W29 summary contains "The -18.8% WoW drop is basket, not ..." and "These are the period's growth leaders": a correct direction word next to a negative number must PASS, and claim words like "leaders" are currently unchecked.

## 2. Target design
Move from "some fact matches this number" to "this number is the fact it cites, and the words around it agree with that fact".

**2a. Texts cite fact keys.**
- AI texts (pregenerated, template and live) are written with placeholders instead of literal figures, for example `W29 demand {l1w_sales_ty|money_k}, {l1w_sales_yoy_pct|pct+} YoY.`
- The key is the same path syntax `fact_numbers` already produces (`a.b[0].c`); the format specifier is explicit and drawn from a small fixed set (for example `money`, `money_k`, `pct`, `pct+`, `pts+`, `int`, `wos`, `ratio2`) that reproduces the display formats in `CLAUDE.md` (12.7%, YoY of 100% or more as a whole percent, $71.3K, $564,028, 2.1 weeks, +5.0 pts).
- Python (16) renders each text once and stores the source text, the rendered text and a citation list (span, key, value, format) per text; 18 exports all three to `app.json`.
  The UI keeps showing the rendered text and does no formatting of AI numbers itself.
- A printed number with no citation (outside the existing masks) is FLAGGED.
  This is the strict rule that makes misattribution visible in a key name.

**2b. Checks the validator runs on every text (Python and JS, identical).**
1. Citation check: every cited key exists in that text's facts, and the rendered number re-parses to within half a unit of the cited value (this keeps the injected-error self-test meaningful: editing a rendered number must flag).
2. Metric check: map metric words to key classes with one shared vocabulary (demand/sales/revenue → `sales`; transactions/orders → `txns`; AOV/basket → `aov`; units; weeks of supply → `wos`; receipts → `receipts_to_sales`; share; customers/new customers; and so on).
   If the clause containing a citation names a metric, the key must be in that class.
3. Subject check: if the clause names an entity (Gen Z, a generation, a product family such as Tabby or Pillow Tabby, a segment), the cited key must belong to that entity, either by its name or, for list records, by the record's name field; a total-business key under a named entity is FLAGGED.
4. Direction check: up-words (up, rose, grew, gained, ahead, increase) and down-words (down, fell, dropped, declined, drag, decrease, drop) in the clause must agree with the sign of the cited value.
5. Comparison check where the facts allow it: "less than half"/"more than half"/"majority" against 0.5, "doubled" against 1.0 or +100%, and "leader"/"top"/"largest" against the rank or order the facts provide.
   Any claim type you cannot check from the facts must be listed as unchecked in the docs and on the How page, never silently passed.

Keep clause detection simple and deterministic (split on sentence and clause punctuation), and prefer flagging over guessing; then adjust wording in the texts, not the validator, when a check is too strict for an honest sentence.
The existing number check stays as a second layer.

**2c. One shared test corpus.**
- Put adversarial and regression cases in one JSON file both validators read, for example `web/scripts/validator_cases.json` (it must live under `web/` because Vercel's Root Directory is `web`).
- Each case: text, facts (or a reference to a week's facts), expected status, and expected reason (citation, metric, subject, direction, comparison).
- Include at least the four sentences above (rewritten in placeholder form where needed), a correct negative-with-down-word case, an uncited literal number, a key that does not exist, and an edited rendered number.
- `parity.mjs` runs the corpus and compares Python and JS verdicts and reasons; `17` runs it too; both exit 1 on any mismatch, so the Vercel build (`npm run verify && npm run build`) fails on a regression.

**2d. Writer and texts.**
- Update the three system prompts in 16 (`SYSTEM_SUMMARY`, `SYSTEM_HEADLINE`, `SYSTEM_CARD`) to require placeholders, list the allowed format specifiers, and forbid literal figures.
- Update the template fallback to emit placeholders.
- Rewrite every text in `ai/session_texts.json` into placeholder form without changing its meaning, then follow the documented order: run 17 (must PASS), `16 --stamp`, then 16, 17 and 18.
  Never stamp blindly.

**2e. UI.**
- `annotate` should use the stored citations, so each number's hover tooltip shows the exact cited key and source path instead of a best guess.
- Remove `nearestFact` guessing for cited numbers; for a failing text, the held-back panel should name the failed check and the cited key.
- Extend the demo links so a reviewer can see each check fire, for example `&demo=blocked` (edited number, existing), `&demo=metric` and `&demo=direction`, each driven by data, with no figures typed into UI copy.
- Update the How page copy (from data) to describe the new checks and the unchecked claim types.

## 3. Done when
- The four reproduction sentences give PASS, FLAGGED (metric), FLAGGED (direction), FLAGGED (subject), in both validators, from the shared corpus, and the build fails if any case regresses.
- All texts for W23-W30 (56 today: 8 headlines, 8 summaries, 40 cards) are in placeholder form and PASS every check, and their meaning is unchanged.
  Hand-check a number trace (printed number → cited key → upstream `_sources` path) for W28, W29 and W30.
- `npm --prefix web run verify` prints parity with 0 problems and the corpus result.
- `./run_all.sh --clean` run twice gives byte-identical outputs, and the md5 of `data/raw/TYLY_data_sample.xlsx` is unchanged.
- The app works in the browser preview (`.claude/launch.json` config `web`, port 5199) on `#/briefing?wk=23`, `wk=29`, `wk=30` and each demo link, with no console errors; check hover tooltips and the held-back panel pixel by pixel.
- Docs updated: `DECISIONS.md` D25, `HISTORY.md` Iteration 17, `PROMPTS.md` P20, `NOTES.md` current state, `web/README.md`, and `CLAUDE.md` ("How components work" item 5 no longer says the validator is an existence check; add any mistakes to Learnings).

## 4. Report back
Summarise what changed, the corpus results, any honest sentence you had to reword to satisfy a check (and why), and the claim types that remain unchecked.
Do not commit or push until the user asks.
