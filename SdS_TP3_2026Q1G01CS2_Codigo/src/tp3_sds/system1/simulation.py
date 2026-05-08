from __future__ import annotations

import heapq
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

from tp3_sds.system1.config import SimulationConfig, validate_config
from tp3_sds.system1.events import Event, EventKind
from tp3_sds.system1.model import Geometry, Particle, ParticleState
from tp3_sds.system1.observables import RadialProfileBin, RadialProfileSnapshot, System1Observables
from tp3_sds.system1.output import SnapshotWriter

EPSILON = 1e-9


@dataclass(frozen=True)
class SimulationResult:
    output_path: Path
    processed_events: int
    snapshots_written: int
    final_time: float
    scanning_count: int
    center_contact_series: list[tuple[float, int]]
    used_fraction_history: list[tuple[float, float]]
    radial_profiles: list[RadialProfileBin]
    radial_profile_samples: list[RadialProfileSnapshot]
    final_particles: list[Particle]


class SimulationEngine:
    def __init__(
        self,
        config: SimulationConfig,
        *,
        writer_handle: TextIO | None = None,
        config_path: Path | None = None,
    ) -> None:
        validation = validate_config(config)
        if not validation.is_valid:
            raise ValueError("; ".join(validation.errors))

        self.config = config
        self.config_path = config_path
        self.writer = SnapshotWriter(writer_handle, config, config_path=config_path) if writer_handle is not None else None
        self.observables = System1Observables(config.geometry, config.observables.radial_bin_width)
        self.particles = generate_initial_particles(config)
        self.current_time = 0.0
        self.processed_events = 0
        self.snapshots_written = 0
        self.last_snapshot_time = -math.inf
        self.last_snapshot_event_id: int | None = None
        self._queue: list[Event] = []
        self._sequence = 0

        if self.writer is not None:
            self.writer.write_header()

        self._schedule_initial_events()
        self._record_snapshot(0)

    def run_until(self, target_time: float) -> None:
        if target_time < self.current_time - EPSILON:
            raise ValueError("target_time must not move the simulation backwards.")

        while True:
            event = self._pop_next_valid_event()
            if event is None:
                break
            if event.time > target_time + EPSILON:
                self._push_event(event)
                break

            self._advance_all(event.time - self.current_time)
            self.current_time = event.time
            touched = self._process_event(event)
            self.processed_events += 1

            self._schedule_events_for_touched(touched)
            if self.processed_events % self.config.output.snapshot_every == 0:
                self._record_snapshot(self.processed_events)

        if target_time > self.current_time + EPSILON:
            self._advance_all(target_time - self.current_time)
            self.current_time = target_time

    def finalize(self, *, force_final_snapshot: bool = True) -> SimulationResult:
        if force_final_snapshot and (
            self.last_snapshot_event_id != self.processed_events
            or abs(self.current_time - self.last_snapshot_time) > EPSILON
        ):
            self._record_snapshot(self.processed_events)

        return SimulationResult(
            output_path=self.config.output.path,
            processed_events=self.processed_events,
            snapshots_written=self.snapshots_written,
            final_time=self.current_time,
            scanning_count=self.observables.scanning_count,
            center_contact_series=list(self.observables.center_contact_series),
            used_fraction_history=list(self.observables.used_fraction_history),
            radial_profiles=self.observables.export_radial_profiles(),
            radial_profile_samples=list(self.observables.radial_profile_samples),
            final_particles=[clone_particle(particle) for particle in self.particles],
        )

    def _schedule_initial_events(self) -> None:
        for index in range(len(self.particles)):
            self._schedule_boundary_events(index)
        for index in range(len(self.particles)):
            for other_index in range(index + 1, len(self.particles)):
                self._schedule_pair_event(index, other_index)

    def _schedule_events_for_touched(self, touched: set[int]) -> None:
        touched_sorted = sorted(touched)
        touched_set = set(touched_sorted)
        for index in touched_sorted:
            self._schedule_boundary_events(index)
            for other_index in range(index + 1, len(self.particles)):
                self._schedule_pair_event(index, other_index)
            for other_index in range(index):
                if other_index in touched_set:
                    continue
                self._schedule_pair_event(other_index, index)

    def _schedule_boundary_events(self, particle_index: int) -> None:
        particle = self.particles[particle_index]
        t_outer = predict_outer_wall_collision_time(particle, self.config.geometry)
        if math.isfinite(t_outer):
            self._push_event(
                Event(
                    time=self.current_time + t_outer,
                    sequence=self._next_sequence(),
                    kind=EventKind.OUTER_WALL,
                    particle_a=particle_index,
                    count_a=particle.collision_count,
                )
            )

        t_inner = predict_inner_obstacle_collision_time(particle, self.config.geometry)
        if math.isfinite(t_inner):
            self._push_event(
                Event(
                    time=self.current_time + t_inner,
                    sequence=self._next_sequence(),
                    kind=EventKind.INNER_OBSTACLE,
                    particle_a=particle_index,
                    count_a=particle.collision_count,
                )
            )

    def _schedule_pair_event(self, index_a: int, index_b: int) -> None:
        particle_a = self.particles[index_a]
        particle_b = self.particles[index_b]
        collision_time = predict_particle_collision_time(particle_a, particle_b)
        if not math.isfinite(collision_time):
            return
        self._push_event(
            Event(
                time=self.current_time + collision_time,
                sequence=self._next_sequence(),
                kind=EventKind.PARTICLE,
                particle_a=index_a,
                particle_b=index_b,
                count_a=particle_a.collision_count,
                count_b=particle_b.collision_count,
            )
        )

    def _process_event(self, event: Event) -> set[int]:
        touched: set[int] = set()
        if event.kind == EventKind.PARTICLE:
            resolve_particle_collision(
                self.particles[event.particle_a],
                self.particles[event.particle_b],
            )
            touched.update({event.particle_a, event.particle_b})
        elif event.kind == EventKind.OUTER_WALL:
            handle_boundary_collision(
                self.particles[event.particle_a],
                EventKind.OUTER_WALL,
                self.observables,
                self.current_time,
            )
            touched.add(event.particle_a)
        elif event.kind == EventKind.INNER_OBSTACLE:
            handle_boundary_collision(
                self.particles[event.particle_a],
                EventKind.INNER_OBSTACLE,
                self.observables,
                self.current_time,
            )
            touched.add(event.particle_a)

        if self.processed_events + 1 > self.config.max_events:
            raise RuntimeError("Maximum event budget reached before the simulation completed.")

        return touched

    def _record_snapshot(self, event_id: int) -> None:
        self.observables.record_snapshot(self.current_time, self.particles)
        if self.writer is not None:
            self.writer.write_step(event_id, self.current_time, self.particles)
        self.snapshots_written += 1
        self.last_snapshot_time = self.current_time
        self.last_snapshot_event_id = event_id

    def _push_event(self, event: Event) -> None:
        heapq.heappush(self._queue, event)

    def _pop_next_valid_event(self) -> Event | None:
        while self._queue:
            event = heapq.heappop(self._queue)
            if event.time + EPSILON < self.current_time:
                continue
            if not event.is_valid(self.particles):
                continue
            return event
        return None

    def _next_sequence(self) -> int:
        self._sequence += 1
        return self._sequence

    def _advance_all(self, dt: float) -> None:
        if abs(dt) <= EPSILON:
            return
        for particle in self.particles:
            particle.advance(dt)


