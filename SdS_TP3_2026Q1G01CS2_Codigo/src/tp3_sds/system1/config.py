from __future__ import annotations

import math
import tomllib
from dataclasses import dataclass
from pathlib import Path

from tp3_sds.system1.model import Geometry

DEFAULT_FRESH_COLOR = (0, 255, 0)
DEFAULT_USED_COLOR = (148, 0, 211)
DEFAULT_AUTO_COUNTS = (8, 16, 24, 32, 48, 64, 80, 96, 128)


@dataclass(frozen=True)
class ParticleConfig:
    count: int
    mass: float = 1.0
    speed: float = 1.0


@dataclass(frozen=True)
class OutputConfig:
    path: Path
    snapshot_every: int = 1
    fresh_color: tuple[int, int, int] = DEFAULT_FRESH_COLOR
    used_color: tuple[int, int, int] = DEFAULT_USED_COLOR


@dataclass(frozen=True)
class ObservableConfig:
    radial_bin_width: float = 0.2


@dataclass(frozen=True)
class SimulationConfig:
    geometry: Geometry
    particles: ParticleConfig
    output: OutputConfig
    observables: ObservableConfig
    duration: float
    seed: int | None = None
    max_events: int = 10_000_000


@dataclass(frozen=True)
class StationaryDetectionConfig:
    resample_dt: float = 0.5
    window_seconds: float = 10.0
    check_interval: float = 5.0
    tolerance: float = 0.02
    consecutive_checks: int = 3
    settle_extension: float = 20.0
    max_time: float = 2000.0


@dataclass(frozen=True)
class StudyOutputConfig:
    artifacts_root: Path
    study_id: str
    snapshot_every: int = 10
    generate_figures: bool = True


@dataclass(frozen=True)
class StudyConfig:
    geometry: Geometry
    particles: ParticleConfig
    observables: ObservableConfig
    output: StudyOutputConfig
    counts_mode: str = "explicit"
    counts: tuple[int, ...] = ()
    auto_counts: tuple[int, ...] = DEFAULT_AUTO_COUNTS
    repetitions: int = 5
    seed_start: int = 1
    runtime_duration: float = 500.0
    runtime_limit_seconds: float = 2000.0
    stationary: StationaryDetectionConfig = StationaryDetectionConfig()
    max_events: int = 100_000_000
    fresh_color: tuple[int, int, int] = DEFAULT_FRESH_COLOR
    used_color: tuple[int, int, int] = DEFAULT_USED_COLOR

    def planned_counts(self) -> list[int]:
        return list(self.counts if self.counts_mode == "explicit" else self.auto_counts)

    def seeds(self) -> list[int]:
        return [self.seed_start + index for index in range(self.repetitions)]


@dataclass(frozen=True)
class ValidationResult:
    errors: list[str]
    warnings: list[str]

    @property
    def is_valid(self) -> bool:
        return not self.errors


def load_config(path: Path) -> SimulationConfig:
    with path.open("rb") as handle:
        data = tomllib.load(handle)

    simulation = data.get("simulation", {})
    geometry_data = data.get("geometry", {})
    particles_data = data.get("particles", {})
    output_data = data.get("output", {})
    observables_data = data.get("observables", {})

    geometry = Geometry(
        diameter=float(geometry_data.get("diameter", 80.0)),
        obstacle_radius=float(geometry_data.get("obstacle_radius", 1.0)),
        particle_radius=float(geometry_data.get("particle_radius", 1.0)),
    )
    particles = ParticleConfig(
        count=int(particles_data.get("count", 0)),
        mass=float(particles_data.get("mass", 1.0)),
        speed=float(particles_data.get("speed", 1.0)),
    )
    output_path = _resolve_path(path.parent, output_data.get("path", "artifacts/system1/latest.txt"))
    output = OutputConfig(
        path=output_path,
        snapshot_every=int(output_data.get("snapshot_every", 1)),
        fresh_color=_parse_color(output_data.get("fresh_color"), DEFAULT_FRESH_COLOR),
        used_color=_parse_color(output_data.get("used_color"), DEFAULT_USED_COLOR),
    )
    observables = ObservableConfig(
        radial_bin_width=float(observables_data.get("radial_bin_width", 0.2))
    )
    return SimulationConfig(
        geometry=geometry,
        particles=particles,
        output=output,
        observables=observables,
        duration=float(simulation.get("duration", 500.0)),
        seed=int(simulation["seed"]) if "seed" in simulation else None,
        max_events=int(simulation.get("max_events", 10_000_000)),
    )


