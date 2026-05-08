# tp4-sds-2026Q1G01S2

Workspace for Simulacion de Sistemas TP4.

## Current Scope

This repository contains the Java TP4 simulation motor scaffold plus the current System 2 molecular-dynamics engine.

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

System 2 can be run from an external TOML config:

```bash
cd SdS_TP4_2026Q1G01CS2_Codigo
mvn exec:java -Dexec.args="system2 configs/system2.example.toml"
```

This writes raw simulation files under the `output_dir` configured in the TOML:
`metadata.json`, `states.csv`, `contacts.csv`, and `boundary_forces.csv`.

System 2 output is sampled so the simulation can keep a small integration `dt`
without producing unmanageable files:

- `state_stride`: writes positions/velocities every `state_stride * dt`.
- `full_contact_stride`: writes all contact types every `full_contact_stride * dt`
  for energy validation.
- obstacle contacts are still written at every integration `dt`, so `Cfc(t)` can
  be reconstructed at the maximum temporal resolution required by the statement.
- `boundary_force_stride`: writes aggregate obstacle/wall forces at a sampled cadence.

For heavy runs with `dt = 1e-4`, start with `state_stride = 5000`,
`full_contact_stride = 5000`, and `boundary_force_stride = 5000`, then reduce
the strides only if energy or radial-profile plots need more temporal detail.

## Python Analysis

Use Python only for outputs derived from simulation text files:

- plots;
- radial-profile figures;
- timing charts;
- animations or MP4 generation.

The Python side should not become the source of truth for the simulation motor.

## Delivery Guardrails

- Final code zip should include only the final simulation motor source code.
- The final code zip should be named `SdS_TP4_2026Q1G01CS2_Codigo.zip`.
- Do not include generated outputs, figures, videos, or extra documentation in the code zip.
- Keep generated files under `outputs/` or another ignored folder.
