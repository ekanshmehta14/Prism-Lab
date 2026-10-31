import hashlib, json, os
import numpy as np, pandas as pd, plotly.graph_objects as go, streamlit as st
from PIL import Image
import physics as P
import simulation
from gemini_reader import read_scale, DEFAULT_MODEL

st.set_page_config(page_title="Prism Lab", page_icon="🔬", layout="wide")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
:root{--line:#263650;--muted:#91A2BC;--text:#EAF1FB}
html,body,[class*="st-"],button,input{font-family:'DM Sans',sans-serif}
[data-testid="stAppViewContainer"]{background:radial-gradient(ellipse at 80% 0%,rgba(30,64,112,.18),transparent 42%),#080D18;color:var(--text)}
[data-testid="stHeader"]{background:rgba(8,13,24,.72)}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0D1728,#0A1220);border-right:1px solid var(--line)}
[data-testid="stSidebar"]>div{padding-top:1.4rem}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3{font-family:'Space Grotesk',sans-serif;color:#F1F7FF}
.block-container{max-width:1380px;padding-top:2.1rem;padding-bottom:4rem}
h1,h2,h3{font-family:'Space Grotesk',sans-serif!important;letter-spacing:-.035em!important;color:#F2F7FF}
h1{font-size:clamp(2rem,4vw,2.8rem)!important;font-weight:700!important}
p,li{color:#C5D1E2}
[data-testid="stCaptionContainer"]{color:var(--muted)!important}
.spectrum{height:5px;border-radius:99px;margin:.55rem 0 1.65rem;background:linear-gradient(90deg,#8B5CF6,#6366F1,#3B82F6,#06B6D4,#22C55E,#EAB308,#F97316,#EF4444);box-shadow:0 0 22px rgba(94,234,212,.13)}
[data-testid=stMetric]{background:linear-gradient(145deg,#142238,#0F1A2C);border:1px solid #2A3B56;border-radius:16px;padding:17px 19px;box-shadow:0 10px 30px rgba(0,0,0,.13)}
[data-testid=stMetricLabel]{color:#9FB0C8!important;font-weight:600}
[data-testid=stMetricValue]{color:#F4F8FF!important;font-family:'Space Grotesk',sans-serif}
.stButton>button,.stDownloadButton>button{border-radius:11px;border:1px solid #344965;background:#172740;color:#EAF1FB;font-weight:700;min-height:2.65rem;transition:all .18s ease}
.stButton>button:hover,.stDownloadButton>button:hover{border-color:#5EEAD4;color:#5EEAD4;background:#1A3048}
.stButton>button[kind="primary"]{background:linear-gradient(110deg,#0F766E,#0891B2);border:0;color:white}
[data-testid="stRadio"] label{padding:.45rem .65rem;border-radius:9px}
[data-testid="stRadio"] label:has(input:checked){background:#18334A;border:1px solid #2B6C75}
[data-testid="stTextInput"] input,[data-testid="stNumberInput"] input,[data-testid="stSelectbox"] [data-baseweb="select"]>div{background:#0E192A;border-color:#30415B;border-radius:10px;color:#EAF1FB}
[data-testid="stFileUploader"]{background:#101B2D;border:1px dashed #3A526F;border-radius:14px;padding:.5rem}
[data-testid="stExpander"]{background:#101B2D;border:1px solid #263650;border-radius:13px}
[data-testid="stDataFrame"],[data-testid="stTable"]{border:1px solid #263650;border-radius:12px;overflow:hidden}
[data-testid="stAlert"]{border-radius:12px}
[data-testid="stVerticalBlockBorderWrapper"]{border-color:#263650!important;border-radius:15px}
hr{border-color:#263650}
.chip{display:inline-block;padding:4px 11px;border-radius:99px;font-size:.78rem;border:1px solid #31536A;color:#8FE9DE;background:#102A37}
.hero-panel{padding:1.5rem 1.7rem;border:1px solid #29435B;border-radius:18px;background:linear-gradient(120deg,rgba(20,54,75,.82),rgba(16,26,43,.96) 65%,rgba(31,39,73,.72));box-shadow:0 18px 50px rgba(0,0,0,.2);margin-bottom:1.1rem}
.hero-kicker{font-size:.75rem;text-transform:uppercase;letter-spacing:.16em;color:#72DCCF;font-weight:700}
.hero-title{font-family:'Space Grotesk',sans-serif;font-size:clamp(1.8rem,4vw,2.65rem);line-height:1.1;font-weight:700;color:#F4F8FF;margin:.45rem 0}
.hero-copy{max-width:720px;color:#B6C6DA;font-size:1rem;line-height:1.65}
.step-card{height:100%;padding:1rem 1.05rem;border-radius:14px;border:1px solid #263B56;background:linear-gradient(145deg,#142238,#101A2B)}
.step-number{color:#5EEAD4;font-family:'Space Grotesk',sans-serif;font-size:.78rem;font-weight:700;letter-spacing:.12em}
.step-title{color:#F0F6FF;font-weight:700;margin:.35rem 0}
.step-copy{color:#AABBD0;font-size:.9rem;line-height:1.5}
[data-testid=stFileUploader] [data-testid=stIconMaterial]{display:none!important}
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

page_descriptions = {
    "Overview": "A guided workspace for your prism spectrometer experiment.",
    "Scan scale (Gemini)": "Upload a scale image, review the AI-assisted reading, then save it to your experiment.",
    "Readings": "Review, correct, and add observations from either vernier side.",
    "Results": "Convert recorded angles into deviation, refractive index, and dispersion results.",
    "Simulation": "Practise aligning the telescope with the virtual spectrometer.",
    "Export": "Download your experiment readings for reports and further analysis."
}
st.caption(page_descriptions[page])
# ---------------------------------------------------------------- Overview
if page == "Overview":
    n = len(ss.obs)
    st.markdown("""
    <section class="hero-panel">
      <div class="hero-kicker">OPTICS • EXPERIMENT WORKSPACE</div>
      <div class="hero-title">Explore light. Measure precision.</div>
      <div class="hero-copy">A digital prism spectrometer lab to capture vernier readings, observe dispersion,
      and calculate the refractive index of a prism — with guided scanning and an interactive virtual bench.</div>
      <div style="margin-top:1rem"><span class="chip">VIBGYOR spectrum</span>&nbsp; <span class="chip">Gemini-assisted reading</span>&nbsp; <span class="chip">Live calculations</span></div>
    </section>
    """, unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("Prism angle", f"{ss.prism:.1f}°", help="Configured prism angle A")
    c2.metric("Direct reading", f"{ss.direct:.3f}°" if ss.direct else "Not set", help="Reference reading before inserting the prism")
    c3.metric("Readings logged", n, help="Saved manual, scanned, and simulated readings")
    st.subheader("Your experiment workflow")
    steps = st.columns(4)
    cards = [
        ("01", "Set up", "Enter the prism angle and record the direct-ray reference in the sidebar."),
        ("02", "Capture", "Upload a clear vernier-scale photo or enter a reading manually."),
        ("03", "Measure", "Use the virtual spectrometer to align spectral lines and record observations."),
        ("04", "Analyse", "Compare deviations, calculate refractive index, and export your data.")
    ]
    for col, (num, title, copy) in zip(steps, cards):
        with col:
            st.markdown(f'<div class="step-card"><div class="step-number">STEP {num}</div><div class="step-title">{title}</div><div class="step-copy">{copy}</div></div>', unsafe_allow_html=True)
    st.subheader("The physics behind the experiment")
    formula_col, note_col = st.columns([1.25, 1])
    with formula_col:
        st.latex(r"\mu=\frac{\sin\left(\frac{A+D_m}{2}\right)}{\sin\left(\frac{A}{2}\right)}")
        st.latex(r"\omega=\frac{\mu_{short}-\mu_{long}}{\mu_{mean}-1}")
    with note_col:
        st.markdown("**Minimum deviation method**")
        st.caption("At minimum deviation, the light path through the prism is symmetric. Use the measured deviation and prism angle to determine the refractive index.")
        st.markdown("**Expected observation**")
        st.caption("For normal dispersion, violet light typically bends more than red light because its refractive index is higher.")
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
