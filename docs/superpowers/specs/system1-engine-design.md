# System 1 Specification And Java Engine Design

**Goal:** Specify the complete TP4 System 1 workflow for the damped punctual oscillator: Java simulation motor, text output contract, independent analysis, ECM study, and presentation-ready figures.

**Status:** Design v2. No implementation in this document.

**Primary sources:** `docs/TP4_Enunciado.pdf` and `docs/Teoricas/Teorica_4.pdf`.

---

## Enunciado Coverage

| Enunciado item | Requirement | Spec coverage |
|---|---|---|
| `1.1` | Integrate the oscillator with at least Gear predictor-corrector order 5, Beeman, original Verlet, and Euler | Java engine integrators and CSV trajectory output |
| `1.2` | Plot analytical and numerical solutions; compute ECM as squared position differences normalized by number of steps | Independent postprocessing from Java CSV |
| `1.3` | Study how ECM decreases as `dt` decreases with logarithmic axes and identify the best scheme | Independent ECM-vs-`dt` analysis and ranking |

System 1 delivery is complete only when all three items are covered. The Java motor alone covers `1.1`; it intentionally does not complete `1.2` or `1.3`.

---

## Scope

This spec covers complete System 1 behavior while keeping the implementation split required by the TP4 statement and repository guardrails.

Included:

- Euler
- Original Verlet
- Beeman
- Gear predictor-corrector order 5
- CLI flags with physical defaults from the course material
- raw numerical trajectory output in one CSV file
- JUnit tests for the Java engine
- independent analysis that reads the Java CSV
- analytical solution reconstruction outside the Java engine
- ECM calculation outside the Java engine
- analytical-vs-numerical figures
- log-log ECM-vs-`dt` figure and method ranking
- minimal README update for commands and output contract

Excluded from the Java motor:

- analytical solution output
- ECM calculation
- plots
- animations
- Python postprocessing
- delivery ZIP packaging
- System 2

The Java motor must generate raw data only. Analysis such as analytical solution reconstruction, ECM, figures, and ranking will be computed later from the output files.

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

Default integration steps are a project experimental sweep chosen to satisfy the enunciado requirement to study decreasing `dt`; the course statement does not mandate these exact values:

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

## Analysis Contract

Independent postprocessing reads the Java CSV while ignoring metadata lines that begin with `#`.

For each trajectory row, the analysis reconstructs the analytical position from the physical metadata. For the default underdamped case:

```text
beta = gamma / (2*m)
omega = sqrt(k/m - beta^2)
x_analytical(t) = exp(-beta*t) * (x0*cos(omega*t) + ((v0 + beta*x0)/omega)*sin(omega*t))
```

With the slide-36 default initial conditions, this reduces to:

```text
x_analytical(t) = A * exp(-(gamma/(2*m))*t) * cos(sqrt(k/m - gamma^2/(4*m^2))*t)
```

The ECM is computed per `(method, dt)` using position error only:

```text
ECM(method, dt) = sum((x_numeric - x_analytical)^2) / number_of_steps
```

The analysis must generate:

- at least one analytical-vs-numerical position comparison figure that includes all four methods clearly
- an ECM table with one row per `(method, dt)`
- one log-log `ECM` vs `dt` figure containing all four methods
- a reproducible text or CSV summary that identifies the best scheme from the generated ECM data

Generated analysis outputs must stay outside the final Java code ZIP.

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

For this oscillator, the force depends on velocity:

```text
a(x, v) = (-k*x - gamma*v) / m
```

Using the plain force-independent Verlet update directly would make `a(t)` depend on the centered velocity, which depends on `x(t+dt)`. Therefore the integrator must use original Verlet with the damping term handled explicitly through the centered velocity:

```text
a(t) = (x(t+dt) - 2*x(t) + x(t-dt)) / dt^2
v(t) = (x(t+dt) - x(t-dt)) / (2*dt)
```

Substituting these into:

```text
m*a(t) = -k*x(t) - gamma*v(t)
```

gives the explicit update:

```text
(m + gamma*dt/2)*x(t+dt) =
    (2*m - k*dt^2)*x(t) + (gamma*dt/2 - m)*x(t-dt)
```

or:

```text
x(t+dt) =
    ((2*m - k*dt^2)*x(t) + (gamma*dt/2 - m)*x(t-dt))
    / (m + gamma*dt/2)
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
- Verlet uses the damped centered-velocity recurrence and computes the extra internal point for `tf`
- Gear initial derivatives follow the recurrence from the oscillator equation
- analysis formula for the analytical solution matches the slide-36 default case
- ECM is computed per `(method, dt)` from generated trajectory rows
- ECM-vs-`dt` analysis includes all configured `dt` values and all four methods

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

No implementation-blocking questions remain for System 1 v2.

The next step is to keep the implementation plan aligned with this spec before writing code.
