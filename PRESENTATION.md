# One-minute GitHub presentation

**Visualizing thermal equilibration in parallel molecular dynamics**  
Daniela Dantas Quintana · CSCI 596

The Fall 2026 final-project handout asks for an informal presentation of about one minute, showing the preliminary GitHub repository. Use the repository README as the visual aid.

## What to open

Open **[the repository README](README.md)** before your turn. Let the kinetic-energy animation load. Keep the temperature graph visible alongside it. Use a browser zoom level that makes both images and their labels readable.

## Speaking script

My project extends our parallel molecular-dynamics code to visualize how a temperature imbalance relaxes. I simulated 1,152 Lennard-Jones atoms with four MPI processes, starting one half hot and the other cold.

In this animation, color represents each atom's kinetic energy. I also created views that map velocity components to RGB, identify the MPI process owning each atom, and display per-atom stress.

The temperature plot shows the two halves approaching a common value near 0.8. I checked that total-energy drift stayed below 0.013 percent and independently verified the stress calculation.

The contribution is a reproducible workflow connecting parallel simulation, physical measurements, and visualization. The repository contains the modified code, actual data, verification, and all four movies.

## Where to point while speaking

| Time | Show in README | Say |
|---|---|---|
| 0–15 seconds | **Problem** and **Method** | The question, starting temperatures, atom count, and four MPI processes |
| 15–35 seconds | The animation and **Four views** | What the colors encode and which extensions were implemented |
| 35–50 seconds | Temperature graph and **Results** | Temperatures approach 0.8; energy and stress were checked |
| 50–60 seconds | **What I added** / **Evidence** | The contribution and reproducible files |

The script is about 115 words. Rehearse it aloud once and shorten a sentence if needed to leave time for scrolling. The MP4 links and the [stress-component image](figures/stress_tensor_components.png) are useful if questions follow; they do not need to be opened during the timed minute.

## Before presenting

- Open the repository while signed out once to confirm the instructor can access it.
- Allow the animation and plot to load before starting.
- Keep the [Q&A](docs/QUESTIONS.md) available for rehearsal.
- Be ready to point to the marked changes in `src/pmd.c` and `src/visualization.h`.
- Describe the observed results as one finite-system simulation; do not claim a thermal-conductivity measurement or a speedup benchmark.

Dates and submission details are recorded in [course requirements](docs/COURSE_REQUIREMENTS.md).
