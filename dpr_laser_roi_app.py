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
        st.session_state.projects[new_proj] = {'days': 100, 'frames': 500, 'modules': 200, 'parts_per_day': 20.0, 'module_value': 200000}
        st.rerun()

if len(st.session_state.projects) > 1:
    to_remove = st.sidebar.selectbox("Remove project", options=["—"] + list(st.session_state.projects.keys()))
    if st.sidebar.button("Remove Selected") and to_remove != "—":
        del st.session_state.projects[to_remove]
        st.rerun()

# -------------------------- INPUTS --------------------------
st.sidebar.header("Labor & Process Assumptions")
col1, col2 = st.sidebar.columns(2)
with col1:
    manual_frame_hr = st.number_input("Manual frame time (hrs)", 5.0, 20.0, 10.0, 0.5)
    manual_final_hr = st.number_input("Manual final scan (hrs)", 8.0, 20.0, 12.0, 0.5)
    manual_rework_hr = st.number_input("Manual rework time (hrs)", 5.0, 20.0, 10.0, 0.5)
with col2:
    gantry_frame_hr = st.number_input("Gantry frame time (hrs)", 0.1, 2.0, 0.25, 0.05)
    gantry_final_hr = st.number_input("Gantry final scan (hrs)", 0.1, 2.0, 0.25, 0.05)
    gantry_rework_hr = st.number_input("Gantry rework time (hrs)", 0.5, 5.0, 1.0, 0.1)

st.sidebar.markdown("---")
st.sidebar.subheader("Financial Inputs")
rate = st.sidebar.slider("Foreman loaded rate ($/hr)", 40, 150, 62, 5)
workdays_per_year = st.sidebar.slider("Workdays per year", 200, 300, 260, 10)

handheld_capex = st.sidebar.number_input("Handheld system CAPEX ($)", 100000, 1000000, 260000, 10000)
gantry_capex_base = st.sidebar.number_input("Gantry CAPEX per unit ($)", 1000000, 5000000, 1479552, 50000)
reprogram_per_project = st.sidebar.number_input("Reprogramming cost per extra project ($)", 0, 200000, 40000, 5000)
num_gantries = st.sidebar.selectbox("Number of gantries deployed", [1, 2, 3, 4], 1)
projects_used = st.sidebar.selectbox("Projects using gantry(s)", [1, 2, 3, 4, 5], 2)

st.sidebar.markdown("---")
st.sidebar.subheader("Uncertainty Ranges")
c1, c2, c3 = st.sidebar.columns(3)
with c1: scan_min = st.number_input("Scan time min (min)", 2.0, 12.0, 5.0, 0.5)
with c2: scan_mode = st.number_input("Scan time mode (min)", 4.0, 20.0, 7.5, 0.5)
with c3: scan_max = st.number_input("Scan time max (min)", 6.0, 30.0, 10.0, 0.5)

p_wrong_alpha = st.sidebar.slider("Error rate α (Beta)", 0.5, 15.0, 2.0, 0.5)
p_wrong_beta = st.sidebar.slider("Error rate β (Beta)", 50.0, 600.0, 198.0, 10.0)
sev_min = st.sidebar.number_input("Severity min (%)", 0.0, 0.2, 0.01, 0.005, format="%.3f")
sev_mode = st.sidebar.number_input("Severity mode (%)", 0.005, 0.2, 0.02, 0.005, format="%.3f")
sev_max = st.sidebar.number_input("Severity max (%)", 0.01, 0.3, 0.05, 0.01, format="%.3f")

