import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parent / "run_tp3_reference_sweep.py"
SPEC = importlib.util.spec_from_file_location("run_tp3_reference_sweep", MODULE_PATH)
run_tp3_reference_sweep = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = run_tp3_reference_sweep
SPEC.loader.exec_module(run_tp3_reference_sweep)


class RunTp3ReferenceSweepTest(unittest.TestCase):
    def test_default_sweep_matches_tp4_comparison_grid(self):
        settings = run_tp3_reference_sweep.SweepSettings(experiment_id="unit")

        runs = run_tp3_reference_sweep.build_run_specs(settings)

        self.assertEqual(25, len(runs))
        self.assertEqual((100, 250, 500, 750, 1000), settings.particle_counts)
        self.assertEqual(5, settings.seed_count)
        self.assertEqual((12345, 12346, 12347, 12348, 12349), settings.seeds)
        self.assertEqual(500.0, settings.final_time)
        self.assertEqual(0.0001, settings.comparison_dt)
        self.assertEqual(5000, settings.state_stride)
        self.assertEqual(0.5, settings.sample_dt)
        self.assertTrue(all(run.config_path.parts[0] == "outputs" for run in runs))

    def test_rejects_out_of_range_particle_count(self):
        with self.assertRaisesRegex(ValueError, "particle_counts must stay inside"):
            run_tp3_reference_sweep.SweepSettings(particle_counts=(99,))

    def test_rendered_toml_contains_reference_metadata_and_compatible_run_config(self):
        settings = run_tp3_reference_sweep.SweepSettings(experiment_id="unit", seed_count=1)
        run = run_tp3_reference_sweep.build_run_specs(settings)[0]

        rendered = run_tp3_reference_sweep.render_toml(run)

        self.assertIn('run_id = "tp3-n100-r00"', rendered)
        self.assertIn("comparison_dt = 0.0001", rendered)
        self.assertIn("sample_dt = 0.5", rendered)
        self.assertIn("duration = 500", rendered)
        self.assertIn("seed = 12345", rendered)
        self.assertIn("count = 100", rendered)
        self.assertIn('path = "../../raw/N_100/r_00/snapshot.txt"', rendered)
        self.assertIn("snapshot_every = 5000", rendered)
        self.assertIn("radial_bin_width = 0.2", rendered)


if __name__ == "__main__":
    unittest.main()
