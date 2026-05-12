#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


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
OBSERVABLE_COLORS = {
    "density": "#1f77b4",
    "normal_velocity": "#ff7f0e",
    "inward_flux": "#2ca02c",
}


@dataclass(frozen=True)
class Run:
    run_id: str
    n: int
    realization: int
    output_dir: Path


@dataclass(frozen=True)
class RadialProfile:
    n: int
    realization: int
    radius_mid: float
    density: float
    normal_velocity: float
    inward_flux: float


def color_for_n(n: int) -> str:
    return N_COLORS.get(int(n), "#7f7f7f")


def read_manifest(path: Path) -> list[Run]:
    runs: list[Run] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            runs.append(
                Run(
                    run_id=row["run_id"],
                    n=int(row["N"]),
                    realization=int(row["realization"]),
                    output_dir=Path(row["output_dir"]),
                )
            )
    return runs


def linear_slope(points: Sequence[tuple[float, float]]) -> float:
    if len(points) < 2:
        return 0.0
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    x_mean = mean(xs)
    y_mean = mean(ys)
    denom = sum((x - x_mean) ** 2 for x in xs)
    if denom == 0:
        return 0.0
    return sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)) / denom


def compute_scanning(root: Path, runs: Sequence[Run]) -> tuple[list[dict], list[dict]]:
    run_rows: list[dict] = []
    for run in runs:
        path = root / run.output_dir / "center_contacts.csv"
        points: list[tuple[float, float]] = []
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                points.append((float(row["time"]), float(row["c_fc"])))
        run_rows.append(
            {
                "run_id": run.run_id,
                "N": run.n,
                "realization": run.realization,
                "J": linear_slope(points),
                "Cfc_final": int(points[-1][1]) if points else 0,
            }
        )
    summary: list[dict] = []
    for n in sorted({row["N"] for row in run_rows}):
        values = [row["J"] for row in run_rows if row["N"] == n]
        summary.append({"N": n, "J_mean": mean(values), "J_std": sample_std(values), "realizations": len(values)})
    return run_rows, summary


def compute_used_fraction(root: Path, runs: Sequence[Run]) -> list[dict]:
    rows: list[dict] = []
    for run in runs:
        path = root / run.output_dir / "used_fraction.csv"
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                rows.append(
                    {
                        "N": run.n,
                        "realization": run.realization,
                        "time": float(row["time"]),
                        "used_fraction": float(row["used_fraction"]),
                    }
                )
    return rows


def summarize_stationary_used_fraction(used_rows: Sequence[dict]) -> list[dict]:
    rows: list[dict] = []
    for n in sorted({row["N"] for row in used_rows}):
        per_seed: list[float] = []
        stationary_times: list[float] = []
        for realization in sorted({row["realization"] for row in used_rows if row["N"] == n}):
            series = [row for row in used_rows if row["N"] == n and row["realization"] == realization]
            tail_start = max(0, int(len(series) * 0.8))
            tail = series[tail_start:] or series
            per_seed.append(mean([row["used_fraction"] for row in tail]))
            stationary_times.append(series[tail_start]["time"] if series else 0.0)
        rows.append(
            {
                "N": n,
                "Fest_mean": mean(per_seed),
                "Fest_std": sample_std(per_seed),
                "stationary_time_mean": mean(stationary_times),
                "stationary_time_std": sample_std(stationary_times),
                "realizations": len(per_seed),
            }
        )
    return rows


def load_radial_profiles(root: Path, runs: Sequence[Run]) -> list[RadialProfile]:
    profiles: list[RadialProfile] = []
    for run in runs:
        path = root / run.output_dir / "radial_profiles.csv"
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                profiles.append(
                    RadialProfile(
                        n=run.n,
                        realization=run.realization,
                        radius_mid=(float(row["radius_start"]) + float(row["radius_end"])) / 2.0,
                        density=float(row["density"]),
                        normal_velocity=float(row["normal_velocity"]),
                        inward_flux=float(row["inward_flux"]),
                    )
                )
    return profiles


def summarize_radial(profiles: Sequence[RadialProfile]) -> list[dict]:
    rows: list[dict] = []
    for n in sorted({profile.n for profile in profiles}):
        for radius_mid in sorted({profile.radius_mid for profile in profiles if profile.n == n}):
            selected = [profile for profile in profiles if profile.n == n and profile.radius_mid == radius_mid]
            rows.append(
                {
                    "N": n,
                    "radius_mid": radius_mid,
                    "density": mean([profile.density for profile in selected]),
                    "density_std": sample_std([profile.density for profile in selected]),
                    "normal_velocity": mean([profile.normal_velocity for profile in selected]),
                    "normal_velocity_std": sample_std([profile.normal_velocity for profile in selected]),
                    "inward_flux": mean([profile.inward_flux for profile in selected]),
                    "inward_flux_std": sample_std([profile.inward_flux for profile in selected]),
                    "realizations": len(selected),
                }
            )
    return rows


