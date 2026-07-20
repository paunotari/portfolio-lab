# The most-downloaded practitioner rules on SSRN — Faber, Antonacci, Buffett's Alpha

*The owner's SSRN sweep ("portfolio", sorted by downloads) surfaces a stable podium of
practitioner papers with enormous readership. They matter for two reasons: referees know
them, and two of them are CONCRETE TESTABLE RULES our walk-forward can field. (SSRN's
Cloudflare blocks automated listing — this note covers the known perennial top of that
ranking; paste further titles from a manual browse and they get added.)*

## 1. Faber (2007, upd. 2013) — "A Quantitative Approach to Tactical Asset Allocation"

One of the most-downloaded investing papers in SSRN history. The rule is one line: for each
asset class, **hold it while its price is above its 10-month simple moving average; sit in
T-bills while below** — checked monthly, applied to 5 asset classes (US/foreign equities,
bonds, commodities, REITs). Claim: ~equity-like returns with bond-like volatility and
drawdowns since 1973 — because the filter sidesteps the deep bear markets.

**⇒ for us:** this is the missing member of our overlay family. We fielded cross-sectional
momentum (Jegadeesh-Titman) and vol-targeting (Moreira-Muir) — both failed to beat 1/N net
of costs (M1/M14) — but NOT time-series trend following, which is mechanically different
(it is an absolute filter, not a relative ranking, and its value concentrates in prolonged
bears, which our modern OOS window lacks — the FF-intl universe with two bears is the fair
arena for it). Candidate contestant: `rules.py` trend overlay (10m SMA per sleeve → cash),
walk-forward + LW p-value, on BOTH the MSCI menu and the virgin universe. Prior
expectation from our own evidence: helps drawdowns, struggles on Sharpe net of costs and
whipsaws — but it deserves the test before the paper claims overlays don't help.
[SSRN 962461](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=962461) ·
[author PDF](https://mebfaber.com/wp-content/uploads/2016/05/SSRN-id962461.pdf)

## 2. Antonacci (2012) — "Risk Premia Harvesting Through Dual Momentum"

Another perennial download leader. **Dual momentum** = relative momentum (hold the stronger
of an asset pair over the last 12m) + absolute momentum (only if it also beat T-bills;
else cash). Reported: higher return, lower vol, smaller max drawdown across equity, credit,
REIT and gold/treasury module pairs.
**⇒ for us:** a hybrid of our momentum contestant (relative) and Faber's filter (absolute).
If we field the trend overlay above, dual momentum is the natural second variant (one
extra line). Same honesty protocol; same prior expectation.
[SSRN 2042750](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2042750)

## 3. Frazzini, Kabiller & Pedersen (2013/2018) — "Buffett's Alpha" (*FAJ* 2018)

Download-ranking royalty, and directly relevant to OUR findings: Berkshire's 0.79 Sharpe is
explained by ~1.7× leverage on **Betting-Against-Beta + Quality-Minus-Junk exposure** — the
world's most famous stock picker decomposes into cheap, safe, quality factor loadings,
levered.
**⇒ for us:** the perfect companion citation for M21 — our min-variance "winner" earns 82%
of its OOS return in Quality sleeves. Same lesson at both scales: *what looks like skill is
usually a factor exposure wearing a name.* Cite next to the low-volatility canon
(`classics/low-volatility-anomaly.md`).
[SSRN 3197185](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3197185) ·
[NBER w19681](https://www.nber.org/papers/w19681)

## Why these three and not the rest of the download podium

The rest of the perennial SSRN "portfolio" top is either already in our canon (López de
Prado's HRP and backtest-overfitting papers, Ledoit-Wolf, Black-Litterman intuition
pieces), factor surveys covered by `classics/factor-canon.md` (Value/Momentum Everywhere,
QMJ, BAB), or wealth-management material with no testable mechanism. The three above are
the ones that add something we can either TEST (Faber, Antonacci) or CITE as independent
confirmation of a measured finding (Buffett's Alpha ↔ M21).
