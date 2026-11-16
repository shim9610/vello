# Codex Cloud unpack measurements

This archive records an exploratory comparison of published `vello_cpu 0.4.0`
and the proposed unaligned-byte-buffer handling. The primary comparison is
`original` versus `bytes`. The `loop` variant is an intermediate implementation
retained because it participated in the recorded execution order.

## Environment and provenance

| Item | Recorded or observed value |
| --- | --- |
| Execution service | Codex Cloud, Linux x86-64 guest |
| Guest-reported CPU brand | AMD EPYC 9V74 80-Core Processor |
| CPU family / model / stepping | 25 / 17 / 1 |
| Virtualization | KVM, full virtualization |
| Exposed CPUs / allowed affinity | 5 logical CPUs, IDs 0–4 |
| CPU quota | `400000 100000`: 4 CPU-seconds per second across the cgroup |
| Benchmark affinity | `taskset -c 0`, one guest logical CPU |
| Memory limit | 16 GiB cgroup limit |
| Guest OS | Debian GNU/Linux 13.6 (trixie), glibc 2.41 |
| Kernel | Linux 6.18.57 |
| Toolchain | rustc 1.99.1 (`58cf8f9c3`, 2026-10-13), LLVM 23.1.1 |
| Build | Cargo release profile, incremental compilation disabled |
| SIMD | Native runtime dispatch; the guest exposes AVX-512 |
| Relevant dependency resolution | `vello_common 0.4.0`, `fearless_simd 1.2.0`, `bytemuck 1.25.2` |

The CPU brand is guest-reported. “80-Core” is part of that brand string; this
benchmark did not have 80 dedicated cores. Guest CPU affinity does not establish
exclusive physical-core ownership. CPU frequency, boost state, thermal state,
and co-tenant load were not recorded or controlled.

[environment.json](environment.json) was collected after the timing run at
2026-11-17 01:35:46 KST (2026-11-16 16:35:46 UTC). The timing harness itself did
not save a hardware inventory or a wall-clock run timestamp. Its retained
metadata records affinity, repetition counts, binary hashes, and elapsed run
time. This separates observed guest inventory from timing-time controls.

These standalone experiments use the published 0.4.0 dependency resolution,
not the upstream workspace lockfile or its Criterion harness. The archived
patches identify the measured implementations.

## Workload and repetition

The benchmark measures `U8Kernel::unpack` on a four-row strip. Source and target
buffers are preallocated and reused, with hot-cache input. Allocation, setup,
initial packing, runtime SIMD detection, and output-equality checks are outside
the timed batch. Source byte `i` is `(7*i + 13) mod 256`. The loop includes the
kernel call and `black_box` arguments.
Each batch reports `Instant` elapsed nanoseconds divided by its call count;
these are not individual-call latency samples or hardware-cycle measurements.

| Strip size | Calls per measured batch | Retained batches per variant | Measured calls per variant |
| --- | ---: | ---: | ---: |
| 16 × 4 | 15,772,009 | 120 | 1,892,641,080 |
| 64 × 4 | 4,048,231 | 120 | 485,787,720 |
| 256 × 4 | 1,719,354 | 120 | 206,322,480 |

Each measured batch has one equally sized warm-up batch in the same process.
All three variants run in each round; all six variant-order permutations occur
20 times per width, and width order rotates. No retained samples were removed.
The archive contains 360 round records, each with three measured batch values:
1,080 observations total. There are 7,754,253,840 measured kernel calls, or
15,508,507,680 including warm-up calls. These counts exclude calibration.
Billions of calls improve batch timing resolution; they are not billions of
independent statistical observations.

The three-variant run took approximately 282 seconds, including orchestration
and intermediate statistical summaries.

## Results and variability

Values below describe the 120 retained batch means per variant. SD is sample
standard deviation; CV is SD divided by the arithmetic mean. Timings and SD are
in nanoseconds per unpack invocation.

| Strip | Original median | Patched median | Original SD | Patched SD | Original CV | Patched CV |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 16 × 4 | 6.56 | 7.15 | 2.80 | 1.74 | 36.5% | 22.2% |
| 64 × 4 | 17.85 | 16.37 | 3.19 | 1.67 | 16.9% | 9.9% |
| 256 × 4 | 53.54 | 58.88 | 7.00 | 8.99 | 12.6% | 14.6% |

For each round, the analysis takes the log of patched/original elapsed time,
then exponentiates the mean log ratio. This paired geometric-mean estimate is
not the ratio of the separate medians in the preceding table.

| Strip | Paired time change | 95% bootstrap confidence interval | Interpretation within this run |
| --- | ---: | ---: | --- |
| 16 × 4 | +4.4% | −1.9% to +11.0% | Direction unresolved |
| 64 × 4 | −9.7% | −12.2% to −7.3% | Lower elapsed time |
| 256 × 4 | +10.4% | +7.3% to +13.6% | Higher elapsed time |

Intervals use a circular moving-block bootstrap: six consecutive rounds per
block, 20 blocks per resample, 5,000 resamples, and percentile bounds at 2.5%
and 97.5%. The fixed random seeds and exact calculation are in
[recorded-runner.py](recorded-runner.py). Resampling blocks retains short-range
round dependence rather than treating every kernel invocation as independent.

The intervals quantify variation in this one recorded run under that resampling
scheme. They do not bound systematic VM scheduling bias, unrecorded host changes,
or differences on another machine. A 95% interval is not a guarantee of 95%
accuracy. The substantial CVs above are part of the result. These kernel results
do not establish whole-frame performance or Apple Silicon/NEON performance.

## Evidence and replay

- [rounds.jsonl](rounds.jsonl): all retained round records, including order.
- [metadata.json](metadata.json): counts, controls, and measured binary SHA-256 hashes.
- [recorded-summary.json](recorded-summary.json): original checkpoint at 120 rounds.
- [variability.json](variability.json): means, SD, CV, quartiles, and ranges.
- [benchmark.rs](benchmark.rs) and [harness/](harness/): measured source and lockfiles.
- [patches/](patches/): measured changes relative to published 0.4.0.
- [recorded-runner.py](recorded-runner.py): exact recorded orchestration script.

`python3 analyze.py` recalculates all nine paired comparisons from the raw
records, checks them against the recorded summary, and prints a compact result.
It does not rerun the benchmark.

On Linux with Python 3.12+, `patch`, `taskset`, and Rust 1.99.1 available:

```sh
python3 prepare-replay.py
python3 replay-runner.py
```

Preparation downloads and checksums the published crate, applies the archived
patches, isolates the copied harness packages from the enclosing workspace, and
builds all variants before timing. The replay runner changes only archive/output
paths relative to the recorded runner and writes fresh results under
`replay-results/`; it does not overwrite the archived measurements. A replay
needs its own environment inventory. The runner's `taskset` affinity mechanism
is Linux-specific; it is not a macOS measurement prescription.
