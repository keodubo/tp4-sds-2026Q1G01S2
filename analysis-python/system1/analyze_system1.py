#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class PhysicalParameters:
    mass: float
    spring_constant: float
    gamma: float
    final_time: float
    initial_position: float
    initial_velocity: float
    dts: tuple[float, ...]


@dataclass(frozen=True)
class AnalyticalState:
    time: float
    position: float
    velocity: float


@dataclass(frozen=True)
class TrajectoryRow:
    method: str
    dt: float
    time: float
    position: float
    velocity: float


@dataclass(frozen=True)
class EcmRow:
    method: str
    dt: float
    rows: int
    ecm: float


@dataclass
class EcmAccumulator:
    rows: int = 0
    squared_error_sum: float = 0.0


REQUIRED_SYSTEM1_METHODS = ("beeman", "euler", "gear5", "verlet")
ECM_PLOT_METHOD_ORDER = ("euler", "gear5", "verlet", "beeman")
ECM_PLOT_STYLES = {
    "euler": {"marker": "o", "linestyle": "-", "linewidth": 1.4, "zorder": 2},
    "gear5": {"marker": "s", "linestyle": "-", "linewidth": 1.4, "zorder": 2},
    "verlet": {"marker": "^", "linestyle": "-.", "linewidth": 1.4, "zorder": 3},
    "beeman": {
        "marker": "D",
        "linestyle": "--",
        "linewidth": 1.8,
        "markerfacecolor": "white",
        "markeredgewidth": 1.2,
        "zorder": 4,
    },
}
POSITION_PLOT_METHOD_ORDER = ("euler", "gear5", "verlet", "beeman")
POSITION_PLOT_STYLES = {
    "euler": {"marker": "o", "linestyle": "-", "color": "#1f77b4", "linewidth": 1.0},
    "gear5": {"marker": "s", "linestyle": "--", "color": "#ff7f0e", "linewidth": 1.0},
    "verlet": {"marker": "^", "linestyle": "-.", "color": "#2ca02c", "linewidth": 1.0},
    "beeman": {"marker": "x", "linestyle": ":", "color": "#9467bd", "linewidth": 1.2},
}


def analytical_state(time: float, params: PhysicalParameters) -> AnalyticalState:
    beta = params.gamma / (2.0 * params.mass)
    omega_squared = params.spring_constant / params.mass - beta * beta
    if omega_squared <= 0.0:
        raise ValueError("System 1 analytical solution expects an underdamped oscillator")

    omega = math.sqrt(omega_squared)
    a = params.initial_position
    b = (params.initial_velocity + beta * params.initial_position) / omega
    cos_term = math.cos(omega * time)
    sin_term = math.sin(omega * time)
    decay = math.exp(-beta * time)

    oscillatory_position = a * cos_term + b * sin_term
    oscillatory_velocity = -a * omega * sin_term + b * omega * cos_term
    position = decay * oscillatory_position
    velocity = decay * (oscillatory_velocity - beta * oscillatory_position)
    return AnalyticalState(time=time, position=position, velocity=velocity)


def compute_ecm(rows: Iterable[TrajectoryRow], params: PhysicalParameters) -> list[EcmRow]:
    grouped_errors: dict[tuple[str, float], EcmAccumulator] = defaultdict(EcmAccumulator)
    for row in rows:
        analytical = analytical_state(row.time, params)
        squared_error = (row.position - analytical.position) ** 2
        accumulator = grouped_errors[(row.method, row.dt)]
        accumulator.rows += 1
        accumulator.squared_error_sum += squared_error

    ecm_rows = [
        EcmRow(
            method=method,
            dt=dt,
            rows=accumulator.rows,
            ecm=accumulator.squared_error_sum / accumulator.rows,
        )
        for (method, dt), accumulator in grouped_errors.items()
    ]
    return sorted(ecm_rows, key=lambda row: (row.method, row.dt))


