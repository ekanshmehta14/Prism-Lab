"""Interactive 360-degree prism-spectrometer simulation."""
import math
from pathlib import Path
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import physics as P

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
        ss.sim_dial_component_value = 180.0
        ss.sim_initialized = True
    if ss.sim_line not in P.LINE_NAMES:
        ss.sim_line = "Green"

    dev = deviations(cfg["A"], cfg["mu_v"], cfg["mu_red"])
    direct = st.number_input("Direct-ray dial reading (°)", 0.0, 359.99, float(ss.sim_direct), 0.01)
    ss.sim_direct = direct

    c1, c2 = st.columns(2)
    if c1.button("Record direct ray", type="primary"):
        ss.direct = direct
        ss.sim_dial_ignore_value = float(ss.sim_reading)
        ss.sim_reading = direct
        ss.sim_dial_component_value = direct
        st.success(f"Direct reading recorded: {direct:.2f}°")
    if c2.button("Reset telescope"):
        ss.sim_dial_ignore_value = float(ss.sim_reading)
        ss.sim_reading = direct
        ss.sim_dial_component_value = direct
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
    st.markdown("---")
    dial_col, eye_col = st.columns([2.0, 1.0])
    reading = float(ss.sim_reading)
    ss.sim_reading = reading
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

    with dial_col:
        st.markdown(
            f"<div style='margin:0 0 .75rem;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.75rem'>"
            f"<div style='padding:.75rem 1rem;border:2px solid #5EEAD4;border-radius:14px;background:#12323A'>"
            f"<div style='color:#9AF3E5;font-size:.78rem;font-weight:700'>VERNIER V1</div>"
            f"<div style='font-size:1.55rem;font-weight:700;color:#FFFFFF'>{v1_reading:.2f}°</div></div>"
            f"<div style='padding:.75rem 1rem;border:2px solid #38BDF8;border-radius:14px;background:#102A40'>"
            f"<div style='color:#BAE6FD;font-size:.78rem;font-weight:700'>VERNIER V2</div>"
            f"<div style='font-size:1.55rem;font-weight:700;color:#FFFFFF'>{v2_reading:.2f}°</div></div>"
            f"</div>",
            unsafe_allow_html=True,
        )
        ss.setdefault("sim_dial_component_value", reading)
        dial_value = DIAL_COMPONENT(
            reading=reading,
            side=side,
            lineAngle=line_deviation,
            prismAngle=cfg["A"],
            color=selected_color,
            hit=hit,
            key=f"prism_dial_component_{side.lower()}_{int(round(reading * 100)):08d}",
            default=reading,
        )
        if isinstance(dial_value, (int, float)):
            dial_value = float(dial_value) % 360
            if abs(dial_value - reading) >= 0.0001:
                ss.sim_dial_component_value = dial_value
                ss.sim_reading = dial_value
                st.rerun()
        st.caption("Rotate the red arm with your mouse or finger.")
    with eye_col:
        eyepiece_offset = ((reading - expected) * 35)
        if abs(eyepiece_offset) > 140:
            eyepiece_offset = 140 if eyepiece_offset > 0 else -140
        st.markdown(
            f'<svg viewBox="0 0 500 180" width="100%"><rect width="500" height="180" rx="12" fill="#05070D"/>'
            f'<line x1="250" y1="10" x2="250" y2="170" stroke="#CBD5E1" stroke-width="1"/>'
            f'<line x1="100" y1="90" x2="400" y2="90" stroke="#CBD5E1" stroke-width="1"/>'
            f'<line x1="{250 + eyepiece_offset:.1f}" y1="20" x2="{250 + eyepiece_offset:.1f}" y2="160" '
            f'stroke="{selected_color}" stroke-width="6"/>'
            '</svg>',
            unsafe_allow_html=True,
        )
        if hit:
            st.success("Spectral line aligned with the cross-wire.")
        else:
            st.warning(f"Align on the cross-wire. Target reading: {expected:.2f}°")

    b1, b2, b3, b4 = st.columns(4)
    for col, label, delta in (
        (b1, "-1°", -1.0), (b2, "-0.01°", -0.01),
        (b3, "+0.01°", 0.01), (b4, "+1°", 1.0),
    ):
        if col.button(label, use_container_width=True):
            new_reading = (reading + delta) % 360
            ss.sim_reading = new_reading
            ss.sim_dial_component_value = new_reading
            ss.sim_dial_ignore_value = reading
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
