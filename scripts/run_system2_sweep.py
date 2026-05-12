#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
JAVA_PROJECT_DIR = PROJECT_ROOT / "SdS_TP4_2026Q1G01CS2_Codigo"
DEFAULT_PARTICLE_COUNTS = (100, 250, 500, 750, 1000)
REQUIRED_STIFFNESS_VALUES = (100.0, 1000.0, 10000.0)
REQUIRED_OUTPUT_FILES = (
    "metadata.json",
    "states.csv",
    "contacts.csv",
    "contact_events.csv",
    "boundary_forces.csv",
)


@dataclass(frozen=True)
class SweepSettings:
    experiment_id: str = "system2-tp4-final"
    particle_counts: tuple[int, ...] = DEFAULT_PARTICLE_COUNTS
    seed_count: int = 5
    seed_start: int = 12345
    final_time: float = 500.0
    dt: float = 0.0001
    state_stride: int = 5000
    full_contact_stride: int = 5000
    boundary_force_stride: int = 5000
    stiffness_values: tuple[float, ...] = field(default=REQUIRED_STIFFNESS_VALUES, init=False)

    def __post_init__(self) -> None:
        if not self.experiment_id:
            raise ValueError("experiment_id must not be blank")
        if not 1 <= self.seed_count <= 5:
            raise ValueError("seed_count must be between 1 and 5")
        if any(count < 100 or count > 1000 for count in self.particle_counts):
            raise ValueError("particle_counts must stay inside the TP4 range [100, 1000]")
        if self.final_time <= 0.0:
            raise ValueError("final_time must be positive")
        if self.dt <= 0.0:
            raise ValueError("dt must be positive")
        if any(stride <= 0 for stride in (self.state_stride, self.full_contact_stride, self.boundary_force_stride)):
            raise ValueError("output strides must be positive")

    @property
    def steps(self) -> int:
        return int(round(self.final_time / self.dt))

    @property
    def seeds(self) -> tuple[int, ...]:
        return tuple(self.seed_start + index for index in range(self.seed_count))


@dataclass(frozen=True)
class RunSpec:
    settings: SweepSettings
    stiffness: float
    particle_count: int
    realization: int
    seed: int
    config_path: Path
    output_dir: Path

    @property
    def run_id(self) -> str:
        return f"system2-k{format_stiffness_id(self.stiffness)}-n{self.particle_count}-r{self.realization:02d}"


def build_run_specs(settings: SweepSettings) -> list[RunSpec]:
    runs: list[RunSpec] = []
    base_dir = Path("outputs") / "system2-sweeps" / settings.experiment_id
    for stiffness in settings.stiffness_values:
        stiffness_id = format_stiffness_id(stiffness)
        for particle_count in settings.particle_counts:
            for realization, seed in enumerate(settings.seeds):
                config_path = (
                    base_dir
                    / "configs"
                    / f"k_{stiffness_id}"
                    / f"N_{particle_count}"
                    / f"r_{realization:02d}.toml"
                )
                output_dir = (
                    base_dir
                    / "raw"
                    / f"k_{stiffness_id}"
                    / f"N_{particle_count}"
                    / f"r_{realization:02d}"
                )
                runs.append(RunSpec(settings, stiffness, particle_count, realization, seed, config_path, output_dir))
    return runs


def render_toml(run: RunSpec) -> str:
    relative_output_dir = relative_output_dir_for_config(run)
    settings = run.settings
    return (
        "[run]\n"
        f'run_id = "{run.run_id}"\n'
        f"realization = {run.realization}\n"
        f'output_dir = "{relative_output_dir}"\n'
        "\n"
        "[geometry]\n"
        "diameter = 80.0\n"
        "obstacle_radius = 1.0\n"
        "particle_radius = 1.0\n"
        "\n"
        "[particles]\n"
        f"count = {run.particle_count}\n"
        "mass = 1.0\n"
        "initial_speed = 1.0\n"
        "\n"
        "[interaction]\n"
        f"k = {run.stiffness:.1f}\n"
        "\n"
        "[simulation]\n"
        f"dt = {settings.dt:g}\n"
        f"steps = {settings.steps}\n"
        f"seed = {run.seed}\n"
        "\n"
        "[output]\n"
        f"state_stride = {settings.state_stride}\n"
        f"full_contact_stride = {settings.full_contact_stride}\n"
        f"boundary_force_stride = {settings.boundary_force_stride}\n"
    )


