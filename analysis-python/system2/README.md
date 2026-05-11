# System 2 Animation

Postprocessing-only animation for the TP4 System 2 Java raw outputs.

The script reads:

- `metadata.json`
- `states.csv`

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

## Current State Coloring Gap

The current Java output contract writes `states.csv` with:

```text
step,t,particle_id,x,y,vx,vy
```

It does not export `fresh`, `used`, or `state` columns. For that reason this
first animation version renders a plain position/movement animation with one
particle color.

Future fresh/used coloring should be added only after the analysis layer either:

- reconstructs the per-particle state from `contact_events.csv`, using
  `particle_obstacle_begin` and `particle_wall_begin` events; or
- receives an explicit state column from a deliberate output-contract change.
