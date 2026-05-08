#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


REQUIRED_STATE_COLUMNS = ("step", "t", "particle_id", "x", "y", "vx", "vy")
STATE_COLOR_COLUMNS = ("state", "particle_state")


@dataclass(frozen=True)
class System2AnimationMetadata:
    run_id: str
    particle_count: int
    outer_radius: float
    obstacle_radius: float
    particle_radius: float
    dt: float
    steps: int


@dataclass(frozen=True)
class ParticleState:
    particle_id: int
    x: float
    y: float
    vx: float
    vy: float


@dataclass(frozen=True)
class AnimationFrame:
    step: int
    time: float
    particles: tuple[ParticleState, ...]


@dataclass(frozen=True)
class System2RunData:
    metadata: System2AnimationMetadata
    frames: tuple[AnimationFrame, ...]
    supports_state_coloring: bool


def load_system2_run(input_dir: Path) -> System2RunData:
    input_dir = Path(input_dir)
    metadata = load_metadata(input_dir / "metadata.json")
    frames, state_columns = read_state_frames_with_columns(input_dir / "states.csv")
    return System2RunData(
        metadata=metadata,
        frames=frames,
        supports_state_coloring=detect_state_coloring_support(state_columns),
    )


def load_metadata(path: Path) -> System2AnimationMetadata:
    if not path.exists():
        raise FileNotFoundError(f"metadata file not found: {path}")

    with path.open(encoding="utf-8") as metadata_file:
        raw_metadata = json.load(metadata_file)

    required_keys = ("N", "R", "obstacle_radius", "particle_radius", "dt", "steps")
    missing = [key for key in required_keys if key not in raw_metadata]
    if missing:
        raise ValueError("metadata.json missing required keys: " + ", ".join(missing))

    return System2AnimationMetadata(
        run_id=str(raw_metadata.get("run_id", path.parent.name)),
        particle_count=int(raw_metadata["N"]),
        outer_radius=float(raw_metadata["R"]),
        obstacle_radius=float(raw_metadata["obstacle_radius"]),
        particle_radius=float(raw_metadata["particle_radius"]),
        dt=float(raw_metadata["dt"]),
        steps=int(raw_metadata["steps"]),
    )


def read_state_frames(path: Path) -> tuple[AnimationFrame, ...]:
    frames, _ = read_state_frames_with_columns(path)
    return frames


def read_state_frames_with_columns(path: Path) -> tuple[tuple[AnimationFrame, ...], tuple[str, ...]]:
    if not path.exists():
        raise FileNotFoundError(f"states file not found: {path}")

    frames_by_step: dict[int, tuple[float, list[ParticleState]]] = {}
    with path.open(newline="", encoding="utf-8") as states_file:
        reader = csv.DictReader(states_file)
        fieldnames = tuple(reader.fieldnames or ())
        missing = [column for column in REQUIRED_STATE_COLUMNS if column not in fieldnames]
        if missing:
            raise ValueError("states.csv missing required columns: " + ", ".join(missing))

        for row_number, record in enumerate(reader, start=2):
            try:
                step = int(record["step"])
                time = float(record["t"])
                particle = ParticleState(
                    particle_id=int(record["particle_id"]),
                    x=float(record["x"]),
                    y=float(record["y"]),
                    vx=float(record["vx"]),
                    vy=float(record["vy"]),
                )
            except ValueError as exception:
                raise ValueError(f"invalid numeric value in states.csv row {row_number}") from exception

            if step not in frames_by_step:
                frames_by_step[step] = (time, [])
            frame_time, particles = frames_by_step[step]
            if abs(frame_time - time) > 1e-12:
                raise ValueError(f"states.csv has inconsistent t values for step {step}")
            particles.append(particle)

    if not frames_by_step:
        raise ValueError(f"states.csv has no data rows: {path}")

    frames = tuple(
        AnimationFrame(
            step=step,
            time=frame_time,
            particles=tuple(sorted(particles, key=lambda particle: particle.particle_id)),
        )
        for step, (frame_time, particles) in sorted(frames_by_step.items())
    )
    return frames, fieldnames


def detect_state_coloring_support(columns: Iterable[str]) -> bool:
    normalized = {column.strip().lower() for column in columns}
    return any(column in normalized for column in STATE_COLOR_COLUMNS) or {"fresh", "used"}.issubset(normalized)