def load_study_config(path: Path) -> StudyConfig:
    with path.open("rb") as handle:
        data = tomllib.load(handle)

    geometry_data = data.get("geometry", {})
    particles_data = data.get("particles", {})
    observables_data = data.get("observables", {})
    study_data = data.get("study", {})
    analysis_data = data.get("analysis", {})

    geometry = Geometry(
        diameter=float(geometry_data.get("diameter", 80.0)),
        obstacle_radius=float(geometry_data.get("obstacle_radius", 1.0)),
        particle_radius=float(geometry_data.get("particle_radius", 1.0)),
    )
    particles = ParticleConfig(
        count=int(particles_data.get("count", 0)),
        mass=float(particles_data.get("mass", 1.0)),
        speed=float(particles_data.get("speed", 1.0)),
    )
    observables = ObservableConfig(
        radial_bin_width=float(observables_data.get("radial_bin_width", 0.2))
    )
    output = StudyOutputConfig(
        artifacts_root=_resolve_path(path.parent, study_data.get("artifacts_root", "artifacts/system1/studies")),
        study_id=str(study_data.get("study_id", path.stem)),
        snapshot_every=int(study_data.get("snapshot_every", 10)),
        generate_figures=bool(study_data.get("generate_figures", True)),
    )
    stationary = StationaryDetectionConfig(
        resample_dt=float(analysis_data.get("resample_dt", 0.5)),
        window_seconds=float(analysis_data.get("window_seconds", 10.0)),
        check_interval=float(analysis_data.get("check_interval", 5.0)),
        tolerance=float(analysis_data.get("tolerance", 0.02)),
        consecutive_checks=int(analysis_data.get("consecutive_checks", 3)),
        settle_extension=float(analysis_data.get("settle_extension", 20.0)),
        max_time=float(analysis_data.get("max_time", 2000.0)),
    )

    counts = tuple(int(value) for value in study_data.get("counts", []))
    auto_counts = tuple(int(value) for value in study_data.get("auto_counts", DEFAULT_AUTO_COUNTS))

    return StudyConfig(
        geometry=geometry,
        particles=particles,
        observables=observables,
        output=output,
        counts_mode=str(study_data.get("counts_mode", "explicit")),
        counts=counts,
        auto_counts=auto_counts,
        repetitions=int(study_data.get("repetitions", 5)),
        seed_start=int(study_data.get("seed_start", 1)),
        runtime_duration=float(study_data.get("runtime_duration", 500.0)),
        runtime_limit_seconds=float(study_data.get("runtime_limit_seconds", 2000.0)),
        stationary=stationary,
        max_events=int(study_data.get("max_events", 100_000_000)),
        fresh_color=_parse_color(study_data.get("fresh_color"), DEFAULT_FRESH_COLOR),
        used_color=_parse_color(study_data.get("used_color"), DEFAULT_USED_COLOR),
    )


def validate_config(config: SimulationConfig) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    if config.duration <= 0:
        errors.append("simulation.duration must be positive.")
    if config.max_events <= 0:
        errors.append("simulation.max_events must be positive.")
    if config.particles.count <= 0:
        errors.append("particles.count must be greater than zero.")
    if config.particles.mass <= 0:
        errors.append("particles.mass must be positive.")
    if config.particles.speed <= 0:
        errors.append("particles.speed must be positive.")
    if config.output.snapshot_every <= 0:
        errors.append("output.snapshot_every must be greater than zero.")
    if config.observables.radial_bin_width <= 0:
        errors.append("observables.radial_bin_width must be positive.")
    _validate_geometry(config.geometry, errors)
    _validate_colors(config.output.fresh_color, "output.fresh_color", errors)
    _validate_colors(config.output.used_color, "output.used_color", errors)
    _validate_particle_density(config.geometry, config.particles.count, errors, warnings)

    return ValidationResult(errors=errors, warnings=warnings)