def read_trajectory_csv(path: Path) -> tuple[PhysicalParameters, list[TrajectoryRow]]:
    params = read_trajectory_metadata(path)
    rows = list(iter_trajectory_rows(path))
    if not rows:
        raise ValueError(f"trajectory CSV has no data rows: {path}")
    return params, rows


def read_trajectory_metadata(path: Path) -> PhysicalParameters:
    metadata: dict[str, str] = {}
    with path.open(newline="", encoding="utf-8") as input_file:
        for line in input_file:
            if line.startswith("#"):
                key, value = parse_metadata_line(line)
                metadata[key] = value
            elif line.strip():
                break

    return physical_parameters_from_metadata(metadata)


def iter_trajectory_rows(path: Path) -> Iterable[TrajectoryRow]:
    with path.open(newline="", encoding="utf-8") as input_file:
        records = csv.DictReader(line for line in input_file if not line.startswith("#"))
        for record in records:
            yield TrajectoryRow(
                method=record["method"],
                dt=float(record["dt"]),
                time=float(record["time"]),
                position=float(record["x"]),
                velocity=float(record["v"]),
            )


def analyze_trajectory_rows(
    path: Path,
    params: PhysicalParameters,
    figure_dts: tuple[float, ...] = (),
) -> tuple[list[EcmRow], list[TrajectoryRow]]:
    grouped_errors: dict[tuple[str, float], EcmAccumulator] = defaultdict(EcmAccumulator)
    figure_rows: list[TrajectoryRow] = []

    for row in iter_trajectory_rows(path):
        analytical = analytical_state(row.time, params)
        squared_error = (row.position - analytical.position) ** 2
        accumulator = grouped_errors[(row.method, row.dt)]
        accumulator.rows += 1
        accumulator.squared_error_sum += squared_error

        if matches_any_dt(row.dt, figure_dts):
            figure_rows.append(row)

    if not grouped_errors:
        raise ValueError(f"trajectory CSV has no data rows: {path}")

    ecm_rows = [
        EcmRow(
            method=method,
            dt=dt,
            rows=accumulator.rows,
            ecm=accumulator.squared_error_sum / accumulator.rows,
        )
        for (method, dt), accumulator in grouped_errors.items()
    ]
    return sorted(ecm_rows, key=lambda row: (row.method, row.dt)), figure_rows


def matches_any_dt(dt: float, requested_dts: tuple[float, ...]) -> bool:
    return any(math.isclose(dt, requested_dt, rel_tol=1e-12, abs_tol=1e-15) for requested_dt in requested_dts)


def parse_metadata_line(line: str) -> tuple[str, str]:
    stripped = line.removeprefix("#").strip()
    if "=" not in stripped:
        raise ValueError(f"invalid metadata line: {line.rstrip()}")
    key, value = stripped.split("=", 1)
    return key.strip(), value.strip()


def physical_parameters_from_metadata(metadata: dict[str, str]) -> PhysicalParameters:
    required = ("m", "k", "gamma", "tf", "x0", "v0", "dts")
    missing = [key for key in required if key not in metadata]
    if missing:
        raise ValueError("trajectory metadata missing required keys: " + ", ".join(missing))

    return PhysicalParameters(
        mass=float(metadata["m"]),
        spring_constant=float(metadata["k"]),
        gamma=float(metadata["gamma"]),
        final_time=float(metadata["tf"]),
        initial_position=float(metadata["x0"]),
        initial_velocity=float(metadata["v0"]),
        dts=tuple(float(value) for value in metadata["dts"].split(",") if value),
    )


