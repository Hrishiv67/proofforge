# NCSEF Region 3A — 2027 entry checklist (Wake County)

Do **not** register until Region 3A posts 2027 dates (usually mid-September on
[ncsef.org/2027-ncsef-regional-fairs](https://ncsef.org/2027-ncsef-regional-fairs/)
and [ncsefreg3a.stemwizard.com](https://ncsefreg3a.stemwizard.com/)).

This project is computational (no humans, animals, or hazardous chemicals). That
keeps the ISEF paperwork small, but you still need an adult sponsor and the
core forms.

## Where you compete
- Wake County (most WCPSS schools) → **NCSEF Region 3A**
- NC School of Science and Math → Region **3B**, not 3A
- State fair: **Saturday, April 3, 2027** at NC State (virtual judging March 30)
- ISEF: only if you place at **state** (NCSEF), not at the regional alone

## People you need
1. **Adult sponsor** — a teacher who reads ISEF rules and signs Forms 1 / 1A / 1B.
2. **Parent/guardian** — signs Form 1B.
3. You — research plan, abstract, poster, live demo (`streamlit run app.py` or `python -m proofforge verify`).

## Forms (run the [ISEF Rules Wizard](https://ruleswizard.societyforscience.org/) to confirm)
Typical set for this project:
- Form **1** (checklist, sponsor)
- Form **1A** (student checklist / research plan)
- Form **1B** (approval, student + parent)
- Abstract (250 words; lead with the novelty sentence and `MATCH: True`)
- Research plan: problem, prior-art gap, method, verifier, results, honest limitations

Form 3 (risk) is usually **not** required for a laptop-only numpy project. If the
wizard asks for it, fill it anyway.

## Research-plan outline (reuse ProofForge docs)
1. Question: can a machine co-invent a short controller **and** a short Lyapunov proof?
2. Method: co-evolutionary GP whose fitness **is** the verifier.
3. Verification: dense grid + local-Lipschitz margin + analytic origin cap.
4. Results: shipped `outputs/certificate.json`, `outputs/proof.png`, generality 3/3.
5. Limitation: not yet interval-arithmetic / SOS (say this out loud; judges respect it).

## What to bring
- Poster with the two-panel proof figure as the centerpiece
- Laptop with the repo + web demo
- One-sentence pitch: *“It invents the law and the proof, then re-checks itself.”*

## Timing
| When | What |
|---|---|
| Mid-September 2026 | Regional dates/deadlines posted — register on STEM Wizard |
| Fall 2026 | Sponsor signs forms **before** you treat later work as “fair research” |
| Winter 2027 | Region 3A fair (date TBA) |
| April 3, 2027 | State NCSEF if you advance |
| May 2027 | ISEF only if selected at state |

## Optional upgrades before the fair (these change prize odds)
- Second plant (cart-pole)
- Barrier / safety certificate (never enter a danger zone)
- Interval-arithmetic check toward a fully formal proof

Skip random online hackathons that require the project to be built during the event.
This codebase is already finished; science fair + Congressional App Challenge are
the contests that allow it.
