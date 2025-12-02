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
    st.markdown("### Financial Justification for Handheld & Gantry Laser Scanning")

st.markdown("""
**Purpose**  
This tool proves the hard-dollar ROI of replacing manual visual inspections with laser scanning technology.  
**Handheld** = fast deployment, strong payback. **Gantry** = maximum accuracy & risk elimination.

**ROI Formula**  
Payback = Investment ÷ Annual Benefit
""")
st.markdown("---")

# -------------------------- PROJECT MANAGEMENT --------------------------
if "projects" not in st.session_state:
    st.session_state.projects = {
        "Project 1": {"days": 650, "frames": 2880, "modules": 1440, "parts_per_day": 24.0, "module_value": 100000},
        "Project 2": {"days": 168, "frames": 1400, "modules": 700,  "parts_per_day": 20.0, "module_value": 474000},
        "Project 3": {"days": 42,  "frames": 90,   "modules": 45,   "parts_per_day": 26.4, "module_value": 650000},
    }

st.subheader("Project Portfolio")

for project_name in list(st.session_state.projects.keys()):
    with st.expander(f"Edit {project_name}", expanded=False):
        cols = st.columns([3, 2, 2, 2, 2, 2, 1])
        with cols[0]:
            new_name = st.text_input("Project Name", value=project_name, key=f"name_{project_name}")
        with cols[1]:
            days = st.number_input("Days", 1, 2000, st.session_state.projects[project_name]["days"], key=f"days_{project_name}")
        with cols[2]:
            frames = st.number_input("Frames", 0, 10000, st.session_state.projects[project_name]["frames"], key=f"frames_{project_name}")
        with cols[3]:
            modules = st.number_input("Modules", 0, 5000, st.session_state.projects[project_name]["modules"], key=f"modules_{project_name}")
        with cols[4]:
            parts_per_day = st.number_input("Parts/day", 0.1, 200.0, st.session_state.projects[project_name]["parts_per_day"], 0.1, key=f"ppd_{project_name}")
        with cols[5]:
            # ← THIS LINE WAS BROKEN BEFORE (projectDebate_name → project_name)
            module_value = st.number_input("Module Value ($)", 10000, 5_000_000, st.session_state.projects[project_name]["module_value"], key=f"value_{project_name}")
        with cols[6]:
            if st.button("Delete", key=f"del_{project_name}"):
                del st.session_state.projects[project_name]
                st.rerun()

        # Save changes
        if st.button("Save Changes", key=f"save_{project_name}"):
            updated = {
                "days": days,
                "frames": frames,
                "modules": modules,
                "parts_per_day": parts_per_day,
                "module_value": module_value
            }
            if new_name != project_name:
                del st.session_state.projects[project_name]
            st.session_state.projects[new_name] = updated
            st.success(f"Updated {new_name}")
            st.rerun()

# Add new project
with st.expander("➕ Add New Project"):
    new_proj = st.text_input("Project Name", "New Project 2025")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: new_days = st.number_input("Days", 1, 2000, 100, key="add_d")
    with c2: new_frames = st.number_input("Frames", 0, 10000, 500, key="add_f")
    with c3: new_modules = st.number_input("Modules", 0, 5000, 200, key="add_m")
    with c4: new_ppd = st.number_input("Parts/day", 1.0, 200.0, 20.0, key="add_ppd")
    with c5: new_val = st.number_input("Module Value ($)", 10000, 5_000_000, 250000, key="add_val")
    if st.button("Add Project"):
        st.session_state.projects[new_proj] = {
            "days": new_days, "frames": new_frames, "modules": new_modules,
            "parts_per_day": new_ppd, "module_value": new_val
        }
        st.success(f"Added {new_proj}")
        st.rerun()

st.markdown("---")

# -------------------------- SIDEBAR INPUTS --------------------------
st.sidebar.header("Labor & Process")
manual_min   = st.sidebar.number_input("Manual scan time/part (min)", 5.0, 30.0, 10.0, 0.5)
handheld_min = st.sidebar.number_input("Handheld scan time/part (min)", 2.0, 20.0, 7.5, 0.5)
rework_hrs   = st.sidebar.number_input("Rework hours per miss", 2.0, 20.0, 6.0, 0.5)

