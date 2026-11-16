from pathlib import Path
import subprocess,statistics,random,math,time,json,hashlib
import os
ARCHIVE=Path(__file__).resolve().parent
ROOT=Path(os.environ.get('VELLO_BENCH_ROOT', str(ARCHIVE/'replay')))
OUT=Path(os.environ.get('VELLO_BENCH_OUTPUT', str(ARCHIVE/'replay-results')))
OUT.mkdir(parents=True, exist_ok=True)
VARIANTS=['original','loop','bytes'];WIDTHS=[16,64,256];ROUNDS=120;CPU=0
rows={w:[] for w in WIDTHS};iterations={}
def run(variant,width,count):
 p=subprocess.run(['taskset','-c',str(CPU),str(ROOT/'native-target/release'/f'unpack-bench-{variant}'),str(width),str(count)],capture_output=True,text=True,check=True)
 return float(p.stdout.strip())
for width in WIDTHS:
 ns=statistics.median(run('original',width,500000) for _ in range(3))
 iterations[width]=max(10000,min(25000000,int(100000000/ns)))
metadata={'rounds':ROUNDS,'widths':WIDTHS,'height':4,'iterations_per_batch':iterations,'cpu':CPU,
 'scope':'unpack only; preallocated source/target; hot cache; one warmup then one measured batch; SIMD level detected once; exact output equality checked after each batch',
 'order':'all six variant permutations cycled; rotating width order',
 'interval':'95% circular moving-block bootstrap; six consecutive rounds per block; 5000 resamples',
 'binary_sha256':{v:hashlib.sha256((ROOT/'native-target/release'/f'unpack-bench-{v}').read_bytes()).hexdigest() for v in VARIANTS}}
(OUT/'metadata.json').write_text(json.dumps(metadata,indent=2))
print(json.dumps({'iterations':iterations}),flush=True)
def estimate(width,records,variant,baseline):
 values=[math.log(r[variant]/r[baseline]) for r in records];n=len(values);rng=random.Random(20261117+width+n+VARIANTS.index(variant));samples=[]
 for _ in range(5000):
  chosen=[]
  while len(chosen)<n:
   i=rng.randrange(n);chosen.extend(values[(i+j)%n] for j in range(6))
  samples.append(math.expm1(statistics.mean(chosen[:n]))*100)
 samples.sort()
 return {'variant':variant,'baseline':baseline,'change_percent':math.expm1(statistics.mean(values))*100,'ci95_percent':[samples[125],samples[4875]]}
def summary():
 return [{'width':width,'height':4,'rounds':len(records),'median_ns':{v:statistics.median(r[v] for r in records) for v in VARIANTS},'comparisons':[estimate(width,records,'loop','original'),estimate(width,records,'bytes','original'),estimate(width,records,'bytes','loop')]} for width,records in rows.items()]
orders=[['original','loop','bytes'],['original','bytes','loop'],['loop','original','bytes'],['loop','bytes','original'],['bytes','original','loop'],['bytes','loop','original']]
started=time.monotonic()
with (OUT/'rounds.jsonl').open('w') as stream:
 for round_id in range(ROUNDS):
  shift=round_id%3
  for width in WIDTHS[shift:]+WIDTHS[:shift]:
   order=orders[(round_id+WIDTHS.index(width))%6];record={'round':round_id+1,'width':width,'order':order}
   for variant in order:record[variant]=run(variant,width,iterations[width])
   rows[width].append(record);stream.write(json.dumps(record)+'\n');stream.flush()
  if (round_id+1)%15==0:print(json.dumps({'rounds':round_id+1,'elapsed_seconds':round(time.monotonic()-started,1)}),flush=True)
  if (round_id+1) in [30,60,90,120]:
   result=summary();(OUT/f'checkpoint-{round_id+1}.json').write_text(json.dumps(result,indent=2));print(json.dumps({'checkpoint':round_id+1,'results':result}),flush=True)
metadata['elapsed_seconds']=time.monotonic()-started
(OUT/'metadata.json').write_text(json.dumps(metadata,indent=2))
