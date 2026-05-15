# System 1 Phased Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Provide a sequential implementation roadmap for TP4 System 1, explicitly mapping phases to enunciado items `1.1`, `1.2`, and `1.3`.

**Architecture:** Build the Java engine first, emitting raw trajectory CSV only. Then add independent postprocessing that reads the Java CSV to compute the analytical solution, ECM, figures, and method ranking. This preserves the enunciado requirement that simulation output is text and analysis runs independently from that output.

**Tech Stack:** Java 21, Maven, JUnit 5 for Java tests, Python later for postprocessing and figures.

---

## Enunciado Coverage Map

| Enunciado item | Requirement | Phases needed | Deliverable status after those phases |
|---|---|---:|---|
| `1.1` | Integrate the oscillator with Gear 5, Beeman, original Verlet, and Euler | Phases 0-3 | Java engine can generate raw trajectories for all required methods |
| `1.2` | Plot analytical and numerical solutions; compute ECM for each method | Phases 0-5 | Raw trajectories plus independent analysis data/figures for analytical vs numerical comparison |
| `1.3` | Study ECM decrease as `dt` decreases using log axes; identify best scheme | Phases 0-6 | Multi-`dt` ECM dataset, log-log figure, and method ranking |

If there is limited time:

- **Only enough time for `1.1`:** implement Phases 0-3.
- **Enough time for `1.1` + `1.2`:** implement Phases 0-5.
- **Full System 1:** implement Phases 0-6, then Phase 7 for cleanup.

---

## Phase 0: Repository Baseline And Guardrails

**Covers:** prerequisite for `1.1`, `1.2`, `1.3`.

**Purpose:** Confirm the repo builds and lock the scope before adding implementation.

**Files:**

- Read: `CLAUDE.md`
- Read: `README.md`
- Read: `docs/TP4_Enunciado.pdf`
- Read: `docs/Teoricas/Teorica_4.pdf`
- Read: `docs/superpowers/specs/system1-engine-design.md`
- Modify: none

**Checklist:**

- [ ] Confirm `SdS_TP4_2026Q1G01CS2_Codigo/` builds with `mvn test`.
- [ ] Confirm current Java entry point is still only scaffold.
- [ ] Confirm System 1 scope remains Java motor first, analysis later.
- [ ] Confirm no generated outputs or analysis code are added to the final Java code ZIP.

**Verification command:**

```bash
cd SdS_TP4_2026Q1G01CS2_Codigo
mvn test
```

Expected result:

```text
BUILD SUCCESS
```

---

## Phase 1: Java Engine Foundation

**Covers:** prerequisite for `1.1`; enables later `1.2` and `1.3`.

**Purpose:** Create the shared System 1 model, parameter validation, CLI parsing, and CSV output contract without implementing all integrators yet.

**Files:**

- Modify: `SdS_TP4_2026Q1G01CS2_Codigo/pom.xml`
- Modify: `SdS_TP4_2026Q1G01CS2_Codigo/src/main/java/ar/edu/itba/sds/tp4/Tp4Application.java`
- Create: `SdS_TP4_2026Q1G01CS2_Codigo/src/main/java/ar/edu/itba/sds/tp4/system1/System1Command.java`
- Create: `SdS_TP4_2026Q1G01CS2_Codigo/src/main/java/ar/edu/itba/sds/tp4/system1/System1Parameters.java`
- Create: `SdS_TP4_2026Q1G01CS2_Codigo/src/main/java/ar/edu/itba/sds/tp4/system1/Oscillator.java`
- Create: `SdS_TP4_2026Q1G01CS2_Codigo/src/main/java/ar/edu/itba/sds/tp4/system1/OscillatorState.java`
- Create: `SdS_TP4_2026Q1G01CS2_Codigo/src/main/java/ar/edu/itba/sds/tp4/system1/TrajectoryCsvWriter.java`
- Create: `SdS_TP4_2026Q1G01CS2_Codigo/src/test/java/ar/edu/itba/sds/tp4/system1/System1ParametersTest.java`
- Create: `SdS_TP4_2026Q1G01CS2_Codigo/src/test/java/ar/edu/itba/sds/tp4/system1/OscillatorTest.java`
- Create: `SdS_TP4_2026Q1G01CS2_Codigo/src/test/java/ar/edu/itba/sds/tp4/system1/TrajectoryCsvWriterTest.java`

