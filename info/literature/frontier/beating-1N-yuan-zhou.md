# Yuan & Zhou (2023) — "Why Naive 1/N Diversification Is Not So Naive, and How to Beat It?"

*JFQA 2023 (SSRN 4281138). READ IN FULL 2026-07 (owner-supplied PDF). The direct descendant
of DeMiguel et al. attacking our central humility claim — and, read closely, the paper that
gives it a THEORY.*

## 1. The theory (why estimated rules lose)

With N assets, T observations and η = N/T, the plug-in Markowitz rule's Sharpe converges
not to the optimal SR but to **τ·SR with τ = √((1−η)/(1+η/SR²)) < 1** (their eq. 12) — the
estimation haircut in one formula. The 1/N rule beats the plug-in asymptotically whenever
**η > (1−δ²)/(1+δ²/SR²)**, δ = SR_{1/N}/SR (eq. 13); calibrated with δ=85%, SR=0.5/√12,
this yields **T > 3,205 for N=25 — DeMiguel's famous 3,000 months, derived instead of
simulated.** And Proposition 3: in a one-factor world with diversifiable idiosyncratic
risk, **1/N is asymptotically OPTIMAL as N grows** (SR_{1/N} = SR + O(1/√N)) — their
simulations: 1/N captures 90% of the optimal Sharpe with N=5, >99% with N=100.

**⇒ for our paper:** this upgrades our Section 5.1 from "replicates DeMiguel" to
"consistent with the Yuan-Zhou asymptotics": our menu is one-factor-dominated (first PC
77%, M18) and our η ranges 0.23→0.085 along the expanding window — the regime where their
theory says the humility result MUST hold.

## 2. How they beat it (N < T): two combination rules, closed form

- **GMV combo** (eq. 27): ŵ_{g,λ} = λ·Σ̂⁻¹1 + (1−λ)·1_N/N, with the asymptotic-Sharpe-
  maximizing λ* in closed form (eq. 29) from five estimable scalars (η, σ_g, σ_{1/N},
  SR_g, SR_{1/N}).
- **Plug-in combo** (eq. 30): ŵ_λ = λ·(1/γ)Σ̂⁻¹μ̂ + (1−λ)·1_N/N, λ* from eq. 34.

Both shrink WEIGHTS toward 1/N with a data-driven intensity — the same James-Stein family
as everything else that works at small T (their innovation vs Tu-Zhou 2011: Sharpe-ratio
objective + explicit λ*, not utility).

## 3. Their own empirical bounds (the fine print that matters)

Size-portfolio universes, estimation window **T = 360 months** ("smaller is not
sufficient"), OOS 2003-2022: combos beat 1/N at N=5 and N=20; at N=50 only the GMV combo;
at **N=100 every estimated rule INCLUDING the combos loses to 1/N**. For N>T they resort to
conditional information (anomaly/ML portfolios) with an explicit persistence caveat.

## 4. ⇒ the test we owe the referee — with the outcome PRE-DICTED by their own theory

Field the GMV combo (eq. 27/29 — the stronger one) as a walk-forward contestant on our
menu, LW p-value vs 1/N, net of costs. Note the deck is stacked in a theoretically
interesting way: our warmup T=120 is a third of their required 360, our menu is
one-factor-dominated (Prop 3 territory), and our N=28 sits where their combos still worked
at T=360. **Their own theory therefore predicts: no significant win on our menu.** If so,
the humility claim survives its strongest published challenger, adjudicated with the
challenger's own mathematics; if the combo DOES win significantly, the paper reports the
exception and cites them. Either outcome is a publishable sentence.

**Lineage to cite:** Kan & Zhou (2007) three-fund; Tu & Zhou (2011) "Markowitz meets
Talmud"; Frahm & Memmel (2010); Pflug-Pichler-Wozabal (2012, 1/N under ambiguity);
Yan & Zhang (2017, 1/N optimality under CAPM). [SSRN 4281138](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4281138)
