"""Core graph data structures for ReelPath.

This module provides:

* :class:`Graph` -- a directed, edge-weighted graph stored as an integer-indexed
  adjacency list. This is the single representation both algorithms operate on.
* :class:`CycleError` -- raised when a precedence instance is not acyclic and
  therefore has no feasible schedule.
* :func:`build_split_dag` -- the *node-splitting* construction from README s2.2
  that turns a set of tasks (with durations) and precedence constraints into one
  purely edge-weighted DAG, so the same longest-path machinery serves both
  algorithms.

No path-finding, topological-sort, or scheduling logic lives here -- this file is
deliberately limited to the data structure and the model construction.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Hashable, Iterable, Iterator


class CycleError(ValueError):
    """Raised when a precedence graph contains a cycle.

    A cyclic set of precedence constraints describes an impossible schedule
    ("A before B before A"), so the instance is *infeasible* and must be
    rejected rather than silently producing a wrong makespan.
    """


class Graph:
    """A directed, edge-weighted graph backed by an adjacency list.

    Vertices are the integers ``0 .. num_vertices - 1``. Each entry
    ``adj[u]`` is a list of ``(v, weight)`` pairs describing an edge ``u -> v``.
    Integer indexing (rather than hashable labels) keeps the inner loops of both
    algorithms tight, which matters at the 10,000-task scale of the benchmark.
    """

    __slots__ = ("num_vertices", "adj", "num_edges")

    def __init__(self, num_vertices: int) -> None:
        if num_vertices < 0:
            raise ValueError("num_vertices must be non-negative")
        self.num_vertices: int = num_vertices
        self.adj: list[list[tuple[int, float]]] = [[] for _ in range(num_vertices)]
        self.num_edges: int = 0

    def add_edge(self, u: int, v: int, weight: float) -> None:
        """Add a directed edge ``u -> v`` with the given non-negative weight."""
        if not (0 <= u < self.num_vertices):
            raise IndexError(f"source vertex {u} out of range")
        if not (0 <= v < self.num_vertices):
            raise IndexError(f"target vertex {v} out of range")
        if weight < 0:
            raise ValueError("edge weights must be non-negative in this model")
        self.adj[u].append((v, weight))
        self.num_edges += 1

    def neighbors(self, u: int) -> list[tuple[int, float]]:
        """Return the out-neighbours of ``u`` as ``(v, weight)`` pairs."""
        return self.adj[u]

    def edges(self) -> Iterator[tuple[int, int, float]]:
        """Yield every edge as a ``(u, v, weight)`` triple."""
        for u in range(self.num_vertices):
            for v, w in self.adj[u]:
                yield u, v, w

    def edge_list(self) -> list[tuple[int, int, float]]:
        """Materialise all edges into a flat list (handy for Bellman-Ford)."""
        return list(self.edges())

    def indegree(self) -> list[int]:
        """Return the in-degree of every vertex."""
        indeg = [0] * self.num_vertices
        for u in range(self.num_vertices):
            for v, _w in self.adj[u]:
                indeg[v] += 1
        return indeg

    def validate(self) -> None:
        """Sanity-check the structure (indices in range, weights finite)."""
        for u in range(self.num_vertices):
            for v, w in self.adj[u]:
                if not (0 <= v < self.num_vertices):
                    raise ValueError(f"edge ({u}->{v}) targets an unknown vertex")
                if w < 0 or w != w or w == float("inf"):
                    raise ValueError(f"edge ({u}->{v}) has an invalid weight {w!r}")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"Graph(V={self.num_vertices}, E={self.num_edges})"


# --------------------------------------------------------------------------- #
# Node-splitting construction (README s2.2)
# --------------------------------------------------------------------------- #


@dataclass
class SplitDAG:
    """The node-split, purely edge-weighted DAG that both algorithms solve.

    Each task ``i`` becomes two vertices ``i_in`` and ``i_out`` joined by a
    duration edge of weight ``d(i)``. A super-source ``s`` feeds every task with
    no prerequisite and a super-sink ``t`` collects every terminal task, so the
    makespan is exactly the maximum-weight ``s -> t`` path.
    """

    graph: Graph
    source: int                       # index of the super-source s
    target: int                       # index of the super-sink t
    task_ids: list[Hashable]          # task ids in a stable order
    task_in: dict[Hashable, int]      # task id -> i_in vertex index
    task_out: dict[Hashable, int]     # task id -> i_out vertex index
    durations: dict[Hashable, float]  # task id -> d(i)
    vertex_label: list[str] = field(default_factory=list)  # index -> readable label

    @property
    def num_vertices(self) -> int:
        return self.graph.num_vertices

    @property
    def num_edges(self) -> int:
        return self.graph.num_edges

    def task_of_vertex(self, vertex: int) -> Hashable | None:
        """Return the task id a vertex belongs to, or ``None`` for s/t."""
        return self._vertex_task.get(vertex)

    def __post_init__(self) -> None:
        self._vertex_task: dict[int, Hashable] = {}
        for tid, vin in self.task_in.items():
            self._vertex_task[vin] = tid
        for tid, vout in self.task_out.items():
            self._vertex_task[vout] = tid


def _normalise_tasks(tasks) -> tuple[list[Hashable], dict[Hashable, float]]:
    """Accept tasks as a ``{id: duration}`` mapping or a list of dicts/tuples.

    Returns the ordered list of ids and an id->duration map. Durations must be
    strictly positive (a zero-length task is meaningless in this model).
    """
    ids: list[Hashable] = []
    durations: dict[Hashable, float] = {}
    if isinstance(tasks, dict):
        items: Iterable = tasks.items()
    else:
        items = []
        for entry in tasks:
            if isinstance(entry, dict):
                items.append((entry["id"], entry["duration"]))
            else:  # (id, duration) pair
                items.append((entry[0], entry[1]))
    for tid, dur in items:
        if tid in durations:
            raise ValueError(f"duplicate task id {tid!r}")
        if dur <= 0:
            raise ValueError(f"task {tid!r} has non-positive duration {dur!r}")
        ids.append(tid)
        durations[tid] = dur
    return ids, durations


def build_split_dag(tasks, deps) -> SplitDAG:
    """Build the node-split weighted DAG from tasks and precedence pairs.

    Parameters
    ----------
    tasks:
        Either a ``{task_id: duration}`` mapping, or an iterable of
        ``{"id": ..., "duration": ...}`` dicts / ``(id, duration)`` pairs.
    deps:
        Iterable of ``(i, j)`` pairs meaning "task ``i`` must finish before
        task ``j`` may start". Every id referenced must appear in ``tasks``.

    The construction never creates a cycle on its own; a cycle can only come
    from the precedence pairs and is detected later when an algorithm tries to
    order the graph topologically (see :func:`reelpath.critical_path.topological_sort`).
    """
    ids, durations = _normalise_tasks(tasks)
    id_set = set(ids)

    dep_list = [(i, j) for (i, j) in deps]
    for i, j in dep_list:
        if i not in id_set:
            raise ValueError(f"dependency references unknown task {i!r}")
        if j not in id_set:
            raise ValueError(f"dependency references unknown task {j!r}")
        if i == j:
            raise CycleError(f"task {i!r} depends on itself")

    # Vertex layout: 0 = s, 1 = t, then (i_in, i_out) per task in id order.
    source = 0
    target = 1
    num_vertices = 2 * len(ids) + 2
    g = Graph(num_vertices)
    labels = ["s", "t"] + [""] * (num_vertices - 2)

    task_in: dict[Hashable, int] = {}
    task_out: dict[Hashable, int] = {}
    next_idx = 2
    for tid in ids:
        task_in[tid] = next_idx
        task_out[tid] = next_idx + 1
        labels[next_idx] = f"{tid}_in"
        labels[next_idx + 1] = f"{tid}_out"
        next_idx += 2

    # Duration edges: i_in --d(i)--> i_out.
    for tid in ids:
        g.add_edge(task_in[tid], task_out[tid], durations[tid])

    # Precedence edges: i_out --0--> j_in.
    has_pred = {tid: False for tid in ids}
    has_succ = {tid: False for tid in ids}
    for i, j in dep_list:
        g.add_edge(task_out[i], task_in[j], 0)
        has_succ[i] = True
        has_pred[j] = True

    # Source edges (tasks with no prerequisite) and sink edges (terminal tasks).
    for tid in ids:
        if not has_pred[tid]:
            g.add_edge(source, task_in[tid], 0)
        if not has_succ[tid]:
            g.add_edge(task_out[tid], target, 0)

    return SplitDAG(
        graph=g,
        source=source,
        target=target,
        task_ids=ids,
        task_in=task_in,
        task_out=task_out,
        durations=durations,
        vertex_label=labels,
    )
