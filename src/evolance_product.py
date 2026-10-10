"""Product adapter over immutable Evolance v1.1; no downloads or research writes."""
import hashlib
import numpy as np
import pandas as pd
from src.evolance.v1_1.spec import SPEC, load_spec
from src.evolance.v1_1.metrics import evidence
from src.evolance.v1_1.scoring import score_evidence
from src.evolance.v1_1.states import interpret
from src.evolance.v1_1.outlook import forward_distributions, interpret_outlook
from src.future_simulation import estimate_parameters
from src.portfolio_analysis import validate_weights
from src.i18n import tr


def latest_outlooks(returns, existing=None):
    """Reuse only an exactly compatible existing simulation; otherwise frozen helper."""
    cfg=SPEC['forward']; parameters=estimate_parameters(returns)
    if existing and existing.get('parameters')==parameters:
        sim=existing.get('simulation',{})
        if all(sim.get(k)==v for k,v in {'initial_value':cfg['initial_value'],'horizon':1,'simulations':cfg['simulations'],'seed':cfg['seed']}.items()):
            paths=np.asarray(sim.get('paths'))
            if paths.shape==(13,cfg['simulations']) and np.isfinite(paths).all():
                result={}
                for months in cfg['horizons_months']:
                    terminal=paths[months]/cfg['initial_value']-1
                    q=np.percentile(terminal,[10,50,90])
                    result[months]=dict(months=months,p10=float(q[0]),p50=float(q[1]),p90=float(q[2]),probability_up=float(np.mean(terminal>0)),loss_probability=float(np.mean(terminal<0)),tie_probability=float(np.mean(terminal==0)))
                return result
    return forward_distributions(returns)


def build_comparison(prices,config,synthetic=False,existing=None):
    load_spec()
    missing=dict(status='insufficient',synthetic=synthetic)
    if prices is None or len(prices)<253:return missing
    weights=dict(zip(config['tickers'],validate_weights(config['tickers'],config['weights'])))
    needed=list(dict.fromkeys([*weights,config['benchmark']]))
    if not set(needed).issubset(prices.columns):return missing
    frame=prices[needed]
    if (not isinstance(frame.index,pd.DatetimeIndex) or frame.index.tz is not None or frame.index.has_duplicates
        or frame.index.hasnans or not frame.index.is_monotonic_increasing
        or not np.isfinite(frame.to_numpy()).all() or (frame<=0).any().any()
        or frame.index.to_series().diff().dt.days.max()>SPEC['history']['max_gap_days']):
        return dict(status='quality',synthetic=synthetic)
    history=[];periods=frame.index.to_period('M')
    for period in periods.unique():
        end=period.end_time.normalize();pos=int(np.flatnonzero(periods==period)[-1])
        if end>frame.index[-1] or pos<252:continue
        metrics,returns=evidence(frame.iloc[pos-252:pos+1],weights,config['benchmark'])
        scored=score_evidence(metrics,history);state=interpret(scored,metrics,history)
        history.append(dict(date=frame.index[pos].date().isoformat(),window_start=frame.index[pos-252].date().isoformat(),available_at=end.date().isoformat(),metrics=metrics,**scored,**state))
    if not history:return missing
    latest=history[-1]
    distributions=latest_outlooks(returns,existing)
    latest['outlooks']={str(m):interpret_outlook(d,latest['metrics'],latest['scores'],latest,synthetic) for m,d in distributions.items()}
    return dict(status='ready',synthetic=synthetic,latest=latest)


def comparison_for(historical):
    """Cache per in-memory analysis; language changes never recalculate simulation."""
    prices=historical.get('evolance_prices');cfg=historical.get('portfolio_config')
    demo=any(m.get('provider')=='demo' for m in historical.get('source_metadata',{}).values())
    if prices is None or cfg is None:return dict(status='insufficient',synthetic=demo)
    key=hashlib.sha256(pd.util.hash_pandas_object(prices,index=True).values.tobytes()+repr((list(prices.columns),cfg,demo)).encode()).hexdigest()
    if historical.get('_evolance_key')!=key:
        historical['_evolance_result']=build_comparison(prices,cfg,demo,historical.get('future_outlook'))
        historical['_evolance_key']=key
    return historical['_evolance_result']


def conclusion(row,language):
    t=lambda k,**v:tr('ev_'+k,language,**v)
    out=row['outlooks']['12']
    flags=', '.join(t(f) for f in row['flags']) if row['flags'] else t('no_flags')
    if language == '中文':
        flags = t('copy_flags', flags='、'.join(t(f) for f in row['flags'])) if row['flags'] else t('no_flags')
        return t('conclusion', state=t(row['confirmed_state']),
                 transition=t('copy_transition_' + row['transition']),
                 direction=t(out['direction']), confidence=t(out['confidence']), flags=flags)
    return t('conclusion',state=t(row['confirmed_state']),transition=t(row['transition']),direction=t(out['direction']),confidence=t(out['confidence']),flags=flags)
