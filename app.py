"""
PharmaSPC Intelligence - Streamlit Dashboard

Main application entry point.
Connects all backend modules into a single interactive dashboard.

Run with: streamlit run app.py
"""

import streamlit as st
import sys
import os

# Allow importing from src/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from data.data_loader import load_csv, extract_measurements
from stats.basic_stats import (
    calculate_mean,
    calculate_std_dev,
    calculate_range,
    calculate_control_limits,
    calculate_cp,
    calculate_cpk,
    interpret_cpk,
)
from charts.spc_charts import create_xbar_chart, create_r_chart, create_histogram

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="PharmaSPC Intelligence",
    page_icon="💊",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("💊 PharmaSPC Intelligence")
st.caption("Statistical Process Control for Pharmaceutical Manufacturing")
st.divider()

# ---------------------------------------------------------------------------
# Sidebar — user inputs
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Configuration")

    uploaded_file = st.file_uploader(
        "Upload Measurement CSV",
        type=["csv"],
        help="CSV file must contain at least one numeric column.",
    )

    measurement_column = st.text_input(
        "Measurement Column Name",
        value="weight_mg",
        help="Exact name of the column containing measurements.",
    )

    st.subheader("Specification Limits")
    usl = st.number_input("Upper Specification Limit (USL)", value=510.0, step=0.1)
    lsl = st.number_input("Lower Specification Limit (LSL)", value=490.0, step=0.1)

    st.subheader("R Chart Settings")
    subgroup_size = st.selectbox(
        "Subgroup Size",
        options=[2, 3, 4, 5, 6, 7, 8, 9, 10],
        index=3,  # default = 5
        help="Number of measurements per subgroup for R chart.",
    )

# ---------------------------------------------------------------------------
# Main content — only shown after file upload
# ---------------------------------------------------------------------------
if uploaded_file is None:
    st.info("👈 Upload a CSV file from the sidebar to begin analysis.")

    # Show sample data format
    st.subheader("Expected CSV Format")
    st.code(
        "sample_id,weight_mg\n"
        "1,500.2\n"
        "2,501.5\n"
        "3,499.8\n"
        "...",
        language="text",
    )
    st.stop()

# ---------------------------------------------------------------------------
# Load and validate data
# ---------------------------------------------------------------------------
try:
    df, warnings = load_csv(uploaded_file, measurement_column)
except (FileNotFoundError, ValueError) as e:
    st.error(f"❌ Data loading error: {e}")
    st.stop()

# Show warnings if any
for w in warnings:
    st.warning(f"⚠️ {w}")

measurements = extract_measurements(df, measurement_column)

# ---------------------------------------------------------------------------
# Section 1: Data Preview
# ---------------------------------------------------------------------------
st.subheader("📋 Data Preview")
col1, col2 = st.columns([2, 1])

with col1:
    st.dataframe(df, use_container_width=True, height=250)

with col2:
    st.metric("Total Measurements", len(measurements))
    st.metric("Column", measurement_column)
    if warnings:
        st.metric("Warnings", len(warnings))

st.divider()

# ---------------------------------------------------------------------------
# Section 2: Statistical Summary
# ---------------------------------------------------------------------------
st.subheader("📊 Statistical Summary")

mean_val = calculate_mean(measurements)
std_val = calculate_std_dev(measurements)
range_val = calculate_range(measurements)
limits = calculate_control_limits(measurements)

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Mean", f"{mean_val:.3f}")
col2.metric("Std Dev", f"{std_val:.3f}")
col3.metric("Range", f"{range_val:.3f}")
col4.metric("UCL", f"{limits['ucl']:.3f}")
col5.metric("LCL", f"{limits['lcl']:.3f}")

st.divider()

# ---------------------------------------------------------------------------
# Section 3: Process Capability
# ---------------------------------------------------------------------------
st.subheader("🎯 Process Capability")

if usl <= lsl:
    st.error("❌ USL must be greater than LSL. Please fix specification limits in the sidebar.")
else:
    try:
        cp_val = calculate_cp(measurements, usl, lsl)
        cpk_val = calculate_cpk(measurements, usl, lsl)
        interpretation = interpret_cpk(cpk_val)

        col1, col2, col3 = st.columns(3)
        col1.metric("Cp", f"{cp_val:.3f}")
        col2.metric("Cpk", f"{cpk_val:.3f}")

        with col3:
            if cpk_val >= 1.33:
                st.success(f"✅ {interpretation}")
            elif cpk_val >= 1.0:
                st.warning(f"⚠️ {interpretation}")
            else:
                st.error(f"❌ {interpretation}")

    except ValueError as e:
        st.error(f"❌ Capability calculation error: {e}")

st.divider()

# ---------------------------------------------------------------------------
# Section 4: SPC Charts
# ---------------------------------------------------------------------------
st.subheader("📈 SPC Charts")

tab1, tab2, tab3 = st.tabs(["X-Bar Chart", "R Chart", "Histogram"])

with tab1:
    fig_xbar = create_xbar_chart(
        measurements=measurements,
        ucl=limits["ucl"],
        centerline=limits["centerline"],
        lcl=limits["lcl"],
        title=f"X-Bar Chart — {measurement_column}",
        y_label=measurement_column,
    )
    st.plotly_chart(fig_xbar, use_container_width=True)

with tab2:
    try:
        fig_r = create_r_chart(
            measurements=measurements,
            subgroup_size=subgroup_size,
            title=f"R Chart — {measurement_column} (subgroup size = {subgroup_size})",
            y_label="Range",
        )
        st.plotly_chart(fig_r, use_container_width=True)
    except ValueError as e:
        st.warning(f"⚠️ Cannot generate R Chart: {e}")

with tab3:
    fig_hist = create_histogram(
        measurements=measurements,
        usl=usl if usl else None,
        lsl=lsl if lsl else None,
        title=f"Distribution — {measurement_column}",
        x_label=measurement_column,
    )
    st.plotly_chart(fig_hist, use_container_width=True)

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.divider()
st.caption("PharmaSPC Intelligence | Phase 1 MVP | Built with Python & Streamlit")