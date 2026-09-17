import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="LiFi 6G Analyzer",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- Custom CSS ----------------
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #00c6ff, #0072ff, #8e2de2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding-bottom: 0.5rem;
    }
    .sub-header {
        text-align: center;
        color: #888;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">LiFi 6G Analyzer</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Analyze Visible Light Communication performance for next-gen 6G networks</div>', unsafe_allow_html=True)

# ---------------- Sidebar Inputs ----------------
st.sidebar.header("Input Parameters")

led_power = st.sidebar.slider(
    "LED / Laser Power (W)", min_value=0.1, max_value=20.0,
    value=5.0, step=0.1,
    help="Transmit optical power of the LED/laser source"
)

distance = st.sidebar.slider(
    "Distance (m)", min_value=0.1, max_value=20.0,
    value=3.0, step=0.1,
    help="Distance between transmitter and receiver"
)

sensitivity = st.sidebar.slider(
    "Receiver Sensitivity (dBm)", min_value=-60.0, max_value=-5.0,
    value=-30.0, step=1.0,
    help="Minimum detectable signal power"
)

bandwidth = st.sidebar.slider(
    "Bandwidth (MHz)", min_value=1.0, max_value=500.0,
    value=100.0, step=1.0,
    help="Modulation bandwidth of the LiFi channel"
)

ambient_light = st.sidebar.slider(
    "Ambient Light (lux)", min_value=0.0, max_value=2000.0,
    value=300.0, step=10.0,
    help="Background light causing shot noise"
)

num_users = st.sidebar.slider(
    "Number of Users", min_value=1, max_value=50,
    value=5, step=1,
    help="Users sharing the LiFi access point"
)

obstruction = st.sidebar.slider(
    "Obstruction / Blockage (%)", min_value=0, max_value=100,
    value=10, step=1,
    help="Percentage of the optical path blocked"
)

st.sidebar.markdown("---")
st.sidebar.caption("Built for LiFi 6G research and education.")

# ---------------- Physics / Model ----------------
def compute_lifi_metrics(P_tx, d, sens_dbm, bw_mhz, amb_lux, users, blockage):
    ref_distance = 1.0
    path_loss_exp = 2.0
    geometric_loss_db = 20 * np.log10(max(d, 0.1) / ref_distance) * (path_loss_exp / 2.0)

    P_tx_dbm = 10 * np.log10(P_tx * 1000)

    blockage_factor = 1.0 - (blockage / 100.0)
    blockage_loss_db = -10 * np.log10(max(blockage_factor, 1e-6))

    ambient_loss_db = 0.0025 * amb_lux

    P_rx_dbm = P_tx_dbm - geometric_loss_db - blockage_loss_db - ambient_loss_db

    noise_floor_dbm = sens_dbm + 0.001 * amb_lux
    snr_db = P_rx_dbm - noise_floor_dbm
    snr_linear = 10 ** (snr_db / 10)
    snr_linear = max(snr_linear, 1e-6)

    bw_hz = bw_mhz * 1e6
    capacity_bps = bw_hz * np.log2(1 + snr_linear)
    per_user_bps = capacity_bps / users

    link_ok = P_rx_dbm >= sens_dbm and blockage < 90

    max_dist = ref_distance * 10 ** ((P_tx_dbm - sens_dbm - blockage_loss_db - ambient_loss_db) / (20 * path_loss_exp / 2.0))
    max_dist = max(max_dist, 0.0)

    return {
        "P_tx_dbm": P_tx_dbm,
        "P_rx_dbm": P_rx_dbm,
        "geometric_loss_db": geometric_loss_db,
        "blockage_loss_db": blockage_loss_db,
        "ambient_loss_db": ambient_loss_db,
        "snr_db": snr_db,
        "capacity_mbps": capacity_bps / 1e6,
        "per_user_mbps": per_user_bps / 1e6,
        "link_ok": link_ok,
        "max_dist": max_dist,
    }

metrics = compute_lifi_metrics(
    led_power, distance, sensitivity, bandwidth,
    ambient_light, num_users, obstruction
)

# ---------------- KPI Cards ----------------
st.markdown("### Key Performance Indicators")
c1, c2, c3, c4 = st.columns(4)

c1.metric("Received Power", f"{metrics['P_rx_dbm']:.2f} dBm",
          delta=f"{metrics['P_rx_dbm'] - sensitivity:.2f} dB vs sens.")
c2.metric("SNR", f"{metrics['snr_db']:.2f} dB")
c3.metric("Total Capacity", f"{metrics['capacity_mbps']:.2f} Mbps")
c4.metric("Per-User Rate", f"{metrics['per_user_mbps']:.2f} Mbps")

status_color = "#00ff88" if metrics["link_ok"] else "#ff4b4b"
status_text = "LINK ACTIVE" if metrics["link_ok"] else "LINK FAILED"
st.markdown(
    f"<h3 style='text-align:center;color:{status_color};'>{status_text}</h3>",
    unsafe_allow_html=True
)

st.markdown("---")

# ---------------- Detailed Metrics ----------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("Link Budget Breakdown")
    budget_df = pd.DataFrame({
        "Parameter": [
            "Transmit Power (dBm)",
            "Geometric Path Loss (dB)",
            "Blockage Loss (dB)",
            "Ambient Interference (dB)",
            "Received Power (dBm)",
            "Receiver Sensitivity (dBm)",
            "Link Margin (dB)"
        ],
        "Value": [
            f"{metrics['P_tx_dbm']:.2f}",
            f"{metrics['geometric_loss_db']:.2f}",
            f"{metrics['blockage_loss_db']:.2f}",
            f"{metrics['ambient_loss_db']:.2f}",
            f"{metrics['P_rx_dbm']:.2f}",
            f"{sensitivity:.2f}",
            f"{metrics['P_rx_dbm'] - sensitivity:.2f}"
        ]
    })
    st.dataframe(budget_df, use_container_width=True, hide_index=True)

with col2:
    st.subheader("System Parameters")
    params_df = pd.DataFrame({
        "Parameter": [
            "LED/Laser Power",
            "Distance",
            "Bandwidth",
            "Ambient Light",
            "Number of Users",
            "Obstruction"
        ],
        "Value": [
            f"{led_power} W",
            f"{distance} m",
            f"{bandwidth} MHz",
            f"{ambient_light} lux",
            f"{num_users}",
            f"{obstruction} %"
        ]
    })
    st.dataframe(params_df, use_container_width=True, hide_index=True)

st.markdown("---")

# ---------------- Charts ----------------
st.subheader("Performance Analysis")

tab1, tab2, tab3 = st.tabs(["Power vs Distance", "Capacity vs Bandwidth", "Capacity vs Users"])

with tab1:
    d_range = np.linspace(0.5, 20, 100)
    p_rx_curve = []
    for dd in d_range:
        m = compute_lifi_metrics(led_power, dd, sensitivity, bandwidth,
                                 ambient_light, num_users, obstruction)
        p_rx_curve.append(m["P_rx_dbm"])

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=d_range, y=p_rx_curve, mode='lines',
                             name='Received Power', line=dict(color='#00c6ff', width=3)))
    fig.add_hline(y=sensitivity, line_dash="dash", line_color="red",
                  annotation_text=f"Sensitivity ({sensitivity} dBm)")
    fig.add_vline(x=distance, line_dash="dot", line_color="yellow",
                  annotation_text=f"Current ({distance} m)")
    fig.update_layout(
        xaxis_title="Distance (m)", yaxis_title="Received Power (dBm)",
        template="plotly_dark", height=420
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    bw_range = np.linspace(1, 500, 100)
    cap_curve = []
    for bw in bw_range:
        m = compute_lifi_metrics(led_power, distance, sensitivity, bw,
                                 ambient_light, num_users, obstruction)
        cap_curve.append(m["capacity_mbps"])

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=bw_range, y=cap_curve, mode='lines',
                              name='Capacity', line=dict(color='#8e2de2', width=3)))
    fig2.add_vline(x=bandwidth, line_dash="dot", line_color="yellow",
                   annotation_text=f"Current ({bandwidth} MHz)")
    fig2.update_layout(
        xaxis_title="Bandwidth (MHz)", yaxis_title="Total Capacity (Mbps)",
        template="plotly_dark", height=420
    )
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    users_range = np.arange(1, 51)
    per_user_curve = []
    total_curve = []
    for u in users_range:
        m = compute_lifi_metrics(led_power, distance, sensitivity, bandwidth,
                                 ambient_light, u, obstruction)
        per_user_curve.append(m["per_user_mbps"])
        total_curve.append(m["capacity_mbps"])

    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=users_range, y=total_curve, mode='lines',
                              name='Total Capacity', line=dict(color='#00ff88', width=3)))
    fig3.add_trace(go.Scatter(x=users_range, y=per_user_curve, mode='lines',
                              name='Per-User Rate', line=dict(color='#ff6b6b', width=3)))
    fig3.add_vline(x=num_users, line_dash="dot", line_color="yellow",
                   annotation_text=f"Current ({num_users} users)")
    fig3.update_layout(
        xaxis_title="Number of Users", yaxis_title="Rate (Mbps)",
        template="plotly_dark", height=420
    )
    st.plotly_chart(fig3, use_container_width=True)

# ---------------- Coverage and Insights ----------------
st.markdown("---")
st.subheader("Coverage and Insights")

i1, i2 = st.columns(2)
with i1:
    st.info(f"Estimated Max Coverage Distance: {metrics['max_dist']:.2f} m")
    if metrics["link_ok"]:
        st.success("The LiFi link is operational with current settings.")
    else:
        st.error("Link failure detected. Reduce distance, blockage, or increase power.")

with i2:
    recommendations = []
    if obstruction > 50:
        recommendations.append("High blockage. Consider multiple APs or beam steering.")
    if ambient_light > 1000:
        recommendations.append("High ambient light. Add optical filters.")
    if metrics["per_user_mbps"] < 10 and metrics["link_ok"]:
        recommendations.append("Per-user rate below 10 Mbps. Consider reducing users or increasing bandwidth.")
    if not recommendations:
        recommendations.append("System parameters are well-balanced.")
    for r in recommendations:
        st.write(r)

st.markdown("---")
st.caption("LiFi 6G Analyzer | For research and educational purposes only.")
