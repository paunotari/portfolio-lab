# The other leg of the table — asset SELECTION and menu design (not weights)

*Our research adjudicates how to WEIGHT a menu; this note collects the best literature on
how to BUILD the menu — which assets deserve a slot, measured by what they add in return
sources and low covariance. Ties directly to M18 (the 28-sleeve equity menu ≈ 2.8 effective
bets) and the paper's menu-design paragraph.*

## 1. Ilmanen & Kizer (2012), "The Death of Diversification Has Been Greatly Exaggerated" — *JPM* (Bernstein-Fabozzi award)

The selection-side thesis with the best evidence: **diversify across FACTORS, not asset
classes.** Average correlation across factor constituents ≈ **0**, vs ≈ **0.4** for
asset-class-diversified portfolios — so a factor-spanning menu diversifies far more per
slot. Benefits largest long-short but "meaningful in a long-only context" (our case).
**⇒ for us:** the citation that upgrades our menu-design paragraph from taste to
literature: our menu already spans factor premia (Value/Momentum/Quality long-only tilts) +
term premium (Treasuries) + a real asset (gold) — Ilmanen-Kizer is the reason that
STRUCTURE diversifies while 28 equity region sleeves alone do not (M18's 2.8 effective
bets). [AQR PDF](https://www.aqr.com/-/media/AQR/Documents/Journal-Articles/JPM-The-Death-of-Diversification-Greatly-Exaggerated.pdf) ·
[SSRN 2998754](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2998754)

## 2. Choueifaty & Coignard (2008) + Choueifaty-Froidure-Reynier (2013) — the Diversification Ratio

DR(w) = (Σ w_i σ_i) / σ_p — how much volatility "disappears" through imperfect
correlations; **DR² = the number of independent bets** the portfolio actually holds. The
Most Diversified Portfolio (MDP) maximizes DR.
**⇒ for us — a cheap, adoptable METRIC (the actionable item):** we already report
eigenvalue-entropy effective bets (M18) and look-through HHIs; **DR² is the
practitioner-standard companion** and costs three lines (needs only σ and Σ we already
have). Candidate: add DR² per portfolio to the optimizer report scorecards and the menu
line. MDP as a *contestant* is lower priority (another μ-free construction — expect
HRP/ERC-family behavior), but the metric is immediately useful for answering "does adding
sleeve X buy a new bet?". [SSRN 1895459](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1895459)

## 3. Brodie, Daubechies, De Mol, Giannone & Loris (2009), "Sparse and Stable Markowitz Portfolios" — *PNAS* (READ IN FULL 2026-07)

Selection INSIDE the optimizer: an ℓ1 penalty on weights stabilizes the ill-conditioned
Markowitz regression, promotes sparsity, and doubles as a transaction-cost model. **They
claim their sparse portfolios "outperform 1/N significantly and consistently"** (owner
spotted the quote) — the verified specifics behind it:

- Universes FF48 industries / FF100 size×B/M; annual rebuild, 5-year estimation windows,
  target return = trailing 1/N mean; evaluation 1976-2006. FF48 full-period monthly Sharpe
  0.41 vs 1/N's 0.27 — a big point gap.
- **Their own p.6 observation:** under the budget constraint the ℓ1 penalty is exactly a
  short-position penalty, and in the long-only case it is INERT (‖w‖₁≡1) — their FF48
  winner is simply **no-short Markowitz at a target return** (Jagannathan-Ma
  regularization, which they cite), naturally sparse at ~6 of 48 names.
- Through our checklist: "significantly" is used colloquially — **no Sharpe-difference
  test** anywhere (LW 2008 was contemporaneous), and **no transaction costs charged**;
  sub-period tables exist (good) and they honestly flag that dense targets degrade
  ("overfitting").

**⇒ for us:** an ALLY, not a challenge — what wins in their experiment is the same family
as our measured winner (positivity-constrained variance minimization; ours lands p=0.055
net of costs on a far more redundant menu, and decomposes into 82% Quality, M21). The
universe is the other half of the story: 48-100 dispersed industry portfolios leave real
room for variance reduction; our 2.8-effective-bets index menu does not. Paper paragraph:
cite them + DeMiguel-Garlappi-Nogales-Uppal (2009, *Mgmt Sci*, norm-constrained portfolios
— the same-year regularization cousin) as the constrained-min-variance lineage our result
extends WITH inference and costs. Candidate cheap test (TODO): field their exact rule —
long-only min-variance at the trailing-1/N target return (our `optimize()` already supports
hard targets) — as a walk-forward contestant with a LW p-value.
[PNAS](https://www.pnas.org/doi/10.1073/pnas.0904287106) ·
[arXiv 0708.0046](https://arxiv.org/pdf/0708.0046)

## 4. How many assets is "enough" — the classic line

Statman (1987, 30-40 stocks); Campbell-Lettau-Malkiel-Xu (2001, *JF*: idiosyncratic vol
rose — you need ~50). For INDEX menus the question mutates: each sleeve is already
diversified inside, so the binding count is independent RISK SOURCES, not names — our
answer is M18's 2.8 (equity) growing only when a new asset CLASS joins (M6). Cite the
classics to frame why "how many indices" ≠ "how many stocks".

## 5. The missing diversifier the selection literature keeps pointing at: trend/managed futures

Hurst, Ooi & Pedersen, "A Century of Evidence on Trend-Following Investing" (AQR/JPM):
time-series momentum across assets, positive in most decades since 1880 and — the selection
argument — **historically strongest in prolonged equity bears** ("crisis alpha"), i.e. low
covariance exactly when it matters. Moskowitz-Ooi-Pedersen (2012, *JFE*, "Time Series
Momentum") is the academic base.
**⇒ for us:** this is the literature's answer to our own B1b gap (gold alone carries
stagflation). A trend sleeve = mechanically different crisis diversifier; but as a RULE it
must pass our overlay discipline first (Faber note in `practitioner-tactical-rules.md` —
same family; our momentum/vol-target overlays failed net of costs, M1/M14). Selection
verdict: the *asset-class* route (commodities, B1b) stays ahead of the *rule* route in our
queue, and both need the M16-style pre-registration if promoted.

## The menu-design principles, distilled (for the paper)

1. A slot must add an independent RISK SOURCE (measure: DR², eigen-entropy, corr < ~0.6 to
   everything held) — not another wrapper on the same beta (M18).
2. Factor spread beats asset-class count per slot (Ilmanen-Kizer).
3. The marginal diversifier is the one that pays in your WORST regime (M6: bonds/gold
   doubled the stagflation floor; trend/commodities are the next candidates).
4. Selection ends where redundancy begins: past ~0.9 correlation a new sleeve is paperwork
   (S&P500 vs MSCI USA = 0.99).
5. Never select on trailing performance (M9/M12) — select on what the asset DOES
   (its regime profile), not on what it recently DID.
