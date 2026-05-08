# CLAUDE.md

## Project Intent

This repository is for Simulacion de Sistemas TP4. The implementation direction is:

- Java for the simulation motor.
- Python or similar tools only for postprocessing, figures, and animations.
- Text files as the contract between simulation and analysis.

## Required Context

Before non-trivial work, read:

- `docs/TP4_Enunciado.pdf`
- `docs/Teorica_4.pdf`
- this `CLAUDE.md`
- `README.md`

The TP4 enunciado requires both systems:

1. damped oscillator integrator comparison;
2. scanning rate with time-stepped molecular dynamics.

## Scope Rules

- Keep scaffold, implementation, analysis, and delivery packaging clearly separated.
- Do not implement TP4 logic unless the user explicitly asks for implementation.
- Do not delete or rewrite TP3 reference material unless the user explicitly asks.
- Do not put analysis or plotting logic inside the Java engine.
- Do not put simulation-engine logic inside `analysis-python/`.

## Java Engine Conventions

- Maven project lives in `engine-java/`.
- Main package starts at `ar.edu.itba.sds.tp4`.
- Keep shared primitives and output contracts under `common`.
- Keep System 1 code under `system1`.
- Keep System 2 code under `system2`.
- Prefer simple Java standard-library code before adding dependencies.

## Output Contract

The Java motor should eventually emit text or CSV files that can be consumed by independent analysis tools.

Generated files should go under ignored output folders, not into the final code zip.

## Verification

For scaffold or Java changes, run:

```bash
cd engine-java
mvn test
```

For executable-entrypoint changes, also run:

```bash
cd engine-java
mvn exec:java
```

## Delivery Notes

The final campus code zip should contain only the final simulation motor source code. It should not include generated outputs, figures, animations, presentation files, or exploratory scripts.
