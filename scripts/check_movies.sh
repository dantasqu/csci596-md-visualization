#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
module load ffmpeg/7.0
mkdir -p results/media-check
for mode in kinetic_energy velocity_rgb parallel_domains stress_von_mises; do
  ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=codec_name,width,height,pix_fmt,r_frame_rate,nb_read_frames,duration -of json "movies/$mode.mp4" > "results/media-check/$mode.json"
  ffmpeg -hide_banner -v error -threads 1 -filter_threads 1 -i "movies/$mode.mp4" -threads 1 -f null - 2> "results/media-check/$mode-decode.log"
  ffmpeg -hide_banner -v error -threads 1 -filter_threads 1 -y -i "movies/$mode.mp4" -vf "select='eq(n,0)+eq(n,100)+eq(n,200)',scale=480:360,tile=3x1" -threads 1 -frames:v 1 "results/media-check/$mode-contact.png"
done
python3 - <<'PY'
import json
from pathlib import Path
result={}
for p in Path('results/media-check').glob('*.json'):
    if p.name=='verification.json': continue
    d=json.loads(p.read_text())['streams'][0]
    assert int(d['nb_read_frames'])==201,(p,d)
    assert (d['width'],d['height'])==(960,720)
    assert d['r_frame_rate']=='20/1'
    assert abs(float(d['duration'])-10.05)<.01
    assert not (p.parent/(p.stem+'-decode.log')).read_text().strip()
    result[p.stem]=d
assert len(result)==4
Path('results/media-check/verification.json').write_text(json.dumps({'passed':True,'movies':result},indent=2)+'\n')
print('All four movies decoded: 201 frames, 20 fps, 10.05 seconds, 960x720.')
PY
