"""Analyze the untouched PWM, encoder degrees, elapsed milliseconds log.
Requires numpy and matplotlib. Fits T by one-dimensional variable projection.
"""
from pathlib import Path
import csv, json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent
SOURCE = OUT.parent / 'Husanboy_motor_data.txt'
data = np.loadtxt(SOURCE, delimiter=',')
assert data.ndim == 2 and data.shape[1] == 3 and np.isfinite(data).all()
assert np.array_equal(np.unique(data[:, 0]), np.arange(-100, 101, 5))

def basis(t, T):
    return t + T * np.expm1(-t / T)

def fit(t, theta):
    # At each T, the least-squares optimum for signed omega is analytic.
    grid = np.geomspace(0.0001, 5., 2500)
    b = basis(t[:, None], grid[None, :])
    w = (theta @ b) / (b*b).sum(axis=0)
    loss = ((theta[:, None] - b*w)**2).sum(axis=0)
    i = int(np.argmin(loss))
    lo, hi = grid[max(0, i-1)], grid[min(len(grid)-1, i+1)]
    def objective(T)
        b = basis(t, T)
        w = np.dot(theta,b) / np.dot(b,b)
        return np.sum((theta-w*b)**2), w
    # Golden-section refinement, retaining global grid search robustness.
    for _ in range(60):
        a = hi - (hi-lo)/1.61803398875
        c = lo + (hi-lo)/1.61803398875
        if objective(a)[0] < objective(c)[0]: hi = c
        else: lo = a
    T = (lo+hi)/2
    loss, w = objective(T)
    return T, w, w*basis(t,T), i in (0,len(grid)-1)

results=[]; series={}; intervals=[]
for pwm in np.arange(-100,101,5):
    d = data[data[:,0] == pwm]
    t, theta = d[:,2]/1000, np.deg2rad(d[:,1])
    assert np.all(np.diff(t)>0), f'Non-increasing time at PWM {pwm}'
    intervals.extend(np.diff(d[:,2]))
    tail = t>=1.5
    tail_w = np.polyfit(t[tail],theta[tail],1)[0]
    early_w = np.polyfit(t[(t>=.5)&(t<=1)],theta[(t>=.5)&(t<=1)],1)[0]
    late_w = np.polyfit(t[t>=1],theta[t>=1],1)[0]
    stationary = np.ptp(theta) == 0
    if stationary:
        T,w,pred,bound = np.nan,0,np.zeros_like(t),False
        r2=np.nan
    else:
        T,w,pred,bound=fit(t,theta)
        r2=1-np.sum((theta-pred)**2)/np.sum((theta-theta.mean())**2)
    rmse=float(np.rad2deg(np.sqrt(np.mean((theta-pred)**2))))
    # Flag unresolved dynamics, or a substantial speed change after acceleration.
    drift=abs(late_w-early_w)/max(abs(late_w),abs(early_w),.01)
    flags=[]
    if stationary: flags.append('no motion; T unidentifiable')
    else:
        if bound: flags.append('T at search bound; unidentifiable')
        if T<.02: flags.append('T below/near sample interval')
        if T>.5: flags.append('slow fit; steady state uncertain')
        if r2<.99:flags.append('model mismatch')
        if drift>.2:flags.append('speed changes after 0.5 s')
    row=dict(pwm_percent=int(pwm),samples=len(t),first_ms=int(d[0,2]),last_ms=int(d[-1,2]),
             median_interval_ms=float(np.median(np.diff(d[:,2]))),final_angle_deg=float(d[-1,1]),
             T_m_s=float(T),omega_fit_rad_s=float(w),omega_tail_rad_s=float(tail_w),
             rmse_deg=rmse,r_squared=float(r2),speed_drift_fraction=float(drift),flags='; '.join(flags))
    results.append(row);series[int(pwm)]=(t,theta,pred)
with (OUT/'motor_parameters.csv').open('w') as f:
    writer=csv.DictWriter(f,fieldnames=list(results[0]));writer.writeheader();writer.writerows(results)

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,axes=plt.subplots(2,2,figsize=(12,8),layout='constrained')
p=np.array([r['pwm_percent'] for r in results]);w=np.array([r['omega_tail_rad_s'] for r in results]);wf=np.array([r['omega_fit_rad_s'] for r in results]);Ts=np.array([r['T_m_s'] for r in results])
ax=axes[0,0];ax.plot(p,w,'o-',label='Measured slope, final 0.5 s');ax.plot(p,wf,'.--',label='First-order fitted asymptote',alpha=.7);ax.axhline(0,color='gray',lw=.6);ax.axvline(0,color='gray',lw=.6);ax.set(xlabel='PWM (%)',ylabel='Angular speed (rad/s)',title='Speed versus power — one motor');ax.legend(fontsize=8)
ax=axes[0,1];pos=p>0;neg=p<0;ax.plot(p[pos],w[pos],'o-',label='Forward');ax.plot(-p[neg][::-1],-w[neg][::-1],'o-',label='Reverse magnitude');ax.set(xlabel='Absolute PWM (%)',ylabel='Speed magnitude (rad/s)',title='Direction comparison');ax.legend()
ax=axes[1,0];valid_T=np.where((Ts>0.00011)&(Ts<4.99),Ts,np.nan);ax.semilogy(p,valid_T,'o-');ax.axhline(.016,color='gray',ls='--',label='Typical sample interval');ax.set(xlabel='PWM (%)',ylabel='Fitted T (s, logarithmic scale)',title='Response times — unresolved fits omitted');ax.legend(fontsize=8)
ax=axes[1,1];ax.hist(intervals,bins=np.arange(0,52,2),color='#277c8e');ax.set(xlabel='Actual sample interval (ms)',ylabel='Count',title='Recorded timing (5 ms requested)')
fig.savefig(OUT/'motor_overview.png',dpi=180);plt.close(fig)
fig,axes=plt.subplots(2,2,figsize=(12,8),layout='constrained')
for ax,power in zip(axes.flat,[100,-100,-60,5]):
    t,theta,pred=series[power];r=next(r for r in results if r['pwm_percent']==power)
    ax.plot(t,np.rad2deg(theta),'.',ms=3,label='Encoder measurement');ax.plot(t,np.rad2deg(pred),lw=2,label='First-order model')
    T_label = 'T unresolved' if r['T_m_s']<.00011 or r['T_m_s']>4.99 else f'T={r["T_m_s"]:.3f} s'
    ax.set(xlabel='Elapsed time (s)',ylabel='Angle (degrees)',title=f'PWM {power:+d}%: {T_label}, RMSE={r["rmse_deg"]:.1f}°');ax.legend(fontsize=8)
fig.savefig(OUT/'step_responses.png',dpi=180);plt.close(fig)

summary={'rows':len(data),'power_levels':len(results),'median_interval_ms':float(np.median(intervals)),'min_interval_ms':float(min(intervals)),'max_interval_ms':float(max(intervals)),'zero_motion_pwm':[r['pwm_percent'] for r in results if r['final_angle_deg']==0],'full_power':{str(r['pwm_percent']):r for r in results if abs(r['pwm_percent'])==100},'flagged':[r for r in results if r['flags']]}
def clean(value):
    if isinstance(value,float) and not np.isfinite(value): return None
    if isinstance(value,dict): return {k:clean(v) for k,v in value.items()}
    if isinstance(value,list): return [clean(v) for v in value]
    return value
summary=clean(summary)
(OUT/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False))
print(json.dumps(summary,indent=2))
