"""
Basic statistical calculations module for SPC analysis.

This module provides core statistical functions used throughout
the PharmaSPC Intelligence system: central tendency, dispersion,
control limits, and process capability indices (Cp, Cpk).
"""

from typing import List
import math


def calculate_mean(data: List[float]) -> float:
    """
    Calculate the arithmetic mean of a dataset.

    Args:
        data: List of numeric measurements.

    Returns:
        The mean value.

    Raises:
        ValueError: If data is empty.
    """
    if not data:
        raise ValueError("Cannot calculate mean of empty dataset")
    return sum(data) / len(data)


def calculate_std_dev(data: List[float], sample: bool = True) -> float:
    """
    Calculate the standard deviation of a dataset.

    Args:
        data: List of numeric measurements.
        sample: If True, uses sample standard deviation (n-1 divisor).
                If False, uses population standard deviation (n divisor).
                Sample std dev is standard practice in SPC.

    Returns:
        The standard deviation.

    Raises:
        ValueError: If data has fewer than 2 points (sample mode)
                    or is empty (population mode).
    """
    n = len(data)
    if sample and n < 2:
        raise ValueError("Sample standard deviation requires at least 2 data points")
    if not sample and n < 1:
        raise ValueError("Cannot calculate standard deviation of empty dataset")

    mean = calculate_mean(data)
    squared_diffs = [(x - mean) ** 2 for x in data]
    divisor = (n - 1) if sample else n

    return math.sqrt(sum(squared_diffs) / divisor)


def calculate_range(data: List[float]) -> float:
    """
    Calculate the range (max - min) of a dataset.

    Args:
        data: List of numeric measurements.

    Returns:
        The range value.

    Raises:
        ValueError: If data is empty.
    """
    if not data:
        raise ValueError("Cannot calculate range of empty dataset")
    return max(data) - min(data)


def calculate_control_limits(data: List[float], sigma_multiplier: float = 3.0) -> dict:
    """
    Calculate SPC control limits (UCL, Centerline, LCL) using
    the standard mean +/- k*sigma method.

    Args:
        data: List of numeric measurements.
        sigma_multiplier: Number of standard deviations for control limits.
                           Standard SPC practice uses 3.0 (3-sigma limits).

    Returns:
        Dictionary with keys: 'ucl', 'centerline', 'lcl'.

    Raises:
        ValueError: If data has fewer than 2 points.
    """
    mean = calculate_mean(data)
    std_dev = calculate_std_dev(data, sample=True)

    return {
        "ucl": mean + sigma_multiplier * std_dev,
        "centerline": mean,
        "lcl": mean - sigma_multiplier * std_dev,
    }


def calculate_cp(data: List[float], usl: float, lsl: float) -> float:
    """
    Calculate process capability index Cp.

    Cp measures whether the process spread fits within specification
    limits, WITHOUT considering how centered the process is.

    Formula: Cp = (USL - LSL) / (6 * sigma)

    Args:
        data: List of numeric measurements.
        usl: Upper Specification Limit.
        lsl: Lower Specification Limit.

    Returns:
        The Cp value.

    Raises:
        ValueError: If USL <= LSL, or data has fewer than 2 points.
    """
    if usl <= lsl:
        raise ValueError("USL must be greater than LSL")

    std_dev = calculate_std_dev(data, sample=True)
    if std_dev == 0:
        raise ValueError("Cannot calculate Cp: standard deviation is zero")

    return (usl - lsl) / (6 * std_dev)


def calculate_cpk(data: List[float], usl: float, lsl: float) -> float:
    """
    Calculate process capability index Cpk.

    Unlike Cp, Cpk accounts for process centering — it measures
    capability relative to the nearest specification limit.

    Formula: Cpk = min[(USL - mean) / (3*sigma), (mean - LSL) / (3*sigma)]

    Args:
        data: List of numeric measurements.
        usl: Upper Specification Limit.
        lsl: Lower Specification Limit.

    Returns:
        The Cpk value.

    Raises:
        ValueError: If USL <= LSL, or data has fewer than 2 points.
    """
    if usl <= lsl:
        raise ValueError("USL must be greater than LSL")

    mean = calculate_mean(data)
    std_dev = calculate_std_dev(data, sample=True)
    if std_dev == 0:
        raise ValueError("Cannot calculate Cpk: standard deviation is zero")

    cpu = (usl - mean) / (3 * std_dev)
    cpl = (mean - lsl) / (3 * std_dev)

    return min(cpu, cpl)


def interpret_cpk(cpk: float) -> str:
    """
    Provide a human-readable interpretation of a Cpk value.

    Interpretation thresholds follow common pharmaceutical
    quality engineering conventions:
        Cpk < 1.0            -> Poor capability
        1.0 <= Cpk < 1.33     -> Marginal capability
        1.33 <= Cpk < 1.67    -> Acceptable capability
        Cpk >= 1.67           -> Excellent capability

    Args:
        cpk: The calculated Cpk value.

    Returns:
        A short interpretation string.
    """
    if cpk < 1.0:
        return "Poor capability - process is not capable of meeting specifications"
    elif cpk < 1.33:
        return "Marginal capability - process needs improvement"
    elif cpk < 1.67:
        return "Acceptable capability - process meets requirements"
    else:
        return "Excellent capability - process is well controlled"