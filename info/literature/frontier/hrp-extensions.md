# HRP beyond López de Prado 2016 — theory, HERC, and corroboration (owner-supplied links, 2026-07)

*Three additions around our HRP construction (the marginally-better-standalone rule of
M25), from the owner's sweep.*

## 1. Antonov, Lipton & López de Prado (2024) — "Overcoming Markowitz's Instability with HRP: Theoretical Evidence"

*Transactions of ADIA Lab (World Scientific) / SSRN 4748151 / Risk.net. THE missing theory
citation for M2.* They derive **analytical expressions for the noise in allocation weights
induced by covariance estimation** and show HRP's weights are provably less noisy — more
robust — than classical Markowitz's, plus closed-form portfolio-variance comparisons.
López de Prado proposed HRP empirically in 2016; this is him (with Antonov and Lipton)
supplying the theorem eight years later.
**⇒ for us:** cite next to M2/M25 wherever we say "structure generalizes": our 90-year
race measured what ALP prove — the noise channel is exactly the one our walk-forward
punishes. [SSRN 4748151](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4748151) ·
[ADIA Lab](https://www.adialab.ae/research-series/overcoming-markowitzs-instability-with-the-help-of-the-hierarchical-risk-parity)

## 2. Raffinot (2018) — HERC, the Hierarchical Equal Risk Contribution (via Hudson & Thames)

The hybrid of our anchor decision's two protagonists: **cluster hierarchically (Ward
linkage instead of HRP's chain-prone single linkage), choose the number of clusters by the
Gap index (early stopping instead of growing the full dendrogram), split top-down
respecting the dendrogram (instead of HRP's count-based bisection), then equal-risk-
contribution within/across clusters**; supports CVaR/CDaR as the risk measure. Reported
(vendor/blog evidence, not peer-reviewed inference): more diversified, better OOS than
HRP.
**⇒ for us:** the natural CANDIDATE CONTESTANT — literally "ERC with HRP's topology," i.e.
both sides of M25 in one rule. Cheap to implement from our existing pieces (we have the
clustering, the ERC solver and now risk budgets). Recorded in TODO as a frontier
follow-up; enters only through the standard walk-forward + LW p-value, and any promotion
to anchor needs the M16-style discipline. Prior expectation, declared: behaves like
HRP/ERC (statistically indistinguishable), maybe marginally better drawdowns via Ward
clusters. [Hudson & Thames explainer](https://hudsonthames.org/beyond-risk-parity-the-hierarchical-equal-risk-contribution-algorithm/)

## 3. CBS master thesis (Copenhagen Business School) — empirical HRP validation

Multi-universe HRP vs 1/N/ERC/min-var/Markowitz with denoising (random-matrix theory),
linkage comparisons, turnover accounting and significance testing; concludes HRP's OOS
robustness advantage, strongest in stress periods.
**⇒ for us:** corroborating tier (a thesis, not peer-reviewed) — useful as a
"consistent with independent replications" footnote, not a headline citation. Their
linkage-choice comparison is a reminder for the HERC test: linkage IS a hyperparameter,
so any HERC contestant should report single-vs-Ward sensitivity in the same run.
[PDF](https://research-api.cbs.dk/ws/portalfiles/portal/76452070/1332322_Master_Thesis_Hierarchical_Risk_Parity.pdf)
