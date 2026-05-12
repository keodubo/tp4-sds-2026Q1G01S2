import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parent / "analyze_system2.py"
SPEC = importlib.util.spec_from_file_location("analyze_system2", MODULE_PATH)
analyze_system2 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = analyze_system2
SPEC.loader.exec_module(analyze_system2)


class AnalyzeSystem2Test(unittest.TestCase):
    def test_uses_fixed_n_palette_requested_for_final_figures(self):
        self.assertEqual("#1f77b4", analyze_system2.color_for_n(100))
        self.assertEqual("#f2c94c", analyze_system2.color_for_n(250))
        self.assertEqual("#2ca02c", analyze_system2.color_for_n(500))
        self.assertEqual("#d62728", analyze_system2.color_for_n(750))
        self.assertEqual("#9467bd", analyze_system2.color_for_n(1000))

    def test_formats_k_as_power_of_ten_for_spanish_legends(self):
        self.assertEqual("10^2", analyze_system2.format_k(100.0))
        self.assertEqual("10^3", analyze_system2.format_k(1000.0))
        self.assertEqual("10^4", analyze_system2.format_k(10000.0))

    def test_uses_distinct_k_line_colors_outside_n_palette(self):
        colors = [
            analyze_system2.color_for_k(100.0),
            analyze_system2.color_for_k(1000.0),
            analyze_system2.color_for_k(10000.0),
        ]

        self.assertEqual(len(colors), len(set(colors)))
        self.assertTrue(all(color not in analyze_system2.N_COLORS.values() for color in colors))
        self.assertEqual("#ff1493", analyze_system2.color_for_k(10000.0))

    def test_near_obstacle_tp3_keeps_error_bars_by_n(self):
        rows = [
            {"N": 100, "realization": 0, "radius_mid": 2.1, "inward_flux": 1.0},
            {"N": 100, "realization": 1, "radius_mid": 2.1, "inward_flux": 3.0},
            {"N": 250, "realization": 0, "radius_mid": 2.1, "inward_flux": 2.0},
            {"N": 250, "realization": 1, "radius_mid": 2.1, "inward_flux": 6.0},
        ]

        summary = analyze_system2.near_obstacle_tp3(rows)

        first = summary[0]
        self.assertEqual(100, first["N"])
        self.assertEqual(2.0, first["inward_flux"])
        self.assertGreater(first["inward_flux_std"], 0.0)
        self.assertEqual(2, first["realizations"])

    def test_near_obstacle_summary_uses_closest_obstacle_layer_not_full_zoom_window(self):
        profiles = [
            analyze_system2.RadialProfile(
                k=1000.0,
                n=100,
                realization=0,
                radius_mid=2.1,
                density=10.0,
                normal_velocity=-0.2,
                inward_flux=2.0,
                frames=1,
                particle_samples=1,
            ),
            analyze_system2.RadialProfile(
                k=1000.0,
                n=100,
                realization=0,
                radius_mid=4.1,
                density=99.0,
                normal_velocity=-0.8,
                inward_flux=99.0,
                frames=1,
                particle_samples=1,
            ),
        ]

        summary = analyze_system2.near_obstacle_rows(profiles)

        self.assertEqual(1, len(summary))
        self.assertAlmostEqual(10.0, summary[0]["density"])
        self.assertAlmostEqual(0.2, summary[0]["normal_velocity"])
        self.assertAlmostEqual(2.0, summary[0]["inward_flux"])

    def test_near_obstacle_tp3_uses_closest_obstacle_layer_not_full_zoom_window(self):
        rows = [
            {"N": 100, "realization": 0, "radius_mid": 2.1, "density": 10.0, "normal_velocity": -0.2, "inward_flux": 2.0},
            {"N": 100, "realization": 0, "radius_mid": 4.1, "density": 99.0, "normal_velocity": -0.8, "inward_flux": 99.0},
        ]

        summary = analyze_system2.near_obstacle_tp3(rows)

        self.assertEqual(1, len(summary))
        self.assertAlmostEqual(10.0, summary[0]["density"])
        self.assertAlmostEqual(0.2, summary[0]["normal_velocity"])
        self.assertAlmostEqual(2.0, summary[0]["inward_flux"])

    def test_layer_s2_rows_use_closest_radial_bin_per_seed_and_k(self):
        profiles = [
            analyze_system2.RadialProfile(
                k=1000.0,
                n=100,
                realization=0,
                radius_mid=2.1,
                density=1.0,
                normal_velocity=-0.2,
                inward_flux=0.2,
                frames=1,
                particle_samples=1,
            ),
            analyze_system2.RadialProfile(
                k=1000.0,
                n=100,
                realization=0,
                radius_mid=2.3,
                density=99.0,
                normal_velocity=-99.0,
                inward_flux=99.0,
                frames=1,
                particle_samples=1,
            ),
            analyze_system2.RadialProfile(
                k=1000.0,
                n=100,
                realization=1,
                radius_mid=2.1,
                density=3.0,
                normal_velocity=-0.4,
                inward_flux=1.2,
                frames=1,
                particle_samples=1,
            ),
        ]

        rows = analyze_system2.layer_s2_rows(profiles)

        self.assertEqual(1, len(rows))
        self.assertEqual(1000.0, rows[0]["k"])
        self.assertEqual(100, rows[0]["N"])
        self.assertAlmostEqual(2.0, rows[0]["density"])
        self.assertAlmostEqual(0.3, rows[0]["normal_velocity"])
        self.assertAlmostEqual(0.7, rows[0]["inward_flux"])
        self.assertEqual(2, rows[0]["realizations"])

    def test_radial_plot_uses_n_palette_without_n_colorbar(self):
        profiles = [
            analyze_system2.RadialProfile(
                k=1000.0,
                n=100,
                realization=0,
                radius_mid=2.1,
                density=1.0,
                normal_velocity=-0.1,
                inward_flux=0.1,
                frames=1,
                particle_samples=1,
            ),
            analyze_system2.RadialProfile(
                k=1000.0,
                n=250,
                realization=0,
                radius_mid=2.1,
                density=2.0,
                normal_velocity=-0.2,
                inward_flux=0.4,
                frames=1,
                particle_samples=1,
            ),
        ]
        fake_plt = FakePlt()

        analyze_system2.plot_radial_curves(
            profiles,
            "density",
            "Densidad de particulas frescas [1/m^2]",
            Path("radial.png"),
            fake_plt,
            FakeNormalize,
            FakeScalarMappable,
        )

        self.assertFalse(fake_plt.figures[0].colorbar_called)
        self.assertEqual(
            [analyze_system2.color_for_n(100), analyze_system2.color_for_n(250)],
            [line["color"] for line in fake_plt.axes[0].lines],
        )
        self.assertIn("Sistema 2", fake_plt.axes[0].title)

    def test_radial_inward_flux_zoom_sets_tight_y_axis_from_visible_means(self):
        profiles = [
            analyze_system2.RadialProfile(
                k=1000.0,
                n=100,
                realization=0,
                radius_mid=2.1,
                density=1.0,
                normal_velocity=-0.2,
                inward_flux=0.2,
                frames=1,
                particle_samples=1,
            ),
            analyze_system2.RadialProfile(
                k=1000.0,
                n=100,
                realization=1,
                radius_mid=2.1,
                density=1.0,
                normal_velocity=-0.4,
                inward_flux=0.4,
                frames=1,
                particle_samples=1,
            ),
        ]
        fake_plt = FakePlt()

        analyze_system2.plot_radial_curves(
            profiles,
            "inward_flux",
            "Flujo entrante Jin(S) [1/(m s)]",
            Path("radial.png"),
            fake_plt,
            FakeNormalize,
            FakeScalarMappable,
            xlim=(1.5, 5.0),
        )

        self.assertEqual((0.0, 0.36), fake_plt.axes[0].ylim)

    def test_runtime_plot_uses_log_scale_on_time_axis(self):
        fake_plt = FakePlt()

        analyze_system2.plot_runtime(
            rows=[
                {"k": 1000.0, "N": 100, "realization": 0, "runtime_seconds": 10.0},
                {"k": 1000.0, "N": 250, "realization": 0, "runtime_seconds": 100.0},
            ],
            tp3_rows=[{"N": 100, "realization": 0, "runtime_seconds": 1.0}],
            path=Path("runtime.png"),
            plt=fake_plt,
        )

        self.assertEqual("log", fake_plt.axes[0].yscale)

    def test_zoomed_nonnegative_y_axis_uses_observable_means(self):
        axis = FakeAxis()
        rows = [{"inward_flux": 0.01}, {"inward_flux": 0.02}]

        analyze_system2.set_zoomed_nonnegative_yaxis(axis, rows, "inward_flux")

        self.assertEqual((0.0, 0.024), axis.ylim)

    def test_energy_sample_includes_delta_over_initial_energy(self):
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_dir = root / "run"
            run_dir.mkdir()
            (run_dir / "metadata.json").write_text('{"k": 10.0}', encoding="utf-8")
            (run_dir / "states.csv").write_text(
                "step,t,particle_id,x,y,vx,vy\n"
                "0,0.0,1,0.0,0.0,1.0,0.0\n"
                "1,1.0,1,0.0,0.0,2.0,0.0\n",
                encoding="utf-8",
            )
            (run_dir / "contacts.csv").write_text(
                "step,t,contact_type,particle_id,other_id,overlap,force_x,force_y\n",
                encoding="utf-8",
            )
            run = analyze_system2.Run(run_id="run", k=10.0, n=1, realization=0, output_dir=Path("run"))

            rows = analyze_system2.compute_energy_sample(run, root)

        self.assertAlmostEqual(0.0, rows[0]["relative_energy_delta"])
        self.assertAlmostEqual(3.0, rows[1]["relative_energy_delta"])

    def test_energy_plot_uses_delta_over_initial_energy(self):
        fake_plt = FakePlt()
        rows = [
            {"k": 1000.0, "N": 100, "realization": 0, "t": 0.0, "relative_energy_delta": 0.0},
            {"k": 1000.0, "N": 100, "realization": 0, "t": 1.0, "relative_energy_delta": 0.02},
        ]

        analyze_system2.plot_energy(rows, Path("energy.png"), fake_plt)

        self.assertEqual([0.0, 0.02], fake_plt.axes[0].lines[0]["ys"])
        self.assertEqual("Delta E / E inicial", fake_plt.axes[0].ylabel)


