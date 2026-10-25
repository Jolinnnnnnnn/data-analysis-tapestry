# Dashboard walkthrough: 3 minutes, interview style

A spoken script for the follow-up interview, after the deck.
Site: https://data-analysis-tapestry.vercel.app/
Each block has a `Do:` line (what to click) and then the words to say.
The words lead with the business answer, and the screen is the proof.
About 430 spoken words, so it fits in 3 minutes at a natural pace.

## 1. The script

### 0:00-0:15 · Briefing (opens on W29)
`Do:` Open https://data-analysis-tapestry.vercel.app/ and leave it on the top of the Briefing.

> This is the page a merchant or a CRM lead opens on Monday morning.
> It opens on the last full week, W29, and every comparison is like-for-like: same weeks, same weekdays as last year.
> W29 demand was $71.3K, up 12.7% on last year.

### 0:15-0:55 · Briefing: the AI summary, the decision, the check
`Do:` Scroll to the Summary and the "This week · needs you" list, and point at card 01 (CRITICAL, G4 Inventory).

> The AI feature is this briefing.
> Rules decide what's unusual, and Claude writes it up from that week's facts only.
> This week the decision is stock.
> Tabby is down to 2.1 weeks of supply, against 7.0 last year, because replenishment covered only 28% of what it sold.
> So the top action is: re-open replenishment on the Tabby franchise.

`Do:` Under "Try a wrong text", click **Edited number**; the check replays for about 2 seconds and stops on the edited number.

> Accuracy is the part I cared most about.
> Every number cites the fact it came from, and the page re-checks it before showing it.
> Here I've changed one number, so the whole summary is held back and you see the raw facts instead.
> A wrong number never reaches the reader.

`Do:` Click **Exit demo** in the red banner.

### 0:55-1:20 · Explore G1 and the one surprise
`Do:` Click **Explore** (opens G1 Performance) and press **▶ Play**; it replays W23 to W30 in about 6 seconds and leaves the whole dashboard on W30, so click **W29** in the week strip at the top when it stops.
Then click **Naive vs like-for-like →** in the lilac strip, click **Naive**, then **Like-for-like**.

> Explore has one tab per business goal.
> TY beat LY in every single week.
> And here's the surprise in the data.
> Compare all rows naively and growth looks like +7.5%.
> But this year's W30 has only four days, and last year's has seven.
> Like-for-like, growth is +12.8%, which is why that's the default everywhere.

### 1:20-1:40 · G3: where the growth came from
`Do:` Press Esc, click **G3 Products**, click the dark **Demand** bar once, wait for it to open, then click **More customers** once.

> Where did that growth come from?
> 65% of it is more customers, not bigger baskets.
> And one franchise, Tabby plus Pillow Tabby, carries 85% of it.

### 1:40-1:55 · G2: Gen Z
`Do:` Click **G2 Gen Z**; point at the weekly share chart, then the Gen Z row in the table at the bottom.

> On the top priority, Gen Z: new Gen Z customers are up 122% for the period.
> Their share of new customers climbed from 33% in W23 to 47% in W29.

### 1:55-2:05 · G4: stock in the wrong place
`Do:` Click **G4 Inventory**; point at the "Stock vs demand correlation" tile and the scatter.

> And stock.
> Last year, stock tracked demand, with a correlation of 0.96.
> This year it's 0.33, and Knit Dress is sitting on 20.7 weeks of supply.

### 2:05-2:40 · Ask
`Do:` Click **Ask**, type `Why did Gen Z new customers drop this week?` and press Enter (live Claude takes about 10 seconds; talk through the wait).

> Ask lets anyone type a question in plain English.
> Claude only chooses which of 12 query templates fits.
> Code checks that choice and writes every number, so the model never writes a figure.
> I've asked a question with a wrong assumption baked in.

`Do:` Point at the "Premise checked against the data" box when it appears.

> It corrects me before it answers: new Gen Z customers were up 156% on last year in W29.
> And if I ask for something the data can't filter, like Tabby in Japan, it says no rather than quietly answering a different question.

### 2:40-3:00 · Close
`Do:` Click **Briefing** to end on the action list.

