# The factor canon — why our sleeves exist and how they should behave

Deep dive behind [literature.md](../literature.md) §3. The four works that created the products
we allocate between, with the math of how factors are defined and what the literature predicts
about their regime behavior (which our `macro_state_factor_attribution.csv` should — and does —
replicate).

## 1. Fama & French (1993), "Common Risk Factors in the Returns on Stocks and Bonds" — *JFE*

The 3-factor model that ended CAPM-only asset pricing:

```
R_i − r_f = α_i + β_i·(R_m − r_f) + s_i·SMB + h_i·HML + ε_i
```

SMB (small minus big) and HML (high book-to-market minus low = **value**) are long-short
portfolios from independent size/value sorts. The result: α's of size- and value-sorted
portfolios collapse to ~0 once these factors are included — size and value are priced,
systematic dimensions of return. This paper is why "factor investing" and therefore MSCI factor
indices exist. (Carhart 1997 added UMD/momentum as the fourth factor; Fama-French 2015 added
profitability RMW and investment CMA — profitability being the academically respectable core of
"quality.")

## 2. Jegadeesh & Titman (1993), "Returns to Buying Winners and Selling Losers" — *JF*

**Momentum**: stocks ranked by past 3–12 month returns continue outperforming for 3–12 months;
~1%/month long-short in their sample. The most replicated anomaly in finance, robust across
markets and decades (with rare, violent "momentum crashes" at sharp reversals — Daniel &
Moskowitz 2016). Standard index construction follows the paper: rank by **12-month return
skipping the most recent month** (the skip avoids 1-month reversal) — MSCI Momentum does a
variant of exactly this. Its known failure mode — sharp regime turns — is precisely what we
measured (Momentum lags in Stagflation, the 2022 rate-shock pattern).

## 3. Asness, Moskowitz & Pedersen (2013), "Value and Momentum Everywhere" — *JF*

Value and momentum premia exist **in every asset class examined** (equities across regions,
bonds, currencies, commodities) — and are **negatively correlated** (long-run co-movement around
−0.5 between their long-short returns in the same market). Combined value+momentum portfolios
have far higher Sharpe than either alone. This paper is the academic core of our
[factor-diversification-thesis.md](../factor-diversification-thesis.md): the reason to hold
Enhanced Value *and* Momentum sleeves simultaneously is not "both are good," it's that their
excess returns hedge each other's regimes.

## 4. Asness, Frazzini & Pedersen (2019), "Quality Minus Junk" — *Review of Accounting Studies*

**Quality** defined as a z-score composite: profitability, growth, and safety (payout in early
versions). Quality stocks earn higher risk-adjusted returns than junk, and QMJ returns are
**defensive** — positive in market drawdowns and flight-to-quality episodes. This is why our USA
Quality / World Quality sleeves exist and why Quality should (and in our attribution, does) hold
up best in Deflationary-bust months.

## 5. What the canon predicts per quadrant — vs what we measured

| Factor | Literature expectation | Our attribution (macro_state_factor_attribution.csv) |
|---|---|---|
| Value | pro-cyclical recovery asset; wins when discount rates/inflation reprice | leads in Deflationary bust (61.5% hit rate) and strong in Reflation ✓ |
| Momentum | trend-continuation; crashes at sharp turns | leads Goldilocks/Reflation; lags Stagflation (−0.1% excess) ✓ — the 2022 pattern |
| Quality | defensive, flight-to-quality | best relative behavior in bust/stress months ✓ |

Independent replication of the canon on our own 28y × 7-region panel is evidence our pipeline
measures signal, not artifact — worth saying in any Tier-1 verdict copy.

## 6. Optimizer-relevant implications

- The **negative value↔momentum excess-return correlation** is the single most exploitable
  structure in our menu — diversification objectives (ERC/HRP) will find and use it via Σ; check
  the HRP dendrogram actually pairs them apart.
- Factor premia are **long-horizon and episodic** — multi-year droughts are normal (value
  2010–2020). The optimizer UI must not present per-regime factor edges as reliable short-term
  bets; they're tilts with decade-scale payoff profiles. Tie every regime tilt to the calibrated
  outlook confidence, never to certainty.

**Primary sources:** Fama & French, *JFE* 33 1993 · Carhart, *JF* 1997 · Jegadeesh & Titman, *JF*
48 1993 · Daniel & Moskowitz, *JFE* 2016 · Asness, Moskowitz & Pedersen, *JF* 68(3) 2013 ·
Asness, Frazzini & Pedersen, *RAS* 24 2019 · Fama & French, *JFE* 2015 (5-factor).
