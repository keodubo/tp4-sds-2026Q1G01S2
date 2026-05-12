#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TP3_SRC = PROJECT_ROOT / "SdS_TP3_2026Q1G01CS2_Codigo" / "src"
SNAPSHOT_FILE_NAME = "snapshot.txt"
DEFAULT_OUTPUT_NAME = "animation.mp4"
if str(TP3_SRC) not in sys.path:
    sys.path.insert(0, str(TP3_SRC))

from tp3_sds.system1.output import ParsedStep, parse_snapshot_output  # noqa: E402


@dataclass(frozen=True)
class Tp3ParticleFrame:
    particle_id: int
    x: float
    y: float
    vx: float
    vy: float
    state: str
    color: str


@dataclass(frozen=True)
class Tp3AnimationFrame:
    event_id: int
    time: float
    n_used: int
    particles: tuple[Tp3ParticleFrame, ...]


@dataclass(frozen=True)
class Tp3SnapshotRun:
    source_path: Path
    duration: float
    particle_count: int
    outer_radius: float
    obstacle_radius: float
    particle_radius: float
    snapshot_every: int
    frames: tuple[Tp3AnimationFrame, ...]


def resolve_snapshot_path(path: Path) -> Path:
    path = Path(path)
    if path.is_dir():
        path = path / SNAPSHOT_FILE_NAME
    if not path.exists():
        raise FileNotFoundError(f"TP3 snapshot file not found: {path}")
    if not path.is_file():
        raise ValueError(f"TP3 snapshot input is not a file: {path}")
    return path


def discover_snapshot_paths(root: Path) -> tuple[Path, ...]:
    root = Path(root)
    if root.is_file():
        return (resolve_snapshot_path(root),)

    direct_snapshot = root / SNAPSHOT_FILE_NAME
    if direct_snapshot.exists():
        return (resolve_snapshot_path(direct_snapshot),)

    snapshots = tuple(sorted(root.glob(f"N_*/r_*/{SNAPSHOT_FILE_NAME}")))
    if snapshots:
        return snapshots

    snapshots = tuple(sorted(root.rglob(SNAPSHOT_FILE_NAME)))
    if not snapshots:
        raise FileNotFoundError(f"No {SNAPSHOT_FILE_NAME} files found under {root}")
    return snapshots


def default_output_path(snapshot_path: Path, output_name: str = DEFAULT_OUTPUT_NAME) -> Path:
    output_name_path = Path(output_name)
    if output_name_path.is_absolute() or output_name_path.parent != Path("."):
        raise ValueError("output_name must be a file name, not a path")
    return Path(snapshot_path).parent / output_name_path


def load_tp3_snapshot_run(path: Path) -> Tp3SnapshotRun:
    path = resolve_snapshot_path(path)
    parsed = parse_snapshot_output(path)
    header = parsed.header
    return Tp3SnapshotRun(
        source_path=path,
        duration=header.duration,
        particle_count=header.particle_count,
        outer_radius=header.domain_diameter / 2.0,
        obstacle_radius=header.obstacle_radius,
        particle_radius=header.particle_radius,
        snapshot_every=header.snapshot_every,
        frames=tuple(convert_step(step) for step in parsed.steps),
    )


def convert_step(step: ParsedStep) -> Tp3AnimationFrame:
    return Tp3AnimationFrame(
        event_id=step.event_id,
        time=step.time,
        n_used=step.n_used,
        particles=tuple(
            Tp3ParticleFrame(
                particle_id=particle.id,
                x=particle.x,
                y=particle.y,
                vx=particle.vx,
                vy=particle.vy,
                state=particle.state,
                color=rgb_to_hex(particle.r, particle.g, particle.b),
            )
            for particle in sorted(step.particles, key=lambda item: item.id)
        ),
    )


def rgb_to_hex(red: int, green: int, blue: int) -> str:
    return f"#{red:02x}{green:02x}{blue:02x}"


def event_time_deltas(frames: Sequence[Tp3AnimationFrame]) -> tuple[float, ...]:
    deltas: list[float] = []
    previous_time: float | None = None
    for frame in frames:
        if previous_time is None:
            deltas.append(0.0)
        else:
            deltas.append(frame.time - previous_time)
        previous_time = frame.time
    return tuple(deltas)


def select_frames(
    frames: Sequence[Tp3AnimationFrame],
    frame_stride: int,
    max_frames: int | None,
) -> tuple[Tp3AnimationFrame, ...]:
    if frame_stride <= 0:
        raise ValueError("frame_stride must be positive")
    selected = tuple(frames[::frame_stride])
    if max_frames is not None:
        if max_frames <= 0:
            raise ValueError("max_frames must be positive when provided")
        selected = selected[:max_frames]
    return selected


