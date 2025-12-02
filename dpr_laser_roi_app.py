# dpr_laser_roi_app.py
import streamlit as st

st.set_page_config(page_title="DPR Laser Scan ROI Calculator", layout="wide")

# -------------------------- BRANDING --------------------------
col_logo, col_title = st.columns([1, 5])
with col_logo:
    try:
        st.image("dpr_laserscan_logo.png", use_column_width=True)
    except Exception:
        st.image("https://via.placeholder.com/150x150.png?text=DPR", use_column_width=True)

with col_title:
    st.title("DPR Laser Scan ROI Calculator")
    st.markdown("#### Financial Justification for Laser Scanning Systems")

st.markdown("""
**Purpose**  
This tool uses the same assumptions and formulas as the DPR laser-scanning ROI model to estimate the financial case for:

- **Handheld scanning** at receiving  
- **Gantry scanning** for frame and final module QC
""")

st.markdown("---")

# -------------------------- DEFAULT PROJECTS --------------------------
if "projects" not in st.session_state:
    st.session_state.projects = {
        "Project 1": {"days": 650, "frames": 2880, "modules": 1440, "parts_per_day": 24.0, "module_value": 100000},
        "Project 2": {"days": 168, "frames": 1400, "modules": 700,  "parts_per_day": 20.0, "module_value": 474000},
        "Project 3": {"days": 42,  "frames": 90,   "modules": 45,   "parts_per_day": 26.4, "module_value": 650000},
    }

