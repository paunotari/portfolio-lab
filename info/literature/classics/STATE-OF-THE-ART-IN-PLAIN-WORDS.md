# The state of the art, in plain words

Companion to [literature.md](../literature.md) (index + verdicts) and the technical deep dives in
this folder. No formulas here: this is the whole portfolio-construction and regime literature as
one readable story, for comprehensive understanding before diving into the math. If you only read
one file in this folder, read this one; if you're about to *implement*, read the deep dives.

---

## The story, chapter by chapter

### 1. The dream (Markowitz, 1952)

You can balance return against risk mathematically: tell me what each asset returns, how risky it
is, and how they move together, and I'll compute the best mix. Beautiful idea, Nobel Prize, and
still the frame everyone uses.

### 2. The catch: the machine trusts you too much (Michaud, 1989)

The optimizer treats your inputs as *facts*. But your inputs are guesses estimated from history.
And here's the cruel part: the optimizer doesn't just accept the errors — it *hunts* for them.
Whichever asset got lucky in your sample (return looks a bit too good, risk looks a bit too low)
is exactly the one the optimizer piles money into. It's not an "optimizer," it's an **error
amplifier**. Like a genie that grants your wish too literally.

### 3. The humiliation (DeMiguel, Garlappi & Uppal, 2009)

Researchers raced 14 sophisticated optimization models against the dumbest possible strategy —
split your money equally (1/N) and walk away. **None of the 14 beat it consistently.** The math
says you'd need roughly 250 *years* of monthly data before the fancy version reliably wins. We
have ~27. That's not an argument against optimizing — it's an argument against *naive*
optimizing, and it tells you the dumb benchmark must always be on screen for comparison.

### 4. Which inputs can you actually trust? (Chopra & Ziemba, 1993)

There's a hierarchy. Errors in **expected returns** hurt ~11× more than errors in risk
estimates — and returns are also the *hardest* thing to estimate. Correlations ("do these move
together?") are the most stable, most trustworthy input. So the rule:
**build on correlations and risk, never on past average returns.** "EM returned 12%/year
historically" is nearly noise; "EM and Asia move together, Quality holds up when things fall" is
real signal.

### 5. What the professionals did about it — four escapes

Each of these made careers and firms:

- **Clean the risk numbers** (Ledoit & Wolf — shrinkage). Extreme correlations in your data are
  usually luck, so pull them gently toward the average. Boring, free, everyone does it.
  → [ledoit-wolf-shrinkage.md](ledoit-wolf-shrinkage.md)
- **Skip return predictions entirely** (risk parity / Bridgewater's All Weather; López de Prado's
  HRP). Allocate so each asset contributes *equal risk*, or group similar assets into a family
  tree and split money down the branches. No predictions needed — so no predictions to be wrong
  about. Bridgewater built the world's largest hedge fund on essentially this idea, applied to
  the same four macro quadrants we use.
  → [risk-parity-erc.md](risk-parity-erc.md), [hierarchical-risk-parity.md](hierarchical-risk-parity.md)
- **If you have opinions, add them gently** (Black & Litterman / Goldman Sachs). Start from a
  neutral portfolio, then tilt it *in proportion to how confident you are*. A 34%-confidence view
  tilts you 34%-hard, not 100%-hard. No opinion? You stay neutral. This is how opinions enter
  without letting them wreck the diversification.
  → [black-litterman.md](black-litterman.md)
- **Respect regimes** (Hamilton; Ang & Bekaert). Markets change personality with the macro
  environment — and crucially, diversification fails exactly in the bad regime (everything
  crashes together). The measured value of being regime-aware comes mostly from **not being
  destroyed in the worst quadrant**, not from brilliantly picking the best one.
  → [regime-switching.md](regime-switching.md)

### 6. Always verify like a skeptic

Test on data the method never saw (walk-forward), compare against equal weight, and measure tail
pain as "the average of the worst months" (CVaR — [cvar-optimization.md](cvar-optimization.md)),
not just volatility. The same honesty protocol our quadrant forecasting already follows.

### 7. The plot twist: the boring portfolio keeps winning (the low-volatility anomaly)

Finance's founding promise — more risk, more reward — turns out to be empirically backwards
*within* stock markets: boring, low-risk stocks have earned about as much as exciting, risky
ones, which makes their risk-adjusted returns far better. Why doesn't everyone pile in and fix
it? Because most investors can't or won't borrow to amplify boring returns, so they overpay for
exciting stocks instead — leaving the calm ones structurally cheap (Frazzini & Pedersen's
"Betting Against Beta"). This is why plain minimum-variance — the strategy that never even looks
at returns — won both halves of our own out-of-sample test. It's not smarter; it's harvesting
this premium while having no return forecast to be wrong about.
→ [low-volatility-anomaly.md](low-volatility-anomaly.md)

### 8. Has anyone put it all together?

Every big shop built its franchise on one piece: Goldman on Black-Litterman, Bridgewater on All
Weather (our maximin, industrialized), AQR on factors + risk parity. In books, three
single-volume syntheses stand out: Ilmanen's *Expected Returns* (what each asset should earn and
why), Ang's *Asset Management* (everything reorganized as factors), López de Prado's *Advances
in Financial Machine Learning* (how not to fool yourself). There is no single canonical
combination — ours is [portfolio_optimization.md](../portfolio_optimization.md), and its
deliberate edge is the one thing commercial syntheses won't sell: measured honesty.

---

## The global picture — what to keep in mind when building a portfolio

A pyramid, from most to least trustworthy:

1. **Structure first.** The reliable information is *how assets relate*: which are siblings,
   which hedge each other (our Value↔Momentum negative correlation is the crown jewel — see
   [factor-canon.md](factor-canon.md)). Start the portfolio from structure — equal weight, equal
   risk, or HRP's family tree — cleaned with shrinkage.
2. **Constraints are your friend.** Caps like "max 40% per sleeve, minimum 3 sleeves" aren't just
   prudence — mathematically they act like error-dampers and measurably *improve* out-of-sample
   results. Guardrails are part of the engine, not an apology.
3. **Preferences tilt, they don't command.** The three sliders (return / risk / diversification)
   and the regime views should *bend* the neutral portfolio proportionally to confidence — never
   hand the wheel to "maximize past returns," which is the one wish the genie always corrupts.
4. **Build to survive all four quadrants.** Since regime calls are ~50% right at 3 months (we
   measured it — TODO.md round 2), the robust move is a portfolio that's acceptable in *every*
   quadrant and tilted only mildly toward the likely one — the maximin idea, which is All
   Weather's whole philosophy.
5. **Judge the result honestly.** Show it next to equal weight; show where the risk actually sits
   (risk contributions); stress it through the scenario engine; report the worst-case months. If
   the clever portfolio can't clearly justify itself against the dumb one, the dumb one wins —
   and saying so is a feature.

---

## One sentence

**With 27 years of data, your biggest enemy isn't the market — it's your own estimation error;
so build from the stable structure of the assets, add opinions only in proportion to confidence,
defend the worst regime rather than chasing the best, and always keep the humble equal-weight
benchmark on screen to keep yourself honest.**

And the product implication: our optimizer's edge won't be "it predicts better." It'll be that
it's *transparent about uncertainty* — the same honesty built into the quadrant forecasting —
applied to allocation.