**Checklist:**

- [ ] Add JUnit 5 as a test dependency only.
- [ ] Implement default parameters from slide 36: `m=70`, `k=10000`, `gamma=100`, `tf=5`, `x0=1`, `v0=-gamma/(2m)`.
- [ ] Implement default `dt` sweep: `0.01,0.001,0.0001,0.00001,0.000001`. Treat these as the group's reproducible experimental sweep for item `1.3`, including the professor-requested `10^-6` value.
- [ ] Validate `m > 0`, `k > 0`, `gamma >= 0`, `tf > 0`, each `dt > 0`, no duplicate `dt`, and integer `tf/dt`.
- [ ] Implement oscillator acceleration `a(x,v)=(-k*x-gamma*v)/m`.
- [ ] Implement CSV metadata and columns: `method,dt,time,x,v`.
- [ ] Route `Tp4Application` command `system1` to `System1Command`.

**Exit criteria:**

- CLI can parse System 1 flags.
- Invalid parameters fail before running.
- CSV writer can write metadata and rows.
- No required integrator behavior is claimed complete yet.

**Verification command:**

```bash
cd SdS_TP4_2026Q1G01CS2_Codigo
mvn test
```

Expected result:

```text
BUILD SUCCESS
```

---

## Phase 2: First Integrator Slice With Euler

**Covers:** partial `1.1`.

**Purpose:** Implement the simplest integrator end-to-end so the engine can produce a real trajectory before adding the more complex schemes.

**Files:**

- Create: `SdS_TP4_2026Q1G01CS2_Codigo/src/main/java/ar/edu/itba/sds/tp4/system1/Integrator.java`
- Create: `SdS_TP4_2026Q1G01CS2_Codigo/src/main/java/ar/edu/itba/sds/tp4/system1/EulerIntegrator.java`
- Modify: `SdS_TP4_2026Q1G01CS2_Codigo/src/main/java/ar/edu/itba/sds/tp4/system1/System1Command.java`
- Create: `SdS_TP4_2026Q1G01CS2_Codigo/src/test/java/ar/edu/itba/sds/tp4/system1/IntegratorContractTest.java`

**Checklist:**

- [ ] Define `Integrator` contract returning states from `t=0` through `t=tf`, inclusive.
- [ ] Implement Euler with course formula:

```text
x(t+dt) = x(t) + v(t)*dt + 0.5*a(t)*dt^2
v(t+dt) = v(t) + a(t)*dt
```

- [ ] Emit method name `euler`.
- [ ] Write all default `dt` trajectories into one long-format CSV.
- [ ] Test row count for `tf=5` and each default `dt`.

**Exit criteria:**

- Running `system1` produces a CSV with Euler rows for every configured `dt`.
- This phase alone is not enough for `1.1`, because `1.1` requires all four methods.

**Verification command:**

```bash
cd SdS_TP4_2026Q1G01CS2_Codigo
mvn test
mvn exec:java -Dexec.args="system1 --dt 0.01 --output ../outputs/system1-euler-smoke.csv"
```

Expected result:

```text
BUILD SUCCESS
```

and `../outputs/system1-euler-smoke.csv` contains rows with `method=euler`.

---

## Phase 3: Complete Required Integrators

**Covers:** completes `1.1`.

**Purpose:** Add the remaining mandatory methods from the enunciado: original Verlet, Beeman, and Gear predictor-corrector order 5.

**Files:**