def run_simulation(config: SimulationConfig, config_path: Path | None = None) -> SimulationResult:
    config.output.path.parent.mkdir(parents=True, exist_ok=True)
    with config.output.path.open("w", encoding="utf-8") as handle:
        engine = SimulationEngine(config, writer_handle=handle, config_path=config_path)
        engine.run_until(config.duration)
        return engine.finalize(force_final_snapshot=True)


def clone_particle(particle: Particle) -> Particle:
    return Particle(
        id=particle.id,
        x=particle.x,
        y=particle.y,
        vx=particle.vx,
        vy=particle.vy,
        radius=particle.radius,
        mass=particle.mass,
        state=particle.state,
        collision_count=particle.collision_count,
    )


def generate_initial_particles(config: SimulationConfig) -> list[Particle]:
    generator = random.Random(config.seed)
    try:
        return _generate_particles_random_rejection(config, generator)
    except ValueError:
        return _generate_particles_ring_seeded(config, generator)


def _generate_particles_random_rejection(config: SimulationConfig, generator: random.Random) -> list[Particle]:
    particles: list[Particle] = []
    inner = config.geometry.inner_travel_radius
    outer = config.geometry.outer_travel_radius
    max_attempts = max(2000, config.particles.count * 1500)

    for particle_id in range(config.particles.count):
        placed = False
        for _ in range(max_attempts):
            radius = math.sqrt(generator.uniform(inner * inner, outer * outer))
            angle = generator.uniform(0.0, 2.0 * math.pi)
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            if all(
                distance_between_xy(x, y, other.x, other.y) >= 2.0 * config.geometry.particle_radius - EPSILON
                for other in particles
            ):
                particles.append(_build_particle(config, generator, particle_id, x, y))
                placed = True
                break
        if not placed:
            raise ValueError("Random rejection initialization failed.")
    return particles


