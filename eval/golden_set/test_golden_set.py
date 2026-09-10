"""
Pytest integration for Golden-Set regression evaluations.
"""

from eval.golden_set.run_evals import run_golden_set_evals


def test_golden_set_regression():
    assert run_golden_set_evals() is True
