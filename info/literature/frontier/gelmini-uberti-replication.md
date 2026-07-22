# Gelmini & Uberti (2024) — "The equally weighted portfolio still remains a challenging benchmark"

*International Economics 179, 100525. DOI [10.1016/j.inteco.2024.100525](https://doi.org/10.1016/j.inteco.2024.100525).
Open access (CC-BY). **FULL TEXT READ 2026-07-22** (owner supplied the PDF). This supersedes the
abstract-only draft; the ⚠ positioning inference in that draft was WRONG and is corrected in §4.*

## 1. What it is

A **declared replication of DeMiguel, Garlappi & Uppal (2009)** — the paper our humility result
replicates — on the *same* datasets extended to mid-2023 (theirs stopped 2004), so it contains
the GFC and COVID and a "generally higher level of price volatility". Two authors, Univ. of
Milano-Bicocca, Dept. of Statistics.

**Datasets (Table 1), all monthly:** S&P sectors (N=11), industry portfolios (N=11),
international country indexes (N=9), MSH = Mkt/SMB/HML (N=3), FF1 = 21 size/BM + market (N=21),
FF4 = 24 size/BM + MKT/SMB/HML/UMD (N=24). Ken French library except S&P and Int.

**Strategies (~17):** 1/N, in-sample MV, Bayes-Stein, Data-and-Model, minimum-variance, VW
(value-weighted/CAPM market), MP (missing-data implied), three-fund (MV-MIN), EW-MIN
(Kan-Zhou mixture of min-var and 1/N), **ERC (added by them, not in the original)**, and the
short-sale-constrained versions (MV-C, BS-C, MIN-C, G-MIN-C, ERC-C).

**Protocol:** rolling window W, holding period H, monthly. Optimal weights from the first W×N
returns, held H months, rolled. **Turnover = |allocation at holding-period end − optimal
allocation at next period start|. Transaction cost = 50 bps × turnover** (exactly DeMiguel; even
1/N carries small turnover because prices drift). Net returns = gross − costs. Metrics: **Sharpe,
certainty-equivalent (CE), turnover**. Four experiments: W=120/H=1 (referring), W=60/H=1,
growing-W/H=1, and W=120/**H=12** (new, per Chan et al. 1999 / Jagannathan-Ma 2003).

## 2. THE FACT THAT CORRECTS OUR NOTE: they DO run a significance test

**Jobson & Korkie (1981)** test for Sharpe-ratio (and Treynor) differences **vs 1/N**, p-values
in brackets under every point estimate in Tables 2–13, with **bold + \*/\*\*/\*\*\*** marking
significant OUT-performance at 10/5/1%. They explicitly "do not differentiate" non-significant
cells from significant UNDER-performance (both left plain) — a conservative display choice.

So the abstract-only guess that they lack inference was **false**. What they actually do:

- **Their headline is a "wins everywhere" claim, not a "never significant" claim.** Verbatim:
  *"there is no bold line in the tables, so there is no investment strategy that significantly
  outperforms the benchmark for each database and performance metric."* I.e. no single strategy
  beats 1/N across **all six datasets and all metrics at once**.
- **But individual-cell significant beats are COMMON.** In the referring experiment (Table 2,
  Sharpe, W=120): MV on FF4 **0.4215\*\*\*** (p 0.001), DM on Ind **0.3368\*\*\*** (0.007), MIN on
  FF1 **0.2993\*\*\***, ERC-C on Ind **0.2312\*\*** / FF1 **0.1963\*\*\*** / FF4 **0.2371\*\***,
  plus many \*. **On dispersed academic datasets, optimization significantly beats 1/N often — it
  just never wins on every dataset simultaneously.**
- **Their ERC finding.** ERC-C is the strategy that *most often* significantly beats 1/N on
  Sharpe (3 cells in the referring run) — but ERC's allocation is *very close to 1/N* because the
  assets are themselves factor portfolios, and as W grows "the performance of the ERC ... does
  not get better while the results of the other strategies seem to generally improve".
- **Growing W helps the optimizers** (Table 8: MV becomes \*\*\* on Ind/FF1/FF4) — longer windows,
  more stable covariance — but still no strategy wins on all datasets. **Longer H (=12) does not
  rescue them** either.
- **Their stated mechanism for WHY optimization sometimes wins**, quoting DeMiguel: *"all else
  equal, the performance of sample-based mean–variance ... would improve relative to that of 1/N
  if the idiosyncratic asset volatility was much higher than 20% ... with higher idiosyncratic
  volatility the covariance matrix is less likely to be singular, and hence easier to invert."*

## 3. Their conclusion

The main DeMiguel result is *qualitatively* confirmed: **1/N remains a challenging benchmark** —
no strategy beats it systematically across datasets/metrics/parameters. More strategies beat it
than in 2009, which they attribute to **higher volatility** in the recent sample. ERC is "very
competitive" but they "cannot conclude that it statistically significantly beats 1/N for all the
metrics and all the databases".

## 4. ⇒ for us — corrected, and BETTER than the abstract-only read suggested

**(a) De-risks "is your result stale?" — HOLDS, unchanged.** A 2024 replication on DeMiguel's own
data + 20 years incl. GFC/COVID reaches our verdict. Section 5.1 cites it next to DeMiguel (2009)
and Yuan-Zhou (2023): the empirical and theoretical 2020s updates of the same finding.

**(b) ⚠ CORRECTION — the positioning is NOT "we add p-values they lack".** They use Jobson-Korkie
(1981). The honest and still-strong positioning is a **test-quality** one: JK 1981 is the
*non-robust* precursor; **Ledoit-Wolf (2008), which we use, is explicitly its HAC + bootstrap
successor, built because JK over-rejects under the fat tails and autocorrelation of monthly
returns.** We add the studentized circular block bootstrap on top. So: *"the most recent
replication tests Sharpe differences with the classical Jobson-Korkie statistic; we use its
heteroskedasticity-and-autocorrelation-robust successor and a block bootstrap, which matters
precisely for the non-normal monthly returns both studies use."* Real, defensible, not inflated.

**(c) THE STRONGER POSITIONING — the multiplicity they eyeball, we quantify.** They run **~17
strategies × 6 datasets × 3 metrics ≈ 300+ JK tests** and adjudicate "no strategy wins
everywhere" by **visually scanning for a bold line that spans all columns**. At 300+ tests and 5%,
~15 false positives are expected by chance, and they duly find significance scattered across
cells. **Our deflated Sharpe (Bailey-LdP), PBO (CSCV) and Friedman-Nemenyi (M31) are exactly the
formal multiplicity machinery this eyeballing lacks.** That is a genuine methodological
contribution over the most recent replication, and M34's "the 17 rows are ~4 strategies" honesty
pass is the same instinct applied to our own table.

**(d) THE BEST ONE — their data CORROBORATES our menu finding (M27/M34), externally.** On their
*dispersed* datasets (industry portfolios; 21-24 FF factor portfolios) optimization
significantly beats 1/N in many cells; and they *explain it by idiosyncratic dispersion* (the
DeMiguel quote in §2). That is our DR² argument in someone else's paper: **optimization wins when
there is dispersion to exploit.** Our retail-investable MSCI menu has almost none (DR²=1.31, mean
pairwise corr 0.885 among long-only factor tilts, M27/M34) — so on our menu nothing beats 1/N,
consistent with their mechanism. **This turns our menu limitation into a positioned finding:
where Gelmini-Uberti find scattered significant wins on high-dispersion academic portfolios, a
one-factor-dominated investable index menu yields none — the opportunity set, not the optimizer,
decides.** This is the bridge from paper 1's menu limitation to paper 2.

**(e) ERC corroboration — PARTIAL, state it precisely.** They: ERC-C most often beats 1/N on
Sharpe but never systematically, and its edge does not grow with W; ERC allocation ≈ 1/N because
their assets are factor portfolios. Us: ERC Δ +0.018 vs 1/N at p 0.191, lowest turnover in the
table, HRP≈ERC at 0.998 corr (M14/M25/M34). Same shape — the best-behaved structural rule, never
a significant systematic winner — on two different opportunity sets.

## 5. Mine-able references (frontier shelf gaps)

Their 27 refs, ones we do NOT already hold: **Kirby & Ostdiek (2012)** "It's all in the timing"
(active rules that beat 1/N — a pro-optimization foil worth reading); **Kritzman, Page &
Turkington (2010)** "In defense of optimization: the fallacy of 1/N" (the direct rebuttal to
DeMiguel — we should read and position against it); **Malladi & Fabozzi (2017)** "Equal-weighted
strategy: why it outperforms" (mechanism for 1/N's edge); **Pflug-Pichler-Wozabal (2012)** "the
1/N strategy is optimal under high model ambiguity" (the ambiguity-aversion justification for
1/N — a theory citation we lack); **Fugazza-Guidolin-Nicodano (2015)** equally-weighted vs
long-run optimal. Kirby-Ostdiek and Kritzman are the two "optimization CAN beat 1/N" papers our
introduction should engage rather than ignore.

## 6. What to do

- [x] Full text read; §4 positioning corrected.
- [ ] **Rewrite the paper's DeMiguel/1-N positioning** around (b)+(c)+(d): test-quality upgrade
      (JK 1981 → LW 2008 + bootstrap), formal multiplicity control (DSR/PBO/Nemenyi vs their
      eyeballed "bold line"), and the dispersion bridge (their high-dispersion datasets win,
      our redundant menu doesn't — same mechanism, opposite outcome).
- [ ] Read Kritzman-Page-Turkington (2010) and Kirby-Ostdiek (2012) — the pro-optimization side
      the intro must engage. Add Pflug-Pichler-Wozabal (2012) as the model-ambiguity theory for
      why 1/N is hard to beat.

**Lineage:** DeMiguel-Garlappi-Uppal (2009) parent; **Gelmini-Uberti (2024) = the empirical 2020s
replication** (this note); Yuan-Zhou (2023, [beating-1N-yuan-zhou.md](beating-1N-yuan-zhou.md)) =
the theoretical 2020s companion. Cite the three as the modern trunk of the 1/N debate.
