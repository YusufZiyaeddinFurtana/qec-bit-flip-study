"""Independent channel checks, including coherence and uncorrectable errors."""

import unittest

import numpy as np

from qec_study.model import (
    CORRECTIONS, PATTERNS, PLUS, PLUS_I, ONE, ZERO, X, Z,
    apply_pattern, decode_density, encode, logical_error_theory,
    logical_output, pure_state_fidelity, recovery_density, syndrome_projector,
)


STATES = (ZERO, ONE, PLUS, PLUS_I,
          np.array([np.sqrt(0.3), np.exp(0.7j) * np.sqrt(0.7)]))


class QuantumRecoveryTests(unittest.TestCase):
    def test_parity_projectors_form_a_complete_orthogonal_measurement(self):
        projectors = [syndrome_projector(s) for s in CORRECTIONS]
        np.testing.assert_allclose(sum(projectors), np.eye(8))
        for index, left in enumerate(projectors):
            for other, right in enumerate(projectors):
                np.testing.assert_allclose(left @ right,
                                           left if index == other else np.zeros((8, 8)))

    def test_all_bit_error_patterns_on_complex_superpositions(self):
        for state in STATES:
            for pattern in PATTERNS:
                with self.subTest(state=state, pattern=pattern):
                    actual = decode_density(recovery_density(
                        apply_pattern(encode(state), pattern, "X")
                    ))
                    target = state if sum(pattern) <= 1 else X @ state
                    np.testing.assert_allclose(actual, np.outer(target, target.conj()), atol=1e-14)

    def test_all_phase_error_patterns_reduce_to_phase_parity(self):
        for state in STATES:
            for pattern in PATTERNS:
                with self.subTest(state=state, pattern=pattern):
                    corrupted = apply_pattern(encode(state), pattern, "Z")
                    # Every phase-only error remains in the no-bit-error syndrome.
                    np.testing.assert_allclose(syndrome_projector((0, 0)) @ corrupted, corrupted)
                    actual = decode_density(recovery_density(corrupted))
                    target = state if sum(pattern) % 2 == 0 else Z @ state
                    np.testing.assert_allclose(actual, np.outer(target, target.conj()), atol=1e-14)

    def test_exact_channel_matches_analytic_channel_for_arbitrary_inputs(self):
        for pauli, gate in (("X", X), ("Z", Z)):
            for state in STATES:
                for p in (0, 0.005, 0.1, 0.3, 0.5, 0.8, 1):
                    with self.subTest(pauli=pauli, p=p, state=state):
                        rate = logical_error_theory(p, pauli)
                        transformed = gate @ state
                        expected = ((1 - rate) * np.outer(state, state.conj())
                                    + rate * np.outer(transformed, transformed.conj()))
                        actual = logical_output(state, p, pauli)
                        np.testing.assert_allclose(actual, expected, atol=1e-13)
                        self.assertAlmostEqual(np.trace(actual).real, 1)
                        self.assertGreaterEqual(np.linalg.eigvalsh(actual).min(), -1e-13)

    def test_single_bit_flip_preserves_coherence(self):
        actual = decode_density(recovery_density(
            apply_pattern(encode(PLUS_I), (0, 1, 0), "X")
        ))
        self.assertAlmostEqual(abs(actual[0, 1]), 0.5)
        self.assertAlmostEqual(pure_state_fidelity(actual, PLUS_I), 1)

    def test_single_phase_flip_is_a_visible_failure_on_plus(self):
        actual = decode_density(recovery_density(
            apply_pattern(encode(PLUS), (1, 0, 0), "Z")
        ))
        self.assertAlmostEqual(pure_state_fidelity(actual, PLUS), 0)

    def test_invalid_inputs_are_rejected(self):
        for p in (-0.1, 1.1, float("nan")):
            with self.assertRaises(ValueError):
                logical_output(ZERO, p, "X")
        with self.assertRaises(ValueError):
            encode(np.array([1, 1]))
        with self.assertRaises(ValueError):
            apply_pattern(encode(ZERO), (0, 0, 0), "Y")
        outside_code = np.zeros((8, 8), dtype=complex)
        outside_code[1, 1] = 1
        with self.assertRaises(ValueError):
            decode_density(outside_code)


if __name__ == "__main__":
    unittest.main()
