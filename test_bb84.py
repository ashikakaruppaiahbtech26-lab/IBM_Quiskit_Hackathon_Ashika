"""Run with:  pytest -q"""
import numpy as np
import bb84


def test_no_eve_gives_identical_keys():
    r = bb84.run_bb84(n=300, eve=False, seed=1)
    assert r["error_rate"] == 0.0
    assert len(r["alice_key"]) > 100         


def test_eve_causes_about_25_percent_errors():
    r = bb84.run_bb84(n=3000, eve=True, seed=1)
    assert 0.20 < r["error_rate"] < 0.30


def test_results_are_reproducible():
    a = bb84.run_bb84(n=200, eve=True, seed=7)
    b = bb84.run_bb84(n=200, eve=True, seed=7)
    assert np.array_equal(a["bob_bits"], b["bob_bits"])


def test_partial_eve_scales_error():
    r = bb84.run_bb84(n=3000, eve=True, eve_fraction=0.5, seed=3)
    assert 0.07 < r["error_rate"] < 0.18      # ~12.5%


def test_noise_creates_errors_without_eve():
    r = bb84.run_bb84(n=3000, eve=False, noise=0.05, seed=2)
    assert 0.02 < r["error_rate"] < 0.09
