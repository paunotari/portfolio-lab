# portfolio_lab

Macro-regime-aware portfolio analytics — MSCI factor/region study (28y monthly data), factor-vs-
reference performance, correlations, and look-through concentration, with a self-contained dashboard.

This is the empirical foundation for a larger goal: an integrated, affordable, macro-aware portfolio
planner + optimizer + tracker for individual investors. See **[info/vision.md](info/vision.md)**.

## Quick start

```bash
pip install -r requirements.txt     # installs the package (editable) + its deps
cp .env.example .env                 # optional: add a FRED_API_KEY for macro data
python scripts/run_pipeline.py      # rebuild processed data, analytics, and dashboard
python tests/test_pipeline.py       # data-integrity checks
open outputs/dashboard.html         # 7 tabs: Performance / Factor vs Reference / Regimes / Correlations / Macro / Macro State / Diversification
```

Without a FRED key the macro steps fall back to the keyless endpoint; skip them entirely with
`python scripts/run_pipeline.py --no-macro` (this also skips macro-link, the 4-quadrant macro-state
classifier, and the scenario simulation, all of which depend on FRED data — see
[info/CLAUDE.md](info/CLAUDE.md) §4-5 for what each does).

## Where things are

- **How the code works, module map, caveats:** [info/CLAUDE.md](info/CLAUDE.md)
- **Product vision & roadmap:** [info/vision.md](info/vision.md)
- **Conceptual diversification thesis:** [info/factor-diversification-thesis.md](info/factor-diversification-thesis.md)
- **Source data:** `data/raw/msci_indexes/<REGION>/` (xlsx returns + pdf factsheets) — **not
  included, see Data below**
- **Code:** `src/portfolio_lab/` (`ingest` → `analytics` / `portfolio` → `dashboard`)
- **Generated output:** `data/processed/` and `outputs/` (both regenerable; gitignored)

## Data

Three of the four sources are public and free, and the pipeline fetches them at run time:
**FRED** (macro indicators), the **Ken French data library** (research factors) and an
**LBMA gold** mirror. The frozen Ken French snapshot behind the confirmatory test is the one
data file committed here, so that run reproduces exactly.

The fourth is not. **MSCI index levels and factsheets are licensed and are deliberately not
committed here** — redistributing them is not ours to do. Everything else, including all the
code and the findings ledger, is present, so the pipeline runs end to end once you supply your
own copies:

```
data/raw/msci_indexes/<REGION>/*.xlsx   # monthly net-USD index levels
data/raw/msci_indexes/<REGION>/*.pdf    # factsheets, for look-through weights
```

`<REGION>` is one of ACWI, World, World_ex_USA, USA, EM, Europe, AC_Asia_ex_Japan, Japan, and
`data/index_registry.csv` lists exactly which index each file should be. Without them the
macro, long-history and Fama-French stages still run; the MSCI stages do not.

## Coverage

21 return series (7 regions × Reference/Momentum/Enhanced Value/Quality, coverage uneven),
1997–2026 monthly, net USD. Factsheet sector/country/top-10 weights as of 2026-06-30.

> Note: returns and weights label EM differently — **join on `region`+`factor_type`, not
> `index_name`**. Details in [info/CLAUDE.md](info/CLAUDE.md) §7.
