from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

from tp3_sds.system1.config import OutputConfig, SimulationConfig
from tp3_sds.system1.model import Particle, ParticleState


@dataclass(frozen=True)
class SnapshotHeader:
    duration: float
    particle_count: int
    domain_diameter: float
    obstacle_radius: float
    particle_radius: float
    snapshot_every: int
    fresh_color: tuple[int, int, int]
    used_color: tuple[int, int, int]
    config_path: str | None = None


@dataclass(frozen=True)
class ParsedParticle:
    id: int
    x: float
    y: float
    vx: float
    vy: float
    state: str
    r: int
    g: int
    b: int


@dataclass(frozen=True)
class ParsedStep:
    event_id: int
    time: float
    n_used: int
    particles: list[ParsedParticle]


@dataclass(frozen=True)
class ParsedSnapshotOutput:
    header: SnapshotHeader
    steps: list[ParsedStep]


def particle_color(particle: Particle, output_config: OutputConfig) -> tuple[int, int, int]:
    if particle.state == ParticleState.USED:
        return output_config.used_color
    return output_config.fresh_color


class SnapshotWriter:
    def __init__(self, handle: TextIO, config: SimulationConfig, config_path: Path | None = None) -> None:
        self.handle = handle
        self.config = config
        self.config_path = config_path

    def write_header(self) -> None:
        geometry = self.config.geometry
        self.handle.write("# tp3-sds system1 output\n")
        if self.config_path is not None:
            self.handle.write(f"config_path = {self.config_path}\n")
        self.handle.write(f"duration = {self.config.duration:.6f}\n")
        self.handle.write(f"particle_count = {self.config.particles.count}\n")
        self.handle.write(f"domain_diameter = {geometry.diameter:.6f}\n")
        self.handle.write(f"obstacle_radius = {geometry.obstacle_radius:.6f}\n")
        self.handle.write(f"particle_radius = {geometry.particle_radius:.6f}\n")
        self.handle.write(f"snapshot_every = {self.config.output.snapshot_every}\n")
        self.handle.write(f"fresh_color = {','.join(str(value) for value in self.config.output.fresh_color)}\n")
        self.handle.write(f"used_color = {','.join(str(value) for value in self.config.output.used_color)}\n")
        self.handle.write("---\n")

    def write_step(self, event_id: int, time: float, particles: list[Particle]) -> None:
        n_used = sum(particle.state == ParticleState.USED for particle in particles)
        self.handle.write(f"step event_id={event_id} time={time:.6f} n_used={n_used}\n")
        for particle in particles:
            red, green, blue = particle_color(particle, self.config.output)
            self.handle.write(
                "particle "
                f"id={particle.id} "
                f"x={particle.x:.6f} "
                f"y={particle.y:.6f} "
                f"vx={particle.vx:.6f} "
                f"vy={particle.vy:.6f} "
                f"state={particle.state.value} "
                f"r={red} "
                f"g={green} "
                f"b={blue}\n"
            )


REQUIRED_HEADER_FIELDS = {
    "duration",
    "particle_count",
    "domain_diameter",
    "obstacle_radius",
    "particle_radius",
    "snapshot_every",
    "fresh_color",
    "used_color",
}


def parse_snapshot_output(path: Path) -> ParsedSnapshotOutput:
    lines = path.read_text(encoding="utf-8").splitlines()
    header_lines: list[str] = []
    body_lines: list[str] = []
    in_body = False

    for line in lines:
        if not in_body:
            if line.strip() == "---":
                in_body = True
                continue
            header_lines.append(line)
            continue
        body_lines.append(line)

    if not in_body:
        raise ValueError(f"{path} is missing the header separator '---'.")

    header = _parse_header(header_lines, path)
    steps = _parse_steps(body_lines, header, path)
    return ParsedSnapshotOutput(header=header, steps=steps)


def parse_output(path: Path) -> list[ParsedStep]:
    return parse_snapshot_output(path).steps


