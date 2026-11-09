"""Render all four Assignment 7 project extensions with OVITO Pro."""
from pathlib import Path
import argparse,json,inspect
import numpy as np
import ovito
from ovito.io import import_file
from ovito.vis import Viewport,TachyonRenderer,TextLabelOverlay,ColorLegendOverlay
from ovito.modifiers import ColorCodingModifier,PythonScriptModifier
from PySide6.QtCore import Qt

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--preview',action='store_true')
args=parser.parse_args()
ranges=json.loads((ROOT/'results/visualization_ranges.json').read_text())
palette=np.array([[.16,.43,.69],[.91,.51,.14],[.48,.35,.64],[.22,.62,.48]])

def add_properties(frame,data):
    p=data.particles_
    v=np.asarray(p['Velocity']); xx,yy,zz,xy,xz,yz=[np.asarray(p[k]) for k in ('sxx','syy','szz','sxy','sxz','syz')]
    p.create_property('Stress Tensor',data=np.column_stack([xx,yy,zz,xy,xz,yz]))
    vm=np.sqrt(.5*((xx-yy)**2+(yy-zz)**2+(zz-xx)**2)+3*(xy**2+xz**2+yz**2))
    p.create_property('Von Mises',data=vm)
    p.create_property('Kinetic Energy',data=np.asarray(p['ke']))
    data.attributes['TimeLabel']=f"{data.attributes['Timestep']*.005:.2f}"

def color_velocity(frame,data):
    v=np.asarray(data.particles['Velocity'])
    data.particles_.create_property('Color',data=np.clip(.5+.5*v/ranges['velocity_component_limit'],0,1))

def color_rank(frame,data):
    data.particles_.create_property('Color',data=palette[np.asarray(data.particles['rank']).astype(int)])

def saved_modifier(function):
    code=inspect.getsource(function).replace('def '+function.__name__+'(', 'def modify(')
    code=code.replace("ranges['velocity_component_limit']",repr(ranges['velocity_component_limit']))
    prefix='import numpy as np\n'
    if function is color_rank: prefix+='palette=np.array('+repr(palette.tolist())+')\n'
    return PythonScriptModifier(script=prefix+code)

def setup(mode):
    for pipe in list(ovito.scene.pipelines): pipe.remove_from_scene()
    pipe=import_file(str(ROOT/'results/production/trajectory.dump'))
    pipe.modifiers.append(saved_modifier(add_properties))
    mapping=None
    if mode=='kinetic_energy':
        prop='Kinetic Energy'; end=ranges['kinetic_energy_max']; title='Kinetic energy (LJ units)'
        mapping=ColorCodingModifier(property=prop,start_value=0,end_value=end,gradient=ColorCodingModifier.Viridis())
    elif mode=='stress_von_mises':
        prop='Von Mises'; end=ranges['von_mises_max']; title='Von Mises stress (LJ units)'
        mapping=ColorCodingModifier(property=prop,start_value=0,end_value=end,gradient=ColorCodingModifier.Magma())
    elif mode=='velocity_rgb': pipe.modifiers.append(saved_modifier(color_velocity))
    elif mode=='parallel_domains': pipe.modifiers.append(saved_modifier(color_rank))
    else:
        prop=mode; end=ranges['stress_component_limit']; title=f'{mode} (LJ units)'
        mapping=ColorCodingModifier(property=prop,start_value=-end,end_value=end,gradient=ColorCodingModifier.BlueWhiteRed())
    if mapping is not None: pipe.modifiers.append(mapping)
    d=pipe.compute(); d.particles.vis.radius=.38
    d.cell.vis.render_cell=True; d.cell.vis.line_width=.025
    pipe.add_to_scene()
    vp=Viewport(type=Viewport.Type.Ortho)
    box=np.diag(d.cell.matrix[:,:3]); center=box/2
    direction=np.array([-.22,1.,-.35]); direction/=np.linalg.norm(direction)
    vp.camera_dir=tuple(direction); vp.camera_pos=tuple(center-direction*40); vp.camera_up=(0,0,1)
    vp.fov=9.8
    labels={'kinetic_energy':'Kinetic energy','velocity_rgb':'Velocity components mapped to RGB','parallel_domains':'Parallel MD: four MPI domains','stress_von_mises':'Per-atom stress: von Mises invariant'}
    label=labels.get(mode,f'Stress component: {mode}')
    vp.overlays.append(TextLabelOverlay(text=label,alignment=Qt.AlignmentFlag.AlignTop|Qt.AlignmentFlag.AlignLeft,offset_x=.025,offset_y=.025,font_size=.032,text_color=(.1,.1,.1)))
    vp.overlays.append(TextLabelOverlay(text='t = [TimeLabel] LJ units | 1,152 atoms',pipeline=pipe,alignment=Qt.AlignmentFlag.AlignTop|Qt.AlignmentFlag.AlignRight,offset_x=-.025,offset_y=-.055,font_size=.024,text_color=(.2,.2,.2)))
    if mapping is not None:
        vp.overlays.append(ColorLegendOverlay(modifier=mapping,title=title,alignment=Qt.AlignmentFlag.AlignBottom|Qt.AlignmentFlag.AlignHCenter,offset_y=.035,legend_size=.42,aspect_ratio=18,font_size=.085,format_string='%.2f'))
    else:
        text='R = vx, G = vy, B = vz | fixed symmetric component scale' if mode=='velocity_rgb' else 'MPI rank: 0 blue | 1 orange | 2 purple | 3 green'
        vp.overlays.append(TextLabelOverlay(text=text,alignment=Qt.AlignmentFlag.AlignBottom|Qt.AlignmentFlag.AlignHCenter,offset_y=.04,font_size=.023,text_color=(.15,.15,.15)))
    return pipe,vp

renderer=TachyonRenderer(ambient_occlusion=True,ambient_occlusion_samples=6,shadows=False,antialiasing=True,antialiasing_samples=6)
for mode in ('kinetic_energy','velocity_rgb','parallel_domains','stress_von_mises'):
    pipe,vp=setup(mode)
    for frame,suffix in ((0,'initial'),(200,'final')):
        vp.render_image(filename=str(ROOT/f'figures/{mode}_{suffix}.png'),size=(1000,750),frame=frame,renderer=renderer)
    ovito.scene.viewports.active_vp.camera_pos=vp.camera_pos
    ovito.scene.viewports.active_vp.camera_dir=vp.camera_dir
    ovito.scene.viewports.active_vp.camera_up=vp.camera_up
    ovito.scene.viewports.active_vp.type=vp.type
    ovito.scene.viewports.active_vp.fov=vp.fov
    ovito.scene.viewports.active_vp.overlays.clear()
    ovito.scene.viewports.active_vp.overlays.extend(vp.overlays)
    ovito.scene.save(str(ROOT/f'ovito/{mode}.ovito'))
    print('PREVIEW',mode,flush=True)
    if not args.preview:
        vp.render_anim(filename=str(ROOT/f'movies/{mode}.mp4'),size=(960,720),fps=20,range=(0,200),renderer=renderer)
        print('MOVIE',mode,'201 frames',flush=True)
for component in ('sxx','syy','szz','sxy','sxz','syz'):
    pipe,vp=setup(component)
    vp.render_image(filename=str(ROOT/f'figures/stress_{component}.png'),size=(800,600),frame=100,renderer=renderer)
    print('STRESS',component,flush=True)
(ROOT/'results/ovito-render.json').write_text(json.dumps({'OVITO_version':ovito.version_string,'frames_per_movie':201,'fps':20,'resolution':[960,720],'preview_only':args.preview},indent=2)+'\n')
