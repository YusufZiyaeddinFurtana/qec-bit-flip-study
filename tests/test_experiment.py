"""Check estimation boundaries and sampling against independent predictions."""

import unittest

import numpy as np

from qec_study.experiment import count_errors, wilson_interval


class EstimationTests(unittest.TestCase):
    def test_wilson_matches_published_reference_example(self):
        # 778/1497 example: RWTH Aachen, DS Python appendix, section B4.1.
        low, high = wilson_interval(778, 1497)
        self.assertAlmostEqual(low, 0.4943793119474541, places=12)
        self.assertAlmostEqual(high, 0.5449319688365669, places=12)

    def test_wilson_does_not_claim_zero_uncertainty_at_zero_errors(self):
        low, high = wilson_interval(0, 100)
        self.assertEqual(low, 0)
        self.assertGreater(high, 0.03)
        opposite_low, opposite_high = wilson_interval(100, 100)
        self.assertAlmostEqual(opposite_low, 1 - high)
        self.assertEqual(opposite_high, 1)

    def test_sampling_handles_deterministic_endpoints(self):
        for pauli in ("X", "Z"):
            self.assertEqual(count_errors(np.random.default_rng(1), 0, 100, pauli), (0, 0))
            self.assertEqual(count_errors(np.random.default_rng(1), 1, 100, pauli), (100, 100))

    def test_sampled_rates_agree_with_independent_analytic_values(self):
        # A generous fixed-seed six-standard-error bound avoids a flaky 95% test.
        shots = 200_000
        expected = {"X": 0.028, "Z": 0.244}
        for pauli in ("X", "Z"):
            uncoded, logical = count_errors(np.random.default_rng(17), 0.1, shots, pauli)
            for count, truth in ((uncoded, 0.1), (logical, expected[pauli])):
                tolerance = 6 * np.sqrt(truth * (1 - truth) / shots)
                self.assertLess(abs(count / shots - truth), tolerance)

    def test_invalid_counts_and_trial_numbers_are_rejected(self):
        for errors, shots in ((0, 0), (-1, 10), (11, 10)):
            with self.assertRaises(ValueError):
                wilson_interval(errors, shots)
        with self.assertRaises(ValueError):
            count_errors(np.random.default_rng(1), 0.1, 0, "X")


if __name__ == "__main__":
    unittest.main()
