# DECISIONS: dashboard session (continues analysis/DECISIONS.md D1–D13)
Each entry: question · options · choice · rationale · consequence.

---
## D14 Repository layout
- **Question:** the brief assumes `analysis/`, `dashboard/` and `design/` folders and a root `run_all.sh`, but the repo was flat (analysis files at the root).
- **Options:** (a) keep it flat and map every path in the brief; (b) restructure to the layout the brief describes.
- **Choice:** (b). `git mv` moved every analysis file into `analysis/` as tracked renames, with history preserved. The scripts were not edited: they resolve `ROOT = Path(__file__).parents[1]`, so `analysis/` is now their root. `analysis/run_all.sh` uses the repo-root `.venv`. The new root `run_all.sh` creates or installs the venv, runs `analysis/run_all.sh`, then `dashboard/run_all.sh`.
- **Rationale:** every path in the brief (and in future prompts) then resolves literally. Git keeps it reversible.
- **Consequence:** the old `handoff/` prompts that referenced flat paths are historical. pip runs as `python -m pip`, because the venv's `pip` shebang pointed at an old checkout path (it broke during setup).

## D15 Missing design spec
- **Question:** `design/DESIGN_SIGNAL.md` (the REQUIRED design) did not exist.
- **Choice:** reconstruct it from the live reference (https://signal-agent-nu.vercel.app/). The light/dark token sets were read programmatically from its CSS custom properties, and the type scale and component metrics from computed styles (pill, buttons, chip, segmented control, card rule, rail, KPI tile, Ask pill). The result is written to `design/DESIGN_SIGNAL.md` with the section numbering the brief cites (§2 tokens, §5 components, §7 voice, §8 content mapping).
- **Rationale:** the reference is the stated source of truth for the design, and measured values beat eyeballed ones.

## D16 New precomputed fields (no app-side math)
- **Question:** the briefing lead and the How-it-was-built page need record counts, week dates and the alternative-basis YoY figures, none of which were in metrics.json.
- **Choice:** add them to `analysis/scripts/11_metrics.py` → `meta.counts`, `meta.week_dates_ty`, `meta.basis_alternatives` (copied from 05_g1_kpi_windows.csv) and `meta.data_quality` (the F13/F14 diagnostics, same closed form as script 04). Documented in `metrics_schema.md` via `13_docs.py` (new "meta fields" table). Per-week alert counts, rule hit counts and the number of "needs you" cards are precomputed in `dashboard/scripts/15_build_facts.py`, so the app never counts or sums.
- **Consequence:** all other analysis outputs were byte-identical after the change (only metrics.json and the schema moved). Logged in analysis/HISTORY.md Iteration 14.

## D17 Which cards, which pill, which numbers (rules, not the LLM)
- **Choice:** five card types per week (stock, retention, pattern, win, overstock). The pill comes from the anomalies that week: a critical hit gives *Needs you today*, a warning gives *Needs you*, and no hit gives *Watch*. The pattern card is *Pattern* (it escalates to *Needs you* if a Gen Z share/new rule fires). The win card is always *Win*. Overstock is always *Watch*: R2 is a planning action, not this week's decision. Cards are sorted by that pill rank, and the h1 counts the "Needs you" cards.
- **Time travel:** each week's card uses only values as of that week (inventory_by_week, trailing, products_by_week, genz_weekly). The latest-position facts (receipts W24–29, R1/R2/R3 sizing, the TY Insider segment gaps) are attached only for W29 and W30, because they are not valid "as of" earlier weeks.
- **Rationale:** the LLM must not decide what is anomalous or how urgent it is. It only words what the rules selected.

## D18 Validator semantics
- **Number grammar:** `$`, `%`, `K`/`M`, `pts`/`pp`, decimals, integers with thousands separators, signed values. Week labels (W29, W26–W29), FY26, L1W/L4W, ISO dates and hyphenated window words ("4-week") are masked, not checked.
- **Match rule:** a number passes if *some* numeric leaf of the facts JSON equals it within half a unit of the printed precision (12.7% → ±0.0005; $71.3K → ±50). An explicit sign must match the fact's sign. An unsigned number is compared with |fact|, so "down 18.8%" can be written.
- **Excluded leaves:** week-index fields (`weeks`, `l4w_weeks`, `wk`), because a count must never validate against a week number. **Included:** each anomaly's documented `rule_threshold`, because rule messages quote it ("(< 20%)").
- **Known limitation:** this is an existence check, not a semantic one. A small integer, or a value that several facts round to, can match a different fact than the sentence means. Mitigations: per-card facts are narrow (each card is validated only against its own ~10 values); the trace (`dashboard/tests/trace_numbers.py`) lists every candidate fact for each number; and the W28/W29/W30 texts were reviewed by hand (dashboard/HISTORY.md Iteration 6). Derived numbers ("2.9 times", differences, sums) can't pass, because they aren't in any facts file.

## D19 metrics.json precision: 4 → 6 decimals
- **Question:** fractions were stored at 4 dp (0.1265), so a 1-dp percentage sits exactly on a rounding tie. The UI showed the naive YoY as +7.4% (true 0.074522 → +7.5% in FINDINGS) and L1W W29 as +12.6% (true 0.126536 → +12.7%).
- **Choice:** `r()` in 11_metrics.py rounds to 6 dp. This only changes serialization precision, not the analysis.
- **Consequence:** findings audit still 30/30. Anomalies unchanged (71, 8 critical). The tighter facts exposed **7 rounding errors** in the session-written texts (they had been rounded on the 4-dp ties); all were corrected and re-validated (PROMPTS P20).

## D20 Writer priority and staleness
- **Choice:** live Claude (if `ANTHROPIC_API_KEY`) → pregenerated session text → deterministic template. A pregenerated text carries the md5 of the facts it was written from; if the facts change it is *stale* and the template is used, with a warning. Live text gets one retry with the unmatched numbers fed back, then falls back to the template, with the rejected attempt logged in `live_attempts`. A pregenerated text that fails validation is not silently replaced: the build fails, so a human fixes it.
- **Rationale:** a reviewer can always regenerate, and nothing unverified ships.

## D21 Defaults
- Week defaults to `meta.last_full_week` (W29). Window defaults to **L4W**: the 4-week read is less noisy than a single sample-scale week (D12), and L1W/PTD are one click away. TY-vs-LY comparison is shown by default.

## D22 Explore = Classic dashboard; tabs as a radio
- The Briefing's "Classic dashboard" toggle and the Explore nav item open the same view (as in the reference). The G1–G4 tabs are a styled `st.radio`, not `st.tabs`, because "Open in Explore" must select a tab programmatically, which `st.tabs` cannot do.

## D23 Tables as HTML, not st.dataframe
- `st.dataframe` is a canvas grid that ignores page CSS, so it can't follow the token set or the light/dark switch. Family, scorecard, style and risk tables are escaped HTML tables. Sorting uses a select (sorting is selection, not math).

## D24 Theme switching
- The tokens are swapped in one CSS block, and Plotly reads the same tokens. Streamlit's own widget theme (select menus, toggle, popovers) is switched with `streamlit.config.set_option("theme.*")` on each run. This is a private API and process-wide, which is fine for a single-user local dashboard; the CSS overrides keep it legible if that call ever stops working.

## D25 Ask: template Q&A
- Eight fixed templates over metrics.json/anomalies.json. Offline, a deterministic keyword/regex parser picks the template and parameters. With `ANTHROPIC_API_KEY`, Claude picks them instead (JSON only; it never sees or writes data values), and invalid output falls back to the parser. Answers are rendered by code, and every answer lists its steps (pick → read → render). Unmatched questions get the template list, never a guess. "Why is retention flagged" means the retention card's rule set (it includes the new-Gen-Z Insider rule, whose entity is `genz`).

## D26 What "no ad-hoc math" allows in the app
- **Allowed:** selecting, filtering, sorting and threshold comparisons on precomputed fields; display formatting (0.128 → +12.8%, 71,311 → $71.3K, 0.0755 contribution fraction → +7.5 pts); drawing geometry (bar widths, bubble sizes, label positions); and the length of a result list in an Ask answer ("2 families have WOS below 3").
- **Not allowed (none present):** sums, differences, ratios, YoY, averages. The KPI tile spot-check (dashboard/tests/tile_spotcheck.py) is the only place a ratio is computed, and that is test-side, to cross-check UPT.

## D27 Partial week and truncated windows in the UI
- W30 is labelled "W30 · partial" everywhere and the briefing says "so far". The weekly line dots its W30 segment, and the LY full week is a hollow reference point. Before W26 the WOS readings come from truncated windows: cards say so, the WOS chart note says "window truncated: rules off", and the Ask answer adds the caveat.