def write_configs_and_manifest(runs: list[RunSpec]) -> Path:
    if not runs:
        raise ValueError("runs must not be empty")
    for run in runs:
        absolute_config_path = PROJECT_ROOT / run.config_path
        absolute_config_path.parent.mkdir(parents=True, exist_ok=True)
        absolute_config_path.write_text(render_toml(run), encoding="utf-8")

    manifest_path = PROJECT_ROOT / "outputs" / "system2-sweeps" / runs[0].settings.experiment_id / "manifest.csv"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8", newline="") as manifest_file:
        writer = csv.DictWriter(
            manifest_file,
            fieldnames=("run_id", "k", "N", "realization", "seed", "config_path", "output_dir"),
        )
        writer.writeheader()
        for run in runs:
            writer.writerow(
                {
                    "run_id": run.run_id,
                    "k": f"{run.stiffness:.1f}",
                    "N": run.particle_count,
                    "realization": run.realization,
                    "seed": run.seed,
                    "config_path": run.config_path.as_posix(),
                    "output_dir": run.output_dir.as_posix(),
                }
            )
    return manifest_path


def run_sweep(runs: list[RunSpec], skip_tests: bool, resume: bool = False) -> None:
    if not skip_tests:
        subprocess.run(["mvn", "test"], cwd=JAVA_PROJECT_DIR, check=True)

    skipped = 0
    for index, run in enumerate(runs, start=1):
        if resume and is_run_complete(run):
            skipped += 1
            print(f"[{index}/{len(runs)}] {run.run_id} SKIP complete existing output", flush=True)
            continue
        print(f"[{index}/{len(runs)}] {run.run_id}", flush=True)
        subprocess.run(
            ["mvn", "exec:java", f"-Dexec.args=system2 {(PROJECT_ROOT / run.config_path).as_posix()}"],
            cwd=JAVA_PROJECT_DIR,
            check=True,
        )
    if resume:
        print(f"Resume skipped {skipped}/{len(runs)} complete runs.", flush=True)


def is_run_complete(run: RunSpec) -> bool:
    output_dir = absolute_project_path(run.output_dir)
    if not all((output_dir / file_name).is_file() for file_name in REQUIRED_OUTPUT_FILES):
        return False
    if any((output_dir / file_name).stat().st_size == 0 for file_name in REQUIRED_OUTPUT_FILES):
        return False

    metadata = load_json_file(output_dir / "metadata.json")
    if metadata is None:
        return False
    settings = run.settings
    expected_values: dict[str, object] = {
        "run_id": run.run_id,
        "realization": run.realization,
        "seed": run.seed,
        "N": run.particle_count,
        "k": run.stiffness,
        "dt": settings.dt,
        "steps": settings.steps,
        "state_stride": settings.state_stride,
        "full_contact_stride": settings.full_contact_stride,
        "boundary_force_stride": settings.boundary_force_stride,
    }
    for key, expected in expected_values.items():
        if key not in metadata or not metadata_value_matches(metadata[key], expected):
            return False

    final_state_step = last_csv_step(output_dir / "states.csv")
    return final_state_step == settings.steps


