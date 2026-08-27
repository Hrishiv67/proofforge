"""Command-line interface for ProofForge."""

from __future__ import annotations

import argparse

from proofforge.certifier import verify_certificate
from proofforge.orchestrator import OUTPUTS, invent
from proofforge.plant import Plant


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="proofforge", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    pi = sub.add_parser("invent", help="invent + certify a proof-carrying controller")
    pi.add_argument("--seed", type=int, default=1)
    pi.add_argument("--pop", type=int, default=200)
    pi.add_argument("--generations", type=int, default=45)
    pi.add_argument("--gravity", type=float, default=10.0, help="g/l of the pendulum")

    sub.add_parser("smoke", help="fast run to confirm everything is wired up")

    pv = sub.add_parser("verify", help="independently re-check outputs/certificate.json")
    pv.add_argument("--path", default=str(OUTPUTS / "certificate.json"))

    pg = sub.add_parser("generality", help="re-invent a proof across several systems")
    pg.add_argument("--gravities", default="6,10,16")

    args = p.parse_args(argv)

    if args.cmd == "invent":
        invent(Plant(g_over_l=args.gravity), seed=args.seed, pop=args.pop,
               generations=args.generations)
        return 0
    if args.cmd == "smoke":
        invent(Plant(), seed=1, pop=160, generations=30)
        return 0
    if args.cmd == "verify":
        r = verify_certificate(args.path)
        print("Controller:", r["controller_u"])
        print("Lyapunov  :", r["lyapunov_V"])
        print("claimed certified   :", r["claimed_certified"])
        print("recomputed certified:", r["recomputed_certified"])
        print("MATCH               :", r["match"])
        return 0 if r["match"] else 1
    if args.cmd == "generality":
        gs = [float(x) for x in args.gravities.split(",")]
        wins = 0
        for g in gs:
            print(f"\n########## SYSTEM g/l = {g} ##########")
            cert = invent(Plant(g_over_l=g), seed=1, pop=180, generations=40, render=False)
            wins += int(cert.get("verification", {}).get("certified", cert.get("certified", False)))
        print(f"\nGENERALITY: certified {wins}/{len(gs)} distinct systems.")
        return 0
    return 1
