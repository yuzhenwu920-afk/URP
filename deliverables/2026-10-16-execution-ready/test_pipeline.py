"""Analytic and synthetic software checks only; no crop model is validated."""
import json
import math
import tempfile
import unittest
from pathlib import Path

import numpy as np
from SALib.sample import sobol
from SALib.test_functions import Ishigami

import real_model_pipeline as p


def synthetic_response(irrigation=445.27):
    return dict(Y_13pct=16.7, Y_dry=16.7 * .87, B_t_ha=35.,
                Tr_mm=200., Es_mm=50., ET_mm=250., MaxCC=.94,
                Irrigation_mm=irrigation, Rain_mm=100., CR_mm=0., GwIn_mm=0.,
                Runoff_mm=10., DeepPerc_mm=0., TileDrain_mm=0.,
                Profile_initial_mm=500., Profile_final_mm=500 + irrigation + 100 - 250 - 10,
                Surface_initial_mm=0., Surface_final_mm=0., Water_balance_residual_mm=0.,
                Max_daily_balance_residual_mm=0.)


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.config = self.root / "config.json"
        original = p.read(Path(__file__).with_name("study_config.json"))["cases"]["2019"]
        original["baseline_expected"] = synthetic_response()
        self.case = original
        p.write(self.config, {"cases": {"2019": original}})

    def tearDown(self):
        self.temp.cleanup()

    def adapter(self, mutate=False):
        path = self.root / "synthetic_fixture.py"
        source = self.root / "synthetic_source.txt"
        source.write_text("SOFTWARE TEST FIXTURE, NOT A CROP MODEL", encoding="utf-8")
        info = {"engine": "Modified_DI_AquaCrop", "deterministic": True,
                "notice": "synthetic software fixture only",
                "files": [{"role": role, "path": source.name, "sha256": p.sha(source)}
                          for role in ["model_source", "input"]]}
        path.write_text("counter=0\n" + f"def provenance(): return {info!r}\n"
                        + "def simulate(*,params,year,management=None):\n"
                        + " global counter\n counter+=1\n"
                        + f" r={synthetic_response()!r}\n"
                        + (" r['B_t_ha']+=counter\n" if mutate else "")
                        + " return r\n", encoding="utf-8")
        return path

    def test_ishigami_known_indices(self):
        problem = {"num_vars": 3, "names": ["x1", "x2", "x3"], "bounds": [[-math.pi, math.pi]] * 3}
        x = sobol.sample(problem, 4096, calc_second_order=False, seed=281)
        result = p.sensitivity(problem, Ishigami.evaluate(x), seed=903)
        np.testing.assert_allclose([r["S1"] for r in result["indices"]], [.313905, .442411, 0.], atol=.03)
        np.testing.assert_allclose([r["ST"] for r in result["indices"]], [.557589, .442411, .243684], atol=.03)

    def test_constant_output_is_not_fake_zero_sensitivity(self):
        problem = p.problem(self.case)
        self.assertIsNone(p.sensitivity(problem, np.ones(80))["indices"])
        with self.assertRaises(ValueError):
            p.sensitivity(problem, np.r_[np.ones(79), np.nan])

    def test_design_size_order_and_expansion_prefix(self):
        problem = p.problem(self.case)
        a = sobol.sample(problem, 128, calc_second_order=False, seed=101)
        b = sobol.sample(problem, 512, calc_second_order=False, seed=101)
        self.assertEqual(a.shape, (1280, 8))
        np.testing.assert_array_equal(a, b[:1280])
        for j in range(8):
            expected = a[0].copy()
            expected[j] = a[9, j]
            np.testing.assert_array_equal(a[j + 1], expected)

    def test_units_and_complete_water_ledger(self):
        checked = p.check_response(synthetic_response(), self.case)
        self.assertAlmostEqual(checked["IWP_kg_m3"], 100 * 16.7 / 445.27)
        for key, bad in [("Y_dry", 16.7), ("MaxCC", 94.), ("ET_mm", 260.),
                         ("Irrigation_mm", 400.), ("Profile_final_mm", 500.),
                         ("Max_daily_balance_residual_mm", .1), ("B_t_ha", float("nan"))]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                p.check_response(dict(synthetic_response(), **{key: bad}), self.case)

    def test_template_fails_without_proxy_fallback(self):
        with self.assertRaises(NotImplementedError):
            p.load_adapter(Path(__file__).with_name("adapter_template.py"))

    def test_stateful_adapter_rejected(self):
        with self.assertRaisesRegex(ValueError, "Repeated baseline changed"):
            p.benchmark(self.config, self.adapter(mutate=True), 2019, self.root / "receipt.json")

    def test_source_hash_change_rejected(self):
        adapter = self.adapter()
        (self.root / "synthetic_source.txt").write_text("changed", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "checksum mismatch"):
            p.load_adapter(adapter)

    def test_resume_complete_and_reject_corrupt_response(self):
        design = self.root / "design"
        p.prepare(self.config, design, n=8, seeds=(101,))
        adapter = self.adapter()
        receipt = self.root / "receipt.json"
        p.benchmark(self.config, adapter, 2019, receipt)
        journal = self.root / "responses.jsonl"
        first = p.run_design(self.config, design, adapter, receipt, 2019, 101, journal, limit=3)
        self.assertEqual(first["status"], "PARTIAL")
        with self.assertRaisesRegex(ValueError, "Complete response provenance"):
            p.analyze(self.config, design, 2019, 101, journal, self.root / "si.json")
        result = p.run_design(self.config, design, adapter, receipt, 2019, 101, journal)
        self.assertEqual(result["new_calls"], 77)
        p.analyze(self.config, design, 2019, 101, journal, self.root / "si.json")
        analyzed = p.read(self.root / "si.json")
        self.assertTrue(all(r["indices"] is None for r in analyzed["outputs"].values()))
        self.assertEqual(p.run_design(self.config, design, adapter, receipt, 2019, 101, journal)["new_calls"], 0)
        lines = journal.read_text().splitlines()
        journal.write_text("\n".join(lines[:-1]) + "\n")
        with self.assertRaisesRegex(ValueError, "Incomplete Saltelli"):
            p.analyze(self.config, design, 2019, 101, journal, self.root / "bad.json")
        journal.write_text("\n".join(lines + [lines[0]]) + "\n")
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            p.analyze(self.config, design, 2019, 101, journal, self.root / "bad.json")

    def test_design_tampering_rejected(self):
        design = self.root / "design"
        p.prepare(self.config, design, n=8, seeds=(101,))
        path = design / "X_2019_N8_seed101.npy"
        a = np.load(path)
        a[0, 0] += .01
        np.save(path, a)
        with self.assertRaisesRegex(ValueError, "Design checksum"):
            p.load_design(self.config, design, 2019, 101)

    def test_unverified_baseline_is_blocked(self):
        self.case["baseline_expected"] = None
        p.write(self.config, {"cases": {"2019": self.case}})
        with self.assertRaisesRegex(ValueError, "not verified"):
            p.benchmark(self.config, self.adapter(), 2019, self.root / "receipt.json")


if __name__ == "__main__":
    unittest.main(verbosity=2)
