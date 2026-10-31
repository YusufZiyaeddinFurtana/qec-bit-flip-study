"""Ideal quantum recovery, implemented independently of the probability formulas.

Conventions: |q0 q1 q2>, with q0 the most significant bit. A syndrome is
(q0 XOR q1, q1 XOR q2). Projectors model ideal ancilla parity measurements;
they do not measure the individual data qubits. Branch vectors remain
unnormalized, so outer products retain the branch probabilities.
"""

from itertools import product

import numpy as np


I = np.eye(2, dtype=complex)
X = np.array([[0, 1], [1, 0]], dtype=complex)
Z = np.diag([1, -1]).astype(complex)
ZERO = np.array([1, 0], dtype=complex)
ONE = np.array([0, 1], dtype=complex)
PLUS = np.array([1, 1], dtype=complex) / np.sqrt(2)
PLUS_I = np.array([1, 1j], dtype=complex) / np.sqrt(2)
PATTERNS = tuple(product((0, 1), repeat=3))
CORRECTIONS = {(0, 0): None, (1, 0): 0, (1, 1): 1, (0, 1): 2}


def validate_probability(p: float) -> None:
    if not np.isfinite(p) or not 0 <= p <= 1:
        raise ValueError("Error probability must be finite and in [0, 1].")


def encode(state: np.ndarray) -> np.ndarray:
    """Map alpha|0> + beta|1> to alpha|000> + beta|111>."""
    state = np.asarray(state, dtype=complex)
    if state.shape != (2,) or not np.isclose(np.vdot(state, state), 1):
        raise ValueError("Input must be a normalized two-amplitude qubit state.")
    encoded = np.zeros(8, dtype=complex)
    encoded[[0, 7]] = state
    return encoded


def apply_pattern(state: np.ndarray, pattern: tuple, pauli: str) -> np.ndarray:
    """Apply X or Z to the selected physical qubits."""
    if pauli not in ("X", "Z"):
        raise ValueError("Supported noise types are X and Z.")
    if len(pattern) != 3 or any(bit not in (0, 1) for bit in pattern):
        raise ValueError("An error pattern must contain three binary values.")
    gate = X if pauli == "X" else Z
    operator = np.array([[1]], dtype=complex)
    for bit in pattern:
        operator = np.kron(operator, gate if bit else I)
    return operator @ state


def syndrome_projector(syndrome: tuple) -> np.ndarray:
    """Project onto one eigenspace of Z0 Z1 and Z1 Z2."""
    if syndrome not in CORRECTIONS:
        raise ValueError("A syndrome must be one of 00, 10, 11, 01.")
    diagonal = np.zeros(8)
    for index, (q0, q1, q2) in enumerate(PATTERNS):
        diagonal[index] = (q0 ^ q1, q1 ^ q2) == syndrome
    return np.diag(diagonal)


def recovery_density(encoded_state: np.ndarray) -> np.ndarray:
    """Measure parity, apply the syndrome-dependent X, and forget the syndrome."""
    density = np.zeros((8, 8), dtype=complex)
    for syndrome, qubit in CORRECTIONS.items():
        branch = syndrome_projector(syndrome) @ encoded_state
        if qubit is not None:
            pattern = tuple(int(index == qubit) for index in range(3))
            branch = apply_pattern(branch, pattern, "X")
        density += np.outer(branch, branch.conj())
    return density


def decode_density(encoded_density: np.ndarray) -> np.ndarray:
    """Invert the encoding on its code space (all recovery outputs lie there)."""
    if encoded_density.shape != (8, 8):
        raise ValueError("Encoded density matrix must have shape (8, 8).")
    logical = encoded_density[np.ix_([0, 7], [0, 7])]
    if not np.isclose(np.trace(logical), np.trace(encoded_density)):
        raise ValueError("State has support outside the code space.")
    return logical


def logical_output(state: np.ndarray, p: float, pauli: str) -> np.ndarray:
    """Exact noisy channel: enumerate all 8 errors, recover, and decode.

No sampling or analytical logical-error formula is used in this function.
Noise occurs once, between ideal encoding and ideal recovery.
"""
    validate_probability(p)
    encoded = encode(state)
    output = np.zeros((2, 2), dtype=complex)
    for pattern in PATTERNS:
        weight = sum(pattern)
        probability = p**weight * (1 - p) ** (3 - weight)
        corrupted = apply_pattern(encoded, pattern, pauli)
        output += probability * decode_density(recovery_density(corrupted))
    return output


def pure_state_fidelity(density: np.ndarray, target: np.ndarray) -> float:
    """Return <target|density|target> for a pure target state."""
    return float(np.clip(np.vdot(target, density @ target).real, 0, 1))


def logical_error_theory(p: float, pauli: str) -> float:
    validate_probability(p)
    if pauli == "X":
        return 3 * p**2 * (1 - p) + p**3
    if pauli == "Z":
        return 3 * p * (1 - p) ** 2 + p**3
    raise ValueError("Supported noise types are X and Z.")