# Project Inputs
st.sidebar.markdown("---")
st.sidebar.subheader("Project Details")
for proj_name, defaults in st.session_state.projects.items():
    with st.sidebar.expander(f"Edit {proj_name}", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.projects[proj_name]['days'] = st.number_input(f"{proj_name} days", 1, 2000, defaults['days'], key=f"days_{proj_name}")
            st.session_state.projects[proj_name]['frames'] = st.number_input(f"{proj_name} frames", 1, 10000, defaults['frames'], key=f"frames_{proj_name}")
            st.session_state.projects[proj_name]['modules'] = st.number_input(f"{proj_name} modules", 1, 5000, defaults['modules'], key=f"modules_{proj_name}")
        with col2:
            st.session_state.projects[proj_name]['parts_per_day'] = st.number_input(f"{proj_name} parts/day", 1.0, 100.0, defaults['parts_per_day'], 0.5, key=f"ppd_{proj_name}")
            st.session_state.projects[proj_name]['module_value'] = st.number_input(f"{proj_name} value ($)", 10000, 5000000, defaults['module_value'], 10000, key=f"value_{proj_name}")

# -------------------------- CALCULATIONS --------------------------
total_days = sum(p['days'] for p in st.session_state.projects.values())

def tri_mean(a, m, b): return (a + m + b) / 3
def beta_mean(a, b): return a / (a + b)

scan_mean = tri_mean(scan_min, scan_mode, scan_max)
p_wrong_mean = beta_mean(p_wrong_alpha, p_wrong_beta)
severity_mean = tri_mean(sev_min, sev_mode, sev_max)
p_late_manual = beta_mean(4, 196)
p_late_gantry = beta_mean(1, 99)

def calculate_roi():
    # Handheld
    hh_savings = 0
    for p in st.session_state.projects.values():
        labor_save = (manual_frame_hr + manual_final_hr + manual_rework_hr) * rate - p['parts_per_day'] * (scan_mean / 60) * rate
        rework_save = p['parts_per_day'] * p_wrong_mean * 6 * rate
        hh_savings += (labor_save + rework_save) * p['days']

    hh_roi = (hh_savings - handheld_capex) / handheld_capex
    hh_payback = handheld_capex / (hh_savings / total_days * workdays_per_year) if hh_savings > 0 else 999

    # Gantry
    gn_savings = 0
    for p in st.session_state.projects.values():
        labor_save = p['frames'] * (manual_frame_hr - gantry_frame_hr) * rate + \
                     p['modules'] * ((manual_final_hr - gantry_final_hr) + (manual_rework_hr - gantry_rework_hr)) * rate
        ev_save = p['modules'] * (p_late_manual - p_late_gantry) * severity_mean * p['module_value']
        gn_savings += labor_save + ev_save

    investment = num_gantries * gantry_capex_base + reprogram_per_project * num_gantries * max(projects_used - 1, 0)
    gn_roi = (gn_savings - investment) / investment if investment > 0 else 0
    gn_payback = investment / (gn_savings / total_days * workdays_per_year) if gn_savings > 0 else 999

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

        hh_roi_list = []
        hh_payback_list = []
        gn_roi_list = []
        gn_payback_list = []

        for i in range(N):
            # Temporarily override means
            temp_scan = scan_times[i]
            temp_p_wrong = p_wrongs[i]
            temp_sev = severities[i]

            # Handheld
            hh_sav_i = 0
            for p in st.session_state.projects.values():
                labor_save = (manual_frame_hr + manual_final_hr + manual_rework_hr) * rate - p['parts_per_day'] * (temp_scan / 60) * rate
                rework_save = p['parts_per_day'] * temp_p_wrong * 6 * rate
                hh_sav_i += (labor_save + rework_save) * p['days']
            hh_roi_i = (hh_sav_i - handheld_capex) / handheld_capex
            hh_payback_i = handheld_capex / (hh_sav_i / total_days * workdays_per_year) if hh_sav_i > 0 else 999

            # Gantry
            gn_sav_i = 0
            for p in st.session_state.projects.values():
                labor_save = p['frames'] * (manual_frame_hr - gantry_frame_hr) * rate + \
                             p['modules'] * ((manual_final_hr - gantry_final_hr) + (manual_rework_hr - gantry_rework_hr)) * rate
                ev_save = p['modules'] * (p_late_manual - p_late_gantry) * temp_sev * p['module_value']
                gn_sav_i += labor_save + ev_save
            investment_i = num_gantries * gantry_capex_base + reprogram_per_project * num_gantries * max(projects_used - 1, 0)
            gn_roi_i = (gn_sav_i - investment_i) / investment_i if investment_i > 0 else 0
            gn_payback_i = investment_i / (gn_sav_i / total_days * workdays_per_year) if gn_sav_i > 0 else 999

            hh_roi_list.append(hh_roi_i)
            hh_payback_list.append(hh_payback_i)
            gn_roi_list.append(gn_roi_i)
            gn_payback_list.append(gn_payback_i)

        st.success("Monte Carlo Complete!")

        # Histograms
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

        # Sensitivity Button
        if st.button("Show Sensitivity Tornado Charts"):
            # Run sensitivity
            sensitivity_vars = {
                "Foreman Rate": ("rate", 0.8, 1.2),
                "Workdays/Year": ("workdays_per_year", 0.9, 1.1),
                "Handheld CAPEX": ("handheld_capex", 0.9, 1.1),
                "Gantry CAPEX": ("gantry_capex_base", 0.9, 1.1),
                "Reprogram Cost": ("reprogram_per_project", 0.8, 1.2),
                "Scan Time": ("scan_mean", 0.8, 1.2),
                "Error Rate": ("p_wrong_mean", 0.8, 1.2),
                "Severity": ("severity_mean", 0.8, 1.2),
            }

            hh_delta = {}
            gn_delta = {}
            for label, (var, low, high) in sensitivity_vars.items():
                orig = eval(var)
                globals()[var] = orig * low
                _, h_low, _, _, _, g_low, _ = calculate_roi()
                globals()[var] = orig * high
                _, h_high, _, _, _, g_high, _ = calculate_roi()
                globals()[var] = orig
                hh_delta[label] = (h_low - hh_roi, h_high - hh_roi)
                gn_delta[label] = (g_low - gn_roi, g_high - gn_roi)

            def plot_tornado(data, base, title):
                labels = sorted(data, key=lambda k: max(abs(data[k][0]), abs(data[k][1])), reverse=True)
                low = [data[l][0] for l in labels]
                high = [data[l][1] for l in labels]
                fig, ax = plt.subplots(figsize=(10, 6))
                y = np.arange(len(labels))
                ax.barh(y, low, left=base, color="#e74c3c", label="−20%")
                ax.barh(y, high, left=base, color="#27ae60", label="+20%")
                ax.set_yticks(y); ax.set_yticklabels(labels)
                ax.set_xlabel("Δ ROI (x)"); ax.set_title(title)
                ax.legend(); ax.grid(True, axis='x', alpha=0.3)
                return fig

            c1, c2 = st.columns(2)
            with c1: st.pyplot(plot_tornado(hh_delta, hh_roi, "Handheld ROI Sensitivity"))
            with c2: st.pyplot(plot_tornado(gn_delta, gn_roi, "Gantry ROI Sensitivity"))

# -------------------------- RECOMMENDATION --------------------------
st.markdown("---")
st.success(f"""
**Recommendation**

**Deploy {num_gantries} Gantry System(s)** → **{gn_roi:.2f}x ROI** • **{gn_pb*12:.1f} months** payback  
Handheld System → **{hh_roi:.2f}x ROI** • **{hh_pb:.1f} years** payback  

**Gantry is the superior investment.**
""")
st.caption("DPR Construction • Laser Scan Car Wash • 2025")
