"""Monte Carlo error sampling, confidence intervals, and reproducible outputs."""

import csv
import json
import platform
from pathlib import Path
from statistics import NormalDist

import matplotlib
import numpy as np

from .model import (
    PLUS,
    ZERO,
    logical_error_theory,
    logical_output,
    pure_state_fidelity,
    validate_probability,
)


DEFAULT_SEED = 20261031
DEFAULT_SHOTS = 200_000
PROBABILITIES = (
    0.0, 0.005, 0.01, 0.02, 0.03, 0.05, 0.075, 0.1,
    0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5,
)


def wilson_interval(errors: int, shots: int) -> tuple[float, float]:
    """Two-sided 95% Wilson score interval for a binomial proportion."""
    if shots <= 0 or not 0 <= errors <= shots:
        raise ValueError("Need shots > 0 and 0 <= errors <= shots.")
    z = NormalDist().inv_cdf(0.975)
    rate = errors / shots
    denominator = 1 + z**2 / shots
    center = (rate + z**2 / (2 * shots)) / denominator
    half_width = z * np.sqrt(
        rate * (1 - rate) / shots + z**2 / (4 * shots**2)
    ) / denominator
    low = max(0.0, float(center - half_width))
    high = min(1.0, float(center + half_width))
    # Preserve exact endpoints instead of tiny floating-point roundoff.
    return (0.0 if errors == 0 else low, 1.0 if errors == shots else high)


def count_errors(
    rng: np.random.Generator, p: float, shots: int, pauli: str
) -> tuple[int, int]:
    """Sample physical error masks, rather than drawing from the target formula.

The uncoded baseline uses a separate sample at the same physical p. Memory
is bounded by processing blocks; changing the block size changes RNG ordering.
"""
    validate_probability(p)
    if shots <= 0 or pauli not in ("X", "Z"):
        raise ValueError("Need positive shots and noise type X or Z.")
    uncoded_errors = logical_errors = 0
    for offset in range(0, shots, 100_000):
        block = min(100_000, shots - offset)
        uncoded_errors += int(np.count_nonzero(rng.random(block) < p))
        masks = rng.random((block, 3)) < p
        weight = masks.sum(axis=1)
        failed = weight >= 2 if pauli == "X" else weight % 2 == 1
        logical_errors += int(np.count_nonzero(failed))
    return uncoded_errors, logical_errors


def run_experiments(shots: int, seed: int) -> list[dict]:
    rng = np.random.Generator(np.random.PCG64(seed))
    rows = []
    for pauli in ("X", "Z"):
        probe = ZERO if pauli == "X" else PLUS
        for p in PROBABILITIES:
            uncoded, logical = count_errors(rng, p, shots, pauli)
            uncoded_ci = wilson_interval(uncoded, shots)
            logical_ci = wilson_interval(logical, shots)
            exact = 1 - pure_state_fidelity(logical_output(probe, p, pauli), probe)
            theory = logical_error_theory(p, pauli)
            if not np.isclose(exact, theory, atol=1e-12, rtol=0):
                raise RuntimeError("Quantum channel and analytical model disagree.")
            rows.append({
                "noise": pauli,
                "physical_error_probability": p,
                "probe_state": "|0>" if pauli == "X" else "|+>",
                "shots": shots,
                "uncoded_errors": uncoded,
                "uncoded_rate": uncoded / shots,
                "uncoded_ci_low": uncoded_ci[0],
                "uncoded_ci_high": uncoded_ci[1],
                "logical_errors": logical,
                "logical_rate": logical / shots,
                "logical_ci_low": logical_ci[0],
                "logical_ci_high": logical_ci[1],
                "theoretical_logical_rate": theory,
                "exact_quantum_infidelity": float(exact),
            })
    return rows


def write_results(root: Path, rows: list[dict], shots: int, seed: int) -> None:
    directory = root / "results"
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / "performance.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    metadata = {
        "seed": seed,
        "bit_generator": "PCG64",
        "shots_per_noise_type_per_probability": shots,
        "probabilities": list(PROBABILITIES),
        "noise_types": ["X", "Z"],
        "noise_rounds": 1,
        "interval": "pointwise 95% Wilson score, two-sided",
        "python": platform.python_version(),
        "numpy": np.__version__,
        "matplotlib": matplotlib.__version__,
        "platform": platform.system(),
        "architecture": platform.machine(),
    }
    (directory / "metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# Generated results", "",
        f"Seed: `{seed}`. Trials per noise type and probability: **{shots:,}**.", "",
        "Intervals below are pointwise 95% Wilson intervals for the coded rate.",
        "These are simulated estimates; the exact quantum calculation is separate.", "",
        "| Noise / probe | Physical p | Uncoded estimate | Coded estimate | Coded 95% interval | Theory |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        if row["physical_error_probability"] not in (0.01, 0.05, 0.1, 0.2):
            continue
        probe_label = row["probe_state"].replace("|", "\\|")
        lines.append(
            f"| {row['noise']} / {probe_label} | "
            f"{row['physical_error_probability']:.2f} | "
            f"{row['uncoded_rate']:.5f} | {row['logical_rate']:.5f} | "
            f"[{row['logical_ci_low']:.5f}, {row['logical_ci_high']:.5f}] | "
            f"{row['theoretical_logical_rate']:.5f} |"
        )
    lines += [
        "", "All entries are probabilities, not percentages.", "",
        "The interval is a repeated-sampling uncertainty statement, not a 95%",
        "probability assigned to the fixed true parameter. Intervals are not",
        "simultaneous across the sweep, and individual intervals can miss the theory.", "",
        "See `performance.csv` for every count, interval, and exact quantum check.",
        "The X probe is |0>; the Z probe is |+> so phase errors are observable.", "",
    ]
    (directory / "summary.md").write_text("\n".join(lines), encoding="utf-8")
