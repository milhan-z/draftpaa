"""Hand-verified tiny instances (README s2.5, s8)."""

import pytest

from reelpath import build_split_dag, solve
from reelpath.critical_path import topological_sort
from reelpath.graph import CycleError


def test_shoot_then_edit_makespan_is_9():
    """The README sanity instance: Shoot(5) -> Edit(4) => makespan 9."""
    tasks = {"Shoot": 5, "Edit": 4}
    deps = [("Shoot", "Edit")]
    dag = build_split_dag(tasks, deps)

    res = solve(dag, "A")
    assert res.makespan == 9
    assert res.critical_path == ["Shoot", "Edit"]
    # Both tasks lie on the only path, so both are critical (zero slack).
    assert res.schedule["Shoot"].slack == 0
    assert res.schedule["Edit"].slack == 0
    assert res.schedule["Shoot"].es == 0
    assert res.schedule["Edit"].es == 5
    assert res.schedule["Edit"].ef == 9


def test_diamond_dag_hand_computed():
    """Diamond A->{B,C}->D. Durations A2 B3 C5 D4 => longest path A,C,D = 11."""
    tasks = {"A": 2, "B": 3, "C": 5, "D": 4}
    deps = [("A", "B"), ("A", "C"), ("B", "D"), ("C", "D")]
    dag = build_split_dag(tasks, deps)

    res = solve(dag, "A")
    assert res.makespan == 11
    assert res.critical_path == ["A", "C", "D"]
    # B is the slack task: ES=2, LS=4 => slack 2; it is NOT critical.
    assert res.schedule["B"].slack == 2
    assert res.schedule["B"].critical is False
    assert sorted(res.critical_ids) == ["A", "C", "D"]
    # The critical chain's durations must sum to the makespan.
    assert sum(tasks[t] for t in res.critical_path) == res.makespan


def test_two_algorithms_agree_on_diamond():
    tasks = {"A": 2, "B": 3, "C": 5, "D": 4}
    deps = [("A", "B"), ("A", "C"), ("B", "D"), ("C", "D")]
    dag = build_split_dag(tasks, deps)
    assert solve(dag, "A").makespan == solve(dag, "B").makespan == 11


def test_cyclic_instance_is_rejected():
    """A precedence cycle X->Y->Z->X is infeasible and must raise CycleError."""
    tasks = {"X": 1, "Y": 1, "Z": 1}
    deps = [("X", "Y"), ("Y", "Z"), ("Z", "X")]
    dag = build_split_dag(tasks, deps)  # construction itself is fine...

    with pytest.raises(CycleError):
        topological_sort(dag.graph)      # ...the cycle is caught when ordering
    with pytest.raises(CycleError):
        solve(dag, "A")                  # ...and surfaces through the solver


def test_self_dependency_is_rejected():
    with pytest.raises(CycleError):
        build_split_dag({"A": 3}, [("A", "A")])


def test_single_task():
    dag = build_split_dag({"Only": 7}, [])
    res = solve(dag, "A")
    assert res.makespan == 7
    assert res.critical_path == ["Only"]
