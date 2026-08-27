"""End-to-end: invent a proof-carrying controller, certify it, draw the proof."""

from __future__ import annotations

from pathlib import Path

from proofforge.certifier import (
    build_certificate,
    deserialize,
    verify_certificate,
    write_certificate,
)
from proofforge.plant import Plant
from proofforge.synthesizer import synthesize
from proofforge.verifier import verify
from proofforge.visualize import render_proof

ROOT = Path(__file__).resolve().parent.parent
OUTPUTS = ROOT / "outputs"


def invent(plant: Plant | None = None, *, seed: int = 1, pop: int = 200,
           generations: int = 45, out_dir: Path = OUTPUTS, render: bool = True) -> dict:
    plant = plant or Plant()
    res = synthesize(plant, seed=seed, pop=pop, generations=generations, verbose=True)
    champ = res["champion"]
    if champ is None:
        print("\nNo certified controller found this run (try more generations/pop).")
        return {"certified": False}

    rep = verify(champ.u, champ.V, plant)
    cert = build_certificate(champ.u, champ.V, plant, rep)
    path = write_certificate(cert, out_dir)
    fig = None
    if render:
        fig = render_proof(champ.u, champ.V, plant, rep, out_dir / "proof.png",
                           title="ProofForge -- proof-carrying controller")

    print("\n" + "=" * 64)
    print("PROOFFORGE -- PROOF-CARRYING CONTROLLER INVENTED")
    print("=" * 64)
    print("Controller u(theta,omega) =", cert["controller_u"])
    print("Lyapunov   V(theta,omega) =", cert["lyapunov_V"])
    print(f"Total formula size        = {cert['total_nodes']} nodes")
    print(f"First certified at gen    = {res['first_cert_gen']}")
    print(f"Certified                 = {rep['certified']}")
    print(f"Certified safe-region frac= {rep['roa_area_fraction']:.3f}")
    print(f"Certificate               = {path}")
    if fig:
        print(f"Proof figure              = {fig}")
    print("=" * 64 + "\n")
    return cert


def replay(cert_path: Path | None = None, *, out_dir: Path = OUTPUTS,
           render: bool = True) -> dict:
    """Reload the saved certificate, re-verify it, and optionally redraw the figure."""
    import json

    path = Path(cert_path) if cert_path else out_dir / "certificate.json"
    check = verify_certificate(path)
    cert = json.loads(path.read_text(encoding="utf-8"))
    u = deserialize(cert["controller_tree"])
    V = deserialize(cert["lyapunov_tree"])
    pl = cert["plant"]
    plant = Plant(g_over_l=pl["g_over_l"], damping=pl["damping"],
                  theta_max=pl["theta_max"], omega_max=pl["omega_max"])
    rep = verify(u, V, plant)
    fig = None
    if render:
        fig = render_proof(u, V, plant, rep, out_dir / "proof.png",
                           title="ProofForge -- proof-carrying controller")
    check["certificate"] = cert
    check["report"] = rep
    check["figure"] = fig
    return check
