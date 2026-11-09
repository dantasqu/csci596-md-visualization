# Questions to prepare for

## What is the main question?

How does a hot/cold temperature imbalance relax in a periodic molecular-dynamics simulation, and how do complementary property views help explain the dynamics?

## How is this different from Assignment 7?

Assignment 7 visualized the supplied trajectory and cube file. This project generates a new trajectory with the parallel MD program and adds physical-property export, persistent IDs across MPI migration, four property views, quantitative temperature plots, and independent verification. The four extensions are explicitly suggested in the handout.

## What code did you modify?

I extended the instructor's `pmd.c` and changed the MPI grid in `pmd.h`. The marked changes add hooks for preparation/output, stable atom IDs in migration messages, and per-atom virial accumulation. `visualization.h` implements hot/cold initialization, resident-atom gathering, and output. The original force law, integrator, periodic boundary treatment, and linked-cell approach are retained.

## How are hot and cold temperatures imposed?

After a 2,000-step preparation period, I divide the current positions at x = Lx/2, subtract each half's mean velocity, and rescale velocities once to temperatures 1.5 and 0.5. Production then runs for 6,000 steps without a thermostat. Temperatures are measured in fixed spatial halves, not fixed sets of atoms.

## Why do the temperatures approach about 0.8 rather than the initial average of 1.0?

Temperature measures kinetic energy. Kinetic and potential energy exchange while total energy remains nearly constant. The average initial temperature therefore does not have to remain the final kinetic temperature. The measured late-time values are approximately 0.800 and 0.793, with finite-system fluctuations.

## What units are used?

Lennard-Jones reduced units: particle mass, Boltzmann constant, the potential energy scale, and the length scale are set to one. The temperatures are not Kelvin. Stress has reduced energy-per-volume units.

## What do the RGB colors mean?

The x, y, and z velocity components are mapped to red, green, and blue. Each component has a fixed symmetric scale: zero maps to 0.5, positive values increase that channel, and negative values decrease it. Extreme values saturate. The numerical bound is fixed from the full trajectory, so it does not change frame by frame.

## What stress is being shown?

The tensor follows the Assignment 7 formula: a kinetic term plus half the sum of pair virials, multiplied by number density. The force includes the starter's cutoff force shift. Six components describe the symmetric 3×3 tensor. The movie colors the von Mises invariant; the six-component image shows the individual components. This scalar view does not establish plastic yielding.

## How did you verify the calculations?

The visualization-disabled short run reproduces the original program's printed results. Independent calculations from the exported velocities check kinetic energy, regional temperature, and total momentum. A separate all-pairs minimum-image calculation checks potential energy and all six stress components at three frames. I also verify atom count, unique IDs, MPI ownership, movie decoding, and saved-session color mappings.

## Is this really a parallel simulation?

Yes. The actual run uses four MPI ranks on four CPU cores of one Discovery node with a 2×2×1 domain grid. Rank colors show the current owner; IDs remain stable when atoms migrate. This demonstrates parallel computation and data gathering, but is not a multi-node scalability study.

## Why are the color limits fixed?

Changing the color range in each frame could make the same physical value appear as different colors over time. Fixed ranges make frames comparable. The global 99.5th-percentile bounds limit the effect of rare extremes, and values outside the bounds are explicitly saturated.

## What are the main limitations and next steps?

The evidence is one finite system and one initialization. A stronger statistical study would use independent seeds, other system sizes, and a smaller time step. A transport study would need a method designed to estimate thermal conductivity. Additional rendering choices could expose interior atoms or visualize principal stress directions. These are possible extensions, not completed results.

## Can another student reproduce the work?

The repository contains source, original starter files, input parameters, actual trajectory, thermodynamic output, verification scripts, and rendering scripts. Discovery users with the class allocation can use the supplied Slurm script; analysis uses NumPy/Matplotlib and rendering uses OVITO Pro 3.16.1.
