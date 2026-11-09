"""Check actual MPI results, including an independent minimum-image pair sum."""
from pathlib import Path
import json, re, hashlib
import numpy as np

ROOT=Path(__file__).resolve().parents[1]

def read_dump(path):
    with Path(path).open() as f:
        while True:
            line=f.readline()
            if not line:
                return
            assert line.strip()=='ITEM: TIMESTEP'
            step=int(f.readline()); assert f.readline().strip()=='ITEM: NUMBER OF ATOMS'
            count=int(f.readline()); assert f.readline().strip()=='ITEM: BOX BOUNDS pp pp pp'
            box=np.array([list(map(float,f.readline().split())) for _ in range(3)])
            columns=f.readline().split()[2:]
            values=np.array([list(map(float,f.readline().split())) for _ in range(count)])
            yield step,box,dict(zip(columns,values.T))

def verify():
    numeric=re.compile(r'^\s*[0-9]+\.[0-9]+\s+[-0-9]')
    def rows(name):
        return [line.strip() for line in (ROOT/f'results/{name}/pmd.out').read_text().splitlines() if numeric.match(line)]
    assert rows('baseline')==rows('instrumented-check'), 'Baseline behavior changed'
    assert len(rows('baseline'))==4
    table=np.genfromtxt(ROOT/'results/production/thermo.csv',delimiter=',',names=True)
    frames=list(read_dump(ROOT/'results/production/trajectory.dump'))
    assert len(frames)==201==len(table)
    assert frames[0][0]==0 and frames[-1][0]==6000
    errors={'kinetic_energy':0.,'temperature':0.,'momentum':0.,'stress_tensor':0.,'potential_energy':0.}
    initial_owner=None; changed_owner=0
    for k,(step,box,d) in enumerate(frames):
        n=len(d['id']); lengths=box[:,1]-box[:,0]
        assert n==1152 and np.array_equal(d['id'],np.arange(1,n+1))
        assert np.array_equal(d['rank'],d['rank'].astype(int))
        assert set(d['rank'])=={0,1,2,3}
        xyz=np.array([d[x] for x in ('x','y','z')]).T
        vel=np.array([d[x] for x in ('vx','vy','vz')]).T
        assert np.isfinite(xyz).all() and np.isfinite(vel).all()
        assert (xyz>=-1e-9).all() and (xyz<lengths+1e-9).all()
        expected_rank=(xyz[:,0]>=lengths[0]/2).astype(int)*2+(xyz[:,1]>=lengths[1]/2).astype(int)
        assert np.array_equal(d['rank'],expected_rank)
        if initial_owner is None: initial_owner=d['rank'].copy()
        changed_owner=max(changed_owner,int(np.count_nonzero(d['rank']!=initial_owner)))
        ke=.5*np.sum(vel**2,axis=1)
        errors['kinetic_energy']=max(errors['kinetic_energy'],float(np.max(abs(ke-d['ke']))))
        for g,label in enumerate(('T_left','T_right')):
            group=(xyz[:,0]<lengths[0]/2) if g==0 else (xyz[:,0]>=lengths[0]/2)
            sub=vel[group]; temp=np.mean(np.sum((sub-sub.mean(axis=0))**2,axis=1))/3
            errors['temperature']=max(errors['temperature'],float(abs(temp-table[label][k])))
        errors['momentum']=max(errors['momentum'],float(np.max(abs(vel.sum(axis=0)))))
        assert abs(np.mean(ke)*2/3-table['T_global'][k])<1e-9
        if k in (0,len(frames)//2,len(frames)-1):
            dr=xyz[:,None,:]-xyz[None,:,:]
            dr-=lengths*np.rint(dr/lengths)
            rr=np.sum(dr**2,axis=2)
            mask=(rr>0)&(rr<2.5**2)
            ri2=np.zeros_like(rr); ri2[mask]=1/rr[mask]
            ri6=ri2**3
            duc=-48*(2.5**-6)*(2.5**-6-.5)/2.5
            fc=np.zeros_like(rr); fc[mask]=48*ri2[mask]*ri6[mask]*(ri6[mask]-.5)+duc/np.sqrt(rr[mask])
            virial=.5*np.einsum('ij,ija,ijb->iab',fc,dr,dr)
            sigma=n/np.prod(lengths)*(np.einsum('ia,ib->iab',vel,vel)+virial)
            indices=((0,0),(1,1),(2,2),(0,1),(0,2),(1,2))
            for label,(a,b) in zip(('sxx','syy','szz','sxy','sxz','syz'),indices):
                errors['stress_tensor']=max(errors['stress_tensor'],float(np.max(abs(sigma[:,a,b]-d[label]))))
            uc=4*2.5**-6*(2.5**-6-1)
            pair=4*ri6[mask]*(ri6[mask]-1)-uc-duc*(np.sqrt(rr[mask])-2.5)
            u=pair.sum()/(2*n)
            errors['potential_energy']=max(errors['potential_energy'],float(abs(u-table['E_potential'][k])))
            assert abs(u+ke.mean()-table['E_total'][k])<2e-8
    assert errors['stress_tensor']<2e-7,errors
    assert errors['potential_energy']<2e-8,errors
    assert errors['temperature']<1e-9 and errors['kinetic_energy']<1e-9,errors
    assert errors['momentum']<1e-7,errors
    assert changed_owner>0, 'No evidence of ownership changes'
    assert abs(table['T_left'][0]-1.5)<1e-9 and abs(table['T_right'][0]-.5)<1e-9
    drift=float(np.max(abs(table['E_total']-table['E_total'][0])))
    relative=drift/abs(float(table['E_total'][0]))
    assert relative<.001, f'Energy drift too large: {relative}'
    late=table[table['time']>=20]
    report={
      'passed':True,'atoms':1152,'MPI_ranks':4,'frames':201,'steps':6000,'time_step':.005,'simulation_time':30,
      'baseline_unchanged':True,'independent_pair_check_frames':[0,100,200],
      'maximum_errors':errors,'maximum_absolute_energy_drift_per_atom':drift,'maximum_relative_energy_drift':relative,
      'initial_spatial_temperatures':[float(table['T_left'][0]),float(table['T_right'][0])],
      'late_interval':[20,30], 'late_mean_spatial_temperatures':[float(late['T_left'].mean()),float(late['T_right'].mean())],
      'late_mean_temperature_difference':float((late['T_left']-late['T_right']).mean()),
      'maximum_atoms_with_changed_MPI_owner':changed_owner,
      'trajectory_sha256':hashlib.sha256((ROOT/'results/production/trajectory.dump').read_bytes()).hexdigest()
    }
    (ROOT/'results/verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__': verify()
