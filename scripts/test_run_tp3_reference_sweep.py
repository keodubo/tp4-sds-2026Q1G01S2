import importlib.util
import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


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

    def test_write_reference_artifacts_exports_observable_csvs(self):
        settings = run_tp3_reference_sweep.SweepSettings(experiment_id="unit", seed_count=1)
        with tempfile.TemporaryDirectory() as temp_dir:
            run = run_tp3_reference_sweep.RunSpec(
                settings=settings,
                particle_count=100,
                realization=0,
                seed=12345,
                config_path=Path("unused.toml"),
                output_dir=Path(temp_dir) / "raw" / "N_100" / "r_00",
            )
            result = SimpleNamespace(
                processed_events=12,
                snapshots_written=2,
                final_time=5.0,
                scanning_count=1,
                center_contact_series=[(0.0, 0), (1.25, 1)],
                used_fraction_history=[(0.0, 0.0), (1.25, 0.01)],
                radial_profile_samples=[
                    SimpleNamespace(
                        time=1.25,
                        densities=(0.5,),
                        normal_velocities=(-0.2,),
                        valid_counts=(3,),
                    )
                ],
                radial_profiles=[
                    SimpleNamespace(
                        radius_start=2.0,
                        radius_end=2.2,
                        density=0.5,
                        normal_velocity=-0.2,
                        inward_flux=0.1,
                        samples=1,
                        particle_samples=3,
                    )
                ],
            )

            run_tp3_reference_sweep.write_reference_artifacts(run, result, runtime_seconds=0.75)

            output_dir = run.output_dir
            metadata = json.loads((output_dir / "metadata.json").read_text(encoding="utf-8"))
            self.assertEqual("tp3-reference-v1", metadata["contract_version"])
            self.assertEqual(0.75, metadata["runtime_seconds"])
            self.assertEqual(1, metadata["scanning_count"])

            with (output_dir / "center_contacts.csv").open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual({"time": "1.25", "c_fc": "1"}, rows[-1])

            with (output_dir / "radial_profile_samples.csv").open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual("2", rows[0]["radius_start"])
            self.assertEqual("0.1", rows[0]["inward_flux"])


if __name__ == "__main__":
    unittest.main()