def _generate_particles_ring_seeded(config: SimulationConfig, generator: random.Random) -> list[Particle]:
    spacing = 2.05 * config.geometry.particle_radius
    inner = config.geometry.inner_travel_radius
    outer = config.geometry.outer_travel_radius
    span = outer - inner
    edge_margin = min(config.geometry.particle_radius * 0.05, span / 4.0)
    if edge_margin <= EPSILON:
        raise ValueError("Unable to place fallback initialization rings strictly inside the annulus.")
    candidate_positions: list[tuple[float, float]] = []
    ring_radius = inner + edge_margin
    max_ring_radius = outer - edge_margin

    while ring_radius <= max_ring_radius + EPSILON:
        circumference = 2.0 * math.pi * ring_radius
        slot_count = max(1, int(circumference / spacing))
        angle_offset = generator.uniform(0.0, 2.0 * math.pi)
        for slot in range(slot_count):
            angle = angle_offset + slot * (2.0 * math.pi / slot_count)
            candidate_positions.append((ring_radius * math.cos(angle), ring_radius * math.sin(angle)))
        ring_radius += spacing

    generator.shuffle(candidate_positions)
    if len(candidate_positions) < config.particles.count:
        raise ValueError("Unable to initialize the requested number of particles inside the annulus.")

    particles = [
        _build_particle(config, generator, particle_id, x, y)
        for particle_id, (x, y) in enumerate(candidate_positions[: config.particles.count])
    ]
    if has_any_overlap(particles):
        raise ValueError("Fallback initialization produced overlapping particles.")
    return particles


def _build_particle(
    config: SimulationConfig,
    generator: random.Random,
    particle_id: int,
    x: float,
    y: float,
) -> Particle:
    velocity_angle = generator.uniform(0.0, 2.0 * math.pi)
    return Particle(
        id=particle_id,
        x=x,
        y=y,
        vx=config.particles.speed * math.cos(velocity_angle),
        vy=config.particles.speed * math.sin(velocity_angle),
        radius=config.geometry.particle_radius,
        mass=config.particles.mass,
    )


def predict_particle_collision_time(particle_a: Particle, particle_b: Particle) -> float:
    dx = particle_b.x - particle_a.x
    dy = particle_b.y - particle_a.y
    dvx = particle_b.vx - particle_a.vx
    dvy = particle_b.vy - particle_a.vy
    dvdr = dx * dvx + dy * dvy
    if dvdr >= 0:
        return math.inf
    dvdv = dvx * dvx + dvy * dvy
    if dvdv <= EPSILON:
        return math.inf
    sigma = particle_a.radius + particle_b.radius
    drdr = dx * dx + dy * dy
    discriminant = dvdr * dvdr - dvdv * (drdr - sigma * sigma)
    if discriminant < 0:
        return math.inf
    collision_time = -(dvdr + math.sqrt(discriminant)) / dvdv
    if collision_time <= EPSILON:
        return math.inf
    return collision_time


