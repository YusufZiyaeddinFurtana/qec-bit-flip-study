"""Run with python -m qec_study."""

import argparse
from pathlib import Path

from .experiment import DEFAULT_SEED, DEFAULT_SHOTS, run_experiments, write_results
from .plotting import plot_results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shots", type=int, default=DEFAULT_SHOTS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--output", type=Path, default=Path("."))
    args = parser.parse_args()
    if args.shots <= 0 or args.seed < 0:
        parser.error("--shots must be positive and --seed must be nonnegative")
    rows = run_experiments(args.shots, args.seed)
    write_results(args.output, rows, args.shots, args.seed)
    plot_results(args.output, rows)
    print(f"Generated {len(rows)} experiment rows and two figures (PNG + SVG).")
    for pauli in ("X", "Z"):
        row = next(r for r in rows if r["noise"] == pauli
                   and r["physical_error_probability"] == 0.1)
        print(f"{pauli} noise, p=0.1: simulated={row['logical_rate']:.5f}, "
              f"theory={row['theoretical_logical_rate']:.5f}")


if __name__ == "__main__":
    main()
