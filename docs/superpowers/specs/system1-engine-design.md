# System 1 Java Engine Design

**Goal:** Implement only the Java simulation motor for TP4 System 1: the damped punctual oscillator used to compare numerical integration schemes.

**Status:** Design v1. No implementation in this document.

**Primary sources:** `docs/TP4_Enunciado.pdf` and `docs/Teoricas/Teorica_4.pdf`.

---

## Scope

This phase covers only the Java engine for System 1.

Included:

- Euler
- Original Verlet
- Beeman
- Gear predictor-corrector order 5
- CLI flags with defaults from the course material
- raw numerical trajectory output in one CSV file
- JUnit tests for the Java engine
- minimal README update for commands and output contract

Excluded for this phase:

- analytical solution output
- ECM calculation
- plots
- animations
- Python postprocessing
- delivery ZIP packaging
- System 2

The Java motor must generate raw data only. Analysis such as ECM and figures will be computed later from the output files.

---

## Course Parameters

Default values come from slide 36 of `Teorica_4.pdf`:

```text
m = 70 kg
k = 10000 N/m
gamma = 100 kg/s
tf = 5 s
A = 1 m
x(0) = 1 m
v(0) = -A * gamma / (2m) = -0.7142857142857143 m/s
```

Default integration steps:

```text
dt = 0.1, 0.01, 0.001, 0.0001
```

The equation of motion is:

```text
m*x'' = -k*x - gamma*x'
a(x, v) = (-k*x - gamma*v) / m
```

The engine must allow overriding physical parameters through CLI flags, but defaults remain aligned with the course values.

---

## CLI Contract

Recommended command:

```bash
cd SdS_TP4_2026Q1G01CS2_Codigo
mvn exec:java -Dexec.args="system1 --output ../outputs/system1.csv"
```

Fully explicit equivalent:

```bash
cd SdS_TP4_2026Q1G01CS2_Codigo
mvn exec:java -Dexec.args="system1 --m 70 --k 10000 --gamma 100 --tf 5 --x0 1 --v0 -0.7142857142857143 --dt 0.1,0.01,0.001,0.0001 --output ../outputs/system1.csv"
```

Validation happens automatically before running. There is no separate `validate` subcommand in this phase.

Validation rules:

- `m > 0`
- `k > 0`
- `gamma >= 0`
- `tf > 0`
- each `dt > 0`
- no duplicate `dt` values
- each `tf / dt` must be an integer within floating-point tolerance
- output path must be present and writable
- warn or fail before producing impractically large outputs

---

## Output Contract

The engine writes one long-format CSV file with commented metadata followed by raw trajectory rows.

Example:

```csv
# system=system1
# m=70.0
# k=10000.0
# gamma=100.0
# tf=5.0
# x0=1.0
# v0=-0.7142857142857143
# dts=0.1,0.01,0.001,0.0001
method,dt,time,x,v
euler,0.1,0.0,1.0,-0.7142857142857143
verlet,0.1,0.0,1.0,-0.7142857142857143
beeman,0.1,0.0,1.0,-0.7142857142857143
gear5,0.1,0.0,1.0,-0.7142857142857143
```

Method names are fixed:

```text
euler
verlet
beeman
gear5
```

For every method and every `dt`, the CSV includes rows from `t = 0` through `t = tf`, inclusive.

The output intentionally does not include:

- analytical `x(t)`
- analytical `v(t)`
- ECM
- plotting-specific columns

Those are postprocessing responsibilities.

---

## Integrator Details

### Euler

Use the Euler formula shown in the course material:

```text
x(t+dt) = x(t) + v(t)*dt + 0.5*a(t)*dt^2
v(t+dt) = v(t) + a(t)*dt
```

where:

```text
a(t) = a(x(t), v(t))
```

### Original Verlet

Use original Verlet position update:

```text
x(t+dt) = 2*x(t) - x(t-dt) + a(t)*dt^2
```

The first previous state is estimated with Euler evaluated at `-dt`, following slide 14 of the theory:

```text
x(-dt) = x(0) - v(0)*dt + 0.5*a(0)*dt^2
v(-dt) = v(0) - a(0)*dt
```

The exported velocity uses the centered formula from the theory:

```text
v(t) = (x(t+dt) - x(t-dt)) / (2*dt)
```

To export `v(tf)` consistently, the integrator computes one extra internal position `x(tf+dt)` but does not write a `tf+dt` row.

### Beeman

Use the predictor-corrector variant for forces that depend on velocity, as shown in slide 20 of the theory:

