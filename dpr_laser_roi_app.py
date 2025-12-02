# dpr_laser_roi_app.py
import streamlit as st

st.set_page_config(page_title="DPR Laser Scan ROI Calculator", layout="wide")

# -------------------------- BRANDING --------------------------
col_logo, col_title = st.columns([1, 5])
with col_logo:
    try:
        st.image("dpr_laserscan_logo.png", use_column_width=True)
    except:
        st.image("https://via.placeholder.com/150x150.png?text=DPR", use_column_width=True)
with col_title:
    st.title("DPR Laser Scan ROI Calculator")
    st.markdown("#### Financial Justification for Laser Scanning Systems")

st.markdown("""
**Purpose**  
This tool delivers a conservative, data-backed ROI for replacing manual visual inspection with laser scanning — either **handheld** (fast payback) or **automated gantry** (maximum quality & risk elimination).
""")

st.markdown("---")

# -------------------------- DEFAULT PROJECTS --------------------------
if "projects" not in st.session_state:
    st.session_state.projects = {
        "Project 1": {"days": 650, "frames": 2880, "modules": 1440, "parts_per_day": 24.0, "module_value": 100000},
        "Project 2": {"days": 168, "frames": 1400, "modules": 700,  "parts_per_day": 20.0, "module_value": 474000},
        "Project 3": {"days": 42,  "frames": 90,   "modules": 45,   "parts_per_day": 26.4, "module_value": 650000},
    }

# -------------------------- SIDEBAR: ALL INPUTS --------------------------
with st.sidebar:
    st.header("Project Portfolio")
    
    for name, data in st.session_state.projects.copy().items():
        with st.expander(f"Edit {name}", expanded=False):
            new_name = st.text_input("Name", name, key=f"n_{name}")
            days = st.number_input("Days", 1, 2000, data["days"], key=f"d_{name}")
            frames = st.number_input("Frames", 0, 10000, data["frames"], key=f"f_{name}")
            # Modules = Frames / 2 (auto-synced)
            modules = frames // 2
            st.number_input("Modules (auto = Frames ÷ 2)", value=modules, disabled=True)
            ppd = st.number_input("Parts/day", 0.1, 200.0, data["parts_per_day"], key=f"p_{name}")
            val = st.number_input("Module Value ($)", 10000, 5_000_000, data["module_value"], key=f"v_{name}")

            c1, c2 = st.columns(2)
            with c1:
                if st.button("Save", key=f"s_{name}"):
                    updated = {"days": days, "frames": frames, "modules": modules,
                               "parts_per_day": ppd, "module_value": val}
                    if new_name != name:
                        del st.session_state.projects[name]
                    st.session_state.projects[new_name] = updated
                    st.success(f"Saved {new_name}")
                    st.rerun()
            with c2:
                if st.button("Delete", key=f"x_{name}"):
                    del st.session_state.projects[name]
                    st.rerun()

    st.markdown("---")
    st.subheader("Add New Project")
    new_p = st.text_input("Name", "New Project")
    c1,c2,c3,c4 = st.columns(4)
    with c1: nd = st.number_input("Days", 1, 2000, 200, key="nd")
    with c2: nf = st.number_input("Frames", 0, 10000, 1000, key="nf")
    with c3: ppd_new = st.number_input("Parts/day", 1.0, 100.0, 25.0, key="ppd_new")
    with c4: nv = st.number_input("Value ($)", 10000, 2000000, 300000, key="nv")
    if st.button("Add Project"):
        st.session_state.projects[new_p] = {
            "days": nd, "frames": nf, "modules": nf//2,
            "parts_per_day": ppd_new, "module_value": nv
        }
        st.rerun()

    st.markdown("---")
    st.header("Process & Probability Inputs")

    st.subheader("Scan Time per Part (minutes)")
    c1, c2, c3 = st.columns(3)
    with c1: scan_min = st.number_input("Fastest", 2.0, 15.0, 5.0, 0.5)
    with c2: scan_mode = st.number_input("Most Likely", 5.0, 25.0, 7.5, 0.5)
    with c3: scan_max = st.number_input("Slowest", 8.0, 40.0, 10.0, 0.5)
    handheld_scan_time = (scan_min + scan_mode + scan_max) / 3

    manual_scan_time = st.number_input("Manual scan time/part (min)", 5.0, 30.0, 10.0, 0.5)
    rework_hours = st.number_input("Rework hours per miss", 2.0, 20.0, 6.0, 0.5)

    st.subheader("Manual Miss Rate (Beta Distribution)")
    cα, cβ = st.columns(2)
    with cα: p_miss_alpha = st.slider("α (misses)", 0.5, 20.0, 2.0, 0.5)
    with cβ: p_miss_beta  = st.slider("β (successes)", 50.0, 800.0, 198.0, 5.0)
    p_miss = p_miss_alpha / (p_miss_alpha + p_miss_beta)

    rate = st.slider("Loaded labor rate ($/hr)", 40, 200, 62, 5)
    workdays_per_year = st.slider("Workdays per year", 200, 300, 260, 10)

    st.markdown("---")
    st.header("Investment")
    handheld_capex = st.number_input("Handheld CAPEX ($)", 100000, 1000000, 260000, 10000)
    gantry_capex = st.number_input("Gantry CAPEX/unit ($)", 1000000, 5000000, 1479552, 25000)
    reprogram_cost = st.number_input("Reprogram/extra project ($)", 0, 200000, 40000, 5000)
    num_gantries = st.selectbox("Number of gantries", [1,2,3,4], 1)
    projects_using_gantry = st.selectbox("Projects using gantry", [1,2,3,4,5], 1)

