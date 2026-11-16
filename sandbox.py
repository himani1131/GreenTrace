"""
sandbox.py - the only place that starts runner.py as a separate process.

Running user code in its own process means an infinite loop or a crash cannot
take the web server down. NOTE: this is isolation, not a full security sandbox.
Run GreenTrace on your own computer only.
"""
import json
import os
import subprocess
import sys
import tempfile

RUNNER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "runner.py")


def run_code(code, mode="measure", timeout=20):
    """
    mode "measure": run many times, report wall time, CPU time and peak memory.
    mode "check"  : run once, report only what the program printed.
    """
    with tempfile.TemporaryDirectory() as folder:
        path = os.path.join(folder, "user_code.py")
        with open(path, "w", encoding="utf-8") as f:
            f.write(code)
        try:
            done = subprocess.run([sys.executable, RUNNER, path, mode], capture_output=True,
                                  text=True, timeout=timeout, cwd=folder,
                                  stdin=subprocess.DEVNULL)
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": f"The code ran for more than {timeout} seconds and was stopped."}

    try:
        return json.loads(done.stdout.strip().splitlines()[-1])
    except (IndexError, ValueError):
        if done.returncode < 0:  # killed by the operating system (CPU / memory limit)
            return {"ok": False, "error": "The code was stopped because it used too much CPU time "
                                          "or memory (limits: 10 s of CPU, 1 GB of memory)."}
        return {"ok": False, "error": "The code crashed the runner: " + done.stderr[-300:]}
