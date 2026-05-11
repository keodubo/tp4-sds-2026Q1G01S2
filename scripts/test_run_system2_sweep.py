import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parent / "run_system2_sweep.py"
SPEC = importlib.util.spec_from_file_location("run_system2_sweep", MODULE_PATH)
run_system2_sweep = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = run_system2_sweep
SPEC.loader.exec_module(run_system2_sweep)


class RunSystem2SweepTest(unittest.TestCase):
    def test_default_sweep_matches_required_tp4_grid(self):
        settings = run_system2_sweep.SweepSettings(experiment_id="unit")

        runs = run_system2_sweep.build_run_specs(settings)

        self.assertEqual(75, len(runs))
        self.assertEqual((100, 250, 500, 750, 1000), settings.particle_counts)
        self.assertEqual((100.0, 1000.0, 10000.0), settings.stiffness_values)
        self.assertEqual(5, settings.seed_count)
        self.assertEqual(500.0, settings.final_time)
        self.assertEqual(0.0001, settings.dt)
        self.assertEqual(5_000_000, settings.steps)
        self.assertEqual((12345, 12346, 12347, 12348, 12349), settings.seeds)
        self.assertTrue(all(run.output_dir.parts[0] == "outputs" for run in runs))

    def test_rejects_more_than_five_seeds(self):
        with self.assertRaisesRegex(ValueError, "seed_count must be between 1 and 5"):
            run_system2_sweep.SweepSettings(seed_count=6)

    def test_rendered_toml_contains_strides_and_relative_output_dir(self):
        settings = run_system2_sweep.SweepSettings(experiment_id="unit", seed_count=1)
        run = run_system2_sweep.build_run_specs(settings)[0]

        rendered = run_system2_sweep.render_toml(run)

        self.assertIn('run_id = "system2-k100-n100-r00"', rendered)
        self.assertIn('output_dir = "../../../raw/k_100/N_100/r_00"', rendered)
        self.assertIn("count = 100", rendered)
        self.assertIn("k = 100.0", rendered)
        self.assertIn("dt = 0.0001", rendered)
        self.assertIn("steps = 5000000", rendered)
        self.assertIn("state_stride = 5000", rendered)
        self.assertIn("full_contact_stride = 5000", rendered)
        self.assertIn("boundary_force_stride = 5000", rendered)


if __name__ == "__main__":
    unittest.main()
