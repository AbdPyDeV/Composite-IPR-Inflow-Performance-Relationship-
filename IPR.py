import streamlit as st
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Composite IPR Tool", layout="wide")
st.title("Composite IPR (Inflow Performance Relationship)")

# --- SIDEBAR ---
st.sidebar.header("Input Parameters")
pr = st.sidebar.number_input("Pr (Reservoir Pressure) [psi]", min_value=1, value=2500)
pb = st.sidebar.number_input("Pb (Bubble Point Pressure) [psi]", min_value=0, value=1000)

st.sidebar.divider()
pwf_test = st.sidebar.number_input("Pwfₜ (Test Pressure) [psi]", min_value=0, max_value=int(pr), value=2000)
q_test = st.sidebar.number_input("Qₜ (Test Rate) [STB/d]", min_value=1, value=350)
pwf_target = st.sidebar.number_input("Pwf* (Target Pressure) [psi]", min_value=0, max_value=int(pr), value=1850)

# --- COMPOSITE MATH ENGINE ---
def calculate_q(p_val, pr, pb, q_test, pwf_test):
    # 1. Determine Productivity Index (J) based on test point
    if pwf_test >= pb:
        # Test point is in linear region
        j = q_test / (pr - pwf_test)
    else:
        # Test point is in Vogel region (Composite case)
        # q_test = q_linear_at_pb + q_vogel
        # q_test = J*(pr - pb) + (J*pb/1.8) * (1 - 0.2*(pwf_test/pb) - 0.8*(pwf_test/pb)**2)
        vogel_term = (1 - 0.2*(pwf_test/pb) - 0.8*(pwf_test/pb)**2)
        j = q_test / ((pr - pb) + (pb / 1.8) * vogel_term)

    # 2. Calculate Rate at the requested pressure (p_val)
    if p_val >= pb:
        return j * (pr - p_val)
    else:
        q_at_pb = j * (pr - pb)
        vogel_term = (1 - 0.2*(p_val/pb) - 0.8*(p_val/pb)**2)
        return q_at_pb + (j * pb / 1.8) * vogel_term

# Vectorize for the plot
pwf_range = np.linspace(0, pr, 100)
q_curve = [calculate_q(p, pr, pb, q_test, pwf_test) for p in pwf_range]
q_target = calculate_q(pwf_target, pr, pb, q_test, pwf_test)

# --- PLOT ---
fig = go.Figure()

# Add the curve
fig.add_trace(go.Scatter(x=q_curve, y=pwf_range, name="Composite IPR", line=dict(color='seagreen', width=3)))

# Add Pb line for visual reference
fig.add_hline(y=pb, line_dash="dash", line_color="orange", annotation_text="Bubble Point (Pb)")

# Add points
fig.add_trace(go.Scatter(x=[q_test], y=[pwf_test], mode='markers', name='Test Point', marker=dict(color='black', size=10)))
fig.add_trace(go.Scatter(x=[q_target], y=[pwf_target], mode='markers+text', name='Target', 
                         text=[f"{q_target:.1f}"], textposition="top right", marker=dict(color='red', size=10)))

fig.update_layout(xaxis_title="Rate (STB/d)", yaxis_title="Pressure (psi)", template="plotly_white", height=600)
st.plotly_chart(fig, use_container_width=True)

# --- RESULTS ---
col1, col2, col3 = st.columns(3)
state = "Undersaturated" if pr > pb else "Saturated"
col1.metric("Reservoir Status", state)
col2.metric("Target Rate", f"{q_target:.1f} STB/d")
# Calculate J for display
if pwf_test >= pb: j_disp = q_test / (pr - pwf_test)
else: j_disp = q_test / ((pr - pb) + (pb / 1.8) * (1 - 0.2*(pwf_test/pb) - 0.8*(pwf_test/pb)**2))
col3.metric("Productivity Index (J)", f"{j_disp:.2f}")