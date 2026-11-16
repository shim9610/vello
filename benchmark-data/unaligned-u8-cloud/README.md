# Codex Cloud unpack benchmark results

Comparison of published `vello_cpu 0.4.0` (`original`) and the byte-copy patch
(`bytes`). The intermediate `loop` implementation is also retained in the data.

## Setup

- Codex Cloud Linux x86-64 KVM guest; CPU brand: AMD EPYC 9V74 80-Core Processor.
- Five exposed logical CPUs, four-CPU cgroup quota; benchmark pinned to guest CPU 0.
- Debian 13.6, Linux 6.18.57, glibc 2.41; 16 GiB memory limit.
- Rust 1.99.1 / LLVM 23.1.1; release builds; runtime SIMD dispatch, AVX-512 exposed.
- Dependencies: `vello_common 0.4.0`, `fearless_simd 1.2.0`, `bytemuck 1.25.2`.

The environment inventory was collected after the run, at 2026-11-17 01:35 KST.
Frequency, thermals, and host load were not recorded.

The harness repeatedly calls `U8Kernel::unpack` on preallocated, hot four-row
strips. Each width has 120 paired rounds. All six execution orders of the three
variants occur 20 times. Each measured batch follows an equally sized warm-up.
The full run took approximately 282 seconds.

| Strip | Calls per batch | Rounds |
| --- | ---: | ---: |
| 16 × 4 | 15,772,009 | 120 |
| 64 × 4 | 4,048,231 | 120 |
| 256 × 4 | 1,719,354 | 120 |

## Results

Times are batch medians in ns per call. Change is the geometric mean of paired
patched/original ratios; negative means faster.

| Strip | Original → patched, ns | Change | 95% CI | CV, original / patched |
| --- | ---: | ---: | ---: | ---: |
| 16 × 4 | 6.56 → 7.15 | +4.4% | −1.9% to +11.0% | 36.5% / 22.2% |
| 64 × 4 | 17.85 → 16.37 | −9.7% | −12.2% to −7.3% | 16.9% / 9.9% |
| 256 × 4 | 53.54 → 58.88 | +10.4% | +7.3% to +13.6% | 12.6% / 14.6% |

Results varied by width: unresolved at 16, faster at 64, slower at 256.
Batch variation was substantially higher than in the native M4 campaign.

CIs use a circular moving-block bootstrap with six-round blocks and 5,000
resamples. CV is sample SD divided by the mean of 120 batch timings.

## Data and replay

- [Raw rounds](rounds.jsonl), [run metadata](metadata.json), [environment](environment.json).
- [Recorded summary](recorded-summary.json), [variation statistics](variability.json).
- [Source](benchmark.rs), [harnesses and lockfiles](harness/), [patches](patches/).
- [Recorded runner](recorded-runner.py).

Recalculate:

```sh
python3 analyze.py
```

Rebuild and rerun on Linux with Python 3.12+, `patch`, `taskset`, and Rust 1.99.1:

```sh
python3 prepare-replay.py
python3 replay-runner.py
```

Fresh measurements are written to `replay-results/`.
