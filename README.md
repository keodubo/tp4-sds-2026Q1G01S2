# tp4-sds-2026Q1G01S2

Workspace for Simulacion de Sistemas TP4.

## Current Scope

This repository contains the Java TP4 simulation motor for System 1 and the current System 2 molecular-dynamics engine. System 1 also has independent Python postprocessing for ECM and figures.

Planned split:

- `SdS_TP4_2026Q1G01CS2_Codigo/`: Java simulation motor for both required systems, named to match the final code deliverable.
- `analysis-python/`: postprocessing scripts for plots, figures, GIFs, or MP4 files.
- `docs/`: enunciado, teoricas, format guides, and bibliography.
- `outputs/`: generated simulation outputs, ignored by git.

## TP4 Requirements Summary

The TP4 enunciado asks for both systems:

1. System 1: damped oscillator with analytical solution, used to compare integration schemes.
2. System 2: scanning rate in a circular enclosure with a fixed central obstacle using time-stepped molecular dynamics.

For delivery, keep the simulation output as text files. Analysis and animation should run independently from those text outputs.

## System 1 Status

| Enunciado item | Requirement | Current coverage |
|---|---|---|
| `1.1` | Integrate the damped oscillator with Gear 5, Beeman, original Verlet, and Euler | Java motor under `SdS_TP4_2026Q1G01CS2_Codigo/` writes raw trajectory CSV rows for all four methods. |
| `1.2` | Plot analytical and numerical solutions and compute ECM | `analysis-python/system1/analyze_system1.py` reads the Java CSV, reconstructs the analytical solution, computes ECM, and generates comparison figures. |
| `1.3` | Study ECM decrease as `dt` decreases with log axes and identify the best scheme | The analysis command generates `ecm_vs_dt.png` and `system1_summary.md` from the ECM data. |

The Java motor alone covers only item `1.1`. Complete System 1 evidence requires the postprocessing artifacts from `analysis-python/system1/` for items `1.2` and `1.3`.

## System 2 Status

The current Java System 2 engine includes geometry/state models, contact detection, elastic-force evaluation, velocity Verlet integration, TOML config loading, CSV output, and runner tests.

It writes raw simulation files under the configured output directory:

- `metadata.json`
- `states.csv`
- `contacts.csv`
- `boundary_forces.csv`

System 2 output is sampled so the simulation can keep a small integration `dt` without producing unmanageable files:

- `state_stride`: writes positions/velocities every `state_stride * dt`.
- `full_contact_stride`: writes all contact types every `full_contact_stride * dt` for energy validation.
- obstacle and outer-wall contacts are still written at every integration `dt`, so `Cfc(t)` and fresh/used state transitions can be reconstructed at the maximum temporal resolution required by the statement.
- `boundary_force_stride`: writes aggregate obstacle/wall forces at a sampled cadence.

For heavy runs with `dt = 1e-4`, start with `state_stride = 5000`, `full_contact_stride = 5000`, and `boundary_force_stride = 5000`, then reduce the strides only if energy or radial-profile plots need more temporal detail.

## Java Engine

Requirements:

- Java 21
- Maven 3.9+

Useful commands:

```bash
cd SdS_TP4_2026Q1G01CS2_Codigo
mvn test
mvn exec:java
```

The Java entry point is:

```text
SdS_TP4_2026Q1G01CS2_Codigo/src/main/java/ar/edu/itba/sds/tp4/Tp4Application.java
```

Generate the default System 1 raw trajectory:

```bash
cd SdS_TP4_2026Q1G01CS2_Codigo
mvn exec:java -Dexec.args="system1 --output ../outputs/system1.csv"
```

The default System 1 sweep uses the course oscillator parameters from `docs/Teoricas/Teorica_4.pdf` and `dt=0.01,0.001,0.0001,0.00001,0.000001`. To run a smaller smoke case:

```bash
cd SdS_TP4_2026Q1G01CS2_Codigo
mvn exec:java -Dexec.args="system1 --dt 0.01 --output ../outputs/system1-smoke.csv"
```

Run System 2 from an external TOML config:

```bash
cd SdS_TP4_2026Q1G01CS2_Codigo
mvn exec:java -Dexec.args="system2 configs/system2.example.toml"
```

Run a short System 2 smoke case:

```bash
cd SdS_TP4_2026Q1G01CS2_Codigo
mvn exec:java -Dexec.args="system2-smoke ../outputs/system2-smoke"
```

Prepare the TP4 System 2 sweep configs and manifest without running the heavy simulations:

```bash
python3 scripts/run_system2_sweep.py
```

Run the full required System 2 sweep after the dry-run looks correct:

```bash
python3 scripts/run_system2_sweep.py --execute
```

Default sweep:

- `N = 100, 250, 500, 750, 1000`
- `k = 100, 1000, 10000`
- `5` seeds per `(N, k)` pair
- `tf = 500 s`
- `dt = 1e-4`
- `state_stride = full_contact_stride = boundary_force_stride = 5000`

This creates generated configs, raw outputs, and `manifest.csv` under
`outputs/system2-sweeps/system2-tp4-final/`, which is ignored by git.

## Codex Cloud Output Run

For an overnight cloud run that generates the final raw outputs, publishes them
as GitHub Release assets, and pushes a small handoff commit to the current
branch, use:

```bash
bash scripts/cloud_run_outputs_and_push.sh
```

By default this runs:

