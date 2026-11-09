"""Arrange the scientific OVITO renders without altering their content."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

ROOT=Path(__file__).resolve().parents[1]
def compose(files,name,shape):
    rows,cols=shape
    fig,axes=plt.subplots(rows,cols,figsize=(5.99,5.99*rows/cols*.75),dpi=400)
    for ax,file in zip(axes.flat,files):
        ax.imshow(mpimg.imread(ROOT/'figures'/file)); ax.axis('off')
    fig.subplots_adjust(0,0,1,1,wspace=.015,hspace=.025)
    fig.savefig(ROOT/f'figures/{name}.png',dpi=400)
    plt.close(fig)
compose([f'{mode}_initial.png' for mode in ('kinetic_energy','velocity_rgb','parallel_domains','stress_von_mises')],'visualization_overview',(2,2))
compose([f'stress_{c}.png' for c in ('sxx','syy','szz','sxy','sxz','syz')],'stress_tensor_components',(3,2))
compose(['kinetic_energy_initial.png','kinetic_energy_final.png'],'thermal_equilibration_comparison',(1,2))
