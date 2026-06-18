"""Seeded synthetic generator for layered production DAGs.

A *layered* DAG is acyclic by construction: every task sits in a layer and edges
only ever go to a strictly later layer, so no cycle can form. This gives us a
realistic family of "stages feed later stages" production schedules with a
tunable size, density, and duration spread -- all driven by an explicit ``seed``
so every benchmark instance is reproducible.

The generator returns the *readable* task graph (tasks + precedence pairs). Feed
it to :func:`reelpath.graph.build_split_dag` to obtain the node-split weighted
DAG the algorithms solve.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Hashable

from .graph import SplitDAG, build_split_dag


@dataclass
class TaskGraph:
    """A readable production instance: tasks with durations + precedence pairs."""

    tasks: list[dict]          # [{"id", "name", "duration", "layer"}, ...]
    deps: list[tuple[int, int]]  # (i, j): task i must finish before task j starts
    num_layers: int

    def as_payload(self) -> dict:
        """JSON-friendly form used by the demo backend."""
        return {
            "tasks": [dict(t) for t in self.tasks],
            "deps": [[i, j] for (i, j) in self.deps],
        }

    def durations(self) -> dict[Hashable, float]:
        return {t["id"]: t["duration"] for t in self.tasks}


def generate_task_graph(
    n_tasks: int,
    avg_out_degree: int = 3,
    duration_range: tuple[int, int] = (1, 20),
    seed: int = 0,
) -> TaskGraph:
    """Generate a seeded layered DAG with ``n_tasks`` tasks.

    Parameters
    ----------
    n_tasks:
        Number of tasks (must be >= 1).
    avg_out_degree:
        Approximate average number of successors per non-terminal task; controls
        edge density (``m ~ avg_out_degree * n``).
    duration_range:
        Inclusive ``(min, max)`` range for integer task durations. Integer
        durations keep the A == B cross-check exact.
    seed:
        Seed for the random number generator -- the only source of randomness, so
        the same seed always yields the same instance.
    """
    if n_tasks < 1:
        raise ValueError("n_tasks must be >= 1")
    dmin, dmax = duration_range
    if dmin <= 0:
        raise ValueError("durations must be strictly positive")

    rng = random.Random(seed)

    # Roughly sqrt(n) layers balances width against depth, so the critical path
    # is long enough to be interesting without the graph degenerating to a path.
    num_layers = max(2, round(math.sqrt(n_tasks)))
    per_layer = math.ceil(n_tasks / num_layers)

    layer_of = [min(num_layers - 1, i // per_layer) for i in range(n_tasks)]
    layers: list[list[int]] = [[] for _ in range(num_layers)]
    for i in range(n_tasks):
        layers[layer_of[i]].append(i)

    tasks = [
        {
            "id": i,
            "name": f"T{i}",
            "duration": rng.randint(dmin, dmax),
            "layer": layer_of[i],
        }
        for i in range(n_tasks)
    ]

    window = 3  # successors are drawn from the next few layers (locality)
    lo = max(1, avg_out_degree - 2)
    hi = avg_out_degree + 2

    dep_set: set[tuple[int, int]] = set()
    for i in range(n_tasks):
        ell = layer_of[i]
        if ell >= num_layers - 1:
            continue
        candidates: list[int] = []
        for nxt in range(ell + 1, min(num_layers, ell + 1 + window)):
            candidates.extend(layers[nxt])
        if not candidates:
            continue
        k = min(len(candidates), rng.randint(lo, hi))
        for j in rng.sample(candidates, k):
            dep_set.add((i, j))

    # Light connectivity guarantee: give every non-first-layer task at least one
    # predecessor, so the instance is one coherent pipeline rather than a cloud
    # of isolated sources.
    has_pred = [False] * n_tasks
    for i, j in dep_set:
        has_pred[j] = True
    for j in range(n_tasks):
        if layer_of[j] > 0 and not has_pred[j]:
            earlier = layers[layer_of[j] - 1]
            if earlier:
                dep_set.add((rng.choice(earlier), j))

    deps = sorted(dep_set)
    return TaskGraph(tasks=tasks, deps=deps, num_layers=num_layers)


def generate_split_dag(
    n_tasks: int,
    avg_out_degree: int = 3,
    duration_range: tuple[int, int] = (1, 20),
    seed: int = 0,
) -> tuple[SplitDAG, TaskGraph]:
    """Convenience: generate a task graph and its node-split DAG together."""
    tg = generate_task_graph(n_tasks, avg_out_degree, duration_range, seed)
    dag = build_split_dag(tg.durations(), tg.deps)
    return dag, tg
