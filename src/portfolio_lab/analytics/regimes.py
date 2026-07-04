"""Macro regime map for the MSCI factor/region study (monthly boundaries, inclusive start,
exclusive end). Dates are month-end labels matching the data index.

Each regime carries analyst annotation: the macro backdrop, which FACTORS historically led,
which REGIONS were most helped/hurt, and the GEOGRAPHIC leadership shift. These are qualitative
priors from well-documented market history; analytics.py computes the ACTUAL realized returns
and correlations per regime from the data so the narrative can be confirmed or challenged.
"""

REGIMES = [
    {
        "id": "dotcom_peak",
        "name": "Late dot-com bubble",
        "start": "1999-01-31", "end": "2000-03-31",
        "macro": "Final TMT blow-off: Nasdaq roughly doubled Oct-1999→Mar-2000. Fed hiked from "
                 "4.75% to 6.0% (Jun-1999→Mar-2000); strong USD; EM rebounding post-Asian/Russian crises.",
        "factors": "Momentum & growth dominate as internet/telecom multiples expand; Value and "
                   "defensive Quality left far behind — the widest growth-over-value gap of the sample.",
        "regions": "US tech and North-Asian tech (Korea/Taiwan) lead; EM tech-heavy names surge; "
                   "Europe lags.",
        "shift": "Peak US-and-Asian technology/growth leadership just before the top.",
    },
    {
        "id": "dotcom_bust",
        "name": "Dot-com bust",
        "start": "2000-04-30", "end": "2002-09-30",
        "macro": "TMT collapse (Nasdaq -78% into Oct-2002), 2001 US recession, 9/11, Enron/WorldCom. "
                 "Fed cut from 6.5% to 1.75%.",
        "factors": "Value & Low-Vol sharply outperform; Momentum/growth crushed as prior winners "
                   "unwind — textbook post-bubble factor reversal.",
        "regions": "USA & tech-heavy World worst hit; EM/Asia relatively resilient, cushioned by "
                   "cheap valuations and early-2000s recovery.",
        "shift": "Rotation out of US growth toward value and, increasingly, non-US/EM.",
    },
    {
        "id": "em_supercycle",
        "name": "Global expansion & EM/commodity supercycle",
        "start": "2002-10-31", "end": "2007-10-31",
        "macro": "BRIC-driven synchronised boom: China accession-to-WTO demand, energy +~186%, weak "
                 "USD, abundant cheap credit. MSCI EM multiplied several-fold vs a modest DM gain.",
        "factors": "Value leads decisively (commodity/financial/cyclical tilt); Momentum strong once "
                   "trends establish; Quality lags in the low-quality, high-beta melt-up.",
        "regions": "EM and AC Asia ex Japan dominate globally; Europe solid; USA the clear laggard "
                   "as the USD falls and capital rotates offshore.",
        "shift": "Decisive, multi-year leadership shift to Emerging Markets, Asia and commodities.",
    },
    {
        "id": "gfc",
        "name": "Global Financial Crisis",
        "start": "2007-11-30", "end": "2009-02-28",
        "macro": "US housing/subprime bust → Lehman (Sep-2008) → global banking crisis and recession. "
                 "MSCI World max drawdown ~-54%; cross-asset correlations spiked toward 1.",
        "factors": "Quality & Low-Vol most defensive (Quality drawdown ~45% vs market ~54%; Min-Vol "
                   "~39%); Enhanced Value hammered by its heavy bank/financials weight.",
        "regions": "Broad-based crash; high-beta EM and AC Asia ex Japan fell hardest, USA relatively "
                   "less bad in local terms — regional diversification provided little protection.",
        "shift": "Diversification fails: nearly everything sold off together; only defensive factors helped.",
    },
    {
        "id": "post_gfc_rebound",
        "name": "Post-GFC rebound & early QE",
        "start": "2009-03-31", "end": "2011-06-30",
        "macro": "Mar-2009 bottom → V-shaped recovery on QE1/QE2, near-zero rates and a sharp "
                 "commodity/China-stimulus rebound.",
        "factors": "Value & Momentum snap back hardest in the junk/high-beta rally; Quality lags as "
                   "the most-distressed names lead off the low.",
        "regions": "EM and AC Asia ex Japan lead the rebound; cyclicals and commodity exporters "
                   "favour non-US markets.",
        "shift": "Brief but powerful EM/cyclical leadership before the 2011 turn back to the US.",
    },
    {
        "id": "eurocrisis_us_turn",
        "name": "Eurozone crisis & start of US leadership",
        "start": "2011-07-31", "end": "2015-12-31",
        "macro": "Euro sovereign-debt crisis (2011-12), Draghi 'whatever it takes' (Jul-2012), 2013 "
                 "taper tantrum, a strengthening USD, and the 2014-15 oil crash (~$110→<$50).",
        "factors": "Quality & Momentum begin structural outperformance; Value fades as the strong-USD, "
                   "low-growth backdrop punishes cyclicals and commodity names.",
        "regions": "USA pulls decisively ahead; Europe whipsaws through the debt crisis; EM and "
                   "commodity exporters stall under a rising dollar.",
        "shift": "Turn back to US leadership; strong USD becomes a persistent EM headwind.",
    },
    {
        "id": "us_megacap",
        "name": "US & mega-cap tech dominance",
        "start": "2016-01-31", "end": "2020-01-31",
        "macro": "Low inflation, low rates, and FAANG earnings dominance drive a long US bull market; "
                 "capped the longest Value drawdown since WWII (mid-2007 onward).",
        "factors": "Momentum & Quality dominate; Enhanced Value suffers historic underperformance — "
                   "factor indexes' structural underweight of expensive mega-cap tech was the main drag.",
        "regions": "USA (mega-cap tech) crushes EM, Europe and World ex USA by a wide margin.",
        "shift": "Extreme concentration into US large-cap growth/tech.",
    },
    {
        "id": "covid",
        "name": "COVID crash & liquidity-driven recovery",
        "start": "2020-02-29", "end": "2021-12-31",
        "macro": "Feb-Mar 2020 crash (fastest-ever -30%+), then unprecedented fiscal/monetary stimulus, "
                 "reopening and a late-2020 reflation trade.",
        "factors": "Momentum/growth surge into the recovery; sharp Value/cyclical rotation from the "
                   "Nov-2020 vaccine news — a growth-then-value whipsaw in one compressed window.",
        "regions": "US tech leads the bounce; EM/Asia strong through 2020 (early virus control); "
                   "commodity/energy names drive the 2021 reflation leg.",
        "shift": "Rapid growth→value rotation; leadership flips twice inside ~2 years.",
    },
    {
        "id": "rate_shock",
        "name": "Inflation & rate-hike shock",
        "start": "2022-01-31", "end": "2022-10-31",
        "macro": "40-yr-high inflation → fastest Fed hiking cycle since the 1980s (0%→~4%), war in "
                 "Ukraine, and a simultaneous bond sell-off.",
        "factors": "Value beat Growth by ~24% in 2022 (2nd-widest since 1975) via a long-energy / "
                   "short-tech tilt; Momentum/Quality/growth de-rated as long-duration cash flows repriced.",
        "regions": "US growth-heavy indices worst hit; value-tilted and energy-heavy exposures (incl. "
                   "parts of Europe) relatively resilient; strong USD pressured Asia/EM.",
        "shift": "Duration and growth punished; a brief but violent Value revival.",
    },
    {
        "id": "ai_boom",
        "name": "AI boom & mega-cap concentration",
        "start": "2022-11-30", "end": "2026-06-30",
        "macro": "ChatGPT (Nov-2022) ignites an AI/GPU capex boom; disinflation, resilient US growth, "
                 "record-narrow breadth and a semiconductor supercycle.",
        "factors": "Momentum & Quality lead again on the mega-cap AI winners; Value mixed; index "
                   "concentration (Nvidia/Mag-7, TSMC) reaches record highs.",
        "regions": "USA mega-cap and Taiwan/Korea semis (AC Asia ex Japan) dominate; China-heavy broad "
                   "EM lags on weak domestic demand and policy overhang.",
        "shift": "Back to US-plus-Asian-semiconductor leadership; extreme single-stock concentration risk.",
    },
]
