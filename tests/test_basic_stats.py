"""
Unit tests for basic_stats module.

Run with: pytest tests/test_basic_stats.py -v
"""

import sys
import os
import pytest

# Allow importing from src/ without installing the package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from stats.basic_stats import (
    calculate_mean,
    calculate_std_dev,
    calculate_range,
    calculate_control_limits,
    calculate_cp,
    calculate_cpk,
    interpret_cpk,
)


class TestCalculateMean:
    def test_simple_mean(self):
        assert calculate_mean([500, 502, 501, 498, 505]) == pytest.approx(501.2)

    def test_single_value(self):
        assert calculate_mean([10]) == 10

    def test_empty_raises_error(self):
        with pytest.raises(ValueError):
            calculate_mean([])


class TestCalculateStdDev:
    def test_sample_std_dev(self):
        # Known dataset with pre-verified sample std dev
        data = [2, 4, 4, 4, 5, 5, 7, 9]
        assert calculate_std_dev(data, sample=True) == pytest.approx(2.138, abs=0.01)

    def test_single_value_raises_error(self):
        with pytest.raises(ValueError):
            calculate_std_dev([5], sample=True)

    def test_population_std_dev(self):
        data = [2, 4, 4, 4, 5, 5, 7, 9]
        assert calculate_std_dev(data, sample=False) == pytest.approx(2.0, abs=0.01)


class TestCalculateRange:
    def test_simple_range(self):
        assert calculate_range([500, 502, 501, 498, 505]) == 7

    def test_empty_raises_error(self):
        with pytest.raises(ValueError):
            calculate_range([])


class TestControlLimits:
    def test_control_limits_structure(self):
        data = [500, 502, 501, 498, 505]
        limits = calculate_control_limits(data)
        assert "ucl" in limits
        assert "centerline" in limits
        assert "lcl" in limits
        assert limits["ucl"] > limits["centerline"] > limits["lcl"]

    def test_centerline_equals_mean(self):
        data = [500, 502, 501, 498, 505]
        limits = calculate_control_limits(data)
        assert limits["centerline"] == pytest.approx(calculate_mean(data))


class TestCp:
    def test_cp_calculation(self):
        data = [500, 502, 501, 498, 505]
        cp = calculate_cp(data, usl=510, lsl=490)
        assert cp > 0

    def test_invalid_spec_limits_raises_error(self):
        data = [500, 502, 501, 498, 505]
        with pytest.raises(ValueError):
            calculate_cp(data, usl=490, lsl=510)  # USL < LSL


class TestCpk:
    def test_cpk_centered_process(self):
        # Process centered exactly between spec limits
        data = [500] * 10  # zero variation edge case handled separately
        # Using slightly varied data to avoid zero std dev
        data = [499, 500, 501, 500, 499, 501, 500, 500, 501, 499]
        cpk = calculate_cpk(data, usl=510, lsl=490)
        assert cpk > 0

    def test_invalid_spec_limits_raises_error(self):
        data = [500, 502, 501, 498, 505]
        with pytest.raises(ValueError):
            calculate_cpk(data, usl=490, lsl=510)


class TestInterpretCpk:
    def test_poor_capability(self):
        assert "Poor" in interpret_cpk(0.8)

    def test_marginal_capability(self):
        assert "Marginal" in interpret_cpk(1.1)

    def test_acceptable_capability(self):
        assert "Acceptable" in interpret_cpk(1.5)

    def test_excellent_capability(self):
        assert "Excellent" in interpret_cpk(1.8)