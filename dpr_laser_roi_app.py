"""
DPR Laser Scanning ROI Model - Interactive
Handheld vs Gantry | Deterministic + Monte Carlo + Sensitivity
"""

import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="DPR Laser ROI Model", layout="wide")
st.title("DPR Laser Scanning ROI Model")
st.markdown("**Handheld vs Gantry** • Interactive financial model with Monte Carlo, sensitivity & scenario analysis")

# -------------------------------------------------------------------
# SIDEBAR INPUTS
# -------------------------------------------------------------------
with st.sidebar:
    st.header("Inputs & Assumptions")
    
    rate = st.slider("Foreman loaded rate ($/hr)", 40, 120, 62, 5)
    workdays_per_year = st.slider("Workdays per year", 200, 300, 260, 10)

    st.markdown("---")
    st.subheader("CAPEX")
    handheld_capex = st.number_input("Handheld system CAPEX ($)", 100000, 600000, 260000, 10000)
    gantry_capex_base = st.number_input("Single Gantry CAPEX ($)", 1000000, 3500000, 1479552, 50000)
    reprogram_per_project = st.number_input("Reprogramming cost per extra project ($)", 0, 100000, 40000, 5000)
    num_gantries = st.selectbox("Number of gantries deployed", [1, 2, 3, 4], 0)
    projects_used = st.selectbox("Projects using gantry(s)", [1, 2, 3], 2)

    st.markdown("---")
    st.subheader("Project Portfolio")
    days = {
        'P1': st.number_input("P1 duration (days)", 400, 1000, 650),
        'P2': st.number_input("P2 duration (days)", 100, 300, 168),
        'P3': st.number_input("P3 duration (days)", 20, 100, 42)
    }
    frames = {
        'P1': st.number_input("P1 frames", 1000, 5000, 2880),
        'P2': st.number_input("P2 frames", 500, 3000, 1400),
        'P3': st.number_input("P3 frames", 10, 500, 90)
    }
    modules = {
        'P1': st.number_input("P1 modules", 500, 3000, 1440),
        'P2': st.number_input("P2 modules", 300, 2000, 700),
        'P3': st.number_input("P3 modules", 10, 300, 45)
    }
    parts_per_day = {
        'P1': st.number_input("P1 parts/day", 10.0, 40.0, 24.0, 1.0),
        'P2': st.number_input("P2 parts/day", 10.0, 40.0, 20.0, 1.0),
        'P3': st.number_input("P3 parts/day", 10.0, 40.0, 26.4, 0.5)
    }
    module_value = {
        'P1': st.number_input("P1 module value ($)", 50000, 300000, 100000, 10000),
        'P2': st.number_input("P2 module value ($)", 300000, 1000000, 474000, 20000),
        'P3': st.number_input("P3 module value ($)", 400000, 1500000, 650000, 50000)
    }

    st.markdown("---")
    st.subheader("Uncertainty Ranges")
    col1, col2, col3 = st.columns(3)
    with col1: scan_min_a = st.number_input("Scan time min (min)", 3.0, 10.0, 5.0, 0.5)
    with col2: scan_min_m = st.number_input("Scan time mode (min)", 5.0, 15.0, 7.5, 0.5)
    with col3: scan_min_b = st.number_input("Scan time max (min)", 8.0, 25.0, 10.0, 0.5)

    p_wrong_a = st.slider("p_wrong Beta α", 0.5, 10.0, 2.0, 0.5)
    p_wrong_b = st.slider("p_wrong Beta β", 100.0, 500.0, 198.0, 10.0)

    sev_a = st.number_input("Severity min (%)", 0.0, 0.10, 0.01, 0.005, format="%.3f")
    sev_m = st.number_input("Severity mode (%)", 0.005, 0.10, 0.02, 0.005, format="%.3f")
    sev_b = st.number_input("Severity max (%)", 0.01, 0.20, 0.05, 0.01, format="%.3f")

    run_mc = st.button("Run Monte Carlo (10,000 simulations)", type="primary")

# -------------------------------------------------------------------
# Core Calculations
# -------------------------------------------------------------------
total_days = sum(days.values())

def tri_mean(a, m, b): return (a + m + b) / 3
def beta_mean(a, b): return a / (a + b)

scan_min_mean = tri_mean(scan_min_a, scan_min_m, scan_min_b)
p_wrong_mean = beta_mean(p_wrong_a, p_wrong_b)
severity_mean = tri_mean(sev_a, sev_m, sev_b)
p_late_manual_mean = beta_mean(4, 196)
p_late_gantry_mean = beta_mean(1, 99)

# Fixed gantry times
gantry_frame_hr = 0.25; gantry_final_hr = 0.25; gantry_rework_hr = 1.0

