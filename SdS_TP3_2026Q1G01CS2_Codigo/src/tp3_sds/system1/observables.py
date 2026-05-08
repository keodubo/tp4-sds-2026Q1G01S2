from __future__ import annotations

import math
from dataclasses import dataclass

from tp3_sds.system1.model import Geometry, Particle, ParticleState


@dataclass(frozen=True)
class RadialProfileSnapshot:
    time: float
    densities: tuple[float, ...]
    normal_velocities: tuple[float, ...]
    valid_counts: tuple[int, ...]


@dataclass(frozen=True)
class RadialProfileBin:
    radius_start: float
    radius_end: float
    density: float
    normal_velocity: float
    inward_flux: float
    samples: int
    particle_samples: int


class System1Observables:
    def __init__(self, geometry: Geometry, radial_bin_width: float) -> None:
        self.geometry = geometry
        self.radial_bin_width = radial_bin_width
        span = geometry.outer_travel_radius - geometry.inner_travel_radius
        self.bin_count = max(1, math.ceil(span / radial_bin_width))
        self.center_contact_series: list[tuple[float, int]] = [(0.0, 0)]
        self.scanning_count = 0
        self.used_fraction_history: list[tuple[float, float]] = []
        self.radial_profile_samples: list[RadialProfileSnapshot] = []

    def note_center_contact(self, time: float, was_fresh: bool) -> None:
        if was_fresh:
            self.scanning_count += 1
            self.center_contact_series.append((time, self.scanning_count))

    def record_snapshot(self, time: float, particles: list[Particle]) -> None:
        used_fraction = sum(particle.state == ParticleState.USED for particle in particles) / len(particles) if particles else 0.0
        self.used_fraction_history.append((time, used_fraction))
        self.radial_profile_samples.append(
            compute_radial_profile_snapshot(
                geometry=self.geometry,
                bin_width=self.radial_bin_width,
                time=time,
                particles=particles,
            )
        )

    def export_radial_profiles(self, *, time_min: float = 0.0) -> list[RadialProfileBin]:
        return aggregate_radial_profile_snapshots(
            self.geometry,
            self.radial_bin_width,
            self.radial_profile_samples,
            time_min=time_min,
        )


def compute_radial_profile_snapshot(
    *,
    geometry: Geometry,
    bin_width: float,
    time: float,
    particles: list[Particle],
) -> RadialProfileSnapshot:
    span = geometry.outer_travel_radius - geometry.inner_travel_radius
    bin_count = max(1, math.ceil(span / bin_width))
    counts = [0 for _ in range(bin_count)]
    velocity_sums = [0.0 for _ in range(bin_count)]
    inner = geometry.inner_travel_radius
    outer = geometry.outer_travel_radius

    for particle in particles:
        if particle.state != ParticleState.FRESH:
            continue
        radius = particle.distance_to_origin()
        if radius < inner or radius > outer:
            continue
        radial_dot = particle.radial_velocity()
        if radial_dot >= 0:
            continue
        index = min(bin_count - 1, int((radius - inner) / bin_width))
        counts[index] += 1
        velocity_sums[index] += radial_dot / radius

    densities: list[float] = []
    normal_velocities: list[float] = []
    for index in range(bin_count):
        radius_start = inner + index * bin_width
        radius_end = min(outer, radius_start + bin_width)
        area = math.pi * (radius_end * radius_end - radius_start * radius_start)
        density = counts[index] / area if area > 0 else 0.0
        density = density if counts[index] else 0.0
        mean_velocity = velocity_sums[index] / counts[index] if counts[index] else 0.0
        densities.append(density)
        normal_velocities.append(mean_velocity)

    return RadialProfileSnapshot(
        time=time,
        densities=tuple(densities),
        normal_velocities=tuple(normal_velocities),
        valid_counts=tuple(counts),
    )


def aggregate_radial_profile_snapshots(
    geometry: Geometry,
    bin_width: float,
    samples: list[RadialProfileSnapshot],
    *,
    time_min: float = 0.0,
) -> list[RadialProfileBin]:
    selected = [sample for sample in samples if sample.time >= time_min]
    span = geometry.outer_travel_radius - geometry.inner_travel_radius
    bin_count = max(1, math.ceil(span / bin_width))
    inner = geometry.inner_travel_radius
    outer = geometry.outer_travel_radius

    if not selected:
        return [
            RadialProfileBin(
                radius_start=inner + index * bin_width,
                radius_end=min(outer, inner + (index + 1) * bin_width),
                density=0.0,
                normal_velocity=0.0,
                inward_flux=0.0,
                samples=0,
                particle_samples=0,
            )
            for index in range(bin_count)
        ]

    bins: list[RadialProfileBin] = []
    for index in range(bin_count):
        radius_start = inner + index * bin_width
        radius_end = min(outer, radius_start + bin_width)
        density_sum = sum(sample.densities[index] for sample in selected)
        density = density_sum / len(selected)

        velocity_weighted_sum = 0.0
        particle_samples = 0
        for sample in selected:
            valid_count = sample.valid_counts[index]
            if valid_count <= 0:
                continue
            velocity_weighted_sum += sample.normal_velocities[index] * valid_count
            particle_samples += valid_count
        normal_velocity = velocity_weighted_sum / particle_samples if particle_samples else 0.0

        bins.append(
            RadialProfileBin(
                radius_start=radius_start,
                radius_end=radius_end,
                density=density,
                normal_velocity=normal_velocity,
                inward_flux=density * abs(normal_velocity),
                samples=len(selected),
                particle_samples=particle_samples,
            )
        )
    return bins
