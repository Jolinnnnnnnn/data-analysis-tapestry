# FINDINGS — verified findings with evidence
Basis: PTD like-for-like = FY26 W23–W30 (W30 Sun–Wed) vs FY25 same weeks/days (D3). Counts are from a sample extract (D11), so read ratios and shares as the robust signal. p-values: Poisson count test / two-proportion z / bootstrap (D12).

### F1: [G1] Demand is up +12.8% YoY like-for-like, and the growth comes from more customers rather than bigger baskets
- Evidence: scripts/05_g1_performance.py → outputs/tables/05_g1_kpi_windows.csv, 05_g1_decomposition.csv, 05_g1_summary.md; figures g1_weekly_sales_ty_vs_ly.png, g1_yoy_decomposition.png
- Magnitude: demand $564,028 vs $499,804 (+12.8%); transactions 1,829 vs 1,690 (+8.2%, p=0.019); AOV $308.38 vs $295.74 (+4.3%, 95% CI on diff [-$1.75, +$27.28], p=0.085); UPT flat (1.24); frequency 1.00. Log decomposition: customers 65% of growth, AUR 34%, UPT/frequency ~0. L1W (W29) +12.7%, L4W (W26–29) +13.2%, WTD (W30 Sun–Wed) +21.7%. TY beat LY in all 8 weeks.
- Caveats: the AOV lift is not significant and shrinks to +2.3% when the top 1% of lines are excluded. Customer count ≈ transaction count because CUST_ID doesn't link purchases (D5).
- Challenge (09_sensitivity.md): holds for full weeks only (+12.1%), dropping the top 1% of lines (+10.1%), and leave-one-week-out (+11.1% to +14.3%). All 8 weeks are positive. Channel mix is stable (outlet 30.8% → 29.2% of transactions). **Concentration:** ex-Tabby growth is +6.4%, and ex-Tabby-and-Pillow-Tabby it is +2.4% (see F9).
- Status: verified
- So what: growth is a traffic/acquisition story. Basket-building (UPT 1.24, single-line transactions) is untapped.

### F2: [G1][surprising] The YoY headline depends on the period definition: naive all-rows comparison gives +7.5%, like-for-like gives +12.8%
- Evidence: scripts/05_g1_performance.py → outputs/tables/05_g1_kpi_windows.csv (windows "PTD alt-a" vs "PTD")
- Magnitude: TY's last week (W30) has only 4 days (Sun–Wed 2026-08-16..19) while LY W30 has 7. Comparing all rows overstates LY by 90 lines ($25.1K), which understates growth by ~5 pts. Full-weeks-only (W23–W29) gives +12.1%.
- Caveats: none; this is an arithmetic artifact of the extract cut-off.
- Status: surprising (artifact, handled)
- So what: the dashboard must default to like-for-like days. Any weekly report that compares a partial TY week to a full LY week will mis-state performance.

### F3: [G1] W29 was down -18.8% WoW, but that is a W28 basket spike, not a traffic drop
- Evidence: scripts/05_g1_performance.py → outputs/tables/05_g1_wow_prior.csv, 05_g1_weekly.csv
- Magnitude: W29 vs W28 transactions -2.3% (250 vs 256), AOV -16.9% ($285 vs $343). W29 is still +12.7% YoY. W28 was the strongest YoY week (+23.1%) on AOV +13%.
- Caveats: weekly AOV is noisy at ~250 transactions/week.
- Status: verified
- So what: read trailing performance YoY and on traffic, not raw WoW demand. The anomaly rules (Phase M) should separate traffic moves from AOV moves.

