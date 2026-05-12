#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TP3_PROJECT_DIR = PROJECT_ROOT / "SdS_TP3_2026Q1G01CS2_Codigo"
DEFAULT_PARTICLE_COUNTS = (100, 250, 500, 750, 1000)
REQUIRED_OUTPUT_FILES = (
    "snapshot.txt",
    "center_contacts.csv",
    "used_fraction.csv",
    "radial_profile_samples.csv",
    "radial_profiles.csv",
    "metadata.json",
)

sys.path.insert(0, str(TP3_PROJECT_DIR / "src"))

from tp3_sds.system1.config import load_config, validate_config  # noqa: E402
from tp3_sds.system1.simulation import SimulationResult, run_simulation  # noqa: E402


@dataclass(frozen=True)
class SweepSettings:
    experiment_id: str = "tp3-final-grid"
    particle_counts: tuple[int, ...] = DEFAULT_PARTICLE_COUNTS
    seed_count: int = 5
    seed_start: int = 12345
    final_time: float = 500.0
    comparison_dt: float = 0.0001
    state_stride: int = 5000
    full_contact_stride: int = 5000
    boundary_force_stride: int = 5000
    max_events: int = 100_000_000

    def __post_init__(self) -> None:
        if not self.experiment_id:
            raise ValueError("experiment_id must not be blank")
        if not 1 <= self.seed_count <= 5:
            raise ValueError("seed_count must be between 1 and 5")
        if any(count < 100 or count > 1000 for count in self.particle_counts):
            raise ValueError("particle_counts must stay inside the comparison range [100, 1000]")
        if self.final_time <= 0.0:
            raise ValueError("final_time must be positive")
        if self.comparison_dt <= 0.0:
            raise ValueError("comparison_dt must be positive")
        if any(stride <= 0 for stride in (self.state_stride, self.full_contact_stride, self.boundary_force_stride)):
            raise ValueError("output strides must be positive")
        if self.max_events <= 0:
            raise ValueError("max_events must be positive")

    @property
    def seeds(self) -> tuple[int, ...]:
        return tuple(self.seed_start + index for index in range(self.seed_count))

    @property
    def sample_dt(self) -> float:
        return self.comparison_dt * self.state_stride


@dataclass(frozen=True)
class RunSpec:
    settings: SweepSettings
    particle_count: int
    realization: int
    seed: int
    config_path: Path
    output_dir: Path

    @property
    def run_id(self) -> str:
        return f"tp3-n{self.particle_count}-r{self.realization:02d}"

    @property
    def snapshot_path(self) -> Path:
        return self.output_dir / "snapshot.txt"


def build_run_specs(settings: SweepSettings) -> list[RunSpec]:
    runs: list[RunSpec] = []
    base_dir = Path("outputs") / "tp3-reference" / settings.experiment_id
    for particle_count in settings.particle_counts:
        for realization, seed in enumerate(settings.seeds):
            config_path = base_dir / "configs" / f"N_{particle_count}" / f"r_{realization:02d}.toml"
            output_dir = base_dir / "raw" / f"N_{particle_count}" / f"r_{realization:02d}"
            runs.append(RunSpec(settings, particle_count, realization, seed, config_path, output_dir))
    return runs


def render_toml(run: RunSpec) -> str:
    settings = run.settings
    relative_output_path = path_relative_to(run.snapshot_path, run.config_path.parent).as_posix()
    return (
        "[reference]\n"
        f'run_id = "{run.run_id}"\n'
        f"realization = {run.realization}\n"
        f"comparison_dt = {settings.comparison_dt:g}\n"
        f"state_stride = {settings.state_stride}\n"
        f"full_contact_stride = {settings.full_contact_stride}\n"
        f"boundary_force_stride = {settings.boundary_force_stride}\n"
        f"sample_dt = {settings.sample_dt:g}\n"
        'note = "TP3 is event-driven; comparison_dt and strides document the TP4-compatible observation cadence, not a TP3 integration step."\n'
        "\n"
        "[simulation]\n"
        f"duration = {settings.final_time:g}\n"
        f"seed = {run.seed}\n"
        f"max_events = {settings.max_events}\n"
        "\n"
        "[geometry]\n"
        "diameter = 80.0\n"
        "obstacle_radius = 1.0\n"
        "particle_radius = 1.0\n"
        "\n"
        "[particles]\n"
        f"count = {run.particle_count}\n"
        "mass = 1.0\n"
        "speed = 1.0\n"
        "\n"
        "[output]\n"
        f'path = "{relative_output_path}"\n'
        f"snapshot_every = {settings.state_stride}\n"
        "fresh_color = [0, 255, 0]\n"
        "used_color = [148, 0, 211]\n"
        "\n"
        "[observables]\n"
        "radial_bin_width = 0.2\n"
    )


