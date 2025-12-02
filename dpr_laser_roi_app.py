import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="DPR Laser ROI Model", layout="wide")

# -------------------------- BRANDING --------------------------
col_logo, col_title = st.columns([1, 4])
with col_logo:
    st.image("dpr_laserscan_logo.png", use_column_width=True)
with col_title:
    st.title("DPR Laser Scan Car Wash ROI Model")
    st.markdown("**Handheld vs Gantry** • Fully customizable financial model")

# -------------------------- PROJECT MANAGER (Add/Remove Projects) --------------------------
if 'projects' not in st.session_state:
    st.session_state.projects = {
        'Project 1': {'days': 650, 'frames': 2880, 'modules': 1440, 'parts_per_day': 24.0, 'module_value': 100000},
        'Project 2': {'days': 168, 'frames': 1400, 'modules': 700, 'parts_per_day': 20.0, 'module_value': 474000},
        'Project 3': {'days': 42,  'frames': 90,   'modules': 45,  'parts_per_day': 26.4, 'module_value': 650000},
    }

st.sidebar.header("Project Manager")
new_proj = st.sidebar.text_input("Add new project (e.g., Project 4)")
if st.sidebar.button("Add Project") and new_proj:
    if new_proj not in st.session_state.projects:
        st.session_state.projects[new_proj] = {
            'days': 100,
            'frames': 500,
            'modules': 200,
            'parts_per_day': 20.0,
            'module_value': 200000,
        }
        st.rerun()

if len(st.session_state.projects) > 1:
    to_remove = st.sidebar.selectbox("Remove project", options=["—"] + list(st.session_state.projects.keys()))
    if st.sidebar.button("Remove Selected") and to_remove != "—":
        del st.session_state.projects[to_remove]
        st.rerun()

# -------------------------- INPUTS --------------------------
st.sidebar.header("Labor & Process Assumptions")

# Receiving / handheld side
col1, col2 = st.sidebar.columns(2)
with col1:
    manual_receiving_hours_day = st.number_input(
        "Manual receiving hrs/day", 0.0, 40.0, 8.0, 0.5
    )
    rework_hours = st.number_input(
        "Wrong-size rework hrs/incident", 1.0, 40.0, 6.0, 0.5
    )

# Gantry / QC side
with col2:
    manual_frame_hr = st.number_input("Manual frame time (hrs)", 5.0, 20.0, 10.0, 0.5)
    manual_final_hr = st.number_input("Manual final scan (hrs)", 8.0, 20.0, 12.0, 0.5)
    manual_rework_hr = st.number_input("Manual rework time (hrs)", 5.0, 20.0, 10.0, 0.5)

st.sidebar.markdown("**Gantry process times**")
g1, g2, g3 = st.sidebar.columns(3)
with g1:
    gantry_frame_hr = st.number_input("Gantry frame (hrs)", 0.1, 2.0, 0.25, 0.05)
with g2:
    gantry_final_hr = st.number_input("Gantry final (hrs)", 0.1, 2.0, 0.25, 0.05)
with g3:
    gantry_rework_hr = st.number_input("Gantry rework (hrs)", 0.5, 5.0, 1.0, 0.1)

st.sidebar.markdown("---")
st.sidebar.subheader("Financial Inputs")
rate = st.sidebar.slider("Foreman loaded rate ($/hr)", 40, 150, 62, 5)
workdays_per_year = st.sidebar.slider("Workdays per year", 200, 300, 260, 10)

handheld_capex = st.sidebar.number_input("Handheld system CAPEX ($)", 100000, 1000000, 260000, 10000)
gantry_capex_base = st.sidebar.number_input("Gantry CAPEX per unit ($)", 1000000, 5000000, 1479552, 50000)
reprogram_per_project = st.sidebar.number_input("Reprogramming cost per extra project ($)", 0, 200000, 40000, 5000)

