#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


OBSTACLE_EVENT = "particle_obstacle_begin"
WALL_EVENT = "particle_wall_begin"
RADIAL_BIN_WIDTH = 0.2
NEAR_OBSTACLE_MIN = 1.5
NEAR_OBSTACLE_MAX = 5.0
LAYER_S_TARGET = 2.0
N_COLORS = {
    100: "#1f77b4",
    250: "#f2c94c",
    500: "#2ca02c",
    750: "#d62728",
    1000: "#9467bd",
}
K_LINE_STYLES = {
    100.0: "-",
    1000.0: "--",
    10000.0: ":",
}
K_LINE_COLORS = {
    100.0: "#ff7f0e",
    1000.0: "#17becf",
    10000.0: "#ff1493",
}
OBSERVABLE_COLORS = {
    "density": "#1f77b4",
    "normal_velocity": "#ff7f0e",
    "inward_flux": "#2ca02c",
}


@dataclass(frozen=True)
class Run:
    run_id: str
    k: float
    n: int
    realization: int
    output_dir: Path


@dataclass(frozen=True)
class ScanningRun:
    run: Run
    j: float
    c_final: int
    points: tuple[tuple[float, int], ...]


@dataclass(frozen=True)
class UsedToWallRun:
    run: Run
    particle_id: int | None
    t_obstacle: float | None
    t_wall: float | None
    delta_t: float | None


@dataclass(frozen=True)
class RadialProfile:
    k: float
    n: int
    realization: int
    radius_mid: float
    density: float
    normal_velocity: float
    inward_flux: float
    frames: int
    particle_samples: int


def color_for_n(n: int) -> str:
    return N_COLORS.get(int(n), "#7f7f7f")


def color_for_k(k: float) -> str:
    return K_LINE_COLORS.get(float(k), "#4d4d4d")


def read_manifest(path: Path) -> list[Run]:
    runs: list[Run] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            runs.append(
                Run(
                    run_id=row["run_id"],
                    k=float(row["k"]),
                    n=int(row["N"]),
                    realization=int(row["realization"]),
                    output_dir=Path(row["output_dir"]),
                )
            )
    return runs


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def compute_scanning_run(run: Run, root: Path) -> ScanningRun:
    events_path = root / run.output_dir / "contact_events.csv"
    metadata = load_json(root / run.output_dir / "metadata.json")
    tf = float(metadata["steps"]) * float(metadata["dt"])
    used: set[int] = set()
    points: list[tuple[float, int]] = [(0.0, 0)]
    count = 0
    with events_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            event_type = row["event_type"]
            particle_id = int(row["particle_id"])
            if event_type == OBSTACLE_EVENT:
                if particle_id not in used:
                    used.add(particle_id)
                    count += 1
                    points.append((float(row["t"]), count))
            elif event_type == WALL_EVENT:
                used.discard(particle_id)
    if points[-1][0] < tf:
        points.append((tf, count))
    j = linear_slope(points)
    return ScanningRun(run=run, j=j, c_final=count, points=tuple(points))


def linear_slope(points: Sequence[tuple[float, int]]) -> float:
    if len(points) < 2:
        return 0.0
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    x_mean = sum(xs) / len(xs)
    y_mean = sum(ys) / len(ys)
    denom = sum((x - x_mean) ** 2 for x in xs)
    if denom == 0.0:
        return 0.0
    return sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)) / denom


def summarize_scanning(scanning_runs: Sequence[ScanningRun]) -> list[dict[str, float]]:
    grouped: dict[tuple[float, int], list[float]] = defaultdict(list)
    for item in scanning_runs:
        grouped[(item.run.k, item.run.n)].append(item.j)
    rows: list[dict[str, float]] = []
    for (k, n), values in sorted(grouped.items()):
        mean = sum(values) / len(values)
        std = sample_std(values)
        rows.append({"k": k, "N": n, "J_mean": mean, "J_std": std, "realizations": len(values)})
    return rows


def compute_used_to_wall_run(run: Run, root: Path) -> UsedToWallRun:
    events_path = root / run.output_dir / "contact_events.csv"
    first_obstacle_by_particle: dict[int, float] = {}
    best_particle_id: int | None = None
    best_t_obstacle: float | None = None
    best_t_wall: float | None = None
    best_delta: float | None = None
    with events_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            particle_id = int(row["particle_id"])
            event_type = row["event_type"]
            time = float(row["t"])
            if event_type == OBSTACLE_EVENT and particle_id not in first_obstacle_by_particle:
                first_obstacle_by_particle[particle_id] = time
            elif event_type == WALL_EVENT and particle_id in first_obstacle_by_particle:
                delta = time - first_obstacle_by_particle[particle_id]
                if delta >= 0 and (best_delta is None or delta < best_delta):
                    best_particle_id = particle_id
                    best_t_obstacle = first_obstacle_by_particle[particle_id]
                    best_t_wall = time
                    best_delta = delta
    return UsedToWallRun(
        run=run,
        particle_id=best_particle_id,
        t_obstacle=best_t_obstacle,
        t_wall=best_t_wall,
        delta_t=best_delta,
    )


def summarize_used_to_wall(rows: Sequence[UsedToWallRun]) -> list[dict[str, float]]:
    grouped: dict[tuple[float, int], list[float]] = defaultdict(list)
    for row in rows:
        if row.delta_t is not None:
            grouped[(row.run.k, row.run.n)].append(row.delta_t)
    summary: list[dict[str, float]] = []
    for (k, n), values in sorted(grouped.items()):
        summary.append(
            {
                "k": k,
                "N": n,
                "used_to_wall_time_mean": mean(values),
                "used_to_wall_time_std": sample_std(values),
                "realizations_with_arrival": len(values),
            }
        )
    return summary


