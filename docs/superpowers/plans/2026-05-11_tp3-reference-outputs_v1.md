# TP3 Reference Outputs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Verify the local TP3 System 1 motor against `docs/TP3_Enunciado.pdf`, then generate TP3 reference outputs inside this TP4 repo with the same `N`, seed count, `tf`, and output cadence intended for the TP4 System 2 sweep.

**Architecture:** Keep TP3 as an event-driven Python reference motor and do not convert it to fixed-`dt` dynamics. Add a repo-local sweep/output layer that drives the TP3 motor, writes generated artifacts under ignored `outputs/`, and normalizes the output cadence to the TP4 observation cadence (`dt * stride = 0.5 s` for the current candidate). Keep TP4 Java and TP3 Python separated; comparison scripts should consume text/CSV outputs from both.

**Tech Stack:** Python 3.11+, standard library CSV/JSON/TOML parsing, existing TP3 package under `SdS_TP3_2026Q1G01CS2_Codigo/`, existing TP4 sweep conventions under `scripts/run_system2_sweep.py`.

---

## Current Baseline

- Local TP3 code exists in `SdS_TP3_2026Q1G01CS2_Codigo/`.
- `PYTHONPATH=src python3 -m tp3_sds system1 validate-config --config configs/system1.example.toml` currently passes.
- The local TP3 copy is the compact motor package: `cli.py` exposes `system1 validate-config` and `system1 run`.
- The local TP3 README still mentions study/export commands from the older full TP3 workspace, but those commands are not present in this compact copy.
- The sibling historical TP3 repo at `/Users/keoni/Claude-Workspace/projects/tp3-sds-2026Q1G01S2` contains the fuller study pipeline, but that checkout is dirty. Treat it as reference material only until explicitly synced.
- The current TP4 System 2 sweep script already uses:
  - `N = [100, 250, 500, 750, 1000]`
  - `seed_count = 5`
  - `seed_start = 12345`
  - `tf = 500 s`
  - `dt = 1e-4`
  - `state_stride = full_contact_stride = boundary_force_stride = 5000`

## Key Assumption

For TP3, `dt` is not a physical integration step. The TP3 enunciado requires event-driven dynamics with variable event times. We should store the candidate `dt = 1e-4` as a comparison parameter and use `dt * stride = 0.5 s` as the sampled output cadence. The TP3 event engine itself should still process exact collision events.

## Recommended Default

| Option | Recommendation | Why | Downside |
|---|---|---|---|
| Add a root `scripts/run_tp3_reference_sweep.py` and minimal TP3 sampling hooks | Recommended | Keeps the TP3 motor compact, outputs ignored, and the comparison workflow local to this TP4 repo | Requires one careful engine touch if we want exact sampled states without huge event-snapshot files |
| Port the full old TP3 study pipeline into this repo | Not recommended for v1 | Reuses more prior code | Bigger diff, pulls plotting/animation concerns into a repo that only needs reference outputs |
| Reimplement TP3 in Java beside TP4 System 2 | Not recommended | Same language as TP4 | Higher risk and unnecessary because the TP3 motor already exists |

## Phase 1: Read-Only Enunciado And Code Audit

**Purpose:** Decide what is compliant now, what is missing, and what must be added before producing comparison-grade outputs.

**Files:**

- Read: `CLAUDE.md`
- Read: `README.md`
- Read: `docs/TP3_Enunciado.pdf`
- Read: `SdS_TP3_2026Q1G01CS2_Codigo/src/tp3_sds/system1/config.py`
- Read: `SdS_TP3_2026Q1G01CS2_Codigo/src/tp3_sds/system1/simulation.py`
- Read: `SdS_TP3_2026Q1G01CS2_Codigo/src/tp3_sds/system1/output.py`
- Read: `SdS_TP3_2026Q1G01CS2_Codigo/src/tp3_sds/system1/observables.py`
- Optional reference: `/Users/keoni/Claude-Workspace/projects/tp3-sds-2026Q1G01S2/docs/wiki/source_tp3_enunciado.md`