def _parse_header(lines: list[str], path: Path) -> SnapshotHeader:
    raw_fields: dict[str, str] = {}
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            raise ValueError(f"{path} contains an invalid header line: {line!r}")
        key, value = stripped.split("=", maxsplit=1)
        raw_fields[key.strip()] = value.strip()

    missing = sorted(REQUIRED_HEADER_FIELDS - set(raw_fields))
    if missing:
        raise ValueError(f"{path} is missing required header fields: {', '.join(missing)}")

    return SnapshotHeader(
        config_path=raw_fields.get("config_path"),
        duration=float(raw_fields["duration"]),
        particle_count=int(raw_fields["particle_count"]),
        domain_diameter=float(raw_fields["domain_diameter"]),
        obstacle_radius=float(raw_fields["obstacle_radius"]),
        particle_radius=float(raw_fields["particle_radius"]),
        snapshot_every=int(raw_fields["snapshot_every"]),
        fresh_color=_parse_color(raw_fields["fresh_color"], path, "fresh_color"),
        used_color=_parse_color(raw_fields["used_color"], path, "used_color"),
    )


def _parse_steps(lines: list[str], header: SnapshotHeader, path: Path) -> list[ParsedStep]:
    steps: list[ParsedStep] = []
    current_fields: dict[str, str] | None = None
    current_particles: list[ParsedParticle] = []
    previous_time: float | None = None

    def finalize_current() -> None:
        nonlocal current_fields, current_particles, previous_time
        if current_fields is None:
            return

        step = ParsedStep(
            event_id=int(current_fields["event_id"]),
            time=float(current_fields["time"]),
            n_used=int(current_fields["n_used"]),
            particles=list(current_particles),
        )

        if len(step.particles) != header.particle_count:
            raise ValueError(
                f"{path} step event_id={step.event_id} has {len(step.particles)} particles; "
                f"expected {header.particle_count}."
            )
        actual_n_used = sum(particle.state == ParticleState.USED.value for particle in step.particles)
        if step.n_used != actual_n_used:
            raise ValueError(
                f"{path} step event_id={step.event_id} reports n_used={step.n_used} but contains {actual_n_used} used particles."
            )
        if previous_time is not None and step.time < previous_time:
            raise ValueError(f"{path} contains out-of-order step times at event_id={step.event_id}.")

        previous_time = step.time
        steps.append(step)
        current_fields = None
        current_particles = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("step "):
            finalize_current()
            current_fields = _parse_fields(stripped)
            current_particles = []
            continue
        if stripped.startswith("particle "):
            if current_fields is None:
                raise ValueError(f"{path} contains a particle entry before any step line.")
            current_particles.append(_parse_particle(stripped, path))
            continue
        raise ValueError(f"{path} contains an unrecognized body line: {line!r}")

    finalize_current()
    if not steps:
        raise ValueError(f"{path} does not contain any step entries.")
    return steps


def _parse_particle(line: str, path: Path) -> ParsedParticle:
    parts = _parse_fields(line)
    particle = ParsedParticle(
        id=int(parts["id"]),
        x=float(parts["x"]),
        y=float(parts["y"]),
        vx=float(parts["vx"]),
        vy=float(parts["vy"]),
        state=parts["state"],
        r=int(parts["r"]),
        g=int(parts["g"]),
        b=int(parts["b"]),
    )
    if particle.state not in {state.value for state in ParticleState}:
        raise ValueError(f"{path} contains an invalid particle state: {particle.state!r}")
    _validate_color_channels((particle.r, particle.g, particle.b), path, f"particle id={particle.id}")
    return particle


def _parse_fields(line: str) -> dict[str, str]:
    chunks = line.split()[1:]
    parsed: dict[str, str] = {}
    for chunk in chunks:
        if "=" not in chunk:
            raise ValueError(f"Malformed field in line: {line!r}")
        key, value = chunk.split("=", maxsplit=1)
        parsed[key] = value
    return parsed


def _parse_color(raw_value: str, path: Path, label: str) -> tuple[int, int, int]:
    channels = tuple(int(part.strip()) for part in raw_value.split(",") if part.strip())
    _validate_color_channels(channels, path, label)
    return channels


def _validate_color_channels(channels: tuple[int, ...], path: Path, label: str) -> None:
    if len(channels) != 3 or any(channel < 0 or channel > 255 for channel in channels):
        raise ValueError(f"{path} contains an invalid RGB triplet for {label}: {channels!r}")
