# tp3-sds-2026Q1G01S2

Python implementation and research workspace for SDS TP3, focused on `Sistema 1: scanning rate en recinto cerrado con obstáculo fijo` using hard spheres.

The repo has two main responsibilities:

- `Sistema 1` simulation code: an event-driven hard-sphere engine, study pipeline for points `1.1` to `1.4`, and delivery packaging.
- Persistent wiki: `docs/raw/` stores immutable source documents and `docs/wiki/` stores the synthesized markdown knowledge base used to drive implementation decisions.

## Project Structure

- `src/tp3_sds/`: Python package with the CLI, wiki helpers, and System 1 code.
- `configs/`: example TOML configs for a single run and for the study pipeline.
- `artifacts/system1/`: generated outputs such as snapshots, study datasets, figures, and delivery zip files.
- `docs/raw/`: original PDFs and raw source material.
- `docs/wiki/`: maintained wiki with enunciado details, observables, protocol, and implementation notes.

## What System 1 Produces

The current System 1 tooling can generate:

- a single-run snapshot file for an external animator or inspection,
- a GIF animation rendered directly from the snapshot file,
- a study for points `1.1` to `1.4` with CSV aggregates and PNG figures,
- a compact delivery zip with only the final System 1 simulation motor source code and minimal run metadata.

The single-run output is a plain text file with:

- run metadata and geometry in the header,
- one snapshot per recorded step,
- one line per particle with `id, x, y, vx, vy, state, r, g, b`.

## Requirements

- Python `3.11+`
- `pip`

Recommended setup:

```bash
python3 -m pip install -e .
```

You can also run everything without installation by prefixing commands with `PYTHONPATH=src`.

## Run Everything In One Go

Use the root script:

```bash
./generate_all.sh
```

This executes, in order:

1. `system1 validate-config`
2. `system1 run`
3. `system1 animate`
4. `system1 validate-study`
5. `system1 study`
6. `system1 export-scientific-assets`
7. `system1 package-delivery`

The script uses these defaults:

- run config: `configs/system1.example.toml`
- study config: `configs/system1.study.submission.toml`
- delivery zip: `artifacts/system1/delivery/SdS_TP3_2026Q1G01CS2_Codigo.zip`

You can override them with environment variables:

```bash
RUN_CONFIG=/abs/path/to/run.toml \
STUDY_CONFIG=/abs/path/to/study.toml \
DELIVERY_ZIP=/abs/path/to/system1-motor.zip \
./generate_all.sh
```

## Run Manually

If you do not want to use `generate_all.sh`, run the commands directly from the repo root.

### Without installing the package

```bash
PYTHONPATH=src python3 -m tp3_sds system1 validate-config --config configs/system1.example.toml
PYTHONPATH=src python3 -m tp3_sds system1 run --config configs/system1.example.toml
PYTHONPATH=src python3 -m tp3_sds system1 animate --input artifacts/system1/example_run.txt --output artifacts/system1/example_run.gif
PYTHONPATH=src python3 -m tp3_sds system1 validate-study --config configs/system1.study.example.toml
PYTHONPATH=src python3 -m tp3_sds system1 study --config configs/system1.study.example.toml
PYTHONPATH=src python3 -m tp3_sds system1 export-scientific-assets --config configs/system1.study.submission.toml --output-root .
PYTHONPATH=src python3 -m tp3_sds system1 package-delivery --output artifacts/system1/delivery/SdS_TP3_2026Q1G01CS2_Codigo.zip
```

### With editable install

```bash
tp3 system1 validate-config --config configs/system1.example.toml
tp3 system1 run --config configs/system1.example.toml
tp3 system1 animate --input artifacts/system1/example_run.txt --output artifacts/system1/example_run.gif
tp3 system1 validate-study --config configs/system1.study.example.toml
tp3 system1 study --config configs/system1.study.example.toml
tp3 system1 export-scientific-assets --config configs/system1.study.submission.toml --output-root .
tp3 system1 package-delivery --output artifacts/system1/delivery/SdS_TP3_2026Q1G01CS2_Codigo.zip
```

## Animation

The animator reads the existing plain-text snapshot format, so there is no second export path to maintain.

```bash
tp3 system1 run --config configs/system1.example.toml
tp3 system1 animate --input artifacts/system1/example_run.txt --output artifacts/system1/example_run.gif
```

Optional flags:

- `--fps 12` controls playback speed independently from simulation time.
- `--show-step-label` overlays the event id, physical time, and used-particle count.

## Useful Outputs

After a normal run, the main files to inspect are:

- single-run snapshots: `artifacts/system1/example_run.txt`
- rendered animation: `artifacts/system1/example_run.gif`
- study summary: `artifacts/system1/studies/example-study/summary.md`
- delivery package: `artifacts/system1/delivery/SdS_TP3_2026Q1G01CS2_Codigo.zip`

The study command writes:

- `artifacts/system1/studies/<study_id>/runs/`
- `artifacts/system1/studies/<study_id>/raw/`
- `artifacts/system1/studies/<study_id>/aggregates/`
- `artifacts/system1/studies/<study_id>/figures/`
- `artifacts/system1/studies/<study_id>/summary.md`

The scientific-export command writes:

- `output_1.1/`
- `output_1.2/`
- `output_1.3/`
- `output_1.4/`
- `output_gifs/`

## Wiki Commands

The repo also includes wiki maintenance helpers:

```bash
PYTHONPATH=src python3 -m tp3_sds wiki search "scanning rate"
PYTHONPATH=src python3 -m tp3_sds wiki refresh-index
PYTHONPATH=src python3 -m tp3_sds wiki lint
```

## Tests

Run the test suite with:

```bash
pytest -q
```

## Notes

- `generate_all.sh` is the safest default for a first full run because it validates configs before executing anything expensive.
- `configs/system1.study.example.toml` is intentionally small; it is for verification, not for final delivery-quality measurements.
- `configs/system1.study.submission.toml` is the delivery-oriented study config for `N = [10, 50, 100, 200, 400, 800]` with `tf = 500 s`.
- The animation uses the snapshot header geometry directly, so the outer boundary, obstacle, and particle scale stay consistent with the simulation output.
