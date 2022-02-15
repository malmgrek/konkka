import unittest

from app import State


class TestState(unittest.TestCase):

    def setUp(self):
        users =  ["A", "B", "C"]
        self.state = State(
            name="test",
            workspace="work_dir",
            users=["A", "B", "C"],
            bills={
                "first_bill": {
                    "A": {"payment": 10.0, "share": 1./3},
                    "B": {"payment": 20.0, "share": 1./3},
                    "C": {"payment": 30.0, "share": 1./3},
                },
                "second_bill": {
                    "A": {"payment": 5.0, "share": 1./3},
                    "B": {"payment": 4.0, "share": 1./3},
                    "C": {"payment": 3.0, "share": 1./3},
                },
                "third_bill": {
                    "A": {"payment": 9.0, "share": 0.},
                    "B": {"payment": 0.0, "share": 0.},
                    "C": {"payment": 0.0, "share": 1.},
                }
            }
        )
        return

    def test_calculate_balance(self):
        balance = self.state.calculate_balance()
        self.assertEqual(balance, {"A": 0., "B": 0., "C": 0.})
        return

    def test_calculate_flow(self):
        flow = self.state.calculate_flow()
        self.assertEqual(flow, [])
        return


if __name__ == "__main__":
    unittest.main()
