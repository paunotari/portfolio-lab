# Gelmini & Uberti (2024) — "The equally weighted portfolio still remains a challenging benchmark"

*International Economics 179, 100525. DOI [10.1016/j.inteco.2024.100525](https://doi.org/10.1016/j.inteco.2024.100525).
Owner-supplied link 2026-07-22.*

> **SOURCING CAVEAT, stated up front.** ScienceDirect served a CAPTCHA and the Milano-Bicocca
> repository copy is behind a bot check, so this note is built from the **abstract, the RePEc
> metadata record and search summaries — not the full text.** Everything below marked ⚠ is
> INFERRED and must be verified against the PDF before any of it enters the paper. The owner may
> have institutional access; recorded as a TODO.

## 1. What it is

**A declared replication study of DeMiguel, Garlappi & Uppal (2009)** — the paper our entire
humility result replicates — rerun on the *same* datasets extended by **twenty more years**
(DeMiguel's sample stopped in 2004; this one runs to ~2024, so it contains the GFC and the
pandemic shock, neither of which the original could see).

Protocol, as far as the abstract states it:
- Mean-variance framework, same strategy set as the original.
- Metrics: **Sharpe ratio, certainty equivalent (CEQ), turnover**.
- **Proportional transaction costs** charged.
- **Rolling estimation windows of limited length**, and — the extension we care about — they vary
  BOTH the **holding period** and the **estimation-window length** to ask whether either can
  rescue the optimizers.
- **They add the ERC portfolio** to the comparison set, motivated as "strictly related to the
  mean-variance approach when variance is the risk measure".

## 2. Their verdict

**1/N still is not systematically beaten.** Two refinements worth quoting precisely:

- **More strategies beat it than in 2009 — because volatility rose**, not because the methods got
  better. (That is a genuinely useful mechanism sentence: higher dispersion widens the gap the
  optimizers can exploit, which is the flip side of our own DR²=1.31 finding — on a menu with no
  dispersion there is nothing to exploit.)
- **Neither route out works.** Limiting the impact of transaction costs by holding a *stable*
  allocation like ERC, nor tuning the estimation window / holding period, is sufficient to beat
  naive diversification **systematically**.

27 references; 4 citing works as of mid-2026.

## 3. ⇒ for us — the most important citation added to this project in months

**(a) It de-risks the single biggest reviewer objection to our headline.** Our humility result is
currently anchored on a 2009 paper. A referee can reasonably ask "is this just a stale finding on
a pre-GFC sample?" Gelmini-Uberti answers it in print, in 2024, on the original datasets plus two
decades including both crises. Our Section 5.1 goes from "replicates DeMiguel (2009)" to
"consistent with the most recent published replication of DeMiguel (2009), on different data".

**(b) Their ERC finding independently reproduces ours.** They field ERC and find that its stability
(low turnover, hence low cost drag) is *not* enough to beat 1/N. Our numbers: ERC turnover **0.4%
per refit** — the lowest of any active rule in our table — and Δ vs 1/N **+0.018 annualized Sharpe
at p_boot 0.191** (M14/M25). Same rule, different data, same verdict. That is exactly the kind of
independent corroboration the ledger's `OOS modern` claims want.

**(c) Their window/holding-period grid reproduces our sensitivity plateau.** They vary estimation
window and holding period; we vary refit cadence (6/12/24m), window start (A2's four variants) and
now the covariance estimator (M33). Neither study finds a cell that flips the verdict.

**(d) ⚠ Where we go beyond them — the positioning claim, PENDING VERIFICATION.** The abstract and
metadata describe Sharpe / CEQ / turnover point estimates; **no Sharpe-difference significance
test is mentioned**. If the full text confirms that, then our contribution over the *most recent*
replication is the same one we claim over Brodie (2009): **we attach a p-value to every ranking
sentence** (Ledoit-Wolf 2008 studentized block bootstrap, deflated Sharpe, PBO, and now the
Demšar/Nemenyi joint test — M31). That is a much stronger positioning sentence than "we go beyond
a 2009 paper". **But it must not be written until someone reads their Section 4.** If they DO test
significance, the honest framing changes to "concurs with, and we extend to a
regime-conditioned/retail-investable setting".

**(e) Complementary data, not overlapping.** They use the DeMiguel academic datasets (industry /
international / factor portfolios). Ours is a retail-investable MSCI index menu plus non-equity
proxies. Two different opportunity sets, same verdict — which is worth one sentence, because our
M27/M34 measurements say the opportunity set is where the action is.

## 4. What to do with it

- [ ] Get the full text (owner institutional access) and **verify (d)** before it enters the draft.
- [ ] Mine the 27 references for anything the frontier shelf is missing.
- [ ] Check whether their "volatility rose ⇒ more strategies beat 1/N" claim is quantified; if it
      is, it is a testable prediction on OUR data (our OOS window 2009-2026 vs the 1998-2008
      warmup) and a cheap, referee-pleasing extra.

**Lineage:** DeMiguel-Garlappi-Uppal (2009) is the parent; Yuan-Zhou (2023,
[beating-1N-yuan-zhou.md](beating-1N-yuan-zhou.md)) is the *theoretical* update to the same
question, this is the *empirical* one. Cite the pair together.