- TP4 System 2 final sweep: `75` runs = `5 N` values * `3 k` values * `5` seeds.
- TP3 reference sweep: `25` runs = `5 N` values * `5` seeds, with `snapshot.txt`, `center_contacts.csv`, `used_fraction.csv`, `radial_profile_samples.csv`, `radial_profiles.csv`, and `metadata.json` per run.
- script-level unit tests before the heavy run.
- compressed split release assets under a tag like `tp4-outputs-YYYYMMDDTHHMMSSZ`.
- a final handoff commit and push with summary, release notes, and SHA-256 checksums.

The script keeps `outputs/` ignored for normal local work and force-adds only
small handoff files:

```text
outputs/cloud-run-summary-*.txt
outputs/script-tests-*.log
outputs/release-assets/*/SHA256SUMS.txt
outputs/release-assets/*/release-notes.md
```

Useful environment overrides:

```bash
RUN_TP3=0 bash scripts/cloud_run_outputs_and_push.sh
RUN_TP4=0 bash scripts/cloud_run_outputs_and_push.sh
COMMIT_MESSAGE="data: add output release handoff" bash scripts/cloud_run_outputs_and_push.sh
PUBLISH_MODE=lfs bash scripts/cloud_run_outputs_and_push.sh
```

`PUBLISH_MODE=lfs` is a fallback only. The default `release` mode is preferred
for datasets larger than 1 GB because it avoids growing the Git history and
does not depend on Git LFS quota.

After the cloud run finishes, pull the handoff commit and download the assets:

```bash
git pull --ff-only
gh release download <release-tag> --dir outputs/downloaded-<release-tag>
cd outputs/downloaded-<release-tag>
cat system2-tp4-final.tar.gz.part-* > system2-tp4-final.tar.gz
cat tp3-final-grid.tar.gz.part-* > tp3-final-grid.tar.gz
tar -xzf system2-tp4-final.tar.gz -C ../..
tar -xzf tp3-final-grid.tar.gz -C ../..
```

## Python Analysis

Use Python only for outputs derived from simulation text files:

- plots;
- radial-profile figures;
- timing charts;
- animations or MP4 generation.

The Python side should not become the source of truth for the simulation motor.

Generate the full System 1 ECM, figures, and ranking outputs after refreshing the Java trajectory:

```bash
python3 analysis-python/system1/analyze_system1.py \
  --input outputs/system1.csv \
  --ecm-output outputs/system1_ecm.csv \
  --figures-dir outputs/system1_figures \
  --figure-dt 0.001 \
  --summary-output outputs/system1_summary.md
```

Expected generated System 1 artifacts:

- `outputs/system1.csv`: raw Java trajectory data for item `1.1`.
- `outputs/system1_ecm.csv`: ECM table for item `1.2`.
- `outputs/system1_figures/system1_position_dt_0.001.png`: analytical vs numerical comparison for item `1.2`.
- `outputs/system1_figures/system1_position_dt_0.001_zoom.png`: zoomed analytical vs numerical comparison for item `1.2`.
- `outputs/system1_figures/ecm_vs_dt.png`: log-log ECM vs `dt` study for item `1.3`.
- `outputs/system1_summary.md`: method ranking for item `1.3`.
- `outputs/system1_outputs_manifest.csv`: generated artifact manifest.

## Output Manifest

`outputs/system1_outputs_manifest.csv` is the handoff index for generated TP artifacts. Future System 2 outputs and animations should follow the same convention:

```csv
system,inciso,artifact_type,path,description
```

Use `system` for the TP system number, `inciso` for the enunciado item, `artifact_type` for the artifact kind such as `raw-trajectory`, `analysis-data`, `figure`, `summary`, or `animation`, and `path` for the generated file path.

## Delivery Guardrails

- Final code zip should include only the final simulation motor source code.
- The final code zip should be named `SdS_TP4_2026Q1G01CS2_Codigo.zip`.
- Do not include generated outputs, figures, videos, analysis scripts, or extra documentation in the code zip.
- Keep generated files under `outputs/` or another ignored folder.

## Manual QA Checklist

- [ ] Run Java tests with `cd SdS_TP4_2026Q1G01CS2_Codigo && mvn test`.
- [ ] Generate `outputs/system1.csv` with the default Java command.
- [ ] Confirm `outputs/system1.csv` contains `euler`, `verlet`, `beeman`, and `gear5` rows for every default `dt`.
- [ ] Run the full System 1 analysis command from the repository root.
- [ ] Confirm `outputs/system1_ecm.csv` has one row per `(method, dt)` pair.
- [ ] Open the analytical-vs-numerical figures and check that all four numerical methods and the analytical curve are visible.
- [ ] Open `outputs/system1_figures/ecm_vs_dt.png` and check that it uses logarithmic axes and all four methods are distinguishable.
- [ ] Read `outputs/system1_summary.md` and confirm the reported best method comes from the smallest generated `dt`.
- [ ] Check `outputs/system1_outputs_manifest.csv` includes entries for incisos `1.1`, `1.2`, and `1.3`.
- [ ] Run System 2 from `configs/system2.example.toml` and confirm `metadata.json`, `states.csv`, `contacts.csv`, and `boundary_forces.csv` are generated.
- [ ] Run `system2-smoke` and confirm it completes without changing tracked files.
- [ ] Before creating `SdS_TP4_2026Q1G01CS2_Codigo.zip`, verify it contains only the Java simulation motor source code and excludes `outputs/`, `analysis-python/`, figures, docs, and generated data.
