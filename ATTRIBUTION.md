# Attribution and source provenance

The baseline molecular-dynamics code is supplied by **Prof. Aiichiro Nakano** for **USC CSCI 596, Scientific Computing and Visualization**. This project extends that teaching code; it does not claim authorship of the original molecular-dynamics algorithm or starter implementation.

- Instructor profile: <https://github.com/aiichironakano>
- Course page: <https://aiichironakano.github.io/cs596.html>
- Instructor's parallel/hybrid MD repository: <https://github.com/aiichironakano/scicomp>
- Visualization lecture: <https://aiichironakano.github.io/cs596/VMD.pdf>

The exact starter files used here came from the **Assignment 4 course package**. They are preserved in `original/`; their SHA-256 digests are in `original/SHA256.json`. The public `scicomp` repository is provided as related instructor material, not as a claim that its current files are byte-identical to this starter package.

The Assignment 7 handout suggests kinetic-energy coloring, velocity-to-RGB mapping, parallel MD animation, and atomic stress visualization. Those suggestions motivate this project's scope.

Project-specific additions are the hot/cold setup, stable IDs in migration messages, diagnostic export, analysis and verification, and OVITO rendering. Modifications to the starter files are explicitly marked. The trajectory, plots, and movies in this repository were generated from the actual four-rank run recorded in `results/`.

The original starter files do not include an explicit license declaration in the supplied package. This repository does not apply a new blanket license to those files. Attribution is retained.

Rendering and analysis use [OVITO](https://www.ovito.org/), [NumPy](https://numpy.org/), and [Matplotlib](https://matplotlib.org/). Their software is not redistributed in this repository.
