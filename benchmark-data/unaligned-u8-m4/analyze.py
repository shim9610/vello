#!/usr/bin/env python3
"""Independent process-pair inference; individual Criterion samples are not replicates."""
import argparse,csv,hashlib,itertools,json,math,pathlib,random,statistics
ROOT=pathlib.Path(__file__).resolve().parent

def quantile(data,p):
 i=(len(data)-1)*p;a=int(i);b=min(a+1,len(data)-1);return data[a]+(data[b]-data[a])*(i-a)
def geometric(values):return math.exp(statistics.mean(map(math.log,values)))
def bootstrap_logs(values,n=100000,seed=20261117):
 rng=random.Random(seed);length=len(values)
 result=[sum(values[rng.randrange(length)] for _ in values)/length for _ in range(n)]
 result.sort();return result

def analyze(path,output):
 completion=json.loads((path/'completion.json').read_text());plan=json.loads((path/'plan.json').read_text());assert completion['status']=='complete'
 runs=json.loads((path/'executions.json').read_text());pairs=sorted(set(r['pair'] for r in runs));assert len(runs)==2*len(pairs) and len(pairs)==plan['pairs']
 assert all(r['status']=='complete' and r['exit']==0 for r in runs)
 names=json.loads((path/'plan.json').read_text())['names'];table=[];details=[]
 for index,name in enumerate(names):
  entries=[]
  for pair in pairs:
   a=next(r for r in runs if r['pair']==pair and r['variant']=='original');b=next(r for r in runs if r['pair']==pair and r['variant']=='modified')
   x=a['measurements'][name];y=b['measurements'][name];e=dict(pair=pair,order='AB' if a['slot']==0 else 'BA',original_ns=x['slope_ns'],modified_ns=y['slope_ns'],delta_percent=(y['slope_ns']/x['slope_ns']-1)*100,original_ci_low_ns=x['slope_ci']['lower_bound'],original_ci_high_ns=x['slope_ci']['upper_bound'],modified_ci_low_ns=y['slope_ci']['lower_bound'],modified_ci_high_ns=y['slope_ci']['upper_bound'])
   details.append(dict(benchmark=name,**e));entries.append(e)
  original=[r['original_ns'] for r in entries];modified=[r['modified_ns'] for r in entries];logs=[math.log(y/x) for x,y in zip(original,modified)];boots=bootstrap_logs(logs,seed=20261117+index)
  observed=abs(sum(logs));permutations=itertools.product([-1,1],repeat=len(logs));tail=sum(abs(sum(s*v for s,v in zip(signs,logs)))>=observed-1e-12 for signs in permutations)
  delta=lambda value:100*math.expm1(value)
  row=dict(benchmark=name,n_pairs=len(pairs),original_geomean_ns=geometric(original),modified_geomean_ns=geometric(modified),original_mean_ns=statistics.mean(original),modified_mean_ns=statistics.mean(modified),original_sd_ns=statistics.stdev(original),modified_sd_ns=statistics.stdev(modified),original_cv_percent=100*statistics.stdev(original)/statistics.mean(original),modified_cv_percent=100*statistics.stdev(modified)/statistics.mean(modified),delta_percent=delta(statistics.mean(logs)),paired_bootstrap95_ci_percent=[delta(quantile(boots,.025)),delta(quantile(boots,.975))],bonferroni_family95_ci_percent=[delta(quantile(boots,.00625)),delta(quantile(boots,.99375))],exact_two_sided_signflip_p=tail/(2**len(logs)),modified_faster_pairs=sum(x<0 for x in logs),modified_slower_pairs=sum(x>0 for x in logs),per_pair_delta_sd_percentage_points=statistics.stdev([r['delta_percent'] for r in entries]),per_pair_delta_minmax_percent=[min(r['delta_percent'] for r in entries),max(r['delta_percent'] for r in entries)],order_delta_percent={order:delta(statistics.mean(math.log(r['modified_ns']/r['original_ns']) for r in entries if r['order']==order)) for order in ['AB','BA']},half_delta_percent={label:delta(statistics.mean(values)) for label,values in [('first',logs[:len(logs)//2]),('second',logs[len(logs)//2:])]},pairs=entries)
  table.append(row)
 for index,row in enumerate(table):
  for variant in ['original','modified']:
   values=[math.log(p[variant+'_ns']) for p in row['pairs']];draws=bootstrap_logs(values,seed=20261117+index)
   row[variant+'_geomean95_ci_ns']=[math.exp(quantile(draws,.025)),math.exp(quantile(draws,.975))]
 previous=0
 for i,row in enumerate(sorted(table,key=lambda r:r['exact_two_sided_signflip_p'])):
  previous=max(previous,min(1,(len(table)-i)*row['exact_two_sided_signflip_p']));row['holm_adjusted_p']=previous;row['significant_family_0_05']=previous<.05
 thermal=[json.loads(line) for line in (path/'thermal.jsonl').read_text().splitlines() if line.startswith('{')]
 summary=dict(campaign=str(path),pairs=len(pairs),primary_unit='One separately launched process per version per pair; slope ns/iteration; all200 samples retained within Criterion run',analysis='geometric mean times, paired log-ratio percentile bootstrap100000 seed20261117+i; exact two-sided paired sign-flip; Holm family4 alpha0.05; 98.75% per-comparison bootstrap intervals also reported for Bonferroni family95%',thermal_counts={str(state):sum(r['thermal_state']==state for r in thermal) for state in sorted(set(r['thermal_state'] for r in thermal))},thermal_state_names={'0':'nominal','1':'fair','2':'serious','3':'critical'},needs_noise_diagnostic=any(max(r['original_cv_percent'],r['modified_cv_percent'])>5 for r in table) or any(r['thermal_state']!=0 for r in thermal),benchmarks=table)
 (output/'analysis.json').write_text(json.dumps(summary,indent=2)+'\n')
 with (output/'per-pair.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(details[0]));w.writeheader();w.writerows(details)
 fields=[k for k,v in table[0].items() if not isinstance(v,(list,dict))]
 with (output/'summary.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:r[k] for k in fields} for r in table)
 for row in table:print(row['benchmark'],round(row['original_geomean_ns'],4),round(row['modified_geomean_ns'],4),round(row['delta_percent'],4),row['paired_bootstrap95_ci_percent'],'pHolm',row['holm_adjusted_p'],'faster/slower',row['modified_faster_pairs'],row['modified_slower_pairs'])
 print('THERMAL',summary['thermal_counts'],'NOISE_DIAGNOSTIC',summary['needs_noise_diagnostic'])
 return summary
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('campaign',type=pathlib.Path);ap.add_argument('--out',type=pathlib.Path,default=ROOT/'recomputed');args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True);analyze(args.campaign.resolve(),args.out.resolve())
