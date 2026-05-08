import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from animate_system2 import (
    detect_state_coloring_support,
    load_system2_run,
    read_state_frames,
)


class AnimateSystem2Test(unittest.TestCase):
    def test_load_system2_run_reads_metadata_and_groups_particles_by_frame(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            input_dir = Path(temp_dir)
            write_metadata(input_dir / "metadata.json")
            write_states(
                input_dir / "states.csv",
                [
                    "step,t,particle_id,x,y,vx,vy",
                    "0,0.0,0,1.0,2.0,0.1,0.2",
                    "0,0.0,1,3.0,4.0,0.3,0.4",
                    "10,1.0,0,2.0,3.0,0.1,0.2",
                    "10,1.0,1,4.0,5.0,0.3,0.4",
                ],
            )

            run = load_system2_run(input_dir)

            self.assertEqual(40.0, run.metadata.outer_radius)
            self.assertEqual(1.0, run.metadata.obstacle_radius)
            self.assertEqual(1.0, run.metadata.particle_radius)
            self.assertEqual(2, run.metadata.particle_count)
            self.assertFalse(run.supports_state_coloring)
            self.assertEqual([0, 10], [frame.step for frame in run.frames])
            self.assertEqual([0, 1], [particle.particle_id for particle in run.frames[0].particles])
            self.assertEqual(4.0, run.frames[1].particles[1].x)

    def test_read_state_frames_rejects_missing_required_columns(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            states_path = Path(temp_dir) / "states.csv"
            write_states(
                states_path,
                [
                    "step,t,particle_id,x,y,vx",
                    "0,0.0,0,1.0,2.0,0.1",
                ],
            )

            with self.assertRaisesRegex(ValueError, "missing required columns.*vy"):
                read_state_frames(states_path)

    def test_detect_state_coloring_support_only_when_state_columns_are_exported(self):
        current_columns = ("step", "t", "particle_id", "x", "y", "vx", "vy")
        state_column = current_columns + ("state",)
        fresh_used_columns = current_columns + ("fresh", "used")

        self.assertFalse(detect_state_coloring_support(current_columns))
        self.assertTrue(detect_state_coloring_support(state_column))
        self.assertTrue(detect_state_coloring_support(fresh_used_columns))


def write_metadata(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "system": "system2",
                "run_id": "unit",
                "N": 2,
                "R": 40.0,
                "obstacle_radius": 1.0,
                "particle_radius": 1.0,
                "dt": 0.1,
                "steps": 10,
            }
        ),
        encoding="utf-8",
    )


def write_states(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
