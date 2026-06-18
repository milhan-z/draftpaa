"""Cross-check: Algorithm A and Algorithm B must agree on every instance.

For many seeds and sizes we assert:

* ``makespan_A == makespan_B`` exactly (integer durations => exact equality);
* the backtracked critical path's durations sum to the makespan;
* every task flagged critical (slack == 0) really has zero slack.
"""

import pytest

from reelpath import analyze, bellman_ford, critical_path, generate_split_dag

SIZES = [10, 25, 50, 100, 200, 500]
SEEDS = [1, 2, 3, 4, 5]


@pytest.mark.parametrize("n", SIZES)
@pytest.mark.parametrize("seed", SEEDS)
def test_algorithms_agree(n, seed):
    dag, tg = generate_split_dag(n, avg_out_degree=3, seed=seed)

    res_a = analyze(dag, critical_path.longest_path)
    res_b = analyze(dag, bellman_ford.longest_path)

    # Core cross-check: identical makespan.
    assert res_a.makespan == res_b.makespan

    # The critical chain really is a maximum-weight path.
    durations = tg.durations()
    chain_total = sum(durations[t] for t in res_a.critical_path)
    assert chain_total == res_a.makespan

    # Every "critical" task genuinely has zero slack.
    for tid in res_a.critical_ids:
        assert res_a.schedule[tid].slack == 0

    # ES/EF consistency: EF = ES + duration for every task.
    for tid, row in res_a.schedule.items():
        assert row.ef == row.es + durations[tid]
        assert row.slack >= 0


@pytest.mark.parametrize("seed", SEEDS)
def test_critical_path_endpoints(seed):
    """A critical path must start at a source task and end at a terminal task."""
    dag, tg = generate_split_dag(60, avg_out_degree=3, seed=seed)
    res = analyze(dag, critical_path.longest_path)
    assert len(res.critical_path) >= 1
    # First task has earliest start 0; last task finishes exactly at the makespan.
    first, last = res.critical_path[0], res.critical_path[-1]
    assert res.schedule[first].es == 0
    assert res.schedule[last].ef == res.makespan
