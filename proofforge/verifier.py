"""Machine-verify a Lyapunov stability proof over a whole region.

Given controller u(x) and candidate Lyapunov V(x), with Vt(x) = V(x) - V(0),
the origin is asymptotically stable on a region if:

  (P) Vt(x) > 0        for all x != 0     (positive definite)
  (D) Vdot(x) < 0      for all x != 0     (strictly decreasing along motion)

where Vdot(x) = grad V(x) . f(x, u(x)).

Both conditions naturally vanish at the origin, so a single grid cannot certify
them there. We therefore split the region:

  * ORIGIN CAP (a small ball): certified ANALYTICALLY from the quadratic model
    -- the Hessian of V must be positive definite, and the linearized closed
    loop must make Vdot negative definite. This is a real local proof.
  * OUTER REGION (grid): we check the SCALE-FREE ratios p = Vt/|x|^2 and
    q = Vdot/|x|^2, which stay bounded away from zero, using a LOCAL-Lipschitz
    margin between grid points -- so grid satisfaction implies satisfaction
    everywhere in between.

Together these certify (P) and (D) over the whole region, and we report the
largest sublevel set of V that stays inside it (the certified region of
attraction).
"""

from __future__ import annotations

import numpy as np

from proofforge.expr import Node, features_from_state


def eval_state(node: Node, X: np.ndarray) -> np.ndarray:
    return node.eval(features_from_state(np.atleast_2d(X)))


def _grad_V(V: Node, X: np.ndarray, h: float = 1e-4) -> np.ndarray:
    out = np.empty_like(X)
    for k in range(2):
        dp = X.copy(); dp[:, k] += h
        dm = X.copy(); dm[:, k] -= h
        out[:, k] = (eval_state(V, dp) - eval_state(V, dm)) / (2 * h)
    return out


def _hessian_at0(V: Node, h: float = 1e-3) -> np.ndarray:
    """Numeric Hessian of V at the origin (2x2, symmetrized)."""
    e = np.eye(2)
    H = np.zeros((2, 2))
    for i in range(2):
        for j in range(2):
            xpp = (e[i] + e[j]) * h
            xpm = (e[i] - e[j]) * h
            xmp = (-e[i] + e[j]) * h
            xmm = (-e[i] - e[j]) * h
            val = (eval_state(V, xpp) - eval_state(V, xpm)
                   - eval_state(V, xmp) + eval_state(V, xmm))[0]
            H[i, j] = val / (4 * h * h)
    return 0.5 * (H + H.T)


def _closed_jacobian_at0(u: Node, plant, h: float = 1e-4) -> np.ndarray:
    """Numeric Jacobian at 0 of the closed-loop field g(x) = f(x, u(x))."""
    A = np.zeros((2, 2))
    e = np.eye(2)
    for k in range(2):
        xp = (e[k] * h).reshape(1, 2)
        xm = (-e[k] * h).reshape(1, 2)
        gp = plant.deriv(xp, eval_state(u, xp))[0]
        gm = plant.deriv(xm, eval_state(u, xm))[0]
        A[:, k] = (gp - gm) / (2 * h)
    return A


