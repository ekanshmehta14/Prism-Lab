import hashlib, json, os
import numpy as np, pandas as pd, plotly.graph_objects as go, streamlit as st
from PIL import Image
import physics as P
import simulation
from gemini_reader import read_scale, DEFAULT_MODEL

st.set_page_config(page_title="Prism Lab", page_icon="🔬", layout="wide")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=IBM+Plex+Sans:wght@400;500;600&display=swap');
html,body,[class*="st-"],button,input{font-family:'IBM Plex Sans',sans-serif}
h1,h2,h3{font-family:'Fraunces',serif!important;letter-spacing:-.01em}
.block-container{max-width:1200px;padding-top:2rem}
.spectrum{height:6px;border-radius:3px;margin:.2rem 0 1.4rem;
 background:linear-gradient(90deg,#8B5CF6,#3B82F6,#06B6D4,#22C55E,#EAB308,#F59E0B,#EF4444)}
[data-testid=stMetric]{background:#121A2B;border:1px solid #24304A;border-radius:10px;padding:12px 16px}
[data-testid=stSidebar]{border-right:1px solid #24304A}
.stButton>button,.stDownloadButton>button{border-radius:8px;font-weight:600}
.chip{display:inline-block;padding:2px 10px;border-radius:99px;font-size:.8rem;border:1px solid #24304A;color:#A9B4CC}
[data-testid=stFileUploader] [data-testid=stIconMaterial]{display:none!important}
[data-testid=stExpander] summary{list-style:none!important}
[data-testid=stExpander] summary::-webkit-details-marker{display:none!important}
[data-testid=stExpander] summary [data-testid=stIconMaterial]{display:none!important}
</style>""", unsafe_allow_html=True)

ss = st.session_state
ss.setdefault("obs", pd.DataFrame(columns=["Line", "Side", "Reading (°)", "Source"]))
ss.setdefault("direct", None)
ss.setdefault("prism", 60.0)
ss.setdefault("scans", {})


def api_key():
    try:
        k = st.secrets["GEMINI_API_KEY"]
    except Exception:
        k = None
    return k or os.getenv("GEMINI_API_KEY")


def add_obs(line, side, reading, source):
    row = pd.DataFrame([{"Line": line, "Side": side, "Reading (°)": round(reading, 4), "Source": source}])
    ss.obs = pd.concat([ss.obs, row], ignore_index=True)


with st.sidebar:
    st.markdown("### 🔬 Prism Lab")
    page = st.radio("Go to", ["Overview", "Scan scale (Gemini)", "Readings", "Results", "Simulation", "Export"],
                    label_visibility="collapsed")
    st.divider()
    ss.prism = st.number_input("Prism angle A (°)", 10.0, 90.0, float(ss.prism), 0.1)
    d = st.number_input("Direct ray reading (°)", 0.0, 360.0, float(ss.direct or 0.0), 0.01, format="%.4f")
    ss.direct = d if d else ss.direct

st.title({"Overview": "Prism spectrometer lab", "Scan scale (Gemini)": "Scan a scale photo",
          "Readings": "Readings", "Results": "Results", "Simulation": "Simulation",
          "Export": "Export"}[page])
st.markdown("<div class='spectrum'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------- Overview
if page == "Overview":
    n = len(ss.obs)
    c1, c2, c3 = st.columns(3)
    c1.metric("Prism angle", f"{ss.prism:.1f}°")
    c2.metric("Direct reading", f"{ss.direct:.3f}°" if ss.direct else "not set")
    c3.metric("Readings logged", n)
    st.subheader("How it works")
    st.markdown("""
1. Set the prism angle and the direct-ray reading in the sidebar.
2. Photograph the vernier scale at minimum deviation for each VIBGYOR spectral line.
3. Upload it under **Scan scale**. Gemini reads the main scale and coinciding vernier line; you check and save.
4. **Results** computes deviation, refractive index μ and dispersive power ω, and fits a Cauchy curve.
""")
    st.latex(r"\mu=\frac{\sin\frac{A+D_m}{2}}{\sin\frac{A}{2}}\qquad \omega=\frac{\mu_{short}-\mu_{long}}{\mu_{mean}-1}")
    with st.expander("Viva quick answers"):
        for q, a in [("Why minimum deviation?", "The ray passes symmetrically, so the standard μ formula holds."),
                     ("Vernier least count?", "One main-scale division divided by the number of vernier divisions."),
                     ("Why does violet bend more?", "μ rises as wavelength falls (normal dispersion)."),
                     ("Why a collimator?", "It sends a parallel beam into the prism."),
                     ("Main sources of error?", "Parallax, backlash, prism not levelled, off-centre prism table.")]:
            st.markdown(f"**{q}** {a}")

# ---------------------------------------------------------------- Scanner
elif page == "Scan scale (Gemini)":
    st.caption(f"Model: {os.getenv('GEMINI_MODEL', DEFAULT_MODEL)}. Photos are sent to Google's Gemini API for reading.")
    files = st.file_uploader("Upload spectrometer scale photos", type=["jpg", "jpeg", "png", "webp"],
                             accept_multiple_files=True)
    for f in files or []:
        img = Image.open(f)
        uid = hashlib.sha256(f.getvalue()).hexdigest()[:10]
        with st.container(border=True):
            left, right = st.columns([1, 1.2])
            left.image(img, caption=f.name, use_container_width=True)
            with right:
                if st.button("Read with Gemini", key=f"go{uid}", type="primary"):
                    with st.spinner("Reading scale..."):
                        ss.scans[uid] = read_scale(img, api_key(), os.getenv("GEMINI_MODEL", DEFAULT_MODEL))
                res = ss.scans.get(uid)
                if res and not res["ok"]:
                    st.error(res["error"])
                if res and res["ok"]:
                    st.progress(res["confidence"], text=f"Confidence {res['confidence']:.0%}")
                    if res["notes"]:
                        st.caption(res["notes"])
                    if res["confidence"] < 0.6:
                        st.warning("Low confidence. Check the values against the photo.")
                a, b, c = st.columns(3)
                ms = a.number_input("Main (°)", value=float(res["main"]) if res and res["ok"] else 0.0,
                                    step=0.5, format="%.2f", key=f"ms{uid}{res and res.get('main')}")
                vd = b.number_input("Vernier div", value=float(res["vernier"]) if res and res["ok"] else 0.0,
                                    step=1.0, key=f"vd{uid}{res and res.get('vernier')}")
                lc = c.number_input("Least count (°)", value=float(res["least_count"]) if res and res["ok"] else 1 / 60,
                                    format="%.5f", key=f"lc{uid}")
                total = P.vernier_reading(ms, vd, lc)
                st.metric("Reading", f"{total:.4f}°")
                d1, d2, d3 = st.columns([1.2, 1, 1])
                line = d1.selectbox("Line", P.LINE_NAMES, key=f"ln{uid}")
                side = d2.selectbox("Side", ["Left", "Right"], key=f"sd{uid}")
                if d3.button("Save reading", key=f"sv{uid}"):
                    add_obs(line, side, total, "Gemini (checked)")
                    st.toast(f"Saved {line} {side}")
                if st.button("Use as direct reading", key=f"dr{uid}"):
                    ss.direct = total
                    st.rerun()
    if not files:
        st.info("Upload a close-up of the main scale and vernier. Sharp, evenly lit photos read best.")

# ---------------------------------------------------------------- Readings
elif page == "Readings":
    st.subheader("Add a reading by hand")
    a, b, c, d = st.columns(4)
    l = a.selectbox("Line", P.LINE_NAMES)
    s = b.selectbox("Side", ["Left", "Right"])
    r = c.number_input("Reading (°)", 0.0, 360.0, 0.0, 0.01, format="%.4f")
    if d.button("Add"):
        add_obs(l, s, r, "Manual")
        st.rerun()
    if ss.obs.empty:
        st.info("No readings yet. Scan a photo or add one by hand.")
    else:
        ss.obs = st.data_editor(ss.obs, num_rows="dynamic", use_container_width=True, hide_index=True,
                                column_config={"Line": st.column_config.SelectboxColumn(options=P.LINE_NAMES),
                                               "Side": st.column_config.SelectboxColumn(options=["Left", "Right"])})

# ---------------------------------------------------------------- Results
elif page == "Results":
    if ss.obs.empty or not ss.direct:
        st.info("Set a direct reading in the sidebar and log at least one reading.")
    else:
        df = ss.obs.dropna().copy()
        df["D (°)"] = [P.angle_diff(r, ss.direct) for r in df["Reading (°)"]]
        g = df.groupby("Line")["D (°)"].mean().reset_index()
        g["λ (nm)"] = g["Line"].map(P.WAVELENGTH)
        g["μ"] = [P.refractive_index(ss.prism, d) for d in g["D (°)"]]
        g = g.sort_values("λ (nm)")
        st.dataframe(g.style.format({"D (°)": "{:.3f}", "μ": "{:.5f}"}), hide_index=True, use_container_width=True)

        have = list(g["Line"])
        st.subheader("Dispersive power")
        c1, c2, c3 = st.columns(3)
        pick = lambda col, lab, dflt: col.selectbox(lab, have, index=have.index(dflt) if dflt in have else 0)
        sh = pick(c1, "Short wavelength", "Blue")
        mn = pick(c2, "Mean wavelength", "Yellow")
        lg = pick(c3, "Long wavelength", "Red")
        mu = dict(zip(g["Line"], g["μ"]))
        if len({sh, mn, lg}) < 3:
            st.warning("Pick three different lines.")
        else:
            w = P.dispersive_power(mu[sh], mu[lg], mu[mn])
            m1, m2 = st.columns(2)
            m1.metric("ω", f"{w:.5f}")
            m2.metric("μ (mean line)", f"{mu[mn]:.5f}")

        fig = go.Figure(go.Scatter(x=g["λ (nm)"], y=g["μ"], mode="markers",
                                   marker=dict(size=11, color=[P.COLOUR[x] for x in g["Line"]]), name="Measured"))
        fit = P.cauchy_fit(g["λ (nm)"], g["μ"])
        if fit:
            xs = np.linspace(400, 650, 60)
            fig.add_scatter(x=xs, y=fit[0] + fit[1] / xs ** 2, mode="lines", name=f"Cauchy A={fit[0]:.4f}, B={fit[1]:.0f} nm²",
                            line=dict(color="#94A3B8", dash="dot"))
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          xaxis_title="Wavelength (nm)", yaxis_title="Refractive index μ", height=420)
        st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------- Virtual bench
elif page == "Simulation":
    simulation.render(ss, add_obs)

# ---------------------------------------------------------------- Export
else:
    if ss.obs.empty:
        st.info("Nothing to export yet.")
    else:
        st.download_button("Download readings (CSV)", ss.obs.to_csv(index=False), "prism_readings.csv", "text/csv")
        st.download_button("Download experiment (JSON)",
                           json.dumps({"prism_angle": ss.prism, "direct": ss.direct,
                                       "observations": ss.obs.to_dict("records")}, indent=2),
                           "prism_experiment.json", "application/json")
