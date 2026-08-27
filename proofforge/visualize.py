"""Figures that make the proof visible: the pole balances, and V only ever
goes downhill."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from proofforge.expr import Node
from proofforge.verifier import _grad_V, eval_state


def _grids(u: Node, V: Node, plant, n=181):
    th = np.linspace(-plant.theta_max, plant.theta_max, n)
    om = np.linspace(-plant.omega_max, plant.omega_max, n)
    T, O = np.meshgrid(th, om)
    X = np.stack([T.ravel(), O.ravel()], axis=1)
    V0 = float(eval_state(V, np.zeros((1, 2)))[0])
    Vt = (eval_state(V, X) - V0).reshape(T.shape)
    f = plant.deriv(X, eval_state(u, X))
    Vdot = np.sum(_grad_V(V, X) * f, axis=1).reshape(T.shape)
    return th, om, T, O, Vt, Vdot


def render_proof(u: Node, V: Node, plant, report: dict, out_path, *, title="ProofForge"):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    th, om, T, O, Vt, Vdot = _grids(u, V, plant)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.6))

    # ---- Left: phase portrait, closed-loop trajectories converge to upright ---
    U = plant.deriv(np.stack([T.ravel(), O.ravel()], axis=1),
                    eval_state(u, np.stack([T.ravel(), O.ravel()], axis=1)))
    dth = U[:, 0].reshape(T.shape)
    dom = U[:, 1].reshape(T.shape)
    ax1.streamplot(th, om, dth, dom, density=1.1, color="#adb5bd", linewidth=0.7,
                   arrowsize=0.7)
    rng = np.random.default_rng(0)
    for _ in range(9):
        s0 = [rng.uniform(-plant.theta_max, plant.theta_max),
              rng.uniform(-plant.omega_max, plant.omega_max)]
        traj = plant.rollout(s0, lambda X: eval_state(u, X), steps=500)
        ax1.plot(traj[:, 0], traj[:, 1], color="#1c7ed6", lw=1.3, alpha=0.9)
    # certified region of attraction contour {V = c*}
    c = report.get("c_star_roa")
    if c and np.isfinite(c):
        ax1.contour(T, O, Vt, levels=[c], colors="#2f9e44", linewidths=2.0)
    ax1.plot(0, 0, "k*", ms=13)
    ax1.set_xlabel("theta  (angle from upright)")
    ax1.set_ylabel("omega  (angular velocity)")
    ax1.set_title("Closed loop: every start spirals to UPRIGHT\n"
                  "(green = certified safe region)")

    # ---- Right: the proof -- V level sets + where Vdot<0 (must be everywhere) --
    cf = ax2.contourf(T, O, Vt, levels=18, cmap="viridis", alpha=0.9)
    plt.colorbar(cf, ax=ax2, label="V (energy of the proof)")
    # Shade any region where Vdot >= 0 (a violation) in red -- should be none.
    viol = (Vdot >= 0).astype(float)
    ax2.contourf(T, O, viol, levels=[0.5, 1.5], colors=["#e03131"], alpha=0.55)
    ax2.contour(T, O, Vdot, levels=[0.0], colors="white", linewidths=1.0)
    ax2.plot(0, 0, "w*", ms=13)
    ax2.set_xlabel("theta")
    ax2.set_ylabel("omega")
    status = "CERTIFIED: V>0 and dV/dt<0 everywhere" if report.get("certified") \
        else "NOT certified"
    ax2.set_title(f"The proof: V downhill everywhere\n{status}")

    fig.suptitle(title, fontsize=13)
    fig.tight_layout()
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=140)
    plt.close(fig)
    return out_path