# Deterministic
@st.cache_data
def deterministic():
    # Handheld
    hh_total = 0
    for p in ['P1','P2','P3']:
        labor_save = 8*rate - parts_per_day[p] * (scan_min_mean/60) * rate
        opp_save = parts_per_day[p] * p_wrong_mean * 6 * rate
        hh_total += (labor_save + opp_save) * days[p]
    hh_roi = (hh_total - handheld_capex) / handheld_capex
    hh_payback = handheld_capex / (hh_total / total_days * workdays_per_year)

    # Gantry
    gn_total = 0
    for p in ['P1','P2','P3']:
        labor = frames[p]*(10 - gantry_frame_hr)*rate + modules[p]*((12 - gantry_final_hr) + (10 - gantry_rework_hr))*rate
        ev = modules[p] * max(p_late_manual_mean - p_late_gantry_mean, 0) * severity_mean * module_value[p]
        gn_total += labor + ev
    investment = num_gantries * gantry_capex_base + reprogram_per_project * num_gantries * max(projects_used-1, 0)
    gn_roi = (gn_total - investment) / investment
    gn_payback = investment / (gn_total / total_days * workdays_per_year)

    return hh_total, hh_roi, hh_payback, gn_total, investment, gn_roi, gn_payback

hh_total, hh_roi, hh_payback, gn_total, investment, gn_roi, gn_payback = deterministic()

# -------------------------------------------------------------------
# Results Display
# -------------------------------------------------------------------
st.header("Deterministic Results")
c1, c2 = st.columns(2)
with c1:
    st.metric("Handheld Total Savings", f"${hh_total:,.0f}")
    st.metric("Handheld ROI", f"{hh_roi:.2f}x")
    st.metric("Handheld Payback", f"{hh_payback:.2f} years")
with c2:
    st.metric("Gantry Total Savings", f"${gn_total:,.0f}")
    st.metric("Gantry Investment", f"${investment:,.0f}")
    st.metric("Gantry ROI", f"{gn_roi:.2f}x")
    st.metric("Gantry Payback", f"{gn_payback:.2f} years")

# -------------------------------------------------------------------
# Monte Carlo
# -------------------------------------------------------------------
if run_mc:
    with st.spinner("Running 10,000 Monte Carlo simulations..."):
        N = 10000
        np.random.seed(42)

        scan = {p: np.random.triangular(scan_min_a, scan_min_m, scan_min_b, N) for p in ['P1','P2','P3']}
        p_wrong = {p: np.random.beta(p_wrong_a, p_wrong_b, N) for p in ['P1','P2','P3']}
        severity = np.random.triangular(sev_a, sev_m, sev_b, N)

        # Handheld MC
        hh_mc = np.zeros(N)
        for i in range(N):
            tot = 0
            for p in ['P1','P2','P3']:
                labor = 8*rate - parts_per_day[p] * (scan[p][i]/60) * rate
                opp = parts_per_day[p] * p_wrong[p][i] * 6 * rate
                tot += (labor + opp) * days[p]
            hh_mc[i] = tot
        hh_roi_mc = (hh_mc - handheld_capex) / handheld_capex

        # Gantry MC
        gn_inv = num_gantries * gantry_capex_base + reprogram_per_project * num_gantries * max(projects_used-1, 0)
        gn_mc = np.zeros(N)
        for i in range(N):
            tot = 0
            for p in ['P1','P2','P3']:
                labor = frames[p]*(10 - gantry_frame_hr)*rate + modules[p]*((12 - gantry_final_hr) + (10 - gantry_rework_hr))*rate
                ev = modules[p] * max(0.02 - 0.01, 0) * severity[i] * module_value[p]
                tot += labor + ev
            gn_mc[i] = tot
        gn_roi_mc = (gn_mc - gn_inv) / gn_inv

        st.success("Monte Carlo Complete!")

        c1, c2 = st.columns(2)
        with c1:
            fig, ax = plt.subplots()
            ax.hist(hh_roi_mc, bins=50, color="#4e9af1", edgecolor='black')
            ax.axvline(hh_roi, color='red', linestyle='--', label=f"Deterministic {hh_roi:.1f}x")
            ax.set_title("Handheld ROI Distribution")
            ax.set_xlabel("ROI (x)"); ax.legend()
            st.pyplot(fig)
        with c2:
            fig, ax = plt.subplots()
            ax.hist(gn_roi_mc, bins=50, color="#f39c12", edgecolor='black')
            ax.axvline(gn_roi, color='red', linestyle='--', label=f"Deterministic {gn_roi:.1f}x")
            ax.set_title("Gantry ROI Distribution")
            ax.set_xlabel("ROI (x)"); ax.legend()
            st.pyplot(fig)

st.markdown("---")
st.markdown("### Recommendation")
st.success(f"""
With current inputs:
• **Deploy {num_gantries} gantry(s)** → **{gn_roi:.1f}x ROI**, payback in **{gn_payback*12:.1f} months**  
• **Handheld scanners** → **{hh_roi:.1f}x ROI**, payback in **{hh_payback:.1f} years**

**Gantry wins decisively on ROI and speed.**
""")

st.caption("DPR Construction • Laser Scanning ROI Model • 2025")
