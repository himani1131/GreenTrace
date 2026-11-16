"""
GreenTrace - Phase II backend (Flask + REST API + JSON + SQLite).

Layers (same as Figure 1 in the report):
    Presentation : static/index.html, style.css, script.js   (served by this app)
    Application  : app.py  (REST routes, JSON)
    Processing   : analyzer.py, optimizer.py, validator.py, sandbox.py/runner.py, energy.py
    Data         : database.py (SQLite)

Run:   python app.py      then open   http://127.0.0.1:5000

WARNING: GreenTrace RUNS the code that is pasted into it. Use it on your own
computer only; never put it on a public server without real sandboxing.
"""
import ast

from flask import Flask, jsonify, render_template_string, request, send_from_directory

import database
import energy
from analyzer import analyze as static_analyze
from optimizer import RULES, optimize
from sandbox import run_code
from validator import validate

app = Flask(__name__, static_folder="static", static_url_path="")
database.init_db(RULES)


# ------------------------------------------------------------------ helpers
def percent_change(old, new):
    """How much smaller `new` is than `old`, in percent (negative = it got worse)."""
    if old is None or new is None or old <= 0:
        return None
    return (old - new) / old * 100


def measure(code, hardware, region, benchmark_on, energy_on, carbon_on):
    """Runs the code, returns the real measurements plus the modelled energy and carbon."""
    if not benchmark_on:
        return {"ok": True, "runtime_s": None, "cpu_s": None, "memory_kb": None,
                "energy_wh": None, "co2_g": None, "runs": 0, "stdout_preview": ""}
    result = run_code(code, "measure")
    if not result["ok"]:
        return result
    energy_wh, co2_g = energy.estimate(result["cpu_seconds"], hardware, region)
    return {"ok": True, "runtime_s": result["wall_seconds"], "cpu_s": result["cpu_seconds"],
            "memory_kb": result["peak_kb"], "runs": result["runs"],
            "energy_wh": energy_wh if energy_on else None,
            "co2_g": co2_g if carbon_on else None,
            "stdout_preview": result["stdout_preview"]}


# ------------------------------------------------------------------ routes
@app.route("/")
def home():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/analyze", methods=["POST"])
def analyze():
    data = request.get_json(silent=True) or {}
    code = data.get("code", "")
    language = data.get("language", "python")
    hardware = data.get("hardware", "laptop")
    region = data.get("region", "india")
    tests = data.get("tests", [])
    modules = data.get("modules", {})

    def on(name):
        return modules.get(name, True)

    if language != "python":
        return jsonify({"error": "This version analyzes Python only. C++ and JavaScript are planned for a later phase."}), 400
    if not code.strip():
        return jsonify({"error": "Please enter or upload source code first."}), 400
    if len(code) > 20000:
        return jsonify({"error": "The code is too long (limit: 20,000 characters)."}), 400
    try:
        ast.parse(code)
    except SyntaxError as error:
        return jsonify({"error": f"Syntax error on line {error.lineno}: {error.msg}"}), 400

    # 1) optimization candidates (static, nothing is run yet)
    optimized_code, applied = optimize(code) if on("optimization") else (code, [])
    opportunities = list(applied)

    # 2) run the original and measure it
    original_run = measure(code, hardware, region, on("benchmark"), on("energy"), on("carbon"))
    if not original_run["ok"]:
        return jsonify({"error": original_run["error"]}), 400

    # 3) prove the optimized code gives the same output, otherwise throw it away
    validation = {"executed": 0, "passed": 0, "failed": 0, "skipped": 0, "status": "NOT RUN", "rows": []}
    status = "Complete"
    message = "No known inefficient pattern could be rewritten automatically, so the code is returned unchanged."
    if applied:
        validation = validate(code, optimized_code, tests)
        if validation["status"] == "VALID":
            status = "Optimized"
            message = "The optimized code printed exactly the same results as the original on every test."
        else:
            optimized_code, applied, status = code, [], "Rejected"
            message = ("A rewrite was found, but it changed the program's output (or crashed) on the tests, "
                       "so it was discarded and the original code is kept.")

    # 4) measure the optimized code
    if applied:
        optimized_run = measure(optimized_code, hardware, region, on("benchmark"), on("energy"), on("carbon"))
        if not optimized_run["ok"]:
            return jsonify({"error": optimized_run["error"]}), 400
    else:
        optimized_run = original_run

    # 5) static analysis of both versions
    original_static = static_analyze(code, opportunities)
    optimized_static = static_analyze(optimized_code) if applied else original_static

    def side(code_text, run, static):
        return {"code": code_text,
                "runtime_s": run["runtime_s"], "cpu_s": run["cpu_s"], "memory_kb": run["memory_kb"],
                "energy_wh": run["energy_wh"], "co2_g": run["co2_g"],
                "complexity": static["complexity"] if on("complexity") else None,
                "findings": static["findings"] if on("static") else [],
                "score": static["score"]}

    def saved(key):
        a, b = original_run[key], optimized_run[key]
        return (a - b) if (a is not None and b is not None) else None

    if applied:
        title = applied[0]["title"]
    elif opportunities:
        title = "Optimization Rejected"
    elif original_static["findings"]:
        title = original_static["findings"][0]["title"]
    else:
        title = "Complexity Analysis"

    result = {
        "language": language,
        "title": title,
        "status": status,
        "message": message,
        "program_output": original_run["stdout_preview"],
        "original": side(code, original_run, original_static),
        "optimized": side(optimized_code, optimized_run, optimized_static),
        "applied": applied,
        "validation": validation,
        "comparison": {
            "runtime_pct": percent_change(original_run["runtime_s"], optimized_run["runtime_s"]),
            "cpu_pct": percent_change(original_run["cpu_s"], optimized_run["cpu_s"]),
            "energy_pct": percent_change(original_run["energy_wh"], optimized_run["energy_wh"]),
            "co2_pct": percent_change(original_run["co2_g"], optimized_run["co2_g"]),
            "energy_saved_wh": saved("energy_wh"),
            "co2_saved_g": saved("co2_g"),
        },
        "settings": {"hardware": hardware, "region": region,
                     "watts": energy.HARDWARE_WATTS.get(hardware), "grid_g_per_kwh": energy.GRID_G_PER_KWH.get(region)},
    }
    database.save_analysis(result)
    return jsonify(result)


