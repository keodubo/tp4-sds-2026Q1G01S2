import math
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from analyze_system1 import (
    EcmRow,
    PhysicalParameters,
    TrajectoryRow,
    analytical_state,
    compute_ecm,
    rank_methods_at_smallest_dt,
    validate_ecm_grid,
    write_ecm_vs_dt_figure,
    write_manifest,
    write_method_ranking_summary,
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

    def test_ecm_grid_requires_every_method_for_every_default_dt(self):
        ecm_rows = phase6_ecm_rows()

        validate_ecm_grid(ecm_rows, (0.01, 0.001, 0.0001, 0.00001))

        incomplete_rows = [
            row
            for row in ecm_rows
            if not (row.method == "verlet" and math.isclose(row.dt, 0.00001))
        ]
        with self.assertRaisesRegex(ValueError, "verlet.*1e-05"):
            validate_ecm_grid(incomplete_rows, (0.01, 0.001, 0.0001, 0.00001))

    def test_method_ranking_uses_lowest_ecm_at_smallest_dt(self):
        ranking = rank_methods_at_smallest_dt(phase6_ecm_rows())

        self.assertEqual("gear5", ranking[0].method)
        self.assertEqual(0.00001, ranking[0].dt)
        self.assertEqual(["gear5", "beeman", "verlet", "euler"], [row.method for row in ranking])

    def test_ecm_vs_dt_figure_and_method_summary_are_generated(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            figure = write_ecm_vs_dt_figure(temp_path, phase6_ecm_rows(), (0.01, 0.001, 0.0001, 0.00001))
            summary = write_method_ranking_summary(temp_path / "system1_summary.md", phase6_ecm_rows())

            self.assertEqual("ecm_vs_dt.png", figure.name)
            self.assertTrue(figure.exists())
            self.assertGreater(figure.stat().st_size, 0)
            self.assertTrue(summary.exists())
            summary_text = summary.read_text(encoding="utf-8")
            self.assertIn("Best method at dt=1e-05: gear5", summary_text)
            self.assertIn("| gear5 | 1e-05 |", summary_text)

    def test_manifest_records_phase6_figure_and_summary(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            manifest = temp_path / "manifest.csv"
            write_manifest(
                manifest,
                temp_path / "system1.csv",
                temp_path / "system1_ecm.csv",
                figure_paths=(temp_path / "system1_figures" / "system1_position_dt_0.01.png",),
                ecm_vs_dt_figure_path=temp_path / "system1_figures" / "ecm_vs_dt.png",
                summary_path=temp_path / "system1_summary.md",
            )

            manifest_text = manifest.read_text(encoding="utf-8")
            self.assertIn("1,1.3,figure", manifest_text)
            self.assertIn("1,1.3,summary", manifest_text)


def phase6_ecm_rows() -> list[EcmRow]:
    dts = (0.01, 0.001, 0.0001, 0.00001)
    final_ecm = {
        "gear5": 1.0e-20,
        "beeman": 1.0e-14,
        "verlet": 2.0e-14,
        "euler": 1.0e-7,
    }
    rows = []
    for method, smallest_ecm in final_ecm.items():
        for index, dt in enumerate(dts):
            rows.append(
                EcmRow(
                    method=method,
                    dt=dt,
                    rows=int(5 / dt) + 1,
                    ecm=smallest_ecm * (10 ** (len(dts) - index - 1)),
                )
            )
    return rows


if __name__ == "__main__":
    unittest.main()
