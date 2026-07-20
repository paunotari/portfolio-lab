# Yuan & Zhou (2023) — "Why Naive 1/N Diversification Is Not So Naive, and How to Beat It?"

*JFQA 2023 (SSRN 4281138, Ming Yuan & Guofu Zhou). THE paper our draft must engage with —
the direct descendant of DeMiguel et al. (2009) attacking our central humility claim.*

## What they show

1. **Why 1/N is hard to beat, formalized.** They prove that in high-dimensional settings the
   1/N rule is a *minimax-optimal-flavored* choice: without strong prior information, the
   estimation error of any sample-based rule grows fast enough with N/T that naive equal
   weighting is nearly unimprovable — DeMiguel's empirical finding given theoretical teeth.
   (This STRENGTHENS our Section 5.1: our p=0.055 borderline is what their theory predicts
   at our T.)
2. **And how to beat it anyway:** an optimal COMBINATION of 1/N with sample-based rules
   (the Kan-Zhou 2007 three-fund / Tu-Zhou 2011 combination lineage): w = δ·w_sample +
   (1−δ)·w_1/N with δ estimated to trade estimation error against optimality loss. The
   combination — not the optimizer alone — beats 1/N out of sample in their tests.

## The lineage to cite alongside

- Kan & Zhou (2007), "Optimal Portfolio Choice with Parameter Uncertainty" (*JFQA*) — the
  three-fund rule (riskless + tangency + GMV) under estimation risk.
- Tu & Zhou (2011), "Markowitz meets Talmud" (*JFE*) — combining 1/N with sophisticated
  rules; the direct ancestor of Yuan-Zhou.

## ⇒ for us — the required response (recorded as a paper-track follow-up)

- **This is weight-space shrinkage with 1/N as the target** — it slots exactly into our
  "shrink in all three places" framing (Σ: Ledoit-Wolf · μ: our estimator · w: caps/BL).
  Position it as such: our caps and BL-anchor already shrink weights, but toward
  structure (ERC), not toward 1/N.
- **The test we owe the referee:** implement the Tu-Zhou/Yuan-Zhou-style combination
  (sample tangency or GMV combined with 1/N, δ from their plug-in formula) as a
  walk-forward CONTESTANT on our menu, same protocol, LW p-value vs 1/N. Two honest
  possible outcomes: it beats 1/N significantly at our T (their claim transfers → our
  humility claim gets a stated exception and cites them), or it doesn't (their result
  needs more T / different menus → our claim holds with the strongest challenger fielded).
  Either outcome improves the paper.
- Note the design difference: their δ is estimated from the SAME sample (within-sample
  shrinkage); our estimator's intensity is months-of-evidence across ERAS with an
  agreement gate. Complementary, not competing, mechanisms.

**Where to read:** [SSRN 4281138](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4281138)
(paywalled PDF; JFQA published version via library). Coverage:
[Alpha Architect summary](https://alphaarchitect.com/naive-diversification/).