### F4: [G2] Gen Z new-customer acquisition more than doubled (+122%) and accounts for ~97% of all new-customer growth
- Evidence: scripts/06_g2_genz.py → outputs/tables/06_g2_by_generation.csv, 06_g2_summary.md; figure g2_new_customers_by_generation_ty_vs_ly.png
- Magnitude: Gen Z new 240 vs 108 (+122%, p<0.001). All new 590 vs 454 (+30%). Non-Gen Z new 350 vs 346 (+1.2%, p=0.88). Gen Z share of new customers 40.7% vs 23.8% (p<0.001). Gen Z transactions +46.9% (398 vs 271), of which new +132 and returning -5. Gen Z = +8.2 pts of the 12.8% demand growth.
- Caveats: "New" is the brand's full-history status (D6), not validated by us. Generation is a label (D7). Equal sampling rate assumed (D11), but the share-of-new result doesn't depend on that.
- Challenge (09_sensitivity.md): survives every test. New+Reactivated definition: +95%, share 32.2% vs 19.2%. Excluding Tabby: +121%. Excluding both Tabby families: +112%. Up in every region (Europe 60/18, Japan 22/4, Greater China 39/23, North America 119/63) and both channels. Product-mix-standardized share 39.3% vs 23.8%; region-mix-standardized 40.2%. Bootstrap CI on the share difference [+11.2, +22.5] pts. Excluding partial W30: +106%.
- Status: verified (robust)
- So what: the G2 acquisition goal is working, and Gen Z is effectively the only source of incremental new customers.

### F5: [G2][surprising] Gen Z acquisition is accelerating through the period: Gen Z share of new customers rose from 33% (W23) to 47% (W29) and 56% in W30 WTD
- Evidence: scripts/06_g2_genz.py → outputs/tables/06_g2_genz_new_by_week.csv; figure g2_genz_share_of_new_by_week.png
- Magnitude: TY above LY in 8 of 8 weeks. LY share flat around 24% (range 13–29%). Weekly Gen Z new counts 22 → 41 (W23 → W29).
- Caveats: weekly n is 50–90 new customers.
- Challenge (09): TY W27–30 vs W23–26 share 46.0% vs 34.9% (p=0.006). Weighted slope +2.8 pts/week. Line-level permutation test p=0.002. LY over the same weeks is flat or falling (20.8% vs 26.9%, p=0.13), so this is not seasonality.
- Where it comes from (06_g2_genz_new_acceleration_split.csv): TY Gen Z new W27–30 vs W23–26 is +44 (142 vs 98) even though W27–30 has only 3.6 weeks of data. Of that, +41 is in physical stores (eComm +3) and +40 in full-price RETAIL (Outlet +4). By region: North America +27, Europe +14, Japan +4, Greater China -1. Spread across product types (Core +17, Evergreen +14, Halo +7, Hero +6), so it's not a single-product effect. Hero's small gain may be constrained by Tabby stock (F11, hypothesis).
- Status: verified (surprising)
- So what: something changed for Gen Z in full-price stores mid-summer (campaign, store event, social moment?). Store teams are now the main Gen Z acquisition channel. The data to explain it isn't in the file (marketing/store-event calendar).

### F6: [G2] Retention proxy is weak: returning-customer transactions are flat (+0.2%), and returning Gen Z is down (-3%) despite last year's Gen Z acquisition
- Evidence: scripts/06_g2_genz.py → outputs/tables/06_g2_by_generation.csv; figure g2_new_vs_returning_yoy_by_generation.png
- Magnitude: returning (Retained+Reactivated) 1,239 vs 1,236 (+0.2%). Gen Z returning 158 vs 163 (-3.1%, n.s.). Returning share of Gen Z transactions 39.7% vs 60.1%. Reactivated 258 vs 276 (-6.5%). Retained demand +2.7% vs New demand +38.9%.
- Caveats: this is a mix proxy, not a cohort retention rate (D8). CUST_ID can't link LY buyers to TY (D5). Flat returning counts are consistent with poor retention, but also with retention benefits that only show up later.
- Challenge (09): Retained only +2.2% (p=0.63). Reactivated -6.5%. Returning non-Gen Z +0.7%. Excluding W30: exactly flat (1,142 vs 1,142). Returning demand +3.2%, which comes only from price.
- Status: verified (as proxy)
- So what: the business is filling a leaky bucket. Gen Z acquired last year are not visibly showing up as returning buyers this year. Retention, not acquisition, is the G2 constraint.

