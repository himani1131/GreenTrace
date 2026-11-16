"""
Run with:  python -m unittest discover tests
Each test feeds code to the optimizer and checks WHICH rule fired (or that none did),
then runs both versions and checks that the printed output is identical.
"""
import os
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from optimizer import optimize


def output_of(code):
    done = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=20)
    return done.returncode, done.stdout


class OptimizerTests(unittest.TestCase):

    def check(self, code, expected_rules):
        new_code, applied = optimize(code)
        self.assertEqual([a["rule_id"] for a in applied], expected_rules)
        if expected_rules:
            self.assertEqual(output_of(code), output_of(new_code))
        return new_code

    def test_pair_search(self):
        code = ("def f(a, t):\n    r = []\n    for i in range(len(a)):\n"
                "        for j in range(i + 1, len(a)):\n            if a[i] + a[j] == t:\n"
                "                r.append((a[i], a[j]))\n    return r\n"
                "print(f([1, 2, 3, 4, 5, 3, 3], 6))\nprint(f([], 3))\nprint(f([3, 3, 3], 6))")
        self.check(code, ["pair_search"])

    def test_append_loop_with_temp_variable(self):
        code = "nums = [1, 2, 3]\nout = []\nfor n in nums:\n    sq = n * n\n    out.append(sq)\nprint(out)"
        new_code = self.check(code, ["append_loop"])
        self.assertIn("[n * n for n in nums]", new_code)

    def test_append_loop_with_condition(self):
        code = "out = []\nfor n in range(20):\n    if n % 3 == 0:\n        out.append(n * 2)\nprint(out)"
        self.check(code, ["append_loop"])

    def test_append_loop_skipped_when_loop_variable_used_later(self):
        code = "out = []\nfor n in range(5):\n    out.append(n)\nprint(out, n)"
        self.check(code, [])

    def test_sum_loop(self):
        code = "total = 0\nfor x in range(100):\n    total += x\nprint(total)"
        self.check(code, ["sum_loop"])

    def test_loop_invariant_code_motion(self):
        code = ("def cost(prices, tax, d):\n    total = 0\n    for p in prices:\n"
                "        total += p * (1 + tax) * (1 - d)\n    return total\n"
                "print(cost([1, 2, 3], 0.1, 0.2))\nprint(cost([], 0.1, 0.2))")
        new_code = self.check(code, ["licm"])
        self.assertIn("_inv1 = 1 + tax", new_code)

    def test_licm_does_not_move_values_that_change_in_the_loop(self):
        code = "k = 2\ntotal = 0\nfor i in range(5):\n    k = k + 1\n    total += i * (k + 1)\nprint(total)"
        self.check(code, [])

    def test_licm_skips_loops_that_call_user_functions(self):
        code = "def bump():\n    pass\nk = 2\ntotal = 0\nfor i in range(5):\n    bump()\n    total += i * (k + 1)\nprint(total)"
        self.check(code, [])

    def test_nothing_to_do(self):
        self.check("print(sum(range(10)))", [])


if __name__ == "__main__":
    unittest.main()
