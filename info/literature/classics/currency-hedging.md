# Currency hedging — what the literature says, what we measured, what remains (C2/B3)

The owner invests from EUR; all project results are USD. This note is the targeted
literature check for the hedging decision plus the tie-in to our own M24 measurement.

## 1. The canon

- **Campbell, Serfaty-de Medeiros & Viceira (2010), "Global Currency Hedging", *JF*.** The
  risk-minimizing currency position is not "hedge everything": currencies that are
  NEGATIVELY correlated with global equities — the USD prominently, also CHF (and JPY in
  much of the sample) — act as embedded hedges, so an equity investor can *reduce* risk by
  keeping (even adding) exposure to them. Reserve/safe-haven currencies appreciate exactly
  when equities fall.
- **The bond-side consensus** (same paper + practitioner literature): for BONDS the calculus
  reverses — FX volatility (~8-10%/yr) swamps bond volatility, adds no expected return, and
  should generally be fully hedged.
- **Hedging mechanics.** By covered interest parity, a rolled 1-month hedge earns
  approximately the short-rate differential: r_hedged ≈ r_USD_asset + (rf_EUR − rf_USD).
  Hedging is not free insurance; it swaps FX risk for the carry differential.

## 2. What we measured (M24 — the unhedged half)

Re-stating the walk-forward's net OOS returns in unhedged EUR (DEXUSEU month-end): the
podium and every construction conclusion survive the currency seat; all Sharpes rise (the
2009-2026 dollar paid the EUR investor); and the vol-target overlays lose their edge — FX
noise dilutes volatility control, so their USD ranking was partly a currency artifact.
Consistent with Campbell et al.: for an equity-heavy EUR investor, unhedged USD exposure
behaved as the embedded hedge the theory predicts over this window.

## 3. The hedged half — MEASURED (same day; B3 closed)

Monthly hedged EUR return ≈ r_USD + (rf_EUR − rf_USD) by covered interest parity (euro-area
3m interbank from FRED as the short rate; FF rf on the US side; mean carry −0.56%/yr over
the OOS window). Result: **rankings are virtually the USD table** — top-5 identical
(min-var 0.99, min-var+VT 0.89, all-weather 0.85, HRP 0.81, ERC 0.79), only 1/N and the
equity maximin swap #6/#7. Across all three seats (USD, EUR unhedged, EUR hedged) every
construction conclusion holds: the currency seat moves LEVELS, never DECISIONS. Caveats:
CIP basis post-2008, frictionless monthly hedge, 3m rate proxying the 1m tenor; and the
whole exercise re-states the same decisions — the weights never see the currency.

**⇒ for us:** the construction verdicts are currency-robust (measured); the hedging DECISION
is a preference/profile question — "hedge the bond sleeve, leave equity USD unhedged" is the
literature's default and can ship as a profile note without new research.
