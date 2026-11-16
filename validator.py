"""
validator.py - proves (on the given tests) that optimized code behaves like the original.

Test cases are Python expressions typed by the user, one per line, for example
    find_pairs([1, 2, 3, 4], 5)
For every test we run  ORIGINAL + print(expression)  and  OPTIMIZED + print(expression)
in separate processes and compare what they print. The plain program run is test #1.
"""
from sandbox import run_code

MAX_TESTS = 10


def clean_tests(raw_tests):
    tests = [t.strip() for t in (raw_tests or []) if t.strip()]
    return [t[:300] for t in tests[:MAX_TESTS]]


def short(text, limit=90):
    text = (text or "").strip().replace("\n", " \u23CE ")
    return text if len(text) <= limit else text[:limit] + "\u2026"


def validate(original_code, optimized_code, raw_tests):
    tests = clean_tests(raw_tests)
    cases = [("Program output", "")] + [(t, f"\nprint({t})\n") for t in tests]

    rows = []
    for name, extra in cases:
        before = run_code(original_code + extra, "check")
        after = run_code(optimized_code + extra, "check")

        if not before["ok"]:
            # The original itself fails on this test, so it proves nothing either way.
            rows.append({"name": name, "status": "skipped", "original": short(before["error"]),
                         "optimized": "\u2014"})
            continue

        def shown(result):
            if not result["ok"]:
                return short(result["error"])
            if name == "Program output":
                return short(result["stdout_preview"]) or "(no output)"
            lines = result["stdout_last"].strip().splitlines()
            return short(lines[-1] if lines else "(no output)")

        same = after["ok"] and before["stdout_hash"] == after["stdout_hash"]
        rows.append({"name": name, "status": "pass" if same else "fail",
                     "original": shown(before), "optimized": shown(after)})

    passed = sum(r["status"] == "pass" for r in rows)
    failed = sum(r["status"] == "fail" for r in rows)
    skipped = sum(r["status"] == "skipped" for r in rows)
    if failed:
        status = "INVALID"
    elif passed:
        status = "VALID"
    else:
        status = "NOT RUN"
    return {"executed": passed + failed, "passed": passed, "failed": failed,
            "skipped": skipped, "status": status, "rows": rows}