def predict_outer_wall_collision_time(particle: Particle, geometry: Geometry) -> float:
    return predict_circle_collision_time(particle, geometry.outer_travel_radius, mode="outer")


def predict_inner_obstacle_collision_time(particle: Particle, geometry: Geometry) -> float:
    return predict_circle_collision_time(particle, geometry.inner_travel_radius, mode="inner")


def predict_circle_collision_time(particle: Particle, target_radius: float, mode: str) -> float:
    a = particle.vx * particle.vx + particle.vy * particle.vy
    if a <= EPSILON:
        return math.inf
    b = 2.0 * (particle.x * particle.vx + particle.y * particle.vy)
    c = particle.x * particle.x + particle.y * particle.y - target_radius * target_radius
    discriminant = b * b - 4.0 * a * c
    if discriminant < 0:
        return math.inf
    sqrt_discriminant = math.sqrt(discriminant)
    roots = sorted(((-b - sqrt_discriminant) / (2.0 * a), (-b + sqrt_discriminant) / (2.0 * a)))
    for root in roots:
        if root <= EPSILON:
            continue
        x = particle.x + particle.vx * root
        y = particle.y + particle.vy * root
        radial_velocity = x * particle.vx + y * particle.vy
        if mode == "outer" and radial_velocity > 0:
            return root
        if mode == "inner" and radial_velocity < 0:
            return root
    return math.inf


def resolve_particle_collision(particle_a: Particle, particle_b: Particle) -> None:
    dx = particle_b.x - particle_a.x
    dy = particle_b.y - particle_a.y
    distance = math.hypot(dx, dy)
    if distance <= EPSILON:
        raise ValueError("Particles overlap at collision resolution time.")
    dvx = particle_b.vx - particle_a.vx
    dvy = particle_b.vy - particle_a.vy
    dvdr = dx * dvx + dy * dvy
    impulse = 2.0 * particle_a.mass * particle_b.mass * dvdr / (
        (particle_a.mass + particle_b.mass) * distance
    )
    fx = impulse * dx / distance
    fy = impulse * dy / distance
    particle_a.vx += fx / particle_a.mass
    particle_a.vy += fy / particle_a.mass
    particle_b.vx -= fx / particle_b.mass
    particle_b.vy -= fy / particle_b.mass
    particle_a.collision_count += 1
    particle_b.collision_count += 1


def handle_boundary_collision(
    particle: Particle,
    kind: EventKind,
    observables: System1Observables,
    current_time: float,
) -> None:
    reflect_velocity(particle)
    was_fresh = particle.state == ParticleState.FRESH
    if kind == EventKind.INNER_OBSTACLE:
        observables.note_center_contact(current_time, was_fresh=was_fresh)
        particle.state = ParticleState.USED
    elif kind == EventKind.OUTER_WALL and particle.state == ParticleState.USED:
        particle.state = ParticleState.FRESH
    particle.collision_count += 1


def reflect_velocity(particle: Particle) -> None:
    distance = particle.distance_to_origin()
    if distance <= EPSILON:
        raise ValueError("Cannot reflect a particle located at the origin.")
    nx = particle.x / distance
    ny = particle.y / distance
    dot = particle.vx * nx + particle.vy * ny
    particle.vx -= 2.0 * dot * nx
    particle.vy -= 2.0 * dot * ny


def distance_between_xy(x1: float, y1: float, x2: float, y2: float) -> float:
    return math.hypot(x2 - x1, y2 - y1)


def has_any_overlap(particles: list[Particle]) -> bool:
    for index, particle in enumerate(particles):
        for other in particles[index + 1 :]:
            if distance_between_xy(particle.x, particle.y, other.x, other.y) < particle.radius + other.radius - 1e-6:
                return True
    return False
