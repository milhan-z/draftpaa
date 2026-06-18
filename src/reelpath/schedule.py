"""Schedule extraction and the shared solve interface.

Given a :class:`~reelpath.graph.SplitDAG` and *either* algorithm's
``longest_path`` function, this module:

* runs the forward longest-path pass (earliest start/finish, the makespan);
* runs a backward pass (latest start/finish) to obtain per-task slack;
* backtracks one concrete critical path;
* packages everything into a :class:`SolveResult`.

The forward pass is delegated to whichever algorithm is passed in, so Algorithm A
and Algorithm B share this entire layer with no duplicated logic -- they differ
only in how ``dist``/``pred`` are computed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Hashable

from .critical_path import topological_sort
from .graph import Graph, SplitDAG

# A solver is "graph + source -> (dist, pred)" -- the common interface both
# critical_path.longest_path and bellman_ford.longest_path satisfy.
LongestPathFn = Callable[[Graph, int], "tuple[list[float], list[int]]"]


@dataclass
class TaskSchedule:
    """Per-task schedule row (Critical Path Method quantities)."""

    task_id: Hashable
    duration: float
    es: float  # earliest start
    ef: float  # earliest finish
    ls: float  # latest start
    lf: float  # latest finish
    slack: float  # ls - es  (0 => task is critical)

    @property
    def critical(self) -> bool:
        return self.slack == 0


@dataclass
class SolveResult:
    """Everything a caller (demo, tests, benchmark) needs from one solve."""

    makespan: float
    critical_path: list[Hashable]   # one concrete s->t critical chain, in order
    critical_ids: list[Hashable]    # every task with slack == 0
    schedule: dict[Hashable, TaskSchedule]
    dist: list[float]
    pred: list[int]


def _backtrack_critical_path(dag: SplitDAG, pred: list[int]) -> list[Hashable]:
    """Follow predecessors from t back to s and collect the task ids in order."""
    chain: list[Hashable] = []
    v = dag.target
    seen_last: Hashable | None = object()  # sentinel distinct from any task id
    while v != -1:
        tid = dag.task_of_vertex(v)
        if tid is not None and tid != seen_last:
            chain.append(tid)
            seen_last = tid
        if v == dag.source:
            break
        v = pred[v]
    chain.reverse()
    return chain


def _latest_times(dag: SplitDAG, makespan: float) -> list[float]:
    """Backward pass: latest time each vertex may be reached keeping t at makespan.

    Processed in reverse topological order, ``latest[v]`` is the minimum over all
    out-edges ``(v -> w)`` of ``latest[w] - weight``. For a task ``i`` this gives
    ``latest[i_in] = LS(i)`` and ``latest[i_out] = LF(i)``.
    """
    order = topological_sort(dag.graph)
    latest = [makespan] * dag.graph.num_vertices
    for u in reversed(order):
        best = makespan
        for v, w in dag.graph.adj[u]:
            cand = latest[v] - w
            if cand < best:
                best = cand
        # Sink t has no out-edges; it stays at makespan, which is correct.
        latest[u] = best if dag.graph.adj[u] else makespan
    return latest


def analyze(dag: SplitDAG, longest_path_fn: LongestPathFn) -> SolveResult:
    """Solve the instance with ``longest_path_fn`` and extract the full schedule."""
    dist, pred = longest_path_fn(dag.graph, dag.source)
    makespan = dist[dag.target]

    latest = _latest_times(dag, makespan)

    schedule: dict[Hashable, TaskSchedule] = {}
    critical_ids: list[Hashable] = []
    for tid in dag.task_ids:
        vin = dag.task_in[tid]
        vout = dag.task_out[tid]
        es = dist[vin]
        ef = dist[vout]
        ls = latest[vin]
        lf = latest[vout]
        slack = ls - es
        schedule[tid] = TaskSchedule(
            task_id=tid, duration=dag.durations[tid],
            es=es, ef=ef, ls=ls, lf=lf, slack=slack,
        )
        if slack == 0:
            critical_ids.append(tid)

    critical_path = _backtrack_critical_path(dag, pred)
    return SolveResult(
        makespan=makespan,
        critical_path=critical_path,
        critical_ids=critical_ids,
        schedule=schedule,
        dist=dist,
        pred=pred,
    )
