# The low-volatility anomaly — Haugen-Baker (1991) → Clarke-de Silva-Thorley (2006) → Blitz-van Vliet (2007) → Frazzini-Pedersen (2014)

Deep dive behind [literature.md](../literature.md) §1. Added 2026-07, after our own walk-forward
made the question unavoidable: min-variance won both halves of the out-of-sample test — *why?*
This is the answer: min-var isn't "optimizing better," it's harvesting a documented structural
premium while being immune to the mean-estimation error that poisons everything else.

## 1. The anomaly

CAPM's central promise is a positively sloped risk-return line: more beta, more expected return.
The data says the line is **flat or inverted**. Low-risk stocks earn about as much as — often
more than — high-risk stocks, which means their *risk-adjusted* returns are far higher. This is
arguably the largest and most persistent anomaly in equity markets, and unlike most anomalies it
*strengthened* after publication decades ago.

The evidence chain:

- **Haugen & Baker (1991), "The Efficient Market Inefficiency of Capitalization-Weighted Stock
  Portfolios" — *JPM*.** First systematic documentation: low-volatility portfolios built from the
  Wilshire 5000 (1972–89) matched or beat the cap-weighted market with substantially less risk.
  Ignored for years because it was "impossible."
- **Clarke, de Silva & Thorley (2006), "Minimum-Variance Portfolios in the U.S. Equity Market" —
  *JPM*.** The direct license for our min-var result: long-only minimum-variance portfolios of
  the 1,000 largest US stocks (1968–2005) delivered **market-like returns at ~25–30% lower
  volatility** — i.e., a materially higher Sharpe, from an optimizer that never sees a return
  estimate.
- **Blitz & van Vliet (2007), "The Volatility Effect" — *JPM*.** Global confirmation (US, Europe,
  Japan): the effect is not a US artifact, holds across regions and after controlling for size
  and value. (Van Vliet went on to run Robeco's Conservative Equity funds on exactly this.)
- **Frazzini & Pedersen (2014), "Betting Against Beta" — *JFE*
  ([pdf](https://pages.stern.nyu.edu/~lpederse/papers/BettingAgainstBeta.pdf)).** The theory.
  Their BAB factor (long leveraged low-beta, short high-beta) earns significant premia in every
  major asset class tested — 55,000+ stocks in 24 markets, plus bonds, credit, futures.

## 2. The mechanism — why it exists and persists

- **Leverage constraints (the core, Frazzini-Pedersen).** Investors who want higher returns but
  can't/won't lever must overweight high-beta assets — bidding their prices up and expected
  returns down. Low-beta assets are left structurally cheap for whoever can hold them levered
  (or, unlevered, simply enjoy the better Sharpe). Formally: constrained investors flatten the
  security-market line; the BAB premium compensates the unconstrained.
  **Same mechanism that explains risk parity's historical edge** — see
  [risk-parity-erc.md](risk-parity-erc.md) §4; the two literatures share this engine.
- **Lottery demand / benchmarking (supporting, Baker-Bradley-Wurgler 2011, *FAJ*).** Investors
  overpay for volatile "lottery ticket" stocks; institutional managers benchmarked to an index
  find low-beta stocks career-risky to hold (they lag in rallies) — both depress demand for the
  boring end. Limits to arbitrage keep the mispricing alive.

## 3. Why this matters to OUR stack (the measured connection)

Our walk-forward (2026-07, OOS 2009–2026, `portfolio/validation.py`):

| Contestant | OOS Sharpe 2009–2017 | OOS Sharpe 2018–2026 |
|---|---|---|
| **Min-variance** | **1.21** | **0.96** |
| HRP | 0.90 | 0.86 |
| ERC (anchor) | 0.89 | 0.83 |
| 1/N | 0.86 | 0.81 |

Min-variance won **both** halves — not one lucky window. Two compounding reasons:

1. **Immunity to the 11× input** (Chopra-Ziemba,
   [mean-variance-and-estimation-error.md](mean-variance-and-estimation-error.md)): it consumes
   only the covariance — the estimable input — so it has no return forecast to be wrong about.
2. **This anomaly**: on our menu the low-vol premium expresses itself through the **Quality
   sleeves** (min-var's holdings are ~84% USA + World Quality) — defensive, stable-earnings
   indices are exactly where low-volatility equity lives.

## 4. Caveats — what min-var is NOT

- **It is a factor bet, not a neutral allocation.** A min-var portfolio on our menu is
  concentrated defensive-equity (4 sleeves, mostly Quality, heavily US). Fine — but say it out
  loud; its geographic and factor concentration is exactly what the look-through report exposes.
- **Crowding / valuation risk.** Post-2010 the "low-vol trade" became popular (dedicated ETFs);
  when low-vol stocks themselves get expensive, the forward premium compresses (van Vliet's own
  warning). The anomaly is a long-run structural tilt, not a guarantee per decade.
- **Rate sensitivity.** Defensive low-vol equity behaves partly bond-like; rising-rate shocks
  (2022) hit it — visible in our per-quadrant numbers.
- **Our OOS window overlaps the great USA-Quality decade** (2009–2026). The sub-period split
  mitigates but doesn't eliminate this; re-run the split as history accumulates before crowning
  min-var as default anchor (open TODO decision).

## 5. For our build

- Explains the walk-forward table; cite when presenting it (done in optimizer_viz).
- Keeps min-variance as a serious candidate for **default anchor** (vs ERC) — the decision
  stays evidence-driven via the walk-forward, per the standing TODO item.
- If we ever add explicit factor tilts, "low-beta/defensive" is a documented premium alongside
  value/momentum/quality ([factor-canon.md](factor-canon.md)) — same selection bar.

**Primary sources:** Haugen & Baker, *JPM* 17(3) 1991 · Clarke, de Silva & Thorley, *JPM* 33(1)
2006 · Blitz & van Vliet, *JPM* 34(1) 2007 ·
[Frazzini & Pedersen, *JFE* 111(1) 2014](https://pages.stern.nyu.edu/~lpederse/papers/BettingAgainstBeta.pdf)
· Baker, Bradley & Wurgler, *FAJ* 67(1) 2011.
