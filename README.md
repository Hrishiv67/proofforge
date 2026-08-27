# ProofForge

**One sentence:** A machine that automatically invents a compact control law *and*
a compact mathematical proof that the law works — together — and machine-verifies
the proof over an entire region of operation, not just by testing.

See [`DOCUMENTATION.md`](DOCUMENTATION.md) for the full writeup.

- **Code:** https://github.com/Hrishiv67/proofforge
- **Live demo:** https://proofforge.streamlit.app
- **DOI:** https://doi.org/10.5281/zenodo.22134279
- **Local web demo:** `streamlit run app.py`

**Kid version:** A pole falls over on its own. ProofForge invents a short formula
that holds it upright, *and* a second short formula that **proves** it can never
fall — like handing in a math answer with the work that shows it must be right.

The core runs entirely on your laptop. **Python + NumPy + Matplotlib** (Streamlit
only for the optional web UI). No datasets, no external APIs.

---

## Why this is different (the novelty, stated honestly)

Everyone can train a controller and then *test* it. The open gap is producing the
controller **together with a machine-checkable proof**, both as short,
human-readable formulas. Nearest prior work and how ProofForge differs:

| Prior work | What it does | ProofForge's difference |
|---|---|---|
| Neural Lyapunov Control (Chang et al., 2019) | co-learns controller + Lyapunov net | ProofForge outputs **symbolic, human-readable** formulas, not black-box nets, and minimizes their **size** |
| VIPER (Bastani et al., 2018) | extracts + verifies a policy as a decision tree | ProofForge **co-invents the proof** (a Lyapunov certificate), not just the policy |
| SOS / Lyapunov synthesis | finds certificates for a *given* controller/form | ProofForge **searches controller and certificate jointly** and returns the **shortest** pair |
| Symbolic regression (PySR, Eureqa, SINDy) | fits short formulas to *data* | ProofForge's formulas carry a **verified stability guarantee**, not a data fit |

**The point of novelty:** *symbolic* + *jointly length-minimal law-and-proof* +
*verified over a region* + *certificate as the deliverable.* Nobody owns that exact
intersection.

## What it produces

For an inverted pendulum (open-loop unstable — it falls over), ProofForge invents:
- a controller `u(theta, omega)` that balances it, and
- a Lyapunov function `V(theta, omega)` proving it,

then **verifies** `V > 0` and `dV/dt < 0` everywhere in a region (so the pole
provably returns to upright), and writes a re-checkable certificate + a figure.

Example invented result:
```
u(theta,omega) = sin(theta) - 22.79*theta - 7.978*omega
V(theta,omega) = 16.33*theta^2 + 1.86*omega^2 + 0.519*theta*omega
-> CERTIFIED over |theta|<=1 rad, |omega|<=2 rad/s
```

## Run it

**Web demo (browser):**
```bat
python -m pip install -r requirements.txt
set PYTHONPATH=%CD%
streamlit run app.py
```
Click **Replay last certificate** to re-check the shipped proof in seconds.
**Invent** is optional and capped so a free host does not time out.

**Command line:**
```bat
run.bat
```
or
```bat
python -m pip install -r requirements.txt
set PYTHONPATH=%CD%
python -m proofforge invent --generations 45
python -m proofforge verify
python -m proofforge generality --gravities 6,10,16
```

| Command | What it does |
|---|---|
| `python -m proofforge smoke` | fast end-to-end sanity run |
| `python -m proofforge invent` | invent + certify a proof-carrying controller, draw the proof |
| `python -m proofforge verify` | independently re-check `outputs/certificate.json` |
| `python -m proofforge generality --gravities 6,10,16` | re-invent a fresh proof for several different systems |

## How it works

1. **plant.py** — the inverted pendulum (open-loop unstable).
2. **expr.py** — compact symbolic trees over `theta, omega, sin(theta), cos(theta)-1`.
3. **verifier.py** — the core: certifies `V>0` and `dV/dt<0` over the region using a
   **dense grid with a local-Lipschitz margin** between grid points, plus an
   **analytic linearization proof** in a small cap at the origin (where the
   conditions naturally vanish). Reports the certified region of attraction.
4. **synthesizer.py** — **co-evolutionary GP**: a genome is a *pair* (u, V). Fitness
   **is the verifier's own margins**, so the search directly optimizes provability;
   once certifiable, it minimizes formula size (minimum description length).
5. **certifier.py** — serializes (u, V) into a certificate; `verify` reloads and
   independently re-checks it.
6. **visualize.py** — the phase portrait (everything spirals to upright) and the
   Lyapunov "bowl" with a banner confirming no violation regions.

## Honesty about the guarantee

The proof is verified on a **dense grid with a conservative local-Lipschitz margin**
(a strong empirical certificate) plus an **analytic** proof at the origin. This is
much stronger than testing, but it is **not yet fully formal**. The clean next step —
and a great "future work" line for any writeup — is to replace the grid check with
**interval arithmetic** or a **sum-of-squares (SOS)** proof for a machine-checkable,
fully rigorous certificate.

## Dependencies
`numpy`, `matplotlib`, and `streamlit` for the web demo. The invent/verify
pipeline itself does not need the internet.
