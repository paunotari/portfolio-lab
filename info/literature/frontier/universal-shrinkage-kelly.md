# Kelly, Malamud, Pourmohammadi & Trojani — "Universal Portfolio Shrinkage" (SSRN 4660670, 2023+)

*The covariance-shrinkage frontier beyond our Ledoit-Wolf 2004 workhorse. READ (intro/
method/results sections) 2026-07, owner-supplied PDF (April 2026 version; Kelly is
AQR/Yale).*

## The idea (verified)

Ledoit-Wolf (2004, our `shrinkage.py`) shrinks LINEARLY toward one target — every
eigenvalue pulled with the same intensity. UPSA ("universal portfolio shrinkage
approximator") learns a NONLINEAR reweighting of principal components π_i = f(λ̄_i)·R̄_i,
implemented in closed form as **a linear combination of ridge portfolios with different
penalty levels** — "diversifying across beliefs" about estimation error (their Bayesian
reading), with optional shape constraints (positivity/monotonicity). Built for the
HIGH-dimensional regime (their lab: 153 anomaly factors, N up to and beyond T); gains vs
ridge/LW-2017 significant (α t-stat 3.72). Two details that resonate with our ledger:
their Figure 1 is our thesis drawn (OOS Sharpe collapsing as c=N/T grows), and UPSA's
spectral tilts load systematically on **quality, value and low-risk** and away from
momentum/seasonality — the same exposures our M21 attribution found behind min-variance.

## ⇒ for us — a robustness column, not a redesign

- Our δ* (constant-correlation LW) is reported as an input-quality diagnostic and feeds
  every risk computation. The referee-grade check: re-run the walk-forward with a nonlinear
  shrinkage Σ (or at minimum LW's analytical nonlinear variant) and confirm the rankings
  don't move — the natural extra column for the M17 sensitivity grid ("Σ estimator" as a
  4th grid dimension: sample / LW-const-corr (shipped) / LW-identity / nonlinear).
- Expectation, stated in advance: with N=28 ≪ T=330 the sample matrix is not desperately
  ill-conditioned and our measured δ* is modest — nonlinear shrinkage's big wins are in
  N≈T or N≫T regimes, so we expect (and would report) "no material change," which
  *supports* the retail-scale framing rather than undermining it.
- Do NOT swap the default without the grid evidence: LW-2004's two-line closed form and
  interpretable δ* are part of the project's transparency contract.

[SSRN 4660670](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4660670) · companion
context: Ledoit & Wolf 2017, "Nonlinear Shrinkage of the Covariance Matrix for Portfolio
Selection" (*RFS*).
