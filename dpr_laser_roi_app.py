# dpr_laser_roi_app.py
import streamlit as st

st.set_page_config(page_title="DPR Laser Scan ROI Calculator", layout="wide")

# -------------------------- BRANDING --------------------------
col_logo, col_title = st.columns([1, 4])
with col_logo:
    try:
        st.image("dpr_laserscan_logo.png", use_column_width=True)
    except:
        st.image("https://via.placeholder.com/150x150.png?text=DPR", use_column_width=True)
with col_title:
    st.title("DPR Laser Scan ROI Calculator")
    st.markdown("### Financial Justification for Handheld & Gantry Laser Scanning Systems")

# -------------------------- PURPOSE & METHODOLOGY --------------------------
st.markdown("""
**Purpose of this Tool**  
This calculator proves the hard-dollar ROI of replacing manual visual inspections with modern laser scanning — either **handheld** (flexible, fast payback) or **automated gantry** (maximum accuracy & risk elimination).

**ROI Formula Used**
Payback = Investment ÷ Annualized Benefit
""")

st.markdown("---")

# -------------------------- DEFAULT PROJECTS --------------------------
if "projects" not in st.session_state:
    st.session_state.projects = {
        "Project 1": {"days": 650, "frames": 2880, "modules": 1440, "parts_per_day": 24.0, "module_value": 100_000},
        "Project 2": {"days": 168, "frames": 1400, "modules": 700,  "parts_per_day": 20.0, "module_value": 474_000},
        "Project 3": {"days": 42,  "frames": 90,   "modules": 45,   "parts_per_day": 26.4, "module_value": 650_000},
    }

# -------------------------- SIDEBAR INPUTS --------------------------
st.sidebar.header("Labor & Process Times")
manual_scan_per_part_min   = st.sidebar.number_input("Manual scan time per part (min)", 5.0, 30.0, 10.0, 0.5)
handheld_scan_per_part_min = st.sidebar.number_input("Handheld scan time per part (min)", 2.0, 20.0, 7.5, 0.5)
rework_hours_per_miss      = st.sidebar.number_input("Rework hours per missed defect", 2.0, 20.0, 6.0, 0.5)

st.sidebar.markdown("---")
rate               = st.sidebar.slider("Fully loaded labor rate ($/hr)", 40, 200, 62, 5)
workdays_per_year  = st.sidebar.slider("Workdays per year", 200, 300, 260, 10)

st.sidebar.header("Investment Costs")
handheld_capex          = st.sidebar.number_input("Handheld system CAPEX ($)", 100_000, 1_000_000, 260_000, 10_000)
gantry_capex_per_unit   = st.sidebar.number_input("Gantry CAPEX per unit ($)", 500_000, 5_000_000, 1_479_552, 25_000)
reprogram_cost          = st.sidebar.number_input("Reprogramming cost per extra project ($)", 0, 300_000, 40_000, 5_000)
num_gantries            = st.sidebar.selectbox("Number of gantry units", [1, 2, 3, 4], 1)
projects_using_gantry   = st.sidebar.selectbox("How many different projects will use the gantry?", [1, 2, 3, 4, 5], 2)

st.sidebar.header("Uncertainty Modeling")
c1, c2, c3 = st.sidebar.columns(3)
with c1: scan_min  = st.number_input("Scan min (min)", 3.0, 15.0, 5.0, 0.5)
with c2: scan_mode = st.number_input("Scan mode (min)", 5.0, 25.0, 7.5, 0.5)
with c3: scan_max  = st.number_input("Scan max (min)", 8.0, 40.0, 10.0, 0.5)

p_miss_alpha = st.sidebar.slider("p_miss α (Beta shape)", 0.5, 20.0, 2.0, 0.5)
p_miss_beta  = st.sidebar.slider("p_miss β (Beta shape)", 50.0, 800.0, 198.0, 10.0)

# -------------------------- CALCULATIONS --------------------------
total_days   = sum(p["days"] for p in st.session_state.projects.values())
total_parts  = sum(p["parts_per_day"] * p["days"] for p in st.session_state.projects.values())
p_miss_mean  = p_miss_alpha / (p_miss_alpha + p_miss_beta)

# Handheld
labor_savings      = total_parts * (manual_scan_per_part_min - handheld_scan_per_part_min) / 60 * rate
rework_avoidance   = total_parts * p_miss_mean * rework_hours_per_miss * rate
hh_total_benefit   = labor_savings + rework_avoidance
hh_investment      = handheld_capex
hh_roi             = (hh_total_benefit - hh_investment) / hh_investment if hh_investment else 0
hh_annual_benefit  = hh_total_benefit * (workdays_per_year / total_days)
hh_payback         = hh_investment / hh_annual_benefit if hh_annual_benefit > 0 else 999

# Gantry
gn_labor_savings = gn_risk_savings = 0
for p in st.session_state.projects.values():
    gn_labor_savings += p["frames"] * 9.75 * rate + p["modules"] * (11.75 + 9.0) * rate
    gn_risk_savings  += p["modules"] * 0.01 * 0.02 * p["module_value"]

gn_total_benefit   = gn_labor_savings + gn_risk_savings
reprogram_total    = reprogram_cost * num_gantries * max(projects_using_gantry - 1, 0)
gn_investment      = num_gantries * gantry_capex_per_unit + reprogram_total
gn_roi             = (gn_total_benefit - gn_investment) / gn_investment if gn_investment else 0
gn_annual_benefit  = gn_total_benefit * (workdays_per_year / total_days)
gn_payback         = gn_investment / gn_annual_benefit if gn_annual_benefit > 0 else 999

# -------------------------- DISPLAY RESULTS --------------------------
st.header("Financial Summary")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Handheld Laser Scanner")
    st.metric("Total Benefit", f"${hh_total_benefit:,.0f}")
    st.caption(f"Labor savings: ${labor_savings:,.0f} | Rework avoidance: ${rework_avoidance:,.0f}")
    st.metric("Total Investment", f"${hh_investment:,.0f}")
    st.metric("ROI", f"{hh_roi:.2f}x")
    st.metric("Payback Period", f"{hh_payback:.2f} years")

with col2:
    st.subheader(f"Automated Gantry ({num_gantries} unit{'s' if num_gantries>1 else ''})")
    st.metric("Total Benefit", f"${gn_total_benefit:,.0f}")
    st.caption("Eliminates manual QA + reduces late-discovery risk")
    st.metric("Total Investment", f"${gn_investment:,.0f}")
    if reprogram_total > 0:
        st.caption(f"{num_gantries} × ${gantry_capex_per_unit:,.0f} + ${reprogram_total:,.0f} reprogramming")
    else:
        st.caption(f"{num_gantries} × ${gantry_capex_per_unit:,.0f}")
    st.metric("ROI", f"{gn_roi:.2f}x")
    st.metric("Payback Period", f"{gn_payback:.2f} years")

# -------------------------- EXECUTIVE SUMMARY --------------------------
st.markdown("---")
st.success(f"""
**Executive Recommendation**

**Handheld System** — **${hh_total_benefit:,.0f}** benefit vs **${hh_investment:,.0f}** invested  
→ **{hh_roi:.2f}x ROI** | **{hh_payback:.2f}-year payback**

**Gantry System** ({num_gantries} unit{'s' if num_gantries>1 else ''}) — **${gn_total_benefit:,.0f}** benefit vs **${gn_investment:,.0f}** invested  
→ **{gn_roi:.2f}x ROI** | **{gn_payback:.2f}-year payback**

Both deliver outstanding returns. Handheld = fastest payback. Gantry = maximum quality & risk elimination.
""")