# -------------------------- SIDEBAR INPUTS --------------------------
with st.sidebar:
    st.header("Project Portfolio")

    # Edit existing projects
    for name, data in st.session_state.projects.copy().items():
        with st.expander(f"Edit {name}", expanded=False):
            new_name = st.text_input("Name", name, key=f"n_{name}")
            days = st.number_input("Days", 1, 2000, data["days"], key=f"d_{name}")
            frames = st.number_input("Frames", 0, 10000, data["frames"], key=f"f_{name}")
            modules = frames // 2
            st.number_input("Modules (auto = Frames ÷ 2)", value=modules, disabled=True)
            ppd = st.number_input("Parts/day", 0.1, 200.0, data["parts_per_day"], key=f"p_{name}")
            mv = st.number_input("Module value ($)", 10_000, 5_000_000, data["module_value"], key=f"mv_{name}")

            c1, c2 = st.columns(2)
            with c1:
                if st.button("Save", key=f"s_{name}"):
                    updated = {
                        "days": days,
                        "frames": frames,
                        "modules": modules,
                        "parts_per_day": ppd,
                        "module_value": mv,
                    }
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
    new_p = st.text_input("New project name", "New Project")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        nd = st.number_input("Days", 1, 2000, 200, key="nd")
    with c2:
        nf = st.number_input("Frames", 0, 10000, 1000, key="nf")
    with c3:
        ppd_new = st.number_input("Parts/day", 1.0, 100.0, 25.0, key="ppd_new")
    with c4:
        nv = st.number_input("Module value ($)", 10_000, 2_000_000, 300_000, key="nv")
    if st.button("Add Project"):
        st.session_state.projects[new_p] = {
            "days": nd,
            "frames": nf,
            "modules": nf // 2,
            "parts_per_day": ppd_new,
            "module_value": nv,
        }
        st.rerun()

    st.markdown("---")
    st.header("Handheld – Receiving Assumptions")

    # Triangular scan time (minutes)
    st.markdown("**Scan time per part (minutes, triangular)**")
    c1, c2, c3 = st.columns(3)
    with c1:
        scan_min = st.number_input("Fastest", 2.0, 20.0, 5.0, 0.5)
    with c2:
        scan_mode = st.number_input("Most likely", 3.0, 30.0, 7.5, 0.5)
    with c3:
        scan_max = st.number_input("Slowest", 5.0, 40.0, 10.0, 0.5)
    handheld_scan_mean = (scan_min + scan_mode + scan_max) / 3.0

    # Manual receiving labor / day
    manual_hours_day = st.number_input(
        "Manual receiving QC hours/day (baseline = 8)",
        0.0,
        40.0,
        8.0,
        0.5,
    )

    # Wrong-size incidence & rework
    st.markdown("**Wrong-size / wrong-fit risk**")
    cα, cβ = st.columns(2)
    with cα:
        p_wrong_alpha = st.number_input("Beta α", 0.5, 50.0, 2.0, 0.5)
    with cβ:
        p_wrong_beta = st.number_input("Beta β", 10.0, 1000.0, 198.0, 1.0)
    p_wrong_mean = p_wrong_alpha / (p_wrong_alpha + p_wrong_beta)

    rework_hours = st.number_input(
        "Rework hours per wrong-size incident",
        1.0,
        40.0,
        6.0,
        0.5,
    )

    st.markdown("**Labor & calendar**")
    rate = st.number_input("Loaded labor rate ($/hr)", 20.0, 300.0, 62.0, 1.0)
    workdays_per_year = st.number_input("Workdays per year", 200, 365, 260, 1)

    st.markdown("---")
    st.header("Gantry – Manual Labor & Risk")

    st.subheader("Manual QC and Rework (per unit)")
    g1, g2, g3 = st.columns(3)
    with g1:
        manual_frame_hr = st.number_input(
            "Frame manual QC hrs",
            0.0,
            40.0,
            10.0,
            0.5,
        )
    with g2:
        manual_final_hr = st.number_input(
            "Final module QC hrs",
            0.0,
            40.0,
            12.0,
            0.5,
        )
    with g3:
        manual_rework_hr = st.number_input(
            "Rework hrs per module",
            0.0,
            40.0,
            10.0,
            0.5,
        )

    st.subheader("Late Defect Risk (final modules)")
    r1, r2, r3 = st.columns(3)
    with r1:
        p_late_manual = st.number_input(
            "Late defect prob – manual (%)",
            0.0,
            10.0,
            2.0,
            0.1,
        ) / 100.0
    with r2:
        p_late_gantry = st.number_input(
            "Late defect prob – gantry (%)",
            0.0,
            10.0,
            1.0,
            0.1,
        ) / 100.0
    with r3:
        severity = st.number_input(
            "Severity (% of module value)",
            0.1,
            20.0,
            2.0,
            0.1,
        ) / 100.0

    st.markdown("---")
    st.header("Investment")

    handheld_capex = st.number_input(
        "Handheld CAPEX ($)",
        50_000,
        1_000_000,
        260_000,
        10_000,
    )

    gantry_capex = st.number_input(
        "Gantry CAPEX per unit ($)",
        500_000,
        5_000_000,
        1_479_552,
        25_000,
    )

    reprogram_cost = st.number_input(
        "Reprogram per additional project ($)",
        0,
        200_000,
        40_000,
        5_000,
    )

    # Base assumption: 1 gantry, 3 projects
    num_gantries = st.number_input("Number of gantries", min_value=1, max_value=5, value=1, step=1)
    projects_using_gantry = st.number_input(
        "Number of projects using the gantry",
        min_value=1,
        max_value=10,
        value=3,
        step=1,
    )

# -------------------------- CALCULATIONS --------------------------
total_days = sum(p["days"] for p in st.session_state.projects.values())

# ---------- Handheld savings (deterministic, matching base model) ----------
labor_savings = 0.0
rework_savings = 0.0

for p in st.session_state.projects.values():
    parts_day = p["parts_per_day"]
    d = p["days"]

    scanning_labor_day = parts_day * (handheld_scan_mean / 60.0) * rate
    manual_labor_day = manual_hours_day * rate

    labor_saving_day = max(manual_labor_day - scanning_labor_day, 0.0)
    opp_gain_day = parts_day * p_wrong_mean * rework_hours * rate

    labor_savings += labor_saving_day * d
    rework_savings += opp_gain_day * d