### F7: [G2] New Gen Z customers are the least likely to join Insider (17% vs 23% Millennials), and the rate isn't improving
- Evidence: scripts/06_g2_genz.py → 06_g2_by_generation.csv (new_insider_rate_*)
- Magnitude: new Gen Z Insider share TY 17.1% vs LY 21.3% (p=0.35). Insider share among Retained customers is ~70% vs 19% among New (04_identity_checks.md), so loyalty enrolment is strongly associated with being a returning customer.
- Caveats: association, not causation, and the Insider→retention link can't be shown at the customer level.
- Where the gap is (06_g2_new_insider_by_segment.csv, TY new Gen Z vs other new): Outlet 9.7% vs 23.1% (p=0.029); Greater China 5.1% vs 21.7% (p=0.023); eComm 12.7% vs 19.2% (n.s.). Full-price RETAIL is at parity (19.7% vs 19.8%).
- Status: verified (rates; segment gaps tentative, n=22–79), tentative (implication)
- So what: Insider enrolment at the first Gen Z purchase is the most actionable retention lever visible in the data. Target Outlet, eComm checkout and Greater China first.

### F8: [G2] New Gen Z buy the Tabby franchise (= "Hero") first, mostly in full-price stores, and are not discount-driven
- Evidence: scripts/06_g2_genz.py → 06_g2_first_purchase_mix.csv, 06_g2_new_genz_value.csv, 06_g2_genz_new_by_region.csv, 06_g2_genz_new_by_channel.csv; figure g2_genz_first_purchase_family_mix.png
- Magnitude (TY): Hero = 24.2% of new Gen Z first purchases vs 14.3% for other new (index 169, p=0.002). Tabby 17.9% vs 10.9% (index 165, p=0.014). Pillow Tabby index 182 (n=15, n.s.). Europe index 148 (p=0.015). Retail Store new Gen Z +145% YoY (49→120). New Gen Z AUR $262 vs $240 (diff +$22, CI [$0.9, $43.0], p=0.04). Outlet share 25.8% vs 30.9% (n.s.). Pooled TY+LY price index 0.93 vs 0.89 (p=0.019). AOV +$24 (n.s.).
- Caveats: family-level cells are small (most n<20). Only Tabby and Hero are significant.
- Challenge (09): "Hero" is exactly Tabby + Pillow Tabby (no other Hero families), so the Hero over-index *is* the Tabby effect. The AUR premium is mostly mix: the within-family gap is only +$8.4 (vs +$22 raw), and the TY-only within-style price index is n.s. (p=0.20). Gen Z chooses pricier families rather than paying more for the same item. "Not discount-driven" still holds (outlet share not higher).
- Status: verified (Tabby gateway, not discount-driven); **downgraded** (AUR premium → mostly product mix)
- So what: Tabby/Hero are the Gen Z gateway, and Gen Z pays full price. Protect Tabby/Hero stock and full-price positioning rather than discounting to acquire.

### F9: [G3] Growth is concentrated in one franchise: Tabby + Pillow Tabby (both Hero) = 85% of total demand growth
- Evidence: scripts/07_g3_products.py → outputs/tables/07_g3_family_scorecard.csv, 07_g3_style_scorecard.csv; figures g3_family_growth_contribution.png, g3_family_growth_vs_genz_index.png
- Magnitude: Tabby $125.8K vs $88.1K (+42.9%, txns p=0.006, +7.6 pts of the 12.8%; Tabby alone = 59% of total growth). Pillow Tabby $37.4K vs $20.4K (+83.4%, p=0.011, +3.4 pts). Hero type +50.5% (+11.0 pts). Lead styles: Tabby 20 (+57%, p=0.04), Tabby Messenger (+42%), Pillow Tabby 18 (+105%, p=0.049). Both families over-index on Gen Z (index 122 / 144) and on new Gen Z first purchases (165 / 182).
- Caveats: style-level n is 40–100 lines per year.
- Status: verified
- So what: Tabby is the winner worth sharing across the business and the Gen Z gateway. Its playbook (Hero newness at full price) is the template.

