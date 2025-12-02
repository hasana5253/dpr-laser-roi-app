import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# -------------------------------------------------------------------
# Page Config & Branding
# -------------------------------------------------------------------
st.set_page_config(page_title="DPR Laser ROI Model", layout="wide")

# Logo + Title (side by side - looks professional)
col_logo, col_title = st.columns([1, 4])
with col_logo:
    st.image("dpr_laserscan_logo.png", use_column_width=True)
with col_title:
    st.title("DPR Laser Scanning ROI Model")
    st.markdown("**Handheld vs Gantry** • Interactive ROI model with Monte Carlo, sensitivity & payback analysis")

# -------------------------------------------------------------------
# Sidebar Inputs
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
    num_gantries = st.selectbox("Number of gantries deployed", [1, 2, 3, 4], 1)
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
    c1, c2, c3 = st.columns(3)
    with c1: scan_min_a = st.number_input("Scan time min (min)", 3.0, 10.0, 5.0, 0.5)
    with c2: scan_min_m = st.number_input("Scan time mode (min)", 5.0, 15.0, 7.5, 0.5)
    with c3: scan_min_b = st.number_input("Scan time max (min)", 8.0, 25.0, 10.0, 0.5)
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
p_late_manual = beta_mean(4, 196)
p_late_gantry = beta_mean(1, 99)

gantry_frame_hr = 0.25
gantry_final_hr = 0.25
gantry_rework_hr = 1.0

@st.cache_data
def calculate_deterministic():
    # Handheld savings
    hh_total = 0
    for p in ['P1', 'P2', 'P3']:
        labor_save = 8 * rate - parts_per_day[p] * (scan_min_mean / 60) * rate
        opp_save = parts_per_day[p] * p_wrong_mean * 6 * rate
        hh_total += (labor_save + opp_save) * days[p]
    hh_roi = (hh_total - handheld_capex) / handheld_capex
    hh_payback_yrs = handheld_capex / (hh_total / total_days * workdays_per_year)

    # Gantry savings
    gn_total = 0
    for p in ['P1', 'P2', 'P3']:
        labor_save = frames[p] * (10 - gantry_frame_hr) * rate + \
                     modules[p] * ((12 - gantry_final_hr) + (10 - gantry_rework_hr)) * rate
        ev_save = modules[p] * (p_late_manual - p_late_gantry) * severity_mean * module_value[p]
        gn_total += labor_save + ev_save

    investment = num_gantries * gantry_capex_base + reprogram_per_project * num_gantries * max(projects_used - 1, 0)
    gn_roi = (gn_total - investment) / investment if investment > 0 else 0
    gn_payback_yrs = investment / (gn_total / total_days * workdays_per_year) if gn_total > 0 else 999

    return hh_total, hh_roi, hh_payback_yrs, gn_total, investment, gn_roi, gn_payback_yrs

hh_total, hh_roi, hh_payback, gn_total, investment, gn_roi, gn_payback = calculate_deterministic()

# -------------------------------------------------------------------
# Deterministic Results
# -------------------------------------------------------------------
st.header("Deterministic Results")
col1, col2 = st.columns(2)
with col1:
    st.metric("Handheld Total Savings", f"${hh_total:,.0f}")
    st.metric("Handheld ROI", f"{hh_roi:.2f}x")
    st.metric("Handheld Payback", f"{hh_payback:.2f} years")
with col2:
    st.metric("Gantry Total Savings", f"${gn_total:,.0f}")
    st.metric("Gantry Investment", f"${investment:,.0f}")
    st.metric("Gantry ROI", f"{gn_roi:.2f}x")
    st.metric("Gantry Payback", f"{gn_payback:.2f} years")

# -------------------------------------------------------------------
# Sensitivity Analysis - Tornado Charts
# -------------------------------------------------------------------
st.header("Sensitivity Analysis - Key Drivers")

vars_to_test = {
    "Foreman Rate (±20%)": ("rate", 0.8, 1.2),
    "Workdays/Year (±10%)": ("workdays_per_year", 0.9, 1.1),
    "Handheld CAPEX (±10%)": ("handheld_capex", 0.9, 1.1),
    "Gantry CAPEX (±10%)": ("gantry_capex_base", 0.9, 1.1),
    "Reprogram Cost (±20%)": ("reprogram_per_project", 0.8, 1.2),
    "Scan Time Mean (±20%)": ("scan_min_mean", 0.8, 1.2),
    "Error Rate (±20%)": ("p_wrong_mean", 0.8, 1.2),
    "Severity (±20%)": ("severity_mean", 0.8, 1.2),
}

def run_one_sensitivity(var_name, factor):
    orig = globals()[var_name]
    globals()[var_name] = orig * factor
    _, hh_r, _, _, _, gn_r, _ = calculate_deterministic()
    globals()[var_name] = orig  # restore
    return hh_r, gn_r

hh_delta_low = {}
hh_delta_high = {}
gn_delta_low = {}
gn_delta_high = {}

for label, (var, low_f, high_f) in vars_to_test.items():
    hh_low, gn_low = run_one_sensitivity(var, low_f)
    hh_high, gn_high = run_one_sensitivity(var, high_f)
    hh_delta_low[label] = hh_low - hh_roi
    hh_delta_high[label] = hh_high - hh_roi
    gn_delta_low[label] = gn_low - gn_roi
    gn_delta_high[label] = gn_high - gn_roi