def sample_std(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    return math.sqrt(sum((value - mean) ** 2 for value in values) / (len(values) - 1))


def load_tp3_scanning(root: Path, manifest_path: Path) -> list[dict[str, float]]:
    if not manifest_path.exists():
        return []
    grouped: dict[int, list[float]] = defaultdict(list)
    with manifest_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            center_path = root / row["output_dir"] / "center_contacts.csv"
            if not center_path.exists():
                continue
            points: list[tuple[float, int]] = []
            with center_path.open(newline="", encoding="utf-8") as center_file:
                for contact_row in csv.DictReader(center_file):
                    points.append((float(contact_row["time"]), int(contact_row["c_fc"])))
            grouped[int(row["N"])].append(linear_slope(points))
    rows: list[dict[str, float]] = []
    for n, values in sorted(grouped.items()):
        rows.append({"N": n, "J_mean": sum(values) / len(values), "J_std": sample_std(values), "realizations": len(values)})
    return rows


def load_tp3_radial(root: Path, manifest_path: Path) -> list[dict[str, float]]:
    if not manifest_path.exists():
        return []
    rows: list[dict[str, float]] = []
    with manifest_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            path = root / row["output_dir"] / "radial_profiles.csv"
            if not path.exists():
                continue
            n = int(row["N"])
            realization = int(row["realization"])
            with path.open(newline="", encoding="utf-8") as radial_file:
                for profile_row in csv.DictReader(radial_file):
                    radius_mid = (float(profile_row["radius_start"]) + float(profile_row["radius_end"])) / 2.0
                    rows.append(
                        {
                            "N": n,
                            "realization": realization,
                            "radius_mid": radius_mid,
                            "density": float(profile_row["density"]),
                            "normal_velocity": float(profile_row["normal_velocity"]),
                            "inward_flux": float(profile_row["inward_flux"]),
                        }
                    )
    return rows


def load_tp3_runtime(root: Path, manifest_path: Path) -> list[dict[str, float]]:
    if not manifest_path.exists():
        return []
    rows: list[dict[str, float]] = []
    with manifest_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            metadata_path = root / row["output_dir"] / "metadata.json"
            if not metadata_path.exists():
                continue
            metadata = load_json(metadata_path)
            if "runtime_seconds" not in metadata:
                continue
            rows.append(
                {
                    "run_id": row["run_id"],
                    "N": int(row["N"]),
                    "realization": int(row["realization"]),
                    "runtime_seconds": float(metadata["runtime_seconds"]),
                }
            )
    return rows


def compute_radial_profiles(runs: Sequence[Run], root: Path) -> list[RadialProfile]:
    return [profile for run in runs for profile in compute_radial_profile_for_run(run, root)]


def compute_radial_profile_for_run(run: Run, root: Path) -> list[RadialProfile]:
    run_dir = root / run.output_dir
    metadata = load_json(run_dir / "metadata.json")
    outer_radius = float(metadata["R"])
    particle_radius = float(metadata["particle_radius"])
    min_radius = float(metadata["obstacle_radius"]) + particle_radius
    max_radius = outer_radius - particle_radius
    bins = build_bins(min_radius, max_radius, RADIAL_BIN_WIDTH)
    density_sum = [0.0 for _ in bins]
    velocity_sum = [0.0 for _ in bins]
    particle_counts = [0 for _ in bins]
    frame_count = 0
    event_map = read_events_by_step(run_dir / "contact_events.csv")
    used: set[int] = set()
    with (run_dir / "states.csv").open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        current_step: int | None = None
        frame_rows: list[dict[str, str]] = []
        for row in reader:
            step = int(row["step"])
            if current_step is None:
                current_step = step
            if step != current_step:
                apply_events_until(current_step, event_map, used)
                accumulate_radial_frame(frame_rows, used, bins, density_sum, velocity_sum, particle_counts)
                frame_count += 1
                frame_rows = []
                current_step = step
            frame_rows.append(row)
        if current_step is not None:
            apply_events_until(current_step, event_map, used)
            accumulate_radial_frame(frame_rows, used, bins, density_sum, velocity_sum, particle_counts)
            frame_count += 1
    profiles: list[RadialProfile] = []
    for index, (start, end) in enumerate(bins):
        area = math.pi * (end * end - start * start)
        density = density_sum[index] / frame_count / area if frame_count else 0.0
        velocity = velocity_sum[index] / particle_counts[index] if particle_counts[index] else 0.0
        profiles.append(
            RadialProfile(
                k=run.k,
                n=run.n,
                realization=run.realization,
                radius_mid=(start + end) / 2.0,
                density=density,
                normal_velocity=velocity,
                inward_flux=density * abs(velocity),
                frames=frame_count,
                particle_samples=particle_counts[index],
            )
        )
    return profiles


def build_bins(min_radius: float, max_radius: float, width: float) -> list[tuple[float, float]]:
    bins: list[tuple[float, float]] = []
    start = min_radius
    while start + width <= max_radius + 1e-9:
        bins.append((start, start + width))
        start += width
    return bins


def read_events_by_step(path: Path) -> dict[int, list[tuple[str, int]]]:
    events: dict[int, list[tuple[str, int]]] = defaultdict(list)
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["event_type"] in {OBSTACLE_EVENT, WALL_EVENT}:
                events[int(row["step"])].append((row["event_type"], int(row["particle_id"])))
    return dict(sorted(events.items()))


def apply_events_until(step: int, event_map: dict[int, list[tuple[str, int]]], used: set[int]) -> None:
    for event_step in [candidate for candidate in event_map.keys() if candidate <= step]:
        for event_type, particle_id in event_map.pop(event_step):
            if event_type == OBSTACLE_EVENT:
                used.add(particle_id)
            elif event_type == WALL_EVENT:
                used.discard(particle_id)


def accumulate_radial_frame(
    frame_rows: Sequence[dict[str, str]],
    used: set[int],
    bins: Sequence[tuple[float, float]],
    density_sum: list[float],
    velocity_sum: list[float],
    particle_counts: list[int],
) -> None:
    for row in frame_rows:
        particle_id = int(row["particle_id"])
        if particle_id in used:
            continue
        x = float(row["x"])
        y = float(row["y"])
        vx = float(row["vx"])
        vy = float(row["vy"])
        radius = math.hypot(x, y)
        if radius <= 0:
            continue
        radial_velocity = (x * vx + y * vy) / radius
        if radial_velocity >= 0:
            continue
        index = int((radius - bins[0][0]) / RADIAL_BIN_WIDTH)
        if 0 <= index < len(bins) and bins[index][0] <= radius < bins[index][1]:
            density_sum[index] += 1.0
            velocity_sum[index] += radial_velocity
            particle_counts[index] += 1


def compute_energy_sample(run: Run, root: Path, max_rows: int = 250) -> list[dict[str, float]]:
    run_dir = root / run.output_dir
    metadata = load_json(run_dir / "metadata.json")
    k = float(metadata["k"])
    potential_by_step: dict[int, float] = defaultdict(float)
    with (run_dir / "contacts.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            potential_by_step[int(row["step"])] += 0.5 * k * float(row["overlap"]) ** 2
    kinetic_by_step: dict[int, tuple[float, float]] = defaultdict(lambda: (0.0, 0.0))
    with (run_dir / "states.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            step = int(row["step"])
            kinetic, time = kinetic_by_step[step]
            vx = float(row["vx"])
            vy = float(row["vy"])
            kinetic_by_step[step] = (kinetic + 0.5 * (vx * vx + vy * vy), float(row["t"]))
    rows: list[dict[str, float]] = []
    for step in sorted(kinetic_by_step.keys()):
        kinetic, time = kinetic_by_step[step]
        potential = potential_by_step.get(step, 0.0)
        rows.append({"k": run.k, "N": run.n, "realization": run.realization, "step": step, "t": time, "kinetic": kinetic, "potential": potential, "total": kinetic + potential})
    initial_energy = rows[0]["total"] if rows else 0.0
    for row in rows:
        row["relative_energy_delta"] = ((row["total"] - initial_energy) / initial_energy) if initial_energy else 0.0
    stride = max(1, len(rows) // max_rows)
    return rows[::stride]


def parse_runtime_log(path: Path) -> list[dict[str, float]]:
    if not path.exists():
        return []
    rows: list[dict[str, float]] = []
    current_run_id: str | None = None
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        match = re.search(r"Run id: (system2-k(?P<k>\d+)-n(?P<n>\d+)-r(?P<r>\d+))", line)
        if match:
            current_run_id = match.group(1)
            current = (float(match.group("k")), int(match.group("n")), int(match.group("r")))
            continue
        time_match = re.search(r"Total time:\s+([0-9:.]+)\s*(min|s)?", line)
        if current_run_id and time_match:
            seconds = parse_maven_time_seconds(time_match.group(1), time_match.group(2) or "s")
            rows.append({"run_id": current_run_id, "k": current[0], "N": current[1], "realization": current[2], "runtime_seconds": seconds})
            current_run_id = None
    return rows


def load_system2_runtime_rows(system2_root: Path) -> list[dict[str, float]]:
    by_run_id: dict[str, dict[str, float]] = {}
    for log_path in sorted(system2_root.glob("local-run-*.log")):
        for row in parse_runtime_log(log_path):
            by_run_id[str(row["run_id"])] = row
    return sorted(by_run_id.values(), key=lambda row: (row["k"], row["N"], row["realization"]))


def parse_maven_time_seconds(value: str, unit: str) -> float:
    if ":" in value:
        minutes, seconds = value.split(":", 1)
        return float(minutes) * 60.0 + float(seconds)
    seconds = float(value)
    return seconds * 60.0 if unit == "min" else seconds


def write_csv(path: Path, rows: Sequence[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def plot_all(
    scanning_runs: Sequence[ScanningRun],
    scanning_summary: Sequence[dict[str, float]],
    radial_profiles: Sequence[RadialProfile],
    used_to_wall_summary: Sequence[dict[str, float]],
    tp3_scanning: Sequence[dict[str, float]],
    tp3_radial: Sequence[dict[str, float]],
    system2_layer_rows: Sequence[dict[str, float]],
    tp3_layer_rows: Sequence[dict[str, float]],
    tp3_runtime: Sequence[dict[str, float]],
    runtime_rows: Sequence[dict[str, float]],
    energy_rows: Sequence[dict[str, float]],
    figures_dir: Path,
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import Normalize
    from matplotlib.cm import ScalarMappable

    figures_dir.mkdir(parents=True, exist_ok=True)
    plot_cfc(scanning_runs, figures_dir / "system2_cfc_t_representative.png", plt)
    plot_scanning_rate(scanning_summary, tp3_scanning, figures_dir / "system2_scanning_rate_vs_n_tp3.png", plt)
    plot_radial_curves(radial_profiles, "density", "Densidad de particulas frescas [1/m^2]", figures_dir / "system2_radial_density_profiles.png", plt, Normalize, ScalarMappable)
    plot_radial_curves(radial_profiles, "normal_velocity", "Velocidad radial media fresca |<v_fin>(S)| [m/s]", figures_dir / "system2_radial_velocity_profiles.png", plt, Normalize, ScalarMappable)
    plot_radial_curves(radial_profiles, "inward_flux", "Flujo entrante Jin(S) [1/(m s)]", figures_dir / "system2_radial_inward_flux_profiles.png", plt, Normalize, ScalarMappable)
    plot_radial_curves(radial_profiles, "inward_flux", "Flujo entrante Jin(S) [1/(m s)]", figures_dir / "system2_radial_inward_flux_zoom_obstacle.png", plt, Normalize, ScalarMappable, xlim=(1.5, 5.0))
    plot_near_obstacle(radial_profiles, tp3_radial, figures_dir / "system2_near_obstacle_vs_n_tp3.png", plt)
    plot_layer_s2_by_k(system2_layer_rows, figures_dir / "system2_layer_s2_observables_vs_n.png", plt)
    if tp3_layer_rows:
        plot_layer_s2_triptych(tp3_layer_rows, figures_dir / "tp3_layer_s2_observables_vs_n.png", plt)
    plot_k_comparison(scanning_summary, radial_profiles, tp3_scanning, tp3_radial, figures_dir / "system2_k_comparison_j_and_jin.png", plt)
    plot_k_scalars(scanning_summary, radial_profiles, figures_dir / "system2_k_scalars.png", plt)
    if used_to_wall_summary:
        plot_used_to_wall(used_to_wall_summary, figures_dir / "system2_optional_1_5_used_to_wall_time_vs_n.png", plt)
    if runtime_rows or tp3_runtime:
        plot_runtime(runtime_rows, tp3_runtime, figures_dir / "system2_runtime_vs_n_tp3.png", plt)
    if energy_rows:
        plot_energy(energy_rows, figures_dir / "system2_energy_validation_representative.png", plt)


def plot_cfc(scanning_runs, path, plt) -> None:
    fig, ax = plt.subplots(figsize=(8, 5), constrained_layout=True)
    for item in scanning_runs:
        if item.run.realization == 0 and item.run.k == 1000.0:
            xs = [point[0] for point in item.points]
            ys = [point[1] for point in item.points]
            ax.step(xs, ys, where="post", color=color_for_n(item.run.n), label=f"N={item.run.n}")
    ax.set_xlabel("Tiempo [s]")
    ax.set_ylabel("Cfc(t)")
    ax.set_title(f"Sistema 2: Cfc(t), k={format_k(1000.0)} N/m, realizacion 0")
    ax.legend(title="N", ncol=2)
    ax.grid(alpha=0.3)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_scanning_rate(summary, tp3, path, plt) -> None:
    fig, ax = plt.subplots(figsize=(8, 5), constrained_layout=True)
    for k in sorted({row["k"] for row in summary}):
        rows = [row for row in summary if row["k"] == k]
        plot_n_summary(
            ax,
            rows,
            "J_mean",
            "J_std",
            line_color=color_for_k(k),
            linestyle=K_LINE_STYLES.get(k, "-"),
            marker="o",
            label=f"TP4 k={format_k(k)} N/m",
        )
    if tp3:
        plot_n_summary(ax, tp3, "J_mean", "J_std", line_color="black", linestyle="-.", marker="s", label="TP3")
    ax.set_xlabel("N")
    ax.set_ylabel("<J> [1/s]")
    ax.set_title("Scanning rate promedio en funcion de N: TP4 vs TP3")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_radial_curves(profiles, attr, ylabel, path, plt, Normalize, ScalarMappable, xlim=None) -> None:
    for k in sorted({profile.k for profile in profiles}):
        fig, ax = plt.subplots(figsize=(8, 5), constrained_layout=True)
        ns = sorted({profile.n for profile in profiles})
        visible_means: list[float] = []
        for n in ns:
            rows = radial_mean_std_by_radius([profile for profile in profiles if profile.k == k and profile.n == n], attr)
            xs = [row["radius_mid"] for row in rows]
            ys = [row["mean"] for row in rows]
            err = [row["std"] for row in rows]
            if xlim and attr == "inward_flux":
                visible_means.extend(row["mean"] for row in rows if xlim[0] <= row["radius_mid"] <= xlim[1])
            color = color_for_n(n)
            ax.plot(xs, ys, color=color, linewidth=1.8, label=f"N={n}")
            ax.fill_between(xs, [y - e for y, e in zip(ys, err)], [y + e for y, e in zip(ys, err)], color=color, alpha=0.12, linewidth=0)
        ax.set_xlabel("Distancia radial S [m]")
        ax.set_ylabel(ylabel)
        ax.set_title(f"Sistema 2: {ylabel}, k={format_k(k)} N/m")
        if xlim:
            ax.set_xlim(*xlim)
        if visible_means:
            set_zoomed_nonnegative_yaxis(ax, [{"inward_flux": value} for value in visible_means], "inward_flux")
        ax.grid(alpha=0.3)
        ax.legend(title="N", ncol=2)
        suffix = f"_k{int(k)}"
        fig.savefig(path.with_name(path.stem + suffix + path.suffix), dpi=180)
        plt.close(fig)


def plot_near_obstacle(profiles, tp3_radial, path, plt) -> None:
    rows = near_obstacle_rows(profiles)
    tp3_near_rows = near_obstacle_tp3(tp3_radial) if tp3_radial else []
    fig, axes = plt.subplots(3, 1, figsize=(8, 10), constrained_layout=True, sharex=True)
    for attr, axis, ylabel in [
        ("inward_flux", axes[0], "Jin en S~2 [1/(m s)]"),
        ("density", axes[1], "Densidad fresca en S~2 [1/m^2]"),
        ("normal_velocity", axes[2], "|<v_fin>| en S~2 [m/s]"),
    ]:
        for k in sorted({row["k"] for row in rows}):
            selected = [row for row in rows if row["k"] == k]
            plot_n_summary(
                axis,
                selected,
                attr,
                f"{attr}_std",
                line_color=color_for_k(k),
                linestyle=K_LINE_STYLES.get(k, "-"),
                marker="o",
                label=f"TP4 k={format_k(k)} N/m",
            )
        if attr == "inward_flux" and tp3_near_rows:
            plot_n_summary(axis, tp3_near_rows, "inward_flux", "inward_flux_std", line_color="black", linestyle="-.", marker="s", label="TP3")
            set_zoomed_nonnegative_yaxis(axis, [*rows, *tp3_near_rows], "inward_flux")
        axis.set_ylabel(ylabel)
        axis.grid(alpha=0.3)
        axis.legend()
    axes[-1].set_xlabel("N")
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_layer_s2_by_k(rows: Sequence[dict[str, float]], path: Path, plt) -> None:
    for k in sorted({row["k"] for row in rows}):
        selected = [row for row in rows if row["k"] == k]
        suffix = f"_k{int(k)}"
        plot_layer_s2_triptych(selected, path.with_name(path.stem + suffix + path.suffix), plt)
        if abs(k - 1000.0) <= 1e-9:
            plot_layer_s2_triptych(selected, path, plt)


def plot_layer_s2_triptych(rows: Sequence[dict[str, float]], path: Path, plt) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.2), constrained_layout=True, sharex=True)
    panel_specs = [
        ("density", "density_std", r"$\langle \rho_f^{in} \rangle$ cerca de $S = 2$"),
        ("normal_velocity", "normal_velocity_std", r"$|\langle v_f^{in} \rangle|$ cerca de $S = 2$"),
        ("inward_flux", "inward_flux_std", r"$J_{in}$ cerca de $S = 2$"),
    ]
    for axis, (attr, err_attr, ylabel) in zip(axes, panel_specs):
        plot_observable_panel(axis, rows, attr, err_attr, OBSERVABLE_COLORS[attr], ylabel)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_observable_panel(axis, rows: Sequence[dict[str, float]], attr: str, err_attr: str, color: str, ylabel: str) -> None:
    ordered = sorted(rows, key=lambda row: row["N"])
    xs = [row["N"] for row in ordered]
    ys = [row[attr] for row in ordered]
    err = [row[err_attr] for row in ordered]
    lower = [max(0.0, y - e) for y, e in zip(ys, err)]
    upper = [y + e for y, e in zip(ys, err)]
    lower_err = [min(e, y) for y, e in zip(ys, err)]
    axis.plot(xs, ys, color=color, linewidth=2.0)
    axis.fill_between(xs, lower, upper, color=color, alpha=0.16, linewidth=0)
    axis.errorbar(xs, ys, yerr=[lower_err, err], fmt="o", color=color, ecolor=color, capsize=5, markersize=5)
    axis.set_xlabel(r"$N$")
    axis.set_ylabel(ylabel)
    axis.set_ylim(bottom=0.0)
    axis.grid(alpha=0.25)


def near_obstacle_rows(profiles: Sequence[RadialProfile]) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for k in sorted({profile.k for profile in profiles}):
        for n in sorted({profile.n for profile in profiles}):
            per_seed = near_obstacle_per_seed(profiles, k, n)
            rows.append(
                {
                    "k": k,
                    "N": n,
                    "target_radius": LAYER_S_TARGET,
                    "radius_mid": mean([row["radius_mid"] for row in per_seed]),
                    "density": mean([row["density"] for row in per_seed]),
                    "density_std": sample_std([row["density"] for row in per_seed]),
                    "normal_velocity": mean([abs(row["normal_velocity"]) for row in per_seed]),
                    "normal_velocity_std": sample_std([abs(row["normal_velocity"]) for row in per_seed]),
                    "inward_flux": mean([row["inward_flux"] for row in per_seed]),
                    "inward_flux_std": sample_std([row["inward_flux"] for row in per_seed]),
                    "realizations": len(per_seed),
                }
            )
    return rows


def layer_s2_rows(profiles: Sequence[RadialProfile], target_radius: float = LAYER_S_TARGET) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for k in sorted({profile.k for profile in profiles}):
        for n in sorted({profile.n for profile in profiles if profile.k == k}):
            per_seed: list[dict[str, float]] = []
            for realization in sorted({profile.realization for profile in profiles if profile.k == k and profile.n == n}):
                selected = [
                    profile
                    for profile in profiles
                    if profile.k == k and profile.n == n and profile.realization == realization
                ]
                closest = closest_profiles_to_radius(selected, target_radius)
                if not closest:
                    continue
                per_seed.append(
                    {
                        "radius_mid": mean([profile.radius_mid for profile in closest]),
                        "density": mean([profile.density for profile in closest]),
                        "normal_velocity": abs(mean([profile.normal_velocity for profile in closest])),
                        "inward_flux": mean([profile.inward_flux for profile in closest]),
                    }
                )
            rows.append(
                {
                    "k": k,
                    "N": n,
                    "target_radius": target_radius,
                    "radius_mid": mean([row["radius_mid"] for row in per_seed]),
                    "density": mean([row["density"] for row in per_seed]),
                    "density_std": sample_std([row["density"] for row in per_seed]),
                    "normal_velocity": mean([row["normal_velocity"] for row in per_seed]),
                    "normal_velocity_std": sample_std([row["normal_velocity"] for row in per_seed]),
                    "inward_flux": mean([row["inward_flux"] for row in per_seed]),
                    "inward_flux_std": sample_std([row["inward_flux"] for row in per_seed]),
                    "realizations": len(per_seed),
                }
            )
    return rows


def near_obstacle_per_seed(profiles: Sequence[RadialProfile], k: float, n: int) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for realization in sorted({profile.realization for profile in profiles if profile.k == k and profile.n == n}):
        selected = [
            profile
            for profile in profiles
            if profile.k == k
            and profile.n == n
            and profile.realization == realization
        ]
        selected = closest_profiles_to_radius(selected, LAYER_S_TARGET)
        rows.append(
            {
                "realization": realization,
                "radius_mid": mean([p.radius_mid for p in selected]),
                "density": mean([p.density for p in selected]),
                "normal_velocity": mean([p.normal_velocity for p in selected]),
                "inward_flux": mean([p.inward_flux for p in selected]),
            }
        )
    return rows


def closest_profiles_to_radius(profiles: Sequence[RadialProfile], target_radius: float) -> list[RadialProfile]:
    if not profiles:
        return []
    best_distance = min(abs(profile.radius_mid - target_radius) for profile in profiles)
    return [profile for profile in profiles if abs(abs(profile.radius_mid - target_radius) - best_distance) <= 1e-9]


def radial_mean_std_by_radius(profiles: Sequence[RadialProfile], attr: str) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for radius_mid in sorted({profile.radius_mid for profile in profiles}):
        values = [profile_value(profile, attr) for profile in profiles if profile.radius_mid == radius_mid]
        rows.append({"radius_mid": radius_mid, "mean": mean(values), "std": sample_std(values)})
    return rows


def near_obstacle_tp3(rows: Sequence[dict[str, float]]) -> list[dict[str, float]]:
    out: list[dict[str, float]] = []
    for n in sorted({int(row["N"]) for row in rows}):
        per_seed: list[dict[str, float]] = []
        for realization in sorted({int(row["realization"]) for row in rows if int(row["N"]) == n}):
            selected = [
                row
                for row in rows
                if int(row["N"]) == n and int(row["realization"]) == realization
            ]
            selected = closest_dict_rows_to_radius(selected, LAYER_S_TARGET)
            if selected:
                per_seed.append(
                    {
                        "radius_mid": mean([row["radius_mid"] for row in selected]),
                        "density": mean([row.get("density", 0.0) for row in selected]),
                        "normal_velocity": abs(mean([row.get("normal_velocity", 0.0) for row in selected])),
                        "inward_flux": mean([row["inward_flux"] for row in selected]),
                    }
                )
        out.append(
            {
                "N": n,
                "target_radius": LAYER_S_TARGET,
                "radius_mid": mean([row["radius_mid"] for row in per_seed]),
                "density": mean([row["density"] for row in per_seed]),
                "density_std": sample_std([row["density"] for row in per_seed]),
                "normal_velocity": mean([row["normal_velocity"] for row in per_seed]),
                "normal_velocity_std": sample_std([row["normal_velocity"] for row in per_seed]),
                "inward_flux": mean([row["inward_flux"] for row in per_seed]),
                "inward_flux_std": sample_std([row["inward_flux"] for row in per_seed]),
                "realizations": len(per_seed),
            }
        )
    return out


def layer_s2_tp3(rows: Sequence[dict[str, float]], target_radius: float = LAYER_S_TARGET) -> list[dict[str, float]]:
    out: list[dict[str, float]] = []
    for n in sorted({int(row["N"]) for row in rows}):
        per_seed: list[dict[str, float]] = []
        for realization in sorted({int(row["realization"]) for row in rows if int(row["N"]) == n}):
            selected = [
                row
                for row in rows
                if int(row["N"]) == n and int(row["realization"]) == realization
            ]
            closest = closest_dict_rows_to_radius(selected, target_radius)
            if not closest:
                continue
            per_seed.append(
                {
                    "radius_mid": mean([row["radius_mid"] for row in closest]),
                    "density": mean([row.get("density", 0.0) for row in closest]),
                    "normal_velocity": abs(mean([row.get("normal_velocity", 0.0) for row in closest])),
                    "inward_flux": mean([row["inward_flux"] for row in closest]),
                }
            )
        out.append(
            {
                "N": n,
                "target_radius": target_radius,
                "radius_mid": mean([row["radius_mid"] for row in per_seed]),
                "density": mean([row["density"] for row in per_seed]),
                "density_std": sample_std([row["density"] for row in per_seed]),
                "normal_velocity": mean([row["normal_velocity"] for row in per_seed]),
                "normal_velocity_std": sample_std([row["normal_velocity"] for row in per_seed]),
                "inward_flux": mean([row["inward_flux"] for row in per_seed]),
                "inward_flux_std": sample_std([row["inward_flux"] for row in per_seed]),
                "realizations": len(per_seed),
            }
        )
    return out


def closest_dict_rows_to_radius(rows: Sequence[dict[str, float]], target_radius: float) -> list[dict[str, float]]:
    if not rows:
        return []
    best_distance = min(abs(row["radius_mid"] - target_radius) for row in rows)
    return [row for row in rows if abs(abs(row["radius_mid"] - target_radius) - best_distance) <= 1e-9]


def profile_value(profile: RadialProfile, attr: str) -> float:
    value = getattr(profile, attr)
    return abs(value) if attr == "normal_velocity" else value


def plot_k_comparison(summary, profiles, tp3_scanning, tp3_radial, path, plt) -> None:
    near_rows = near_obstacle_rows(profiles)
    tp3_near = near_obstacle_tp3(tp3_radial) if tp3_radial else []
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), constrained_layout=True)
    for k in sorted({row["k"] for row in summary}):
        rows = [row for row in summary if row["k"] == k]
        plot_n_summary(
            axes[0],
            rows,
            "J_mean",
            "J_std",
            line_color=color_for_k(k),
            linestyle=K_LINE_STYLES.get(k, "-"),
            marker="o",
            label=f"TP4 k={format_k(k)} N/m",
        )
        nr = [row for row in near_rows if row["k"] == k]
        plot_n_summary(
            axes[1],
            nr,
            "inward_flux",
            "inward_flux_std",
            line_color=color_for_k(k),
            linestyle=K_LINE_STYLES.get(k, "-"),
            marker="o",
            label=f"TP4 k={format_k(k)} N/m",
        )
    if tp3_scanning:
        plot_n_summary(axes[0], tp3_scanning, "J_mean", "J_std", line_color="black", linestyle="-.", marker="s", label="TP3")
    if tp3_near:
        plot_n_summary(axes[1], tp3_near, "inward_flux", "inward_flux_std", line_color="black", linestyle="-.", marker="s", label="TP3")
    axes[0].set_xlabel("N")
    axes[0].set_ylabel("<J> [1/s]")
    axes[1].set_xlabel("N")
    axes[1].set_ylabel("Jin en S~2 [1/(m s)]")
    set_zoomed_nonnegative_yaxis(axes[1], [*near_rows, *tp3_near], "inward_flux")
    for axis in axes:
        axis.grid(alpha=0.3)
        axis.legend()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_k_scalars(summary, profiles, path, plt) -> None:
    near_rows = near_obstacle_rows(profiles)
    rows: list[dict[str, float]] = []
    for k in sorted({row["k"] for row in summary}):
        j_rows = [row for row in summary if row["k"] == k]
        jin_rows = [row for row in near_rows if row["k"] == k]
        rows.append({"k": k, "max_J": max(row["J_mean"] for row in j_rows), "N_star_J": max(j_rows, key=lambda row: row["J_mean"])["N"], "max_Jin": max(row["inward_flux"] for row in jin_rows)})
    fig, axes = plt.subplots(1, 3, figsize=(13, 4), constrained_layout=True)
    xs = [row["k"] for row in rows]
    axes[0].plot(xs, [row["max_J"] for row in rows], marker="o")
    axes[1].plot(xs, [row["N_star_J"] for row in rows], marker="o")
    axes[2].plot(xs, [row["max_Jin"] for row in rows], marker="o")
    axes[0].set_ylabel("maximo <J>")
    axes[1].set_ylabel("N*(k)")
    axes[2].set_ylabel("maximo Jin en S~2")
    for axis in axes:
        axis.set_xscale("log")
        axis.set_xlabel("k [N/m]")
        axis.grid(alpha=0.3)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_used_to_wall(rows, path, plt) -> None:
    fig, ax = plt.subplots(figsize=(8, 5), constrained_layout=True)
    for k in sorted({row["k"] for row in rows}):
        selected = [row for row in rows if row["k"] == k]
        plot_n_summary(
            ax,
            selected,
            "used_to_wall_time_mean",
            "used_to_wall_time_std",
            line_color=color_for_k(k),
            linestyle=K_LINE_STYLES.get(k, "-"),
            marker="o",
            label=f"k={format_k(k)} N/m",
        )
    ax.set_xlabel("N")
    ax.set_ylabel("Tiempo usado-borde [s]")
    ax.set_title("Opcional 1.5: primer arribo al borde de una particula usada")
    annotate_partial_arrivals(ax, rows)
    ax.grid(alpha=0.3)
    ax.legend()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def annotate_partial_arrivals(axis, rows) -> None:
    for row in rows:
        observed = int(row.get("realizations_with_arrival", 0))
        if 0 < observed < 5:
            axis.annotate(
                f"{observed}/5",
                xy=(row["N"], row["used_to_wall_time_mean"]),
                xytext=(0, 8),
                textcoords="offset points",
                ha="center",
                fontsize=8,
                color="#4d4d4d",
            )


def plot_used_to_wall_heatmap(rows, path, plt) -> None:
    import numpy as np

    ks = sorted({row["k"] for row in rows})
    ns = sorted({row["N"] for row in rows})
    matrix = np.full((len(ks), len(ns)), np.nan)
    for row in rows:
        matrix[ks.index(row["k"]), ns.index(row["N"])] = row["used_to_wall_time_mean"]
    fig, ax = plt.subplots(figsize=(8, 4.5), constrained_layout=True)
    image = ax.imshow(matrix, aspect="auto", cmap="magma")
    ax.set_xticks(range(len(ns)), labels=[str(n) for n in ns])
    ax.set_yticks(range(len(ks)), labels=[format_k(k) for k in ks])
    ax.set_xlabel("N")
    ax.set_ylabel("k [N/m]")
    ax.set_title("Opcional 1.5: tiempo medio usado-borde [s]")
    colorbar = fig.colorbar(image, ax=ax)
    colorbar.set_label("Tiempo [s]")
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_runtime(rows, tp3_rows, path, plt) -> None:
    grouped: dict[tuple[float, int], list[float]] = defaultdict(list)
    for row in rows:
        grouped[(row["k"], row["N"])].append(row["runtime_seconds"])
    tp3_grouped: dict[int, list[float]] = defaultdict(list)
    for row in tp3_rows:
        tp3_grouped[int(row["N"])].append(row["runtime_seconds"])
    fig, ax = plt.subplots(figsize=(8, 5), constrained_layout=True)
    for k in sorted({row["k"] for row in rows}):
        ns = sorted({n for kk, n in grouped if kk == k})
        summary = [
            {"N": n, "runtime_seconds": mean(grouped[(k, n)]), "runtime_seconds_std": sample_std(grouped[(k, n)])}
            for n in ns
        ]
        plot_n_summary(
            ax,
            summary,
            "runtime_seconds",
            "runtime_seconds_std",
            line_color=color_for_k(k),
            linestyle=K_LINE_STYLES.get(k, "-"),
            marker="o",
            label=f"TP4 k={format_k(k)} N/m",
        )
    if tp3_grouped:
        tp3_summary = [
            {"N": n, "runtime_seconds": mean(tp3_grouped[n]), "runtime_seconds_std": sample_std(tp3_grouped[n])}
            for n in sorted(tp3_grouped)
        ]
        plot_n_summary(ax, tp3_summary, "runtime_seconds", "runtime_seconds_std", line_color="black", linestyle="-.", marker="s", label="TP3")
    ax.set_xlabel("N")
    ax.set_ylabel("Tiempo de ejecucion [s]")
    ax.set_title("Tiempo de ejecucion en funcion de N: TP4 vs TP3")
    ax.set_yscale("log")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_energy(rows, path, plt) -> None:
    fig, ax = plt.subplots(figsize=(8, 5), constrained_layout=True)
    for key in sorted({(row["k"], row["N"]) for row in rows}):
        selected = [row for row in rows if (row["k"], row["N"]) == key]
        ax.plot([row["t"] for row in selected], [row["relative_energy_delta"] for row in selected], color=color_for_n(key[1]), linestyle=K_LINE_STYLES.get(key[0], "-"), label=f"k={format_k(key[0])} N/m, N={key[1]}")
    ax.set_xlabel("Tiempo [s]")
    ax.set_ylabel("Delta E / E inicial")
    ax.set_title("Validacion de energia relativa, corridas representativas")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_n_summary(
    axis,
    rows: Sequence[dict[str, float]],
    y_key: str,
    yerr_key: str,
    *,
    line_color: str,
    linestyle: str,
    marker: str,
    label: str,
) -> None:
    ordered = sorted(rows, key=lambda row: row["N"])
    xs = [row["N"] for row in ordered]
    ys = [row[y_key] for row in ordered]
    axis.plot(xs, ys, color=line_color, linestyle=linestyle, linewidth=1.4, label=label)
    for row in ordered:
        n = int(row["N"])
        axis.errorbar(
            [n],
            [row[y_key]],
            yerr=[row.get(yerr_key, 0.0)],
            marker=marker,
            markersize=5,
            markerfacecolor=color_for_n(n),
            markeredgecolor=line_color,
            color=line_color,
            ecolor=line_color,
            capsize=3,
            linestyle="none",
        )


def set_zoomed_nonnegative_yaxis(axis, rows: Sequence[dict[str, float]], y_key: str, padding: float = 0.2) -> None:
    values = [max(0.0, float(row[y_key])) for row in rows if y_key in row]
    if not values:
        return
    top = max(max(values) * (1.0 + padding), 1e-12)
    axis.set_ylim(0.0, round(top, 12))


def mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def format_k(k: float) -> str:
    exponent = round(math.log10(k))
    if abs(k - 10**exponent) <= max(1e-9, k * 1e-9):
        return f"10^{exponent}"
    return f"{k:g}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate TP4 System 2 analysis tables and figures.")
    parser.add_argument("--system2-root", type=Path, default=Path("outputs/system2-sweeps/system2-tp4-final"))
    parser.add_argument("--tp3-root", type=Path, default=Path("outputs/tp3-reference/tp3-final-grid"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/system2-sweeps/system2-tp4-final/analysis"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path.cwd()
    system2_manifest = args.system2_root / "manifest.csv"
    runs = read_manifest(system2_manifest)
    scanning_runs = [compute_scanning_run(run, root) for run in runs]
    scanning_summary = summarize_scanning(scanning_runs)
    used_to_wall_runs = [compute_used_to_wall_run(run, root) for run in runs]
    used_to_wall_summary = summarize_used_to_wall(used_to_wall_runs)
    radial_profiles = compute_radial_profiles(runs, root)
    tp3_scanning = load_tp3_scanning(root, args.tp3_root / "manifest.csv")
    tp3_radial = load_tp3_radial(root, args.tp3_root / "manifest.csv")
    system2_layer_rows = layer_s2_rows(radial_profiles)
    tp3_layer_rows = layer_s2_tp3(tp3_radial)
    tp3_runtime = load_tp3_runtime(root, args.tp3_root / "manifest.csv")
    runtime_rows = load_system2_runtime_rows(args.system2_root)
    representative = [run for run in runs if run.realization == 0 and run.n in {100, 500, 1000} and run.k == 1000.0]
    energy_rows = [row for run in representative for row in compute_energy_sample(run, root)]

    analysis_dir = args.output_dir
    figures_dir = analysis_dir / "figures"
    write_csv(analysis_dir / "system2_scanning_runs.csv", [{"run_id": item.run.run_id, "k": item.run.k, "N": item.run.n, "realization": item.run.realization, "J": item.j, "Cfc_final": item.c_final} for item in scanning_runs])
    write_csv(analysis_dir / "system2_scanning_summary.csv", scanning_summary)
    write_csv(
        analysis_dir / "system2_optional_1_5_used_to_wall_runs.csv",
        [
            {
                "run_id": item.run.run_id,
                "k": item.run.k,
                "N": item.run.n,
                "realization": item.run.realization,
                "particle_id": "" if item.particle_id is None else item.particle_id,
                "t_obstacle": "" if item.t_obstacle is None else item.t_obstacle,
                "t_wall": "" if item.t_wall is None else item.t_wall,
                "delta_t": "" if item.delta_t is None else item.delta_t,
            }
            for item in used_to_wall_runs
        ],
    )
    write_csv(analysis_dir / "system2_optional_1_5_used_to_wall_summary.csv", used_to_wall_summary)
    write_csv(analysis_dir / "tp3_scanning_summary.csv", tp3_scanning)
    write_csv(analysis_dir / "tp3_runtime_available.csv", tp3_runtime)
    write_csv(analysis_dir / "tp3_near_obstacle_summary.csv", near_obstacle_tp3(tp3_radial))
    write_csv(analysis_dir / "tp3_layer_s2_summary.csv", tp3_layer_rows)
    write_csv(analysis_dir / "system2_radial_profiles.csv", [profile.__dict__ for profile in radial_profiles])
    write_csv(analysis_dir / "system2_near_obstacle_summary.csv", near_obstacle_rows(radial_profiles))
    write_csv(analysis_dir / "system2_layer_s2_summary.csv", system2_layer_rows)
    write_csv(analysis_dir / "system2_runtime_available.csv", runtime_rows)
    write_csv(analysis_dir / "system2_energy_representative.csv", energy_rows)
    plot_all(
        scanning_runs,
        scanning_summary,
        radial_profiles,
        used_to_wall_summary,
        tp3_scanning,
        tp3_radial,
        system2_layer_rows,
        tp3_layer_rows,
        tp3_runtime,
        runtime_rows,
        energy_rows,
        figures_dir,
    )
    write_summary(analysis_dir, figures_dir)
    print(f"Wrote System 2 analysis: {analysis_dir}")
    return 0


def write_summary(analysis_dir: Path, figures_dir: Path) -> None:
    figures = [
        figure
        for figure in sorted(figures_dir.glob("*.png"))
        if figure.name not in {
            "system2_runtime_vs_n_available.png",
            "system2_optional_1_5_used_to_wall_time_heatmap.png",
        }
    ]
    lines = ["# Salidas de analisis Sistema 2", "", "Figuras generadas:", ""]
    lines.extend(f"- `{figure.relative_to(analysis_dir)}`" for figure in figures)
    lines.extend(
        [
            "",
            "Notas:",
            "- El tiempo de ejecucion TP4 se reconstruye desde todos los logs locales disponibles; TP3 se toma de `metadata.json` por corrida.",
            "- Los perfiles radiales reconstruyen el estado fresco/usado desde `contact_events.csv` y muestrean posiciones desde `states.csv`.",
            "- Las barras de error y bandas radiales de Sistema 2 agrupan las 5 realizaciones por cada par `(k, N)`.",
            "- Las figuras `*_layer_s2_observables_vs_n*.png` usan la capa radial disponible mas cercana a S=2.",
            "- En la figura opcional 1.5, los promedios usan solo realizaciones con arribo usado-borde observado antes de `tf=500 s`.",
            "- Los colores de N son fijos en todos los graficos: 100 azul, 250 amarillo, 500 verde, 750 rojo y 1000 violeta.",
        ]
    )
    (analysis_dir / "system2_analysis_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
