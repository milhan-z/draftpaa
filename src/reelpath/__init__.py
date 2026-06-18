"""ReelPath -- critical-path analyzer for video production schedules.

Public API
----------
* :class:`Graph`, :class:`SplitDAG`, :func:`build_split_dag`, :class:`CycleError`
  -- the model and its construction (:mod:`reelpath.graph`).
* :func:`generate_task_graph`, :func:`generate_split_dag`
  -- seeded instance generation (:mod:`reelpath.generator`).
* :mod:`reelpath.critical_path` and :mod:`reelpath.bellman_ford`
  -- the two algorithms, each exposing ``longest_path(graph, source)``.
* :func:`analyze`, :class:`SolveResult`, :class:`TaskSchedule`
  -- schedule extraction (:mod:`reelpath.schedule`).
* :func:`solve` -- thin convenience that solves with a named algorithm.
"""

from __future__ import annotations

from . import bellman_ford, critical_path
from .graph import CycleError, Graph, SplitDAG, build_split_dag
from .generator import TaskGraph, generate_split_dag, generate_task_graph
from .schedule import SolveResult, TaskSchedule, analyze

__all__ = [
    "Graph",
    "SplitDAG",
    "build_split_dag",
    "CycleError",
    "TaskGraph",
    "generate_task_graph",
    "generate_split_dag",
    "critical_path",
    "bellman_ford",
    "analyze",
    "solve",
    "SolveResult",
    "TaskSchedule",
    "ALGORITHMS",
]

__version__ = "1.0.0"

# Map a friendly name to each algorithm's longest_path function (shared interface).
ALGORITHMS = {
    "A": critical_path.longest_path,   # topo-sort + DAG longest path  (O(V+E))
    "B": bellman_ford.longest_path,    # Bellman-Ford on negated weights (O(V*E))
    "topo": critical_path.longest_path,
    "bellman-ford": bellman_ford.longest_path,
}


def solve(dag: SplitDAG, algorithm: str = "A") -> SolveResult:
    """Solve ``dag`` with the named algorithm (``"A"`` or ``"B"``)."""
    try:
        fn = ALGORITHMS[algorithm]
    except KeyError:
        raise ValueError(
            f"unknown algorithm {algorithm!r}; choose from {sorted(ALGORITHMS)}"
        ) from None
    return analyze(dag, fn)