def write_ecm_csv(path: Path, ecm_rows: Iterable[EcmRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=("method", "dt", "rows", "ecm"))
        writer.writeheader()
        for row in ecm_rows:
            writer.writerow(
                {
                    "method": row.method,
                    "dt": format_float(row.dt),
                    "rows": row.rows,
                    "ecm": format_float(row.ecm),
                }
            )


def write_position_figures(
    figures_dir: Path,
    rows: Iterable[TrajectoryRow],
    params: PhysicalParameters,
    figure_dts: tuple[float, ...],
) -> list[Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figures_dir.mkdir(parents=True, exist_ok=True)
    grouped_rows: dict[float, dict[str, list[TrajectoryRow]]] = {
        dt: defaultdict(list) for dt in figure_dts
    }
    matched_dts: set[float] = set()
    for row in rows:
        for requested_dt in figure_dts:
            if math.isclose(row.dt, requested_dt, rel_tol=1e-12, abs_tol=1e-15):
                grouped_rows[requested_dt][row.method].append(row)
                matched_dts.add(requested_dt)
                break

    missing_dts = [dt for dt in figure_dts if dt not in matched_dts]
    if missing_dts:
        raise ValueError(
            "requested figure dt values not found in trajectory CSV: "
            + ", ".join(format_float(dt) for dt in missing_dts)
        )

    generated: list[Path] = []
    for dt in sorted(figure_dts):
        rows_by_method = grouped_rows[dt]
        if not rows_by_method:
            continue

        times = sorted({row.time for method_rows in rows_by_method.values() for row in method_rows})
        analytical_positions = [analytical_state(time, params).position for time in times]

        fig, axis = plt.subplots(figsize=(9, 5))
        plot_position_curves(axis, times, analytical_positions, rows_by_method)
        axis.set_title(f"System 1 position comparison dt={format_float(dt)}")
        axis.set_xlabel("time (s)")
        axis.set_ylabel("x (m)")
        axis.grid(True, linestyle="--", alpha=0.35)
        axis.legend()
        fig.tight_layout()

        output_path = figures_dir / f"system1_position_dt_{format_float(dt)}.png"
        fig.savefig(output_path, dpi=150)
        plt.close(fig)
        generated.append(output_path)

        if math.isclose(dt, min(figure_dts), rel_tol=1e-12, abs_tol=1e-15):
            zoom_path = figures_dir / f"system1_position_dt_{format_float(dt)}_zoom.png"
            write_position_zoom_figure(zoom_path, times, analytical_positions, rows_by_method, dt)
            generated.append(zoom_path)

    return generated


def plot_position_curves(axis, times: list[float], analytical_positions: list[float], rows_by_method: dict[str, list[TrajectoryRow]]) -> None:
    axis.plot(times, analytical_positions, color="black", linewidth=1.8, linestyle="-", label="analytical")
    for method in POSITION_PLOT_METHOD_ORDER:
        if method not in rows_by_method:
            continue
        method_rows = sorted(rows_by_method[method], key=lambda row: row.time)
        style = dict(POSITION_PLOT_STYLES[method])
        if style["marker"] != "x":
            style["markerfacecolor"] = "white"
            style["markeredgewidth"] = 1.0
        axis.plot(
            [row.time for row in method_rows],
            [row.position for row in method_rows],
            label=method,
            markersize=4.0,
            markevery=marker_interval(len(method_rows)),
            **style,
        )


def marker_interval(series_length: int) -> int:
    return max(1, series_length // 45)


def write_position_zoom_figure(
    output_path: Path,
    times: list[float],
    analytical_positions: list[float],
    rows_by_method: dict[str, list[TrajectoryRow]],
    dt: float,
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axis = plt.subplots(figsize=(9, 5))
    plot_position_curves(axis, times, analytical_positions, rows_by_method)
    apply_zoom_window(axis, times, analytical_positions, rows_by_method)
    axis.set_title(f"System 1 position comparison dt={format_float(dt)} zoom")
    axis.set_xlabel("time (s)")
    axis.set_ylabel("x (m)")
    axis.grid(True, linestyle="--", alpha=0.35)
    axis.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def apply_zoom_window(axis, times: list[float], analytical_positions: list[float], rows_by_method: dict[str, list[TrajectoryRow]]) -> None:
    ordered_method_rows = [
        sorted(rows_by_method[method], key=lambda row: row.time)
        for method in POSITION_PLOT_METHOD_ORDER
        if method in rows_by_method
    ]
    if not times or not ordered_method_rows:
        return

    shared_length = min(len(times), len(analytical_positions), *(len(rows) for rows in ordered_method_rows))
    if shared_length == 0:
        return

    spreads = []
    for index in range(shared_length):
        values = [analytical_positions[index]]
        values.extend(method_rows[index].position for method_rows in ordered_method_rows)
        spreads.append(max(values) - min(values))

    center_index = max(range(shared_length), key=lambda index: spreads[index])
    window_size = min(shared_length, max(80, shared_length // 50))
    start = max(0, center_index - window_size // 2)
    end = min(shared_length, start + window_size)
    start = max(0, end - window_size)

    window_values = analytical_positions[start:end]
    for method_rows in ordered_method_rows:
        window_values.extend(row.position for row in method_rows[start:end])

    min_y = min(window_values)
    max_y = max(window_values)
    padding = max((max_y - min_y) * 0.20, 1e-12)
    axis.set_xlim(times[start], times[end - 1])
    axis.set_ylim(min_y - padding, max_y + padding)


def validate_ecm_grid(
    ecm_rows: Iterable[EcmRow],
    required_dts: tuple[float, ...],
    required_methods: tuple[str, ...] = REQUIRED_SYSTEM1_METHODS,
) -> None:
    rows = list(ecm_rows)
    missing = []
    for method in required_methods:
        for required_dt in required_dts:
            has_row = any(
                row.method == method
                and math.isclose(row.dt, required_dt, rel_tol=1e-12, abs_tol=1e-15)
                for row in rows
            )
            if not has_row:
                missing.append(f"{method}@dt={format_float(required_dt)}")

    if missing:
        raise ValueError(
            "ECM rows missing required method/dt combinations: " + ", ".join(missing)
        )


def rank_methods_at_smallest_dt(ecm_rows: Iterable[EcmRow]) -> list[EcmRow]:
    rows = list(ecm_rows)
    if not rows:
        raise ValueError("cannot rank methods without ECM rows")

    smallest_dt = min(row.dt for row in rows)
    ranking_rows = [
        row for row in rows if math.isclose(row.dt, smallest_dt, rel_tol=1e-12, abs_tol=1e-15)
    ]
    return sorted(ranking_rows, key=lambda row: (row.ecm, row.method))


def write_ecm_vs_dt_figure(
    figures_dir: Path,
    ecm_rows: Iterable[EcmRow],
    required_dts: tuple[float, ...],
) -> Path:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = list(ecm_rows)
    validate_ecm_grid(rows, required_dts)

    figures_dir.mkdir(parents=True, exist_ok=True)
    fig, axis = plt.subplots(figsize=(8, 5))
    for method in ECM_PLOT_METHOD_ORDER:
        method_rows = sorted(
            (row for row in rows if row.method == method),
            key=lambda row: row.dt,
        )
        axis.loglog(
            [row.dt for row in method_rows],
            [row.ecm for row in method_rows],
            label=method,
            **ECM_PLOT_STYLES[method],
        )

    axis.set_title("System 1 ECM vs dt")
    axis.set_xlabel("dt (s)")
    axis.set_ylabel("ECM")
    axis.grid(True, which="both", linestyle="--", alpha=0.35)
    axis.legend()
    fig.tight_layout()

    output_path = figures_dir / "ecm_vs_dt.png"
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path


def write_method_ranking_summary(path: Path, ecm_rows: Iterable[EcmRow]) -> Path:
    ranking = rank_methods_at_smallest_dt(ecm_rows)
    if not ranking:
        raise ValueError("cannot write ranking summary without ECM rows")

    best = ranking[0]
    lines = [
        "# System 1 Method Ranking",
        "",
        f"Best method at dt={format_float(best.dt)}: {best.method}",
        "",
        "| method | dt | rows | ECM |",
        "|---|---:|---:|---:|",
    ]
    for row in ranking:
        lines.append(
            f"| {row.method} | {format_float(row.dt)} | {row.rows} | {format_float(row.ecm)} |"
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_manifest(
    path: Path,
    trajectory_path: Path,
    ecm_path: Path,
    figure_paths: Iterable[Path] = (),
    ecm_vs_dt_figure_path: Path | None = None,
    summary_path: Path | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(
            output_file,
            fieldnames=("system", "inciso", "artifact_type", "path", "description"),
        )
        writer.writeheader()
        writer.writerow(
            {
                "system": "1",
                "inciso": "1.1",
                "artifact_type": "raw-trajectory",
                "path": normalize_output_path(trajectory_path),
                "description": "Raw Java trajectory CSV for System 1 numerical methods.",
            }
        )
        writer.writerow(
            {
                "system": "1",
                "inciso": "1.2",
                "artifact_type": "analysis-data",
                "path": normalize_output_path(ecm_path),
                "description": "ECM per integration method and dt computed from the raw trajectory CSV.",
            }
        )
        for figure_path in figure_paths:
            writer.writerow(
                {
                    "system": "1",
                    "inciso": "1.2",
                    "artifact_type": "figure",
                    "path": normalize_output_path(figure_path),
                    "description": "Analytical vs numerical position comparison for System 1.",
                }
            )
        if ecm_vs_dt_figure_path:
            writer.writerow(
                {
                    "system": "1",
                    "inciso": "1.3",
                    "artifact_type": "figure",
                    "path": normalize_output_path(ecm_vs_dt_figure_path),
                    "description": "Log-log ECM vs dt comparison for all System 1 integration methods.",
                }
            )
        if summary_path:
            writer.writerow(
                {
                    "system": "1",
                    "inciso": "1.3",
                    "artifact_type": "summary",
                    "path": normalize_output_path(summary_path),
                    "description": "Method ranking by lowest ECM at the smallest generated dt.",
                }
            )


def normalize_output_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path)


def format_float(value: float) -> str:
    return format(value, ".15g")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze TP4 System 1 raw trajectory CSV output.")
    parser.add_argument("--input", required=True, type=Path, help="Java-generated trajectory CSV.")
    parser.add_argument("--ecm-output", required=True, type=Path, help="CSV output for ECM by method and dt.")
    parser.add_argument(
        "--manifest-output",
        type=Path,
        help="Output manifest CSV. Defaults to system1_outputs_manifest.csv beside the ECM output.",
    )
    parser.add_argument("--figures-dir", type=Path, help="Optional directory for analytical-vs-numerical figures.")
    parser.add_argument(
        "--figure-dt",
        default="0.001",
        help="Comma-separated dt values to plot when --figures-dir is provided. Defaults to 0.001.",
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        help="Optional Markdown summary for the System 1 ECM-vs-dt method ranking.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest_output = args.manifest_output or args.ecm_output.parent / "system1_outputs_manifest.csv"

    figure_dts = tuple()
    if args.figures_dir:
        figure_dts = tuple(float(value.strip()) for value in args.figure_dt.split(",") if value.strip())

    params = read_trajectory_metadata(args.input)
    ecm_rows, figure_rows = analyze_trajectory_rows(args.input, params, figure_dts)
    write_ecm_csv(args.ecm_output, ecm_rows)
    figure_paths = []
    if args.figures_dir:
        figure_paths = write_position_figures(args.figures_dir, figure_rows, params, figure_dts)
    ecm_vs_dt_figure_path = None
    summary_path = None
    if args.summary_output:
        validate_ecm_grid(ecm_rows, params.dts)
        if args.figures_dir:
            ecm_vs_dt_figure_path = write_ecm_vs_dt_figure(args.figures_dir, ecm_rows, params.dts)
        summary_path = write_method_ranking_summary(args.summary_output, ecm_rows)
    write_manifest(
        manifest_output,
        args.input,
        args.ecm_output,
        figure_paths,
        ecm_vs_dt_figure_path=ecm_vs_dt_figure_path,
        summary_path=summary_path,
    )

    print(args.ecm_output)
    for figure_path in figure_paths:
        print(figure_path)
    if ecm_vs_dt_figure_path:
        print(ecm_vs_dt_figure_path)
    if summary_path:
        print(summary_path)
    print(manifest_output)


if __name__ == "__main__":
    main()