def near_obstacle_summary(profiles: Sequence[RadialProfile]) -> list[dict]:
    rows: list[dict] = []
    for n in sorted({profile.n for profile in profiles}):
        per_seed: list[dict[str, float]] = []
        for realization in sorted({profile.realization for profile in profiles if profile.n == n}):
            selected = [
                profile
                for profile in profiles
                if profile.n == n and profile.realization == realization and NEAR_OBSTACLE_MIN <= profile.radius_mid <= NEAR_OBSTACLE_MAX
            ]
            per_seed.append(
                {
                    "density": mean([profile.density for profile in selected]),
                    "normal_velocity": mean([profile.normal_velocity for profile in selected]),
                    "inward_flux": mean([profile.inward_flux for profile in selected]),
                }
            )
        rows.append(
            {
                "N": n,
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


def layer_s2_summary(profiles: Sequence[RadialProfile], target_radius: float = LAYER_S_TARGET) -> list[dict]:
    rows: list[dict] = []
    for n in sorted({profile.n for profile in profiles}):
        per_seed: list[dict[str, float]] = []
        for realization in sorted({profile.realization for profile in profiles if profile.n == n}):
            selected = [
                profile
                for profile in profiles
                if profile.n == n and profile.realization == realization
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


def closest_profiles_to_radius(profiles: Sequence[RadialProfile], target_radius: float) -> list[RadialProfile]:
    if not profiles:
        return []
    best_distance = min(abs(profile.radius_mid - target_radius) for profile in profiles)
    return [profile for profile in profiles if abs(abs(profile.radius_mid - target_radius) - best_distance) <= 1e-9]


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
    runs: Sequence[Run],
    scanning_runs: Sequence[dict],
    scanning_summary: Sequence[dict],
    used_rows: Sequence[dict],
    used_summary: Sequence[dict],
    radial_summary: Sequence[dict],
    near_rows: Sequence[dict],
    layer_rows: Sequence[dict],
    figures_dir: Path,
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import Normalize
    from matplotlib.cm import ScalarMappable

    figures_dir.mkdir(parents=True, exist_ok=True)
    plot_runtime(runs, figures_dir / "tp3_runtime_vs_n.png", plt)
    plot_cfc(runs, figures_dir / "tp3_cfc_t_representative.png", plt)
    plot_scanning(scanning_summary, figures_dir / "tp3_scanning_rate_vs_n.png", plt)
    plot_used_fraction(used_rows, figures_dir / "tp3_used_fraction_t_representative.png", plt)
    plot_used_summary(used_summary, figures_dir / "tp3_used_stationary_vs_n.png", plt)
    plot_radial(radial_summary, "density", "Densidad de particulas frescas [1/m^2]", figures_dir / "tp3_radial_density_profiles.png", plt, Normalize, ScalarMappable)
    plot_radial(radial_summary, "normal_velocity", "Velocidad radial media fresca |<v_fin>(S)| [m/s]", figures_dir / "tp3_radial_velocity_profiles.png", plt, Normalize, ScalarMappable)
    plot_radial(radial_summary, "inward_flux", "Flujo entrante Jin(S) [1/(m s)]", figures_dir / "tp3_radial_inward_flux_profiles.png", plt, Normalize, ScalarMappable)
    plot_radial(radial_summary, "inward_flux", "Flujo entrante Jin(S) [1/(m s)]", figures_dir / "tp3_radial_inward_flux_zoom_obstacle.png", plt, Normalize, ScalarMappable, xlim=(1.5, 5.0))
    plot_near(near_rows, figures_dir / "tp3_near_obstacle_vs_n.png", plt)
    plot_layer_s2(layer_rows, figures_dir / "tp3_layer_s2_observables_vs_n.png", plt)


def plot_runtime(runs: Sequence[Run], path: Path, plt) -> None:
    rows: list[dict] = []
    for run in runs:
        # Runtime is stored in metadata by the TP3 reference runner.
        import json

        metadata = json.loads((Path.cwd() / run.output_dir / "metadata.json").read_text(encoding="utf-8"))
        rows.append({"N": run.n, "runtime": float(metadata.get("runtime_seconds", 0.0))})
    fig, ax = plt.subplots(figsize=(8, 5), constrained_layout=True)
    summary = [{"N": n, "runtime": mean([row["runtime"] for row in rows if row["N"] == n]), "runtime_std": sample_std([row["runtime"] for row in rows if row["N"] == n])} for n in sorted({row["N"] for row in rows})]
    plot_n_summary(ax, summary, "runtime", "runtime_std", line_color="#4d4d4d", label="TP3")
    ax.set_xlabel("N")
    ax.set_ylabel("Tiempo de ejecucion [s]")
    ax.set_title("TP3: tiempo de ejecucion en funcion de N")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_cfc(runs: Sequence[Run], path: Path, plt) -> None:
    fig, ax = plt.subplots(figsize=(8, 5), constrained_layout=True)
    for run in runs:
        if run.realization != 0:
            continue
        points = read_xy(Path.cwd() / run.output_dir / "center_contacts.csv", "time", "c_fc")
        ax.step([p[0] for p in points], [p[1] for p in points], where="post", color=color_for_n(run.n), label=f"N={run.n}")
    ax.set_xlabel("Tiempo [s]")
    ax.set_ylabel("Cfc(t)")
    ax.set_title("TP3: Cfc(t), realizacion 0")
    ax.legend(ncol=2)
    ax.grid(alpha=0.3)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_scanning(summary: Sequence[dict], path: Path, plt) -> None:
    fig, ax = plt.subplots(figsize=(8, 5), constrained_layout=True)
    plot_n_summary(ax, summary, "J_mean", "J_std", line_color="#4d4d4d", label="TP3")
    ax.set_xlabel("N")
    ax.set_ylabel("<J> [1/s]")
    ax.set_title("TP3: scanning rate promedio en funcion de N")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_used_fraction(rows: Sequence[dict], path: Path, plt) -> None:
    fig, ax = plt.subplots(figsize=(8, 5), constrained_layout=True)
    for n in sorted({row["N"] for row in rows}):
        selected = [row for row in rows if row["N"] == n and row["realization"] == 0]
        ax.plot([row["time"] for row in selected], [row["used_fraction"] for row in selected], color=color_for_n(n), label=f"N={n}")
    ax.set_xlabel("Tiempo [s]")
    ax.set_ylabel("Fu(t)")
    ax.set_title("TP3: fraccion de particulas usadas, realizacion 0")
    ax.legend(ncol=2)
    ax.grid(alpha=0.3)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_used_summary(summary: Sequence[dict], path: Path, plt) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), constrained_layout=True)
    plot_n_summary(axes[0], summary, "Fest_mean", "Fest_std", line_color="#4d4d4d", label="TP3")
    plot_n_summary(axes[1], summary, "stationary_time_mean", "stationary_time_std", line_color="#4d4d4d", label="TP3")
    axes[0].set_ylabel("Fraccion estacionaria Fest")
    axes[1].set_ylabel("Tiempo estacionario [s]")
    for axis in axes:
        axis.set_xlabel("N")
        axis.grid(alpha=0.3)
        axis.legend()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_radial(rows: Sequence[dict], attr: str, ylabel: str, path: Path, plt, Normalize, ScalarMappable, xlim=None) -> None:
    fig, ax = plt.subplots(figsize=(8, 5), constrained_layout=True)
    ns = sorted({row["N"] for row in rows})
    for n in ns:
        selected = [row for row in rows if row["N"] == n]
        xs = [row["radius_mid"] for row in selected]
        ys = [plot_value(row, attr) for row in selected]
        err = [row[f"{attr}_std"] for row in selected]
        color = color_for_n(n)
        ax.plot(xs, ys, color=color, linewidth=1.8, label=f"N={n}")
        ax.fill_between(xs, [y - e for y, e in zip(ys, err)], [y + e for y, e in zip(ys, err)], color=color, alpha=0.12, linewidth=0)
    ax.set_xlabel("Distancia radial S [m]")
    ax.set_ylabel(ylabel)
    ax.set_title(f"TP3: {ylabel}")
    if xlim:
        ax.set_xlim(*xlim)
    ax.grid(alpha=0.3)
    ax.legend(title="N", ncol=2)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_near(rows: Sequence[dict], path: Path, plt) -> None:
    fig, axes = plt.subplots(3, 1, figsize=(8, 10), constrained_layout=True, sharex=True)
    for attr, axis, ylabel in [
        ("inward_flux", axes[0], "Jin cerca del obstaculo [1/(m s)]"),
        ("density", axes[1], "Densidad fresca cerca del obstaculo [1/m^2]"),
        ("normal_velocity", axes[2], "|<v_fin>| cerca del obstaculo [m/s]"),
    ]:
        plot_n_summary(axis, rows, attr, f"{attr}_std", line_color="#4d4d4d", label="TP3")
        axis.set_ylabel(ylabel)
        axis.grid(alpha=0.3)
        axis.legend()
    axes[-1].set_xlabel("N")
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_layer_s2(rows: Sequence[dict], path: Path, plt) -> None:
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


def plot_observable_panel(axis, rows: Sequence[dict], attr: str, err_attr: str, color: str, ylabel: str) -> None:
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


def plot_n_summary(axis, rows: Sequence[dict], y_key: str, yerr_key: str, *, line_color: str, label: str) -> None:
    ordered = sorted(rows, key=lambda row: row["N"])
    xs = [row["N"] for row in ordered]
    ys = [row[y_key] for row in ordered]
    axis.plot(xs, ys, color=line_color, linewidth=1.4, label=label)
    for row in ordered:
        n = int(row["N"])
        axis.errorbar(
            [n],
            [row[y_key]],
            yerr=[row[yerr_key]],
            marker="o",
            markersize=5,
            markerfacecolor=color_for_n(n),
            markeredgecolor=line_color,
            color=line_color,
            ecolor=line_color,
            capsize=3,
            linestyle="none",
        )


def plot_value(row: dict, attr: str) -> float:
    value = row[attr]
    return abs(value) if attr == "normal_velocity" else value


def read_xy(path: Path, x_key: str, y_key: str) -> list[tuple[float, float]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [(float(row[x_key]), float(row[y_key])) for row in csv.DictReader(handle)]


def mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def sample_std(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    avg = mean(values)
    return math.sqrt(sum((value - avg) ** 2 for value in values) / (len(values) - 1))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate TP3 reference analysis tables and figures.")
    parser.add_argument("--tp3-root", type=Path, default=Path("outputs/tp3-reference/tp3-final-grid"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/tp3-reference/tp3-final-grid/analysis"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    runs = read_manifest(args.tp3_root / "manifest.csv")
    scanning_runs, scanning_summary = compute_scanning(Path.cwd(), runs)
    used_rows = compute_used_fraction(Path.cwd(), runs)
    used_summary = summarize_stationary_used_fraction(used_rows)
    profiles = load_radial_profiles(Path.cwd(), runs)
    radial_summary = summarize_radial(profiles)
    near_rows = near_obstacle_summary(profiles)
    layer_rows = layer_s2_summary(profiles)
    analysis_dir = args.output_dir
    figures_dir = analysis_dir / "figures"
    write_csv(analysis_dir / "tp3_scanning_runs.csv", scanning_runs)
    write_csv(analysis_dir / "tp3_scanning_summary.csv", scanning_summary)
    write_csv(analysis_dir / "tp3_used_fraction_samples.csv", used_rows)
    write_csv(analysis_dir / "tp3_used_stationary_summary.csv", used_summary)
    write_csv(analysis_dir / "tp3_radial_profiles_summary.csv", radial_summary)
    write_csv(analysis_dir / "tp3_near_obstacle_summary.csv", near_rows)
    write_csv(analysis_dir / "tp3_layer_s2_summary.csv", layer_rows)
    plot_all(runs, scanning_runs, scanning_summary, used_rows, used_summary, radial_summary, near_rows, layer_rows, figures_dir)
    write_summary(analysis_dir, figures_dir)
    print(f"Wrote TP3 analysis: {analysis_dir}")
    return 0


def write_summary(analysis_dir: Path, figures_dir: Path) -> None:
    figures = sorted(figures_dir.glob("*.png"))
    lines = ["# Salidas de analisis TP3", "", "Figuras generadas:", ""]
    lines.extend(f"- `{figure.relative_to(analysis_dir)}`" for figure in figures)
    lines.extend(["", "Notas:", "- Las barras de error y bandas radiales usan las cinco realizaciones por N.", "- La figura `tp3_layer_s2_observables_vs_n.png` usa la capa radial disponible mas cercana a S=2.", "- La fraccion estacionaria Fu se estima con el ultimo 20% de cada serie temporal.", "- Los colores de N son fijos en todos los graficos: 100 azul, 250 amarillo, 500 verde, 750 rojo y 1000 violeta."])
    (analysis_dir / "tp3_analysis_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
