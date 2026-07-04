# Factor & Geographic Diversification Thesis

**Scope of this document.** This is the *conceptual* layer of the portfolio project: why we diversify across equity factors and regions, what the academic evidence says about how those factors *co-move*, and which future regimes each piece is meant to hedge. It deliberately contains **no realized-return / backtest numbers** — those belong in a separate empirical document. The goal here is to have a defensible, source-backed rationale *before* looking at any performance chart, so that the eventual allocation is driven by structural logic rather than by fitting the recent past.

**A necessary caveat.** Nothing here is personalized investment advice; it is a research synthesis. Every claim that rests on empirical work is attributed to a primary source (see [References](#references)). Where a statement is a modeling judgment rather than a documented finding, it is flagged as such.

---

## 1. The problem statement: two axes of uncertainty, not one

The objective — "a 20–30 year portfolio, diversified for exposure, targeting maximum return" — contains a tension that has to be made explicit, because it drives everything else.

A literal "maximum expected return" portfolio, under most ex-ante models, would be highly concentrated (today: US mega-cap growth/technology). "Diversified" pulls in the opposite direction. So the real objective is not to maximize an unconditional return, but to **maximize expected return *conditional on being robust to a change of regime*** over a horizon long enough that at least one — probably several — regime changes will occur. Framed that way, factor and geographic diversification stop being a "return drag to be tolerated" and become the mechanism that keeps the portfolio participating in whichever regime actually materializes.

There are **two independent axes of uncertainty** the portfolio must survive:

1. **Geographic / country axis** — will the United States continue to dominate global market capitalization, or does leadership rotate toward Europe, Japan, or emerging markets over the horizon?
2. **Factor / style axis** — does the current growth + momentum + mega-cap regime persist, or do we get a multi-year period led by value, quality, or smaller companies (as happened, for example, across 2000–2010)?

These are *separable*. You can be right about geography and wrong about style, or vice versa. A single cap-weighted global index bundles both bets into one implicit, uncontrolled position. The entire thesis below is about **un-bundling** them so each can be sized deliberately.

### 1.1 Why "buying the world" is already an active bet

The starting point most investors treat as neutral — a cap-weighted global index (MSCI ACWI or MSCI World) — is not neutral at all. As of the May 2026 index data:

- **MSCI World** (developed only): the United States is ~72% of the index; Information Technology is ~31% of the sector breakdown.
- **MSCI ACWI** (developed + emerging): the United States is ~64%; emerging markets are only ~12% of the total, despite representing a far larger share of world GDP, population, and prospective growth.

Cap-weighting means the index's country and sector mix is decided *by past price appreciation*. Buying it is therefore an implicit, momentum-like bet that the recent winners keep winning. That may well be correct — but it is a choice, and the point of this project is to make that choice consciously rather than by default.

> **Source note.** US/sector weights above are from the MSCI World and MSCI ACWI index factsheets (data as of 29 May 2026) and the justETF ACWI overview. Weights drift monthly; re-pull before quoting exact figures in any deliverable.

---

## 2. The factors, defined from first principles

MSCI's factor index family (the page under discussion) operationalizes a set of *equity risk/style factors* that decades of academic work have documented. Below, each is defined structurally — what it selects, why a premium might exist, and its known weaknesses — because the diversification argument later depends entirely on these structural differences.

### 2.1 Value

- **What it selects:** companies cheap relative to fundamentals (low price-to-book, low P/E, low EV/EBITDA). MSCI's *Enhanced Value* methodology screens on several such ratios and is designed to mitigate obvious "value traps."
- **Why a premium might exist:** the foundational documentation is Fama & French (1992, 1993), who showed book-to-market equity explains a large part of the cross-section of average stock returns beyond market beta, giving rise to the "HML" (high-minus-low) value factor. Competing explanations divide into *risk-based* (cheap firms are riskier / more exposed to distress) and *behavioral* (investors over-extrapolate bad news, so cheap firms are systematically under-priced).
- **Known weakness:** the premium can be absent for very long stretches. Value materially underperformed growth across roughly 2007–2020 in developed markets — more than a decade. Any value allocation has to be sized so that the investor can psychologically survive a "lost decade" without capitulating, because the whole point is to still be holding it when the regime turns.
- **Structural consequence (important later):** because value *by construction* buys what the market currently shuns, it automatically tilts *away* from whatever is expensive. Today that means tilting away from the US and from mega-cap technology, and toward Europe, Japan, and parts of EM — i.e., value carries a built-in geographic rotation.

### 2.2 Growth

- **What it selects:** the mirror image of value — high sales/earnings growth, high valuation multiples. MSCI's *Growth Target* index currently concentrates in names like Nvidia, Broadcom, and other large-cap technology/AI beneficiaries.
- **Role in the thesis:** growth is **not** treated here as a satellite to *add*, because a cap-weighted developed-market core *already* provides heavy growth exposure. The largest positions in MSCI World are the same names that dominate a growth screen. Adding an explicit growth sleeve would double down on the exposure you are trying to diversify *away* from, not diversify into. Growth is discussed for completeness and to make the overlap point (Section 4) concrete.

### 2.3 Quality

- **What it selects:** profitable, financially healthy firms — high return-on-equity, stable earnings, low leverage.
- **Why a premium might exist:** Novy-Marx (2013), "The Other Side of Value: The Gross Profitability Premium" (*Journal of Financial Economics* 108(1), 1–28), showed that gross-profits-to-assets predicts the cross-section of returns with roughly the same power as book-to-market, and — critically — is *complementary* to it. Asness, Frazzini & Pedersen's "Quality Minus Junk" (2019) generalized quality across multiple dimensions (profitability, growth, safety, payout) and documented a quality premium internationally.
- **Role:** quality tends to be defensive — it holds up better in recessions and periods of stress — while sacrificing less long-run return than a pure low-volatility screen. It also serves as an antidote to the "value trap" problem: a *cheap and high-quality* firm is a better proposition than *cheap and deteriorating*. This is why quality and value are often paired.
- **Overlap caveat:** in the current regime, a global "Quality" screen selects many of the same mega-cap technology names that already dominate the cap-weighted index (they have exceptional ROE and low leverage). So a standalone World Quality sleeve offers *less* incremental geographic diversification than its name implies — it mostly reduces idiosyncratic risk *within* the existing exposure. This is developed in Section 4.

### 2.4 Momentum

- **What it selects:** stocks with strong recent price trends (typically trailing 6–12 month returns, skipping the most recent month).
- **Why a premium might exist:** Jegadeesh & Titman (1993) documented that past winners continue to outperform past losers over intermediate horizons. Behavioral explanations center on investor *under-reaction* to news followed by delayed *over-reaction*.
- **Known weakness — "momentum crashes":** momentum can reverse violently at turning points (the sharp 2009 reversal is the canonical example), producing rare but severe drawdowns. Its return distribution has a fat left tail.
- **Geographic subtlety (important for this project):** momentum is one of the most *pervasive* factors internationally — **except Japan**, which is the documented exception where the momentum effect is weak or absent (Chui, Titman & Wei 2010; Fama & French 2012; Asness, Moskowitz & Pedersen 2013). A momentum index built *without* geographic restriction naturally under-weights Japan (there are no strong trends there to capture) and over-weights markets where trends persist. This argues *against* forcing a Japan-specific momentum sleeve, and *for* letting a global momentum index select freely.

### 2.5 Size (Small-cap)

- **What it selects:** smaller companies (the "SMB" factor of Fama-French). MSCI's *Equal Weighted* indices are a cheap, indirect way to gain a size tilt by breaking the mega-cap concentration of cap-weighting.
- **Status:** the size premium is the most contested of the classic factors — weaker and less stable out-of-sample than value, quality, or momentum, and much of it may be a proxy for quality/junk composition among small firms. It is treated here as *optional* and best accessed via equal-weighting rather than as a standalone conviction sleeve.

### 2.6 Minimum Volatility & High Dividend — and why they are *de-emphasized*

- **Minimum Volatility:** engineered to reduce portfolio variance, not to maximize return. It tends to lag in sustained bull markets. For a 20–30 year *maximum-return-conditional-on-robustness* mandate it is structurally the wrong tool — it belongs closer to a decumulation/defensive phase.
- **High Dividend Yield:** overlaps heavily with value (dividend-payers are disproportionately mature, cheaper firms). It adds little *diversification* beyond an Enhanced Value sleeve and introduces a sector/behavioral bias toward mature payers. De-emphasized for the same reason: redundancy, not defect.

---

## 3. The core of the thesis: how factors *co-move*

This is the analytical heart of the document. Diversification value comes not from each factor's standalone premium but from **low or negative correlation between the factors' active returns**. If two sleeves rise and fall together, holding both adds cost and complexity without reducing risk.

### 3.1 The value–momentum relationship (the strongest result)

The single most important empirical result for this project is Asness, Moskowitz & Pedersen (2013), "Value and Momentum Everywhere" (*Journal of Finance* 68(3), 929–985). Its findings, in order of relevance:

1. **Universality:** value and momentum premia are positive and statistically significant across eight diverse markets and asset classes (US, UK, continental Europe, Japan equities, plus country indices, government bonds, currencies, commodities). This breadth is what makes data-mining an unlikely explanation — it is very hard to over-fit the same two patterns across that many independent arenas.
2. **Negative correlation:** value and momentum are **negatively correlated with each other, both within and across markets**, with a correlation commonly cited in the −0.5 to −0.6 range. When cheap stocks rally (value wins), trend-following typically struggles; when trends persist (momentum wins), value typically lags. *This negative correlation is the quantitative engine of the diversification benefit* — combining the two smooths the ride far more than combining two positively-correlated factors would.
3. **Common global structure:** the returns share a common factor structure partly linked to global funding-liquidity risk, but there remains a *region-specific* component that is not fully explained by the global factor. That residual is what justifies looking at factors region-by-region rather than only globally (Section 5).

### 3.2 Where quality fits

Quality is the natural "third leg." Novy-Marx (2013) framed profitability as *the other side of value* — complementary to it, adding information above and beyond book-to-market even among the largest, most liquid stocks. Practically, quality correlates moderately with both value and momentum and is defensive in stress, so it acts as a *hinge* between the two more cyclical factors rather than as another independent axis. A value + quality pairing specifically counteracts value's "buying deteriorating businesses" failure mode.

### 3.3 The resulting mental model

- **Value ↔ Momentum:** the primary diversifying pair (strong negative correlation). They hedge *each other's* regime.
- **Quality:** defensive hinge; improves the quality of the value sleeve and cushions drawdowns.
- **Size / Equal-weight:** optional concentration-reducer, not a core conviction.
- **Min-Vol / High-Dividend:** de-emphasized for a growth-oriented long horizon.

The design principle that falls out of this: **a value + momentum + quality combination spans most of the plausible regime space** — value wins in mean-reversion/inflationary/rate-normalization regimes, momentum wins in sustained-trend regimes, quality wins in recessions and uncertainty. You are not trying to *predict* the regime; you are trying to *hold something that works in each one*.

---

## 4. The overlap problem: why factor labels can lie

A subtle but critical point that must be checked before any allocation is fixed: **in the current market regime, "Quality," "Momentum," and "Growth" global screens select heavily overlapping names, and those names are also the largest positions in the cap-weighted core.**

Microsoft, Apple, Nvidia (and peers) are simultaneously:
- very high ROE / low leverage → they pass any **Quality** screen;
- strong recent price trends → they pass any **Momentum** screen;
- high growth multiples → they *are* the **Growth** index;
- already the top holdings of **cap-weighted MSCI World / S&P 500**.

The implication: a portfolio that stacks *core + World Quality + World Momentum* can end up with a *de facto* triple-weighting of a handful of stocks while the factsheets make it look diversified. The diversification is nominal, not real.

**Value is the structural exception.** By construction it selects the opposite of what dominates today, which is precisely why it carries genuine diversification *and* an automatic geographic rotation away from the US.

**Practical mandate:** before finalizing weights, run a *holdings-overlap ("X-ray")* analysis across every candidate sleeve — cross the top 20–30 holdings of each fund, and check the effective single-name concentration (e.g., total look-through weight in Nvidia across core + quality + momentum). Morningstar's Instant X-Ray or a manual cross-tabulation of published fund holdings both work. If two "different" sleeves show very high active-return correlation, that is evidence their overlap is cancelling the theoretical benefit of holding both.

---

## 5. The geographic dimension and its interaction with factors

The question that motivated this document — *"can I combine Quality USA, Value ex-USA, World Momentum?"* — is really about whether the *region-specific residual* from Section 3.1 is worth harvesting separately. The answer is a qualified yes, driven by structural (not performance-chasing) reasoning:

- **Value is best expressed with a deliberate geographic tilt.** Because "cheap" currently lives outside the US, a *Value ex-US* (or, better, separate *Value Europe* and *Value EM*) sleeve concentrates the factor where the opportunity set is genuinely larger, instead of diluting it with a thin US-value universe. Europe and EM also have *different* valuation dynamics from each other (Europe: slower structural growth, financial/industrial sector composition; EM: country-risk premium), so splitting them gives finer control than a single "ex-US" bucket.
- **Quality expressed in the US** mostly reduces *idiosyncratic risk within* the US bet; it does not add much geographic diversification (high overlap with core). Legitimate, but understand what it does and does not buy.
- **Momentum is best left geographically unconstrained**, because the factor naturally routes around the Japan exception (Section 2.4). Forcing region-specific momentum sleeves would fight the evidence. If Japan exposure via a factor is desired, it should come through *value* or *quality*, not momentum.

### 5.1 The distinction that separates good design from data-mining

Combining factor × region is defensible **only** when the reason is *structural* (the factor behaves differently there for durable reasons — sector composition, investor behavior, valuation starting point). It is **not** defensible when the reason is that *that specific factor × region × time window* happened to beat its benchmark in a backtest. Almost any factor/region/period triple can be made to look like a winner ex-post if you search enough combinations — this is the classic over-fitting trap. This document intentionally stops at the structural rationale and defers all realized-return evidence to a separate empirical file, precisely to avoid letting the backtest drive the thesis.

---

## 6. Future scenarios and what hedges each

The portfolio should be readable as an explicit set of hedges. The table maps plausible 20–30 year regimes to the sleeve that carries the load in each. (This is a *design map*, not a probability forecast.)

| Future scenario | What outperforms | Sleeve that carries it |
|---|---|---|
| Status quo continues: US + mega-cap growth/AI leadership persists | S&P 500, Momentum, Growth | US core + World Momentum |
| Style rotation to value / end of the structurally-low-rate era | Enhanced Value, High Dividend | Value (Europe + EM) |
| EM (India, China, SE Asia, LatAm) captures a rising share of world GDP relative to its current ~12% index weight | MSCI EM, EM factor tilts | Deliberate EM over-weight vs cap-weight |
| Recession / macro stress / AI-narrative breakdown | Quality, Min-Vol | Quality sleeve as partial cushion |
| Europe regains relative competitiveness (defense, re-industrialization, fiscal expansion) | MSCI Europe | Developed-Europe not under-weighted the way ACWI does |

The unifying idea: **each row is a bet the portfolio would otherwise lose if it simply held the cap-weighted index.** The cap-weighted index wins only the first row cleanly; the diversification exists to keep you solvent and participating in the other four.

---

## 7. Risks, caveats, and honest limits of the thesis

These belong in the thesis itself, not as an afterthought — they are the reasons a factor approach can disappoint, and a report that omits them is not trustworthy.

1. **"Maximum return" and "full diversification" are partly contradictory.** The maximum-*ex-ante*-return portfolio is concentrated; diversification is a deliberate sacrifice of some conditional expected return in exchange for robustness across regimes. Be explicit that this is the trade being made.

2. **Factors can under-perform for 10+ years.** Value's 2007–2020 stretch is the cautionary case. This is *survivable* over a 20–30 year horizon but psychologically brutal in real time; the allocation must be sized so that conviction survives the drawdown.

3. **Factor decay after publication.** McLean & Pontiff (2016), "Does Academic Research Destroy Stock Return Predictability?" (*Journal of Finance* 71(1), 5–32), found that documented predictors' long-short returns were on average ~26% lower out-of-sample and ~58% lower post-publication — evidence that publicizing a factor erodes it as capital crowds in. Expect *smaller* future premia than the historical papers report, especially for the most popular factors (momentum, quality are heavily productized via ETFs today).

4. **Crowding raises correlations.** McLean & Pontiff also documented that predictor portfolios' correlations with *other* published predictors *increase* post-publication — meaning the diversification benefit itself can decay as more investors hold the same factor sleeves. The correlation structure of Section 3 is not a constant of nature.

5. **Overlap can silently undo the design** (Section 4) — the single most likely *implementation* failure. Always X-ray before committing weights.

6. **Cost and operational drag.** Each additional factor × region sleeve adds a management fee (factor UCITS typically ~0.25–0.30% TER vs ~0.07–0.20% for a plain cap-weighted index), a line to manage, and tracking-error budget spent. More sleeves is not automatically better; past 3–4 well-differentiated sleeves the marginal diversification usually shrinks faster than the marginal cost/complexity.

7. **Model risk in this very document.** The correlation figures and factor definitions come from a specific body of literature that could be revised. Treat the −0.5/−0.6 value-momentum correlation as a well-supported historical *average*, not a guaranteed forward constant.

---

## 8. Design principles that fall out of the thesis

Distilled, before any numbers are attached:

1. **Un-bundle the two axes** (geography and style) so each is sized on purpose.
2. **Core + satellite**, not a factor free-for-all: a broad global core carries most of the equity premium; factor sleeves are a *conviction overlay*, not the engine.
3. **Value + Momentum as the primary diversifying pair** (negative correlation), **Quality as the defensive hinge.** De-emphasize Min-Vol / High-Dividend for this horizon.
4. **Express value with a geographic tilt** (Europe + EM separately); **leave momentum geographically free** (it routes around Japan); **understand US-Quality as risk-reduction within the US bet, not diversification of it.**
5. **Deliberately over-weight EM** relative to its ~12% cap-weight, as the explicit bet on the growth/GDP gap the index does not yet price.
6. **X-ray for overlap before finalizing.** Nominal diversification ≠ real diversification.
7. **Size every sleeve to survive a decade of under-performance**, because the whole rationale assumes you are still holding it when its regime returns.

---

## References

**Foundational factor literature**

- Fama, E. F., & French, K. R. (1992). "The Cross-Section of Expected Stock Returns." *Journal of Finance*, 47(2), 427–465.
- Fama, E. F., & French, K. R. (1993). "Common Risk Factors in the Returns on Stocks and Bonds." *Journal of Financial Economics*, 33(1), 3–56.
- Fama, E. F., & French, K. R. (2012). "Size, Value, and Momentum in International Stock Returns." *Journal of Financial Economics*, 105(3), 457–472. *(International breadth; Japan momentum weakness.)*
- Jegadeesh, N., & Titman, S. (1993). "Returns to Buying Winners and Selling Losers: Implications for Stock Market Efficiency." *Journal of Finance*, 48(1), 65–91. *(Momentum.)*
- Novy-Marx, R. (2013). "The Other Side of Value: The Gross Profitability Premium." *Journal of Financial Economics*, 108(1), 1–28. *(Quality/profitability; complementarity with value.)*

**Factor interaction, quality, and correlation structure**

- Asness, C. S., Moskowitz, T. J., & Pedersen, L. H. (2013). "Value and Momentum Everywhere." *Journal of Finance*, 68(3), 929–985. *(The central result: universality + value/momentum negative correlation ≈ −0.5 to −0.6.)*
- Asness, C. S., Frazzini, A., & Pedersen, L. H. (2019). "Quality Minus Junk." *Review of Accounting Studies*, 24. *(Multi-dimensional quality factor, international.)*
- Chui, A. C. W., Titman, S., & Wei, K. C. J. (2010). "Individualism and Momentum around the World." *Journal of Finance*, 65(1), 361–392. *(Cross-country momentum; Japan exception.)*

**Limits of factor investing (decay, crowding)**

- McLean, R. D., & Pontiff, J. (2016). "Does Academic Research Destroy Stock Return Predictability?" *Journal of Finance*, 71(1), 5–32. *(Post-publication decay ≈ 58%; rising cross-predictor correlations.)*

**Index / data sources (re-pull before quoting figures — weights drift monthly)**

- MSCI Factor Indexes category page: https://www.msci.com/indexes/category/factor-indexes
- MSCI World Index factsheet: https://www.msci.com/documents/10199/255599/msci-world-index.pdf
- MSCI ACWI Index factsheet / page: https://www.msci.com/indexes/index/892400
- MSCI ACWI Growth Target Index factsheet: https://www.msci.com/documents/10199/255599/msci-acwi-growth-target-index-usd-net.pdf
- justETF — MSCI ACWI overview (country/sector weights): https://www.justetf.com/en/how-to/msci-acwi-etfs.html

---

*Companion documents to create next: (a) an empirical file with realized returns, correlations, and Portfolio Visualizer backtests using available factor-ETF proxies (2013–present covers one full cycle: 2018, 2020, 2022, and the current AI-concentration phase); (b) an implementation file covering specific UCITS vehicles, TERs, and the Spanish `traspaso` (fund-transfer) tax treatment for rebalancing via redirected contributions rather than sales.*
