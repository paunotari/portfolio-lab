# Rebalancing — frequency, bands, the "premium", and what we measured (C1)

The walk-forward assumed monthly constant-mix between annual refits, costing only
refit-date turnover. This note is the targeted literature check (TODO C1) plus our own
measurement (M22) that closes the assumption.

## 1. What the literature says

- **Frequency barely matters; costs do.** Simulation and empirical studies comparing
  monthly/quarterly/annual and band-based rules (e.g. Dichtl, Drobetz & Wambach 2014,
  "Where is the value added of rebalancing?") find risk-adjusted differences between
  reasonable rules are small, and transaction costs dominate the choice. Practitioner
  band rules (rebalance when a weight strays ±20-25% relative — Masters 2003, *JPM*) exist
  to harvest most of the benefit at a fraction of the trading.
- **The "rebalancing premium" / diversification return** (Booth & Fama 1992; Willenbrock
  2011, *FAJ*) is real but modest for correlated sleeves: constant-mix earns roughly half
  the cross-sectional variance not captured by the buy-and-hold drift. For a menu whose
  effective bets ≈ 2.8 (M18), the premium is small by construction; it is largest for
  volatile, low-correlation sleeves (gold vs equities — visible in our M22 numbers as the
  all-weather's sensitivity to the scheme).
- **Buy-and-hold drift is a momentum tilt; constant-mix is a contrarian one.** Which wins
  ex post is era-dependent (drift wins in trends, mix wins in mean-reversion) — another
  reason not to sell either as an edge.

## 2. What we measured (M22 — closes the stated limitation)

Same per-refit weight schedules, three implementations, no re-optimization:
shipped constant-mix (drift trades free) vs constant-mix with every drift trade costed at
10 bps vs within-interval buy-and-hold (no monthly trades, refit turnover from drifted
weights). Result: the free-drift overstatement is **≤ 0.002 Sharpe** (drift turnover
0.5–1.2%/month ⇒ ~0.6–1.4 bps/month), and the buy-and-hold ranking is **identical** — with
the all-weather slightly better under drift (0.933→0.957, the momentum tilt meeting the
2024+ trend). See `portfolio/rebalancing.py`, `REPORT_rebalancing.md`.

**⇒ for us:** the constant-mix assumption is not load-bearing; the uncosted drift is
bounded and immaterial; annual-refit buy-and-hold is the cheapest implementable scheme and
loses nothing. Band-based rebalancing remains an unexplored refinement — worth a line in
the product, not a research priority.
