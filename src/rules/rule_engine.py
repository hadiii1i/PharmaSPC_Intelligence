"""
SPC Rule Detection Engine for PharmaSPC Intelligence.

Implements Western Electric (WECO) rules for detecting
out-of-control conditions in pharmaceutical manufacturing processes.

Rules implemented:
    Rule 1: One point beyond 3-sigma control limits (UCL/LCL)
    Rule 2: Seven consecutive points trending up or down
    Rule 3: Eight consecutive points on one side of the centerline
"""

from typing import List, Dict


def detect_control_limit_violations(
    measurements: List[float],
    ucl: float,
    lcl: float,
) -> Dict:
    """
    Rule 1: Detect points outside Upper or Lower Control Limits.

    A single point beyond the 3-sigma limits is a strong signal
    of a special cause — the process is out of statistical control.

    Args:
        measurements: List of numeric measurement values.
        ucl: Upper Control Limit.
        lcl: Lower Control Limit.

    Returns:
        Dictionary with keys:
            - 'detected' (bool): True if any violation found.
            - 'violations' (list): Indices of out-of-control points (1-based).
            - 'direction' (list): 'above UCL' or 'below LCL' for each violation.
    """
    violations = []
    directions = []

    for i, value in enumerate(measurements):
        if value > ucl:
            violations.append(i + 1)
            directions.append("above UCL")
        elif value < lcl:
            violations.append(i + 1)
            directions.append("below LCL")

    return {
        "detected": len(violations) > 0,
        "violations": violations,
        "direction": directions,
    }


def detect_trend(
    measurements: List[float],
    run_length: int = 7,
) -> Dict:
    """
    Rule 2: Detect consecutive points trending in one direction.

    Seven (or more) consecutive points continuously increasing
    or decreasing indicates a process drift — likely due to
    tool wear, gradual material change, or environmental drift.

    Args:
        measurements: List of numeric measurement values.
        run_length: Minimum consecutive points required to flag a trend.
                    Standard SPC practice uses 7.

    Returns:
        Dictionary with keys:
            - 'detected' (bool): True if a trend is found.
            - 'start_index' (int or None): 1-based start of trend.
            - 'end_index' (int or None): 1-based end of trend.
            - 'direction' (str or None): 'increasing' or 'decreasing'.
    """
    if len(measurements) < run_length:
        return {"detected": False, "start_index": None,
                "end_index": None, "direction": None}

    for i in range(len(measurements) - run_length + 1):
        window = measurements[i: i + run_length]

        # Check strictly increasing
        if all(window[j] < window[j + 1] for j in range(len(window) - 1)):
            return {
                "detected": True,
                "start_index": i + 1,
                "end_index": i + run_length,
                "direction": "increasing",
            }

        # Check strictly decreasing
        if all(window[j] > window[j + 1] for j in range(len(window) - 1)):
            return {
                "detected": True,
                "start_index": i + 1,
                "end_index": i + run_length,
                "direction": "decreasing",
            }

    return {"detected": False, "start_index": None,
            "end_index": None, "direction": None}


def detect_process_shift(
    measurements: List[float],
    centerline: float,
    run_length: int = 8,
) -> Dict:
    """
    Rule 3: Detect consecutive points on one side of the centerline.

    Eight (or more) consecutive points above or below the process mean
    indicates the process average has shifted — a sustained change
    in the process level.

    Args:
        measurements: List of numeric measurement values.
        centerline: The process mean (center line on the control chart).
        run_length: Minimum consecutive points on one side to flag a shift.
                    Standard SPC practice uses 8.

    Returns:
        Dictionary with keys:
            - 'detected' (bool): True if a shift is found.
            - 'start_index' (int or None): 1-based start of shift.
            - 'end_index' (int or None): 1-based end of shift.
            - 'direction' (str or None): 'above mean' or 'below mean'.
    """
    if len(measurements) < run_length:
        return {"detected": False, "start_index": None,
                "end_index": None, "direction": None}

    for i in range(len(measurements) - run_length + 1):
        window = measurements[i: i + run_length]

        if all(v > centerline for v in window):
            return {
                "detected": True,
                "start_index": i + 1,
                "end_index": i + run_length,
                "direction": "above mean",
            }

        if all(v < centerline for v in window):
            return {
                "detected": True,
                "start_index": i + 1,
                "end_index": i + run_length,
                "direction": "below mean",
            }

    return {"detected": False, "start_index": None,
            "end_index": None, "direction": None}


def run_all_rules(
    measurements: List[float],
    ucl: float,
    lcl: float,
    centerline: float,
) -> Dict:
    """
    Run all three SPC rules against the dataset and return combined results.

    Args:
        measurements: List of numeric measurement values.
        ucl: Upper Control Limit.
        lcl: Lower Control Limit.
        centerline: Process mean.

    Returns:
        Dictionary with keys 'rule1', 'rule2', 'rule3', each containing
        the result dict from the corresponding detection function,
        plus 'any_detected' (bool) indicating if any rule fired.
    """
    rule1 = detect_control_limit_violations(measurements, ucl, lcl)
    rule2 = detect_trend(measurements)
    rule3 = detect_process_shift(measurements, centerline)

    return {
        "rule1": rule1,
        "rule2": rule2,
        "rule3": rule3,
        "any_detected": rule1["detected"] or rule2["detected"] or rule3["detected"],
    }