"""ProofForge web demo — invent a controller, then re-check its proof."""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from proofforge.orchestrator import OUTPUTS, invent, replay
from proofforge.plant import Plant

st.set_page_config(
    page_title="ProofForge — AI that ships its own proof",
    page_icon="⚖️",
    layout="wide",
)

PROOF_PNG = OUTPUTS / "proof.png"
CERT_JSON = OUTPUTS / "certificate.json"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Fraunces:opsz,wght@9..144,500;9..144,700&family=Source+Sans+3:wght@400;600&display=swap');
html, body, [class*="css"] { font-family: "Source Sans 3", sans-serif; }
.block-container { padding-top: 1.4rem; max-width: 1180px; }
h1, h2, h3 { font-family: Fraunces, Georgia, serif !important; letter-spacing: -0.02em; }
.pf-kicker {
  font-family: "IBM Plex Mono", monospace;
  font-size: 0.78rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #c4a35a;
  margin-bottom: 0.35rem;
}
.pf-hero {
  border: 1px solid #3a4458;
  background: linear-gradient(180deg, #1c2230 0%, #161b26 100%);
  padding: 1.25rem 1.4rem 1.1rem;
  margin-bottom: 1rem;
}
.pf-card {
  border: 1px solid #3a4458;
  background: #1c2230;
  padding: 0.9rem 1rem;
  min-height: 7.2rem;
}
.pf-card label {
  font-family: "IBM Plex Mono", monospace;
  font-size: 0.72rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #c4a35a;
  display: block;
  margin-bottom: 0.45rem;
}
.pf-math {
  font-family: "IBM Plex Mono", monospace;
  font-size: 0.95rem;
  color: #f4efe4;
  word-break: break-word;
}
.pf-stamp {
  font-family: "IBM Plex Mono", monospace;
  font-weight: 600;
  letter-spacing: 0.12em;
  border: 2px solid;
  display: inline-block;
  padding: 0.35rem 0.7rem;
  transform: rotate(-2deg);
}
.ok { color: #7dcea0; border-color: #7dcea0; }
.bad { color: #e07a7a; border-color: #e07a7a; }
.pf-foot {
  font-family: "IBM Plex Mono", monospace;
  font-size: 0.75rem;
  color: #8b93a7;
  margin-top: 1.4rem;
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

st.markdown('<div class="pf-kicker">Self-certifying control · inverted pendulum</div>',
            unsafe_allow_html=True)
st.title("ProofForge")
st.markdown(
    '<div class="pf-hero">'
    "Would you trust a controller that only <em>tested well</em>? "
    "ProofForge invents a short control law <strong>and</strong> a short Lyapunov "
    "proof, then machine-checks the proof over a whole region — not just a few trials. "
    "Replay the saved certificate in seconds, or invent a new pair on this page."
    "</div>",
    unsafe_allow_html=True,
)


def _show_formulas(u: str, v: str, match: bool | None) -> None:
    c1, c2, c3 = st.columns([1.35, 1.35, 0.7])
    with c1:
        st.markdown(
            f'<div class="pf-card"><label>Controller u(θ, ω)</label>'
            f'<div class="pf-math">{u}</div></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f'<div class="pf-card"><label>Lyapunov proof V(θ, ω)</label>'
            f'<div class="pf-math">{v}</div></div>',
            unsafe_allow_html=True,
        )
    with c3:
        if match is True:
            stamp = '<div class="pf-stamp ok">MATCH: TRUE</div>'
        elif match is False:
            stamp = '<div class="pf-stamp bad">MATCH: FALSE</div>'
        else:
            stamp = '<div class="pf-stamp">NOT YET CHECKED</div>'
        st.markdown(
            f'<div class="pf-card"><label>Independent re-check</label>{stamp}</div>',
            unsafe_allow_html=True,
        )


with st.sidebar:
    st.markdown("**What to run**")
    st.caption(
        "Cloud hosts time out on a full search. Replay is the demo. "
        "Invent is optional and capped."
    )
    generations = st.slider("Invent generations", 8, 30, 12)
    pop = st.slider("Population size", 40, 120, 80, step=10)
    seed = st.number_input("Random seed", min_value=1, max_value=9999, value=1, step=1)
    gravity = st.selectbox("Pendulum g/ℓ", [6.0, 10.0, 16.0], index=1)

col_a, col_b = st.columns(2)
replay_clicked = col_a.button("Replay last certificate", type="primary",
                              use_container_width=True)
invent_clicked = col_b.button("Invent a new controller + proof",
                              use_container_width=True)

if "result" not in st.session_state:
    st.session_state.result = None

if replay_clicked:
    if not CERT_JSON.exists():
        st.error("No certificate on disk yet. Run Invent first.")
    else:
        with st.spinner("Reloading the saved proof and re-deriving it from scratch…"):
            st.session_state.result = replay(CERT_JSON, out_dir=OUTPUTS, render=True)

if invent_clicked:
    with st.spinner(
        "Searching for a short controller and a short proof. "
        "This can take under a minute on a laptop, longer on a free host…"
    ):
        cert = invent(
            Plant(g_over_l=float(gravity)),
            seed=int(seed),
            pop=int(pop),
            generations=int(generations),
            out_dir=OUTPUTS,
            render=True,
        )
        if cert.get("certified") is False and "controller_u" not in cert:
            st.session_state.result = {"match": False, "certificate": None,
                                       "controller_u": None}
        else:
            st.session_state.result = replay(CERT_JSON, out_dir=OUTPUTS, render=True)

res = st.session_state.result
if res and res.get("certificate"):
    cert = res["certificate"]
    _show_formulas(cert["controller_u"], cert["lyapunov_V"], res.get("match"))
    v = cert.get("verification", {})
    m1, m2, m3 = st.columns(3)
    m1.metric("Certified", str(v.get("certified")))
    m2.metric("Safe-region fraction", f"{v.get('roa_area_fraction', 0):.3f}")
    m3.metric("Formula size (nodes)", cert.get("total_nodes"))
elif CERT_JSON.exists() and not replay_clicked and not invent_clicked:
    import json
    cert = json.loads(CERT_JSON.read_text(encoding="utf-8"))
    _show_formulas(cert["controller_u"], cert["lyapunov_V"], None)
    st.info("Click **Replay last certificate** to independently re-check this result.")

if PROOF_PNG.exists():
    st.subheader("The proof figure")
    st.image(str(PROOF_PNG), use_container_width=True)
    st.caption(
        "Left: closed-loop trajectories spiral to upright inside the certified "
        "region. Right: the Lyapunov energy bowl — red would mark a violation; "
        "there should be none."
    )

st.markdown(
    '<p class="pf-foot">Offline core: Python + NumPy + Matplotlib. '
    "The proof is a dense-grid check with a local-Lipschitz margin plus an "
    "analytic origin cap — stronger than testing, not yet a fully formal SOS proof.</p>",
    unsafe_allow_html=True,
)
