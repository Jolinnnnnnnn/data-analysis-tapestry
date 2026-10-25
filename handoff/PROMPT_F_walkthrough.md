# PROMPT F: write a 3-minute interview walkthrough of the dashboard

You are working in `/Users/dereksun/code/jolin/data-analysis-tapestry`, the TYLY take-home for a Consumer Intelligence & Analytics role.
The dashboard (deliverable D1) is live at https://data-analysis-tapestry.vercel.app/.
In the follow-up interview the candidate presents the deck and then walks the panel through the dashboard live.
Your job is to write that walkthrough: a spoken script of about 3 minutes, in the candidate's own voice, plus the click path that goes with it and short answers to the questions the panel is most likely to ask.
This is a writing task, not a code change: don't edit the web app, the pipeline or any generated file.
Nobody will answer questions while you work, so when something is ambiguous, pick the most defensible option and note it at the end of the file.

## 0. Orient first
Read, in this order:
1. `~/.claude/CLAUDE.md` (the user's global rules; they beat any tool default).
2. `CLAUDE.md` (project memory: what the dashboard is, the pipeline, terminology, conventions).
3. `take_home_brief.pdf` (what the panel asked for and how it is judged: design and answer accuracy).
4. `FINDINGS.md` (F1-F15, R1-R3) and `NOTES.md` (current state).
5. `web/README.md`, then skim `web/src/components/Header.tsx`, `Briefing.tsx`, `Explore.tsx` and `Ask.tsx` to learn what each screen shows and what it is called on screen.
6. `DECISIONS.md` D14-D26 (why the dashboard works the way it does; the panel will ask "why").

Then open the live site in the built-in browser and click through every screen you plan to show: Briefing, Explore (G1-G4), Ask, and the like-for-like switch.
The nav may have changed since this prompt was written (for example, the "How it was built" tab may have been removed by the deck work in `handoff/PROMPT_D_deck.md`), so script what is actually there.
Note the exact on-screen labels, so the script says "click Explore, then G3" and not a guess.

## 1. Rules that matter most here
- Every figure in the script must be one the dashboard shows, read from `web/src/data/app.json` or `FINDINGS.md`, never from this prompt or from memory.
  The headline numbers below are a guide to the story; confirm each one before you use it.
- Use the project's display formats (12.8%, +122%, $71.3K, 2.1 weeks, +5.0 pts) and say "like-for-like" and "sample-scale" where they apply.
- Never use the em dash or en dash characters; use a plain "-".
- American English (enroll, color, labeled).
- Long Markdown: one full sentence per physical line.
- Commit and push only if the user asks, and never add a `Co-Authored-By` or any agent-name trailer.

## 2. What "interview style" means here
- It is spoken, first person, conversational: short sentences, no bullet-speak, no jargon the panel has to decode.
  Read it aloud in your head; if a sentence needs a breath in the middle, split it.
- It leads with the business answer, then shows the proof on screen.
  The panel are analytics people: they want "what's happening, why, and what do we do", and they will judge whether the numbers can be trusted.
- It talks to a business user's needs (what the trading or CRM team would do on Monday), not about React or scripts.
  The "how" gets one tight beat on trust, because answer accuracy is a judging criterion.
- It sounds like a person who made decisions: say what was chosen and why in a phrase ("I default to like-for-like because LY W30 has three extra days").
- About 3 minutes at a natural pace of about 150 words a minute, so 420-470 spoken words in total.
  Count them and report the count.

## 3. Suggested shape (adjust to what the site actually shows)
| Time | Screen | Beat |
|---|---|---|
| 0:00-0:20 | Briefing, default W29 | What this is and who it's for: a weekly TY vs LY view a merchant opens on Monday, defaulting to the last full week, like-for-like. |
| 0:20-1:00 | Briefing | The headline and the AI summary; the five flagged cards with their severity; the action list. Point out that every AI number is checked against the data before it is shown, and show the held-back state once (`#/briefing?wk=29&demo=blocked`). |
| 1:00-1:50 | Explore G1-G4 | G1: demand up like-for-like, driven by more customers, not bigger baskets (press Play or drag the playhead). The naive vs like-for-like switch as the one data surprise. G2: Gen Z new customers. G3: the Tabby franchise as most of the growth (drill-down). G4: Tabby nearly out of stock while Halo apparel is overstocked. |
| 1:50-2:30 | Ask | Type one question that shows judgment, for example a wrong premise ("Why did sales drop?") or an entity filter ("Show me Tabby performance"). Explain in one sentence that Claude only picks which question template to run and the code computes the answer, so the model never writes a number. |
| 2:30-3:00 | Close | Tie back to the top recommendation (R1-R3, ranked) and one honest limit (retention is a proxy because CUST_ID does not link customers), then hand back to the panel. |

Story points to confirm (FINDINGS.md): F1 demand +12.8% like-for-like; F2 naive +7.5%; Gen Z new customers +122%; Tabby + Pillow Tabby about 85% of growth; Tabby receipts-to-sales 0.28 TY vs 0.95 LY; Halo apparel overstocked.

## 4. What to deliver
Write `WALKTHROUGH.md` at the repo root with:
1. **The script**, split by the time blocks above.
   Each block has a one-line `Do:` (the exact click, URL hash or keystroke) followed by the spoken words.
   Put the full URL hash for any state that is fiddly to reach by clicking, so the candidate can paste it.
2. **A pre-flight checklist**: tabs to have open, the browser zoom level that keeps a screen readable when shared, reduce-motion off (or the "Animations" toggle on) so Play actually animates, and a fallback if live Ask is slow (the keyword parser still answers).
3. **Likely panel questions** (6-8) with a 2-3 sentence spoken answer each.
   Cover at least: why like-for-like, how you know an AI number is right, what happens when the AI is wrong, what the model can and can't see in Ask, why sample-scale counts are read as shares, what you would build next with more data, and how this stays correct when next week's data lands.
   Ground each answer in the repo (DECISIONS, FINDINGS, the validator), and cite the ID in a comment so the candidate can find the detail.
4. **A 60-second cut**: the same walkthrough trimmed to its three most important beats, in case the panel is short on time.
5. **A notes section**: the spoken word count, every figure used with where it came from (app.json path or finding ID), and any judgment call you made.

## 5. Verify before you finish
- Click through the script on the live site, in order, and confirm every `Do:` step lands on the screen the words describe.
- Check every figure in the script against the dashboard as shown, not only against the files.
- Read the script aloud (or count words) and confirm it fits in 3 minutes; cut, don't speed up.
- Search the file for em dash and en dash characters (U+2014, U+2013) and confirm there are none.
- If something on the site looks broken or off while you click through, don't fix it here: list it at the end of `WALKTHROUGH.md` under "Site issues seen".
