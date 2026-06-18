"""Flask backend for the ReelPath demo.

Endpoints
---------
``GET  /``        serve the single-page UI (``ReelPath.dc.html``).
``GET  /sample``  the seeded sample production pipeline (README demo seed).
``POST /solve``   ``{tasks, deps}`` -> real critical-path analysis.

Every number the UI shows comes from the real core: the makespan, critical set,
per-task schedule, and the A/B timings + cross-check are all computed here by
:mod:`reelpath` -- there are no mocked values.

Run:  ``python app/server.py``   then open http://localhost:5000
"""

from __future__ import annotations

import pathlib
import sys
import time

from flask import Flask, jsonify, request, send_from_directory

# Make `reelpath` importable straight from a clean checkout (no install needed).
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from reelpath import analyze, bellman_ford, critical_path  # noqa: E402
from reelpath.graph import CycleError, build_split_dag  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
app = Flask(__name__, static_folder=str(HERE), static_url_path="")


# Seeded sample: a small but realistic short-film production pipeline.
# Critical path (makespan 27): Script -> Casting -> Shoot -> Edit -> VFX ->
# Color grade -> Render -> Publish.  Storyboard / Location scout / Sound design
# carry slack, so the demo shows both critical and non-critical tasks.
SAMPLE_TASKS = [
    {"id": "script", "name": "Write script", "duration": 3},
    {"id": "storyboard", "name": "Storyboard", "duration": 2},
    {"id": "casting", "name": "Casting", "duration": 4},
    {"id": "location", "name": "Location scout", "duration": 3},
    {"id": "shoot", "name": "Shoot", "duration": 6},
    {"id": "edit", "name": "Edit", "duration": 5},
    {"id": "vfx", "name": "VFX", "duration": 4},
    {"id": "sound", "name": "Sound design", "duration": 3},
    {"id": "color", "name": "Color grade", "duration": 2},
    {"id": "render", "name": "Render", "duration": 2},
    {"id": "publish", "name": "Publish", "duration": 1},
]
SAMPLE_DEPS = [
    ["script", "storyboard"],
    ["script", "casting"],
    ["storyboard", "shoot"],
    ["casting", "shoot"],
    ["location", "shoot"],
    ["shoot", "edit"],
    ["edit", "vfx"],
    ["edit", "sound"],
    ["vfx", "color"],
    ["sound", "color"],
    ["color", "render"],
    ["render", "publish"],
]


@app.get("/")
def index():
    return send_from_directory(str(HERE), "ReelPath.dc.html")


@app.get("/sample")
def sample():
    return jsonify({"tasks": SAMPLE_TASKS, "deps": SAMPLE_DEPS})


@app.post("/solve")
def solve_endpoint():
    """Run BOTH algorithms on the posted instance and return real results."""
    payload = request.get_json(force=True, silent=True) or {}
    tasks = payload.get("tasks", [])
    deps = payload.get("deps", [])

    durations = {t["id"]: t["duration"] for t in tasks}
    names = {t["id"]: t.get("name", str(t["id"])) for t in tasks}

    try:
        dag = build_split_dag(durations, deps)
        # Time the solve only (each algorithm's longest_path), like the benchmark.
        g, src = dag.graph, dag.source
        t0 = time.perf_counter()
        dist_a, _ = critical_path.longest_path(g, src)
        a_ms = (time.perf_counter() - t0) * 1000.0
        t0 = time.perf_counter()
        dist_b, _ = bellman_ford.longest_path(g, src)
        b_ms = (time.perf_counter() - t0) * 1000.0

        result = analyze(dag, critical_path.longest_path)  # full schedule via A
    except CycleError as exc:
        return jsonify({"error": "cycle", "message": str(exc)}), 400
    except (KeyError, ValueError) as exc:
        return jsonify({"error": "bad_input", "message": str(exc)}), 400

    makespan_a = dist_a[dag.target]
    makespan_b = dist_b[dag.target]
    crosscheck_ok = bool(makespan_a == makespan_b)

    schedule = [
        {
            "id": tid,
            "name": names.get(tid, str(tid)),
            "duration": row.duration,
            "es": row.es, "ef": row.ef,
            "ls": row.ls, "lf": row.lf,
            "slack": row.slack,
            "critical": row.critical,
        }
        for tid, row in result.schedule.items()
    ]

    return jsonify({
        "makespan": result.makespan,
        "critical_ids": result.critical_ids,
        "critical_path": result.critical_path,
        "schedule": schedule,
        "deps": deps,
        "timing": {"A_ms": round(a_ms, 4), "B_ms": round(b_ms, 4)},
        "crosscheck_ok": crosscheck_ok,
    })


if __name__ == "__main__":
    print("ReelPath demo running at http://localhost:5000  (Ctrl+C to stop)")
    app.run(host="127.0.0.1", port=5000, debug=False)
