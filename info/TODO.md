# TODO — task backlog

Actionable backlog for `portfolio_lab`. `vision.md` is the narrative roadmap (why, phases);
this file is the concrete, checkable list derived from it plus ad-hoc engineering tasks. When a
phase in `vision.md` completes, update its status there too — this file doesn't replace it.

Check items off as completed. Add new ones as they come up; keep entries short and specific.

---

## MAIN GOAL — research roadmap: which portfolio distributions are actually optimal (2026-07)

> The owner's framing: this is the project's primary objective. The honest split the whole
> plan rests on: **"optimal" = an empirical part (which construction rules survive
> out-of-sample — the engine tests this) + a preference part (risk profile, equity-only vs
> all-weather, home bias — profiles select this, and the engine MEASURES what each preference
> costs).** The owner's own profile (equity-heavy, factor-diversified even among correlated
> good performers, geographically spread, anti-recency on USA) is already expressible:
> equity-only + factor caps + geo caps + return-tilted sliders.

### Phase A — squeeze what we already have (no new data needed)

- [x] **A1 — 60-year walk-forward on the proxy universe — DONE 2026-07.**
      `portfolio/proxy_backtest.py` (+ 6 FF size×value long-only portfolios ingested,
      `ff_portfolios_monthly.csv`). Two races, same engines and honesty protocol:
      **Equity, OOS 1936→2026 (~90y, 1079 months):** HRP 0.76 > ERC 0.75 ≈ 1/N 0.74 >
      min-variance 0.71 — **min-var's 2009-2026 MSCI win does NOT generalize across eras**
      (consistent with the low-vol caveat about the Quality decade). Structure-based rules
      (HRP/ERC) match or edge 1/N over 90 years, at low turnover.
      **Multi-asset, OOS 1972→2026 (~54y incl. the real 1970s; Sharpe vs cash):**
      **ERC 0.64 wins** (risk balance across stocks/bonds/gold — Bridgewater's thesis at
      century scale); **maximin sleeve≤25% 0.59 > 1/N 0.58 > unconstrained maximin 0.56** —
      the diversified maximin's edge survives the real stagflation decade out of sample.
      Design lesson found: with cash in the menu, min-var/HRP degenerate into T-bills
      (excess ≈0.07) — cap or exclude cash for min-var/HRP-style engines.
- [x] **A2 — window-robustness — DONE 2026-07** (`proxy_backtest.py --dispersion`, 4 window
      variants per race). **The equity finding is robust: HRP and ERC beat 1/N in 100% of
      windows** (HRP top rule in 75%); min-variance beats 1/N in only 25% — its MSCI-era win
      confirmed as era-specific. Multi-asset: ERC the most robust (beats 1/N in 75%, top in
      50%); maximin variants mid-pack; min-var/HRP cash-degenerate in all windows.
- [x] **A3 — named-episode stress library — DONE 2026-07** (`portfolio/stress.py`, pipeline
      stage 13). Modern table (flagships through dot-com/GFC/COVID/2022): 2022 rate shock =
      all-weather −16.9% vs −24.8% balanced / −27% anchors. Historic table (static archetypes,
      century of storms): OPEC stagflation 1973-74 = **all-weather static +9.8% vs 60/40
      −28.5% vs pure equity −44.6%**; the allocation-shape story per episode, free of any
      optimizer's estimates.
- [x] **A4 — user profiles + "price of preferences" — DONE 2026-07.**
      `config.OPTIMIZER_PROFILES` + `optimizer.run_profiles()` + report section. Three
      presets (all with the diversified cap family): **Pure equity — diversified growth**
      (the owner's stated profile: return-tilted sliders; lands on 7 sleeves, momentum+value
      spread across regions, price −0.8pt CAGR vs its uncapped twin), Equity — balanced
      (10 sleeves), All-weather — defensive (maximin over the extended menu; price −2.0pt
      CAGR vs uncapped for −2.4pt vol and +1 sleeve). Each profile printed next to its
      unrestricted twin so the guardrails' cost — and what they buy — is a number, not a
      debate. Follow-up someday: profiles in the viz / dashboard tab (3c).

### Phase B — data that moves the needle (owner offered to source)

- [ ] **B1 — investable non-equity sleeves beyond the proxies**: REITs, broad commodities,
      TIPS, IG credit — each a DISTINCT quadrant profile (we only have gold+treasuries).
      Free candidates to evaluate first: FRED (TIPS yields → constructed TR, same Swinkels
      pattern), FTSE Nareit (REITs, downloadable), commodities likely needs a provider.
      Lands via the `source=api` registry branch.
      **Route found (Bouyé-Teiletche read, 2026-07): TIPS pre-1997 backfill via Swinkels'
      SPF-expectations method** — the same approach they use in the FAJ paper; un-blocks
      the descoped TIPS sleeve if we want the 1973+ history. Also noted from their OOS
      protocol: the real-time Sahm rule as a publication-lag-free growth signal — an
      alternative/complement to our lagged-labels discipline (idea only, needs its own
      test).
