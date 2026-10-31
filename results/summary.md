# Generated results

Seed: `20261031`. Trials per noise type and probability: **200,000**.

Intervals below are pointwise 95% Wilson intervals for the coded rate.
These are simulated estimates; the exact quantum calculation is separate.

| Noise / probe | Physical p | Uncoded estimate | Coded estimate | Coded 95% interval | Theory |
|---|---:|---:|---:|---:|---:|
| X / \|0> | 0.01 | 0.01022 | 0.00023 | [0.00018, 0.00031] | 0.00030 |
| X / \|0> | 0.05 | 0.05044 | 0.00736 | [0.00699, 0.00774] | 0.00725 |
| X / \|0> | 0.10 | 0.10104 | 0.02840 | [0.02768, 0.02913] | 0.02800 |
| X / \|0> | 0.20 | 0.20116 | 0.10340 | [0.10207, 0.10474] | 0.10400 |
| Z / \|+> | 0.01 | 0.00980 | 0.02971 | [0.02897, 0.03046] | 0.02940 |
| Z / \|+> | 0.05 | 0.05034 | 0.13670 | [0.13521, 0.13822] | 0.13550 |
| Z / \|+> | 0.10 | 0.10041 | 0.24280 | [0.24092, 0.24468] | 0.24400 |
| Z / \|+> | 0.20 | 0.20053 | 0.39365 | [0.39151, 0.39579] | 0.39200 |

All entries are probabilities, not percentages.

The interval is a repeated-sampling uncertainty statement, not a 95%
probability assigned to the fixed true parameter. Intervals are not
simultaneous across the sweep, and individual intervals can miss the theory.

See `performance.csv` for every count, interval, and exact quantum check.
The X probe is |0>; the Z probe is |+> so phase errors are observable.
