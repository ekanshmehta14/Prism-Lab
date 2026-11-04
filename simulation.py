"""Interactive 360-degree prism-spectrometer simulation."""
import math
from pathlib import Path
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import physics as P
import ui

DIAL_COMPONENT = components.declare_component(
    "prism_dial",
    path=str(Path(__file__).resolve().parent / "dial_component"),
)

def deviations(A, mu_violet, mu_red):
    lv = P.WAVELENGTH["Violet"]
    lr = P.WAVELENGTH["Red"]
    b = (mu_violet - mu_red) / (1 / lv ** 2 - 1 / lr ** 2)
    a = mu_violet - b / lv ** 2
    return {name: (a + b / wavelength ** 2, P.min_deviation(A, a + b / wavelength ** 2))
            for name, wavelength, _ in P.LINES}


def telescope_svg(reading, side, selected_line, line_angle, prism_angle, hit):
    arm_angle = math.radians(reading - 180)
    color = "#5EEAD4" if selected_line == "UDR" else P.COLOUR[selected_line]
    status = "#22C55E" if hit else "#64748B"
    return f'''
    <svg viewBox="0 0 900 390" width="100%" style="background:#0D1424;border-radius:16px">
      <defs>
        <linearGradient id="tube" x1="0" x2="1">
          <stop offset="0" stop-color="#334155"/><stop offset=".5" stop-color="#94A3B8"/><stop offset="1" stop-color="#334155"/>
        </linearGradient>
      </defs>
      <circle cx="450" cy="245" r="130" fill="none" stroke="#24304A" stroke-width="10"/>
      <circle cx="450" cy="245" r="24" fill="#121A2B" stroke="#94A3B8" stroke-width="4"/>
      <polygon points="390,155 510,155 540,335 360,335" fill="#111827" stroke="#5EEAD4" stroke-width="3"/>
      <polygon points="450,180 410,280 490,280" fill="#1B2A44" stroke="#C4B5FD" stroke-width="2"/>
      <line x1="450" y1="245" x2="{450 + 210 * math.cos(arm_angle):.1f}" y2="{245 + 210 * math.sin(arm_angle):.1f}"
            stroke="{status}" stroke-width="28" stroke-linecap="round"/>
      <circle cx="{450 + 210 * math.cos(arm_angle):.1f}" cy="{245 + 210 * math.sin(arm_angle):.1f}"
              r="56" fill="#1E293B" stroke="url(#tube)" stroke-width="18"/>
      <circle cx="{450 + 210 * math.cos(arm_angle):.1f}" cy="{245 + 210 * math.sin(arm_angle):.1f}"
              r="20" fill="#05070D" stroke="#94A3B8" stroke-width="4"/>
      <rect x="70" y="210" width="140" height="70" rx="12" fill="#334155" stroke="#94A3B8" stroke-width="4"/>
      <line x1="210" y1="245" x2="390" y2="245" stroke="#E8ECF5" stroke-width="3"/>
      <line x1="450" y1="245" x2="450" y2="100" stroke="#94A3B8" stroke-width="2" stroke-dasharray="8 7"/>
      <line x1="450" y1="245" x2="{450 + 200 * math.cos(math.radians(line_angle - 90)):.1f}"
            y2="{245 + 200 * math.sin(math.radians(line_angle - 90)):.1f}"
            stroke="{color}" stroke-width="5" opacity=".9"/>
      <text x="450" y="38" fill="#E8ECF5" font-size="20" text-anchor="middle">
        Telescope reading {reading:.2f}° — {side} side
      </text>
      <text x="450" y="370" fill="#A9B4CC" font-size="16" text-anchor="middle">
        Prism A = {prism_angle:.1f}°
      </text>
    </svg>
    '''