def load_json_file(path: Path) -> dict[str, object] | None:
    try:
        with path.open(encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def metadata_value_matches(actual: object, expected: object) -> bool:
    if isinstance(expected, float):
        try:
            return abs(float(actual) - expected) <= max(1e-9, abs(expected) * 1e-9)
        except (TypeError, ValueError):
            return False
    return actual == expected


def last_csv_step(path: Path) -> int | None:
    last_line = read_last_nonempty_line(path)
    if last_line is None:
        return None
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            header = handle.readline().strip()
        record = next(csv.DictReader([header, last_line]))
        return int(record["step"])
    except (OSError, KeyError, StopIteration, ValueError, csv.Error):
        return None


def read_last_nonempty_line(path: Path) -> str | None:
    try:
        with path.open("rb") as handle:
            handle.seek(0, os.SEEK_END)
            position = handle.tell()
            buffer = b""
            while position > 0:
                read_size = min(4096, position)
                position -= read_size
                handle.seek(position)
                buffer = handle.read(read_size) + buffer
                lines = [line for line in buffer.splitlines() if line.strip()]
                if len(lines) >= 2 or position == 0:
                    return lines[-1].decode("utf-8")
    except OSError:
        return None
    return None


def absolute_project_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def relative_output_dir_for_config(run: RunSpec) -> str:
    return path_relative_to(run.output_dir, run.config_path.parent).as_posix()


def path_relative_to(path: Path, start: Path) -> Path:
    absolute_path = (PROJECT_ROOT / path).resolve()
    absolute_start = (PROJECT_ROOT / start).resolve()
    return Path(__import__("os").path.relpath(absolute_path, absolute_start))


def format_stiffness_id(stiffness: float) -> str:
    if stiffness.is_integer():
        return str(int(stiffness))
    return str(stiffness).replace(".", "p")


def parse_particle_counts(raw_counts: str) -> tuple[int, ...]:
    counts = tuple(int(value.strip()) for value in raw_counts.split(",") if value.strip())
    if not counts:
        raise ValueError("at least one particle count is required")
    return counts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate and optionally run the TP4 System 2 sweep.")
    parser.add_argument("--experiment-id", default="system2-tp4-final")
    parser.add_argument("--particle-counts", default="100,250,500,750,1000")
    parser.add_argument("--seed-count", type=int, default=5)
    parser.add_argument("--seed-start", type=int, default=12345)
    parser.add_argument("--tf", type=float, default=500.0)
    parser.add_argument("--dt", type=float, default=0.0001)
    parser.add_argument("--state-stride", type=int, default=5000)
    parser.add_argument("--full-contact-stride", type=int, default=5000)
    parser.add_argument("--boundary-force-stride", type=int, default=5000)
    parser.add_argument("--execute", action="store_true", help="Run Maven simulations after writing configs.")
    parser.add_argument("--skip-preflight-tests", action="store_true", help="Skip mvn test before --execute.")
    parser.add_argument("--resume", action="store_true", help="Skip runs whose existing raw outputs are complete.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    settings = SweepSettings(
        experiment_id=args.experiment_id,
        particle_counts=parse_particle_counts(args.particle_counts),
        seed_count=args.seed_count,
        seed_start=args.seed_start,
        final_time=args.tf,
        dt=args.dt,
        state_stride=args.state_stride,
        full_contact_stride=args.full_contact_stride,
        boundary_force_stride=args.boundary_force_stride,
    )
    runs = build_run_specs(settings)
    manifest_path = write_configs_and_manifest(runs)
    print(f"Wrote {len(runs)} configs")
    print(f"Manifest: {manifest_path.relative_to(PROJECT_ROOT).as_posix()}")
    print(f"N values: {','.join(str(value) for value in settings.particle_counts)}")
    print("k values: 100,1000,10000")
    print(f"seeds: {','.join(str(value) for value in settings.seeds)}")
    print(f"tf={settings.final_time:g} dt={settings.dt:g} steps={settings.steps}")

    if args.execute:
        run_sweep(runs, skip_tests=args.skip_preflight_tests, resume=args.resume)
    else:
        print("Dry-run only. Add --execute to run the simulations.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
