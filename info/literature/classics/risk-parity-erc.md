# Risk parity / Equal Risk Contribution — Dalio (production), Maillard-Roncalli-Teïletche (2010), Asness-Frazzini-Pedersen (2012)

Deep dive behind [literature.md](../literature.md) §1. The μ-free allocation family; candidate
prior for the BL blend and candidate default engine alongside HRP.

## 1. Principle

Dollars diversify badly because risk concentrates: 60/40 in dollars is ~90/10 in *risk* (equities
dominate variance). Risk parity allocates **risk budgets**, not capital — and needs no expected
returns at all, sidestepping the least-estimable input entirely
(see [mean-variance-and-estimation-error.md](mean-variance-and-estimation-error.md)).

Bridgewater's All Weather (1996, production) is the ancestor and is built on the same
growth×inflation quadrant map as our macro module: balance risk across the four economic
environments so no single regime can sink the portfolio. Our "maximin across quadrants" mode is
this idea made explicit.

## 2. The math (Euler decomposition of portfolio risk)

σ_p(w) = √(wᵀΣw) is homogeneous of degree 1, so it decomposes exactly:

```
marginal risk contribution:   MRC_i = ∂σ_p/∂w_i = (Σw)_i / σ_p
risk contribution:            RC_i  = w_i·(Σw)_i / σ_p
Euler identity:               Σ_i RC_i = σ_p
```

**ERC portfolio:** RC_i equal for all i (each asset contributes σ_p/n of the risk).

Properties (Maillard, Roncalli & Teïletche 2010, *JPM* — "the ERC paper"):
- Long-only ERC **exists and is unique**.
- Volatility ordering: `σ_minvar ≤ σ_ERC ≤ σ_1/N` — ERC sits between min-var (all in the
  low-vol corner) and naive equal weight; a principled middle.
- If all correlations were equal, ERC = inverse-volatility weights.

## 3. Computation (both trivial at n=21)

**Convex reformulation (Spinu 2013):**

```
y* = argmin_y  ½·yᵀΣy − Σ_i ln(y_i)      (unconstrained, convex)
w  = y*/1ᵀy*
```

Solvable by Newton or even our SLSQP; the log barrier forces strictly positive weights and the
first-order condition y_i(Σy)_i = const is exactly ERC.

**Fixed-point iteration (simpler):** `w_i ← (σ_p²/ (Σw)_i) · normalize` until RCs equalize.

**Naive inverse-vol** (`w_i ∝ 1/σ_i`) ignores correlations — acceptable quick baseline, not ERC.

Risk *budgeting* generalizes: target contributions b_i (Σb_i = 1), condition
`RC_i = b_i·σ_p` — same convex program with `b_i·ln(y_i)`. This is how a user could say
"EM gets 10% of my risk, not 10% of my money."

## 4. The academic explanation (Asness, Frazzini & Pedersen 2012, *FAJ*)

Why has risk parity outperformed? **Leverage aversion**: most investors can't/won't lever, so
they overpay for high-beta assets to reach return targets; low-beta/low-risk assets get
structurally underpriced ([paper](https://pages.stern.nyu.edu/~afrazzin/pdf/Leverage%20Aversion%20and%20Risk%20Parity%20-%20Asness%20,%20Frazzini%20and%20Pedersen.pdf)).
Levered risk parity harvests that premium. Same mechanism as their "Betting Against Beta."

**Unlevered caveat for us:** we run long-only, no leverage, single asset class (equity indices).
Cross-asset RP's biggest wins came from levering bonds — not available here. What survives in our
context: ERC as a *robust diversification engine* across region/factor sleeves — its value to us
is estimation-robustness, not the leverage-aversion premium. Set expectations accordingly.

## 5. For our build

- ERC on the **shrunk** Σ = the default `w_prior` for [black-litterman.md](black-litterman.md).
- Risk budgeting = natural Tier-2 extension (per-sleeve or per-region risk budgets).
- Report the RC vector with any recommended portfolio — "where your risk actually sits" is a
  Tier-1-worthy honesty number, and it reuses the same math.
- Unit test: on a diagonal Σ, ERC must equal inverse-vol; σ ordering vs min-var and 1/N must hold.

**Primary sources:** Maillard, Roncalli & Teïletche, *JPM* 36(4) 2010 · Spinu 2013 (SSRN) ·
[Asness, Frazzini & Pedersen, *FAJ* 68(1) 2012](https://pages.stern.nyu.edu/~afrazzin/pdf/Leverage%20Aversion%20and%20Risk%20Parity%20-%20Asness%20,%20Frazzini%20and%20Pedersen.pdf)
· Bridgewater, "The All Weather Story" (firm publication).
