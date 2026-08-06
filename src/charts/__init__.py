"""
SPC chart generation module for PharmaSPC Intelligence.

Generates interactive Plotly charts for Statistical Process Control:
- X-Bar Chart: monitors process mean over time
- R Chart: monitors process variation (range) over time
- Histogram: shows data distribution with specification limits
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Optional


def create_xbar_chart(
    measurements: List[float],
    ucl: float,
    centerline: float,
    lcl: float,
    title: str = "X-Bar Control Chart",
    y_label: str = "Measurement",
) -> go.Figure:
    """
    Create an X-Bar control chart.

    Plots each individual measurement against control limits.
    Points outside UCL or LCL are highlighted in red.

    Args:
        measurements: List of numeric measurement values.
        ucl: Upper Control Limit.
        centerline: Process mean (center line).
        lcl: Lower Control Limit.
        title: Chart title.
        y_label: Y-axis label (e.g. 'Weight (mg)').

    Returns:
        A Plotly Figure object.
    """
    x_values = list(range(1, len(measurements) + 1))

    # Identify out-of-control points
    out_of_control = [
        m for m in measurements if m > ucl or m < lcl
    ]
    point_colors = [
        "red" if (m > ucl or m < lcl) else "steelblue"
        for m in measurements
    ]

    fig = go.Figure()

    # Measurement line
    fig.add_trace(go.Scatter(
        x=x_values,
        y=measurements,
        mode="lines+markers",
        name="Measurements",
        line=dict(color="steelblue", width=1.5),
        marker=dict(color=point_colors, size=7),
    ))

    # UCL line
    fig.add_trace(go.Scatter(
        x=x_values,
        y=[ucl] * len(measurements),
        mode="lines",
        name=f"UCL ({ucl:.3f})",
        line=dict(color="red", width=1.5, dash="dash"),
    ))

    # Centerline
    fig.add_trace(go.Scatter(
        x=x_values,
        y=[centerline] * len(measurements),
        mode="lines",
        name=f"Mean ({centerline:.3f})",
        line=dict(color="green", width=1.5, dash="dot"),
    ))

    # LCL line
    fig.add_trace(go.Scatter(
        x=x_values,
        y=[lcl] * len(measurements),
        mode="lines",
        name=f"LCL ({lcl:.3f})",
        line=dict(color="red", width=1.5, dash="dash"),
    ))

    fig.update_layout(
        title=dict(text=title, font=dict(size=16)),
        xaxis_title="Sample Number",
        yaxis_title=y_label,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis=dict(showgrid=True, gridcolor="lightgrey"),
        yaxis=dict(showgrid=True, gridcolor="lightgrey"),
    )

    return fig


def create_r_chart(
    measurements: List[float],
    subgroup_size: int = 5,
    title: str = "R Control Chart",
    y_label: str = "Range",
) -> go.Figure:
    """
    Create an R (Range) control chart.

    Divides measurements into subgroups and plots the range
    of each subgroup to monitor process variation.

    Control limits are calculated using standard SPC d2/D3/D4 constants.

    Args:
        measurements: List of numeric measurement values.
        subgroup_size: Number of measurements per subgroup (default 5).
        title: Chart title.
        y_label: Y-axis label.

    Returns:
        A Plotly Figure object.

    Raises:
        ValueError: If there are fewer than 2 complete subgroups.
    """
    # Split into subgroups
    subgroups = [
        measurements[i: i + subgroup_size]
        for i in range(0, len(measurements), subgroup_size)
        if len(measurements[i: i + subgroup_size]) == subgroup_size
    ]

    if len(subgroups) < 2:
        raise ValueError(
            f"Not enough data for R chart. "
            f"Need at least {2 * subgroup_size} measurements "
            f"for subgroup size {subgroup_size}."
        )

    ranges = [max(sg) - min(sg) for sg in subgroups]
    r_bar = sum(ranges) / len(ranges)

    # SPC constants for R chart (based on subgroup size)
    # Source: ASTM SPC constants table
    d2_constants = {2: 1.128, 3: 1.693, 4: 2.059, 5: 2.326,
                    6: 2.534, 7: 2.704, 8: 2.847, 9: 2.970, 10: 3.078}
    D3_constants = {2: 0, 3: 0, 4: 0, 5: 0,
                    6: 0, 7: 0.076, 8: 0.136, 9: 0.184, 10: 0.223}
    D4_constants = {2: 3.267, 3: 2.574, 4: 2.282, 5: 2.114,
                    6: 2.004, 7: 1.924, 8: 1.864, 9: 1.816, 10: 1.777}

    n = subgroup_size
    d2 = d2_constants.get(n, 2.326)
    D3 = D3_constants.get(n, 0)
    D4 = D4_constants.get(n, 2.114)

    ucl_r = D4 * r_bar
    lcl_r = D3 * r_bar

    x_values = list(range(1, len(ranges) + 1))
    point_colors = [
        "red" if (r > ucl_r or r < lcl_r) else "darkorange"
        for r in ranges
    ]

    fig = go.Figure()

    # Range line
    fig.add_trace(go.Scatter(
        x=x_values,
        y=ranges,
        mode="lines+markers",
        name="Range",
        line=dict(color="darkorange", width=1.5),
        marker=dict(color=point_colors, size=7),
    ))

    # UCL
    fig.add_trace(go.Scatter(
        x=x_values,
        y=[ucl_r] * len(ranges),
        mode="lines",
        name=f"UCL ({ucl_r:.3f})",
        line=dict(color="red", width=1.5, dash="dash"),
    ))

    # R-bar (centerline)
    fig.add_trace(go.Scatter(
        x=x_values,
        y=[r_bar] * len(ranges),
        mode="lines",
        name=f"R-bar ({r_bar:.3f})",
        line=dict(color="green", width=1.5, dash="dot"),
    ))

    # LCL (only show if > 0)
    if lcl_r > 0:
        fig.add_trace(go.Scatter(
            x=x_values,
            y=[lcl_r] * len(ranges),
            mode="lines",
            name=f"LCL ({lcl_r:.3f})",
            line=dict(color="red", width=1.5, dash="dash"),
        ))

    fig.update_layout(
        title=dict(text=title, font=dict(size=16)),
        xaxis_title="Subgroup Number",
        yaxis_title=y_label,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis=dict(showgrid=True, gridcolor="lightgrey"),
        yaxis=dict(showgrid=True, gridcolor="lightgrey"),
    )

    return fig


def create_histogram(
    measurements: List[float],
    usl: Optional[float] = None,
    lsl: Optional[float] = None,
    title: str = "Measurement Distribution",
    x_label: str = "Measurement",
) -> go.Figure:
    """
    Create a histogram of measurement data with optional spec limit lines.

    Args:
        measurements: List of numeric measurement values.
        usl: Upper Specification Limit (optional, shown as red vertical line).
        lsl: Lower Specification Limit (optional, shown as red vertical line).
        title: Chart title.
        x_label: X-axis label.

    Returns:
        A Plotly Figure object.
    """
    fig = go.Figure()

    fig.add_trace(go.Histogram(
        x=measurements,
        name="Measurements",
        marker_color="steelblue",
        opacity=0.75,
        nbinsx=10,
    ))

    # Add USL line
    if usl is not None:
        fig.add_vline(
            x=usl,
            line=dict(color="red", width=2, dash="dash"),
            annotation_text=f"USL ({usl})",
            annotation_position="top right",
        )

    # Add LSL line
    if lsl is not None:
        fig.add_vline(
            x=lsl,
            line=dict(color="red", width=2, dash="dash"),
            annotation_text=f"LSL ({lsl})",
            annotation_position="top left",
        )

    fig.update_layout(
        title=dict(text=title, font=dict(size=16)),
        xaxis_title=x_label,
        yaxis_title="Frequency",
        bargap=0.05,
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis=dict(showgrid=True, gridcolor="lightgrey"),
        yaxis=dict(showgrid=True, gridcolor="lightgrey"),
    )

    return fig