### F10: [G3] Halo statement pieces, especially apparel and Rogue, are the drag
- Evidence: scripts/07_g3_products.py → 07_g3_family_scorecard.csv; 05_g1_contribution.csv
- Magnitude: Halo -21.2% (-5.6 pts). Rogue -22.6% (p=0.021, -2.5 pts), Knit Dress -50.8% (p=0.029, -2.1 pts), Tailored Jacket -33.3% (p=0.081), Trench -22.2% (n.s.). Womens Apparel category -35.7% (txns p=0.009).
- Caveats: Halo's role is brand-building, not volume, so a sales decline may be acceptable. Margin data isn't in the file.
- Status: verified (Rogue, Knit Dress); tentative (Trench, Tailored Jacket)
- So what: reduce Halo apparel buys and redirect open-to-buy to Hero.

### F11: [G4] Stock is in the wrong place: the winners (Tabby, Pillow Tabby) have <2 weeks of supply while slow apparel holds 16–21 weeks
- Evidence: scripts/08_g4_inventory.py → outputs/tables/08_g4_position.csv, 08_g4_weekly_family.csv, 08_g4_summary.md; figures g4_weeks_of_supply_by_family.png, g4_stock_vs_demand_share.png
- Magnitude: Tabby WOS 1.9 (LY 7.0); EOH 82 at W30 vs 290 at W23 (-72%); W29 EOH -66% YoY. Pillow Tabby WOS 1.6 (LY 5.1). Tabby = 14.0% of L4W unit demand but 3.5% of stock (-10.5 pts). Knit Dress WOS 21.2 (units -55%), Trench 16.9 (EOH +83% YoY, units -12%), Tailored Jacket 16.3. Median family WOS 7.9. Family stock-vs-demand correlation 0.96 LY → 0.33 TY.
- Caveats: WOS uses sample-scale sales. The scale check passes (implied receipts never negative, 0/273). TY W30 snapshot is dated after the last sales day (F13).
- Status: verified
- So what: Tabby will likely stock out within about 2 weeks at the current run rate, which would cap the main growth driver and the main Gen Z acquisition product.

### F12: [G4][surprising] Replenishment stopped following demand this year: Tabby received only 28% of what it sold (LY 95%)
- Evidence: scripts/08_g4_inventory.py → 08_g4_position.csv (receipts_*), 08_g4_weekly_family.csv (implied_receipts)
- Magnitude: implied receipts W24–29 (ΔEOH + units): Tabby 78 vs LY 203 (-62%), receipts/sales 0.28 vs 0.95. Pillow Tabby 0.29 vs 0.85. Apparel 1.30–1.38 (Knit Dress 1.34 while units -55%). Receipts-vs-demand correlation 0.99 LY → 0.53 TY. Total receipts/sales 0.87 vs 0.99.
- Caveats: receipts are inferred, not observed (no PO/receipt data), and transfers or damages are indistinguishable.
- Status: surprising (looks real, not an artifact: consistent across 6 weeks and both Tabby families)
- So what: this is a process failure (allocation/replenishment rules or supply constraint), not a demand problem. Need PO/supplier data to tell which.

### F13: [G4][surprising] The TY W30 inventory snapshot is labelled "end of week" but is dated after the last TY sale (Wed 2026-08-19)
- Evidence: scripts/02_profile.py → outputs/tables/02_profile.md (week coverage); scripts/03_clean.py → 03_cleaning_log.md (TY as-of)
- Magnitude: TY W30 sales cover 4 of 7 days, yet all 21 families have a W30 ON_HAND_UNITS value.
- Caveats: it could be a mid-week snapshot mislabelled, a planned/projected position, or an extract-timing artifact.
- Status: surprising (likely artifact of extract timing)
- So what: used only as the "latest position" with a full-week (W26–29) demand denominator. F11 conclusions hold with W29 EOH instead (09: Tabby WOS 2.1, Pillow Tabby 1.8).

### F14: [All][surprising] The extract can't support basket or cohort analysis: every transaction is one line, and CUST_ID behaves like a random number
- Evidence: scripts/02_profile.py (3,609 rows = 3,609 TXN_IDs); scripts/04_identity_checks.py → 04_identity_checks.md, 04_repeat_ids.csv
- Magnitude: 9 repeat IDs vs 7.2 expected from random 6-digit IDs (Monte Carlo p=0.30). 0/9 repeat IDs agree on age, insider and region. One ID is "New" on two TY purchases 20 days apart with different generations.
- Caveats: the full source table may link correctly. This is a property of the sample.
- Status: surprising (artifact of sampling / ID anonymisation)
- So what: retention has to be proxied with COHORT_STATUS (D8). The top data request is a persistent customer key with full purchase history.