- Create: `SdS_TP4_2026Q1G01CS2_Codigo/src/main/java/ar/edu/itba/sds/tp4/system1/VerletIntegrator.java`
- Create: `SdS_TP4_2026Q1G01CS2_Codigo/src/main/java/ar/edu/itba/sds/tp4/system1/BeemanIntegrator.java`
- Create: `SdS_TP4_2026Q1G01CS2_Codigo/src/main/java/ar/edu/itba/sds/tp4/system1/Gear5Integrator.java`
- Modify: `SdS_TP4_2026Q1G01CS2_Codigo/src/main/java/ar/edu/itba/sds/tp4/system1/System1Command.java`
- Modify: `SdS_TP4_2026Q1G01CS2_Codigo/src/test/java/ar/edu/itba/sds/tp4/system1/IntegratorContractTest.java`

**Checklist:**

- [ ] Implement original Verlet with previous state estimated by Euler evaluated at `-dt`.
- [ ] Use the explicit original Verlet recurrence from the theory:

```text
x(t+dt) = 2*x(t) - x(t-dt) + a(t)*dt^2
```

- [ ] Evaluate the damped acceleration using the configured initial velocity at `t=0` and the explicit backward velocity estimate for later steps:

```text
v(t) ~= (x(t) - x(t-dt)) / dt
a(t) = (-k*x(t) - gamma*v(t)) / m
```

- [ ] Export Verlet velocity using that same explicit estimate.
- [ ] Implement Beeman predictor-corrector for velocity-dependent forces.
- [ ] Initialize Beeman `a(t-dt)` from the Euler-estimated previous state.
- [ ] Implement Gear 5 predictor-corrector from the theory.
- [ ] Use Gear order-5 coefficients for `r2 = f(r,r1)`:

```text
alpha0 = 3/16
alpha1 = 251/360
alpha2 = 1
alpha3 = 11/18
alpha4 = 1/6
alpha5 = 1/60
```

- [ ] Initialize Gear derivatives using recurrence:

```text
r[n+2] = -(gamma/m)*r[n+1] - (k/m)*r[n]
```

- [ ] Emit fixed method names: `verlet`, `beeman`, `gear5`.
- [ ] Test that the CSV contains all four methods for each `dt`.
- [ ] Test the Verlet one-step update against the explicit original-Verlet recurrence.

**Exit criteria for `1.1`:**

- The Java engine integrates with all four required schemes.
- The engine produces raw text/CSV output for every required scheme.
- No ECM or plots are required for this phase.

**Verification command:**

```bash
cd SdS_TP4_2026Q1G01CS2_Codigo
mvn test
mvn exec:java -Dexec.args="system1 --output ../outputs/system1.csv"
```

Expected result:

```text
BUILD SUCCESS
```

and `../outputs/system1.csv` contains `euler`, `verlet`, `beeman`, and `gear5` rows.

---

## Phase 4: Analysis Foundation For Analytical Solution And ECM

**Covers:** prerequisite for `1.2`; does not change Java motor.

**Purpose:** Add independent postprocessing that reads the Java CSV, reconstructs the analytical solution, and computes ECM outside the simulation engine.

**Files:**

- Create: `analysis-python/system1/README.md`
- Create: `analysis-python/system1/analyze_system1.py`
- Create: `analysis-python/system1/test_analyze_system1.py` or equivalent lightweight verification
- Create during execution: `outputs/system1_outputs_manifest.csv`

**Checklist:**

- [ ] Read Java CSV while ignoring metadata lines beginning with `#`.
- [ ] Reconstruct the analytical solution from metadata using the general underdamped form, which reduces to the slide-36 expression for the default initial conditions:

```text
beta = gamma / (2*m)
omega = sqrt(k/m - beta^2)
x(t) = exp(-beta*t) * (x0*cos(omega*t) + ((v0 + beta*x0)/omega)*sin(omega*t))
```

- [ ] Compute analytical velocity consistently from the derivative of `x(t)`.
- [ ] Compute squared error per row for position.
- [ ] Compute ECM per `(method, dt)`:

```text
ECM = sum((x_numeric - x_analytical)^2) / number_of_steps
```

- [ ] Write an analysis CSV such as `outputs/system1_ecm.csv`.
- [ ] Write or update `outputs/system1_outputs_manifest.csv` with one row per generated output and these columns:

```text
system,inciso,artifact_type,path,description
```

- [ ] Record `outputs/system1.csv` as `system=1`, `inciso=1.1`, `artifact_type=raw-trajectory`.
- [ ] Record `outputs/system1_ecm.csv` as `system=1`, `inciso=1.2`, `artifact_type=analysis-data`.
- [ ] Add a lightweight analysis test or fixture proving that the default initial conditions reduce the general solution to the slide-36 expression.
- [ ] Add a lightweight analysis test or fixture proving that ECM is grouped by `(method, dt)` and normalized by the number of trajectory rows in that group.

**Exit criteria:**

- Given `outputs/system1.csv`, analysis can produce ECM values without rerunning Java.
- The output manifest maps generated files to TP4 incisos.
- This phase still does not satisfy the plotting part of `1.2`.

**Verification command:**

```bash
python3 analysis-python/system1/analyze_system1.py --input outputs/system1.csv --ecm-output outputs/system1_ecm.csv
```

Expected result:

```text
outputs/system1_ecm.csv
outputs/system1_outputs_manifest.csv
```

contains one row per `(method, dt)`.

---

## Phase 5: Figures For Analytical Vs Numerical Comparison

**Covers:** completes `1.2`.

**Purpose:** Generate the required comparison plots: analytical solution and numerical solutions for each method.

**Files:**

- Modify: `analysis-python/system1/analyze_system1.py`
- Create: `outputs/system1_figures/` during execution only

**Checklist:**

- [ ] Generate position comparison figures from Java CSV plus reconstructed analytical solution.
- [ ] Generate readable analytical-vs-numerical plots for `dt=0.001`, while keeping the command configurable for other `dt` values if the presentation needs them.
- [ ] Generate an additional zoomed analytical-vs-numerical plot for `dt=0.001` so the overlap differences are visible.
- [ ] Use distinct marker shapes for the numerical methods in position comparison figures so overlapping curves remain distinguishable.
- [ ] Include all four methods in the comparison, either as separate plots or a clear combined plot.
- [ ] Add every generated analytical-vs-numerical figure to `outputs/system1_outputs_manifest.csv` as `system=1`, `inciso=1.2`, `artifact_type=figure`.
- [ ] Keep generated figures out of the Java code ZIP.
- [ ] Document exact command in `analysis-python/system1/README.md`.

**Exit criteria for `1.2`:**

- There is a figure comparing analytical and numerical solutions.
- ECM is computed from output files, not during simulation.
- The manifest identifies every figure generated for `1.2`.

**Verification command:**

```bash
python3 analysis-python/system1/analyze_system1.py --input outputs/system1.csv --ecm-output outputs/system1_ecm.csv --figures-dir outputs/system1_figures --figure-dt 0.001
```

Expected result:

```text
outputs/system1_ecm.csv
outputs/system1_figures/
outputs/system1_outputs_manifest.csv
```

---

## Phase 6: ECM vs dt Study And Method Ranking

**Covers:** completes `1.3`.

**Purpose:** Use the multi-`dt` Java output to study how ECM decreases with `dt`, using log-log axes, and decide which scheme performs best.

**Files:**

- Modify: `analysis-python/system1/analyze_system1.py`
- Modify: `analysis-python/system1/README.md`
- Create: `outputs/system1_figures/ecm_vs_dt.png` during execution only

**Checklist:**