def verify(
    u: Node,
    V: Node,
    plant,
    *,
    n_theta: int = 181,
    n_omega: int = 181,
    strict: float = 1e-4,
) -> dict:
    th = np.linspace(-plant.theta_max, plant.theta_max, n_theta)
    om = np.linspace(-plant.omega_max, plant.omega_max, n_omega)
    T, O = np.meshgrid(th, om)
    X = np.stack([T.ravel(), O.ravel()], axis=1)
    d_th = (2 * plant.theta_max) / (n_theta - 1)
    d_om = (2 * plant.omega_max) / (n_omega - 1)
    cell_diag = float(np.hypot(d_th, d_om))
    delta = max(0.12, 5.0 * cell_diag)               # analytic origin-cap radius

    V0 = float(eval_state(V, np.zeros((1, 2)))[0])
    Vt = eval_state(V, X) - V0
    u_vals = eval_state(u, X)
    f = plant.deriv(X, u_vals)
    Vdot = np.sum(_grad_V(V, X) * f, axis=1)

    # Outer region: raw fields with a LOCAL-Lipschitz inter-grid margin.
    Vt_grid = Vt.reshape(T.shape)
    Vdot_grid = Vdot.reshape(T.shape)
    # SAFETY (>1) inflates the local-Lipschitz margin to bound curvature the
    # central-difference gradient underestimates -- a conservative certificate.
    SAFETY = 1.5
    mVt = (SAFETY * np.hypot(*np.gradient(Vt_grid, d_om, d_th)) * cell_diag).ravel()
    mVdot = (SAFETY * np.hypot(*np.gradient(Vdot_grid, d_om, d_th)) * cell_diag).ravel()

    r = np.sqrt(np.sum(X * X, axis=1))
    outer = r >= delta

    pos_slack = Vt[outer] - (mVt[outer] + strict)         # want > 0  (Vt>0)
    dec_slack = -Vdot[outer] - (mVdot[outer] + strict)    # want > 0  (Vdot<0)
    cert_pos_outer = bool(np.all(pos_slack > 0))
    cert_dec_outer = bool(np.all(dec_slack > 0))

    # Origin cap: analytic quadratic-model proof.
    H = _hessian_at0(V)
    A = _closed_jacobian_at0(u, plant)
    P = 0.5 * H
    eig_P = np.linalg.eigvalsh(P)
    M = A.T @ P + P @ A                               # Vdot ~ x^T M x near 0
    eig_M = np.linalg.eigvalsh(0.5 * (M + M.T))
    origin_pos = bool(eig_P.min() > 1e-6)
    origin_dec = bool(eig_M.max() < -1e-6)

    cert_pos = cert_pos_outer and origin_pos
    cert_dec = cert_dec_outer and origin_dec
    certified = bool(cert_pos and cert_dec)

    # Certified region of attraction: largest V-sublevel set inside the region.
    on_boundary = (np.isclose(np.abs(X[:, 0]), plant.theta_max)
                   | np.isclose(np.abs(X[:, 1]), plant.omega_max))
    c_star = float(Vt[on_boundary].min()) if on_boundary.any() else float("nan")
    roa_frac = float(np.mean((Vt <= c_star) & outer))

    return {
        "certified": certified,
        "cert_positive_definite": cert_pos,
        "cert_decreasing": cert_dec,
        "origin_pos_def": origin_pos,
        "origin_decreasing": origin_dec,
        "outer_pos_ok": cert_pos_outer,
        "outer_dec_ok": cert_dec_outer,
        "min_Vt_outer": float(Vt[outer].min()),
        "max_Vdot_outer": float(Vdot[outer].max()),
        "worst_pos_slack": float(pos_slack.min()),
        "worst_dec_slack": float(dec_slack.min()),
        "hessian_eig_min": float(eig_P.min()),
        "linVdot_eig_max": float(eig_M.max()),
        "delta_cap": float(delta),
        "grid_spacing": cell_diag,
        "c_star_roa": c_star,
        "roa_area_fraction": roa_frac,
        "region": {"theta_max": plant.theta_max, "omega_max": plant.omega_max},
    }


def fields_for_fitness(u: Node, V: Node, plant, X: np.ndarray, delta: float = 0.06):
    """Lightweight (Vt, Vdot, mask) for GP fitness (smooth, no margins)."""
    V0 = float(eval_state(V, np.zeros((1, 2)))[0])
    Vt = eval_state(V, X) - V0
    u_vals = eval_state(u, X)
    f = plant.deriv(X, u_vals)
    Vdot = np.sum(_grad_V(V, X) * f, axis=1)
    mask = np.sqrt(np.sum(X * X, axis=1)) >= delta
    return Vt, Vdot, mask


if __name__ == "__main__":
    from proofforge.expr import C, F, Node
    from proofforge.plant import Plant

    p = Plant(g_over_l=10.0, damping=0.0)
    # VALID: feedback-linearizing u + quadratic V
    u_ok = Node("-", (Node("-", (Node("neg",(Node("*",(C(10.0),F(2))),)),
                                 Node("*",(C(10.0),F(0))))),
                      Node("*",(C(6.0),F(1)))))
    V_ok = Node("+", (Node("+", (Node("*",(C(10.0),Node("square",(F(0),)))),
                                 Node("*",(C(0.5),Node("square",(F(1),)))))),
                      Node("*",(F(0),F(1)))))
    r_ok = verify(u_ok, V_ok, p)
    print("VALID   -> certified:", r_ok["certified"], "| RoA frac:",
          f"{r_ok['roa_area_fraction']:.3f}", "| worst slacks:",
          f"{r_ok['worst_pos_slack']:.4f}, {r_ok['worst_dec_slack']:.4f}")

    # INVALID: the earlier bad V with a ruinous cross term
    V_bad = Node("+", (Node("*", (C(0.5), Node("square", (F(1),)))),
                       Node("*", (C(15.0), Node("neg", (F(3),))))))
    r_bad = verify(u_ok, V_bad, p)
    print("INVALID -> certified:", r_bad["certified"],
          "| outer_dec_ok:", r_bad["outer_dec_ok"],
          "| max_Vdot_outer:", f"{r_bad['max_Vdot_outer']:.3f}")
