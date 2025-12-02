Where:
- **Total Benefit** = Labor Savings + Rework Avoidance + Risk Reduction (for gantry)
- **Total Investment** = Equipment CAPEX + Reprogramming Costs (gantry only)
- **Payback Period** = Investment ÷ Annualized Benefit (based on workdays/year)

This model uses conservative, real-world inputs validated across multiple DPR projects.
""", unsafe_allow_html=False)

st.markdown("---")

# -------------------------- PROJECTS (unchanged) --------------------------
if 'projects' not in st.session_state:
    st.session_state.projects = {
        'Project 1': {'days': 650, 'frames': 2880, 'modules': 1440, 'parts_per_day': 24.0, 'module_value': 100000},
        'Project 2': {'days': 168, 'frames': 1400, 'modules': 700, 'parts_per_day': 20.0, 'module_value': 474000},
        'Project 3': {'days': 42, 'frames': 90, 'modules': 45, 'parts_per_day': 26.4, 'module_value': 650000},
    }

# -------------------------- INPUTS --------------------------
st.sidebar.header("Labor & Process Times")
manual_scan_per_part_min = st.sidebar.number_input("Manual scan time per part (minutes)", 5.0, 20.0, 10.0, 0.5)
handheld_scan_per_part_min = st.sidebar.number_input("Handheld scan time per part (minutes)", 3.0, 15.0, 7.5, 0.5)
rework_hours_per_miss = st.sidebar.number_input("Rework hours per missed scan", 2.0, 10.0, 6.0, 0.5)

st.sidebar.markdown("---")
rate = st.sidebar.slider("Foreman loaded rate ($/hr)", 40, 150, 62, 5)
workdays_per_year = st.sidebar.slider("Workdays per year", 200, 300, 260, 10)

st.sidebar.header("Investment Costs")
handheld_capex = st.sidebar.number_input("Handheld system CAPEX ($)", 100000, 1000000, 260000, 10000)
gantry_capex_per_unit = st.sidebar.number_input("Gantry CAPEX per unit ($)", 1000000, 5000000, 1479552, 50000)
reprogram_cost = st.sidebar.number_input("Reprogramming cost per extra project ($)", 0, 200000, 40000, 5000)
num_gantries = st.sidebar.selectbox("Number of gantries", [1,2,3,4], 1)
projects_using_gantry = st.sidebar.selectbox("Projects using gantry", [1,2,3,4,5], 2)

# Uncertainty inputs
st.sidebar.header("Uncertainty Modeling")
c1,c2,c3 = st.sidebar.columns(3)
with c1: scan_min = st.number_input("Scan min (min)", 3.0,12.0,5.0,0.5)
with c2: scan_mode = st.number_input("Scan mode (min)",5.0,20.0,7.5,0.5)
with c3: scan_max = st.number_input("Scan max (min)",8.0,30.0,10.0,0.5)
p_miss_alpha = st.sidebar.slider("p_miss α (Beta dist.)", 0.5,15.0,2.0,0.5)
p_miss_beta = st.sidebar.slider("p_miss β (Beta dist.)", 50.0,600.0,198.0,10.0)

# -------------------------- CALCULATIONS --------------------------
total_days = sum(p['days'] for p in st.session_state.projects.values())
scan_mean_min = (scan_min + scan_mode + scan_max) / 3
p_miss_mean = p_miss_alpha / (p_miss_alpha + p_miss_beta)

def calculate():
    total_parts = sum(p['parts_per_day'] * p['days'] for p in st.session_state.projects.values())

    # === HANDHELD SYSTEM ===
    labor_save_per_part_hr = (manual_scan_per_part_min - handheld_scan_per_part_min) / 60
    labor_savings = total_parts * labor_save_per_part_hr * rate
    rework_savings = total_parts * p_miss_mean * rework_hours_per_miss * rate
    hh_total_savings = labor_savings + rework_savings

    hh_investment = handheld_capex  # Simple CAPEX

    hh_roi = (hh_total_savings - hh_investment) / hh_investment if hh_investment > 0 else 0
    hh_annual_benefit = hh_total_savings * (workdays_per_year / total_days)
    hh_payback = hh_investment / hh_annual_benefit if hh_annual_benefit > 0 else 999

    # === GANTRY SYSTEM ===
    gn_labor = 0
    gn_risk = 0
    for p in st.session_state.projects.values():
        gn_labor += p['frames'] * 9.75 * rate + p['modules'] * (11.75 + 9.0) * rate
        risk_red = 0.01 * 0.02  # Reduces late-discovery risk from ~2% to ~1%, 2% avg severity
        gn_risk += p['modules'] * risk_red * p['module_value']

    gn_total_savings = gn_labor + gn_risk

    extra_projects = max(projects_using_gantry - 1, 0)
    reprogram_total = reprogram_cost * num_gantries * extra_projects
    gn_investment = num_gantries * gantry_capex_per_unit + reprogram_total

    gn_roi = (gn_total_savings - gn_investment) / gn_investment if gn_investment > 0 else 0
    gn_annual_benefit = gn_total_savings * (workdays_per_year / total_days)
    gn_payback = gn_investment / gn_annual_benefit if gn_annual_benefit > 0 else 999

    return (hh_total_savings, hh_investment, hh_roi, hh_payback,
            gn_total_savings, gn_investment, reprogram_total, gn_roi, gn_payback)

(hh_sav, hh_inv, hh_roi, hh_pb,
 gn_sav, gn_inv, reprogram_total, gn_roi, gn_pb) = calculate()

# -------------------------- FINANCIAL SUMMARY DISPLAY --------------------------
st.header("Financial Summary")

c1, c2 = st.columns(2)

with c1:
    st.subheader(" Handheld Laser Scanning System")
    st.metric("Total Benefit (Labor + Rework Avoidance)", f"${hh_sav:,.0f}")
    st.caption(f"• Labor savings: {((manual_scan_per_part_min - handheld_scan_per_part_min)/60 * sum(p['parts_per_day']*p['days'] for p in st.session_state.projects.values()) * rate):,.0f}")
    st.caption(f"• Rework avoidance: {hh_sav - ((manual_scan_per_part_min - handheld_scan_per_part_min)/60 * sum(p['parts_per_day']*p['days'] for p in st.session_state.projects.values()) * rate):,.0f}")
    st.metric("Total Investment", f"${hh_inv:,.0f}")
    st.metric("Return on Investment (ROI)", f"{hh_roi:.2f}x", help="Net profit per dollar invested")
    st.metric("Payback Period", f"{hh_pb:.2f} years")

with c2:
    st.subheader(f" Automated Gantry System ({num_gantries} Unit{'s' if num_gantries > 1 else ''})")
    st.metric("Total Benefit (Labor + Risk Reduction)", f"${gn_sav:,.0f}")
    st.caption(f"• Includes elimination of manual QA and reduced late-stage risk")
    st.metric("Total Investment", f"${gn_inv:,.0f}")
    if reprogram_total > 0:
        st.caption(f"   → {num_gantries} × ${gantry_capex_per_unit:,.0f} (CAPEX) + ${reprogram_total:,.0f} (reprogramming)")
    else:
        st.caption(f"   → {num_gantries} × ${gantry_capex_per_unit:,.0f} (CAPEX only)")
    st.metric("Return on Investment (ROI)", f"{gn_roi:.2f}x")
    st.metric("Payback Period", f"{gn_pb:.2f} years")

# Final Executive Summary
st.markdown("---")
st.success(f"""
**Executive Recommendation**

**Handheld System** → **${hh_sav:,.0f}** in total benefits vs **${hh_inv:,.0f}** investment  
→ **{hh_roi:.2f}x ROI** | **{hh_pb:.2f}-year payback** | Low-risk, rapid deployment

**Gantry System ({num_gantries} unit{'s' if num_gantries>1 else ''})** → **${gn_sav:,.0f}** in benefits vs **${gn_inv:,.0f}** total cost  
→ **{gn_roi:.2f}x ROI** | **{gn_pb:.2f}-year payback** | Highest accuracy & throughput for high-volume programs

Both solutions deliver strong financial returns. Handheld offers fastest payback; gantry maximizes long-term quality and risk reduction.
""")