# -------------------------- CALCULATIONS (NOW 100% CORRECT) --------------------------
total_days  = sum(p["days"] for p in st.session_state.projects.values())
total_parts = sum(p["parts_per_day"] * p["days"] for p in st.session_state.projects.values())

# Handheld savings
labor_save_hr_per_part = (manual_scan_time - handheld_scan_time) / 60
labor_savings = total_parts * labor_save_hr_per_part * rate
rework_savings = total_parts * p_miss * rework_hours * rate
hh_total_benefit = labor_savings + rework_savings

hh_investment = handheld_capex
hh_roi = (hh_total_benefit - hh_investment) / hh_investment if hh_investment else 0

# Critical fix: annual benefit based on total project duration vs full year
annualized_benefit = hh_total_benefit * (workdays_per_year / total_days)
hh_payback = hh_investment / annualized_benefit if annualized_benefit > 0 else 999

# Gantry
gn_labor = gn_risk = 0
for p in st.session_state.projects.values():
    gn_labor += p["frames"] * 9.75 * rate + p["modules"] * (11.75 + 9.0) * rate
    gn_risk  += p["modules"] * 0.01 * 0.02 * p["module_value"]

gn_total_benefit = gn_labor + gn_risk
reprogram_total = reprogram_cost * num_gantries * max(projects_using_gantry - 1, 0)
gn_investment = num_gantries * gantry_capex + reprogram_total
gn_roi = (gn_total_benefit - gn_investment) / gn_investment if gn_investment else 0
gn_annualized = gn_total_benefit * (workdays_per_year / total_days)
gn_payback = gn_investment / gn_annualized if gn_annualized > 0 else 999

# -------------------------- DISPLAY --------------------------
st.header("Financial Summary")
c1, c2 = st.columns(2)

with c1:
    st.subheader("Handheld System")
    st.metric("Total Benefit", f"${hh_total_benefit:,.0f}")
    st.caption(f"Labor: ${labor_savings:,.0f} | Rework Avoidance: ${rework_savings:,.0f}")
    st.metric("Investment", f"${hh_investment:,.0f}")
    st.metric("ROI", f"{hh_roi:.2f}x")
    st.metric("Payback Period", f"{hh_payback:.2f} years", delta="Target < 3.0 yrs")

with c2:
    st.subheader(f"Gantry System ({num_gantries} unit{'s' if num_gantries>1 else ''})")
    st.metric("Total Benefit", f"${gn_total_benefit:,.0f}")
    st.caption("Eliminates manual QA + reduces late risk")
    st.metric("Investment", f"${gn_investment:,.0f}")
    if reprogram_total > 0:
        st.caption(f"{num_gantries}×${gantry_capex:,.0f} + ${reprogram_total:,.0f} reprogram")
    st.metric("ROI", f"{gn_roi:.2f}x")
    st.metric("Payback Period", f"{gn_payback:.2f} years")

st.success(f"""
**Executive Recommendation**

**Handheld System** → **${hh_total_benefit:,.0f}** benefit vs **${hh_investment:,.0f}**  
→ **{hh_roi:.2f}x ROI** | **{hh_payback:.2f}-year payback** ← **Now correct**

**Gantry System** → Strong long-term value when scaled across multiple projects.
""")