def validate_study_config(config: StudyConfig) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    if config.particles.mass <= 0:
        errors.append("particles.mass must be positive.")
    if config.particles.speed <= 0:
        errors.append("particles.speed must be positive.")
    if config.output.snapshot_every <= 0:
        errors.append("study.snapshot_every must be greater than zero.")
    if config.observables.radial_bin_width <= 0:
        errors.append("observables.radial_bin_width must be positive.")
    if config.repetitions <= 0:
        errors.append("study.repetitions must be greater than zero.")
    if config.runtime_duration <= 0:
        errors.append("study.runtime_duration must be positive.")
    if config.runtime_limit_seconds <= 0:
        errors.append("study.runtime_limit_seconds must be positive.")
    if config.max_events <= 0:
        errors.append("study.max_events must be positive.")
    if config.counts_mode not in {"explicit", "auto"}:
        errors.append("study.counts_mode must be 'explicit' or 'auto'.")
    if config.counts_mode == "explicit" and not config.counts:
        errors.append("study.counts must contain at least one particle count in explicit mode.")
    if config.counts_mode == "auto" and not config.auto_counts:
        errors.append("study.auto_counts must contain at least one particle count in auto mode.")
    if any(value <= 0 for value in config.planned_counts()):
        errors.append("All study particle counts must be positive integers.")

    stationary = config.stationary
    if stationary.resample_dt <= 0:
        errors.append("analysis.resample_dt must be positive.")
    if stationary.window_seconds <= 0:
        errors.append("analysis.window_seconds must be positive.")
    if stationary.check_interval <= 0:
        errors.append("analysis.check_interval must be positive.")
    if stationary.tolerance < 0:
        errors.append("analysis.tolerance must be non-negative.")
    if stationary.consecutive_checks <= 0:
        errors.append("analysis.consecutive_checks must be positive.")
    if stationary.settle_extension < 0:
        errors.append("analysis.settle_extension must be non-negative.")
    if stationary.max_time <= 0:
        errors.append("analysis.max_time must be positive.")
    if stationary.check_interval > stationary.window_seconds:
        warnings.append("analysis.check_interval is larger than the detection window; stationary detection may react late.")

    _validate_geometry(config.geometry, errors)
    _validate_colors(config.fresh_color, "study.fresh_color", errors)
    _validate_colors(config.used_color, "study.used_color", errors)
    for count in config.planned_counts():
        _validate_particle_density(config.geometry, count, errors, warnings, label=f"count={count}")

    return ValidationResult(errors=errors, warnings=warnings)


def build_run_config_from_study(
    study_config: StudyConfig,
    *,
    count: int,
    seed: int,
    duration: float,
    output_path: Path,
) -> SimulationConfig:
    return SimulationConfig(
        geometry=study_config.geometry,
        particles=ParticleConfig(count=count, mass=study_config.particles.mass, speed=study_config.particles.speed),
        output=OutputConfig(
            path=output_path,
            snapshot_every=study_config.output.snapshot_every,
            fresh_color=study_config.fresh_color,
            used_color=study_config.used_color,
        ),
        observables=study_config.observables,
        duration=duration,
        seed=seed,
        max_events=study_config.max_events,
    )


def _resolve_path(base_dir: Path, raw_path: str | Path) -> Path:
    path = Path(raw_path)
    if not path.is_absolute():
        path = (base_dir / path).resolve()
    return path


def _parse_color(raw_value: object, fallback: tuple[int, int, int]) -> tuple[int, int, int]:
    if raw_value is None:
        return fallback
    if isinstance(raw_value, (list, tuple)) and len(raw_value) == 3:
        return tuple(int(channel) for channel in raw_value)
    raise ValueError(f"Invalid color value {raw_value!r}. Expected a 3-item array.")


def _validate_geometry(geometry: Geometry, errors: list[str]) -> None:
    if geometry.diameter <= 0:
        errors.append("geometry.diameter must be positive.")
    if geometry.obstacle_radius <= 0:
        errors.append("geometry.obstacle_radius must be positive.")
    if geometry.particle_radius <= 0:
        errors.append("geometry.particle_radius must be positive.")
    if geometry.outer_travel_radius <= geometry.inner_travel_radius:
        errors.append("The annulus available to particle centers must have positive width.")


def _validate_colors(color: tuple[int, int, int], label: str, errors: list[str]) -> None:
    if len(color) != 3 or any(channel < 0 or channel > 255 for channel in color):
        errors.append(f"{label} must contain exactly three integers between 0 and 255.")


def _validate_particle_density(
    geometry: Geometry,
    particle_count: int,
    errors: list[str],
    warnings: list[str],
    *,
    label: str = "particles.count",
) -> None:
    if particle_count <= 0:
        return

    annulus_area = math.pi * (
        geometry.outer_travel_radius * geometry.outer_travel_radius
        - geometry.inner_travel_radius * geometry.inner_travel_radius
    )
    particle_area = math.pi * geometry.particle_radius * geometry.particle_radius
    if annulus_area <= 0:
        errors.append("Available annulus area is non-positive.")
    elif particle_count * particle_area > annulus_area * 0.45:
        warnings.append(
            f"{label} occupies more than 45% of the annulus area; random placement may fail."
        )
