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
[literature/state-of-the-art-in-plain-words.md](literature/state-of-the-art-in-plain-words.md).
Each entry below also has an implementation-grade deep dive in [literature/](literature/) — the
principles AND the mathematics (formulas, algorithms, pitfalls, unit tests), written to be
codeable without fetching the paper:

| Deep dive | Covers |
|---|---|
| [mean-variance-and-estimation-error.md](literature/mean-variance-and-estimation-error.md) | Markowitz math · Michaud error-maximization mechanics · Chopra-Ziemba 11× · DeMiguel evidence · resampled efficiency |
| [ledoit-wolf-shrinkage.md](literature/ledoit-wolf-shrinkage.md) | both shrinkage estimators, closed-form, numpy-ready |
| [black-litterman.md](literature/black-litterman.md) | full posterior math + our prior/regime-views adaptation |
| [risk-parity-erc.md](literature/risk-parity-erc.md) | Euler risk contributions, ERC existence/computation, leverage-aversion caveat |
| [hierarchical-risk-parity.md](literature/hierarchical-risk-parity.md) | exact 3-stage HRP algorithm, pitfalls, unit tests |
| [cvar-optimization.md](literature/cvar-optimization.md) | Rockafellar-Uryasev LP formulation, when to un-park it |
| [regime-switching.md](literature/regime-switching.md) | Hamilton filter math, Ang-Bekaert findings, maximin reformulation, ToS boundary |
| [nowcasting-dfm.md](literature/nowcasting-dfm.md) | DFM/Kalman sketch, GDPNow/NY Fed production notes, upgrade path |
| [stationary-bootstrap.md](literature/stationary-bootstrap.md) | Politis-Romano ↔ our scenario engine, exact correspondence |
| [factor-canon.md](literature/factor-canon.md) | FF3/momentum/VME/QMJ math + per-quadrant predictions vs our measurements |

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

### Rockafellar & Uryasev (2000), "Optimization of Conditional Value-at-Risk" — *Journal of Risk* ([pdf](https://uryasev.ams.stonybrook.edu/wp-content/uploads/2011/11/kro_CVaR.pdf))
Made **tail risk optimizable**: CVaR (expected loss beyond the α-quantile) is coherent, and
minimizing it reduces to a *linear program*. Regulatory endorsement: Basel's FRTB (2016) moved
market-risk capital from VaR to Expected Shortfall (= CVaR, 97.5%).
**⇒ for us: later, optional.** Our Tier-2 risk-metric choice (vol ↔ maxDD) can add CVaR-95 as a
third option; monthly data (330 obs ⇒ ~17 tail months at 95%) makes it noisy, so it's an option,
not the default.

---

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