# Force gantry = 1 unit (per your request)
num_gantries = 1
projects_used = st.sidebar.selectbox("Projects using the gantry", [1, 2, 3, 4, 5], 2)

st.sidebar.markdown("---")
st.sidebar.subheader("Uncertainty Ranges (Handheld & Risk)")
c1, c2, c3 = st.sidebar.columns(3)
with c1:
    scan_min = st.number_input("Scan time min (min)", 2.0, 12.0, 5.0, 0.5)
with c2:
    scan_mode = st.number_input("Scan time mode (min)", 4.0, 20.0, 7.5, 0.5)
with c3:
    scan_max = st.number_input("Scan time max (min)", 6.0, 30.0, 10.0, 0.5)

p_wrong_alpha = st.sidebar.slider("Wrong-size α (Beta)", 0.5, 15.0, 2.0, 0.5)
p_wrong_beta = st.sidebar.slider("Wrong-size β (Beta)", 50.0, 600.0, 198.0, 10.0)
sev_min = st.sidebar.number_input("Late defect severity min (%)", 0.0, 0.2, 0.01, 0.005, format="%.3f")
sev_mode = st.sidebar.number_input("Late defect severity mode (%)", 0.005, 0.2, 0.02, 0.005, format="%.3f")
sev_max = st.sidebar.number_input("Late defect severity max (%)", 0.01, 0.3, 0.05, 0.01, format="%.3f")

