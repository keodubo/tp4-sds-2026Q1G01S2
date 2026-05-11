import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "SdS_TP3_2026Q1G01CS2_Codigo" / "src"))

from animate_tp3 import (
    default_output_path,
    discover_snapshot_paths,
    event_time_deltas,
    load_tp3_snapshot_run,
    resolve_snapshot_path,
    select_frames,
)


class AnimateTp3Test(unittest.TestCase):
    def test_load_tp3_snapshot_run_reads_header_steps_and_particles(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            snapshot_path = Path(temp_dir) / "snapshot.txt"
            snapshot_path.write_text(
                "\n".join(
                    [
                        "# tp3-sds system1 output",
                        "duration = 10.000000",
                        "particle_count = 2",
                        "domain_diameter = 80.000000",
                        "obstacle_radius = 1.000000",
                        "particle_radius = 1.000000",
                        "snapshot_every = 1",
                        "fresh_color = 0,255,0",
                        "used_color = 148,0,211",
                        "---",
                        "step event_id=0 time=0.000000 n_used=0",
                        "particle id=0 x=3.000000 y=0.000000 vx=1.000000 vy=0.000000 state=fresh r=0 g=255 b=0",
                        "particle id=1 x=5.000000 y=0.000000 vx=-1.000000 vy=0.000000 state=fresh r=0 g=255 b=0",
                        "step event_id=1 time=1.500000 n_used=1",
                        "particle id=0 x=4.500000 y=0.000000 vx=-1.000000 vy=0.000000 state=used r=148 g=0 b=211",
                        "particle id=1 x=3.500000 y=0.000000 vx=1.000000 vy=0.000000 state=fresh r=0 g=255 b=0",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            run = load_tp3_snapshot_run(snapshot_path)

            self.assertEqual(40.0, run.outer_radius)
            self.assertEqual(1.0, run.obstacle_radius)
            self.assertEqual(1.0, run.particle_radius)
            self.assertEqual([0, 1], [frame.event_id for frame in run.frames])
            self.assertEqual("used", run.frames[1].particles[0].state)
            self.assertEqual("#9400d3", run.frames[1].particles[0].color)

    def test_event_time_deltas_are_measured_between_recorded_events(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            snapshot_path = Path(temp_dir) / "snapshot.txt"
            snapshot_path.write_text(
                "\n".join(
                    [
                        "# tp3-sds system1 output",
                        "duration = 10.000000",
                        "particle_count = 1",
                        "domain_diameter = 80.000000",
                        "obstacle_radius = 1.000000",
                        "particle_radius = 1.000000",
                        "snapshot_every = 1",
                        "fresh_color = 0,255,0",
                        "used_color = 148,0,211",
                        "---",
                        "step event_id=0 time=0.000000 n_used=0",
                        "particle id=0 x=3.000000 y=0.000000 vx=1.000000 vy=0.000000 state=fresh r=0 g=255 b=0",
                        "step event_id=3 time=2.000000 n_used=0",
                        "particle id=0 x=5.000000 y=0.000000 vx=1.000000 vy=0.000000 state=fresh r=0 g=255 b=0",
                        "step event_id=4 time=2.500000 n_used=0",
                        "particle id=0 x=5.500000 y=0.000000 vx=1.000000 vy=0.000000 state=fresh r=0 g=255 b=0",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            run = load_tp3_snapshot_run(snapshot_path)

            self.assertEqual((0.0, 2.0, 0.5), event_time_deltas(run.frames))

    def test_select_frames_keeps_event_snapshots_not_fixed_time_samples(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            snapshot_path = Path(temp_dir) / "snapshot.txt"
            snapshot_path.write_text(
                "\n".join(
                    [
                        "# tp3-sds system1 output",
                        "duration = 10.000000",
                        "particle_count = 1",
                        "domain_diameter = 80.000000",
                        "obstacle_radius = 1.000000",
                        "particle_radius = 1.000000",
                        "snapshot_every = 1",
                        "fresh_color = 0,255,0",
                        "used_color = 148,0,211",
                        "---",
                        "step event_id=0 time=0.000000 n_used=0",
                        "particle id=0 x=3.000000 y=0.000000 vx=1.000000 vy=0.000000 state=fresh r=0 g=255 b=0",
                        "step event_id=1 time=0.100000 n_used=0",
                        "particle id=0 x=3.100000 y=0.000000 vx=1.000000 vy=0.000000 state=fresh r=0 g=255 b=0",
                        "step event_id=7 time=3.000000 n_used=0",
                        "particle id=0 x=6.000000 y=0.000000 vx=1.000000 vy=0.000000 state=fresh r=0 g=255 b=0",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            run = load_tp3_snapshot_run(snapshot_path)

            selected = select_frames(run.frames, frame_stride=2, max_frames=None)

            self.assertEqual([0, 7], [frame.event_id for frame in selected])

    def test_resolve_snapshot_path_accepts_script_run_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "outputs" / "tp3-reference" / "tp3-final-grid" / "raw" / "N_100" / "r_00"
            run_dir.mkdir(parents=True)
            snapshot_path = run_dir / "snapshot.txt"
            snapshot_path.write_text("placeholder\n", encoding="utf-8")

            self.assertEqual(snapshot_path, resolve_snapshot_path(run_dir))

    def test_discover_snapshot_paths_finds_script_raw_grid(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            raw_root = Path(temp_dir) / "outputs" / "tp3-reference" / "tp3-final-grid" / "raw"
            expected = [
                raw_root / "N_100" / "r_00" / "snapshot.txt",
                raw_root / "N_250" / "r_01" / "snapshot.txt",
            ]
            for snapshot_path in reversed(expected):
                snapshot_path.parent.mkdir(parents=True)
                snapshot_path.write_text("placeholder\n", encoding="utf-8")

            self.assertEqual(expected, list(discover_snapshot_paths(raw_root)))

    def test_default_output_path_writes_animation_next_to_snapshot(self):
        snapshot_path = Path("outputs/tp3-reference/tp3-final-grid/raw/N_100/r_00/snapshot.txt")

        output_path = default_output_path(snapshot_path, "animation-preview.mp4")

        self.assertEqual(
            Path("outputs/tp3-reference/tp3-final-grid/raw/N_100/r_00/animation-preview.mp4"),
            output_path,
        )


if __name__ == "__main__":
    unittest.main()
