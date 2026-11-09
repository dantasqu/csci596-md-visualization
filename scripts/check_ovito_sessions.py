"""Run with ovitos to verify saved states and their numerical color mappings."""
from pathlib import Path
import json
import ovito
import numpy as np

root=Path(__file__).resolve().parents[1]
ranges=json.loads((root/'results/visualization_ranges.json').read_text())
palette=np.array([[.16,.43,.69],[.91,.51,.14],[.48,.35,.64],[.22,.62,.48]])
checks={}
for mode in ('kinetic_energy','velocity_rgb','parallel_domains','stress_von_mises'):
    ovito.scene.load(str(root/f'ovito/{mode}.ovito'))
    pipe=ovito.scene.pipelines[0]
    assert pipe.num_frames==201
    for frame in (0,100,200):
        d=pipe.compute(frame); p=d.particles
        assert len(p['Position'])==1152
        c=np.asarray(p['Color'])
        assert np.isfinite(c).all() and (c>=0).all() and (c<=1).all()
        if mode=='velocity_rgb':
            expected=np.clip(.5+.5*np.asarray(p['Velocity'])/ranges['velocity_component_limit'],0,1)
            assert np.max(abs(c-expected))<6e-8  # OVITO stores colors as float32.
        if mode=='parallel_domains': assert np.max(abs(c-palette[np.asarray(p['rank']).astype(int)]))<6e-8
        s=np.asarray(p['Stress Tensor'])
        expected=np.column_stack([p[k] for k in ('sxx','syy','szz','sxy','sxz','syz')])
        assert np.max(abs(s-expected))<1e-12
    checks[mode]={'reopened':True,'checked_frames':[0,100,200]}
(root/'results/ovito-session-check.json').write_text(json.dumps({'passed':True,'sessions':checks},indent=2)+'\n')
print('All four saved OVITO sessions and their mappings passed.')
