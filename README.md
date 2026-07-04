# portfolio_lab

Macro-regime-aware portfolio analytics — MSCI factor/region study (28y monthly data), factor-vs-
reference performance, correlations, and look-through concentration, with a self-contained dashboard.

This is the empirical foundation for a larger goal: an integrated, affordable, macro-aware portfolio
planner + optimizer + tracker for individual investors. See **[info/vision.md](info/vision.md)**.

## Quick start

```bash
pip install -r requirements.txt
python scripts/run_pipeline.py      # rebuild processed data, analytics, and dashboard
python tests/test_pipeline.py       # data-integrity checks
open outputs/dashboard.html         # 5 tabs: Performance / Factor vs Reference / Regimes / Correlations / Diversification
```

## Where things are

- **How the code works, module map, caveats:** [info/CLAUDE.md](info/CLAUDE.md)
- **Product vision & roadmap:** [info/vision.md](info/vision.md)
- **Conceptual diversification thesis:** [info/factor-diversification-thesis.md](info/factor-diversification-thesis.md)
- **Source data:** `data/raw/msci_indexes/<REGION>/` (xlsx returns + pdf factsheets)
- **Code:** `src/portfolio_lab/` (`ingest` → `analytics` / `portfolio` → `dashboard`)
- **Generated output:** `data/processed/` and `outputs/` (both regenerable; gitignored)

## Coverage

21 return series (7 regions × Reference/Momentum/Enhanced Value/Quality, coverage uneven),
1997–2026 monthly, net USD. Factsheet sector/country/top-10 weights as of 2026-06-30.

> Note: returns and weights label EM differently — **join on `region`+`factor_type`, not
> `index_name`**. Details in [info/CLAUDE.md](info/CLAUDE.md) §7.
