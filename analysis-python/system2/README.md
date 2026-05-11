# System 2 Animation

Postprocessing-only animation for the TP4 System 2 Java raw outputs.

The script reads:

- `metadata.json`
- `states.csv`
- `contact_events.csv` when present, to color particles as fresh/used

It does not run or modify the Java simulation motor.

## Usage

From the repository root:

```bash
python3 analysis-python/system2/animate_system2.py \
  --input-dir outputs/system2-smoke-local \
  --output outputs/system2-smoke-local/animation.mp4
```

Useful preview options:

```bash
python3 analysis-python/system2/animate_system2.py \
  --input-dir SdS_TP4_2026Q1G01CS2_Codigo/outputs/system2/system2-example \
  --output SdS_TP4_2026Q1G01CS2_Codigo/outputs/system2/system2-example/animation.mp4 \
  --fps 20 \
  --frame-stride 1 \
  --max-frames 20
```

By default the script refuses to replace an existing output file. Use
`--overwrite` only when intentionally regenerating the same animation.

## State Coloring

The Java output contract writes `states.csv` with:

```text
step,t,particle_id,x,y,vx,vy
```

It does not export `fresh`, `used`, or `state` columns directly. When
`contact_events.csv` exists, the animation reconstructs state from:

- `particle_obstacle_begin`: marks a particle as used.
- `particle_wall_begin`: marks a particle as fresh again.

Particles are rendered green while fresh and purple while used. If
`contact_events.csv` is missing, the script falls back to a plain position
animation with one particle color.
