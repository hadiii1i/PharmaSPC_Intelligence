"""
PharmaSPC Intelligence - Streamlit Dashboard (Phase 1 - Improved UI)

Run with: streamlit run app.py
"""

import streamlit as st
import sys
import os

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
from rules.rule_engine import run_all_rules
from rules.assistant import generate_recommendations

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="PharmaSPC Intelligence",
    page_icon="💊",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    /* Main background */
    .stApp { background-color: #0f1117; }

    /* Metric cards */
    [data-testid="metric-container"] {
        background-color: #1e2130;
        border: 1px solid #2d3250;
        border-radius: 10px;
        padding: 16px;
    }

    /* Metric label */
    [data-testid="metric-container"] label {
        color: #a0aec0 !important;
        font-size: 0.78rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    /* Metric value */
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #e2e8f0 !important;
        font-size: 1.6rem !important;
        font-weight: 700 !important;
    }

    /* Section headers */
    .section-header {
        font-size: 1.1rem;
        font-weight: 700;
        color: #a0aec0;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 12px;
        padding-bottom: 6px;
        border-bottom: 1px solid #2d3250;
    }

    /* Status badge */
    .badge-excellent {
        background-color: #1a4731;
        color: #68d391;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
    }
    .badge-acceptable {
        background-color: #744210;
        color: #f6ad55;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
    }
    .badge-poor {
        background-color: #742a2a;
        color: #fc8181;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #161b2e;
        border-right: 1px solid #2d3250;
    }
    [data-testid="stSidebar"] .stTextInput input,
    [data-testid="stSidebar"] .stNumberInput input {
        background-color: #1e2130;
        border: 1px solid #2d3250;
        color: #e2e8f0;
        border-radius: 8px;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #1e2130;
        border-radius: 10px;
        padding: 4px;
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: #a0aec0;
        font-weight: 600;
        padding: 8px 20px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2d3250 !important;
        color: #e2e8f0 !important;
    }

    /* Divider */
    hr { border-color: #2d3250; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 💊 PharmaSPC")
    st.markdown("---")

    st.markdown("### 📂 Data Source")
    uploaded_file = st.file_uploader(
        "Upload CSV File",
        type=["csv"],
        help="CSV file must contain at least one numeric measurement column.",
        label_visibility="collapsed",
    )

    st.markdown("### 🏷️ Column")
    measurement_column = st.text_input(
        "Measurement Column Name",
        value="weight_mg",
        label_visibility="collapsed",
        placeholder="e.g. weight_mg",
    )

    st.markdown("---")
    st.markdown("### 📐 Specification Limits")
    col_a, col_b = st.columns(2)
    with col_a:
        usl = st.number_input("USL", value=510.0, step=0.1)
    with col_b:
        lsl = st.number_input("LSL", value=490.0, step=0.1)

    st.markdown("---")
    st.markdown("### ⚙️ R Chart")
    subgroup_size = st.select_slider(
        "Subgroup Size",
        options=[2, 3, 4, 5, 6, 7, 8, 9, 10],
        value=5,
        label_visibility="collapsed",
    )
    st.caption(f"Subgroup size: **{subgroup_size}**")

    st.markdown("---")
    st.caption("PharmaSPC Intelligence · Phase 1")

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown("# 💊 PharmaSPC Intelligence")
st.caption("Statistical Process Control · Pharmaceutical Manufacturing")
st.divider()

# ---------------------------------------------------------------------------
# No file uploaded
# ---------------------------------------------------------------------------
if uploaded_file is None:
    st.markdown("""
    <div style='text-align:center; padding: 60px 0;'>
        <div style='font-size: 3rem;'>📂</div>
        <div style='font-size: 1.3rem; color: #a0aec0; margin-top: 12px;'>
            Upload a CSV file from the sidebar to begin
        </div>
        <div style='font-size: 0.85rem; color: #4a5568; margin-top: 8px;'>
            Supported format: CSV with numeric measurement column
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📋 Expected CSV Format"):
        st.code(
            "sample_id,weight_mg\n1,500.2\n2,501.5\n3,499.8\n...",
            language="text",
        )
    st.stop()

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
try:
    df, warnings = load_csv(uploaded_file, measurement_column)
except (FileNotFoundError, ValueError) as e:
    st.error(f"❌ {e}")
    st.stop()

for w in warnings:
    st.warning(f"⚠️ {w}")

measurements = extract_measurements(df, measurement_column)

# ---------------------------------------------------------------------------
# Section 1: Overview metrics
# ---------------------------------------------------------------------------
st.markdown('<div class="section-header">📋 Data Overview</div>', unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
c1.metric("Total Measurements", len(measurements))
c2.metric("Column", measurement_column)
c3.metric("File", uploaded_file.name)

with st.expander("🔍 View Raw Data"):
    st.dataframe(df, use_container_width=True, height=220)

st.divider()

# ---------------------------------------------------------------------------
# Section 2: Statistical Summary
# ---------------------------------------------------------------------------
mean_val = calculate_mean(measurements)
std_val = calculate_std_dev(measurements)
range_val = calculate_range(measurements)
limits = calculate_control_limits(measurements)

st.markdown('<div class="section-header">📊 Statistical Summary</div>', unsafe_allow_html=True)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Mean", f"{mean_val:.3f}")
c2.metric("Std Dev (σ)", f"{std_val:.3f}")
c3.metric("Range", f"{range_val:.3f}")
c4.metric("UCL", f"{limits['ucl']:.3f}", delta=f"+{limits['ucl']-mean_val:.3f}", delta_color="off")
c5.metric("LCL", f"{limits['lcl']:.3f}", delta=f"{limits['lcl']-mean_val:.3f}", delta_color="off")

st.divider()

# ---------------------------------------------------------------------------
# Section 3: Process Capability
# ---------------------------------------------------------------------------
st.markdown('<div class="section-header">🎯 Process Capability</div>', unsafe_allow_html=True)

if usl <= lsl:
    st.error("❌ USL must be greater than LSL.")
else:
    try:
        cp_val = calculate_cp(measurements, usl, lsl)
        cpk_val = calculate_cpk(measurements, usl, lsl)
        interpretation = interpret_cpk(cpk_val)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Cp", f"{cp_val:.3f}", help="Process spread vs specification width (centering ignored)")
        c2.metric("Cpk", f"{cpk_val:.3f}", help="Process capability accounting for centering")
        c3.metric("USL", f"{usl:.1f}")
        c4.metric("LSL", f"{lsl:.1f}")

        # Status badge
        if cpk_val >= 1.33:
            badge_class = "badge-excellent"
            icon = "✅"
        elif cpk_val >= 1.0:
            badge_class = "badge-acceptable"
            icon = "⚠️"
        else:
            badge_class = "badge-poor"
            icon = "❌"

        st.markdown(
            f'<div class="{badge_class}">{icon} {interpretation}</div>',
            unsafe_allow_html=True,
        )

    except ValueError as e:
        st.error(f"❌ {e}")

st.divider()

# ---------------------------------------------------------------------------
# Section 4: SPC Charts
# ---------------------------------------------------------------------------
st.markdown('<div class="section-header">📈 SPC Charts</div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📉 X-Bar Chart", "📊 R Chart", "📋 Histogram"])

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
    st.caption("Red points indicate out-of-control measurements (outside UCL or LCL).")

with tab2:
    try:
        fig_r = create_r_chart(
            measurements=measurements,
            subgroup_size=subgroup_size,
            title=f"R Chart — {measurement_column} (n={subgroup_size})",
            y_label="Range",
        )
        st.plotly_chart(fig_r, use_container_width=True)
        st.caption(f"Each point represents the range within a subgroup of {subgroup_size} measurements.")
    except ValueError as e:
        st.warning(f"⚠️ {e}")

with tab3:
    fig_hist = create_histogram(
        measurements=measurements,
        usl=usl,
        lsl=lsl,
        title=f"Distribution — {measurement_column}",
        x_label=measurement_column,
    )
    st.plotly_chart(fig_hist, use_container_width=True)
    st.caption("Red dashed lines show Upper and Lower Specification Limits.")

# ---------------------------------------------------------------------------
# Section 5: Investigation Assistant
# ---------------------------------------------------------------------------
st.divider()
st.markdown('<div class="section-header">🔍 Investigation Assistant</div>', unsafe_allow_html=True)

rule_results = run_all_rules(
    measurements=measurements,
    ucl=limits["ucl"],
    lcl=limits["lcl"],
    centerline=limits["centerline"],
)

recommendations = generate_recommendations(rule_results)

for rec in recommendations:
    if rec["severity"] == "critical":
        icon = "🔴"
    elif rec["severity"] == "warning":
        icon = "🟡"
    else:
        icon = "🟢"

    with st.expander(f"{icon} {rec['title']}", expanded=rec["severity"] == "critical"):
        st.markdown("**Finding:**")
        st.info(rec["finding"])

        if rec["probable_causes"]:
            st.markdown("**Probable Causes:**")
            for cause in rec["probable_causes"]:
                st.markdown(f"- {cause}")

        st.markdown("**Recommended Investigation Steps:**")
        for i, step in enumerate(rec["investigation_steps"], 1):
            st.markdown(f"{i}. {step}")

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.divider()
st.caption("PharmaSPC Intelligence · Phase 1 MVP · Built with Python & Streamlit")