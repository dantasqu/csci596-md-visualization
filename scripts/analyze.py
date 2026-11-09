"""Make supporting scientific figures from the verified trajectory."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator
from verify import read_dump

ROOT=Path(__file__).resolve().parents[1]
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.linewidth':.8,'savefig.dpi':300})
def finish(ax):
    ax.tick_params(which='both',direction='in',top=True,right=True)
    ax.xaxis.set_minor_locator(AutoMinorLocator()); ax.yaxis.set_minor_locator(AutoMinorLocator())
def save(fig,name):
    fig.savefig(ROOT/f'figures/{name}.png',dpi=300)
    fig.savefig(ROOT/f'figures/{name}.svg')
    plt.close(fig)

t=np.genfromtxt(ROOT/'results/production/thermo.csv',delimiter=',',names=True)
fig,ax=plt.subplots(figsize=(5.99,3.9),layout='constrained')
for key,color,style,label in [('T_left','#c56217','-','Left half (initially hot)'),('T_right','#246b9e','--','Right half (initially cold)')]:
    ax.plot(t['time'],t[key],color=color,alpha=.22,lw=.7)
    window=9
    ax.plot(np.convolve(t['time'],np.ones(window)/window,'valid'),np.convolve(t[key],np.ones(window)/window,'valid'),color=color,ls=style,lw=1.6,label=label)
ax.set(xlabel='Time (Lennard-Jones units)',ylabel='Temperature (Lennard-Jones units)',xlim=(0,30),ylim=(.35,1.6))
ax.legend(frameon=False,fontsize=9); finish(ax)
save(fig,'temperature_evolution')
fig,ax=plt.subplots(figsize=(5.99,3.3),layout='constrained')
ax.plot(t['time'],100*(t['E_total']-t['E_total'][0])/abs(t['E_total'][0]),color='#246b9e',lw=1.2)
ax.set(xlabel='Time (Lennard-Jones units)',ylabel='Relative total-energy change (%)',xlim=(0,30)); finish(ax)
save(fig,'energy_conservation')

frames=list(read_dump(ROOT/'results/production/trajectory.dump'))
samples={'ke':[], 'speed_components':[], 'vm':[], 'components':[]}
temperature=[]
for step,box,d in frames:
    v=np.array([d[k] for k in ('vx','vy','vz')]).T
    samples['ke'].extend(d['ke']); samples['speed_components'].extend(abs(v).ravel())
    xx,yy,zz,xy,xz,yz=[d[k] for k in ('sxx','syy','szz','sxy','sxz','syz')]
    vm=np.sqrt(.5*((xx-yy)**2+(yy-zz)**2+(zz-xx)**2)+3*(xy**2+xz**2+yz**2))
    samples['vm'].extend(vm)
    samples['components'].extend(abs(np.array([xx,yy,zz,xy,xz,yz])).ravel())
    which=np.minimum((d['x']/box[0,1]*16).astype(int),15)
    row=[]
    for i in range(16):
        sub=v[which==i]
        row.append(np.mean(np.sum((sub-sub.mean(axis=0))**2,axis=1))/3)
    temperature.append(row)
fig,ax=plt.subplots(figsize=(5.99,3.9),layout='constrained')
im=ax.pcolormesh(np.linspace(0,1,17),np.linspace(-.075,30.075,len(frames)+1),np.array(temperature),vmin=.4,vmax=1.5,cmap='inferno',rasterized=True)
ax.set(xlabel='Position along box ($x/L_x$)',ylabel='Time (Lennard-Jones units)',ylim=(0,30))
fig.colorbar(im,ax=ax,label='Local temperature (Lennard-Jones units)'); finish(ax)
save(fig,'temperature_profile')
ranges={
    'kinetic_energy_max':float(np.quantile(samples['ke'],.995)),
    'velocity_component_limit':float(np.quantile(samples['speed_components'],.995)),
    'von_mises_max':float(np.quantile(samples['vm'],.995)),
    'stress_component_limit':float(np.quantile(samples['components'],.995)),
    'clipping_policy':'Fixed global 99.5th-percentile bounds; values outside the range saturate. All frames use identical bounds.',
    'temperature_curve_smoothing':'Nine-frame moving average (1.35 reduced time units); raw samples shown faintly.',
    'temperature_profile':'16 fixed spatial bins; subtract instantaneous mean velocity in each bin.'
}
(ROOT/'results/visualization_ranges.json').write_text(json.dumps(ranges,indent=2)+'\n')
print(json.dumps(ranges,indent=2))
