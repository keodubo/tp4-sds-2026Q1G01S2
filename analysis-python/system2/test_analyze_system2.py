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

    def plot(self, xs, ys, **kwargs):
        self.lines.append(kwargs)

    def fill_between(self, xs, y1, y2, **kwargs):
        pass

    def set_xlabel(self, label):
        self.xlabel = label

    def set_ylabel(self, label):
        self.ylabel = label

    def set_title(self, title):
        self.title = title

    def set_xlim(self, *args):
        pass

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
