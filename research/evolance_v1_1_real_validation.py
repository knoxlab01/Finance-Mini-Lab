"""Offline real-history study; frozen signal engine, explicit derived-only exports."""
import hashlib
import itertools
import json
from pathlib import Path
import numpy as np
import pandas as pd
from research.real_data_loader import load_local_dataset, ROOT
from research.real_data_check import private_git_status
from src.evolance.v1_1.spec import SPEC, SPEC_SHA256, load_spec
from src.evolance.v1_1.timeline import walk_forward
from src.evolance.v1_1.validation import evaluate_outcomes

OUTPUT = ROOT / 'research/evolance_v1_1_real_results'
METHOD = ROOT / 'docs/evolance_v1_1_real_method.md'
METHOD_SHA256 = 'd90bb0bce897cd25aa7a49a361416fa47e5d8d9942293a33ed3ec40e8f2fa5bb'
PORTFOLIOS = {'equal_weight': {'AAPL':.3333,'MSFT':.3333,'NVDA':.3334},
              'concentrated': {'AAPL':.70,'MSFT':.15,'NVDA':.15},
              'aapl': {'AAPL':1.}, 'msft': {'MSFT':1.}, 'nvda': {'NVDA':1.}}
NEUTRAL = 'Neutral / Uncertain'
STATES = ['Balanced Growth','Growth-Led','Defensive','Stressed','Mixed / Neutral']
METRICS = ['absolute_return','active_return','cagr','annualized_return','volatility','sharpe','drawdown',
           'downside_deviation','tracking_error','sortino','information_ratio','mean_correlation',
           'max_weight','hhi','effective_holdings','benchmark_return','benchmark_sharpe','benchmark_volatility',
           'portfolio_volatility','effective_risk_contributors','risk_breadth_score','diversification_ratio']


def hit(direction, realized):
    if direction == NEUTRAL or realized is None or not np.isfinite(realized):
        return None
    return bool(('Bullish' in direction and realized > 0) or ('Bearish' in direction and realized < 0))


def stats(rows, key='direction'):
    complete=[r for r in rows if r['complete']]
    directional=[r for r in complete if r[key]!=NEUTRAL]
    def moment(field, op):
        x=[r[field] for r in complete]
        return float(op(x)) if x else None
    result=dict(signals=len(rows),complete=len(complete),censored=len(rows)-len(complete),
                directional_n=len(directional),neutral_n=len(complete)-len(directional),
                hit_rate=float(np.mean([hit(r[key],r['forward_return']) for r in directional])) if directional else None,
                neutral_coverage=sum(r[key]==NEUTRAL for r in rows)/len(rows) if rows else None,
                complete_neutral_coverage=(len(complete)-len(directional))/len(complete) if complete else None,
                mean_return=moment('forward_return',np.mean),median_return=moment('forward_return',np.median),
                mean_drawdown=moment('forward_drawdown',np.mean),
                std_return=moment('forward_return',lambda x:np.std(x,ddof=1)) if len(complete)>1 else None,
                positive_frequency=moment('forward_return',lambda x:np.mean(np.array(x)>0)),
                evidence='insufficient evidence' if len(complete)<20 else 'descriptive; overlapping observations')
    for label in ['Bullish','Bearish']:
        selected=[r for r in directional if label in r[key]]
        result[label.lower()+'_n']=len(selected)
        for field,suffix in [('forward_return','return'),('forward_drawdown','drawdown')]:
            result[label.lower()+'_mean_'+suffix]=float(np.mean([r[field] for r in selected])) if selected else None
    return result