def write_configs_and_manifest(runs: list[RunSpec]) -> Path:
    if not runs:
        raise ValueError("runs must not be empty")
    for run in runs:
        absolute_config_path = PROJECT_ROOT / run.config_path
        absolute_config_path.parent.mkdir(parents=True, exist_ok=True)
        absolute_config_path.write_text(render_toml(run), encoding="utf-8")

    manifest_path = PROJECT_ROOT / "outputs" / "tp3-reference" / runs[0].settings.experiment_id / "manifest.csv"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8", newline="") as manifest_file:
        writer = csv.DictWriter(
            manifest_file,
            fieldnames=(
                "run_id",
                "N",
                "realization",
                "seed",
                "tf",
                "comparison_dt",
                "state_stride",
                "full_contact_stride",
                "boundary_force_stride",
                "sample_dt",
                "config_path",
                "output_dir",
                "snapshot_path",
            ),
        )
        writer.writeheader()
        for run in runs:
            settings = run.settings
            writer.writerow(
                {
                    "run_id": run.run_id,
                    "N": run.particle_count,
                    "realization": run.realization,
                    "seed": run.seed,
                    "tf": f"{settings.final_time:g}",
                    "comparison_dt": f"{settings.comparison_dt:g}",
                    "state_stride": settings.state_stride,
                    "full_contact_stride": settings.full_contact_stride,
                    "boundary_force_stride": settings.boundary_force_stride,
                    "sample_dt": f"{settings.sample_dt:g}",
                    "config_path": run.config_path.as_posix(),
                    "output_dir": run.output_dir.as_posix(),
                    "snapshot_path": run.snapshot_path.as_posix(),
                }
            )
    return manifest_path


def run_sweep(runs: list[RunSpec], skip_validation: bool, resume: bool = False) -> None:
    skipped = 0
    for index, run in enumerate(runs, start=1):
        if resume and is_run_complete(run):
            skipped += 1
            print(f"[{index}/{len(runs)}] {run.run_id} SKIP complete existing output", flush=True)
            continue
        config_path = (PROJECT_ROOT / run.config_path).resolve()
        config = load_config(config_path)
        if not skip_validation:
            validation = validate_config(config)
            if not validation.is_valid:
                raise ValueError("; ".join(validation.errors))
        print(f"[{index}/{len(runs)}] {run.run_id}", flush=True)
        started_at = time.perf_counter()
        result = run_simulation(config, config_path=config_path)
        runtime_seconds = time.perf_counter() - started_at
        write_reference_artifacts(run, result, runtime_seconds=runtime_seconds)
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
        "contract_version": "tp3-reference-v1",
        "run_id": run.run_id,
        "N": run.particle_count,
        "realization": run.realization,
        "seed": run.seed,
        "tf": settings.final_time,
        "comparison_dt": settings.comparison_dt,
        "sample_dt": settings.sample_dt,
        "state_stride": settings.state_stride,
        "full_contact_stride": settings.full_contact_stride,
        "boundary_force_stride": settings.boundary_force_stride,
    }
    for key, expected in expected_values.items():
        if key not in metadata or not metadata_value_matches(metadata[key], expected):
            return False
    try:
        return float(metadata.get("final_time", -1.0)) >= settings.final_time - 1e-6
    except (TypeError, ValueError):
        return False


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


def absolute_project_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def write_reference_artifacts(run: RunSpec, result: SimulationResult, *, runtime_seconds: float) -> None:
    output_dir = PROJECT_ROOT / run.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    write_metadata(run, result, runtime_seconds=runtime_seconds)
    write_center_contacts(output_dir / "center_contacts.csv", result)
    write_used_fraction(output_dir / "used_fraction.csv", result)
    write_radial_profile_samples(output_dir / "radial_profile_samples.csv", result)
    write_radial_profiles(output_dir / "radial_profiles.csv", result)


def write_metadata(run: RunSpec, result: SimulationResult, *, runtime_seconds: float) -> None:
    settings = run.settings
    metadata = {
        "contract_version": "tp3-reference-v1",
        "run_id": run.run_id,
        "N": run.particle_count,
        "realization": run.realization,
        "seed": run.seed,
        "tf": settings.final_time,
        "comparison_dt": settings.comparison_dt,
        "sample_dt": settings.sample_dt,
        "state_stride": settings.state_stride,
        "full_contact_stride": settings.full_contact_stride,
        "boundary_force_stride": settings.boundary_force_stride,
        "event_driven": True,
        "processed_events": result.processed_events,
        "snapshots_written": result.snapshots_written,
        "final_time": result.final_time,
        "runtime_seconds": runtime_seconds,
        "scanning_count": result.scanning_count,
        "files": [
            "snapshot.txt",
            "center_contacts.csv",
            "used_fraction.csv",
            "radial_profile_samples.csv",
            "radial_profiles.csv",
            "metadata.json",
        ],
        "note": (
            "TP3 is event-driven. comparison_dt and strides document the "
            "TP4-compatible observation cadence, not a TP3 integration step."
        ),
    }
    metadata_path = PROJECT_ROOT / run.output_dir / "metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_center_contacts(path: Path, result: SimulationResult) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=("time", "c_fc"))
        writer.writeheader()
        for time_value, count in result.center_contact_series:
            writer.writerow({"time": f"{time_value:.12g}", "c_fc": count})


