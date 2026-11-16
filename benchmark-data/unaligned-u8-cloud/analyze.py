"""Recalculate the recorded paired comparisons without running benchmarks."""
from pathlib import Path
import json
import math
import random
import statistics

VARIANTS = ["original", "loop", "bytes"]
archive = Path(__file__).resolve().parent
records = [json.loads(line) for line in (archive / "rounds.jsonl").read_text().splitlines()]

def estimate(width,records,variant,baseline):
 values=[math.log(r[variant]/r[baseline]) for r in records];n=len(values);rng=random.Random(20261117+width+n+VARIANTS.index(variant));samples=[]
 for _ in range(5000):
  chosen=[]
  while len(chosen)<n:
   i=rng.randrange(n);chosen.extend(values[(i+j)%n] for j in range(6))
  samples.append(math.expm1(statistics.mean(chosen[:n]))*100)
 samples.sort()
 return {'variant':variant,'baseline':baseline,'change_percent':math.expm1(statistics.mean(values))*100,'ci95_percent':[samples[125],samples[4875]]}

expected = json.loads((archive / "recorded-summary.json").read_text())
for item in expected:
    width = item["width"]
    group = [record for record in records if record["width"] == width]
    assert len(group) == 120, f"unexpected round count for width {width}"
    for comparison in item["comparisons"]:
        actual = estimate(width, group, comparison["variant"], comparison["baseline"])
        assert actual == comparison, (width, actual, comparison)
    print(json.dumps({"width": width, "verified_comparisons": 3,
                      "patched_vs_original": item["comparisons"][1]}))