# Project Inputs
st.sidebar.markdown("---")
st.sidebar.subheader("Project Details")
for proj_name, defaults in st.session_state.projects.items():
    with st.sidebar.expander(f"Edit {proj_name}", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.projects[proj_name]['days'] = st.number_input(
                f"{proj_name} days", 1, 2000, defaults['days'], key=f"days_{proj_name}"
            )
            st.session_state.projects[proj_name]['frames'] = st.number_input(
                f"{proj_name} frames", 1, 10000, defaults['frames'], key=f"frames_{proj_name}"
            )
            st.session_state.projects[proj_name]['modules'] = st.number_input(
                f"{proj_name} modules", 1, 5000, defaults['modules'], key=f"modules_{proj_name}"
            )
        with col2:
            st.session_state.projects[proj_name]['parts_per_day'] = st.number_input(
                f"{proj_name} parts/day", 1.0, 100.0, defaults['parts_per_day'], 0.5, key=f"ppd_{proj_name}"
            )
            st.session_state.projects[proj_name]['module_value'] = st.number_input(
                f"{proj_name} value ($)", 10000, 5000000, defaults['module_value'], 10000, key=f"value_{proj_name}"
            )

# -------------------------- CALCULATIONS --------------------------
total_days = sum(p['days'] for p in st.session_state.projects.values())

def tri_mean(a, m, b): return (a + m + b) / 3.0
def beta_mean(a, b): return a / (a + b)

scan_mean = tri_mean(scan_min, scan_mode, scan_max)          # minutes
p_wrong_mean = beta_mean(p_wrong_alpha, p_wrong_beta)        # probability
severity_mean = tri_mean(sev_min, sev_mode, sev_max)         # fraction
p_late_manual = beta_mean(4, 196)                            # ~ 2%
p_late_gantry = beta_mean(1, 99)                             # ~ 1%

def calculate_roi():
    # ---------------- HANDHELD (match base Python model) ----------------
    hh_savings = 0.0
    for p in st.session_state.projects.values():
        parts_day = p['parts_per_day']
        days = p['days']

        # Labor per day without handheld vs with handheld
        manual_labor_day = manual_receiving_hours_day * rate
        scanning_labor_day = parts_day * (scan_mean / 60.0) * rate

        labor_saving_day = max(manual_labor_day - scanning_labor_day, 0.0)
        rework_saving_day = parts_day * p_wrong_mean * rework_hours * rate

        hh_savings += (labor_saving_day + rework_saving_day) * days

    hh_roi = (hh_savings - handheld_capex) / handheld_capex if handheld_capex > 0 else 0.0
    hh_annual_sav = hh_savings / total_days * workdays_per_year if total_days > 0 else 0.0
    hh_payback = handheld_capex / hh_annual_sav if hh_annual_sav > 0 else 999.0

    # ---------------- GANTRY (frame + module QC) ----------------
    gn_savings = 0.0
    for p in st.session_state.projects.values():
        frames = p['frames']
        modules = p['modules']
        mv = p['module_value']

        # Labor savings: manual minus gantry, floored at 0
        frame_labor_save = max(manual_frame_hr - gantry_frame_hr, 0.0) * rate
        module_labor_save = (
            max(manual_final_hr - gantry_final_hr, 0.0) +
            max(manual_rework_hr - gantry_rework_hr, 0.0)
        ) * rate

        labor_save_total = frames * frame_labor_save + modules * module_labor_save

        # Expected value of late defects avoided
        delta_p = max(p_late_manual - p_late_gantry, 0.0)
        ev_per_module = delta_p * severity_mean * mv
        ev_save_total = modules * ev_per_module

        gn_savings += labor_save_total + ev_save_total

    investment = num_gantries * gantry_capex_base + \
                 reprogram_per_project * num_gantries * max(projects_used - 1, 0)

    gn_roi = (gn_savings - investment) / investment if investment > 0 else 0.0
    gn_annual_sav = gn_savings / total_days * workdays_per_year if total_days > 0 else 0.0
    gn_payback = investment / gn_annual_sav if gn_annual_sav > 0 else 999.0

    return hh_savings, hh_roi, hh_payback, gn_savings, investment, gn_roi, gn_payback

hh_sav, hh_roi, hh_pb, gn_sav, inv, gn_roi, gn_pb = calculate_roi()

# -------------------------- RESULTS --------------------------
st.header("Financial Summary")
c1, c2 = st.columns(2)
with c1:
    st.metric("Handheld Total Savings", f"${hh_sav:,.0f}")
    st.metric("Handheld ROI", f"{hh_roi:.2f}x")
    st.metric("Handheld Payback", f"{hh_pb:.2f} years")
with c2:
    st.metric("Gantry Total Savings", f"${gn_sav:,.0f}")
    st.metric("Gantry Investment", f"${inv:,.0f}")
    st.metric("Gantry ROI", f"{gn_roi:.2f}x")
    st.metric("Gantry Payback", f"{gn_pb:.2f} years")

# -------------------------- MONTE CARLO --------------------------
run_mc = st.button("Run Monte Carlo Simulation (10,000 runs)", type="primary")

if run_mc:
    with st.spinner("Running 10,000 simulations..."):
        N = 10000
        np.random.seed(42)

        scan_times = np.random.triangular(scan_min, scan_mode, scan_max, N)
        p_wrongs = np.random.beta(p_wrong_alpha, p_wrong_beta, N)
        severities = np.random.triangular(sev_min, sev_mode, sev_max, N)

        hh_roi_list, hh_payback_list = [], []
        gn_roi_list, gn_payback_list = [], []

        for i in range(N):
            temp_scan = scan_times[i]
            temp_p_wrong = p_wrongs[i]
            temp_sev = severities[i]

            # ---- Handheld for this iteration ----
            hh_sav_i = 0.0
            for p in st.session_state.projects.values():
                parts_day = p['parts_per_day']
                days = p['days']

                manual_labor_day = manual_receiving_hours_day * rate
                scanning_labor_day = parts_day * (temp_scan / 60.0) * rate

                labor_saving_day = max(manual_labor_day - scanning_labor_day, 0.0)
                rework_saving_day = parts_day * temp_p_wrong * rework_hours * rate

                hh_sav_i += (labor_saving_day + rework_saving_day) * days

            hh_roi_i = (hh_sav_i - handheld_capex) / handheld_capex if handheld_capex > 0 else 0.0
            hh_annual_sav_i = hh_sav_i / total_days * workdays_per_year if total_days > 0 else 0.0
            hh_payback_i = handheld_capex / hh_annual_sav_i if hh_annual_sav_i > 0 else 999.0

            # ---- Gantry for this iteration ----
            gn_sav_i = 0.0
            for p in st.session_state.projects.values():
                frames = p['frames']
                modules = p['modules']
                mv = p['module_value']

                frame_labor_save = max(manual_frame_hr - gantry_frame_hr, 0.0) * rate
                module_labor_save = (
                    max(manual_final_hr - gantry_final_hr, 0.0) +
                    max(manual_rework_hr - gantry_rework_hr, 0.0)
                ) * rate

                labor_save_total = frames * frame_labor_save + modules * module_labor_save

                delta_p = max(p_late_manual - p_late_gantry, 0.0)
                ev_per_module = delta_p * temp_sev * mv
                ev_save_total = modules * ev_per_module

                gn_sav_i += labor_save_total + ev_save_total

            investment_i = num_gantries * gantry_capex_base + \
                           reprogram_per_project * num_gantries * max(projects_used - 1, 0)

            gn_roi_i = (gn_sav_i - investment_i) / investment_i if investment_i > 0 else 0.0
            gn_annual_sav_i = gn_sav_i / total_days * workdays_per_year if total_days > 0 else 0.0
            gn_payback_i = investment_i / gn_annual_sav_i if gn_annual_sav_i > 0 else 999.0

            hh_roi_list.append(hh_roi_i)
            hh_payback_list.append(hh_payback_i)
            gn_roi_list.append(gn_roi_i)
            gn_payback_list.append(gn_payback_i)

        st.success("Monte Carlo Complete!")

        col1, col2 = st.columns(2)
        with col1:
            fig, ax = plt.subplots()
            ax.hist(hh_roi_list, bins=60, color="#3498db", alpha=0.8, edgecolor='black')
            ax.axvline(hh_roi, color='red', lw=3, label=f"Base: {hh_roi:.2f}x")
            ax.set_title("Handheld ROI Distribution"); ax.set_xlabel("ROI (x)"); ax.legend()
            st.pyplot(fig)

            fig, ax = plt.subplots()
            ax.hist(hh_payback_list, bins=60, color="#3498db", alpha=0.8, edgecolor='black')
            ax.axvline(hh_pb, color='red', lw=3, label=f"Base: {hh_pb:.2f} yrs")
            ax.set_title("Handheld Payback Period"); ax.set_xlabel("Years"); ax.legend()
            st.pyplot(fig)

        with col2:
            fig, ax = plt.subplots()
            ax.hist(gn_roi_list, bins=60, color="#e67e22", alpha=0.8, edgecolor='black')
            ax.axvline(gn_roi, color='red', lw=3, label=f"Base: {gn_roi:.2f}x")
            ax.set_title("Gantry ROI Distribution"); ax.set_xlabel("ROI (x)"); ax.legend()
            st.pyplot(fig)

            fig, ax = plt.subplots()
            ax.hist(gn_payback_list, bins=60, color="#e67e22", alpha=0.8, edgecolor='black')
            ax.axvline(gn_pb, color='red', lw=3, label=f"Base: {gn_pb:.2f} yrs")
            ax.set_title("Gantry Payback Period"); ax.set_xlabel("Years"); ax.legend()
            st.pyplot(fig)

# -------------------------- RECOMMENDATION --------------------------
st.markdown("---")
st.success(f"""
**Recommendation (Base Inputs)**

Gantry System (1 unit) → **{gn_roi:.2f}x ROI** • **{gn_pb*12:.1f} months** payback  
Handheld System → **{hh_roi:.2f}x ROI** • **{hh_pb:.1f} years** payback  

Use the sidebar to adjust labor hours, error rates, and severity to see how the business case shifts.
""")
st.caption("DPR Construction • Laser Scan Car Wash • 2025")

