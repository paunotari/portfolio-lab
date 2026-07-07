# CVaR / Expected Shortfall optimization — Rockafellar & Uryasev (2000)

Deep dive behind [literature.md](../literature.md) §1. Optional Tier-2 tail-risk objective;
parked until wanted. ([Paper pdf](https://uryasev.ams.stonybrook.edu/wp-content/uploads/2011/11/kro_CVaR.pdf),
*Journal of Risk* 2(3) 2000.)

## 1. Principle

VaR_β (the β-quantile of loss) says *where* the tail starts but nothing about how bad it is
inside, and it's non-convex and non-subadditive (a merged portfolio can show *more* VaR than its
parts — incoherent). **CVaR_β = E[loss | loss ≥ VaR_β]** (a.k.a. Expected Shortfall) fixes both:
it measures the tail's *average depth* and is a coherent risk measure (Artzner et al. 1999).
Regulatory stamp: **Basel's FRTB (2016) moved market-risk capital from VaR-99 to ES-97.5** — the
production endorsement of exactly this measure.

## 2. The Rockafellar-Uryasev trick (what made it optimizable)

Minimizing CVaR looks nasty (the quantile moves with w). R-U's auxiliary function removes the
quantile from the problem:

```
F_β(w, α) = α + 1/(1−β) · E[ (L(w) − α)⁺ ]        (x)⁺ = max(x, 0)
```

Theorem: `min_w CVaR_β(L(w)) = min_{w,α} F_β(w, α)`, and the optimal α* is the VaR. F is convex
in (w, α) when L(w) is linear in w — which portfolio loss is: `L_j(w) = −r_jᵀw` per scenario j.

**Scenario LP formulation** (J scenarios, e.g. historical or bootstrapped months):

```
min_{w, α, u}   α + 1/((1−β)·J) · Σ_j u_j
s.t.            u_j ≥ −r_jᵀw − α ,   u_j ≥ 0        for each scenario j
                1ᵀw = 1 ,  w ≥ 0 ,  (other linear constraints)
```

A plain linear program — scales to thousands of scenarios. Alternatively keep SLSQP and minimize
F_β(w, α) directly with the smooth-max approximation; at our size either works.

## 3. For us — why parked, and how to un-park

- **Sample-size honesty:** with 330 monthly observations, β = 0.95 leaves ~17 tail months —
  CVaR estimated on raw history is noisy and dominated by 2008 + 2020 + 2022. That's not
  disqualifying (those ARE the events that matter) but it makes CVaR-optimal weights fragile.
- **The un-parking route:** feed the LP with **scenarios from our regime-persistent bootstrap**
  (`analytics/scenario.py`) instead of raw history — thousands of coherent months, regime-aware,
  and the machinery already exists. CVaR on `current_conditions` scenarios = "tail risk given
  where we are" — genuinely differentiated and honest about its assumption.
- UI: third option in the Tier-2 risk-metric selector (vol / maxDD / CVaR-95), plus reporting
  CVaR of any recommended portfolio (cheap: it's a sorted-average, no optimization needed just to
  *display* it).

## 4. Pitfalls

- β choice changes everything; fix β = 0.95 monthly and say so. (Basel's 97.5% is on daily
  horizons — don't cargo-cult the number.)
- CVaR from a *simulated* scenario set inherits the simulation's assumption (history re-sequenced)
  — display with the same disclaimer the scenario tab already carries.
- Don't optimize maxDD and call it CVaR — maxDD is path-dependent, CVaR is per-period; they are
  different objectives and both can stay.

**Primary sources:** [Rockafellar & Uryasev, *J. Risk* 2000](https://uryasev.ams.stonybrook.edu/wp-content/uploads/2011/11/kro_CVaR.pdf)
· Rockafellar & Uryasev 2002 (general distributions, [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=267256))
· Artzner, Delbaen, Eber & Heath 1999 (coherence) · BCBS, FRTB 2016 (ES 97.5 standard).