def group_tables(records):
    tables={name:[] for name in ['comparison_summary','confidence_calibration','state_outcomes','transition_outcomes','flag_outcomes']}
    for portfolio in ['ALL',*PORTFOLIOS]:
        for months in [6,12]:
            subset=[r for r in records if r['months']==months and (portfolio=='ALL' or r['portfolio']==portfolio)]
            base=dict(portfolio=portfolio,months=months)
            for system,key in [('Traditional','traditional_direction'),('MC-only','mc_only_direction'),('Evolance','direction')]:
                tables['comparison_summary'].append(dict(**base,system=system,**stats(subset,key)))
            for level in ['High','Moderate','Low']:
                selected=[r for r in subset if r['confidence']==level and r['direction']!=NEUTRAL]
                tables['confidence_calibration'].append(dict(**base,confidence=level,**stats(selected)))
            for name,key,groups in [('state_outcomes','state',STATES),('transition_outcomes','transition',['Deteriorating','Stable','Recovering'])]:
                for group in groups:
                    tables[name].append(dict(**base,group=group,**stats([r for r in subset if r[key]==group])))
            for flag in SPEC['flags']:
                for active in [True,False]:
                    tables['flag_outcomes'].append(dict(**base,flag=flag,active=active,**stats([r for r in subset if (flag in r['flags'])==active])))
            for label,predicate in [('Unsupported Growth + Deteriorating',lambda r:'Unsupported Growth' in r['flags'] and r['transition']=='Deteriorating'),('High Risk Concentration + Growth-Led',lambda r:'High Risk Concentration' in r['flags'] and r['state']=='Growth-Led')]:
                tables['flag_outcomes'].append(dict(**base,flag=label,active=True,**stats([r for r in subset if predicate(r)])))
    return tables


def failure_cases(records):
    result=[]
    for r in records:
        if not r['complete']:continue
        fail=hit(r['direction'],r['forward_return']) is False
        kinds=[]
        if 'Bullish' in r['direction'] and r['forward_return']<=0:kinds.append('bullish_loss')
        if 'Bearish' in r['direction'] and r['forward_return']>=0:kinds.append('bearish_gain')
        if r['confidence']=='High' and fail:kinds.append('high_confidence_failure')
        if r['transition']=='Recovering' and r['forward_return']<0:kinds.append('recovering_loss')
        if r['transition']=='Deteriorating' and r['forward_drawdown']>-.05:kinds.append('false_alarm_proxy')
        if r['transition']!='Deteriorating' and r['forward_drawdown']<=-.20:kinds.append('missed_deterioration_proxy')
        for kind in kinds:result.append(dict(kind=kind,**r))
    return result


def interpretation_cases(records):
    result=[]
    frame=pd.DataFrame(records)
    for (date,months),group in frame.groupby(['date','months'],sort=True):
        for a,b in itertools.combinations(group.to_dict('records'),2):
            if not a['complete'] or not b['complete'] or a['direction']!=b['direction']:continue
            if abs(a['probability_up']-b['probability_up'])>.05:continue
            if (a['state'],a['transition'],a['flags'])==(b['state'],b['transition'],b['flags']):continue
            def severity(r):return len(r['flags'])+int(r['transition']=='Deteriorating')+int(r['state']=='Stressed')
            if severity(a)==severity(b):category='redundant';worse,better=a,b
            else:
                worse,better=(a,b) if severity(a)>severity(b) else (b,a)
                delta=worse['forward_drawdown']-better['forward_drawdown']
                category='useful' if delta<-.02 else 'misleading' if delta>.02 else 'redundant'
            row=dict(date=date,months=months,category=category,direction=a['direction'])
            for prefix,r in [('higher_severity',worse),('other',better)]:
                for key in ['portfolio','state','flags','transition','confidence','probability_up','forward_return','forward_drawdown']:
                    row[prefix+'_'+key]=r[key]
            result.append(row)
    return result