### F15: [G3][G2] Watch list: Mens Bag (esp. League Backpack) is the next Gen Z over-indexer, though total family sales are flat
- Evidence: scripts/07_g3_products.py → 07_g3_family_scorecard.csv, 07_g3_style_scorecard.csv; scripts/06_g2_genz.py → 06_g2_genz_new_by_family_yoy.csv; scripts/08_g4_inventory.py → 08_g4_position.csv
- Magnitude: Mens Bag Gen Z index 151 (highest of all families). League Backpack 181. Gen Z transactions in the family +111% YoY. Gen Z new first purchases 11 vs 1 LY. Returning Gen Z mix index 211. Family demand only +5.5% (txns 58 vs 61). WOS 5.8 (below median 7.9).
- Caveats: small n (11 Gen Z new). Gen Z gains are offset by declines among other generations.
- Status: tentative
- So what: a candidate second Gen Z gateway (and a men's/unisex entry point). Test it in Gen Z marketing before scaling buys.

---
## Draft recommendations (ranked)

### R1. Protect and chase the Tabby franchise now: re-open replenishment on Tabby and Pillow Tabby
- Supporting findings: F9 (85% of growth), F8 (Gen Z gateway), F11 (WOS 1.9 / 1.6), F12 (receipts 28% of sales vs 95% LY), F5 (Gen Z wave accelerating).
- Why first: it protects the main growth engine *and* the main Gen Z acquisition product, it's time-critical (about 2–3 weeks to stock-out), and it's within the business's control.
- Expected impact (scripts/10_sizing.py → outputs/tables/10_sizing.md): at the TY replenishment pace, Tabby stocks out in ~2.6 weeks and Pillow Tabby in ~2.2. The 4-week shortfall is 43 + 19 units, about $23.1K sample demand = **7.7% of total demand over the next 4 weeks**, plus ~8 new Gen Z customers (6.4% of the 4-week Gen Z new run-rate). Restoring LY weeks of supply needs ≈ 229 Tabby + 53 Pillow Tabby units. Assumptions: L4W run-rate continues, no substitution, TY AUR.
- Data not in file: open POs / inbound supply and lead times, store-level stock (is the shortage everywhere?), supplier constraints, margin by style.

### R2. Rebalance open-to-buy from Halo apparel to Hero; mark down or transfer the apparel overhang
- Supporting findings: F10 (Halo -21%, Knit Dress -51%, Rogue -23%), F11 (apparel WOS 16–21 vs median 7.9), F12 (apparel receipts 1.3–1.4× sales).
- Expected impact (10_sizing.md): 198 units / **$50.5K retail value** above median weeks of supply in Trench, Tailored Jacket and Knit Dress (9.0% of TY PTD demand at retail). Shifting future receipts toward Hero closes the 282-unit Tabby-franchise gap. Assumptions: median WOS as target, valued at TY AUR (retail, not cost).
- Data not in file: cost/margin and markdown elasticity, Halo's brand-role KPIs (traffic, awareness), size/colour-level stock, store-by-store allocation.

### R3. Turn the Gen Z acquisition wave into repeat customers: Insider enrolment at the first Gen Z purchase, plus a Tabby-led second-purchase journey
- Supporting findings: F4 (+122% Gen Z new), F6 (returning Gen Z -3%, returning flat overall), F7 (Gen Z new Insider attach 17% vs 23% Millennial; 71% of Retained are Insiders), F8 (Tabby gateway, full price).
- Expected impact (10_sizing.md, scenario): closing the Insider gap to Millennial = +15 Gen Z Insiders per 7.6 weeks in the sample (+37% relative). If that lifts returning Gen Z volume by 10%, it adds ≈ +0.85% of TY demand (+1.7% at 20%). Smaller near-term than R1, but compounding, and it's the G2 priority.
- Data not in file: persistent customer key with full history (repeat rate, time to second purchase, CLV), Insider vs non-Insider repeat behaviour, CRM/marketing touches and campaign calendar (to explain F5), birth year.
