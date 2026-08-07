"""
Unit tests for rule_engine module.

Run with: pytest tests/test_rule_engine.py -v
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from rules.rule_engine import (
    detect_control_limit_violations,
    detect_trend,
    detect_process_shift,
    run_all_rules,
)

CENTERLINE = 500.0
UCL = 506.0
LCL = 494.0

BASE_DATA = [500.2, 501.5, 499.8, 502.1, 498.7,
             500.9, 501.1, 499.2, 500.5, 501.8]


class TestControlLimitViolations:
    def test_no_violations(self):
        result = detect_control_limit_violations(BASE_DATA, UCL, LCL)
        assert result["detected"] is False
        assert result["violations"] == []

    def test_detects_point_above_ucl(self):
        data = BASE_DATA.copy()
        data[3] = 510.0  # above UCL
        result = detect_control_limit_violations(data, UCL, LCL)
        assert result["detected"] is True
        assert 4 in result["violations"]
        assert "above UCL" in result["direction"]

    def test_detects_point_below_lcl(self):
        data = BASE_DATA.copy()
        data[5] = 490.0  # below LCL
        result = detect_control_limit_violations(data, UCL, LCL)
        assert result["detected"] is True
        assert 6 in result["violations"]
        assert "below LCL" in result["direction"]


class TestTrendDetection:
    def test_no_trend_in_normal_data(self):
        result = detect_trend(BASE_DATA)
        assert result["detected"] is False

    def test_detects_increasing_trend(self):
        data = [500, 501, 502, 503, 504, 505, 506, 500]
        result = detect_trend(data, run_length=7)
        assert result["detected"] is True
        assert result["direction"] == "increasing"

    def test_detects_decreasing_trend(self):
        data = [506, 505, 504, 503, 502, 501, 500, 506]
        result = detect_trend(data, run_length=7)
        assert result["detected"] is True
        assert result["direction"] == "decreasing"

    def test_insufficient_data(self):
        result = detect_trend([500, 501, 502], run_length=7)
        assert result["detected"] is False


class TestProcessShift:
    def test_no_shift_in_normal_data(self):
        result = detect_process_shift(BASE_DATA, CENTERLINE)
        assert result["detected"] is False

    def test_detects_shift_above_mean(self):
        data = [502, 503, 501, 502, 503, 501, 502, 503, 500]
        result = detect_process_shift(data, centerline=500.0, run_length=8)
        assert result["detected"] is True
        assert result["direction"] == "above mean"

    def test_detects_shift_below_mean(self):
        data = [498, 497, 499, 498, 497, 499, 498, 497, 500]
        result = detect_process_shift(data, centerline=500.0, run_length=8)
        assert result["detected"] is True
        assert result["direction"] == "below mean"


class TestRunAllRules:
    def test_returns_all_rule_keys(self):
        result = run_all_rules(BASE_DATA, UCL, LCL, CENTERLINE)
        assert "rule1" in result
        assert "rule2" in result
        assert "rule3" in result
        assert "any_detected" in result

    def test_clean_data_no_detection(self):
        result = run_all_rules(BASE_DATA, UCL, LCL, CENTERLINE)
        assert result["any_detected"] is False