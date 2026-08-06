"""
Unit tests for spc_charts module.

Run with: pytest tests/test_spc_charts.py -v
"""

import sys
import os
import pytest
import plotly.graph_objects as go

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from charts.spc_charts import create_xbar_chart, create_r_chart, create_histogram


# Sample data representing tablet weight measurements
SAMPLE_DATA = [
    500.2, 501.5, 499.8, 502.1, 498.7,
    503.2, 500.9, 501.1, 499.2, 502.8,
    500.5, 501.8, 499.1, 503.5, 500.3,
    501.2, 498.9, 502.4, 500.7, 501.6,
    499.5, 502.9, 500.1, 501.4, 499.8,
]

UCL = 506.0
CENTERLINE = 501.0
LCL = 496.0


class TestXBarChart:
    def test_returns_figure(self):
        fig = create_xbar_chart(SAMPLE_DATA, UCL, CENTERLINE, LCL)
        assert isinstance(fig, go.Figure)

    def test_has_four_traces(self):
        # measurements + UCL + centerline + LCL
        fig = create_xbar_chart(SAMPLE_DATA, UCL, CENTERLINE, LCL)
        assert len(fig.data) == 4

    def test_custom_title(self):
        fig = create_xbar_chart(
            SAMPLE_DATA, UCL, CENTERLINE, LCL, title="Tablet Weight Chart"
        )
        assert fig.layout.title.text == "Tablet Weight Chart"


class TestRChart:
    def test_returns_figure(self):
        fig = create_r_chart(SAMPLE_DATA, subgroup_size=5)
        assert isinstance(fig, go.Figure)

    def test_correct_number_of_subgroups(self):
        # 25 measurements / 5 per subgroup = 5 subgroups
        fig = create_r_chart(SAMPLE_DATA, subgroup_size=5)
        # First trace is the range line with 5 points
        assert len(fig.data[0].x) == 5

    def test_insufficient_data_raises_error(self):
        with pytest.raises(ValueError):
            create_r_chart([500.0, 501.0, 499.0], subgroup_size=5)


class TestHistogram:
    def test_returns_figure(self):
        fig = create_histogram(SAMPLE_DATA)
        assert isinstance(fig, go.Figure)

    def test_with_spec_limits(self):
        fig = create_histogram(SAMPLE_DATA, usl=510.0, lsl=490.0)
        assert isinstance(fig, go.Figure)

    def test_without_spec_limits(self):
        fig = create_histogram(SAMPLE_DATA)
        # No vertical lines added when no spec limits provided
        assert len(fig.layout.shapes) == 0