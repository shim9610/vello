# Apple M4 benchmark results

Four NEON benchmarks were compared across 12 original/patched process pairs.
None reached statistical significance after Holm correction.

## Setup

- Mac mini Mac16,10; Apple M4, 10 CPU cores, 16 GiB RAM.
- macOS 27.2 (26B123); Rust 1.99.1, LLVM 23.1.1; native arm64.
- Original: `71109540002c9a2c6bb7c000ce8c829ba261304b`.
- Patched: `e1c0151ee65fbef43f37a73bb88a5745c32f22d1`.
- Same workspace lockfile and unchanged `vello_bench` fixtures; release builds.
- Run: 2026-11-17, 01:23–01:47 KST. AC power, low-power mode off,
  `caffeinate -i`; 60-second cooldown after building, three seconds between runs.
  All 299 thermal readings were nominal. CPU frequency and affinity were automatic.

Original/patched order alternated between pairs. Each process ran all four
benchmarks: three-second warm-up, ten-second measurement, 200 Criterion samples.
All 12 pairs were included. Pack/unpack use 256 × 4 pixels; opaque short uses
32 × 4 and opaque long uses 256 × 4.

## Results

Times are geometric means of the 12 process slopes. Negative change means faster.

| Benchmark | Original → patched, ns | Change | 95% CI | Holm-adjusted p |
| --- | ---: | ---: | ---: | ---: |
| pack | 47.485 → 47.409 | −0.161% | −0.317% to −0.047% | 0.0547 |
| unpack | 48.132 → 48.123 | −0.017% | −0.235% to +0.193% | 1.0 |
| opaque short | 6.957 → 6.950 | −0.102% | −0.505% to +0.281% | 1.0 |
| opaque long | 34.056 → 34.028 | −0.083% | −0.460% to +0.267% | 1.0 |

Pack was faster in 10/12 pairs; the other results had mixed directions.
Between-process CV was 0.097–0.982% across all versions and benchmarks.

Change is the geometric mean of paired ratios. CIs use 100,000 paired bootstrap
resamples. P values use the exact two-sided sign-flip test on 12 paired log ratios,
with Holm correction for four comparisons at α=0.05. CIs are unadjusted.

## Tests and data

[All 103 unit tests passed](modified-test.log), including the unaligned-buffer
regression. Recalculation from all 96 raw Criterion series reproduced the timings
and statistics ([verification](independent-validation.json)).

- [Environment](environment.json), [fixture identity](fixture-identity.json),
  [binary hashes](binaries.json), [final integrity](final-integrity.json).
- [Raw series and execution records](runs/main12/), [file hashes](raw-sha256.json).
- [Per-pair results](per-pair.csv), [summary](summary.csv), [full analysis](analysis.json).

Recalculate:

```sh
python3 analyze.py runs/main12 --out recomputed
```