- [x] **B2 — equity menu gaps — MOSTLY DONE 2026-07 via the new `source=msci_api` branch**
      (MSCI's own end-of-day service, keyless, verified identical to the xlsx source to 9
      significant figures; codes discovered by probing — names are embedded in the XLS
      responses). Added: **USA Enhanced Value (705973, 1997-12+), Japan Momentum (703763,
      1997-01+), EM Quality (702788, 1997-01+)** — all preserve the 331-month common window.
      Look-through for api sleeves approximated by borrowing the region Reference factsheet
      (caveat #18). **Japan Reference fetched and REJECTED:** NETR history starts 2000-12 —
      would shrink the common window 330→307 months (the mixed-window trap).
  - [x] **DONE 2026-07-19 — owner manually exported the 4 missing xlsx** (the web UI serves
        longer NETR history than the graph service): Japan Reference (939200, from
        **1998-12-31 — exactly the common-window start, no shrink**; the api copy only had
        2000-12+), Japan Enhanced Value (706026, 1997-11+), Japan Quality (145817, 1997-01+),
        AC Asia ex Japan Quality (145829, 1997-01+). Menu 24 → **28 sleeves**; Japan is now a
        full 4-factor region; AC Asia ex Japan is complete. Ingested as `msci_local` with no
        `weights_file` (returns-only — look-through stays approximated, caveat #18).
  - [ ] Factsheet PDFs for the 7 sleeves without one (3 api + 4 new Japan/Asia xlsx) would
        make their look-through exact instead of approximated.
      **Explicitly NOT needed for research: S&P 500** (≈0.99 correlated with MSCI USA — pure
      redundancy). May still enter the ETF catalog later for mapping convenience.
- [ ] **B1b — broad commodities (energy-weighted)** — **RE-SCOPED 2026-07-21: this is now
      PAPER 2's data, not paper 1's.** Do not add it to the menu until paper 1 ships (see the
      sequencing decision in the Paper track). Extra motivation measured today: the
      all-weather flagship draws **33% of its OOS return from gold alone** and another 32%
      from EM Enhanced Value (M21 attribution) — two sleeves carrying 65% of the record over
      210 months is a concentration of EVIDENCE, not just of weights, and a second
      mechanically different stagflation asset is the direct fix. Original entry: gold alone
      carries the stagflation quadrant and energy was the actual OPEC-era winner — a second,
      mechanically different stagflation asset is the highest-value menu extension left.
      Free long-history sources are poor (GSCI licensed; BCOM ~1991) — needs a sourcing
      decision (owner). REITs/credit: distinct but lower priority (equity-correlated in
      crises / middle profile).
- [x] **Horizon-parametrized cones per profile — DONE 2026-07-19 (M23).** 5/10/20y cones
      per profile in the report (`optimizer._profile_cones`): equity profiles ~14% 5y loss
      probability vs all-weather 1.4% (10x), converging by 20y — horizon is now a measured
      selector between profiles.
- [x] **B3 — currency: EUR re-statement — CLOSED 2026-07-19 (M24 + update).** Unhedged:
      podium unchanged, vol-target overlays lose their edge (FX noise). Hedged (CIP with
      euro 3m interbank, carry −0.56%/yr): rankings virtually the USD table. All
      construction conclusions hold in all three seats; the currency seat moves levels,
      never decisions. C2 deep dive done (`literature/classics/currency-hedging.md`).

### Paper track — toward a publishable contribution (owner goal, 2026-07)

> Honest assessment: the replications (DeMiguel, constraints-as-shrinkage) are solid but not
> novel alone. The **candidate headline contribution** is the era-agreement-gated long-history
> shrinkage for regime-conditioned inputs (M5+M10): a simple, transparent estimator (sign-agree
> rule, month-weighting, β-mapped cross-universe transfer, principled exclusions) with measured
> OOS improvement on two universes. Realistic targets: SSRN working paper → *Journal of
> Portfolio Management* / *Journal of Asset Management* / a quant-finance conference. Top
> academic journals (JF/RFS) are not realistic for this design. What's missing before writing:

- [x] **Statistical significance for Sharpe differences — BUILT 2026-07-19** (`portfolio/
      inference.py` + deep dive `info/literature/classics/sharpe-inference.md`): Ledoit-Wolf (2008)
      HAC + studentized circular block bootstrap, and deflated Sharpe (Bailey-LdP 2014),
      standing section of `REPORT_optimizer.md` on every build. **Verdict (M14): NOTHING
      beats 1/N at 5%** — min-variance's +0.20 ann. Sharpe edge is p_boot 0.055 — and
      1/N+vol-target / balanced sliders are significantly WORSE than 1/N vs Min-var.
  - [x] PBO — **BUILT+MEASURED 2026-07-19 (M21): 33.2%** (CSCV S=16; `inference.pbo_cscv`,
        standing in the report). Block-size sensitivity: done in M17's grid.
- [x] **Exposure-robustness of the walk-forward verdicts — BUILT 2026-07-19** (motivated by
      M12). (a) half-sample Sharpe split + (b) rolling-36m beats-1/N share + per-region
      Reference correlations are now a standing section of `REPORT_optimizer.md`
      (`validation.exposure_diagnostics`, `optimizer_exposure.csv`); (c) leave-one-region-out
      walk-forward via `python -m portfolio_lab.portfolio.validation --loro`
      (`REPORT_exposure_robustness.md`). First read: min-var 100% / ERC 99% / HRP 98% of
      rolling windows beat 1/N; equity maximin 33%, momentum 36%.
  - [x] (d) OOS return attribution by sleeve — **BUILT+MEASURED 2026-07-19 (M21)**:
        per-refit weights now stored in walk-forward meta; `validation.sleeve_attribution`
        → `optimizer_attribution.csv` + report section. Headline: min-variance = 82%
        Quality; the all-weather's gold sleeve = 33% of its OOS return.
  - [x] **Anchor REGIONAL per-quadrant means — MEASURED 2026-07-19, verdict: cannot bite
        (M15).** Built (`long_history.market_prior` + `_anchor_mu_q` pass 1, behind
        `OPTIMIZER_ANCHOR_REGIONAL`) and A/B'd: equity maximin walk-forward IDENTICAL (its
        binding quadrant is Stagflation — the market's one era-flipped cell, so the agree
        gate correctly refuses the transfer); all-weather slightly WORSE (0.933→0.898).
        Default OFF. The estimator is self-limiting where eras disagree — a feature, and a
        paper section ("the obvious refinement, and why it cannot work"). EM's mitigations
        remain the caps + the M12/M13 diagnostics.
- [x] **A third universe — RUN 2026-07-19, verdict: CONFIRMS (M16).** Pre-registered
      protocol (`portfolio/ff_intl_test.py`, committed before the run), 9 virgin Ken French
      international sleeves, 307 OOS months incl. dot-com + GFC: the frozen estimator
      improves both maximin variants (Δ+0.002/+0.016); secondary — nothing beats 1/N
      significantly there either (best p=0.246), maximin family ranks last through two
      bears (equity-only, consistent M6). Snapshot frozen in `data/raw/ff_intl/`.
- [x] **Sensitivity grids — RUN 2026-07-19, verdict: plateau (M17).** `portfolio/
      sensitivity.py` (CLI): costs 0/10/25 bps, refits 6/12/24m, caps 20/35/35–30/45/45,
      LW block 3/6/10. No ledger conclusion flips in any walk-forward cell; the one
      frontier: p(min-var vs 1/N) crosses 5% with block length (0.042/0.055/0.066) —
      reported as borderline/specification-sensitive, conservative reading stands.
      Agreement-rule variants (sign vs magnitude bands) deliberately out of scope: that
      tests the ESTIMATOR's spec post-freeze and would need a fresh confirmatory universe.
- [x] **Formalize the estimator — DONE 2026-07-19** (`info/estimator.md`: notation, the two
      operative lines, EB/pretest interpretation, properties P1-P4 each tied to a ledger
      entry, positioning vs Ang-Bekaert / Guidolin-Timmermann / BL / Jorion, measured
      record M5-M19). Original sub-goals below kept for reference:
      (notation, assumptions, relation to James-Stein and
      empirical-Bayes shrinkage) and position against the regime-allocation literature
      (Ang-Bekaert; Guidolin-Timmermann).
- [ ] **Pre-draft checks (audit 2026-07-19)** — the remaining attackable assumptions:
  - [x] **CORRECTED 2026-08-29 (M40) — this item's plan was never executed and the paper
        text was written as if it had been.** The paper reports rf=0 Sharpes; §4.2 claimed
        excess-over-T-bill. Text now matches the table. The 0.067 below is NOT reproducible:
        both cached risk-free series cover only 148/210 OOS months. Restated on a common
        window instead (rf=0 p=0.180 vs excess p=0.209 — the convention is not load-bearing).
        Open: source a risk-free series spanning 2009-01→2026-06.
  - [x] Sharpe convention: recomputed the walk-forward table as EXCESS over T-bill
        (rf ~1.3%/yr avg) — rankings identical (only #8/#9 swap), min-var vs 1/N p_boot
        0.067 (vs 0.055 rf0): conclusions robust; paper tables will use the excess
        convention (standard).
  - [x] **Real-time discipline — MEASURED 2026-07-19, verdict: NO look-ahead subsidy
        (M19).** Labels lagged 2 months: every regime contestant improves or holds
        (all-weather 0.933→1.114!); non-regime bit-identical. Shipped lag-0 labels are the
        CONSERVATIVE spec; defaults unchanged (no tuning on the test), paper states both.
        Remaining gap stated: revised-vs-vintage FRED values (ALFRED replay = future
        appendix).
  - [x] **MSCI backfill/selection bias — MEASURED 2026-07-19 (M20).** Live-era split
        (2015+ only, 138 months): hierarchy holds (min-var #1 0.963, all-weather #2, HRP >
        ERC > 1/N), no conclusion flips. Plus the FF replications (M2/M16) as the
        structural defense. Limitations paragraph still to be written into the draft.
  - [x] Limitations STATED 2026-07-19 (THESIS.md §5 rewrite + paper/draft.md §7; drift
        turnover upgraded from 'stated' to MEASURED immaterial by M22). Original list:
        within-interval constant-mix drift turnover
        is uncosted (small; C1/C3 survive 25 bps anyway); DSR's N=11 counts fielded
        contestants, not every dev-time variant (the pre-registered M16 test is the
        stronger multiplicity defense); USD-only (B3); 1/N is menu-relative — the menu is
        a design layer and the paper must say so.
- [ ] **Frontier follow-ups (from the 2026-07 literature sweep — `literature/frontier/`).**
      Candidate tests, each cheap and referee-motivated; any design change they suggest
      needs the M16-style pre-registration discipline:
  - [x] **Yuan-Zhou combination contestant — FIELDED + MEASURED 2026-07-21 (M26). The
        prediction held.** `rules.gmv_combo_weights` (λ* re-derived from their five stated
        scalars; derivation in the docstring) is now a standing walk-forward contestant:
        **net Sharpe 0.735 vs 1/N 0.830, Δ −0.095, LW p_boot 0.449** — no win, and
        significantly worse than min-variance (p 0.016). λ* = 0 at the first three refits
        (their own formula refusing the GMV at η≈0.2), then 0.61 mean with a **13.4× gross
        exposure**. Sensitivity reported, not fielded: with our LW Σ, λ* 0.296, exposure
        1.6×, net Sharpe 0.825 — a dead heat with 1/N, so the verdict is not a handicap
        artifact.
  - [x] **Brodie-2009 rule — FIELDED + MEASURED 2026-07-21 (M28).** `rules.brodie_weights`
        (long-only min-variance at the trailing-1/N target, sample covariance — their exact
        specification). **Net Sharpe 0.933, THIRD in the table, ahead of HRP/ERC/1/N — but
        Delta +0.104 vs 1/N at p_boot 0.149, i.e. NOT significant.** Their "significantly and
        consistently" does not survive the Sharpe test and the cost charge they never ran.
        They are an ally, not a challenge: same family as our measured winner.
  - [x] **Random-regime placebo — BUILT + MEASURED 2026-07-21 (M32). THE LABELS DO NOT
        SURVIVE IT.** 80 scrambled-label walk-forwards (40 circular + 40 iid), two metrics
        (net Sharpe AND the realized worst-REAL-quadrant floor, the maximin's actual
        objective). **Nothing reaches significance in any of 12 cells; best p = 0.195; the
        real labels are BELOW the scrambled mean in 7 of 12**, including the flagship's own
        objective (random-label all-weather floor +0.005%/mo vs the real one's -0.090%).
        Harness verified (1/N sd 1.1e-16) and deterministic (Sharpe column reproduced
        exactly on the re-run). Untouched: M1/M2/M3/M13/M14/M25/M31 and every NUMBER in
        M6/M7/M10. Overturned: the ATTRIBUTION — the flagship's record is the MENU (M6/M27),
        not the labels.
  - [x] **Estimator placebo A/B — RUN 2026-07-22 (M35). Neither declared outcome: THERE IS
        NO EFFECT TO ATTRIBUTE.** Paired difference of differences, 20 replicates: every
        real-arm Delta is under half a null standard deviation, no placebo mean clears two
        standard errors of zero, and the estimator "helps" in 45-60% of replicates (a coin
        flip at B=20). The +0.012 M10 claimed was always smaller than M10's own acknowledged
        +/-0.01-0.02 menu-shift band. **The candidate headline contribution does not
        survive.** M10 superseded, M16 given a power post-mortem, the report's verdict logic
        fixed (it was labelling noise directionally).
  - [~] **Paper/THESIS re-framing after M32 + M35 — STARTED 2026-07-22.** Framing DECIDED
        (owner call): the spine is **"dispersion, not method — the opportunity set is why 1/N
        is hard to beat on an investable factor menu"**, which reconciles the 20-year debate
        via five levers (menu dispersion / inputs / turnover / shorting / significance bar).
        The equity-factor menu is the primary object; the multi-asset menu is the
        mechanism-confirming contrast — keep BOTH. Personal preference recast as "the retail
        factor-investor's setting" (general, not idiosyncratic). Factors justified as RETURN
        PREMIA + investability, NOT as diversifiers (M34 disproves that long-only — stated as
        a finding). Horizon stays a MEASURED price-of-preference (A4/M8/M23), never a
        recommendation. **DONE so far: title + abstract rewritten to v0.2, section-skeleton
        note added to draft.md.** Still to do below.
  - [~] **Paper re-framing — remaining sections (from the v0.2 skeleton in draft.md):**
        DONE 2026-07-22: §1 intro rewritten to open with the five-lever debate + the
        opportunity-set resolution; §2 given a new "the debate and its five levers" opening
        that engages the pro-optimization side (Kritzman-Page-Turkington 2010, Kirby-Ostdiek
        2012, Pflug-Pichler-Wozabal 2012) at thesis altitude; §4.2/§4.3/§5.1/§5.4/§5.5/§5.6/
        §6.3/§7/§8 rewritten; figures F0 (dispersion pillar) + F7 (placebo nulls) built;
        6 new references added (a referee-style cited-vs-listed audit caught Gelmini-Uberti
        missing from the list — fixed). STILL PENDING: (1) read KPT + Kirby-Ostdiek full
        text and deepen §2 beyond thesis-altitude; (2) format tables T1-T4 from the CSVs;
        (3) the multiplicity honesty pass (below); (4) owner read-through of v0.2.
        The flagship's NUMBERS stand; both its explanation and the paper's contribution
        change. Concretely: (1) every "regime-aware portfolio" becomes "a capped worst-case
        objective over a regime-DIVERSE MENU"; (2) the abstract's THIRD claim — the estimator
        as the methodological contribution — must be REMOVED as a positive result and
        rewritten as a negative one (M35: no measurable effect on the shipped menu, in either
        arm); (3) both placebos (M32 labels, M35 estimator) become §6 referee's-checklist
        subsections — reporting the two tests that attack our own signature feature is the
        credibility spine, not a loss; (4) the estimator sections (method §4.2, results §5.4)
        shrink to "a transparent construction we pre-registered and then could not resolve
        from noise — here is the power post-mortem (M16)". No longer blocked — the estimator
        placebo is done. See the HEADLINE DECISION block below for the framing choice this
        depends on.
  - [x] **Gelmini-Uberti (2024) READ IN FULL 2026-07-22** (owner supplied the PDF;
        `literature/frontier/gelmini-uberti-replication.md` rewritten from it). The
        abstract-only positioning guess was WRONG and is corrected: **they DO run a Sharpe
        significance test** (Jobson-Korkie 1981, p-values in every table). The real, stronger
        positioning that replaces it: (1) JK-1981 is the non-robust precursor — we use its
        HAC+bootstrap successor Ledoit-Wolf 2008, which matters for the non-normal monthly
        returns both papers use; (2) they run ~300 tests and adjudicate by eyeballing for a
        "bold line spanning all datasets" — our DSR/PBO/Nemenyi are the formal multiplicity
        control they lack; (3) BEST — their dispersed datasets DO yield frequent significant
        beats and they explain it by idiosyncratic dispersion, which is our DR² argument
        (M27/M34) in someone else's paper: optimization wins where there is dispersion to
        exploit, and our one-factor menu has none. Turns our menu limitation into a
        positioned finding and bridges to paper 2.
  - [ ] **Read Kritzman-Page-Turkington (2010) "In defense of optimization: the fallacy of
        1/N" and Kirby-Ostdiek (2012) "It's all in the timing"** — the two pro-optimization
        papers our intro currently ignores; both cited by Gelmini-Uberti as the "1/N can be
        beaten" side. Add Pflug-Pichler-Wozabal (2012) as the model-ambiguity theory for why
        1/N is hard to beat. These are the honest counter-literature the paper must engage,
        not omit.
  - [ ] **Factor-coverage limitations paragraph (referee will ask "what about growth/size/
        low-vol?").** Answer, measured: (1) growth is anti-value, no positive premium — the
        weakest such objection; (2) DR²/M18 says more long-only tilts on the same market beta
        do not add bets (they land at ~0.88 corr like the ones we have), so the verdict is
        coverage-robust; (3) size IS tested in the 90-year proxy race (FF size×value), low-vol
        IS what min-variance harvests (M2/M21). Frame as a limitation that CONFIRMS the
        dispersion mechanism, not a hole. Note the menu is extensible via the msci_api branch
        if a referee insists.
  - [ ] **Figure rework before submission (critical review 2026-07-22).** DONE: built F0b
        (the risk-return achievable-set cloud — the pillar dramatized, shared axes so the
        equity sliver vs extended spread is honest); FIXED F4 (was a truncated axis
        magnifying 0.002 A/B deltas AND foregrounding the M35-dead estimator — now
        full-height from zero with a 1/N line and an "everything clusters, Δ within the noise
        band" title). REMAINING: (a) F1 walk-forward race is 17-line spaghetti and redundant
        with F2/Table 1 — cut, demote to appendix, or rebuild highlighting 3-4 series over a
        gray cloud; (b) F3 LORO is a 17-line bump chart — rebuild highlighting only the
        maximin family (the lines that move); (c) F5 left panel connects heterogeneous grid
        dimensions on one axis (misleading) — rebuild as small multiples AND add the
        sigma-estimator column (M33, the only dimension that moved a number); (d) F7 add the
        realized-floor metric as a second row (the maximin's actual objective); (e)
        consistent contestant colors across all figures.
  - [ ] **Multiplicity honesty pass on the contestant table (M34).**  - [ ] **Factor-coverage limitations paragraph (referee will ask "what about growth/size/
        low-vol?").** Answer, measured: (1) growth is anti-value, no positive premium — the
        weakest such objection; (2) DR²/M18 says more long-only tilts on the same market beta
        do not add bets (they land at ~0.88 corr like the ones we have), so the verdict is
        coverage-robust; (3) size IS tested in the 90-year proxy race (FF size×value), low-vol
        IS what min-variance harvests (M2/M21). Frame as a limitation that CONFIRMS the
        dispersion mechanism, not a hole. Note the menu is extensible via the msci_api branch
        if a referee insists.
  - [ ] **Figure rework before submission (critical review 2026-07-22).** DONE: built F0b
        (the risk-return achievable-set cloud — the pillar dramatized, shared axes so the
        equity sliver vs extended spread is honest); FIXED F4 (was a truncated axis
        magnifying 0.002 A/B deltas AND foregrounding the M35-dead estimator — now
        full-height from zero with a 1/N line and an "everything clusters, Δ within the noise
        band" title). REMAINING: (a) F1 walk-forward race is 17-line spaghetti and redundant
        with F2/Table 1 — cut, demote to appendix, or rebuild highlighting 3-4 series over a
        gray cloud; (b) F3 LORO is a 17-line bump chart — rebuild highlighting only the
        maximin family (the lines that move); (c) F5 left panel connects heterogeneous grid
        dimensions on one axis (misleading) — rebuild as small multiples AND add the
        sigma-estimator column (M33, the only dimension that moved a number); (d) F7 add the
        realized-floor metric as a second row (the maximin's actual objective); (e)
        consistent contestant colors across all figures.
  - [ ] **Rewrite `info/THESIS.md` for the v0.2 framing.** It still carries the v0.1 spine
        (estimator as contribution, "regime-aware" attribution, M1–M21) and now opens with a
        stale-warning header listing the three corrections (M32, M35, M36). Rewrite it to
        mirror `paper/draft.md` v0.2, or retire it and point to the draft — having two
        synthesis documents disagree is worse than having one.
  - [ ] **§3 needs a "the investor's setting" paragraph justifying the MENU choice** (owner
        question 2026-07-22): why long-horizon → equity; why long-only/indexed → what a
        retail investor can actually buy; why factors → documented RETURN PREMIA (not
        diversification, which M34 disproves long-only). Measured support now in hand:
        every factor beats its own Reference in CAGR over the full window (Value +3.70pt,
        Momentum +2.88pt, Quality +1.47pt; 7/7, 7/7, 6/6 regions) and the premia SHRINK BUT
        SURVIVE in the backfill-free live era 2015+ (Momentum +3.38, Value +1.76, Quality
        +1.04; Quality only 4/6 regions) — report BOTH, the shrinkage is the honest part and
        is consistent with McLean-Pontiff (2016) post-publication decay. Literature base:
        Fama-French 1993, Jegadeesh-Titman 1993, Asness-Moskowitz-Pedersen 2013 ("Value and
        Momentum Everywhere" — the anti-data-mining defence), Asness-Frazzini-Pedersen 2019.
        Counterweight to state: McLean-Pontiff decay, Hou-Xue-Zhang (2020) replication
        crisis, and our own M34 (long-only tilts are ~95% market beta).
        M23 belongs here too as the PRICE of the horizon preference — with the caveat that
        loss-probability convergence at 20y is NOT "risk converges" (terminal-wealth
        dispersion grows; Samuelson/Bodie vs Siegel is an open debate).
  - [ ] **Multiplicity honesty pass on the contestant table (M34).** The 17 rows are ~4
        distinct strategies: HRP vs ERC correlate **0.998** OOS, Brodie vs min-variance
        **0.975** (and both live off USA Quality, 47% vs 52%). State this in the results
        section rather than letting the row count imply breadth, and note that Brodie
        inflates the deflated-Sharpe trial count without adding an independent test. A
        referee will find this; better that we find it first.

  > **HEADLINE DECISION PENDING (2026-07-22, after M35).** The estimator was the paper's
  > candidate contribution and it has no measurable effect on the shipped menu. The spine that
  > remains, and it is a real one: **four claims that do not survive proper testing — Yuan-Zhou
  > (M26), Brodie (M28), HERC (M29), our own regime layer (M32) and our own estimator (M35) —
  > plus the adjudication apparatus that killed them, plus the menu measurement (M18/M27/M34).**
  > A paper whose contribution is "here is the checklist, and here is what it destroys,
  > including ours" is publishable and rarer than another positive result. Owner call needed on
  > whether to reframe around that or to hold the draft until paper 2's data can rescue a
  > positive claim. Recommendation: reframe — the negative paper is finished today; the
  > positive one depends on data we do not have.

  > **SEQUENCING DECISION (owner call, 2026-07-21): finish and ship THIS paper on the frozen
  > 28-sleeve menu; the menu-design question becomes PAPER 2.** Rationale recorded so it is
  > not relitigated: (1) paper 1 is complete and self-consistent — it answers "which
  > weighting rule should an investor at this data scale trust?" with "none demonstrably,
  > and here is the full apparatus proving it"; (2) paper 2 needs data we do not have (B1/B1b)
  > and waiting would block paper 1 indefinitely; (3) the menu findings (M18/M27/M34) are
  > currently DESCRIPTIVE and full-sample — turning "selection beats weighting" into a claim
  > needs an out-of-sample protocol for menu SELECTION, which is a real research-design
  > problem and precisely what makes it a separate paper rather than an appendix;
  > (4) expanding the menu now invalidates every number already measured and would break the
  > pre-registration discipline (M16 was frozen against THIS menu). In paper 1 the menu
  > result stays where it now is: a limitation paragraph that also motivates the sequel.
  >
  > **PAPER 2's CANDIDATE HEADLINE — the one genuinely novel result the program could reach
  > (owner-endorsed 2026-07-22, "apunta esa idea para un futuro").** Everything in paper 1 is
  > honestly incremental: the dispersion MECHANISM is not ours (DeMiguel said it; DR² is
  > Choueifaty-Coignard; the inference tools are others'). We measure a known mechanism on a
  > new, practically-relevant menu and debunk one published "significantly" (Brodie, M28). That
  > is a solid JPM/JAM paper, not a novel law. The upgrade that WOULD be novel: **quantify the
  > relationship between a menu's DR² and how much optimization can beat 1/N, across many
  > menus, and find the threshold DR²\* below which no weighting rule beats 1/N.** Right now we
  > have only TWO points (our equity menu DR²≈1.31 → no edge; Gelmini-Uberti's dispersed
  > academic datasets → edge). A real finding needs the CURVE.
  > - **How to build it (menus we already hold, each with a different DR²):** the 28-sleeve
  >   equity menu (DR² 1.31), the asset-class-extended menu (1.43), the 90-year FF proxy
  >   universe, the FF-international universe, sub-menus (single-region factor sets; region
  >   Reference-only). For each: compute DR² (menu property) and the optimization edge
  >   (best structural rule's net OOS Sharpe minus 1/N, with its LW p). Plot edge vs DR².
  > - **The claim if it holds:** "below DR²\* ≈ [x], optimization cannot beat 1/N at any
  >   conventional significance; above it, the edge grows monotonically" — turning a 20-year
  >   qualitative debate into a measured frontier nobody has put a number on. That is the
  >   difference between "correct but incremental" and a paper a referee remembers.
  > - **Honesty guard, declared in advance:** with a handful of menus this is a low-N
  >   regression; report it as suggestive-with-CI, and if the relationship is noisy or
  >   non-monotone, say so — a null here is also publishable ("the threshold is not cleanly
  >   estimable at this menu count"). It needs the M16-style pre-registration before the run.
  > - **Prereqs:** best done WITH the B1/B1b data expansion (more menus = more DR² points =
  >   more power), which is why it is paper 2, not a paper-1 appendix.
  - [x] **Nemenyi — BUILT + MEASURED 2026-07-21 (M31).** `inference.friedman_nemenyi`, a
        standing report section. **Friedman rejects (chi2 46.6, p 0.0001) — the ordering is
        not noise — but the Nemenyi critical difference is 5.99 rank units and NOTHING
        differs from 1/N** (min-var's gap is 2.97, half the threshold). C2 survives the
        simultaneous test as well as the pairwise one.
  - [x] **Trend overlays — BUILT + MEASURED 2026-07-21 (M30).** `rules.trend_overlay`
        (Faber 10m SMA; Antonacci dual momentum = the momentum contestant gated by absolute
        momentum). **Prior confirmed on both counts: Faber's maxDD -19.9% vs 1/N's -26.9%
        (shallowest equity rule in the table) but Sharpe 0.656 vs 0.830; dual momentum 0.460,
        p_boot 0.034 = SIGNIFICANTLY WORSE than 1/N.** The overlay-family verdict is now
        complete and one-directional. Still to read on the FF-intl universe (two bears) —
        the fair arena for a rule whose payoff is sidestepping prolonged bears.
  - [x] **Sigma-estimator grid column — BUILT + MEASURED 2026-07-21 (M33). The declared
        expectation ("no material change at N<<T") was WRONG, and usefully so: nonlinear
        shrinkage costs MIN-VARIANCE 1.031 -> 0.947 (-0.084), the largest single move any
        sensitivity cell has produced here; HRP -0.019, ERC -0.001, HERC +0.008/+0.018,
        every mu_q/rule contestant bit-identical.** Mechanism: at p/n=0.085 nonlinear
        shrinkage correctly barely shrinks, and min-variance is the one Sigma^-1-driven rule,
        so it is the one that notices — our headline winner's edge is partly the crude
        estimator's doing. C1 does not flip but its margin collapses 0.098 -> 0.014.
        Same run exposed and fixed a reporting bug (stale conclusion vs sensitivity flip);
        M17's C4 corrected. Original entry:
        `shrinkage.shrink_nonlinear` (Ledoit-Wolf 2020 ANALYTICAL nonlinear shrinkage,
        closed-form Epanechnikov kernel; unit-tested to beat the sample matrix 4x on a known
        identity) + `shrinkage.estimate_covariance` dispatcher +
        `config.OPTIMIZER_SIGMA_ESTIMATOR`, so the estimator is now a
        `sensitivity.py` dimension. First read on the full window: at p/n = 0.085 nonlinear
        shrinkage barely moves the spectrum (smallest eigenvalue 3.4e-7 vs the sample's
        2.8e-7) — the near-null direction in 28 correlated sleeves is real structure, not
        noise. Run the grid to close the item.
  - [x] **HERC — BUILT + MEASURED 2026-07-21 (M29).** `anchors.herc_weights` + `gap_index`.
        **Prior right about the statistics, wrong about the direction: Ward 0.800 / single
        0.797, indistinguishable from 1/N (p 0.57) but BELOW both parents (ERC 0.848, HRP
        0.870).** Linkage moves it 0.003 Sharpe — the Ward-vs-single debate is not a debate
        here. Third finding: **the gap index never stops early on our menu** (monotone to
        the ceiling), so Raffinot's early stopping is inoperative — M18/M27 from a third
        angle. HERC NOT promoted; M25 unchanged.
  - [x] **Diversification Ratio (DR^2) — BUILT + MEASURED 2026-07-21 (M27).**
        `optimizer.diversification_ratio` + `menu_diagnostics` (which also promotes M18's
        ad-hoc PCA one-liner into a standing report section). Headline: the 28-sleeve
        equity menu at 1/N is **DR^2 = 1.31 independent risk bets** and min-variance's FOUR
        sleeves are 1.28 — 24 extra sleeves buy 0.03 of a bet. Adding the 3 asset-class
        proxies moves min pairwise correlation 0.53 -> **-0.14** and DR^2 -> 1.43, which is
        M6 measured at the MENU level and makes B1/B1b the highest-value open backlog item.
  - [x] **Paper related-work additions — WRITTEN 2026-07-21** (`paper/draft.md` §2): four
        new/rewritten paragraphs (estimation-error-and-1/N now carries Yuan-Zhou's theory and
        our fielded verdict; a new "Selection, not just weighting" paragraph on
        Ilmanen-Kizer + Choueifaty-Coignard + Hurst-Ooi-Pedersen with M27's DR^2 numbers; a
        new "Selecting versus spreading" paragraph on Brodie + DeMiguel-Garlappi-Nogales-
        Uppal; Antonov-Lipton-LdP and Raffinot into "Structure over estimation"; Boyd et al.
        as "The institutional foil"; Demsar + LW-2020 into "Backtest honesty"). Plus 16 new
        references, the MSCI-backfill limitations paragraph (closing the M20 follow-up) and
        a menu-design limitation stating DR^2 = 1.31 so readers discount effect sizes
        accordingly.
- [~] **Paper length pass — v0.3 WRITTEN 2026-08-29** (`paper/draft2.md`). Motivated by a
      measurement against the target outlets' actual guidelines: JPM's abstract target is
      **160 words, explicitly non-technical and reference-free**, and JAM caps articles at
      **6,000 words** — v0.2's abstract was 427 words with 5 citations, and its body 6,850.
      v0.3 cuts body to 5,809 (4,967 of prose + 509 of Table 1 + 333 of figure captions),
      abstract to 161, and re-weights toward the thesis: the dispersion mechanism is promoted
      from §5.4 to its own top-level §6, the race narrates less because Table 1 carries the
      numbers, the estimator's exposition shrinks (it returns a null), and the referee's
      checklist collapses into one §8 pointing at the ledger. Audited: all 49 references still
      cited, every cross-reference resolves, and NO data number was dropped (only old section
      numbers). Estimated ~12–13 pp in JPM's typeset style, inside their 10–14 range.
      **Open decisions for the owner:** (a) §2 is still 829 w — getting it to ~450 for JPM
      means dropping ~15 references, which is a call about whom to stop crediting; (b) whether
      to lead the paper with the F0b frontier-cloud figure (currently Figure 3 in §6) as
      Figure 1 in the intro — the draft itself calls it "the paper's claim in one image";
      (c) draft.md is kept as the long reference text, not deleted — decide before SSRN whether
      to retire it.
  - [x] **v0.5 — simulated peer review run and ALL findings resolved, 2026-08-29.** Ran
    `academic-paper-reviewer` (5 seats + editorial synthesis) against draft2.md. Two CRITICAL,
    five MAJOR. Every one is now closed:
    - **C1 (no inference on the contribution)** → built `inference.dr2_bootstrap`; DR² 1.310
      [1.242, 1.399], equity→extended +0.120 at **p=0.0002** (M39). In §6.
    - **C2 (headline is a non-rejection with no power reported)** → built
      `inference.sharpe_power`; **56% power**, MDES +0.27 vs observed +0.20 (M38). Every
      "nothing beats 1/N" downgraded to "not resolvably at this sample size". New subsection
      in §5.1; abstract, §1 and §10 realigned.
    - **M1 (2.8 vs 1.31 unreconciled)** → §3 now distinguishes eigenvalue-entropy bets from
      DR² and states that all headline claims use DR².
    - **M2 (single-regime OOS)** → §9 opening rewritten; §5.1 now connects the 82%-Quality
      attribution to the 90-year reversal, naming the modern lead regime-shaped.
    - **M3 (index "funds" vs indices)** → abstract corrected to indices.
    - **M4 (no ongoing fund fee)** → §9 states the omission, its direction, and the arithmetic
      (30 bps costs 1/N ~0.020 Sharpe and the 8.7%-vol flagship ~0.034).
    - **M5 (novelty buried)** → the value/momentum sign reversal promoted to a named result in
      §6.1 with the regional spread (M37).
    - Title also cut 15→11 words and "Cannot" dropped (PMR limit is 12): now *Dispersion, Not
      Method: Why 1/N Holds on an Investable Factor Menu*.
  - [x] **Honesty-signalling pass, 2026-08-29.** Owner flagged "Two null results, reported in
    full" as reading like AI boilerplate. Swept the whole .tex: it was not one phrase but a
    repeated tic — **the paper kept announcing its own honesty instead of just being honest**
    (7 instances: "reported in full", "the honest half", "where we correct ourselves", "our own
    signature feature" x2, "we attack it ourselves", "the lesson we draw against ourselves",
    "Reported ungated"). The merit is that the placebo exists, not that we narrate running it;
    a referee reads self-praise and asks why they are being told instead of shown. All cut, plus
    6 superlatives about the paper's own qualities and one over-written metaphor.
    - **One was a substantive error, not a style problem:** the introduction promised "a clean
      and, we show, inevitable answer" while §5.1 reports 56% power and says the race is
      unresolved. "Inevitable" is now gone — it contradicted M38.
    - Rule applied throughout: cut anything describing the paper's virtue, keep anything
      describing the finding. Legitimate technical language ("leak check", "a coin flip") kept.
    - Lesson for future edits: the hard-wrapped .tex breaks literal-string anchors constantly.
      Use whitespace-tolerant regex substitution instead; three separate batches aborted on
      line-wrap mismatches before switching.
  - [x] **PDF read end-to-end and fixed — v3 figures + LaTeX layout, 2026-08-29.** Owner
    compiled the .tex and sent the 20-page PDF. Read all of it. Findings and fixes:
    - **Every figure carried TWO titles and the legible one was wrong.** Each matplotlib chart
      had its own internal title, which at `width=\textwidth` renders around 6pt — smaller
      than body text — directly above a full-size caption saying the same thing. Stripped the
      internal titles/suptitles from F0, F0b, F3, F4, F5, F7; the LaTeX exhibit title now
      carries that job at proper size. Panel labels kept where the caption references them.
    - **Exhibit labels were below the graphics.** PMR's Appendix A puts the number and title
      ABOVE (12pt) and the note BELOW (8pt), for charts as well as tables — not the usual
      academic convention. The paper was also internally inconsistent (table above, figures
      below). Added `\exhibittitle`/`\exhibitnote` macros owning the counter directly, and
      converted all 8 exhibits; every caption split into a short title and an 8pt note.
    - **Legends sat on the data** in F5 (first panel), F0b and F4. All moved below the figure
      via `fig.legend`. F4's first attempt landed on the rotated x-tick labels; pushed further.
    - **Floats drifted away from their text** (Exhibits 4 and 5 both surfaced before the prose
      explaining them). Added the `float` package and pinned every exhibit with `[H]`.
    - **Readability: "one paragraph, one job."** The owner reported being overwhelmed by walls
      of numbers, correctly. Root cause was that no paragraph separated "here is the number"
      from "here is what it means". Three worst offenders rewritten: §5.1's opening (ten
      numbers before the reader had seen the table — the table was on the NEXT page, now moved
      ABOVE its prose), §6's "Second, independent bets" (eight numbers doing four jobs), and
      §3 Sources. Method detail (B, re-shrinking) pushed back to §4.2 where it belongs.
    - Jobson-Korkie citation read as "the Jobson and Korkie 1981 test"; now `\citeauthor` +
      `\citeyear`.
    - [ ] **draft2.md and paper/tex/paper.tex have now DIVERGED.** The prose splits above exist
      only in the .tex. Decide which is the source of truth — recommendation: the .tex, with
      draft2.md retired or regenerated from it. Do not hand-maintain both.
  - [x] **Figures rebuilt — v2, 2026-08-29.** Owner read the figures and reported they were
    unclear with overlapping text. Confirmed by opening all seven. **Originals archived in
    `paper/figures/v1_archive/`.** Findings and fixes:
    - **F0b (the pillar figure) did not show what its caption claimed.** It drew a Dirichlet
      cloud of random weights, and a uniform Dirichlet over N sleeves concentrates its mass
      near 1/N, so both panels rendered as similar blobs. Checked whether the figure or the
      CLAIM was wrong: the claim is true and **stronger** than v1 showed (achievable area ~47
      vs ~20; equity volatility floor **13.3%** vs extended **0.6%**). v2 draws the long-only
      efficient frontier (SLSQP per target return, swept up from the global min-var portfolio
      with warm starts — sweeping from mu.min() gave a sawtooth off the inefficient branch).
    - **F5 joined three unrelated grid dimensions on one continuous axis**, implying trends
      between quantities sharing no scale. Rebuilt as small multiples on a shared y-scale.
      This *revealed* an on-message pattern v1 hid: the all-weather maximin genuinely falls
      0.99→0.87 as caps loosen, i.e. constraints-as-shrinkage made visible.
    - **F3 was 11 equal-weight lines with the legend on top of the data.** Now greys every
      rule that holds rank and colours the maximin family by name (an automatic swing
      threshold picked a set that did not match the paper's claim). The all-weather taking
      rank 1 at −EM is now visible.
    - **F4**: the 1/N reference line struck through a Δ label; per-portfolio colours encoded
      nothing. Two colours + white label bboxes.
    - **F7**: the dotted line (the scrambled mean) was never explained; now in the legend.
    - **F0**: "1 bet" overlapped the reference line; DR² bars flattened by the 0-baseline.
      Now shades the 0–1 dead band and carries the M39 bootstrap CI as an error bar.
    - All six paper captions rewritten to match. `paper/make_figures.py` docstrings record why
      each v1 failed, so the mistakes are not repeated.
  - [x] **Filler pass, 2026-08-29** — 7 cuts of genuine redundancy and meta-commentary
    ("This is the paper's central claim", the Boyd foil, a re-derivation of the M38/M39
    asymmetry in §10). 90 words. Not a restructure: the owner asked to keep everything in the
    body for now.
    - [ ] **CONSEQUENCE — length regressed.** The fixes are all additions: computable body is
      now ~6,370 words vs ~5,130 before, against PMR's 4,000 target (7,500 ceiling) and JAM's
      6,000 cap. PMR states online-supplement material does not count toward length and names
      "detailed empirical results" as suited to it. Candidate move: §5.2 (193) + §7.2 (319) +
      §8 (417) → supplement, which lands ~5,440. Owner call, not done.
  - [x] **v0.4 style pass — DONE 2026-08-29.** Ran `academic-paper`'s
    `references/writing_quality_check.md` against draft2.md. The draft failed three of its
    rules badly: **84 em dashes** (limit 3), **21 binary contrasts** of the "not X, but Y"
    shape (limit 2), **10.2 semicolons per 1000 words** (limit 2.0). Vocabulary was clean —
    the AI register came from punctuation rhythm and rhetorical structure, not word choice.
    Rewrote the whole body: em dashes in prose 75→1, semicolons 10.2→1.1, binary contrasts
    16→7 of which only 2 are rhetorical (the abstract's thesis and the closing
    recommendation — the two the checklist allows). Section headings converted from
    rhetorical to plain noun phrases: "The race: nothing beats equal weight" → "The
    walk-forward race"; "Why: the opportunity set, not the optimizer" → "The opportunity
    set"; "Two null results, reported not buried" → "Placebo tests of the regime layer";
    "Selection, not just weighting" → "Menu selection". Audited: zero data numbers changed,
    all 49 references still cited, all cross-references resolve. Body 6193→6166 words (a
    style pass, not a cut).
  - **Toolkit installed 2026-08-29 (local, gitignored):** `academic-research-skills` v3.21.1
    cloned to `~/academic-research-skills`, symlinked into `.claude/skills/` as 4 skills
    (academic-paper, academic-paper-reviewer, academic-pipeline, deep-research). Installed
    SKILLS-ONLY by symlink, deliberately NOT as a plugin — the plugin ships a PreToolUse hook
    that runs on every Write/Edit/Bash (measured 0.22s/call here). Audited before install: no
    exfiltration, network only to arXiv/OpenAlex/Crossref, no credential access, no
    instruction-override text. **Caveat: licensed CC-BY-NC-4.0 (NonCommercial)** — re-check
    before any commercial use of work it helped produce (see `info/vision.md`). Directly
    useful here: `academic-paper format-convert` and its
    `references/citation_format_switcher.md`, which carries the Chicago 17th **Author-Date**
    spec JPM requires.
- [~] Paper draft — **v0.1 WRITTEN 2026-07-19** (`paper/draft.md`: full SSRN-style working
      paper — abstract, intro, related lit, data incl. virgin universe, method incl. the
      estimator's two operative lines, results R-sections with inference, referee's
      checklist, limitations, references, reproducibility appendix) + **6 publication
      figures** (`paper/make_figures.py` → `paper/figures/F1-F6.pdf`, from the same cached
      CSVs the ledger cites). Owner pass pending: authorship, repo URL, tone check → then
      SSRN.

### Phase C — targeted literature (specific gaps, not more canon)

- [x] **C1 — rebalancing — DEEP DIVE + MEASURED 2026-07-19 (M22)**:
      `literature/classics/rebalancing.md` + `portfolio/rebalancing.py`. Constant-mix vs fully-costed
      vs buy-and-hold on identical weight schedules: <=0.002 Sharpe difference, ranking
      identical — the assumption is not load-bearing. Band rules noted as a product-level
      refinement, not research.
- [x] **C2 — currency hedging — DEEP DIVE 2026-07-19** (`literature/classics/currency-hedging.md`):
      safe-haven currencies are embedded hedges (Campbell-Serfaty-Viceira 2010) — consistent
      with M24's measured unhedged-EUR result; default shippable guidance: hedge the bond
      sleeve, leave equity USD unhedged. Hedged re-statement stays in B3.
- [x] **C3 — factor valuation/timing — DEEP DIVE 2026-07-19** (`literature/classics/factor-timing.md`):
      the Asness-Arnott debate adjudicated for us — no valuation-based factor timing in the
      optimizer (weak at usable horizons, redundant with value, costly; our momentum
      contestant's measured failure is the same verdict with our p-values). Possible future
      Tier-2 dashboard diagnostic only; any promotion to input needs the M16-style
      pre-registered checklist.

_Sequencing: A first (all free, 1-2 sessions each), B in parallel as sourcing decisions land,
C as each deep-dive becomes load-bearing. Every result flows through the same honesty
protocol: walk-forward, net of costs, 1/N on screen._

## Dashboard: Tier-1 essentials layer (vision.md "Product design principle")

- [ ] Add a Tier-1 summary to each existing dashboard tab (Performance, Factor vs Reference /
      Regimes, Correlations/Diversification, Macro) per `vision.md`'s layering table: a small set
      of plain-language verdicts on top, with today's charts/tables becoming the Tier-2 detail
      underneath (collapsed or scrolled-to, not removed). Needs a "verdict generation" step per
      module (e.g. "led 1998–2010, has lagged since ~2010") — mostly template/text generation
      from analytics already computed, not new analysis.
- [ ] When the optimizer (Phase 3) exists, its Tier-1 output must be the recommended allocation +
      a "why" using the same essential bullets per holding — not a separate simplified summary
      disconnected from what the optimizer actually scored on.

## Dashboard: Macro State quadrant visualization

- [x] **4-quadrant position chart with trajectory and forecast** — DONE 2026-07. Lives at the top
      of the Macro State tab (right under the Tier-1 verdict card): current dot on continuous
      composite scores (can straddle borders), selectable trail (12/24/36m/full), month picker
      that also shows the actual forward path from any past date (hollow dots), momentum
      extrapolation arrow, and a collapsible "How is this computed?" block documenting smoothing,
      lag, z-scoring, probability mapping and the forecast method. Enabled by the classifier v2
      redesign below (continuous scores + soft probabilities).

## Portfolio optimization (vision.md Phase 3)

> **The unified method (v2) is documented in [portfolio_optimization.md](portfolio_optimization.md)**
> and **BUILT 2026-07** — 3a engine + 3b regime/maximin + walk-forward validation
> (`portfolio/shrinkage.py`, `anchors.py`, `views.py`, `optimizer.py`, `validation.py`, pipeline
> stage 10, `tests/test_optimizer.py`). The two original checklist items below are done; the
> remaining Phase-3 work is 3c and the smaller follow-ups listed after them.

- [x] **Design the multi-objective portfolio optimizer.** Goal: given the return/risk/exposure
      data already computed, find weights that best satisfy user-specified objectives, not just
      a single fixed formula. Needs to support, at minimum:
  - Single-objective modes, e.g. "maximize historical return" (degenerates to 100% in the best
    performer) or "minimize volatility."
  - Multi-objective modes with 2–3 goals at once, e.g. "maximize return **and** minimize risk
    **and** maximize sector diversification," blended.
  - **User-tunable priority weighting** across objectives — e.g. "I don't care about minimizing
    risk, I'll accept more of it to chase return" vs. "diversification matters most to me, return
    and risk matter less."
  - **Constrained targets**, e.g. "the best achievable return across these indexes is ~14%/yr —
    give me the allocation with maximum diversification and minimum risk subject to achieving at
    least 12%/yr."
  - This is explicitly complex and depends on other pieces landing first (see Depends-on below).
  - **Depends on:** ✅ the 100%-weight constraint and portfolio-level performance stats (both now
    in `portfolio/diversification.py`); a settled set of risk metrics (vol, max DD, maybe CVaR);
    ideally the regime-conditional data from Phase 2 if we want regime-aware optimization, not
    just full-sample optimization.
  - ~~**Open question:** optimization backend~~ — **DECIDED: `scipy.optimize`** (multi-start
    SLSQP). cvxpy can't express max-drawdown / per-regime objectives; Riskfolio-Lib is too heavy
    and opaque for the house style. Rationale in
    [portfolio_optimization.md](portfolio_optimization.md) §2.
- [x] **Regime-targeted allocation** (the signature feature) — DONE 2026-07. Regime row
      (per-quadrant importances, each quadrant scored on its own attainable range; presets
      historical-frequency / even 25×4 / Markov-outlook-weighted) + the **maximin mode**
      (`--maximin`: max the worst quadrant's return, epigraph reformulation) in
      `portfolio/optimizer.py`; regime views also tilt μ_BL via the BL layer, confidence-weighted
      by the Markov outlook. Validated by `analytics/scenario.py::portfolio_cone` + walk-forward.

### Phase-3 follow-ups (post engine build, 2026-07)

- [ ] **Michaud resampled efficient frontier — figure + dashboard panel** (owner question
      2026-07-21: "are we using the efficient frontier, does it make sense?"). We use the
      frontier as the method's SKELETON (`optimizer.py` stage 4) but deliberately never draw
      the classical mean-variance one, because its vertical axis is raw mu — the single most
      error-contaminated object in the theory (Chopra-Ziemba 11x; Michaud's "error
      maximizer"; our T=330 vs DeMiguel's ~3000). The canonical answer to exactly this
      problem is **Michaud (1998) resampled efficiency**: re-draw the frontier over B
      bootstrap resamples and show the CLOUD instead of the line. Cheap for us — the
      stationary-bootstrap machinery already exists in `analytics/scenario.py`, and the
      solver already traces constrained frontiers.
      Deliverables: (a) a paper figure — the resampled frontier cloud with 1/N, ERC, HRP,
      min-var and the flagships plotted on it; (b) a Tier-2 dashboard panel with the same.
      Composition settled by the 2026-07-21 read of a tutorial the owner linked
      (`literature/classics/mean-variance-and-estimation-error.md` §6): **Dirichlet random
      portfolios as the background cloud, but the frontier LINE from the optimizer, never
      from binning the cloud** — measured, a 200k-draw cloud on our 28-sleeve menu reaches
      the true min-variance edge (0.12% gap) but only **68% of the maximum attainable
      return**, because Dirichlet draws concentrate near 1/N as N grows.
      **Why it earns its place: it makes the project's thesis visible in one image** — the
      "frontier" is a wide smear, 1/N falls inside it, and on a DR^2 = 1.31 menu (M27) the
      smear is nearly degenerate, which is why every rule lands within 0.2 Sharpe of every
      other. Declared expectation, recorded in advance: the cloud will be wide enough that
      the flagship portfolios' separation is not visually resolvable.

- [x] **Rule-based contestants + transaction costs in the walk-forward** (2026-07) —
      `portfolio/rules.py` (`momentum_weights` = Jegadeesh-Titman 12-1; `vol_managed` = unlevered
      Moreira-Muir vol targeting) tested through the same walk-forward, now **net of
      `OPTIMIZER_TC_BPS` (10 bps)** one-way turnover cost (`oos_sharpe_gross` reports pre-cost).
      **Verdict: nothing beat min-variance.** Momentum 12-1 (top 6) net Sharpe 0.77 < 1/N 0.84;
      vol-targeting cut min-var's drawdown (−29%→−22%) but not its Sharpe (1.06→0.99); costs
      barely bit at annual refits (gross≈net). A clean, reported negative result — the method
      working. Follow-ups worth a look someday: momentum at a faster refit (its signal decays
      faster than yearly); min-variance as the BL anchor (it keeps winning — see below).

- [x] **Geographic look-through caps** (user request 2026-07: unconstrained maximin was 83%
      look-through Asia) — `optimize(geo_cap=...)` + `config.OPTIMIZER_GEO_ZONES`, linear
      constraints on w·Z so the objective still picks the best sleeves within each zone.
      Geo-capped maximin ships as third flagship + walk-forward contestant; it beat the
      unconstrained maximin OOS (Sharpe 0.84 vs 0.73 — constraints as implicit shrinkage,
      confirmed live).

- [x] **3c — dashboard "Optimizer" tab — SHIPPED AS A VIEWER 2026-07-19.** New 8th tab:
      flagship picker (weights bar + OOS metrics + top-3 attribution per portfolio) + the
      honesty table (walk-forward net OOS with LW Δ/p vs 1/N and DSR columns; significantly-
      worse rows in red). Live sliders deliberately stay CLI (SLSQP is Python — a slider
      grid would need precomputed combos; revisit only on demand). Header subtitle made
      dynamic (28 series · 8 regions — was hardcoded 21/7).
- [ ] CVaR-95 as third Tier-2 risk metric — un-parking route in
      [literature/classics/cvar-optimization.md](literature/classics/cvar-optimization.md): feed the
      Rockafellar-Uryasev LP with scenario-engine months instead of raw history.
- [x] Per-sleeve **risk budgeting — BUILT 2026-07-19**: `anchors.erc_weights(sigma,
      budgets=…)` (Spinu program with b_i-weighted log barrier; equal budgets = classic ERC
      bit-for-bit; convergence checked on contribution SHARES; unit-tested). Per-REGION
      budgets (b over groups) and profile/CLI exposure remain a follow-up when a profile
      wants them.
- [x] Revisit **ERC vs HRP — CLOSED 2026-07-19 (M25)**: HRP edges ERC everywhere by a hair
      (never significantly: LW p 0.119) at 12x the turnover; ERC stays the BL anchor
      (neutrality + stability), HRP stays the marginally better standalone construction.
      Original context: when more walk-forward evidence accumulates
      (first table 2026-07: min-var best OOS Sharpe 1.06, HRP 0.88, ERC 0.86, 1/N 0.84, maximin
      0.73, balanced sliders 0.70 — the balanced blend did NOT beat 1/N, exactly the DeMiguel
      expectation; min-var's win also matches the literature's "most-constrained models do best").

## Macro & regime analysis (vision.md Phase 2 remainder)

Motivating observation (2026-07): over the full 28y, AC Asia ex Japan / EM (esp. Enhanced Value)
top the CAGR table — but that's almost entirely a 1998–2010 story. From ~2010–2026 the leaders
flip to USA Quality, World Momentum/Quality generally, with visibly lower volatility. The
regime/leadership question isn't "who won in 28 years," it's "why did leadership flip, what macro
backdrop was each era in, and can we read the current backdrop to reason about what's more likely
to work now." That's the goal of this section — go beyond who-won-historically to a macro-aware
read of *why*, tying directly into the regime-targeted optimizer above.

**Status (2026-07): all 5 items below are DONE.** Added `breakeven_10y`/`breakeven_5y`
(T10YIE/T5YIE, market inflation expectations) and `us_recession` (NBER USREC) to `ingest/macro.py`
first, as free supporting data for the classifier. See `info/CLAUDE.md` §4 for module details and
§7 caveats #13-15 for the two real bugs found and fixed along the way (pandas NaN-comparison
pitfall in the trend classifier; depression-era history needed clipping out of the frequency
stats). **Now in the dashboard too** (2026-07): the "Macro State" tab shows the Tier-1
current-quadrant verdict, the colored month-by-month state timeline, per-state index performance,
factor edge by state, and the Monte Carlo scenario ranges — the first tab actually built to the
Tier-1/Tier-2 layering principle.

- [x] **Per-regime macro correlations** — `analytics/macro_link.py::regime_correlations()`, one
      matrix per named regime (chg basis, lag 0), written to `correlation_by_regime/*.csv`.
- [x] **4-quadrant macro-state classification** — `analytics/macro_state.py`, growth (indpro_yoy)
      × inflation (core_pce_yoy) trend → Goldilocks/Reflation/Deflationary-bust/Stagflation, with
      per-state performance broken down by series (region+factor) in `macro_state_performance.csv`.
- [x] **Regime-attribution narrative report** — same module's `factor_attribution()`: for each
      state, does each factor type consistently beat its own region's reference, averaged across
      regions (`macro_state_factor_attribution.csv`). Confirms e.g. Value leads in Deflationary
      bust (61.5% hit rate), Momentum leads in Goldilocks/Reflation but notably lags in Stagflation
      (-0.1% excess) — matching the known 2022 rate-shock pattern.
- [x] **Current-regime + trend read** — `macro_state.current_state()`: as of the latest complete
      macro print, which quadrant, which direction growth/inflation are trending, and how many
      consecutive months in that state. Explicitly labeled descriptive, not a forecast.
- [x] **Scenario simulation** — `analytics/scenario.py`: bootstrap Monte Carlo, resampling whole
      historical months (preserving real cross-series correlation) weighted by quadrant
      probability. Two built-in scenarios (historical-frequency-weighted, even 25/25/25/25);
      `simulate_scenario()` takes arbitrary custom weights for later optimizer use.
- [x] *(Explicitly out of scope, confirmed)* an actual predictive model (ML/probabilistic) of
      regime transitions or forward returns stays vision.md Phase 4 territory — same FRED-ToS
      constraint as the deferred ML/RL item below. Everything built here is descriptive/
      correlational + a stated-assumption bootstrap, not a forecast.

### Follow-up: revisit both methods — likely too simple as-is (2026-07)

**Status: DONE 2026-07 — both methods redesigned (v2), all three items landed.** See
`analytics/macro_state.py` / `analytics/scenario.py` docstrings and `info/CLAUDE.md` §4 + caveats
#11/#17 for the full method; the dashboard's "How is this computed?" block mirrors it for users.

- [x] **Classifier v2 — composite, continuous, with persistence.** Growth = z-scored trend
      composite of indpro_yoy, unemployment(−), yield-curve slope, VIX(−), Baa−10Y credit
      spread(−) (BAA10Y newly ingested — full history, unlike the 2023+ HY OAS); inflation =
      core PCE, CPI, PPI commodities, 10y breakeven. Continuous scores + soft quadrant
      probabilities (Φ-mapped, e.g. "45% Stagflation / 38% Reflation") instead of a forced
      bucket; hard label = most probable quadrant, keeping downstream compatibility. Empirical
      monthly Markov transition matrix (`macro_state_transitions.csv`) with per-state persistence
      and expected durations (~4–6 months), plus an NBER-recession overlap sanity check.
- [x] **Scenario v2 — regime-persistent simulation.** Paths are built in regime *spells*
      (geometric durations from the transition matrix) with contiguous block bootstrap within
      each spell — no more month-by-month i.i.d. quadrant flipping. New headline scenario
      `current_conditions` starts from today's actual quadrant and evolves by historical
      transition probabilities; the weighted scenarios (historical/even/custom via
      `simulate_scenario(weights)`) still converge to target long-run month shares (q ∝
      w·(1−p_stay)), so the future optimizer API is unchanged.
- [x] **Statistics-vs-ML line decided** and recorded in `info/CLAUDE.md` caveat #11: counting/
      normalizing/resampling history (z-scores, transition counts, bootstrap, momentum
      extrapolation) = fine under FRED ToS; anything fitted/trained to predict (regression
      forecasts, EM-fitted HMMs, ML) = Phase 4, non-FRED data. v2 stays entirely on the allowed
      side.

### Next: 2–3 month probabilistic quadrant outlook (backtest evidence gathered 2026-07)

A walk-forward backtest (~230 eval months, warmup 120) of the dashboard arrow vs alternatives was
run 2026-07 to decide how to upgrade "a simple arrow" into a proper short-horizon cone. Findings
worth keeping (statistics only, no ML — all within the caveat-#11 line):

- **Arrow (momentum extrapolation):** best *hard* single-quadrant call at every horizon — h=3 hit
  rate 57.4% vs 51.7% persistence — and the best transition-catcher (21.6% of actual quadrant
  flips at h=3 vs 0% for persistence). BUT in score space it overshoots: extrapolated dot position
  is *worse* than assuming no movement (MAE 1.50 vs 1.10 at h=3). Direction useful, length
  exaggerated.
- **Markov h-step (P^h from the transition matrix):** argmax collapses to persistence, but as a
  *probability distribution* it is the best-calibrated forecast at every horizon (Brier 0.168 at
  h=3 vs 0.241 persistence / 0.213 arrow). This is the natural "cone" — and the matrix is already
  computed and baked into the dashboard.
- **Analog (k=20 nearest past months by scores+velocities):** competitive Brier (0.175 at h=3),
  catches 15–20% of transitions, and doubles as narrative ("today most resembles …, here's what
  followed"). Slight full-sample standardization leakage in the quick test — redo clean if built.

- [x] Dashboard: **3-month probabilistic outlook** — DONE 2026-07. `quadrant_outlook()` (soft
      vector × P^3) in the report; outlook pills in the verdict card AND a per-selected-month
      outlook line on the quadrant chart (recomputed client-side from the baked matrix, so it
      follows the date picker).
- [x] Quadrant chart **empirical cone** — DONE 2026-07. 25–75 + 10–90 percentile boxes of
      realized (Δg, Δi) over the next 3 months across all months sharing the selected month's
      state, plus the individual re-anchored outcome dots colored by landing quadrant. Arrow
      kept at FULL length but relabeled direction-only: the damping sweep showed λ=1 gives the
      best hard quadrant call while ANY λ>0 worsens position MAE — so no damping constant,
      direction from the arrow, range from the cone.
- [x] **"Analog months" panel** — DONE 2026-07. k=20 nearest past months (scores + 6m
      velocities, z-scaled, ±6m exclusion), outcome summary pills, top-10 table, optional
      top-5 path overlay on the chart. Follows the date picker.
- ML verdict (recorded): not warranted at this horizon — ~350 monthly obs and ~50–80 observed
  transitions is too small for ML to beat counting; more/longer/higher-frequency data (non-FRED,
  Phase 4) would matter more than model class.

**Round 2 (2026-07): "should the prediction condition on more information?" — tested.** User
hypothesis: analogs/outlook should use trajectory, the underlying macro indicators, and index
trends, not just the quadrant summary. Walk-forward results (h=3, k=20, ~230 eval months):

- [x] **Trajectory: confirmed, shipped.** Analog features already included 6m velocities
      (entering ≠ exiting); adding 3m *accelerations* lifted transition-catching 16.2%→24.3% at
      no calibration cost → now in the dashboard (6-dim feature space).
- **Raw indicator trends in the k-NN: tested, REJECTED.** Adding the 9 component z-trends made
  everything worse (hit 42.2%→39.1%, Brier 0.177→0.192); + index features worse still. The
  composite scores already summarize the indicators — re-adding them as raw dimensions
  double-counts noise (curse of dimensionality at ~350 candidate months). More conditioning
  variables ≠ more signal at this sample size; more DATA would be the lever (Phase 4).
- **Border-distance conditioning: real signal, marginal gain, not implemented.** P(quadrant
  change within 3m) is 64% for months nearest the border vs 32–40% deepest in the quadrant —
  the quadrant label alone is indeed "vague." But an 8-state (quadrant × near/deep) transition
  matrix only improves Brier 0.168→0.161, because the soft-start vector already encodes border
  proximity. Left out for KISS; revisit if a use-case needs the extra ~4% calibration.
- **Markov outlook calibration (answer to "is it precise?"):** predicted 10–20% → realized
  10.6%; 20–30% → 20.7%; 30–40% → 46%; 50–70% → 71%. Mid-range is well calibrated; when it
  leans hard it is *under*confident (errs safe). Hard 3-month calls are right ~52–57% of the
  time vs 25% chance — probabilities honest, certainty impossible at this sample.

## Literature / methodology grounding

**DONE 2026-07 → [literature.md](literature.md).** Top-tier, production-proven canon only, each
entry with an adopt/adapt/benchmark verdict under our KISS + FRED-ToS constraints:

- [x] **Portfolio construction** — Markowitz → Michaud (error-maximization) → DeMiguel (1/N beats
      14 models; needs ~3,000 months to win — we have 330, the decisive number) → Ledoit-Wolf
      shrinkage (adopt) → Black-Litterman (adapt the prior+views pattern for regime tilts) → risk
      parity / All Weather → **HRP (candidate default engine)** → CVaR (optional Tier-2 later).
      Synthesis compressed into 8 build directives in literature.md §4 — these now govern
      [portfolio_optimization.md](portfolio_optimization.md).
- [x] **Regime detection & forecasting** — Hamilton (fitted MS models = Phase 4/non-FRED; our
      counted matrix is the honest cousin), Ang-Bekaert (regime-aware allocation earns its keep;
      value concentrates in avoiding the bad state → maximin), nowcasting/GDPNow (live data >
      fancier model — matches our own backtest conclusion), Politis-Romano stationary bootstrap
      (our scenario engine's method has a name and theory; cite when next touched).
- [x] **Factor canon** (why the sleeves exist) — Fama-French, Jegadeesh-Titman, Value & Momentum
      Everywhere, Quality Minus Junk; our per-regime factor attribution replicates their patterns.

## Data sources

### Data upgrades for the optimizer — prioritized (2026-07)

Decided after the optimizer build, from the "would more/other data help?" analysis. The ranking
logic: expected returns improve only with CALENDAR SPAN, covariance with observation count
(Merton 1980) — and shrinkage already patched the covariance (δ* ≈ 0.14 says the monthly sample
matrix was decent). So frequency is the least valuable axis; breadth and span are the levers.
Matches the round-2 backtest conclusion: at ~350 months, more data — not more conditioning — is
what moves the needle.

- [x] **P1 — Asset classes beyond equities — DONE 2026-07 (free proxy slice).**
      `ingest/asset_classes.py`: US Treasury 10y TR (constructed from `ust_10y`,
      Swinkels-2019 approximation, sanity-checked vs 2008/2013/2022), Gold (LBMA mirror,
      1833+), Cash (FF rf) — all free. Optimizer opt-in `include_asset_classes=True`
      (**equity-only stays the product default** — house thesis: equities are the productive
      asset; profiles opt in). **Measured (same window): the all-weather maximin more than
      doubles the worst-quadrant floor (+0.31%→+0.73%/mo), halves vol (23.9%→13.5%), cuts
      maxDD −61%→−34%, for −1.5pt CAGR — buying 40% gold + 13% bonds.** Ships as a report
      flagship. Traps handled: business-vs-calendar month-end join (period-aligned), geo-cap
      exemption, own-category diversification HHI.
  - [x] Shown in optimizer_viz (2026-07): roster entry (dark-gold), per-quadrant bars, map
        point, weights/risk pairs — build_data now uses per-portfolio series lists
        (`res["all_series"]`/`res["weights"]`), so mixed-universe portfolios render cleanly.
  - [x] **Diversified maximin (2026-07, from user critique):** unconstrained maximin is a
        structural corner solution (LP vertices + noisy per-quadrant means) — 3-4 sleeves,
        100% Enhanced Value, 83% Asia. New `factor_cap` (w·F per label bucket) completes the
        three cap axes; "Maximin (diversified)" preset (sleeve ≤25%, geo ≤40%, factor ≤40%)
        replaces the geo-only flagship/WF contestant, all-weather flagship rebuilt with the
        same caps. Measured: equity-only spread erases the stagflation floor (it WAS the
        concentrated Value bet); with bonds/gold spreading is nearly free (+0.59 vs +0.73
        floor). OOS Sharpe 0.84 vs 0.73 unconstrained.
  - [x] **All-weather honesty loop closed — DONE 2026-07 (see MILESTONES M7):**
        `scenario.build_universe(include_asset_classes=True)` gives all-weather portfolios
        their `current_conditions` cone (flagship: P(10y loss) 0.4%, maxDD p50 −14.5%);
        walk-forward gains the "Maximin (all-weather div)" contestant on its own extended
        universe. **Verdict: OOS Sharpe 0.94 (2009–2026, net of costs) — above every equity
        construction — at the lowest vol in the table (10.6%), maxDD −22.5%.**
  - [x] **μ̂_q long-anchoring — DONE 2026-07 (MILESTONES M10):** the maximin/regime objectives
        now consume `mu_q_obj` (proxy sleeves anchored on their own 1962+ quadrant means,
        factor sleeves on β-scaled FF excess; cash excluded on principle — rate levels aren't
        transferable behavior; reporting keeps empirical `mu_q`). Every maximin variant
        improved OOS; flagship: Sharpe 0.954, vol 8.7%, maxDD −16.7%.
  - [ ] TIPS sleeve — RE-SCOPED 2026-07: FRED's TIPS yield starts 2003; joining it would
        truncate the common window by 4 years (the mixed-window trap) for little testable
        gain. Revisit only with a longer (paid) real-yield series.
- [x] **P2 — Longer PROXY history for the regime layer** — DONE 2026-07 (first slice).
      `ingest/ff_factors.py` (Ken French monthly factors 1926+, free, non-FRED) +
      `analytics/long_history.py`: the classifier labels 789 months from 1960 (vs 353 modern —
      real 1970s Stagflation included, ~2.1× more months per quadrant). **Findings:** 15/16
      state×factor sign cells agree across eras — Value-in-Stagflation (+6.6%/yr over 66y) and
      Momentum's quadrant pattern are structural; the one flip is the MARKET factor in
      Stagflation (+0.5% long vs −5.4% modern) — the modern "equities always lose in
      stagflation" reading is era-specific. Report: `outputs/analytics/long_history/`.
  - [x] Follow-up DONE 2026-07: the regime views' Q now blends toward the long history where
        eras agree (`long_history.msci_factor_prior` + `views.regime_views(long_prior=)`):
        β translates the FF factor into MSCI-excess space (Mom β=0.28, HML β=0.19), blend
        weighted by months of evidence, clipped to the training window in the walk-forward.
        Effect: EV view tempered +0.44%→+0.15%/mo (the century says the modern value premium
        read was window-inflated); Momentum anchored 3/4 quadrants; Quality untouched (no FF
        counterpart). OOS Sharpe of the blend unchanged (0.70) — the tilt is small by design;
        the gain is input robustness, stated in the report per view.
  - [ ] Possible later: MSCI World from 1970 as a second proxy for region-level (not just
        factor-level) behavior; QMJ (AQR) as a Quality counterpart if a clean source exists.
- [ ] **P3 — Live data feed** (see "Live data" below) — the nowcasting lesson: fresher data
      beats a fancier model; our ~1–2 month macro print lag bounds the regime call more than
      method choice does.
- [ ] **P4 (likely never) — Higher-frequency (weekly/daily) returns.** Would only sharpen the
      covariance (already shrunk), does nothing for means (span-pinned), biases cross-region
      correlations via asynchronous closes, and the macro layer is inherently monthly (FRED
      prints monthly — no weekly quadrants). Recorded so the question isn't re-litigated.

### Infrastructure

- [x] **Index registry** (`data/index_registry.csv`) — explicit manifest of tracked indexes;
      ingest is registry-driven so adding an MSCI index = add a row + drop the file(s), no code
      edit. See `info/CLAUDE.md` §5.
- [x] **API data source — DONE 2026-07** (`source=msci_api` branch in `ingest/returns.py`,
      cached JSON, 3 sleeves live). Original text: add a `source=api` branch so indexes can be
      pulled from an API (e.g. a ticker feed) instead of local MSCI files, using the same registry
      contract. Keep the index set small/curated (KISS — the main indexes, not 200 niche ones).
      Now also the door for the P1 asset-class extension above.
- [ ] Optionally move the 2 hardcoded AC Asia ex Japan web-image weights out of
      `ingest/asia_images.py` into a small CSV, so *all* weight data is file-driven.

## Live data (vision.md Phase 1 remainder)

- [ ] Source a reliable, affordable **live index/holdings data feed** (open question — no
      provider chosen yet). Would plug in via the `api` source above.
- [ ] Compare each index's **current** behaviour vs. its own history (needs the live feed above).

## Tracker & product (vision.md Phase 5)

- [ ] **ETF menu per index** (user idea 2026-07): for each sleeve the optimizer can recommend,
      show the investable ETFs that track that index (ticker, TER, domicile, accumulating/
      distributing) so a recommendation translates directly into "what to actually buy."
      Needs an ETF-catalog data source (open question); natural companion to the `source=api`
      registry branch and the live-data feed below.
- [ ] Day-to-day portfolio tracking (positions, cost basis, live valuation).
- [ ] Rebalancing alerts triggered by regime change.
- [ ] Reporting (periodic summaries, exportable).
- [ ] Harden toward a real product: multi-portfolio support, persistence layer, auth, packaging.

## Open questions (from vision.md — resolve as we go, not blocking)

- Additional macro data APIs beyond FRED (OECD, World Bank, ECB, BLS?).
- How to define & detect the macro regime **in real time**, not just label history after the fact.
- ~~Optimization backend choice (`scipy` / `cvxpy` / `Riskfolio-Lib`)~~ — **RESOLVED: `scipy`**,
  see [portfolio_optimization.md](portfolio_optimization.md) §2.

## Deferred / explicitly out of scope for now

- **ML / reinforcement learning allocation** (vision.md Phase 4). Blocked in part by FRED's terms
  of use, which prohibit training ML/AI systems on FRED data — if this is ever built, its macro
  features must come from a different source than FRED (see `info/CLAUDE.md` caveat #11).