def write_used_fraction(path: Path, result: SimulationResult) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=("time", "used_fraction"))
        writer.writeheader()
        for time_value, fraction in result.used_fraction_history:
            writer.writerow({"time": f"{time_value:.12g}", "used_fraction": f"{fraction:.12g}"})


def write_radial_profile_samples(path: Path, result: SimulationResult) -> None:
    inner = 2.0
    outer = 39.0
    bin_width = 0.2
    if result.radial_profiles:
        inner = result.radial_profiles[0].radius_start
        outer = result.radial_profiles[-1].radius_end
        bin_width = result.radial_profiles[0].radius_end - result.radial_profiles[0].radius_start
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=(
                "time",
                "radius_start",
                "radius_end",
                "density",
                "normal_velocity",
                "inward_flux",
                "valid_count",
            ),
        )
        writer.writeheader()
        for sample in result.radial_profile_samples:
            for index, density in enumerate(sample.densities):
                radius_start = inner + index * bin_width
                radius_end = min(outer, radius_start + bin_width)
                normal_velocity = sample.normal_velocities[index]
                writer.writerow(
                    {
                        "time": f"{sample.time:.12g}",
                        "radius_start": f"{radius_start:.12g}",
                        "radius_end": f"{radius_end:.12g}",
                        "density": f"{density:.12g}",
                        "normal_velocity": f"{normal_velocity:.12g}",
                        "inward_flux": f"{density * abs(normal_velocity):.12g}",
                        "valid_count": sample.valid_counts[index],
                    }
                )


def write_radial_profiles(path: Path, result: SimulationResult) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=(
                "radius_start",
                "radius_end",
                "density",
                "normal_velocity",
                "inward_flux",
                "samples",
                "particle_samples",
            ),
        )
        writer.writeheader()
        for radial_bin in result.radial_profiles:
            writer.writerow(
                {
                    "radius_start": f"{radial_bin.radius_start:.12g}",
                    "radius_end": f"{radial_bin.radius_end:.12g}",
                    "density": f"{radial_bin.density:.12g}",
                    "normal_velocity": f"{radial_bin.normal_velocity:.12g}",
                    "inward_flux": f"{radial_bin.inward_flux:.12g}",
                    "samples": radial_bin.samples,
                    "particle_samples": radial_bin.particle_samples,
                }
            )


def path_relative_to(path: Path, start: Path) -> Path:
    absolute_path = (PROJECT_ROOT / path).resolve()
    absolute_start = (PROJECT_ROOT / start).resolve()
    return Path(os.path.relpath(absolute_path, absolute_start))


def parse_particle_counts(raw_counts: str) -> tuple[int, ...]:
    counts = tuple(int(value.strip()) for value in raw_counts.split(",") if value.strip())
    if not counts:
        raise ValueError("at least one particle count is required")
    return counts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate and optionally run the TP3 reference sweep configs.")
    parser.add_argument("--experiment-id", default="tp3-final-grid")
    parser.add_argument("--particle-counts", default="100,250,500,750,1000")
    parser.add_argument("--seed-count", type=int, default=5)
    parser.add_argument("--seed-start", type=int, default=12345)
    parser.add_argument("--tf", type=float, default=500.0)
    parser.add_argument("--comparison-dt", type=float, default=0.0001)
    parser.add_argument("--state-stride", type=int, default=5000)
    parser.add_argument("--full-contact-stride", type=int, default=5000)
    parser.add_argument("--boundary-force-stride", type=int, default=5000)
    parser.add_argument("--max-events", type=int, default=100_000_000)
    parser.add_argument("--execute", action="store_true", help="Run TP3 simulations after writing configs.")
    parser.add_argument("--skip-validation", action="store_true", help="Skip per-config validation before --execute.")
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
        comparison_dt=args.comparison_dt,
        state_stride=args.state_stride,
        full_contact_stride=args.full_contact_stride,
        boundary_force_stride=args.boundary_force_stride,
        max_events=args.max_events,
    )
    runs = build_run_specs(settings)
    manifest_path = write_configs_and_manifest(runs)
    print(f"Wrote {len(runs)} configs")
    print(f"Manifest: {manifest_path.relative_to(PROJECT_ROOT).as_posix()}")
    print(f"N values: {','.join(str(value) for value in settings.particle_counts)}")
    print(f"seeds: {','.join(str(value) for value in settings.seeds)}")
    print(f"tf={settings.final_time:g} comparison_dt={settings.comparison_dt:g} sample_dt={settings.sample_dt:g}")
    print(
        "strides="
        f"{settings.state_stride},{settings.full_contact_stride},{settings.boundary_force_stride}"
    )

    if args.execute:
        run_sweep(runs, skip_validation=args.skip_validation, resume=args.resume)
    else:
        print("Dry-run only. Add --execute to run the simulations.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