def render(ss, add_obs, add_simulation_readings=None):
    st.subheader("Virtual spectrometer bench")
    mode = st.radio("Simulation values", ["Example values", "My own values"], horizontal=True)

    if mode == "Example values":
        cfg = {"A": 60.0, "mu_v": 1.6916, "mu_red": 1.6386}
    else:
        c1, c2, c3 = st.columns(3)
        cfg = {
            "A": c1.number_input("Prism angle A (°)", 30.0, 75.0, 60.0, 0.1),
            "mu_v": c2.number_input("μ violet", 1.001, 2.500, 1.6916, 0.0001, format="%.4f"),
            "mu_red": c3.number_input("μ red", 1.001, 2.500, 1.6386, 0.0001, format="%.4f"),
        }

    if cfg["mu_v"] <= cfg["mu_red"]:
        st.error("Violet refractive index must be greater than red refractive index.")
        return

    if not ss.setdefault("sim_initialized", False):
        ss.sim_direct = 180.0
        ss.sim_reading = 180.0
        ss.sim_line = "Green"
        ss.sim_dial_ack = 0
        ss.sim_initialized = True
    ss.setdefault("sim_dial_ack", 0)
    if ss.sim_line not in P.LINE_NAMES:
        ss.sim_line = "Green"

    dev = deviations(cfg["A"], cfg["mu_v"], cfg["mu_red"])
    direct = st.number_input("Direct-ray dial reading (°)", 0.0, 359.99, float(ss.sim_direct), 0.01)
    ss.sim_direct = direct

    c1, c2 = st.columns(2)
    if c1.button("Record direct ray", type="primary"):
        ss.direct = direct
        ss.sim_reading = direct
        st.success(f"Direct reading recorded: {direct:.2f}°")
    if c2.button("Reset telescope"):
        ss.sim_reading = direct
        st.rerun()

    sim_line_options = ["UDR"] + P.LINE_NAMES
    selected_line = st.selectbox(
        "Spectral line / direct ray to observe",
        sim_line_options,
        index=sim_line_options.index(ss.sim_line) if ss.sim_line in sim_line_options else 1,
    )
    ss.sim_line = selected_line
    line_deviation = 0.0 if selected_line == "UDR" else dev[selected_line][1]
    selected_color = "#5EEAD4" if selected_line == "UDR" else P.COLOUR[selected_line]
    reading = float(ss.sim_reading)
    side = "Right" if reading <= 180.0 else "Left"
    ss.sim_side = side
    v1_reading = (reading + 90.0) % 360
    v2_reading = (reading - 90.0) % 360

    if selected_line == "UDR":
        expected = direct if side == "Right" else (direct + 180.0)
    else:
        expected = (direct - line_deviation) if side == "Right" else (direct + line_deviation)
    expected %= 360
    hit = P.angle_diff(reading, expected) <= 0.15

    # The dial, vernier readouts and eyepiece cross-wire all live in ONE client-side
    # component, so they move together while the arm is dragged. Python is told only
    # once, when the user lets go. The key is constant so the iframe is never rebuilt.
    dial_value = DIAL_COMPONENT(
        reading=reading,
        direct=float(direct),
        lineDeviation=float(line_deviation),
        isUdr=selected_line == "UDR",
        prismAngle=cfg["A"],
        color=selected_color,
        ack=int(ss.sim_dial_ack),
        key="prism_dial",
        default=None,
    )
    if isinstance(dial_value, dict):
        nonce = int(dial_value.get("n", 0))
        if nonce > ss.sim_dial_ack:          # a new release from the user, not a stale value
            ss.sim_dial_ack = nonce
            new_reading = float(dial_value["v"]) % 360
            if P.angle_diff(new_reading, reading) >= 0.0001:
                ss.sim_reading = new_reading
            st.rerun()

    b1, b2, b3, b4 = st.columns(4)
    for col, label, delta in (
        (b1, "-1°", -1.0), (b2, "-0.01°", -0.01),
        (b3, "+0.01°", 0.01), (b4, "+1°", 1.0),
    ):
        if col.button(label, use_container_width=True):
            ss.sim_reading = (reading + delta) % 360
            st.rerun()

    if st.button("Record both vernier readings", type="primary", disabled=not hit):
        if add_simulation_readings:
            add_simulation_readings(
                selected_line,
                ss.sim_side,
                round(v1_reading, 4),
                round(v2_reading, 4),
            )
        else:
            add_obs(selected_line, ss.sim_side, round(v1_reading, 4), "Simulated telescope", "V1")
            add_obs(selected_line, ss.sim_side, round(v2_reading, 4), "Simulated telescope", "V2")
        st.toast(f"Recorded {selected_line} readings for V1 and V2")