**Checklist:**

- [ ] Confirm the motor uses event-driven molecular dynamics, not fixed time stepping.
- [ ] Confirm geometry: `L = 80 m`, obstacle radius `r0 = 1 m`, particle radius `r = 1 m`.
- [ ] Confirm particle initial velocity magnitude `v0 = 1 m/s` and random direction in `[0, 2pi)`.
- [ ] Confirm initial state is `fresh`, obstacle contact turns `fresh -> used`, and outer wall contact turns `used -> fresh`.
- [ ] Confirm the text output contains positions, velocities, and color/state.
- [ ] Confirm `Cfc(t)` is available as a time series, not only a final count.
- [ ] Confirm `Fu(t)` and radial profile samples are available or can be emitted without rerunning.
- [ ] Record the current gap: the compact local TP3 copy does not expose the full `study` command needed for 1.1-1.4 aggregates.

**Verification command:**

```bash
cd SdS_TP3_2026Q1G01CS2_Codigo
PYTHONPATH=src python3 -m tp3_sds system1 validate-config --config configs/system1.example.toml
```

Expected:

```text
Config validation passed.
```

**Audit output:**

- Create: `docs/2026-05-11_tp3-enunciado-audit_v1.md`
- Include a table with columns: `Enunciado item`, `Required`, `Current evidence`, `Gap`, `Action`.

## Phase 2: Define The TP3 Reference Output Contract

**Purpose:** Make TP3 outputs comparable with TP4 outputs without pretending the algorithms have the same time model.

**Files:**

- Create: `docs/2026-05-11_tp3-reference-output-contract_v1.md`
- Modify later if needed: `README.md`

**Run grid:**

```text
N = 100, 250, 500, 750, 1000
realizations = 5 per N
seed_start = 12345
seeds = 12345, 12346, 12347, 12348, 12349
tf = 500 s
comparison_dt = 1e-4
state_stride = 5000
full_contact_stride = 5000
boundary_force_stride = 5000
sample_dt = comparison_dt * state_stride = 0.5 s
```

**Output root:**

```text
outputs/tp3-reference/tp3-final-grid/
```

**Per-run files:**

```text
outputs/tp3-reference/tp3-final-grid/raw/N_100/r_00/metadata.json
outputs/tp3-reference/tp3-final-grid/raw/N_100/r_00/states.csv
outputs/tp3-reference/tp3-final-grid/raw/N_100/r_00/contacts.csv
outputs/tp3-reference/tp3-final-grid/raw/N_100/r_00/center_contacts.csv
outputs/tp3-reference/tp3-final-grid/raw/N_100/r_00/used_fraction.csv
outputs/tp3-reference/tp3-final-grid/raw/N_100/r_00/radial_profile_samples.csv
```

**Root manifest:**

```text
outputs/tp3-reference/tp3-final-grid/manifest.csv
```

**Column contract:**

- `manifest.csv`: `run_id,N,realization,seed,tf,comparison_dt,state_stride,full_contact_stride,boundary_force_stride,sample_dt,output_dir`
- `metadata.json`: simulation parameters, code path, output contract version, event-driven note, generated file list.
- `states.csv`: `time,particle_id,x,y,vx,vy,state`
- `contacts.csv`: `time,event_id,type,particle_id,other_particle_id,was_fresh,became_used`
- `center_contacts.csv`: `time,c_fc`
- `used_fraction.csv`: `time,used_fraction`
- `radial_profile_samples.csv`: `time,radius_start,radius_end,density,normal_velocity,inward_flux,valid_count`

**Decision:** Do not force TP3 to write TP4's `boundary_forces.csv` in v1. TP3 hard-sphere collisions are impulsive event contacts, while TP4 boundary forces are time-stepped force aggregates. If force comparison becomes necessary, add a separate `boundary_impulses.csv` with explicit impulse/bin semantics.

## Phase 3: Add A Small Sampling Hook To The TP3 Motor

