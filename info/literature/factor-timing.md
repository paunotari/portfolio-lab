# Factor valuation & timing — the Asness–Arnott debate, adjudicated for us (C3)

The question behind "which factors are doing well NOW": can you time factor exposure using
valuation spreads (how cheap value/momentum/quality look vs their own history)? Directly
relevant to the anti-recency discipline (M9) and to whether the optimizer should ever
condition on factor valuations.

## 1. The two camps

- **Arnott / Research Affiliates** ("How Can 'Smart Beta' Go Horribly Wrong?", 2016+):
  much of measured factor alpha is revaluation — factors got expensive as money piled in —
  so buy factors when their valuation spread vs history is wide, avoid them when narrow.
  Implication: timing via valuation spreads is both possible and necessary.
- **Asness / AQR** ("Factor Timing is Deceptively Difficult", *JPM* 2017; and the
  contrarian-timing exchanges with Arnott): valuation-spread timing of factors is (a)
  weakly predictive at usable horizons, (b) largely a REDUNDANT bet — tilting toward cheap
  factors mostly re-buys the value factor you already hold — and (c) costly after turnover.
  Verdict: keep diversified factor exposure; "sin a little" at true extremes at most.

## 2. Where the empirical dust settled

Valuation spreads do correlate with subsequent LONG-horizon (5-10y) factor returns — the
same slow mean-reversion that makes trailing returns point backwards at 3-5y (M9, De
Bondt-Thaler). At tactical horizons the signal is weak, and implementations mostly load on
value. The honest reading either camp accepts: factor premia are harvestable diversified
and patiently; timing them adds mostly turnover unless you accept decade-scale
contrarianism.

## 3. ⇒ for us — adjudicated

1. **We do not add valuation-based factor timing to the optimizer.** Our conditioning
   variable is the macro quadrant (observable, era-tested — M4), not factor richness; the
   only "timing" in the system is the confidence-bounded BL tilt from the Markov outlook,
   and the estimator shrinks exactly the cells a valuation-timer would bet on.
2. **The M9/M12 discipline IS the Asness verdict operationalized**: never rank sleeves by
   trailing returns; judge rules walk-forward; and our momentum contestant (the tactical
   timer we did field) fails to clear 1/N net of costs in every universe we tested —
   consistent with (c) above, now with our own p-values.
3. **Possible future Tier-2 diagnostic, not an input**: showing each factor sleeve's current
   valuation spread vs its own history in the dashboard (context for the human, like the
   regime chip) would be honest; feeding it to the optimizer would not be, at our data
   scale. If it ever becomes an input, it needs the full referee checklist first
   (pre-registered, like M16).
