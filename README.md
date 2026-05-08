# tp4-sds-2026Q1G01S2

Workspace for Simulacion de Sistemas TP4.

## Current Scope

This repository is currently scaffolded only. The TP4 simulation logic has not been implemented yet.

Planned split:

- `engine-java/`: Java simulation motor for both required systems.
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
cd engine-java
mvn test
mvn exec:java
```

The current Java entry point is only a scaffold:

```text
engine-java/src/main/java/ar/edu/itba/sds/tp4/Tp4Application.java
```

## Python Analysis

Use Python only for outputs derived from simulation text files:

- plots;
- radial-profile figures;
- timing charts;
- animations or MP4 generation.

The Python side should not become the source of truth for the simulation motor.

## Delivery Guardrails

- Final code zip should include only the final simulation motor source code.
- Do not include generated outputs, figures, videos, or extra documentation in the code zip.
- Keep generated files under `outputs/` or another ignored folder.
