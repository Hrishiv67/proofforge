"""Emit and re-check a proof-carrying controller certificate."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from proofforge.expr import Node
from proofforge.plant import Plant
from proofforge.verifier import verify


def serialize(node: Node) -> dict:
    d = {"op": node.op}
    if node.op == "const":
        d["value"] = node.value
    if node.op == "feat":
        d["feat"] = node.feat
    if node.children:
        d["children"] = [serialize(c) for c in node.children]
    return d


def deserialize(d: dict) -> Node:
    kids = tuple(deserialize(c) for c in d.get("children", []))
    return Node(op=d["op"], children=kids,
                value=float(d.get("value", 0.0)), feat=int(d.get("feat", -1)))


def build_certificate(u: Node, V: Node, plant: Plant, report: dict) -> dict:
    return {
        "item_name": "ProofForge proof-carrying controller",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "system": "inverted pendulum (open-loop unstable)",
        "controller_u": u.to_math(),
        "lyapunov_V": V.to_math(),
        "controller_tree": serialize(u),
        "lyapunov_tree": serialize(V),
        "controller_nodes": u.size(),
        "lyapunov_nodes": V.size(),
        "total_nodes": u.size() + V.size(),
        "plant": {
            "g_over_l": plant.g_over_l, "damping": plant.damping,
            "theta_max": plant.theta_max, "omega_max": plant.omega_max,
        },
        "verification": {
            "certified": report["certified"],
            "positive_definite": report["cert_positive_definite"],
            "decreasing": report["cert_decreasing"],
            "origin_pos_def": report["origin_pos_def"],
            "origin_decreasing": report["origin_decreasing"],
            "worst_pos_slack": report["worst_pos_slack"],
            "worst_dec_slack": report["worst_dec_slack"],
            "hessian_eig_min": report["hessian_eig_min"],
            "lin_Vdot_eig_max": report["linVdot_eig_max"],
            "grid_spacing": report["grid_spacing"],
            "origin_cap_radius": report["delta_cap"],
            "certified_region_of_attraction_c": report["c_star_roa"],
            "roa_area_fraction": report["roa_area_fraction"],
            "method": ("dense-grid local-Lipschitz margin outside an analytic "
                       "linearization cap at the origin"),
        },
    }


def write_certificate(cert: dict, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "certificate.json"
    path.write_text(json.dumps(cert, indent=2), encoding="utf-8")
    return path


def verify_certificate(path: str | Path) -> dict:
    """Reload a certificate's trees and INDEPENDENTLY re-run verification."""
    cert = json.loads(Path(path).read_text(encoding="utf-8"))
    u = deserialize(cert["controller_tree"])
    V = deserialize(cert["lyapunov_tree"])
    pl = cert["plant"]
    plant = Plant(g_over_l=pl["g_over_l"], damping=pl["damping"],
                  theta_max=pl["theta_max"], omega_max=pl["omega_max"])
    rep = verify(u, V, plant)
    return {
        "controller_u": u.to_math(),
        "lyapunov_V": V.to_math(),
        "claimed_certified": cert["verification"]["certified"],
        "recomputed_certified": rep["certified"],
        "match": bool(cert["verification"]["certified"] == rep["certified"]),
        "worst_pos_slack": rep["worst_pos_slack"],
        "worst_dec_slack": rep["worst_dec_slack"],
        "roa_area_fraction": rep["roa_area_fraction"],
    }


if __name__ == "__main__":
    # Build a certificate from a hand controller, then re-verify it.
    from proofforge.expr import C, F
    p = Plant()
    u = Node("-", (Node("neg", (Node("*", (C(14.0), F(0))),)), Node("*", (C(11.0), F(1)))))
    V = Node("+", (Node("+", (Node("*", (C(20.0), Node("square", (F(0),)))),
                              Node("square", (F(1),)))),
                   Node("*", (C(1.3), Node("*", (F(0), F(1)))))))
    rep = verify(u, V, p)
    cert = build_certificate(u, V, p, rep)
    out = Path(__file__).resolve().parent.parent / "outputs"
    path = write_certificate(cert, out)
    check = verify_certificate(path)
    print("wrote", path.name, "| certified:", cert["verification"]["certified"])
    print("re-verify match:", check["match"], "| recomputed:", check["recomputed_certified"])