class FakePlt:
    def __init__(self):
        self.figures = []
        self.axes = []

    def subplots(self, *args, **kwargs):
        fig = FakeFigure()
        axis = FakeAxis()
        self.figures.append(fig)
        self.axes.append(axis)
        return fig, axis

    def close(self, fig):
        pass

    def get_cmap(self, name):
        return lambda value: "cmap-color"


class FakeFigure:
    colorbar_called = False

    def savefig(self, path, dpi):
        pass

    def colorbar(self, *args, **kwargs):
        self.colorbar_called = True
        raise AssertionError("N must be represented with fixed colors, not a colorbar")


class FakeAxis:
    def __init__(self):
        self.lines = []
        self.title = ""
        self.ylabel = ""
        self.ylim = None
        self.yscale = None

    def plot(self, xs, ys, **kwargs):
        self.lines.append({"xs": xs, "ys": ys, **kwargs})

    def fill_between(self, xs, y1, y2, **kwargs):
        pass

    def errorbar(self, xs, ys, yerr=None, **kwargs):
        pass

    def set_xlabel(self, label):
        self.xlabel = label

    def set_ylabel(self, label):
        self.ylabel = label

    def set_title(self, title):
        self.title = title

    def set_xlim(self, *args):
        pass

    def set_ylim(self, bottom=None, top=None, *args, **kwargs):
        self.ylim = (bottom, top)

    def set_yscale(self, scale):
        self.yscale = scale

    def grid(self, *args, **kwargs):
        pass

    def legend(self, *args, **kwargs):
        pass


class FakeNormalize:
    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, value):
        return 0.0


class FakeScalarMappable:
    def __init__(self, *args, **kwargs):
        pass


if __name__ == "__main__":
    unittest.main()
