"""
Unit tests for data_loader module.

Run with: pytest tests/test_data_loader.py -v
"""

import sys
import os
import pytest
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from data.data_loader import load_csv, extract_measurements


# Path to the sample CSV file used in tests
SAMPLE_CSV = os.path.join(
    os.path.dirname(__file__), "..", "data", "samples", "tablet_weight.csv"
)


class TestLoadCsv:
    def test_loads_valid_file(self):
        df, warnings = load_csv(SAMPLE_CSV, "weight_mg")
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 25

    def test_no_warnings_on_clean_data(self):
        _, warnings = load_csv(SAMPLE_CSV, "weight_mg")
        assert len(warnings) == 0

    def test_file_not_found_raises_error(self):
        with pytest.raises(FileNotFoundError):
            load_csv("nonexistent.csv", "weight_mg")

    def test_wrong_column_raises_error(self):
        with pytest.raises(ValueError):
            load_csv(SAMPLE_CSV, "wrong_column")

    def test_missing_values_trigger_warning(self, tmp_path):
        # Create a temporary CSV with a missing value
        csv_content = "sample_id,weight_mg\n1,500\n2,\n3,501\n"
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(csv_content)

        df, warnings = load_csv(str(csv_file), "weight_mg")
        assert len(df) == 2  # one row removed
        assert any("missing" in w.lower() for w in warnings)


class TestExtractMeasurements:
    def test_returns_list(self):
        df, _ = load_csv(SAMPLE_CSV, "weight_mg")
        measurements = extract_measurements(df, "weight_mg")
        assert isinstance(measurements, list)
        assert len(measurements) == 25

    def test_values_are_numeric(self):
        df, _ = load_csv(SAMPLE_CSV, "weight_mg")
        measurements = extract_measurements(df, "weight_mg")
        assert all(isinstance(v, float) for v in measurements)