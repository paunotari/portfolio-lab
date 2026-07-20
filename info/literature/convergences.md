# Convergences — independent literature that confirms each of our measured claims

*The paper's validation ammunition, consolidated (2026-07). Each row: a ledger claim of
ours ↔ the INDEPENDENT work that arrives at the same place ↔ what exactly converges. The
scattered "⇒ for us" verdicts live in the frontier/classics notes; this file is the one
place the draft's related-work and discussion sections mine. Rule: only list genuine
convergences (same finding, independent route) — positioning-only papers stay in their
notes.*

| Our claim (ledger) | Independent confirmation | What exactly converges |
|---|---|---|
| **M1/M14 — nothing beats 1/N significantly at our data scale; the in-sample winner flips OOS** | DeMiguel et al. 2009 (classic) · **Yuan-Zhou 2023** (JFQA) · **Bouyé-Teiletche 2025** (FAJ) · Kelly et al. 2026 (Fig. 1) | Yuan-Zhou DERIVE the 3,000-month break-even we replicate (their eq. 13; τ-haircut eq. 12) and prove 1/N near-optimality in one-factor worlds (our menu: 77% first PC) — our p=0.055 borderline is what their theory predicts at our T. Bouyé-Teiletche's OOS: MVO flips from best in-sample to WORST out-of-sample — our M1 on a 7-asset-class universe. Kelly et al.'s opening figure is the OOS-Sharpe collapse in N/T — our thesis, drawn by an AQR/Yale team. |
| **M2/M25 — structure (HRP/ERC) generalizes; min-variance's win is era-specific; HRP's edge over ERC is real-but-insignificant** | **Antonov, Lipton & López de Prado 2024** (Transactions of ADIA Lab) · CBS master thesis 2021 (corroborating) | ALP derive ANALYTICALLY that HRP's allocation weights carry less covariance-estimation noise than Markowitz's, with closed-form noise expressions — the theory under our 90-year empirical result (HRP/ERC beat 1/N in 100% of window variants while min-var manages 25%). The thesis corroborates empirically across universes with denoising/turnover/significance machinery. |
| **M3/M17 — hard caps IMPROVE out-of-sample results, in every grid cell** | Jagannathan-Ma 2003 (classic) · **Brodie et al. 2009** (PNAS) · DeMiguel-Garlappi-Nogales-Uppal 2009 (Mgmt Sci) · Boyd et al. 2024 | Brodie's winning portfolio IS positivity-constrained variance minimization (their ℓ1 penalty is inert long-only — their own p.6); DGNU generalize norm constraints; Boyd et al. reach "constrain hard, distrust point forecasts" from convex-optimization theory. Same mechanism, four independent routes; ours adds the cost/refit/cap grids and inference. |
| **M7/M14 — the all-weather construction buys a FLOOR, not returns: Sharpe at par with the winner, best drawdown** | **Bouyé-Teiletche 2025** (rg-ERC) · Dalio/All-Weather canon | Their risk-parity-ACROSS-regimes portfolio (explicitly "All Weather philosophy") lands exactly our flagship's OOS profile: at-par Sharpe, lowest maxDD/worst-month, best Calmar — on a different universe (7 Bloomberg asset-class indices), different regime definitions, different construction. Independent replication of the project's central product claim. |
| **M19 — regime results carry no look-ahead subsidy; real-time labels work** | **Bouyé-Teiletche 2025** (OOS protocol) | They independently implement our real-time discipline: inflation lagged ~2 months, NBER replaced by the real-time Sahm rule (official dating lags 4-21 months). Two teams converging on the same publication-lag protocol strengthens both. |
| **M21 — the "winner" decomposes into a Quality exposure (min-variance = 82% Quality)** | **Frazzini-Kabiller-Pedersen "Buffett's Alpha"** (FAJ 2018) · low-vol canon (Clarke et al.; Frazzini-Pedersen BAB) · Kelly et al. 2026 (UPSA tilts) | Buffett's 0.79 Sharpe = BAB+QMJ levered 1.7× — the same "skill is exposure wearing a name" decomposition at the opposite end of fame. UPSA's data-driven spectral tilts load on quality/value/low-risk and away from momentum — the machine rediscovers the same premia our attribution found. |
| **M18 — the equity menu is ~2.8 effective bets; factor spread beats asset-class count; the marginal diversifier is an asset class** | **Ilmanen-Kizer 2012** (JPM, award) · Choueifaty-Coignard 2008 (DR²) · Yuan-Zhou Prop 3 | Ilmanen-Kizer: factor-constituent correlations ≈0 vs ≈0.4 across asset classes — why our region×factor equity menu collapses to ~3 bets and why the factor/asset-class axes diversify. Choueifaty's DR² is the practitioner metric of the same quantity. Yuan-Zhou's one-factor optimality explains why MORE equity sleeves cannot help. |
| **M6/B1b — the stagflation floor is bought by assets, not weights; gold alone carries it today; energy-commodities are the missing second carrier** | **Bouyé-Teiletche 2025** (Tables 2/4) | Their per-regime evidence: gold's best regime is stagflation, commodities-ex-gold's is overheating, their optimal stagflation portfolio is TIPS+gold, and volatilities rise ~50% in bad-growth regimes. Our M6 floor mechanics and the B1b priority, measured by an independent team. (Bonus: their Swinkels-SPF TIPS backfill is the route that un-blocks our TIPS sleeve.) |
| **M9/M12 — trailing returns point backwards; exposure impersonates skill; tactical overlays fail net of costs at our scale** | Asness 2017 (factor-timing verdict) · our Faber/Antonacci reads | Antonacci's verified lift comes from the absolute filter sidestepping 2001-02/2008 with NO cost deduction and NO inference — consistent with our finding that overlays' paper edges do not survive the full checklist; the fair test (two-bear virgin universe) is queued. |

## How the paper uses this

- **Related work**: one paragraph per row's right-hand column, citing the convergence
  explicitly ("independently, Bouyé & Teiletche (2025) arrive at…").
- **Discussion**: the M7↔rg-ERC and M19↔Sahm-protocol convergences are the strongest
  external validations we have — independent teams, different data, same conclusions.
- **Contrasts stay honest**: the k-means TAA paper finds regime information improves
  RETURNS while ours buys a FLOOR (different objectives — stated, not hidden); Yuan-Zhou
  beat 1/N under conditions (T≥360, small N) our setting does not meet — their theory
  predicts our humility result rather than contradicting it.
