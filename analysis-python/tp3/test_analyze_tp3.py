import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parent / "analyze_tp3.py"
SPEC = importlib.util.spec_from_file_location("analyze_tp3", MODULE_PATH)
analyze_tp3 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = analyze_tp3
SPEC.loader.exec_module(analyze_tp3)


class AnalyzeTp3Test(unittest.TestCase):
    def test_uses_fixed_n_palette_requested_for_final_figures(self):
        self.assertEqual("#1f77b4", analyze_tp3.color_for_n(100))
        self.assertEqual("#f2c94c", analyze_tp3.color_for_n(250))
        self.assertEqual("#2ca02c", analyze_tp3.color_for_n(500))
        self.assertEqual("#d62728", analyze_tp3.color_for_n(750))
        self.assertEqual("#9467bd", analyze_tp3.color_for_n(1000))

    def test_radial_plot_uses_n_palette_without_n_colorbar(self):
        rows = [
            {
                "N": 100,
                "radius_mid": 2.1,
                "density": 1.0,
                "density_std": 0.1,
            },
            {
                "N": 250,
                "radius_mid": 2.1,
                "density": 2.0,
                "density_std": 0.2,
            },
        ]
        fake_plt = FakePlt()

        analyze_tp3.plot_radial(
            rows,
            "density",
            "Densidad de particulas frescas [1/m^2]",
            Path("radial.png"),
            fake_plt,
            FakeNormalize,
            FakeScalarMappable,
        )

        self.assertFalse(fake_plt.figures[0].colorbar_called)
        self.assertEqual(
            [analyze_tp3.color_for_n(100), analyze_tp3.color_for_n(250)],
            [line["color"] for line in fake_plt.axes[0].lines],
        )
        self.assertIn("TP3", fake_plt.axes[0].title)
        self.assertNotIn("runtime", fake_plt.axes[0].title.lower())

    def test_layer_s2_summary_uses_closest_radial_bin_per_seed(self):
        profiles = [
            analyze_tp3.RadialProfile(
                n=100,
                realization=0,
                radius_mid=2.1,
                density=1.0,
                normal_velocity=-0.2,
                inward_flux=0.2,
            ),
            analyze_tp3.RadialProfile(
                n=100,
                realization=0,
                radius_mid=2.3,
                density=99.0,
                normal_velocity=-99.0,
                inward_flux=99.0,
            ),
            analyze_tp3.RadialProfile(
                n=100,
                realization=1,
                radius_mid=2.1,
                density=3.0,
                normal_velocity=-0.4,
                inward_flux=1.2,
            ),
        ]

        rows = analyze_tp3.layer_s2_summary(profiles)

        self.assertEqual(1, len(rows))
        self.assertEqual(100, rows[0]["N"])
        self.assertAlmostEqual(2.0, rows[0]["density"])
        self.assertAlmostEqual(0.3, rows[0]["normal_velocity"])
        self.assertAlmostEqual(0.7, rows[0]["inward_flux"])
        self.assertEqual(2, rows[0]["realizations"])


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
