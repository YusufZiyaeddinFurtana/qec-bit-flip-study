"""Readable, headless, exportable scientific plots."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from .model import logical_error_theory


def plot_results(root: Path, rows: list[dict]) -> None:
    output = root / "figures"
    output.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 11,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.titleweight": "bold", "axes.labelcolor": "#25364a",
        "text.color": "#25364a", "svg.fonttype": "none",
        "svg.hashsalt": "qec-bit-flip-study",
    })
    dense = np.linspace(0, 0.5, 501)
    for pauli, filename, title, subtitle, color in (
        ("X", "bit_flip_performance", "Correcting independent bit flips",
         "Three-qubit repetition code | probe: $|0\\rangle$", "#087f8c"),
        ("Z", "phase_flip_limitation", "The same code misses phase flips",
         "Unmodified bit-flip code | probe: $|+\\rangle$", "#a64b2a"),
    ):
        selected = [row for row in rows if row["noise"] == pauli]
        probabilities = np.array([row["physical_error_probability"] for row in selected])
        fig, axis = plt.subplots(figsize=(9, 6))
        fig.subplots_adjust(left=0.12, right=0.96, top=0.79, bottom=0.22)
        fig.text(0.12, 0.94, title, fontsize=19, weight="bold")
        fig.text(0.12, 0.875, subtitle, fontsize=11)
        axis.plot(dense, dense, "--", color="#697586", lw=1.8, label="Uncoded theory: p")
        axis.plot(dense, [logical_error_theory(p, pauli) for p in dense],
                  color=color, lw=2.5, label="Coded theory")
        for prefix, marker, shade, label in (
            ("uncoded", "s", "#697586", "Uncoded Monte Carlo"),
            ("logical", "o", color, "Coded Monte Carlo"),
        ):
            rates = np.array([row[f"{prefix}_rate"] for row in selected])
            lows = np.array([row[f"{prefix}_ci_low"] for row in selected])
            highs = np.array([row[f"{prefix}_ci_high"] for row in selected])
            axis.errorbar(probabilities, rates,
                          yerr=np.maximum(0, np.vstack((rates - lows, highs - rates))),
                          fmt=marker, markersize=4.5, capsize=2.5, color=shade,
                          markerfacecolor="white", label=label, zorder=3)
        axis.set(xlabel=f"Physical {pauli}-error probability per qubit, p",
                 ylabel=f"Logical {pauli}-error probability after recovery",
                 xlim=(-0.006, 0.51), ylim=(-0.006, 0.54))
        axis.grid(alpha=0.18)
        axis.legend(loc="upper left", fontsize=9.5, frameon=False)
        shots = selected[0]["shots"]
        fig.text(0.12, 0.105,
                 f"{shots:,} trials / point. Error bars: pointwise 95% Wilson intervals.",
                 fontsize=9, color="#526174")
        fig.text(0.12, 0.063,
                 "One noise step; independent identical errors; ideal encoding and recovery.",
                 fontsize=9, color="#526174")
        fig.savefig(output / f"{filename}.png", dpi=190, facecolor="white")
        svg = output / f"{filename}.svg"
        fig.savefig(svg, facecolor="white", metadata={"Date": None})
        svg.write_text("\n".join(line.rstrip() for line in
                                 svg.read_text(encoding="utf-8").splitlines()) + "\n",
                       encoding="utf-8")
        plt.close(fig)
