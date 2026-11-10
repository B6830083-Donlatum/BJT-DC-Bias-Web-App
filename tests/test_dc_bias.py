import math
import unittest

from dc_bias import BiasInputs, calculate_dc_bias, parse_form


class TestReferenceOperatingPoint(unittest.TestCase):
    def setUp(self):
        self.inputs = BiasInputs(
            vcc=12.0, r1=100_000.0, r2=22_000.0,
            rc=2_200.0, re=1_000.0, beta=100.0, vbe=0.70,
        )

    def test_known_reference_values(self):
        r = calculate_dc_bias(self.inputs)
        self.assertAlmostEqual(r.vth, 2.1639, places=3)
        self.assertAlmostEqual(r.rth, 18_032.8, delta=1.0)
        self.assertAlmostEqual(r.ib, 12.298e-6, delta=1e-8)
        self.assertAlmostEqual(r.ic, 1.2298e-3, delta=1e-7)
        self.assertAlmostEqual(r.ie, 1.2422e-3, delta=1e-7)
        self.assertAlmostEqual(r.ve, 1.2422, places=3)
        self.assertAlmostEqual(r.vb, 1.9422, places=3)
        self.assertAlmostEqual(r.vc, 9.2943, places=3)
        self.assertAlmostEqual(r.vce, 8.0522, places=3)
        self.assertEqual(r.region, "active")
        self.assertEqual(r.warnings, [])

    def test_extreme_beta_stays_finite(self):
        r = calculate_dc_bias(BiasInputs(
            vcc=12.0, r1=100_000.0, r2=22_000.0,
            rc=2_200.0, re=1_000.0, beta=1.0, vbe=0.70,
        ))
        for value in (r.ib, r.ic, r.ie, r.vce):
            self.assertTrue(math.isfinite(value))


class TestParseForm(unittest.TestCase):
    BASE = {
        "vcc": "12", "beta": "100", "vbe": "0.70",
        "r1": "100", "r1_unit": "kohm",
        "r2": "22", "r2_unit": "kohm",
        "rc": "2.2", "rc_unit": "kohm",
        "re": "1", "re_unit": "kohm",
    }

    def test_kohm_converted_to_ohm(self):
        inputs, errors = parse_form(self.BASE)
        self.assertEqual(errors, [])
        self.assertAlmostEqual(inputs.r1, 100_000.0)

    def test_ohm_unit_is_not_scaled(self):
        form = dict(self.BASE, r1="100000", r1_unit="ohm")
        inputs, errors = parse_form(form)
        self.assertEqual(errors, [])
        self.assertAlmostEqual(inputs.r1, 100_000.0)

    def test_non_numeric_returns_error_not_exception(self):
        form = dict(self.BASE, r1="abc")
        inputs, errors = parse_form(form)
        self.assertIsNone(inputs)
        self.assertTrue(any("R1" in e for e in errors))

    def test_missing_field_returns_error_not_keyerror(self):
        form = {"vcc": "12"}
        inputs, errors = parse_form(form)
        self.assertIsNone(inputs)
        self.assertTrue(len(errors) >= 6)

    def test_comma_in_number_is_reported(self):
        form = dict(self.BASE, r1="1,000")
        inputs, errors = parse_form(form)
        self.assertIsNone(inputs)
        self.assertTrue(any("R1" in e for e in errors))

    def test_whitespace_is_tolerated(self):
        form = dict(self.BASE, r1=" 100 ")
        inputs, errors = parse_form(form)
        self.assertEqual(errors, [])
        self.assertAlmostEqual(inputs.r1, 100_000.0)

    def test_non_positive_values_are_rejected(self):
        for field, value in [("r1", "0"), ("beta", "0"), ("vcc", "-1")]:
            form = dict(self.BASE, **{field: value})
            inputs, errors = parse_form(form)
            self.assertIsNone(inputs, msg=field)
            self.assertTrue(errors, msg=field)

    def test_non_finite_values_are_rejected(self):
        for value in ("nan", "inf", "-inf"):
            form = dict(self.BASE, r1=value)
            inputs, errors = parse_form(form)
            self.assertIsNone(inputs, msg=value)
            self.assertTrue(errors, msg=value)


class TestOperatingRegion(unittest.TestCase):
    def test_cutoff_when_vth_below_vbe(self):
        r = calculate_dc_bias(BiasInputs(
            vcc=12.0, r1=100_000.0, r2=1_000.0,
            rc=2_200.0, re=1_000.0, beta=100.0, vbe=0.70,
        ))
        self.assertEqual(r.region, "cutoff")
        self.assertEqual(r.ic, 0.0)
        self.assertEqual(r.vc, 12.0)
        self.assertEqual(r.ve, 0.0)
        self.assertAlmostEqual(r.vb, r.vth)
        self.assertTrue(any("cutoff" in w.lower() for w in r.warnings))

    def test_saturation_when_vce_below_threshold(self):
        r = calculate_dc_bias(BiasInputs(
            vcc=12.0, r1=100_000.0, r2=22_000.0,
            rc=10_000.0, re=1_000.0, beta=100.0, vbe=0.70,
        ))
        self.assertEqual(r.region, "saturation")
        self.assertTrue(r.vce < 0.3)
        self.assertTrue(any("saturation" in w.lower() for w in r.warnings))

    def test_active_region_has_no_warnings(self):
        r = calculate_dc_bias(BiasInputs(
            vcc=12.0, r1=100_000.0, r2=22_000.0,
            rc=2_200.0, re=1_000.0, beta=100.0, vbe=0.70,
        ))
        self.assertEqual(r.region, "active")
        self.assertEqual(r.warnings, [])


if __name__ == "__main__":
    unittest.main()