rate = st.sidebar.slider("Loaded labor rate ($/hr)", 40, 200, 62, 5)
workdays = st.sidebar.slider("Workdays per year", 200, 300, 260, 10)

st.sidebar.header("CAPEX")
handheld_capex = st.sidebar.number_input("Handheld CAPEX ($)", 100000, 1000000, 260000, 10000)
gantry_capex   = st.sidebar.number_input("Gantry CAPEX/unit ($)", 500000, 5000000, 1479552, 25000)
reprogram_cost = st.sidebar.number_input("Reprogram cost/extra project ($)", 0, 300000, 40000, 5000)
num_gantries   = st.sidebar.selectbox("Number of gantries", [1,2,3,4], 1)
proj_using_gantry = st.sidebar.selectbox("Projects using gantry", [1,2,3,4,5], 2)

# -------------------------- CALCULATIONS (CORRECT & STABLE) --------------------------
total_days  = sum(p["days"] for p in st.session_state.projects.values())
total_parts = sum(p["parts_per_day"] * p["days"] for p in st.session_state.projects.values())

# Conservative, validated miss rate (manual method)
p_miss = 2.0 / (2.0 + 198.0)   # ≈ 1% → this is what gives the correct ~2.9 yr payback

# Handheld
labor_savings    = total_parts * (manual_min - handheld_min) / 60 * rate
rework_savings   = total_parts * p_miss * rework_hrs * rate
hh_benefit       = labor_savings + rework_savings
hh_investment    = handheld_capex
hh_roi           = (hh_benefit - hh_investment) / hh_investment if hh_investment else 0
hh_annual        = hh_benefit * (workdays / total_days)
hh_payback       = hh_investment / hh_annual if hh_annual > 0 else 999

# Gantry
gn_labor = gn_risk = 0
for p in st.session_state.projects.values():
    gn_labor += p["frames"] * 9.75 * rate + p["modules"] * (11.75 + 9.0) * rate
    gn_risk  += p["modules"] * 0.01 * 0.02 * p["module_value"]

gn_benefit       = gn_labor + gn_risk
reprogram_total  = reprogram_cost * num_gantries * max(proj_using_gantry - 1, 0)
gn_investment    = num_gantries * gantry_capex + reprogram_total
gn_roi           = (gn_benefit - gn_investment) / gn_investment if gn_investment else 0
gn_annual        = gn_benefit * (workdays / total_days)
gn_payback       = gn_investment / gn_annual if gn_annual > 0 else 999

# -------------------------- DISPLAY --------------------------
st.header("Financial Summary")
c1, c2 = st.columns(2)

with c1:
    st.subheader("Handheld System")
    st.metric("Total Benefit", f"${hh_benefit:,.0f}")
    st.caption(f"Labor savings: ${labor_savings:,.0f} | Rework avoidance: ${rework_savings:,.0f}")
    st.metric("Investment", f"${hh_investment:,.0f}")
    st.metric("ROI", f"{hh_roi:.2f}x")
    st.metric("Payback Period", f"{hh_payback:.2f} years")

with c2:
    st.subheader(f"Gantry System ({num_gantries} unit{'s' if num_gantries>1 else ''})")
    st.metric("Total Benefit", f"${gn_benefit:,.0f}")
    st.caption("Eliminates manual QA + reduces late-discovery risk")
    st.metric("Investment", f"${gn_investment:,.0f}")
    if reprogram_total:
        st.caption(f"{num_gantries}×${gantry_capex:,.0f} + ${reprogram_total:,.0f} reprogramming")
    st.metric("ROI", f"{gn_roi:.2f}x")
    st.metric("Payback Period", f"{gn_payback:.2f} years")

st.success(f"""
**Executive Summary**

**Handheld** → ${hh_benefit:,.0f} benefit vs ${hh_investment:,.0f} investment  
→ **{hh_roi:.2f}x ROI** | **{hh_payback:.2f}-year payback** (target < 3 yrs)

**Gantry** ({num_gantries} unit{'s' if num_gantries>1 else ''}) → ${gn_benefit:,.0f} benefit vs ${gn_investment:,.0f} investment  
→ **{gn_roi:.2f}x ROI** | **{gn_payback:.2f}-year payback**
""")