hh_total_benefit = labor_savings + rework_savings
hh_investment = handheld_capex

hh_roi = (hh_total_benefit - hh_investment) / hh_investment if hh_investment > 0 else 0.0
hh_annual_savings = (
    hh_total_benefit / total_days * workdays_per_year if total_days > 0 else 0.0
)
hh_payback_years = (
    hh_investment / hh_annual_savings if hh_annual_savings > 0 else float("inf")
)

# ---------- Gantry savings (deterministic, matching base model) ----------
gantry_frame_hr = 0.25
gantry_final_hr = 0.25
gantry_rework_hr = 1.0

saving_per_frame = max(manual_frame_hr - gantry_frame_hr, 0.0) * rate
saving_per_module = (
    max(manual_final_hr - gantry_final_hr, 0.0) +
    max(manual_rework_hr - gantry_rework_hr, 0.0)
) * rate

gn_labor = 0.0
gn_risk = 0.0
delta_p_late = max(p_late_manual - p_late_gantry, 0.0)

for p in st.session_state.projects.values():
    gn_labor += p["frames"] * saving_per_frame + p["modules"] * saving_per_module
    gn_risk += p["modules"] * delta_p_late * severity * p["module_value"]

gn_total_benefit = gn_labor + gn_risk

reprogram_total = reprogram_cost * num_gantries * max(projects_using_gantry - 1, 0)
gn_investment = num_gantries * gantry_capex + reprogram_total

gn_roi = (gn_total_benefit - gn_investment) / gn_investment if gn_investment > 0 else 0.0
gn_annual_savings = (
    gn_total_benefit / total_days * workdays_per_year if total_days > 0 else 0.0
)
gn_payback_years = (
    gn_investment / gn_annual_savings if gn_annual_savings > 0 else float("inf")
)

# -------------------------- DISPLAY --------------------------
st.header("Financial Summary")

c1, c2 = st.columns(2)

with c1:
    st.subheader("Handheld System (Receiving)")
    st.metric("Total Benefit", f"${hh_total_benefit:,.0f}")
    st.caption(f"Labor savings: ${labor_savings:,.0f} | Wrong-size avoidance: ${rework_savings:,.0f}")
    st.metric("Investment", f"${hh_investment:,.0f}")
    st.metric("ROI", f"{hh_roi:.2f}x")
    st.metric("Payback Period", f"{hh_payback_years:.2f} years")

with c2:
    st.subheader(f"Gantry System ({num_gantries} unit{'s' if num_gantries > 1 else ''})")
    st.metric("Total Benefit", f"${gn_total_benefit:,.0f}")
    st.caption(f"Labor savings: ${gn_labor:,.0f} | Late-defect EV reduction: ${gn_risk:,.0f}")
    st.metric("Investment", f"${gn_investment:,.0f}")
    if reprogram_total > 0:
        st.caption(f"{num_gantries} × ${gantry_capex:,.0f} + ${reprogram_total:,.0f} reprogram")
    st.metric("ROI", f"{gn_roi:.2f}x")
    st.metric("Payback Period", f"{gn_payback_years:.2f} years")

st.info(
    f"""
**Defaults** in this app match the base ROI model:

- Manual receiving: **{manual_hours_day:.1f} hours/day**, labor rate **${rate:.0f}/hr**  
- Scan time mean: **{handheld_scan_mean:.1f} minutes/part**  
- Wrong-size probability ≈ **{p_wrong_mean*100:.2f}%**  
- Rework: **{rework_hours:.1f} hours/incident**  
- Portfolio runtime: **{total_days} project days**, annualized to **{workdays_per_year} workdays/year**  
- Gantry: **{num_gantries} unit**, used on **{projects_using_gantry} projects**
"""
)