def plot_tornado(low_dict, high_dict, base, title, color_low="#e74c3c", color_high="#27ae60"):
    labels = list(low_dict.keys())
    low_vals = [low_dict[l] for l in labels]
    high_vals = [high_dict[l] for l in labels]
    fig, ax = plt.subplots(figsize=(9, 5))
    y = np.arange(len(labels))
    ax.barh(y, low_vals, left=base, color=color_low, label="- Scenario")
    ax.barh(y, high_vals, left=base, color=color_high, label="+ Scenario")
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlabel("Change in ROI (x)")
    ax.set_title(title)
    ax.legend()
    ax.grid(True, axis='x', alpha=0.3)
    return fig

c1, c2 = st.columns(2)
with c1:
    st.pyplot(plot_tornado(hh_delta_low, hh_delta_high, hh_roi, "Handheld ROI Sensitivity"))
with c2:
    st.pyplot(plot_tornado(gn_delta_low, gn_delta_high, gn_roi, "Gantry ROI Sensitivity"))

# -------------------------------------------------------------------
# Monte Carlo Simulation
# -------------------------------------------------------------------
if run_mc:
    with st.spinner("Running 10,000 Monte Carlo simulations..."):
        N = 10000
        np.random.seed(42)

        scan_times = np.random.triangular(scan_min_a, scan_min_m, scan_min_b, N)
        p_wrongs = np.random.beta(p_wrong_a, p_wrong_b, N)
        severities = np.random.triangular(sev_a, sev_m, sev_b, N)

        # Handheld
        hh_savings = np.zeros(N)
        for i in range(N):
            tot = 0
            for p in ['P1','P2','P3']:
                labor = 8*rate - parts_per_day[p]*(scan_times[i]/60)*rate
                opp = parts_per_day[p]*p_wrongs[i]*6*rate
                tot += (labor + opp) * days[p]
            hh_savings[i] = tot
        hh_roi_mc = (hh_savings - handheld_capex) / handheld_capex
        hh_payback_mc = handheld_capex / (hh_savings / total_days * workdays_per_year)

        # Gantry
        gn_investment = num_gantries * gantry_capex_base + reprogram_per_project * num_gantries * max(projects_used-1, 0)
        gn_savings = np.zeros(N)
        for i in range(N):
            tot = 0
            for p in ['P1','P2','P3']:
                labor = frames[p]*(10-gantry_frame_hr)*rate + modules[p]*((12-gantry_final_hr) + (10-gantry_rework_hr))*rate
                ev = modules[p] * (p_late_manual - p_late_gantry) * severities[i] * module_value[p]
                tot += labor + ev
            gn_savings[i] = tot
        gn_roi_mc = (gn_savings - gn_investment) / gn_investment
        gn_payback_mc = gn_investment / (gn_savings / total_days * workdays_per_year)

        st.success("Monte Carlo simulation complete!")

        # ROI Distributions
        st.header("Monte Carlo ROI Distributions")
        c1, c2 = st.columns(2)
        with c1:
            fig, ax = plt.subplots()
            ax.hist(hh_roi_mc, bins=60, color="#3498db", alpha=0.8, edgecolor='black')
            ax.axvline(hh_roi, color='red', linewidth=2, label=f"Base: {hh_roi:.2f}x")
            ax.set_title("Handheld ROI Distribution")
            ax.set_xlabel("ROI (x)"); ax.legend()
            st.pyplot(fig)
        with c2:
            fig, ax = plt.subplots()
            ax.hist(gn_roi_mc, bins=60, color="#e67e22", alpha=0.8, edgecolor='black')
            ax.axvline(gn_roi, color='red', linewidth=2, label=f"Base: {gn_roi:.2f}x")
            ax.set_title("Gantry ROI Distribution")
            ax.set_xlabel("ROI (x)"); ax.legend()
            st.pyplot(fig)

        # Payback Period Distributions
        st.header("Monte Carlo Payback Period Distributions")
        c1, c2 = st.columns(2)
        with c1:
            fig, ax = plt.subplots()
            ax.hist(hh_payback_mc, bins=60, color="#3498db", alpha=0.8, edgecolor='black')
            ax.axvline(hh_payback, color='red', linewidth=2, label=f"Base: {hh_payback:.2f} yrs")
            ax.set_title("Handheld Payback Period")
            ax.set_xlabel("Years"); ax.legend()
            st.pyplot(fig)
        with c2:
            fig, ax = plt.subplots()
            ax.hist(gn_payback_mc, bins=60, color="#e67e22", alpha=0.8, edgecolor='black')
            ax.axvline(gn_payback, color='red', linewidth=2, label=f"Base: {gn_payback:.2f} yrs")
            ax.set_title("Gantry Payback Period")
            ax.set_xlabel("Years"); ax.legend()
            st.pyplot(fig)

# -------------------------------------------------------------------
# Final Recommendation
# -------------------------------------------------------------------
st.markdown("---")
st.markdown("### Recommendation")
st.success(f"""
**With current assumptions:**

→ **Deploy {num_gantries} Laser Scan Gantry(s)**  
  ROI: **{gn_roi:.2f}x** • Payback: **{gn_payback*12:.1f} months**

→ Handheld scanners  
  ROI: **{hh_roi:.2f}x** • Payback: **{hh_payback:.1f} years**

**Gantry is the clear financial winner.**
""")

st.caption("DPR Construction • Laser Scan Car Wash ROI Model • 2025")