def derived_timeline(signals, outcomes, portfolio):
    """Explicit export schema: no input price frame, raw columns or arbitrary metadata."""
    by_date={r['date']:r for r in signals}
    exported=[]
    for outcome in outcomes:
        s=by_date[outcome['date']]
        row={k:outcome[k] for k in ['date','months','complete','observations','direction','confidence','mc_only_direction','mc_only_confidence','traditional_direction','state','transition','flags','forward_return','forward_drawdown','probability_up','p10','p50','p90']}
        row.update(portfolio=portfolio,available_at=s['available_at'],window_start=s['window_start'],candidate_state=s['candidate_state'],
                   relative_outlook=s['outlooks'][str(outcome['months'])]['relative_outlook'],relative_confidence=s['outlooks'][str(outcome['months'])]['relative_confidence'])
        for k in METRICS:row['trailing_'+k]=s['metrics'].get(k)
        row.update(s['scores'])
        exported.append(row)
    return exported


def write_csv(path,rows):
    pd.DataFrame([{k:json.dumps(v) if isinstance(v,(list,dict)) else v for k,v in r.items()} for r in rows]).to_csv(path,index=False,float_format='%.10g')


def run():
    load_spec()
    method_hash=hashlib.sha256(METHOD.read_bytes()).hexdigest()
    if method_hash != METHOD_SHA256:raise ValueError('Registered study method changed; stop before validation')
    guard=private_git_status(ROOT/'research/private_data',ROOT/'research/private_data/manifest.json')
    if not guard['verified']:raise ValueError(guard['issues'])
    data=load_local_dataset()
    if data.prices is None or not data.report['evolance_v1_1_compatible']:raise ValueError('Input not technically ready')
    # Only the reviewed warning classes are accepted; other issues need review.
    if any(w['code'] not in {'alignment_dates_dropped','aligned_gap_review'} for w in data.report['warnings']):raise ValueError('Unreviewed input warning')
    gaps=[(str(data.prices.index[k-1].date()),str(data.prices.index[k].date())) for k in range(1,len(data.prices)) if (data.prices.index[k]-data.prices.index[k-1]).days>4]
    if gaps != [('2006-12-29','2007-01-03'),('2012-10-26','2012-10-31')]:raise ValueError('Calendar gaps changed: review required')
    signals={}
    for name,weights in PORTFOLIOS.items():
        print('Generating frozen signals: '+name,flush=True)
        signals[name]=walk_forward(data.prices,weights,'SPY',synthetic=False)['rows']
    # No forward outcomes computed before all signal generation finishes.
    records=[]
    for name,weights in PORTFOLIOS.items():
        outcomes=evaluate_outcomes(data.prices,weights,signals[name])
        records.extend(derived_timeline(signals[name],outcomes,name))
    tables=group_tables(records)
    tables['failure_cases']=failure_cases(records)
    tables['interpretation_cases']=interpretation_cases(records)
    OUTPUT.mkdir(exist_ok=True)
    for name in PORTFOLIOS:write_csv(OUTPUT/(name+'_timeline.csv'),[r for r in records if r['portfolio']==name])
    for name,rows in tables.items():write_csv(OUTPUT/(name+'.csv'),rows)
    summary=dict(spec_sha256=SPEC_SHA256,method_sha256=method_hash,source='User-declared Kaggle Huge Stock Market Dataset / Boris Marjanovic',
                 price_type='source_adjusted_close',period=[data.report['start_date'],data.report['end_date']],aligned_rows=len(data.prices),
                 input_hashes={k:v['source_file_sha256'] for k,v in data.report['per_ticker'].items()},portfolios=PORTFOLIOS,
                 signals_per_portfolio={k:len(v) for k,v in signals.items()},readiness=data.report['status'],calendar_gaps=gaps,
                 calendar_verification='Consistent with known US closures; no independent calendar source verification offline',
                 tables={k:v for k,v in tables.items() if k not in ['failure_cases','interpretation_cases']},
                 failure_counts=pd.Series([r['kind'] for r in tables['failure_cases']]).value_counts().to_dict(),
                 interpretation_counts=pd.Series([r['category'] for r in tables['interpretation_cases']]).value_counts().to_dict())
    load_spec()
    (OUTPUT/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k not in ['tables','input_hashes']},indent=2),flush=True)
    return summary


if __name__=='__main__':run()
