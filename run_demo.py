import argparse
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")              
import matplotlib.pyplot as plt

import bb84

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, "images")
RES = os.path.join(HERE, "results")


def circuit_diagram():
    bits = [0, 1, 1, 0]
    prep = [0, 0, 1, 1]
    meas = [0, 1, 1, 0]
    qc = bb84.build_circuit(bits, prep, meas)
    fig = qc.draw("mpl", fold=-1)
    fig.savefig(os.path.join(IMG, "circuit_example.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)


def qber_chart(res_no_eve, res_eve, n):
    fig, ax = plt.subplots(figsize=(5, 4))
    vals = [res_no_eve["error_rate"] * 100, res_eve["error_rate"] * 100]
    bars = ax.bar(["No Eve", "With Eve"], vals, color=["#2a9d8f", "#e76f51"])
    ax.axhline(25, ls="--", color="gray", lw=1)
    ax.text(1.45, 25.8, "theory: 25%", ha="right", color="gray", fontsize=9)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.8, f"{v:.1f}%", ha="center")
    ax.set_ylabel("Error rate in sifted key (%)")
    ax.set_ylim(0, 40)
    ax.set_title(f"BB84 error rate (Aer simulator, n={n} qubits)")
    fig.tight_layout()
    fig.savefig(os.path.join(IMG, "error_rate.png"), dpi=150)
    plt.close(fig)


def detection_chart(res_eve):
    ks = np.arange(1, 31)
    sim = [bb84.detection_probability(res_eve["alice_key"], res_eve["bob_key"], int(k))
           for k in ks]
    theory = [bb84.theory_detection(k) for k in ks]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(ks, theory, "-", color="gray", label=r"theory: $1-(3/4)^k$")
    ax.plot(ks, sim, "o", color="#e76f51", ms=4, label="simulation")
    ax.set_xlabel("k = number of sifted bits Alice & Bob compare")
    ax.set_ylabel("Probability Eve is detected")
    ax.set_title("More compared bits -> Eve is almost surely caught")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(IMG, "detection_probability.png"), dpi=150)
    plt.close(fig)


def eve_fraction_chart(n, seed):
    fracs = np.linspace(0, 1, 11)
    errs = [bb84.run_bb84(n=n, eve=True, eve_fraction=f, seed=seed)["error_rate"] * 100
            for f in fracs]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(fracs * 100, errs, "o-", color="#264653", label="simulation")
    ax.plot(fracs * 100, fracs * 25, "--", color="gray", label="theory: 0.25 x fraction")
    ax.set_xlabel("% of qubits Eve intercepts")
    ax.set_ylabel("Error rate in sifted key (%)")
    ax.set_title("Error rate grows with how much Eve listens")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(IMG, "eve_fraction.png"), dpi=150)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description="BB84 demo on the Qiskit Aer simulator")
    ap.add_argument("--n", type=int, default=1000, help="number of qubits Alice sends")
    ap.add_argument("--seed", type=int, default=42, help="random seed (reproducible)")
    ap.add_argument("--noise", type=float, default=0.0,
                    help="measurement flip probability, e.g. 0.02")
    ap.add_argument("--no-plots", action="store_true", help="skip saving figures")
    args = ap.parse_args()

    os.makedirs(IMG, exist_ok=True)
    os.makedirs(RES, exist_ok=True)

    clean = bb84.run_bb84(n=args.n, eve=False, noise=args.noise, seed=args.seed)
    attacked = bb84.run_bb84(n=args.n, eve=True, noise=args.noise, seed=args.seed)

    lines = [
        "BB84 results -- Qiskit Aer SIMULATOR (not real quantum hardware)",
        f"qubits sent: {args.n} | seed: {args.seed} | measurement noise: {args.noise}",
        "",
        f"No Eve  : sifted key length = {len(clean['alice_key']):4d}, "
        f"error rate = {clean['error_rate']*100:5.2f}%",
        f"With Eve: sifted key length = {len(attacked['alice_key']):4d}, "
        f"error rate = {attacked['error_rate']*100:5.2f}%  (theory ~25%)",
        "",
        "First 20 sifted bits (No Eve):",
        "  Alice: " + "".join(map(str, clean["alice_key"][:20])),
        "  Bob  : " + "".join(map(str, clean["bob_key"][:20])),
        "First 20 sifted bits (With Eve):",
        "  Alice: " + "".join(map(str, attacked["alice_key"][:20])),
        "  Bob  : " + "".join(map(str, attacked["bob_key"][:20])),
    ]
    report = "\n".join(lines)
    print(report)
    with open(os.path.join(RES, "sample_output.txt"), "w") as f:
        f.write(report + "\n")

    if not args.no_plots:
        circuit_diagram()
        qber_chart(clean, attacked, args.n)
        detection_chart(attacked)
        eve_fraction_chart(args.n, args.seed)
        print("\nFigures saved to ./images")


if __name__ == "__main__":
    main()
