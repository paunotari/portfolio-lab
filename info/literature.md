# Literature — the canon behind what we're building

**Selection bar:** only work that changed practice — papers that created or killed a method, and
methods actually run in production (Goldman, Bridgewater, AQR, central banks, Basel). No paper
soup. Each entry ends with a **⇒ for us** verdict: adopt / adapt / benchmark-against / stays
Phase 4, judged under the house constraints (KISS, transparency, FRED ToS line in
`CLAUDE.md` caveat #11).

Why this doc exists: the mechanics we use are trivial statistics, but two areas — **portfolio
optimization** and **regime forecasting** — have deep production literatures where the naive
version is a *known* failure mode. This is the map so the optimizer
([portfolio_optimization.md](portfolio_optimization.md)) is built on what works.

**This file is the index + verdicts.** For the whole literature as one plain-language story (no
formulas — read this first for comprehensive understanding), see
[literature/classics/STATE-OF-THE-ART-IN-PLAIN-WORDS.md](literature/classics/STATE-OF-THE-ART-IN-PLAIN-WORDS.md).
The deep dives live on two shelves (reorganized 2026-07):
**[literature/classics/](literature/classics/)** — the established canon this project is
built on, implementation-grade (formulas, algorithms, pitfalls, unit tests), codeable
without fetching the paper. **[literature/frontier/](literature/frontier/)** — the LIVING
frontier: working papers and active groups solving our problem now (2023+), each analyzed
with a "⇒ for us" verdict (position against it / borrow a technique / field it as a
contestant). Frontier notes are positioning + candidate tests, not settled canon; anything
promoted from frontier to a design change needs the M16-style pre-registered checklist.
**[convergences.md](literature/convergences.md)** maps each measured ledger claim to the
independent literature that confirms it — the paper's related-work/discussion ammunition,
consolidated.

### Classics — the canon

| Deep dive | Covers |
|---|---|
| [mean-variance-and-estimation-error.md](literature/classics/mean-variance-and-estimation-error.md) | Markowitz math · Michaud error-maximization mechanics · Chopra-Ziemba 11× · DeMiguel evidence · resampled efficiency · **§6 a pedagogical walkthrough fact-checked (owner link)**: the Monte-Carlo bullet cloud as a figure idea + why binning it breaks past N≈10 (measured: 68% return coverage at N=28), their own GMV-vs-tangency table as a ready-made error-maximization illustration, and two defects flagged |
| [ledoit-wolf-shrinkage.md](literature/classics/ledoit-wolf-shrinkage.md) | both shrinkage estimators, closed-form, numpy-ready |
| [black-litterman.md](literature/classics/black-litterman.md) | full posterior math + our prior/regime-views adaptation |
| [risk-parity-erc.md](literature/classics/risk-parity-erc.md) | Euler risk contributions, ERC existence/computation, leverage-aversion caveat |
| [hierarchical-risk-parity.md](literature/classics/hierarchical-risk-parity.md) | exact 3-stage HRP algorithm, pitfalls, unit tests |
| [cvar-optimization.md](literature/classics/cvar-optimization.md) | Rockafellar-Uryasev LP formulation, when to un-park it |
| [regime-switching.md](literature/classics/regime-switching.md) | Hamilton filter math, Ang-Bekaert findings, maximin reformulation, ToS boundary |
| [nowcasting-dfm.md](literature/classics/nowcasting-dfm.md) | DFM/Kalman sketch, GDPNow/NY Fed production notes, upgrade path |
| [stationary-bootstrap.md](literature/classics/stationary-bootstrap.md) | Politis-Romano ↔ our scenario engine, exact correspondence |
| [low-volatility-anomaly.md](literature/classics/low-volatility-anomaly.md) | Haugen-Baker → Clarke-de Silva-Thorley → Blitz-van Vliet · BAB mechanism · why min-var wins our walk-forward |
| [factor-canon.md](literature/classics/factor-canon.md) | FF3/momentum/VME/QMJ math + per-quadrant predictions vs our measurements |
| [sharpe-inference.md](literature/classics/sharpe-inference.md) | JK/Memmel baseline · Ledoit-Wolf 2008 HAC + studentized circular block bootstrap · deflated Sharpe (Bailey-LdP) · CSCV PBO · our pairwise protocol + pitfalls |
| [rebalancing.md](literature/classics/rebalancing.md) | frequency/bands · diversification return (Booth-Fama, Willenbrock) · our M22 measurement: constant-mix vs buy-and-hold is not load-bearing |
| [currency-hedging.md](literature/classics/currency-hedging.md) | Campbell-Serfaty-Viceira 2010 (safe-haven currencies = embedded hedges; hedge bonds, not necessarily equity) · our M24 unhedged-EUR re-statement · the hedged-half implementation sketch |
| [factor-timing.md](literature/classics/factor-timing.md) | the Asness-Arnott valuation-spread debate · why no factor timing enters the optimizer · the M9/M12 tie-in |

### Frontier — the living papers (2023+, added 2026-07)

| Frontier note | Covers | Action it motivates |
|---|---|---|
| [gelmini-uberti-replication.md](literature/frontier/gelmini-uberti-replication.md) | **Gelmini-Uberti 2024 (*International Economics*): the declared REPLICATION of DeMiguel 2009 with +20 years of data incl. GFC and COVID, ERC added, window/holding-period grid** — 1/N still not systematically beaten; more strategies beat it only because volatility rose | de-risks "is your humility result stale?"; their ERC verdict independently reproduces our M14/M25; ⚠ full text not yet read (CAPTCHA) — verify the "no significance test" claim before using it to position the paper |
| [beating-1N-yuan-zhou.md](literature/frontier/beating-1N-yuan-zhou.md) | Yuan-Zhou JFQA 2023 (+ Kan-Zhou/Tu-Zhou lineage): why 1/N is near-unimprovable in theory — and the 1/N-combination rule that beats it | **the required referee response**: field their combination as a walk-forward contestant |
| [regime-allocation-groups.md](literature/frontier/regime-allocation-groups.md) | Bouyé-Teiletche 2024 (regime SAA, our nearest institutional sibling) · k-means TAA w/ FRED-MD (QF 2026) · Shu et al. per-asset regimes · Chan et al. ML-conditional optimization | positioning anchors + 2 cheap borrowed tests: random-regime placebo, Nemenyi multiple-comparison |
| [practitioner-tactical-rules.md](literature/frontier/practitioner-tactical-rules.md) | the perennial SSRN download podium: Faber 10-month-SMA GTAA · Antonacci dual momentum · Buffett's Alpha (=BAB+QMJ levered) | trend-filter overlay as the missing contestant family; Buffett's Alpha ↔ our M21 (min-var = 82% Quality) |
| [universal-shrinkage-kelly.md](literature/frontier/universal-shrinkage-kelly.md) | Kelly-Malamud-Pourmohammadi-Trojani nonlinear/universal covariance shrinkage | Σ-estimator as a 4th sensitivity-grid dimension (expect "no material change" at N≪T — and say so) |
| [asset-selection-menu-design.md](literature/frontier/asset-selection-menu-design.md) | **the other leg — SELECTION, not weights**: Ilmanen-Kizer (factor > asset-class diversification, corr ~0 vs ~0.4) · Choueifaty diversification ratio (DR² = independent bets) · Brodie sparse/lasso Markowitz · how-many-assets classics · trend/managed futures as the crisis diversifier | adopt **DR² as a standing menu/portfolio metric** (3 lines); the paper's menu-design principles now cite literature, not taste |
| [markowitz-at-seventy-boyd.md](literature/frontier/markowitz-at-seventy-boyd.md) | Boyd-Johansson-Kahn-Schiele-Schmelzer 2024: the engineering-grade modern MVO (costs, limits, return-uncertainty penalties, open-source) | the perfect foil for the retail-data-scale framing + the recorded upgrade path if the product ever has institutional inputs |
| [hrp-extensions.md](literature/frontier/hrp-extensions.md) | Antonov-Lipton-López de Prado 2024 (HRP's noise advantage PROVEN analytically — the theory under M2) · Raffinot's HERC (Ward + gap index + dendrogram splits + ERC) · CBS-thesis corroboration | cite ALP next to M2/M25; HERC recorded as candidate contestant ("both sides of M25 in one rule") |

---

## 1. Portfolio construction — the estimation-error war

The whole modern literature is one long argument about a single fact: **optimizers amplify input
error**. Read in this order, it's a narrative.

### Markowitz (1952), "Portfolio Selection" — *Journal of Finance*
Where it all starts: diversification quantified, risk = covariance, the efficient frontier.
Nobel Prize 1990. Every later paper is a footnote or a correction to this one.
**⇒ for us:** the *frame* (return/risk/weights on a simplex) is ours too; the naive
*implementation* is what everything below fixes.

### Michaud (1989), "The Markowitz Optimization Enigma: Is 'Optimized' Optimal?" — *FAJ*
Named the disease: mean-variance is an **"estimation-error maximizer"** — it loads maximum weight
exactly where inputs are most wrong (lucky means, understated variances, spurious negative
correlations). Later patented **Resampled Efficiency** ([US 6,003,018](https://patents.google.com/patent/US6003018A/en),
run commercially by [New Frontier Advisors](https://newfrontieradvisors.com/media/rxbld4hq/estimation-error-and-portfolio-optimization-12-05.pdf)):
optimize on many bootstrapped input sets, average the weights.
**⇒ for us:** the diagnosis is the design constraint for §portfolio_optimization.md. The
resampling cure is patented, but our scenario engine already gives us the honest cousin:
*validate* candidate weights across bootstrapped histories rather than trusting one.

### DeMiguel, Garlappi & Uppal (2009), "Optimal Versus Naive Diversification: How Inefficient is the 1/N Portfolio Strategy?" — *Review of Financial Studies* ([paper](https://academic.oup.com/rfs/article-abstract/22/5/1915/1592901))
The humiliation result. Across 7 datasets and **14 optimization models, none consistently beat
equal weight (1/N)** out of sample. Estimated break-even: ~**3,000 months** of data for 25 assets
(~6,000 for 50) before sample-based mean-variance reliably wins.
**⇒ for us — the single most important number in this doc:** we have **330 months × 21 assets**.
Raw MVO on our data *cannot* be expected to beat 1/N. Consequences: (a) **1/N is the mandatory
benchmark** displayed next to every optimizer output; (b) expected *returns* are the least
estimable input — prefer risk/structure objectives and treat return as a constraint or view, not
a free maximand.

### The low-volatility anomaly — Haugen & Baker (1991); Clarke, de Silva & Thorley (2006); Blitz & van Vliet (2007); explained by Frazzini & Pedersen (2014), "Betting Against Beta" — *JFE* ([pdf](https://pages.stern.nyu.edu/~lpederse/papers/BettingAgainstBeta.pdf))
The empirical scandal CAPM never recovered from: **low-risk stocks earn as much as — often more
than — high-risk stocks**, the exact opposite of "more risk, more reward." Haugen & Baker first
documented it (low-vol Wilshire-5000 portfolios matched the market with far less risk); Clarke,
de Silva & Thorley showed **minimum-variance portfolios** of large US stocks deliver market-like
returns at ~25–30% less volatility; Blitz & van Vliet confirmed it globally. Frazzini & Pedersen
supplied the mechanism: most investors can't or won't use leverage, so they overpay for exciting
high-beta assets to reach return targets, leaving boring low-beta assets structurally cheap —
their BAB factor harvests exactly that premium (same leverage-aversion logic as risk parity,
[risk-parity-erc.md](literature/classics/risk-parity-erc.md) §4).
**⇒ for us: the explanation of our own walk-forward result.** Min-variance won BOTH halves of
our out-of-sample test (Sharpe 1.21 in 2009–2017, 0.96 in 2018–2026 — measured 2026-07) without
estimating a single expected return. That's not "better optimization": it's (a) immunity to
mean-estimation error and (b) harvesting this structural premium — on our menu, via the Quality
sleeves it concentrates in. License to consider min-var as the default anchor (open TODO
decision), with the caveat said out loud: a min-var portfolio is a *factor bet on defensive
equity*, not a neutral allocation. → [low-volatility-anomaly.md](literature/classics/low-volatility-anomaly.md)

### Ledoit & Wolf (2004), "Honey, I Shrunk the Sample Covariance Matrix" — *JPM* ([pdf](http://www.ledoit.net/honey.pdf))
Opening line of the abstract, literally: *"nobody should be using the sample covariance matrix
for portfolio optimization."* Shrink it toward a structured target (constant-correlation);
optimal shrinkage intensity has a closed form. Now the default in production quant stacks (it's
`sklearn.covariance.LedoitWolf`).
**⇒ for us: adopt.** ~30 lines of numpy, no new dependency, closed-form, transparent. Any
covariance our optimizer consumes should be shrunk. (Means are the bigger problem, but this
fixes the fixable input.)

### Black & Litterman (1992), "Global Portfolio Optimization" — *FAJ* (developed at [Goldman Sachs, 1990](https://www.goldmansachs.com/our-firm/history/moments/1990-black-litterman-model); intuition in [He & Litterman 1999](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=334304))
Fixes MVO's garbage-in problem from the other end: **start from an equilibrium prior** (what the
market already holds) and **blend user views in Bayesianly**, weighted by stated confidence. No
view ⇒ you hold the market; strong view ⇒ you tilt, proportionally. In production for 30+ years
(Goldman publishes allocations from it; sovereign funds and endowments anchor SAA with it).
**⇒ for us: adapt the *pattern*, not the machinery.** Prior = a neutral allocation (1/N or
risk-parity weights over our sleeves — there's no market-cap equilibrium for an index menu);
views = the user's sliders and, notably, **our per-quadrant regime expectations** with the Markov
outlook as the confidence weight. This is the principled way to let the macro module *tilt* an
allocation instead of letting historical CAGR dominate it.

### Risk parity — Dalio/Bridgewater "All Weather" (1996, production) + Asness, Frazzini & Pedersen (2012), "Leverage Aversion and Risk Parity" — *FAJ* ([pdf](https://pages.stern.nyu.edu/~afrazzin/pdf/Leverage%20Aversion%20and%20Risk%20Parity%20-%20Asness%20,%20Frazzini%20and%20Pedersen.pdf))
Allocate **risk**, not dollars — sidestep expected returns entirely (they're the unestimable
input). Born in production (Bridgewater's All Weather is explicitly built on the growth/inflation
quadrant logic we use); AQR supplied the academic explanation (leverage aversion ⇒ safe assets
carry a premium the strategy harvests).
**⇒ for us: adopt as a mode.** Equal-risk-contribution weights are computable in a few lines and
make the natural *prior* for the Black-Litterman-style blend above. Also the philosophical
validation of our signature feature: All Weather ≈ "maximin across the 4 quadrants."

### López de Prado (2016), "Building Diversified Portfolios that Outperform Out-of-Sample" — *JPM* ([SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2708678))
**Hierarchical Risk Parity (HRP):** cluster assets by correlation distance, then allocate
top-down through the cluster tree — never inverts the covariance matrix, so estimation error
isn't amplified. Beats CLA/min-var and naive risk parity out of sample in Monte Carlo. Young but
influential (the reference method in the ML-for-finance canon).
**⇒ for us: strong candidate for the default engine.** Perfect KISS fit: deterministic,
explainable ("your money splits where correlations split"), no optimizer pathologies, and the
cluster tree is itself a Tier-2 visualization (it should rediscover our region/factor structure —
a great sanity check). Benchmark HRP vs 1/N vs the slider blend, walk-forward.

### Moreira & Muir (2017), "Volatility-Managed Portfolios" — *Journal of Finance* ([pdf](https://onlinelibrary.wiley.com/doi/10.1111/jofi.12513))
Scale exposure by the **inverse of recent volatility** — lean in when markets are calm, cut risk
when they turn turbulent. Counterintuitive (you reduce risk right after a spike, when expected
returns look highest) yet raised Sharpe and alpha across the market, value, momentum and
profitability factors in their sample. One of the most cited recent results — and one of the most
*contested*: follow-ups (Cederburg et al. 2020; Barroso-Detzel) find the out-of-sample, net-of-cost
benefit is fragile and uneven across factors. A textbook case for our honest walk-forward to
adjudicate rather than assume.
**⇒ for us: tested, and it did NOT win (2026-07).** Added as a walk-forward contestant in the
UNLEVERED form a long-only investor can actually run (`portfolio/rules.py::vol_managed`: cut
exposure toward a vol target, hold cash, never lever up). Result: it **cut drawdowns materially**
(min-variance's maxDD −29% → −22%, vol 14% → 12%) but **did not lift the Sharpe** (1.06 → 0.99) —
the de-risking gives up as much recovery as it saves. Kept as a defensive option to expose in
Tier-2 (maxDD-focused users), not as a performance claim. The contested literature was right to
be cautious; our data agrees.

### Rockafellar & Uryasev (2000), "Optimization of Conditional Value-at-Risk" — *Journal of Risk* ([pdf](https://uryasev.ams.stonybrook.edu/wp-content/uploads/2011/11/kro_CVaR.pdf))
Made **tail risk optimizable**: CVaR (expected loss beyond the α-quantile) is coherent, and
minimizing it reduces to a *linear program*. Regulatory endorsement: Basel's FRTB (2016) moved
market-risk capital from VaR to Expected Shortfall (= CVaR, 97.5%).
**⇒ for us: later, optional.** Our Tier-2 risk-metric choice (vol ↔ maxDD) can add CVaR-95 as a
third option; monthly data (330 obs ⇒ ~17 tail months at 95%) makes it noisy, so it's an option,
not the default.

---

### Ledoit & Wolf (2008), "Robust performance hypothesis testing with the Sharpe ratio" — *Journal of Empirical Finance* ([pdf](http://www.ledoit.net/jef2008_abstract.htm)); + Bailey & López de Prado (2014), "The Deflated Sharpe Ratio" — *JPM*
The referee-standard answer to "is that Sharpe difference real?": a delta-method HAC standard
error plus a **studentized circular block bootstrap** p-value that stays honest under the heavy
tails and autocorrelation that break the classic Jobson-Korkie z-test. Bailey-LdP add the
**multiplicity** correction: the best of N tried strategies has an inflated Sharpe by
construction; the deflated Sharpe is P(true SR > 0) against the expected maximum of N
zero-skill trials.
**⇒ for us — ADOPTED (2026-07, the paper-track gate):** implemented faithfully in
`portfolio/inference.py` (bootstrap primary, HAC alongside, DSR per contestant) and run on the
walk-forward net OOS returns every build. First verdict (M14): **nothing on the menu beats 1/N
significantly at 5%** — even min-variance's +0.20 annualized Sharpe edge lands at p_boot
0.055 — while two overlays are significantly WORSE than 1/N; every ranking sentence in the
reports now carries its p-value. → [sharpe-inference.md](literature/classics/sharpe-inference.md)

## 2. Regime detection & forecasting — what the grown-ups do

### Hamilton (1989), "A New Approach to the Economic Analysis of Nonstationary Time Series and the Business Cycle" — *Econometrica*
THE regime paper: the economy switches between hidden states following a Markov chain; estimate
states + transition probabilities jointly by maximum likelihood. Thousands of descendants
(overview: [Ang & Timmermann 2011, "Regime Changes and Financial Markets"](https://www.nber.org/system/files/working_papers/w17182/w17182.pdf)).
**⇒ for us:** the *fitted* (EM/ML) version is exactly what our FRED-ToS line reserves for
Phase 4 with non-FRED data. Our counted transition matrix is the honest non-fitted cousin — same
mathematical object (Markov chain), transparent estimation. Keep it; know its lineage.

### Ang & Bekaert (2002 RFS, "International Asset Allocation with Regime Shifts"; 2004 FAJ, "How Do Regimes Affect Asset Allocation?")
The bridge from regimes to *money*: correlations spike in bear regimes (diversification fails
when needed most — our rolling-correlation chart shows exactly this), and regime-aware allocation
adds welfare out of sample. First strong evidence that the regime layer earns its keep in
portfolio choice, not just in description. (Guidolin & Timmermann extended to 4-state models
with size/value portfolios — 4 states is a defensible granularity, comfortingly ours.)
**⇒ for us:** the academic license for the signature feature (regime-targeted allocation). Also a
warning they document: regime benefits concentrate in *avoiding the bad state*, which is why the
maximin mode matters.

### Nowcasting: Giannone, Reichlin & Small (2008, *J. Monetary Economics*) → in production as Atlanta Fed [GDPNow](https://ideas.repec.org/p/fip/fedawp/2014-07.html) (2014) and the [NY Fed Staff Nowcast](https://www.newyorkfed.org/research/policy/nowcast/methodology.html) (2016)
The industrial version of "read the current macro state from many noisy, lagging indicators":
dynamic factor models distill dozens of releases into a real-time activity estimate, updating
with each data release. Lineage: Stock & Watson's diffusion indexes.
**⇒ for us:** our composite z-score IS a poor-man's static factor model — one factor per axis,
equal loadings, no Kalman filter. The upgrade path (proper DFM) is fitted ⇒ Phase 4/non-FRED.
What we can steal today, KISS-compatibly: their *release-calendar discipline* (our ~1–2 month
print lag is exactly what nowcasting exists to shrink — a live-data feed would matter more than
a fancier model, consistent with our own backtests).

### Practitioner quadrant frameworks — Bridgewater's economic machine; Hedgeye/42 Macro "quads"
Not peer-reviewed, but this *is* the production setting for growth×inflation quadrants: entire
firms trade this exact 4-state map, conditioning positioning on which quad is coming (rate of
change of growth and inflation — same accelerating/decelerating definition we use).
**⇒ for us:** validation that the frame is production-real, and a differentiator: they sell the
quad call as proprietary conviction; we ship the transparent, backtested, calibrated version.

### Politis & Romano (1994), "The Stationary Bootstrap" — *JASA*
The statistical license for resampling *dependent* time series: resample in blocks (theirs:
random geometric lengths) to preserve serial correlation that i.i.d. draws destroy.
**⇒ for us: already adopted** — our scenario engine's regime-persistent spells with geometric
durations + within-spell contiguous blocks is a regime-conditioned stationary bootstrap. Good to
know it has a name and asymptotic theory; cite it in the scenario docstring when next touched.

---

## 3. The assets themselves — why factor sleeves exist

The menu we optimize over is factor indices; these four papers are why those products exist:

- **Fama & French (1993)**, "Common Risk Factors in the Returns on Stocks and Bonds" — *JFE*.
  The 3-factor model; killed CAPM-only thinking; value (HML) becomes an investable dimension.
- **Jegadeesh & Titman (1993)**, "Returns to Buying Winners and Selling Losers" — *JF*. Momentum:
  the strongest, most replicated anomaly; the reason "MSCI Momentum" exists.
- **Asness, Moskowitz & Pedersen (2013)**, "Value and Momentum Everywhere" — *JF*. Value and
  momentum premia exist in *every* asset class and are **negatively correlated** — the academic
  core of our factor-diversification thesis (see
  [factor-diversification-thesis.md](factor-diversification-thesis.md)).
- **Asness, Frazzini & Pedersen (2019)**, "Quality Minus Junk" — *Rev. of Accounting Studies*.
  Quality: profitable, stable, well-run firms earn a premium; defensive behavior in stress — why
  Quality is the sleeve that shines in our Deflationary-bust months.

**⇒ for us:** per-regime factor behavior we measured (Value in busts, Momentum in
Goldilocks/Reflation, Momentum's 2022-style rate-shock fragility) matches this literature —
our `macro_state_factor_attribution.csv` is a small replication, which raises confidence it's
signal, not artifact.

---

## 4. Synthesis — what the optimizer must therefore be

The literature, compressed into build directives for
[portfolio_optimization.md](portfolio_optimization.md):

1. **1/N is the benchmark, always visible** (DeMiguel). If our recommendation can't beat equal
   weight out of sample, say so on screen. With 330 months, expect humility.
2. **Never maximize raw historical means** (Michaud, DeMiguel). Return enters as a *constraint*
   ("≥ X%/yr") or a *view* with confidence — the slider blend must be built so the return slider
   tilts rather than dominates.
3. **Shrink the covariance** (Ledoit-Wolf) before any risk computation. Closed-form, 30 lines.
4. **Structure beats estimation**: HRP and equal-risk-contribution don't invert matrices or
   need mean estimates — make one of them the default engine / the prior (López de Prado; Dalio;
   AFP 2012).
5. **Blend views the Black-Litterman way**: neutral prior (1/N or ERC) + user sliders + regime
   views weighted by the Markov outlook's confidence. Transparent Bayesian tilt, no black box.
6. **Regime-aware is legitimate and is our edge** (Ang-Bekaert), and its chief value is avoiding
   the bad quadrant ⇒ ship the **maximin** mode.
7. **Validate like we forecast**: walk-forward, out-of-sample, against 1/N and min-var — the
   same honesty protocol that already governs the quadrant forecasting.
8. **CVaR later, ML never (here)**: CVaR as an optional Tier-2 tail metric (Rockafellar-Uryasev);
   fitted regime/return models stay Phase 4 with non-FRED data.
9. **No ranking claim without a p-value** (Ledoit-Wolf 2008; Bailey-LdP 2014): every Sharpe
   comparison ships with the block-bootstrap test and the deflated Sharpe; "indistinguishable
   from 1/N" is a reportable result, not a failure.

---

## 5. The syntheses — who has already combined these practices

There is **no single canonical synthesis** of the canon above — every serious shop and author
picks their own trade-offs. The map of who combined what:

**In production (each firm's synthesis is its franchise):**
- **Goldman Sachs** — built around **Black-Litterman** (1990–): equilibrium prior + client views,
  the standard strategic-asset-allocation anchor at sovereign funds and endowments.
- **Bridgewater** — built around **All Weather / risk parity** (1996–): balance risk across the
  growth×inflation quadrants so no regime sinks the portfolio (≈ our maximin, industrialized).
- **AQR** — built around **factor investing + risk parity**: harvest documented premia (value,
  momentum, quality, low-beta/BAB) systematically; supplied much of the academic canon itself
  (Asness, Frazzini, Pedersen, Moskowitz).

**In books (the three best single-volume syntheses):**
- **Ilmanen, *Expected Returns* (2011)** — what every asset class and factor is expected to
  return and *why* (risk premia, behavioral, frictions); the best "what to expect" reference.
- **Ang, *Asset Management: A Systematic Approach to Factor Investing* (2014)** — the whole
  field reorganized around factors ("assets are bundles of factors"); the academic synthesis.
- **López de Prado, *Advances in Financial Machine Learning* (2018)** — the modern
  robust-methods toolbox (HRP, purged cross-validation, backtest-overfitting diagnostics);
  the "how not to fool yourself" reference.

**In software:** PyPortfolioOpt and Riskfolio-Lib implement the individual pieces (shrinkage,
BL, HRP, CVaR, risk parity) but deliberately without an opinion on how to combine them.

**⇒ for us:** our synthesis is [portfolio_optimization.md](portfolio_optimization.md) — the
five-stage unified method. Its deliberate differentiator, which none of the commercial
syntheses has an incentive to offer, is **measured honesty**: 1/N always on screen, a
walk-forward that admits when the clever portfolio loses, and every tilt auditable. The
scoreboard where our blend loses to equal weight isn't a failure of the synthesis — it *is*
the synthesis.
