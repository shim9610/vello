# Native Apple M4 measurements

The four existing NEON benchmarks did not show a statistically significant
performance difference after Holm correction across the four comparisons.
The largest estimated change was a 0.161% reduction in pack time. This result
does not establish equivalence or zero overhead.

## Environment and compared source

The supplied run records identify a Mac mini, model **Mac16,10**, with an
**Apple M4, 10 CPU cores, and 16 GiB RAM**, running **macOS 27.2 (26B123)**.
The process and both benchmark binaries were native arm64;
`sysctl.proc_translated` was 0. The toolchain was **Rust 1.99.1**, host
`aarch64-apple-darwin`, with **LLVM 23.1.1**.

Measurement window: **2026-11-17 01:23:44–01:47:35 KST**.

| Version | Commit |
| --- | --- |
| Original | `71109540002c9a2c6bb7c000ce8c829ba261304b` |
| Modified | `e1c0151ee65fbef43f37a73bb88a5745c32f22d1` |

Both worktrees used Cargo.lock SHA-256
`66dfe026a6f22cbde77d567985ce5c4db41b38ea6ff2b392debc4ad3eab74f06`.
The benchmark, macro, lockfile, and Cargo configuration identities match in
[fixture-identity.json](fixture-identity.json). Release benchmark binaries were
built before measurement with separate target directories, three build jobs,
and no additional target-CPU, optimization, or compiler-wrapper overrides.
[binaries.json](binaries.json) and [final-integrity.json](final-integrity.json)
record their hashes and unchanged source state. Executables were not included
in the supplied archive, so their hashes were not independently recomputed in
Codex Cloud.

The Mac was on AC power with low-power mode disabled. The run used
`caffeinate -i`, a 60-second post-build cooldown, and three seconds between
executions. All **299 five-second thermal-state observations were nominal**.
CPU frequency and core placement were not fixed; normal desktop services
remained active. Nominal thermal-state readings do not establish constant clocks.

## Method

The existing `vello_bench` fixtures and macros were unchanged. Pack and unpack
use 256 × 4 pixels; opaque short uses 32 × 4 and opaque long uses 256 × 4.
These performance fixtures do not deliberately misalign buffers. Unaligned
correctness is covered separately by the regression test.

There were **12 separately launched process pairs**, with original→modified
for odd pairs and modified→original for even pairs. Each process ran all four
benchmarks with **3-second warm-up, 10-second measurement time, and 200 Criterion
samples**, using 100,000 Criterion resamples and a unique output directory.
No rebuilding occurred during the 24 measured processes.

The independent analysis unit is a process pair: **12 paired observations per
benchmark**, not 200 independent process repetitions. The archive contains
96 Criterion series and 19,200 timed samples. All samples and pairs were retained.
The fixed campaign ended at 12 pairs; the recorded thermal/CV diagnostic trigger
was not met. Samples marked as outliers by Criterion were not removed.

For each process, the timing estimate is Criterion's fitted through-origin
slope in nanoseconds per benchmark iteration. Reported version times are the
geometric mean of 12 process slopes. Change is the exponentiated mean paired
log ratio minus one. Negative changes mean lower elapsed time for the patch.

## Results

| Benchmark | Original ns | Modified ns | Change | Individual 95% bootstrap CI | Holm-adjusted p |
| --- | ---: | ---: | ---: | ---: | ---: |
| `pack_block_u8_neon` | 47.485 | 47.409 | −0.161% | −0.317% to −0.047% | 0.0546875 |
| `unpack_block_u8_neon` | 48.132 | 48.123 | −0.017% | −0.235% to +0.193% | 1.0 |
| `opaque_short_u8_neon` | 6.957 | 6.950 | −0.102% | −0.505% to +0.281% | 1.0 |
| `opaque_long_u8_neon` | 34.056 | 34.028 | −0.083% | −0.460% to +0.267% | 1.0 |

The change intervals resample the 12 complete pairs 100,000 times, with seed
20261117 plus benchmark index. Primary significance uses a two-sided paired
sign-flip test enumerating all 4,096 sign assignments, followed by Holm correction
for four comparisons at family alpha 0.05. Sign-flip inference assumes sign
exchangeability of paired log differences under its null; fixed AB/BA order is
not randomized assignment.

Pack was faster in 10 of 12 pairs, with unadjusted sign-flip p=0.013671875,
but Holm-adjusted p=0.0546875. Its displayed bootstrap interval excludes zero;
that interval is an individual, unadjusted interval from a different procedure,
not an inversion of the family-adjusted test. It does not establish family-level
significance. The other benchmarks had mixed directions across pairs.

### Between-process variation

SD and CV below use the 12 process slopes for each version. CV is sample SD
divided by the arithmetic mean; the means below differ from the geometric
means in the result table.

| Benchmark | Original mean ± SD, ns | Original CV | Modified mean ± SD, ns | Modified CV |
| --- | ---: | ---: | ---: | ---: |
| pack | 47.486 ± 0.101 | 0.213% | 47.409 ± 0.046 | 0.097% |
| unpack | 48.132 ± 0.084 | 0.174% | 48.124 ± 0.159 | 0.330% |
| opaque short | 6.958 ± 0.041 | 0.596% | 6.951 ± 0.067 | 0.967% |
| opaque long | 34.057 ± 0.335 | 0.982% | 34.029 ± 0.297 | 0.871% |

These results concern the listed fixtures, machine, source, and build. They do
not establish whole-frame performance, other widths, other Macs, or Intel SIMD
performance. The cloud experiment used a different harness and dependency
resolution; its absolute times and these times should not be pooled or used
as a cross-machine speed comparison.

## Correctness and independent checks

The supplied [modified-test.log](modified-test.log) records **103 passed,
0 failed, 0 ignored** for `cargo +1.99.1 test --locked -p vello_cpu --all-features
--lib`, including `u8_kernels_accept_unaligned_buffers`.

Codex Cloud independently refitted all **96 slopes from the complete raw
200-sample series**, reproducing the stored estimates with maximum absolute
error **2.14e-14 ns**. The exact sign-flip p values and Holm correction also
matched. Rerunning the supplied analysis reproduced all four benchmark summaries
and bootstrap intervals within 1e-12 floating-point tolerance; minor final-bit
libm differences are retained as a cross-platform numerical tolerance.

## Retained evidence and analysis

- [environment.json](environment.json): selected environment and source-upload hashes.
- [runs/main12/](runs/main12/): plan, execution records, thermal samples, and all 96 unique saved Criterion series.
- [raw-sha256.json](raw-sha256.json): hashes of 384 byte-for-byte preserved Criterion numerical files.
- [analysis.json](analysis.json), [per-pair.csv](per-pair.csv), and [summary.csv](summary.csv): reported inference and each pair.
- [independent-validation.json](independent-validation.json): cloud refit and p-value checks.

Public records normalize the local artifact-root path and exclude process
listings, cleanup history, and unrelated machine context. Duplicate Criterion
`new` directories are omitted; each uniquely named saved baseline is preserved.
CSV line endings are normalized without changing numerical values.

To recalculate statistics without running benchmarks:

```sh
python3 analyze.py runs/main12 --out recomputed
```

The analysis implementation is preserved, with only its default output changed
to a separate `recomputed` directory. It does not launch measurements or clean
build directories. Commands, timing options, source SHAs, and binary hashes
needed to reconstruct a native run are recorded in the plan and executions.