> So the read for this week: growth is real and customer-led, Gen Z is the engine, and the Tabby franchise is about to run out.
> My first recommendation is to re-open Tabby replenishment now.
> One honest limit: customer IDs don't link across years, so retention here is a proxy.
> Happy to go deeper anywhere.

## 2. Pre-flight checklist
- **Tabs.**
  Tab 1: https://data-analysis-tapestry.vercel.app/ (Briefing, W29, L4W, Show LY on).
  Tab 2 (backup): https://data-analysis-tapestry.vercel.app/#/briefing?wk=29&demo=blocked, in case the "Edited number" link is hard to find live.
  Reload both tabs just before you start, so Ask has no old answers stacked up and every view is back to its default.
- **Check the fixes are live.**
  The script relies on two fixes from the `fix-demo-exit-and-ask-premise` branch: **Exit demo** returning to the normal summary, and Ask correcting a wrong premise on every template.
  Before the call, run the demo and exit it once, and ask "Why are sales down vs last year?"; the answer should open with "Premise checked against the data".
  If either fails, the fix is not deployed yet: leave the demo by clicking **Explore** instead of **Exit demo**, and stick to the Gen Z question in Ask.
- **Stay on W29.**
  ▶ Play and dragging the G1 playhead change the selected week for the whole dashboard.
  After Play, click **W29** in the week strip, or later screens (G4's weeks of supply, Ask's "this week") show W30 numbers instead of the ones in this script.
- **Warm up Ask.**
  Ask one throwaway question about five minutes before the call, so the Vercel function is not cold.
  The answer should show "READ BY CLAUDE · claude-opus-5-5".
  If it shows "READ BY KEYWORD PARSER", the live model is unavailable; the same checks still run and both demo questions still work, so say "Claude is unavailable, so the fallback parser picked the template" and carry on.
- **Zoom.**
  On a 1440 px wide laptop screen, browser zoom 110% keeps the Space Mono figures readable on a shared screen.
  Go no higher than 125%: the G3 drill-down's small tiles start to clip their labels.
- **Motion.**
  If the Mac has Reduce motion on, the header shows "Animations off (system setting) · Turn on"; click **Turn on** before you start so the LY-to-TY morphs and the G3 zoom play.
  ▶ Play on G1 animates either way.
- **Click once.**
  On the G3 drill-down, click once and wait for the zoom; a quick double click drills two levels at once.

## 3. Likely panel questions

**"Why like-for-like and not just this year vs last year?"**
<!-- F2; DECISIONS D3; G1 "Naive vs like-for-like" modal -->
> The extract ends on a Wednesday, so this year's last week has four days and last year's has seven.
> A naive comparison gives last year three free days and understates growth by about 5 points, +7.5% instead of +12.8%.
> Any weekly report that compares a partial week to a full one will mis-state performance, so like-for-like is the default and partial weeks are labeled "so far".

**"How do you know a number the AI wrote is right?"**
<!-- DECISIONS D25, D18; web/src/lib/validator.js; scripts/17_validate_summaries.py; How it was built tab -->
> The AI never types a figure.
> It writes a placeholder that names a fact and a format, the build fills in the number, and a validator checks that each printed number is the fact it cites.
> It also checks the words around it: the right metric, subject, period, direction and comparison.
> The check runs in Python at build time and again in the browser, and if they ever disagree the deploy fails.

**"What happens when the AI gets it wrong?"**
<!-- DECISIONS D25, D19; the four demos &demo=blocked|metric|direction|subject -->
> At build time, a text that fails any check fails the build, so it can't ship.
> In the browser, a text that fails is hidden and replaced by its facts table, with the failed check named, which is the demo I showed.
> If the facts change and a text hasn't been re-checked against them, a plain template is shown instead of the stale text.

**"In Ask, what does Claude actually see?"**
<!-- DECISIONS D26; web/api/ask.ts; web/src/lib/ask/catalog.ts and engine.ts -->
> Only the question and the menu: the 12 templates and the allowed families, weeks and windows.
> It never sees a data value and never writes one.
> It returns a structured route, code checks it, and code writes the answer from the metrics file, showing the template, the data it read and the steps.

**"Some of these counts are small. Can you trust them?"**
<!-- DECISIONS D11, D12; FINDINGS F4, F5 -->
> The file is a sample extract, so counts are sample-scale and I read shares and ratios instead.
> The Gen Z result is a share result: Gen Z went from about a quarter of new customers to about 40%, and it holds in every region and channel and under every test I ran.
> Where a number is noisy, like weekly basket size, I say so rather than build a story on it.

