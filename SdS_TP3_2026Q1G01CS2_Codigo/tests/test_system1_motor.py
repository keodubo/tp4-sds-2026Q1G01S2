import math
import unittest

from tp3_sds.system1.events import EventKind
from tp3_sds.system1.model import Geometry, Particle, ParticleState
from tp3_sds.system1.observables import System1Observables
from tp3_sds.system1.simulation import (
    handle_boundary_collision,
    predict_inner_obstacle_collision_time,
    predict_outer_wall_collision_time,
    predict_particle_collision_time,
    resolve_particle_collision,
)


class System1MotorTest(unittest.TestCase):
    def test_particle_collision_prediction_returns_delta_time_between_events(self):
        particle_a = Particle(id=0, x=0.0, y=0.0, vx=1.0, vy=0.0, radius=1.0, mass=1.0)
        particle_b = Particle(id=1, x=5.0, y=0.0, vx=-1.0, vy=0.0, radius=1.0, mass=1.0)

        self.assertTrue(math.isclose(predict_particle_collision_time(particle_a, particle_b), 1.5))

    def test_equal_mass_particle_collision_exchanges_normal_velocities(self):
        particle_a = Particle(id=0, x=0.0, y=0.0, vx=1.0, vy=0.0, radius=1.0, mass=1.0)
        particle_b = Particle(id=1, x=2.0, y=0.0, vx=-1.0, vy=0.0, radius=1.0, mass=1.0)

        resolve_particle_collision(particle_a, particle_b)

        self.assertTrue(math.isclose(particle_a.vx, -1.0))
        self.assertTrue(math.isclose(particle_b.vx, 1.0))

    def test_boundary_collision_predictions_return_delta_times_to_reachable_walls(self):
        geometry = Geometry(diameter=80.0, obstacle_radius=1.0, particle_radius=1.0)
        outer_bound = Particle(id=0, x=38.0, y=0.0, vx=1.0, vy=0.0, radius=1.0, mass=1.0)
        inner_bound = Particle(id=1, x=5.0, y=0.0, vx=-1.0, vy=0.0, radius=1.0, mass=1.0)

        self.assertTrue(math.isclose(predict_outer_wall_collision_time(outer_bound, geometry), 1.0))
        self.assertTrue(math.isclose(predict_inner_obstacle_collision_time(inner_bound, geometry), 3.0))

    def test_boundary_collisions_are_specular_and_update_fresh_used_state(self):
        geometry = Geometry(diameter=80.0, obstacle_radius=1.0, particle_radius=1.0)
        observables = System1Observables(geometry, radial_bin_width=0.2)
        inner_bound = Particle(
            id=0,
            x=2.0,
            y=0.0,
            vx=-1.0,
            vy=0.0,
            radius=1.0,
            mass=1.0,
            state=ParticleState.FRESH,
        )
        outer_bound = Particle(
            id=1,
            x=39.0,
            y=0.0,
            vx=1.0,
            vy=0.0,
            radius=1.0,
            mass=1.0,
            state=ParticleState.USED,
        )

        handle_boundary_collision(inner_bound, EventKind.INNER_OBSTACLE, observables, current_time=3.0)
        handle_boundary_collision(outer_bound, EventKind.OUTER_WALL, observables, current_time=4.0)

        self.assertEqual(ParticleState.USED, inner_bound.state)
        self.assertEqual(ParticleState.FRESH, outer_bound.state)
        self.assertTrue(math.isclose(inner_bound.vx, 1.0))
        self.assertTrue(math.isclose(outer_bound.vx, -1.0))
        self.assertEqual((3.0, 1), observables.center_contact_series[-1])


if __name__ == "__main__":
    unittest.main()
