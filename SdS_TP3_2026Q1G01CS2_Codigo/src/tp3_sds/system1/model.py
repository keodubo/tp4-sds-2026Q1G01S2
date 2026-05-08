from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum


class ParticleState(str, Enum):
    FRESH = "fresh"
    USED = "used"


@dataclass(frozen=True)
class Geometry:
    diameter: float
    obstacle_radius: float
    particle_radius: float

    @property
    def outer_radius(self) -> float:
        return self.diameter / 2.0

    @property
    def inner_travel_radius(self) -> float:
        return self.obstacle_radius + self.particle_radius

    @property
    def outer_travel_radius(self) -> float:
        return self.outer_radius - self.particle_radius


@dataclass
class Particle:
    id: int
    x: float
    y: float
    vx: float
    vy: float
    radius: float
    mass: float
    state: ParticleState = ParticleState.FRESH
    collision_count: int = field(default=0)

    def advance(self, dt: float) -> None:
        self.x += self.vx * dt
        self.y += self.vy * dt

    def speed(self) -> float:
        return math.hypot(self.vx, self.vy)

    def distance_to_origin(self) -> float:
        return math.hypot(self.x, self.y)

    def radial_velocity(self) -> float:
        return self.x * self.vx + self.y * self.vy