**"Why does one screen say +12.1% and another +12.8%? Or +106% and +122% for Gen Z?"**
<!-- F2 full weeks only +12.1%; G3 tiles label PTD W23-W29 vs W23-W30; Briefing W29 win card is W23-W29, G2 table is W23-W30 -->
> They're different periods, and each one is labeled.
> +12.1% is full weeks only, W23 to W29; +12.8% adds the partial W30 compared on the same four days.
> Same for Gen Z: the W29 Briefing counts up to W29, and the G2 table runs to W30.

**"What would you build next with more data?"**
<!-- FINDINGS F14, F12; R1-R3 "Data not in file" -->
> First, a customer ID that links purchases across years, so retention becomes a real repeat rate instead of a proxy.
> Second, purchase orders and lead times, to tell whether Tabby's low replenishment is a supply problem or an allocation rule.
> Third, margin and markdown data, to size the apparel rebalance properly.

**"What happens when next week's data lands?"**
<!-- CLAUDE.md "How components work"; run_all.sh; DECISIONS D17, D19, D22 -->
> One command rebuilds everything from the raw file in about 30 seconds: metrics, rules, facts, AI text, validation and the site.
> Rules, not the AI, decide what's flagged, so the alerts update on their own.
> Each AI text is stamped with a fingerprint of the facts it was written from, so a stale text drops back to the template until it's rewritten and re-checked.

## 4. The 60-second cut
For when the panel is short on time: three beats, about 100 words plus three clicks.

`Do:` Briefing, card 01.
> This is the Monday briefing.
> Rules flag what's unusual, Claude writes it up, and every number is checked against the data before it's shown.
> The decision this week is stock: Tabby has 2.1 weeks of supply against 7.0 last year, so re-open replenishment now.

`Do:` Click **Naive vs like-for-like →**, toggle **Naive** and back.
> The story behind it: demand is up 12.8% like-for-like, not the 7.5% a naive comparison shows, and it's driven by more customers.
> New Gen Z customers are up 122%, and the Tabby franchise carries 85% of growth.

`Do:` Click **Ask**, type `Why did Gen Z new customers drop this week?`.
> And Ask: Claude only picks a query template and code writes every number, so a wrong assumption gets corrected, not answered.

## 5. Notes

**Word count.**
The spoken lines in section 1 come to 426 words (counted from the quoted lines only), about 2 minutes 50 seconds at 150 words a minute, which leaves a few seconds of slack for clicks.
The 60-second cut is 102 words, about 40 seconds of speech, which leaves room for three clicks and the Ask wait.

**Figures used and where they come from** (all checked on the live site on 2026-10-25, and in `web/src/data/app.json`).

| Said | Screen | Source |
|---|---|---|
| W29 demand $71.3K, +12.7% | Briefing hero | `trailing.29.L1W.sales` (71,311.35; 0.126536) |
| Tabby 2.1 weeks of supply vs 7.0 LY | Briefing card 01, G4 table | `inventory_by_week` W29; alert AN049 |
| Replenishment covered 28% of what Tabby sold | Briefing card 01, G4 tile | F12; alert AN060; `recommendations_sizing.R1` |
| Edited number demo | Briefing `&demo=blocked` | built by `16_generate_summaries.py`, asserted by 17 |
| TY beat LY in every week | G1 weekly table | `weekly`; F1 |
| +7.5% naive, +12.8% like-for-like, 4 vs 7 days | Like-for-like modal | `meta.basis_alternatives`; F2 |
| 65% of growth from more customers | G3 drill-down, Drivers | `growth_drill.drivers[0]` (0.649684); F1 |
| Tabby + Pillow Tabby 85% of growth | G3 tile and Families level | `growth_drill.hero_share_of_growth` (0.852543); F9 |
| Gen Z new +122% | G2 generation table | `generation_ptd` Gen Z (240 vs 108); F4 |
| Gen Z share of new 33% (W23) to 47% (W29) | G2 weekly chart | `genz_weekly` (0.333333, 0.471264); F5 |
| Stock vs demand correlation 0.96 to 0.33 | G4 tile | `stock_demand_shares.corr_ly`, `corr_ty`; F11 |
| Knit Dress 20.7 weeks of supply | G4 table | `inventory_by_week` W29; alert AN056 |
| 12 query templates | Ask side panel | `web/src/lib/ask/catalog.ts` |
| Gen Z new +156% vs LY in W29 | Ask premise box | `trailing.29.L1W.genz_new` (41 vs 16) |
| 6 checks | (spoken only) | DECISIONS D25; `web/src/lib/vocabulary.json` |
| About 30 seconds to rebuild | (spoken only) | CLAUDE.md, `run_all.sh --clean` |

