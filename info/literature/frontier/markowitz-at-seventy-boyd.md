# Boyd, Johansson, Kahn, Schiele & Schmelzer (2024) — "Markowitz Portfolio Construction at Seventy"

*Stanford convex-optimization royalty (Boyd) + a BlackRock quant legend (Kahn) writing the
definitive "how professionals actually run MVO in 2024" paper. arXiv 2401.05080 / SSRN
4695694; open PDF on Boyd's Stanford page.*

## What it is

The modern engineering-grade Markowitz: one convex program carrying everything practice
needs — holding and transaction costs, leverage and cardinality-style limits, shorting
costs, factor covariance models, and crucially **robustness terms for uncertainty in the
return forecasts** (penalizing exposure to estimate error directly in the objective).
Solved reliably and fast with modern convex solvers; reference implementation open-source.
Their stance: Markowitz's frame is fine at seventy — the failures people attribute to it
are failures of inputs and of naive implementations, not of the frame.

## ⇒ for us — the perfect foil, and one borrowed idea

- **Positioning:** Boyd et al. is what the state of the art looks like **when you have the
  inputs** (institutional data, live forecasts, engineering budget). Our paper is about the
  regime where you demonstrably do NOT (T≈330, p≈0.055 for the best rule's edge): at that
  scale the correct "robustness term" degenerates to structure + caps + cross-era
  shrinkage. Citing them sharpens the retail-data-scale framing instead of competing
  with it.
- **The borrowed idea worth noting:** their return-uncertainty penalty is a soft,
  continuous version of what our hard caps do bluntly. If the product ever moves upmarket
  (more data, live feeds), the upgrade path is their formulation — recorded here so the
  future decision cites a source, not a hunch.
- **Convergent conclusion, independent route:** their practical advice (constrain hard,
  model costs, distrust point forecasts) is our M3/M17 measured verdict arrived at from
  the opposite direction — theory-first vs adjudication-first. A good closing citation for
  the constraints section.

[arXiv 2401.05080](https://arxiv.org/abs/2401.05080) ·
[Stanford PDF](https://web.stanford.edu/~boyd/papers/pdf/markowitz.pdf) ·
[SSRN 4695694](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4695694)
