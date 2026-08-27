# ProofForge — Project Documentation

## 1. Purpose
ProofForge automatically invents a **control law** for an unstable physical system
**and a machine-checkable mathematical proof that the law works** — both expressed as
short, human-readable formulas — then **verifies the proof over an entire region** of
operation and emits a certificate anyone can independently re-check. It is a step
toward *self-certifying* control: AI controllers that arrive with their own proof of
safety, instead of only a passing test.

## 2. Target audience
- Students and researchers in **control theory, robotics, and trustworthy/safe AI**.
- Anyone who needs a controller with a **guarantee** (aerospace, medical devices,
  autonomous systems) rather than a statistical pass rate.
- Educators demonstrating **Lyapunov stability** and **symbolic/evolutionary search**.

## 3. Main features
- **Co-invents** a controller `u(x)` and a Lyapunov certificate `V(x)` *together* as
  compact symbolic formulas.
- **Region-wide verification** (not sampling): a dense grid with a conservative
  local-Lipschitz margin, plus an analytic linearization proof at the equilibrium.
- **Self-verifying certificates**: `verify` reloads the saved formulas and
  recomputes the proof from scratch.
- **Minimum-description-length pressure**: once a proof exists, the search shrinks the
  formulas.
- **Generality**: the same program re-invents a certified controller+proof for
  different systems (demonstrated on three pendulums).
- **Visual proof**: a two-panel figure (trajectories converging + the Lyapunov "bowl"
  with a no-violations banner).
- **Pure Python** (NumPy + Matplotlib), fully offline, reproducible from a seed.

## 4. How it works (architecture)
| Module | Role |
|---|---|
| `proofforge/plant.py` | The system: an inverted pendulum (open-loop unstable). |
| `proofforge/expr.py` | Compact symbolic expression trees over the state features. |
| `proofforge/verifier.py` | Certifies `V>0` and `dV/dt<0` over the region (grid + local-Lipschitz margin + analytic origin cap); reports the certified region of attraction. |
| `proofforge/synthesizer.py` | Co-evolutionary genetic programming over pairs `(u, V)`; **the verifier is the fitness function**; then minimizes formula size. |
| `proofforge/certifier.py` | Serializes `(u, V)` to a JSON certificate; independently re-verifies it. |
| `proofforge/visualize.py` | The phase-portrait + Lyapunov proof figure. |
| `proofforge/orchestrator.py`, `cli.py` | End-to-end runner and command-line interface. |
| `app.py` | Streamlit web demo: replay the saved certificate or invent a new pair. |

## 5. Installation guide
**Prerequisites:** Python 3.10+ (developed on 3.14), pip.

**Windows (PowerShell or CMD):**
```bat
cd proofforge
python -m pip install -r requirements.txt
set PYTHONPATH=%CD%
```

**macOS / Linux:**
```bash
cd proofforge
python3 -m pip install -r requirements.txt
export PYTHONPATH=$PWD
```

Core dependencies are `numpy` and `matplotlib`. The optional web UI also needs
`streamlit`. No datasets or external APIs required.

## 6. User manual (commands)
Run from the `proofforge/` folder with `PYTHONPATH` set (or just double-click
`run.bat` on Windows).

| Command | What it does | Typical runtime |
|---|---|---|
| `streamlit run app.py` | Browser demo: replay the shipped certificate, or invent a new pair. | replay: seconds |
| `python -m proofforge smoke` | Fast end-to-end sanity run. | seconds |
| `python -m proofforge invent` | Invents + certifies a controller and proof; writes `outputs/certificate.json` and `outputs/proof.png`. | ~1 min |
| `python -m proofforge verify` | **Independently re-checks** the saved certificate; prints `MATCH`. | seconds |
| `python -m proofforge generality --gravities 6,10,16` | Re-invents a certified controller+proof for several different systems. | a few min |

**Options:** `invent` accepts `--seed`, `--pop`, `--generations`, `--gravity`.

**Example session:**
```bat
python -m proofforge invent
python -m proofforge verify
```
Expected: `invent` prints the two invented formulas and `Certified = True`; `verify`
prints `MATCH : True`.

## 7. Outputs
- `outputs/certificate.json` — the controller, the Lyapunov proof, the full
  verification report (slacks, region of attraction, method), re-loadable.
- `outputs/proof.png` — the two-panel proof figure.
- `outputs/results_generality.txt` — the multi-system results.

## 8. Configuration & reproducibility
All randomness derives from a single `--seed`; the same seed reproduces the same
result. Search effort is tuned by `--pop` (population) and `--generations`.

## 9. Honest limitations
The certificate is a **dense-grid check with a conservative local-Lipschitz margin**
plus an **analytic** proof at the equilibrium. This is far stronger than testing but is
**not yet fully formal** (the margin assumes the grid resolves the field's local
variation). The demo is 2-D. Planned next steps: interval-arithmetic / sum-of-squares
verification (fully formal), a safety/barrier certificate, a cart-pole system, and
bounded-disturbance robustness.

## 10. References
1. Khalil, H. K. *Nonlinear Systems*, 3rd ed. Prentice Hall (2002).
2. Chang, Roohi, Gao. Neural Lyapunov Control. *NeurIPS* (2019).
3. Bastani, Pu, Solar-Lezama. Verifiable RL via Policy Extraction (VIPER). *NeurIPS* (2018).
4. Parrilo. Semidefinite programming relaxations for semialgebraic problems. *Math. Programming* (2003).
5. Koza. *Genetic Programming.* MIT Press (1992).