def write_animation(
    run: System2RunData,
    output: Path,
    fps: int = 30,
    dpi: int = 160,
    frame_stride: int = 1,
    max_frames: int | None = None,
    overwrite: bool = False,
) -> Path:
    if fps <= 0:
        raise ValueError("fps must be positive")
    if dpi <= 0:
        raise ValueError("dpi must be positive")
    if frame_stride <= 0:
        raise ValueError("frame_stride must be positive")

    output = Path(output)
    if output.exists() and not overwrite:
        raise FileExistsError(f"output already exists, pass --overwrite to replace it: {output}")

    selected_frames = select_frames(run.frames, frame_stride=frame_stride, max_frames=max_frames)
    if not selected_frames:
        raise ValueError("no frames selected for animation")

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import animation
    from matplotlib.patches import Circle

    if output.suffix.lower() in {".mp4", ".m4v"} and not animation.writers.is_available("ffmpeg"):
        raise RuntimeError("Matplotlib ffmpeg writer is not available; install ffmpeg or choose a GIF output")

    metadata = run.metadata
    figure, axis = plt.subplots(figsize=(7.0, 7.0), constrained_layout=True)
    limit = metadata.outer_radius + metadata.particle_radius * 1.5
    axis.set_xlim(-limit, limit)
    axis.set_ylim(-limit, limit)
    axis.set_aspect("equal", adjustable="box")
    axis.set_xlabel("x [m]")
    axis.set_ylabel("y [m]")
    axis.set_title(f"System 2 - {metadata.run_id}")
    axis.grid(color="#d9dee7", linewidth=0.5, alpha=0.7)

    axis.add_patch(Circle((0.0, 0.0), metadata.outer_radius, fill=False, color="#222222", linewidth=1.3))
    axis.add_patch(
        Circle(
            (0.0, 0.0),
            metadata.obstacle_radius,
            facecolor="#2b2b2b",
            edgecolor="#111111",
            linewidth=1.0,
            zorder=3,
        )
    )

    first_frame = selected_frames[0]
    particle_size = scatter_size_for_particle_radius(axis, metadata.particle_radius)
    scatter = axis.scatter(
        [particle.x for particle in first_frame.particles],
        [particle.y for particle in first_frame.particles],
        s=particle_size,
        c="#2775d1",
        edgecolors="#0c2f57",
        linewidths=0.35,
        alpha=0.88,
        zorder=4,
    )
    time_text = axis.text(
        0.02,
        0.98,
        "",
        transform=axis.transAxes,
        ha="left",
        va="top",
        fontsize=10,
        color="#222222",
        bbox={"boxstyle": "round,pad=0.25", "facecolor": "white", "edgecolor": "#d0d4dc", "alpha": 0.9},
    )

    def update(frame_index: int):
        frame = selected_frames[frame_index]
        scatter.set_offsets([(particle.x, particle.y) for particle in frame.particles])
        time_text.set_text(f"step={frame.step}   t={frame.time:.6g} s   N={len(frame.particles)}")
        return scatter, time_text

    movie = animation.FuncAnimation(
        figure,
        update,
        frames=len(selected_frames),
        interval=1000.0 / fps,
        blit=False,
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    writer = writer_for_output(output, animation, fps)
    movie.save(output, writer=writer, dpi=dpi)
    plt.close(figure)
    return output


def select_frames(
    frames: Sequence[AnimationFrame],
    frame_stride: int,
    max_frames: int | None,
) -> tuple[AnimationFrame, ...]:
    selected = tuple(frames[::frame_stride])
    if max_frames is not None:
        if max_frames <= 0:
            raise ValueError("max_frames must be positive when provided")
        selected = selected[:max_frames]
    return selected


def scatter_size_for_particle_radius(axis, particle_radius: float) -> float:
    axis.figure.canvas.draw()
    bbox = axis.get_window_extent().transformed(axis.figure.dpi_scale_trans.inverted())
    x_min, x_max = axis.get_xlim()
    y_min, y_max = axis.get_ylim()
    points_per_data_x = bbox.width * 72.0 / abs(x_max - x_min)
    points_per_data_y = bbox.height * 72.0 / abs(y_max - y_min)
    diameter_points = 2.0 * particle_radius * min(points_per_data_x, points_per_data_y)
    return max(8.0, diameter_points * diameter_points)


def writer_for_output(output: Path, animation_module, fps: int):
    suffix = output.suffix.lower()
    if suffix in {".mp4", ".m4v"}:
        return animation_module.FFMpegWriter(fps=fps, metadata={"title": output.stem}, bitrate=2400)
    if suffix == ".gif":
        return animation_module.PillowWriter(fps=fps)
    raise ValueError("unsupported output extension. Use .mp4, .m4v, or .gif")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Animate System 2 particle positions from Java raw text outputs."
    )
    parser.add_argument("--input-dir", type=Path, required=True, help="Directory with metadata.json and states.csv")
    parser.add_argument("--output", type=Path, required=True, help="Output animation path (.mp4, .m4v, or .gif)")
    parser.add_argument("--fps", type=int, default=30, help="Animation frames per second")
    parser.add_argument("--dpi", type=int, default=160, help="Output render DPI")
    parser.add_argument("--frame-stride", type=int, default=1, help="Use every Nth written state frame")
    parser.add_argument("--max-frames", type=int, default=None, help="Optional cap for quick preview renders")
    parser.add_argument("--overwrite", action="store_true", help="Replace output if it already exists")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    run = load_system2_run(args.input_dir)
    if not run.supports_state_coloring:
        print(
            "states.csv does not export fresh/used state columns; "
            "rendering plain position/movement animation."
        )
    write_animation(
        run,
        args.output,
        fps=args.fps,
        dpi=args.dpi,
        frame_stride=args.frame_stride,
        max_frames=args.max_frames,
        overwrite=args.overwrite,
    )
    print(f"Wrote animation: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
