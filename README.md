# tp4-sds-2026Q1G01S2

Workspace for Simulacion de Sistemas TP4.

## Current Scope

System 1 is implemented through the Java simulation motor and independent Python postprocessing. System 2 remains planned work.

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

## Java Engine

Requirements:

- Java 21
- Maven 3.9+

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
- [ ] Before creating `SdS_TP4_2026Q1G01CS2_Codigo.zip`, verify it contains only the Java simulation motor source code and excludes `outputs/`, `analysis-python/`, figures, docs, and generated data.