@app.route("/api/history")
def history():
    return jsonify(database.list_history())


@app.route("/api/history/<int:analysis_id>")
def history_item(analysis_id):
    result = database.get_analysis(analysis_id)
    if result is None:
        return jsonify({"error": "Analysis not found."}), 404
    return jsonify(result)


@app.route("/api/stats")
def stats():
    return jsonify(database.stats())


@app.route("/api/rules")
def rules():
    return jsonify(database.list_rules())


REPORT_TEMPLATE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><title>GreenTrace Report #{{ r.id }}</title>
<style>
  body { font-family: Arial, sans-serif; max-width: 900px; margin: 30px auto; color: #1d2b22; padding: 0 16px; }
  h1 { color: #1e9b57; margin-bottom: 4px; } h2 { margin-top: 28px; border-bottom: 1px solid #cfe3d6; padding-bottom: 4px; }
  table { border-collapse: collapse; width: 100%; font-size: 13px; }
  th, td { border: 1px solid #cfe3d6; padding: 7px 9px; text-align: left; vertical-align: top; }
  th { background: #eef7f1; } pre { background: #f4f8f5; padding: 10px; overflow: auto; font-size: 12px; }
  .small { color: #5b6b62; font-size: 12px; } button { padding: 8px 14px; margin-top: 12px; }
  @media print { button { display: none; } }
</style></head><body>
<h1>GreenTrace Analysis Report</h1>
<p class="small">Report #{{ r.id }} &bull; {{ r.created_at }} (UTC) &bull; {{ r.language|capitalize }} &bull; Status: <b>{{ r.status }}</b></p>
<button onclick="window.print()">Print / Save as PDF</button>

<h2>Summary</h2>
<p>{{ r.message }}</p>

<h2>Detected issues</h2>
{% if r.original.findings %}<table><tr><th>Severity</th><th>Issue</th><th>Line</th><th>Why it matters</th></tr>
{% for f in r.original.findings %}<tr><td>{{ f.severity|upper }}</td><td>{{ f.title }}</td><td>{{ f.line }}</td><td>{{ f.why }}</td></tr>{% endfor %}</table>
{% else %}<p>No inefficient patterns were detected.</p>{% endif %}

<h2>Metrics (original &rarr; optimized)</h2>
<table><tr><th>Metric</th><th>Original</th><th>Optimized</th></tr>
<tr><td>Complexity (time / space)</td><td>{{ r.original.complexity.time if r.original.complexity }} / {{ r.original.complexity.space if r.original.complexity }}</td><td>{{ r.optimized.complexity.time if r.optimized.complexity }} / {{ r.optimized.complexity.space if r.optimized.complexity }}</td></tr>
<tr><td>Runtime per run (s)</td><td>{{ r.original.runtime_s }}</td><td>{{ r.optimized.runtime_s }}</td></tr>
<tr><td>CPU time per run (s)</td><td>{{ r.original.cpu_s }}</td><td>{{ r.optimized.cpu_s }}</td></tr>
<tr><td>Energy (Wh)</td><td>{{ r.original.energy_wh }}</td><td>{{ r.optimized.energy_wh }}</td></tr>
<tr><td>CO&#8322; (g)</td><td>{{ r.original.co2_g }}</td><td>{{ r.optimized.co2_g }}</td></tr>
<tr><td>GreenTrace score</td><td>{{ r.original.score }}</td><td>{{ r.optimized.score }}</td></tr></table>
<p class="small">Energy and CO&#8322; are model estimates: CPU time &times; {{ r.settings.watts }} W &times; {{ r.settings.grid_g_per_kwh }} g CO&#8322;/kWh. They are not physical measurements.</p>

<h2>Optimizations applied</h2>
{% if r.applied %}<ul>{% for a in r.applied %}<li><b>{{ a.title }}</b> (line {{ a.line }}) &ndash; {{ a.why }}</li>{% endfor %}</ul>{% else %}<p>None.</p>{% endif %}

<h2>Validation: {{ r.validation.status }}</h2>
{% if r.validation.rows %}<table><tr><th>Test</th><th>Original output</th><th>Optimized output</th><th>Result</th></tr>
{% for t in r.validation.rows %}<tr><td>{{ t.name }}</td><td>{{ t.original }}</td><td>{{ t.optimized }}</td><td>{{ t.status }}</td></tr>{% endfor %}</table>
{% else %}<p>No optimization was applied, so nothing needed validating.</p>{% endif %}

<h2>Original code</h2><pre>{{ r.original.code }}</pre>
<h2>Optimized code</h2><pre>{{ r.optimized.code }}</pre>
</body></html>"""


@app.route("/report/<int:analysis_id>")
def report(analysis_id):
    result = database.get_analysis(analysis_id)
    if result is None:
        return "Analysis not found.", 404
    return render_template_string(REPORT_TEMPLATE, r=result)


if __name__ == "__main__":
    app.run(debug=False, port=5000)
