# Kelly, Malamud, Pourmohammadi & Trojani — "Universal Portfolio Shrinkage" (SSRN 4660670, 2023+)

*The covariance-shrinkage frontier beyond our Ledoit-Wolf 2004 workhorse.*

## The idea

Ledoit-Wolf (2004, our `shrinkage.py`) shrinks LINEARLY toward one target: Σ̂ = δF + (1−δ)S
— every eigenvalue pulled with the same intensity. The nonlinear-shrinkage literature
(Ledoit-Wolf's own 2017+ QuEST/analytical work, and this paper's "universal" formulation)
shrinks **each eigenvalue by its own optimal amount**, in closed form — small (noise-driven)
eigenvalues get pulled hard, large (signal) ones barely. Kelly et al. frame a shrinkage
family that is provably near-optimal across environments ("universal") and cheap to compute.

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