**Purpose:** Export TP3 state at `sample_dt = 0.5 s` without writing every event snapshot and without changing collision physics.

**Files:**

- Modify: `SdS_TP3_2026Q1G01CS2_Codigo/src/tp3_sds/system1/simulation.py`
- Test: `SdS_TP3_2026Q1G01CS2_Codigo/tests/test_system1_sampling.py`

**Implementation shape:**

- Add a public method on `SimulationEngine`:

```python
def sampled_state(self) -> list[Particle]:
    return [clone_particle(particle) for particle in self.particles]
```

- Add a lightweight contact-event dataclass:

```python
@dataclass(frozen=True)
class ContactEventRecord:
    time: float
    event_id: int
    kind: str
    particle_id: int
    other_particle_id: int | None
    was_fresh: bool
    became_used: bool
```

- Add optional event sink support so `_process_event()` can stream records instead of accumulating large lists in memory.
- Keep existing `run_simulation()` behavior compatible with the current compact CLI.

**Tests:**

- [ ] A smoke engine can call `run_until(0.5)`, read `sampled_state()`, and get non-overlapping particles.
- [ ] Sampling does not increment `processed_events`.
- [ ] A fresh obstacle collision writes `became_used = true`.
- [ ] An outer wall collision for a used particle writes state recovery.

**Verification command:**

```bash
cd SdS_TP3_2026Q1G01CS2_Codigo
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_*.py'
```

Expected:

```text
OK
```

## Phase 4: Add The TP3 Reference Sweep Runner

**Purpose:** Generate configs, manifest, and optionally execute the 25 TP3 reference runs.

**Files:**

- Create: `scripts/run_tp3_reference_sweep.py`
- Create: `scripts/test_run_tp3_reference_sweep.py`
- Create generated, ignored output files under `outputs/tp3-reference/`

**CLI contract:**

```bash
python3 scripts/run_tp3_reference_sweep.py
python3 scripts/run_tp3_reference_sweep.py --execute
```

**Default settings:**

```text
experiment_id = tp3-final-grid
particle_counts = 100,250,500,750,1000
seed_count = 5
seed_start = 12345
tf = 500.0
comparison_dt = 0.0001
state_stride = 5000
full_contact_stride = 5000
boundary_force_stride = 5000
```

**Dry-run behavior:**

- Write generated TOML configs under `outputs/tp3-reference/tp3-final-grid/configs/`.
- Write `manifest.csv`.
- Print run count: `25`.
- Print sample cadence: `0.5 s`.
- Do not run simulations unless `--execute` is present.

**Execute behavior:**

- Run a preflight validation.
- For each `(N, seed)`:
  - instantiate the TP3 event engine;
  - sample states every `0.5 s` through `tf = 500 s`;
  - stream contacts and derived observables to per-run CSV;
  - write `metadata.json`;
  - append the run to `manifest.csv`.

**Smoke command before full execution:**

```bash
python3 scripts/run_tp3_reference_sweep.py \
  --experiment-id tp3-smoke \
  --particle-counts 100 \
  --seed-count 1 \
  --tf 5 \
  --execute
```

Expected:

```text
Wrote 1 configs
Manifest: outputs/tp3-reference/tp3-smoke/manifest.csv
Completed 1/1 runs
```

## Phase 5: Aggregate TP3 Observables For Later TP4 Comparison

**Purpose:** Produce the same scientific observables requested by the TP3 enunciado and useful for validating TP4 System 2.

**Files:**

- Create: `analysis-python/system2/aggregate_tp3_reference.py`
- Test: `analysis-python/system2/test_aggregate_tp3_reference.py`
- Create generated outputs under `outputs/tp3-reference/tp3-final-grid/aggregates/`

**Aggregate files:**

```text
outputs/tp3-reference/tp3-final-grid/aggregates/runtime_vs_n.csv
outputs/tp3-reference/tp3-final-grid/aggregates/scanning_rate_vs_n.csv
outputs/tp3-reference/tp3-final-grid/aggregates/used_fraction_vs_n.csv
outputs/tp3-reference/tp3-final-grid/aggregates/near_shell_s2_vs_n.csv
```