- [ ] Use ECM rows for all default `dt`: `0.01`, `0.001`, `0.0001`, `0.00001`, `0.000001`.
- [ ] If the log-log trend is not clear enough, rerun Java with additional positive `dt` values that divide `tf` exactly and include them in the ECM CSV.
- [ ] Plot `ECM` vs `dt` on logarithmic axes.
- [ ] Include all four methods in the same figure for comparison.
- [ ] Generate a compact ranking summary, for example best method by lowest ECM at smallest `dt`.
- [ ] Keep the ranking data in a text or CSV output, not hardcoded into the presentation.
- [ ] Add the ECM-vs-`dt` figure to `outputs/system1_outputs_manifest.csv` as `system=1`, `inciso=1.3`, `artifact_type=figure`.
- [ ] Add the ranking summary to `outputs/system1_outputs_manifest.csv` as `system=1`, `inciso=1.3`, `artifact_type=summary`.

**Exit criteria for `1.3`:**

- There is a log-log ECM vs `dt` figure.
- There is a reproducible method comparison from generated data.
- The team can answer which integration scheme is best for this system.
- The manifest identifies every generated artifact for `1.3`.

**Verification command:**

```bash
python3 analysis-python/system1/analyze_system1.py --input outputs/system1.csv --ecm-output outputs/system1_ecm.csv --figures-dir outputs/system1_figures --figure-dt 0.001 --summary-output outputs/system1_summary.md
```

Expected result:

```text
outputs/system1_figures/ecm_vs_dt.png
outputs/system1_summary.md
outputs/system1_outputs_manifest.csv
```

---

## Phase 7: Documentation And Handoff Cleanup

**Covers:** final polish for `1.1`, `1.2`, `1.3`.

**Purpose:** Make the implementation reproducible for teammates and future delivery packaging.

**Files:**

- Modify: `README.md`
- Modify: `SdS_TP4_2026Q1G01CS2_Codigo/README.md` if created during implementation
- Modify: `analysis-python/system1/README.md`

**Checklist:**

- [ ] Document Java command for generating `outputs/system1.csv`.
- [ ] Document analysis command for generating ECM and figures.
- [ ] Document the `outputs/system1_outputs_manifest.csv` convention so future System 2 outputs and animations also declare their TP4 inciso.
- [ ] Document which phases cover each enunciado item.
- [ ] Document that the Java motor alone covers only `1.1`; complete System 1 requires the analysis artifacts from phases 4-6.
- [ ] Reiterate that generated outputs, figures, and analysis scripts are not part of the final Java code ZIP.
- [ ] Add a manual QA checklist for System 1.

**Final verification commands:**

```bash
cd SdS_TP4_2026Q1G01CS2_Codigo
mvn test
mvn exec:java -Dexec.args="system1 --output ../outputs/system1.csv"
cd ..
python3 analysis-python/system1/analyze_system1.py --input outputs/system1.csv --ecm-output outputs/system1_ecm.csv --figures-dir outputs/system1_figures --figure-dt 0.001 --summary-output outputs/system1_summary.md
```

Expected result:

```text
BUILD SUCCESS
outputs/system1.csv
outputs/system1_ecm.csv
outputs/system1_figures/
outputs/system1_summary.md
```

---

## Recommended Commit Boundaries

Use these boundaries only when implementation begins:

1. `test: add system1 parameter and oscillator tests`
2. `feat: add system1 CLI and CSV contract`
3. `feat: implement euler system1 integrator`
4. `feat: implement required system1 integrators`
5. `feat: add system1 ECM postprocessing`
6. `feat: add system1 figures and dt study`
7. `docs: document system1 workflow`

---

## Stop Points For Limited Time

### Stop after Phase 3

This is the minimum useful Java-engine milestone.

Covered:

- `1.1` motor requirement

Not covered:

- analytical comparison figures
- ECM
- ECM vs `dt`
- method ranking

### Stop after Phase 5

This is enough for analytical comparison and ECM.

Covered:

- `1.1`
- `1.2`

Not covered:

- full `1.3` log-log ECM-vs-`dt` analysis and final method ranking

### Stop after Phase 6

This completes the scientific work for System 1.

Covered:

- `1.1`
- `1.2`
- `1.3`

Remaining:

- documentation polish
- final delivery packaging later