```text
x(t+dt) = x(t) + v(t)*dt + (2/3)*a(t)*dt^2 - (1/6)*a(t-dt)*dt^2

v_pred(t+dt) = v(t) + (3/2)*a(t)*dt - (1/2)*a(t-dt)*dt

a(t+dt) = a(x(t+dt), v_pred(t+dt))

v_corr(t+dt) = v(t) + (1/3)*a(t+dt)*dt + (5/6)*a(t)*dt - (1/6)*a(t-dt)*dt
```

Initialize `a(t-dt)` by estimating `x(-dt)` and `v(-dt)` with Euler evaluated at `-dt`, then computing:

```text
a(-dt) = a(x(-dt), v(-dt))
```

### Gear Predictor-Corrector Order 5

Use the Gear predictor-corrector algorithm from slides 24-29 of the theory.

State derivatives:

```text
r0 = x
r1 = v
r2 = a
r3 = da/dt
r4 = d2a/dt2
r5 = d3a/dt3
```

Prediction:

```text
rp[q](t+dt) = sum from j=q to 5 of r[j](t) * dt^(j-q) / (j-q)!
```

Evaluation:

```text
a_eval = a(rp[0], rp[1])
deltaA = a_eval - rp[2]
deltaR2 = deltaA * dt^2 / 2
```

Correction:

```text
rc[q] = rp[q] + alpha[q] * deltaR2 * q! / dt^q
```

Because the oscillator force depends on position and velocity, use the `r2 = f(r, r1)` order-5 coefficients from slide 29:

```text
alpha0 = 3/16
alpha1 = 251/360
alpha2 = 1
alpha3 = 11/18
alpha4 = 1/6
alpha5 = 1/60
```

Initial derivatives are computed from the differential equation, not from the analytical solution.

Let:

```text
c = gamma / m
w2 = k / m
```

The recurrence is:

```text
r[n+2] = -c*r[n+1] - w2*r[n]
```

Starting with `r0 = x0` and `r1 = v0`, compute `r2` through `r5`.

---

## Java Structure

The Maven project remains under:

```text
SdS_TP4_2026Q1G01CS2_Codigo/
```

Proposed production files:

```text
src/main/java/ar/edu/itba/sds/tp4/Tp4Application.java
src/main/java/ar/edu/itba/sds/tp4/system1/System1Command.java
src/main/java/ar/edu/itba/sds/tp4/system1/System1Parameters.java
src/main/java/ar/edu/itba/sds/tp4/system1/Oscillator.java
src/main/java/ar/edu/itba/sds/tp4/system1/OscillatorState.java
src/main/java/ar/edu/itba/sds/tp4/system1/Integrator.java
src/main/java/ar/edu/itba/sds/tp4/system1/EulerIntegrator.java
src/main/java/ar/edu/itba/sds/tp4/system1/VerletIntegrator.java
src/main/java/ar/edu/itba/sds/tp4/system1/BeemanIntegrator.java
src/main/java/ar/edu/itba/sds/tp4/system1/Gear5Integrator.java
src/main/java/ar/edu/itba/sds/tp4/system1/TrajectoryCsvWriter.java
```

Proposed test files:

```text
src/test/java/ar/edu/itba/sds/tp4/system1/System1ParametersTest.java
src/test/java/ar/edu/itba/sds/tp4/system1/OscillatorTest.java
src/test/java/ar/edu/itba/sds/tp4/system1/IntegratorContractTest.java
src/test/java/ar/edu/itba/sds/tp4/system1/TrajectoryCsvWriterTest.java
```

JUnit 5 is allowed as a test dependency. Avoid production dependencies unless a later phase proves they are necessary.

---

## Testing Strategy

Tests should cover:

- default parameters match the course values
- acceleration formula uses both position and velocity
- invalid CLI/parameter combinations are rejected
- `tf / dt` integer validation
- all methods emit rows for `t=0` and `t=tf`
- CSV metadata and column names are stable
- method names are exactly `euler`, `verlet`, `beeman`, `gear5`
- Verlet uses centered velocity and computes the extra internal point for `tf`
- Gear initial derivatives follow the recurrence from the oscillator equation

Recommended verification commands:

```bash
cd SdS_TP4_2026Q1G01CS2_Codigo
mvn test
mvn exec:java -Dexec.args="system1 --output ../outputs/system1.csv"
```

---

## Design Constraints

- Keep the Java engine compact because the final code ZIP must stay below 100 KB.
- Do not include generated outputs, plots, analysis code, or documentation in the final campus code ZIP.
- Keep Python analysis out of the Java engine.
- Keep System 1 code under `ar.edu.itba.sds.tp4.system1`.
- Prefer standard-library Java for production code.

---

## Open Items

No implementation-blocking questions remain for System 1 Java engine v1.

The next step, after review and approval of this design, is a detailed implementation plan.