**Judgment calls.**
- The suggested shape had 50 seconds for all four Explore tabs; I split it into G1 (with the like-for-like surprise), G3, G2 and G4 in that order, because the growth story reads "how much, from what, from whom", and stock was already covered on the Briefing.
- The Ask demo uses "Why did Gen Z new customers drop this week?" because it ties back to the G2 story and its correction (+156%) is the most striking; "Why are sales down vs last year?" works as well once the premise fix is live.
- The script uses the W29 numbers the default view shows (Tabby 2.1 weeks of supply) rather than the W30 numbers in FINDINGS (1.9), so what you say matches what the panel sees.
- "Tabby in Japan" is mentioned, not typed, to save 10 seconds of live wait; it was tested live and refuses as described.
- The "How it was built" tab is left out: the deck covers the build, and the validator demo on the Briefing shows the accuracy story in context.

## Site issues seen
Found while clicking through on 2026-10-25.

**Fixed on branch `fix-demo-exit-and-ask-premise`** (each reproduced end to end first, on the live site and locally):
- **Leaving a validator demo crashed the app to a blank page.**
  After the summary was held back, **Exit demo** or the "✕ Edited number" toggle threw `Cannot read properties of null (reading 'check')`, because `Summary` drew the old held-back phase with the new, passing text for one render.
  The check now restarts in the same render when the text changes, and the held-back state requires a failing text (`web/src/components/Briefing.tsx`).
- **Ask dropped the premise check on templates without a week or window.**
  "Why are sales down vs last year?" (`growth_drivers`) and the suggested "Why did demand fall in week 29?" (`why_flagged`) answered with no premise note, although Claude returned the premise.
  Every premise now gets a verdict over the period the answer covers, for the route's subject (a family, Gen Z or the whole business), or a sentence saying why it can't be checked; the keyword parser parses premises on every template except the family rankings (`web/src/lib/ask/engine.ts`, tests in `web/scripts/ask-test.mjs`).

**Still open:**

1. **Mixed periods side by side on G3.**
   The first tile is "Demand · PTD W23-W29 +12.1%", the next is "Tabby share of growth · PTD W23-W30", and the drill-down bar right below says "+12.8% · PTD W23-W30".
   Each is labeled, but two different period-to-date totals on one screen invite the question in section 3.
2. **British spelling "Enrol".**
   In the Briefing action list (`web/src/components/Briefing.tsx:445`) and in the W29 retention card text (`ai/session_texts.json`, which needs the validate, stamp and rebuild steps after editing).
3. **Em dash in rule messages.**
   `scripts/12_anomalies.py:104` writes an em dash before "G3 winner / Gen Z gateway." into critical `WOS_LOW` alerts (AN034, AN048, AN049), which show on the Briefing and the G1 playhead.
4. **Clipped labels in the G3 drill-down.**
   The drag chip "Tailored Jacket -9%" is cut off even at 1440 px, and at about 800 px the "Basket & frequency" driver tile and the "Trench" chip clip too.
5. **G4 scatter caption mixes weeks (not verified as a bug).**
   With W29 selected, the caption reads "stock = end-of-week on hand (TY W30, LY W29)".
   This is the F11 basis, but the reason for using different weeks for TY and LY is not explained on screen.
6. **Clickable text that isn't a button.**
   "Replay check", the four "Try a wrong text" demos, "Naive vs like-for-like →" and the How page links are `div`, `b` or `span` elements with an `onClick` and no role or tab stop (`Briefing.tsx:155` and `:157`, `LikeForLike.tsx:77`, `HowBuilt.tsx:57` and `:76`).
   Keyboard and screen-reader users can't reach them, and browser automation can't find them by name.