**Rules:**

- `J` comes from linear regression over exact `center_contacts.csv`.
- `Fu(t)` comes from sampled `used_fraction.csv`.
- Stationary detection should reuse the old TP3 study convention unless a stronger TP4-specific comparison rule is chosen.
- Radial profiles use fresh inward particles only: `R dot v < 0`.
- Near-shell convention is `[2.0, 2.2)`.

**Verification command:**

```bash
python3 analysis-python/system2/aggregate_tp3_reference.py \
  --manifest outputs/tp3-reference/tp3-smoke/manifest.csv
```

Expected:

```text
Wrote aggregates under outputs/tp3-reference/tp3-smoke/aggregates
```

## Phase 6: Validate `dt = 1e-4` For TP4, Not TP3

**Purpose:** Confirm that the chosen TP4 integration step is stable enough before using it as the comparison baseline.

**Files:**

- Reuse: `scripts/run_system2_sweep.py`
- Optional create: `docs/2026-05-11_tp4-dt-validation_v1.md`

**Pilot grid:**

```text
N = 100
seed_count = 1
tf = 20 s or 50 s
dt candidates = 5e-4, 2e-4, 1e-4
state_stride adjusted so state sample cadence stays near 0.5 s
```

**Acceptance criteria:**

- No overlaps or numeric instability in TP4 output.
- `Cfc(t)` and `Fu(t)` trends do not change materially between `2e-4` and `1e-4`.
- Output file sizes remain manageable with the chosen strides.

**Important:** This phase validates TP4 numerical integration. TP3 remains event-driven and does not become a fixed-`dt` simulation.

## Phase 7: Full Run And Handoff

**Purpose:** Generate the real TP3 reference dataset only after smoke runs and dt validation are clean.

**Commands:**

```bash
python3 scripts/run_tp3_reference_sweep.py
python3 scripts/run_tp3_reference_sweep.py --execute
python3 analysis-python/system2/aggregate_tp3_reference.py \
  --manifest outputs/tp3-reference/tp3-final-grid/manifest.csv
```

**Expected run count:**

```text
25 TP3 runs = 5 N values * 5 seeds
```

**Expected state row scale:**

With `sample_dt = 0.5 s` and `tf = 500 s`, each run has `1001` sample times. The largest run has about `1,001,000` state rows for `N=1000`. Across all runs, expect tens of millions of state rows. Keep all generated files under ignored `outputs/`.

## Rollback

- Delete generated data only after confirmation:

```bash
rm -rf outputs/tp3-reference/tp3-smoke
```

- Revert code changes with normal Git review, not `git reset --hard`.
- The safest rollback boundary is:
  - remove `scripts/run_tp3_reference_sweep.py`
  - remove `scripts/test_run_tp3_reference_sweep.py`
  - remove sampling additions from `SdS_TP3_2026Q1G01CS2_Codigo/src/tp3_sds/system1/simulation.py`
  - remove aggregate script/tests if added

## Execution Order

- [ ] Phase 1: produce the enunciado audit.
- [ ] Phase 2: lock the output contract.
- [ ] Phase 3: add and test minimal sampling/contact hooks.
- [ ] Phase 4: add the sweep runner and smoke it.
- [ ] Phase 5: aggregate TP3 observables.
- [ ] Phase 6: validate TP4 `dt = 1e-4` on a pilot.
- [ ] Phase 7: run full TP3 reference dataset and aggregate it.

## Next Actions

- [ ] Confirm that the TP3 seed sequence should match TP4's current default: `12345..12349`.
- [ ] Confirm whether v1 should skip `boundary_forces.csv` and use `contacts.csv`/`center_contacts.csv` as the TP3 event counterpart.
- [ ] If confirmed, implement Phase 1 and Phase 2 first, then stop for review before touching engine code.
