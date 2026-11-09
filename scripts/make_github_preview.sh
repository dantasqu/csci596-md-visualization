#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p figures/github
ffmpeg -hide_banner -v error -threads 1 -filter_complex_threads 1 -y \
  -i movies/kinetic_energy.mp4 \
  -filter_complex '[0:v]fps=8,scale=560:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer:bayer_scale=3' \
  -threads 1 -loop 0 figures/github/kinetic_energy.gif
