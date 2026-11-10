import unittest

from app import app


class TestWebRoutes(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_get_index_returns_form(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'name="vcc"', resp.data)
        self.assertIn(b'name="r1_unit"', resp.data)

    def test_post_valid_inputs_shows_result(self):
        resp = self.client.post("/calculate", data={
            "vcc": "12", "beta": "100", "vbe": "0.70",
            "r1": "100", "r1_unit": "kohm",
            "r2": "22", "r2_unit": "kohm",
            "rc": "2.2", "rc_unit": "kohm",
            "re": "1", "re_unit": "kohm",
        })
        self.assertEqual(resp.status_code, 200)
        self.assertIn("VCE", resp.get_data(as_text=True))
        self.assertIn("8.052", resp.get_data(as_text=True))

    def test_post_invalid_inputs_returns_400_with_error(self):
        resp = self.client.post("/calculate", data={
            "vcc": "12", "beta": "0", "vbe": "0.70",
            "r1": "100", "r1_unit": "kohm",
            "r2": "22", "r2_unit": "kohm",
            "rc": "2.2", "rc_unit": "kohm",
            "re": "1", "re_unit": "kohm",
        })
        self.assertEqual(resp.status_code, 400)
        self.assertIn("ต้องเป็นค่ามากกว่าศูนย์", resp.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
