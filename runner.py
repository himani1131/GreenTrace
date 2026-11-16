"""
runner.py - runs ONE piece of user code in its own process.

    python runner.py code.py            -> measure speed and memory
    python runner.py code.py check      -> run once, report only the output

The last line it prints is a JSON object (sandbox.py reads it).
"""
import contextlib
import hashlib
import io
import json
import sys
import time
import tracemalloc

# Safety limits. Linux/Mac only: Windows has no `resource` module, so there
# only the timeout in sandbox.py protects us.
try:
    import resource
    resource.setrlimit(resource.RLIMIT_CPU, (10, 10))               # max 10 s of CPU
    resource.setrlimit(resource.RLIMIT_AS, (1024 ** 3, 1024 ** 3))  # max 1 GB of memory
except (ImportError, ValueError, OSError):
    pass


def run_once(compiled):
    """Run the code once with fresh globals and return everything it printed."""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        exec(compiled, {"__name__": "__main__"})
    return buffer.getvalue()


def main():
    source = open(sys.argv[1], encoding="utf-8").read()
    mode = sys.argv[2] if len(sys.argv) > 2 else "measure"

    try:
        compiled = compile(source, "<your code>", "exec")

        # First run: gives us the program output and a rough speed.
        cpu_start = time.process_time()
        wall_start = time.perf_counter()
        output = run_once(compiled)
        first_wall = time.perf_counter() - wall_start
        first_cpu = time.process_time() - cpu_start

        result = {
            "ok": True,
            "stdout_hash": hashlib.sha256(output.encode()).hexdigest(),
            "stdout_preview": output[:300],
            "stdout_last": output[-300:],
        }

        if mode == "measure":
            # Fast code finishes in microseconds, which is mostly noise (and the CPU
            # timer is coarse). So repeat it until about 0.2 s have passed in total
            # and take the average per run.
            if first_wall >= 0.2:
                runs, wall_seconds, cpu_seconds = 1, first_wall, first_cpu
            else:
                runs = max(1, min(200000, int(0.2 / max(first_wall, 1e-6))))
                cpu_start = time.process_time()
                wall_start = time.perf_counter()
                for _ in range(runs):
                    run_once(compiled)
                wall_seconds = (time.perf_counter() - wall_start) / runs
                cpu_seconds = (time.process_time() - cpu_start) / runs

            # Peak memory (tracemalloc slows code down, so it is a separate run
            # and skipped for slow programs).
            peak_kb = None
            if first_wall < 1.0:
                tracemalloc.start()
                run_once(compiled)
                peak_kb = tracemalloc.get_traced_memory()[1] / 1024
                tracemalloc.stop()

            result.update(runs=runs, wall_seconds=wall_seconds,
                          cpu_seconds=cpu_seconds, peak_kb=peak_kb)

    except BaseException as error:  # includes SystemExit
        result = {"ok": False, "error": type(error).__name__ + ": " + str(error)}

    print(json.dumps(result))


main()
