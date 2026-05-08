import math
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from analyze_system1 import (
    PhysicalParameters,
    TrajectoryRow,
    analytical_state,
    compute_ecm,
    write_position_figures,
)


class AnalyzeSystem1Test(unittest.TestCase):
    def test_default_initial_conditions_reduce_to_slide_36_position(self):
        params = PhysicalParameters(
            mass=70.0,
            spring_constant=10000.0,
            gamma=100.0,
            final_time=5.0,
            initial_position=1.0,
            initial_velocity=-100.0 / (2.0 * 70.0),
            dts=(0.01,),
        )
        beta = params.gamma / (2.0 * params.mass)
        omega = math.sqrt(params.spring_constant / params.mass - beta * beta)

        for time in (0.0, 0.25, 1.75):
            with self.subTest(time=time):
                state = analytical_state(time, params)
                slide_expression = math.exp(-beta * time) * math.cos(omega * time)
                self.assertAlmostEqual(slide_expression, state.position, places=14)

    def test_ecm_is_grouped_by_method_and_dt_and_normalized_by_row_count(self):
        params = PhysicalParameters(
            mass=70.0,
            spring_constant=10000.0,
            gamma=100.0,
            final_time=1.0,
            initial_position=1.0,
            initial_velocity=-100.0 / (2.0 * 70.0),
            dts=(0.01, 0.001),
        )

        rows = []
        offsets = {
            ("euler", 0.01): (1.0, 2.0, 3.0),
            ("euler", 0.001): (4.0, 5.0),
            ("gear5", 0.01): (2.0, 2.0),
        }
        for (method, dt), group_offsets in offsets.items():
            for index, offset in enumerate(group_offsets):
                time = index * dt
                analytical = analytical_state(time, params)
                rows.append(
                    TrajectoryRow(
                        method=method,
                        dt=dt,
                        time=time,
                        position=analytical.position + offset,
                        velocity=analytical.velocity,
                    )
                )

        ecm_by_key = {
            (row.method, row.dt): row.ecm
            for row in compute_ecm(rows, params)
        }

        self.assertAlmostEqual(14.0 / 3.0, ecm_by_key[("euler", 0.01)])
        self.assertAlmostEqual(41.0 / 2.0, ecm_by_key[("euler", 0.001)])
        self.assertAlmostEqual(4.0, ecm_by_key[("gear5", 0.01)])

    def test_position_figures_are_generated_for_requested_dts(self):
        params = PhysicalParameters(
            mass=70.0,
            spring_constant=10000.0,
            gamma=100.0,
            final_time=0.01,
            initial_position=1.0,
            initial_velocity=-100.0 / (2.0 * 70.0),
            dts=(0.01, 0.001),
        )
        rows = []
        for dt in params.dts:
            for method in ("euler", "gear5"):
                for index in range(2):
                    time = index * dt
                    analytical = analytical_state(time, params)
                    rows.append(
                        TrajectoryRow(
                            method=method,
                            dt=dt,
                            time=time,
                            position=analytical.position,
                            velocity=analytical.velocity,
                        )
                    )

        with tempfile.TemporaryDirectory() as temp_dir:
            generated = write_position_figures(Path(temp_dir), rows, params, (0.01, 0.001))

            self.assertEqual(
                ["system1_position_dt_0.001.png", "system1_position_dt_0.01.png"],
                sorted(path.name for path in generated),
            )
            for path in generated:
                self.assertTrue(path.exists())
                self.assertGreater(path.stat().st_size, 0)

    def test_position_figures_reject_missing_requested_dt(self):
        params = PhysicalParameters(
            mass=70.0,
            spring_constant=10000.0,
            gamma=100.0,
            final_time=0.01,
            initial_position=1.0,
            initial_velocity=-100.0 / (2.0 * 70.0),
            dts=(0.01,),
        )
        analytical = analytical_state(0.0, params)
        rows = [
            TrajectoryRow(
                method="euler",
                dt=0.01,
                time=0.0,
                position=analytical.position,
                velocity=analytical.velocity,
            )
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaisesRegex(ValueError, "0.001"):
                write_position_figures(Path(temp_dir), rows, params, (0.01, 0.001))


if __name__ == "__main__":
    unittest.main()