def write_animation(
    run: Tp3SnapshotRun,
    output: Path,
    fps: int = 12,
    dpi: int = 160,
    frame_stride: int = 1,
    max_frames: int | None = None,
    overwrite: bool = False,
) -> Path:
    if fps <= 0:
        raise ValueError("fps must be positive")
    if dpi <= 0:
        raise ValueError("dpi must be positive")

    output = Path(output)
    if output.exists() and not overwrite:
        raise FileExistsError(f"output already exists, pass --overwrite to replace it: {output}")

    selected_frames = select_frames(run.frames, frame_stride=frame_stride, max_frames=max_frames)
    if not selected_frames:
        raise ValueError("no frames selected for animation")
    selected_deltas = event_time_deltas(selected_frames)

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import animation
    from matplotlib.patches import Circle

    if output.suffix.lower() in {".mp4", ".m4v"} and not animation.writers.is_available("ffmpeg"):
        raise RuntimeError("Matplotlib ffmpeg writer is not available; install ffmpeg or choose a GIF output")

    figure, axis = plt.subplots(figsize=(7.0, 7.0), constrained_layout=True)
    limit = run.outer_radius + run.particle_radius * 1.5
    axis.set_xlim(-limit, limit)
    axis.set_ylim(-limit, limit)
    axis.set_aspect("equal", adjustable="box")
    axis.set_xlabel("x [m]")
    axis.set_ylabel("y [m]")
    axis.set_title(f"TP3 - N={run.particle_count}")
    axis.grid(color="#d9dee7", linewidth=0.5, alpha=0.7)

    axis.add_patch(Circle((0.0, 0.0), run.outer_radius, fill=False, color="#222222", linewidth=1.3))
    axis.add_patch(
        Circle(
            (0.0, 0.0),
            run.obstacle_radius,
            facecolor="#2b2b2b",
            edgecolor="#111111",
            linewidth=1.0,
            zorder=3,
        )
    )

    first_frame = selected_frames[0]
    particle_size = scatter_size_for_particle_radius(axis, run.particle_radius)
    scatter = axis.scatter(
        [particle.x for particle in first_frame.particles],
        [particle.y for particle in first_frame.particles],
        s=particle_size,
        c=[particle.color for particle in first_frame.particles],
        edgecolors="#0c2f57",
        linewidths=0.35,
        alpha=0.9,
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
        scatter.set_color([particle.color for particle in frame.particles])
        time_text.set_text(
            f"event={frame.event_id}   t={frame.time:.6g} s   "
            f"dt_event={selected_deltas[frame_index]:.6g} s   usados={frame.n_used}/{run.particle_count}"
        )
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
        description="Animate TP3 System 1 event snapshots from snapshot.txt."
    )
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--input",
        type=Path,
        help="TP3 snapshot.txt path, or a run directory containing snapshot.txt",
    )
    input_group.add_argument(
        "--batch-root",
        type=Path,
        help="Root containing script outputs such as raw/N_100/r_00/snapshot.txt",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output animation path for --input. Defaults to animation.mp4 next to snapshot.txt",
    )
    parser.add_argument(
        "--output-name",
        default=DEFAULT_OUTPUT_NAME,
        help="Output file name for --batch-root, written next to each snapshot.txt",
    )
    parser.add_argument("--fps", type=int, default=12, help="Playback frames per second")
    parser.add_argument("--dpi", type=int, default=160, help="Output render DPI")
    parser.add_argument("--frame-stride", type=int, default=1, help="Use every Nth recorded event snapshot")
    parser.add_argument("--max-frames", type=int, default=None, help="Optional cap for quick preview renders")
    parser.add_argument("--overwrite", action="store_true", help="Replace output if it already exists")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    if args.input is not None:
        snapshot_path = resolve_snapshot_path(args.input)
        output = args.output or default_output_path(snapshot_path)
        render_one(snapshot_path, output, args)
        return 0

    snapshot_paths = discover_snapshot_paths(args.batch_root)
    for index, snapshot_path in enumerate(snapshot_paths, start=1):
        output = default_output_path(snapshot_path, args.output_name)
        print(f"[{index}/{len(snapshot_paths)}] {snapshot_path.parent}")
        render_one(snapshot_path, output, args)
    print(f"Wrote {len(snapshot_paths)} TP3 animations.")
    return 0


def render_one(snapshot_path: Path, output: Path, args: argparse.Namespace) -> None:
    run = load_tp3_snapshot_run(snapshot_path)
    write_animation(
        run,
        output,
        fps=args.fps,
        dpi=args.dpi,
        frame_stride=args.frame_stride,
        max_frames=args.max_frames,
        overwrite=args.overwrite,
    )
    print(f"Wrote TP3 animation: {output}")
    print(
        f"Rendered {len(select_frames(run.frames, args.frame_stride, args.max_frames))} "
        f"event snapshots from {snapshot_path}"
    )


if __name__ == "__main__":
    raise SystemExit(main())
