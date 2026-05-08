from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tp3_sds.system1.model import Particle


class EventKind(str, Enum):
    PARTICLE = "particle"
    OUTER_WALL = "outer-wall"
    INNER_OBSTACLE = "inner-obstacle"
    STOP = "stop"


@dataclass(order=True)
class Event:
    time: float
    sequence: int
    kind: EventKind = field(compare=False)
    particle_a: int | None = field(compare=False, default=None)
    particle_b: int | None = field(compare=False, default=None)
    count_a: int | None = field(compare=False, default=None)
    count_b: int | None = field(compare=False, default=None)

    def is_valid(self, particles: list[Particle]) -> bool:
        if self.kind == EventKind.STOP:
            return True
        if self.particle_a is not None and particles[self.particle_a].collision_count != self.count_a:
            return False
        if self.particle_b is not None and particles[self.particle_b].collision_count != self.count_b:
            return False
        return True
