import hashlib, json, os
import numpy as np, pandas as pd, plotly.graph_objects as go, streamlit as st
from PIL import Image
import physics as P
import simulation
from gemini_reader import read_scale, DEFAULT_MODEL

st.set_page_config(page_title="Prism Lab", page_icon="🔬", layout="wide")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
:root{
 --bg:#070B14;--panel:#101A2B;--panel2:#142238;--line:#263B56;
 --muted:#9AADC6;--text:#ECF4FF;--cyan:#5EEAD4;--blue:#38BDF8;--violet:#A78BFA;
}
html,body,button,input{font-family:'DM Sans',sans-serif}
[data-testid="stAppViewContainer"]{
 background:
 radial-gradient(ellipse at 78% -5%,rgba(56,189,248,.13),transparent 35%),
 radial-gradient(ellipse at 8% 18%,rgba(124,58,237,.10),transparent 30%),
 var(--bg);color:var(--text)
}
[data-testid="stHeader"]{background:rgba(7,11,20,.76);backdrop-filter:blur(14px)}
[data-testid="stSidebar"]{
 background:linear-gradient(180deg,#0E192B 0%,#091321 100%);
 border-right:1px solid rgba(94,234,212,.13)
}
[data-testid="stSidebar"]>div{padding-top:1.25rem}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3{
 font-family:'Space Grotesk',sans-serif;color:#F4F8FF;letter-spacing:-.04em
}
.block-container{max-width:1440px;padding-top:2rem;padding-bottom:4rem}
h1,h2,h3{font-family:'Space Grotesk',sans-serif!important;letter-spacing:-.04em!important;color:#F3F8FF}
h1{font-size:clamp(2rem,4vw,2.85rem)!important;font-weight:700!important}
h2{font-size:1.55rem!important} h3{font-size:1.18rem!important}
p,li{color:#C7D5E7;line-height:1.65}
[data-testid="stCaptionContainer"]{color:var(--muted)!important}
[data-testid="stIconMaterial"],.material-symbols-rounded,.material-symbols-outlined{
 font-family:'Material Symbols Rounded'!important;font-weight:normal!important;font-style:normal!important;
 font-size:24px;line-height:1;letter-spacing:normal;text-transform:none;display:inline-block;
 white-space:nowrap;word-wrap:normal;direction:ltr;-webkit-font-feature-settings:'liga';
 -webkit-font-smoothing:antialiased
}
.spectrum{height:5px;border-radius:99px;margin:.55rem 0 1.65rem;
 background:linear-gradient(90deg,#8B5CF6,#6366F1,#3B82F6,#06B6D4,#22C55E,#EAB308,#F97316,#EF4444);
 box-shadow:0 0 26px rgba(94,234,212,.18)}
[data-testid=stMetric]{
 background:linear-gradient(145deg,rgba(21,39,62,.96),rgba(13,24,41,.96));
 border:1px solid rgba(111,151,190,.22);border-radius:18px;padding:18px 20px;
 box-shadow:0 14px 34px rgba(0,0,0,.16);transition:transform .18s ease,border-color .18s ease
}
[data-testid=stMetric]:hover{transform:translateY(-2px);border-color:rgba(94,234,212,.45)}
[data-testid=stMetricLabel]{color:#AFC0D5!important;font-weight:600}
[data-testid=stMetricValue]{color:#F4F8FF!important;font-family:'Space Grotesk',sans-serif}
[data-testid=stMetricDelta]{font-size:.82rem}
.stButton>button,.stDownloadButton>button{
 border-radius:12px;border:1px solid #344C69;background:linear-gradient(145deg,#192D47,#122238);
 color:#EAF3FF;font-weight:700;min-height:2.75rem;transition:all .18s ease
}
.stButton>button:hover,.stDownloadButton>button:hover{
 border-color:var(--cyan);color:var(--cyan);background:#19354B;transform:translateY(-1px)
}
.stButton>button[kind="primary"]{
 background:linear-gradient(110deg,#0F766E,#0891B2);border:0;color:white;
 box-shadow:0 8px 22px rgba(8,145,178,.18)
}
[data-testid="stRadio"] label{padding:.55rem .7rem;border-radius:11px;transition:all .16s ease}
[data-testid="stRadio"] label:has(input:checked){
 background:linear-gradient(100deg,rgba(20,184,166,.18),rgba(56,189,248,.12));
 border:1px solid rgba(94,234,212,.35)
}
[data-testid="stTextInput"] input,[data-testid="stNumberInput"] input,
[data-testid="stSelectbox"] [data-baseweb="select"]>div,
[data-testid="stMultiSelect"] [data-baseweb="select"]>div{
 background:#0D192A;border-color:#304761;border-radius:11px;color:#EAF1FB
}
[data-testid="stFileUploader"]{background:rgba(16,29,48,.72);border:1px dashed #45617F;border-radius:16px;padding:.65rem}
[data-testid="stExpander"]{background:rgba(16,27,45,.72);border:1px solid #263B56;border-radius:14px}
[data-testid="stDataFrame"],[data-testid="stTable"]{border:1px solid #263B56;border-radius:14px;overflow:hidden}
[data-testid="stAlert"]{border-radius:14px}
[data-testid="stVerticalBlockBorderWrapper"]{border-color:#2A405C!important;border-radius:17px;background:rgba(15,27,45,.45)}
hr{border-color:#263B56}
.chip{display:inline-flex;align-items:center;gap:.35rem;padding:5px 11px;border-radius:99px;
 font-size:.77rem;font-weight:600;border:1px solid rgba(94,234,212,.28);color:#9AF3E5;background:rgba(16,58,65,.42)}
.hero-panel{
 position:relative;overflow:hidden;padding:2rem 2.1rem;border:1px solid rgba(91,151,190,.28);
 border-radius:24px;background:linear-gradient(115deg,rgba(17,54,76,.94),rgba(13,27,47,.96) 58%,rgba(37,32,77,.86));
 box-shadow:0 24px 70px rgba(0,0,0,.24);margin-bottom:1.3rem
}
.hero-panel:after{content:"";position:absolute;width:290px;height:290px;right:-65px;top:-115px;border-radius:50%;
 border:1px solid rgba(94,234,212,.18);box-shadow:0 0 0 24px rgba(94,234,212,.025),0 0 0 52px rgba(94,234,212,.02)}
.hero-kicker{font-size:.74rem;text-transform:uppercase;letter-spacing:.18em;color:#75E8D9;font-weight:700}
.hero-title{font-family:'Space Grotesk',sans-serif;font-size:clamp(2rem,4.6vw,3.25rem);line-height:1.05;
 font-weight:700;color:#F6FAFF;margin:.55rem 0}
.hero-copy{max-width:740px;color:#B9CBE0;font-size:1.02rem;line-height:1.7}
.step-card{height:100%;padding:1.15rem 1.15rem;border-radius:17px;border:1px solid #2A405C;
 background:linear-gradient(145deg,rgba(21,39,62,.96),rgba(13,24,41,.96));transition:all .2s ease}
.step-card:hover{transform:translateY(-3px);border-color:rgba(94,234,212,.48);box-shadow:0 14px 32px rgba(0,0,0,.18)}
.step-number{color:#5EEAD4;font-family:'Space Grotesk',sans-serif;font-size:.76rem;font-weight:700;letter-spacing:.13em}
.step-title{color:#F0F6FF;font-weight:700;margin:.42rem 0}
.step-copy{color:#AFC0D5;font-size:.9rem;line-height:1.55}
.section-kicker{color:#71DCCC;font-size:.72rem;font-weight:700;letter-spacing:.16em;text-transform:uppercase}
.sidebar-status{padding:.8rem .9rem;border:1px solid rgba(94,234,212,.22);border-radius:14px;
 background:linear-gradient(135deg,rgba(16,58,65,.55),rgba(17,35,55,.75));color:#CDEEEA;font-size:.82rem}
[data-testid=stFileUploader] [data-testid=stIconMaterial]{display:initial!important}
@media(max-width:760px){.block-container{padding-top:1.2rem}.hero-panel{padding:1.35rem}.hero-panel:after{opacity:.35}}
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
    st.caption("OPTICS WORKSPACE  ·  v1.0")
    page = st.radio("Workspace", ["Overview", "Scan scale (Gemini)", "Readings", "Results", "Simulation", "Export"],
                    key="page_nav", label_visibility="collapsed")
    st.markdown(
        f"<div class='sidebar-status'>● Experiment active<br><span style='color:#9FB5C9'>{len(ss.obs)} observation(s) saved</span></div>",
        unsafe_allow_html=True
    )
    st.divider()
    st.markdown("**EXPERIMENT SETUP**")
    ss.prism = st.number_input("Prism angle A (°)", 10.0, 90.0, float(ss.prism), 0.1)
    d = st.number_input("Direct ray reading (°)", 0.0, 360.0, float(ss.direct or 0.0), 0.01, format="%.4f")
    ss.direct = d if d else ss.direct
    st.caption("Set the reference values before analysing observations.")
    st.divider()
    st.markdown("**QUICK STATUS**")
    st.caption("✓ Prism angle configured")
    st.caption("✓ Gemini scanner available" if api_key() else "○ Gemini key not configured")
    st.caption("✓ Direct ray recorded" if ss.direct else "○ Direct ray not recorded")

st.markdown("<div class='section-kicker'>PRISM LAB  /  " + page.upper() + "</div>", unsafe_allow_html=True)
st.title({"Overview": "Prism spectrometer lab", "Scan scale (Gemini)": "Scan a scale photo",
          "Readings": "Readings", "Results": "Results", "Simulation": "Simulation",
          "Export": "Export"}[page])
st.markdown("<div class='spectrum'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------- Overview
if page == "Overview":
    n = len(ss.obs)
    st.markdown("""
    <section class="hero-panel">
      <div class="hero-kicker">OPTICS • EXPERIMENT WORKSPACE</div>
      <div class="hero-title">See the science.<br>Measure the spectrum.</div>
      <div class="hero-copy">Your interactive prism spectrometer workspace. Capture precise vernier readings,
      explore wavelength-dependent refraction, and turn observations into clear experimental results.</div>
      <div style="margin-top:1.1rem;display:flex;gap:.5rem;flex-wrap:wrap">
        <span class="chip">✦ VIBGYOR spectrum</span><span class="chip">✦ Gemini-assisted scan</span><span class="chip">✦ Live calculations</span>
      </div>
    </section>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Prism angle", f"{ss.prism:.1f}°", help="Configured prism angle A")
    c2.metric("Direct reading", f"{ss.direct:.3f}°" if ss.direct else "Not set", help="Reference reading before inserting the prism")
    c3.metric("Readings logged", n, help="Saved manual, scanned, and simulated readings")

    st.markdown("<div class='section-kicker'>YOUR WORKFLOW</div>", unsafe_allow_html=True)
    st.subheader("Move from setup to discovery")
    steps = st.columns(4)
    cards = [
        ("01", "Configure", "Set the prism angle and direct-ray reference."),
        ("02", "Capture", "Scan a vernier photo or enter readings manually."),
        ("03", "Explore", "Align spectral lines on the interactive virtual bench."),
        ("04", "Analyse", "Compare deviations, calculate μ, and export results.")
    ]
    for col, (num, title, copy) in zip(steps, cards):
        with col:
            st.markdown(f'<div class="step-card"><div class="step-number">PHASE {num}</div><div class="step-title">{title}</div><div class="step-copy">{copy}</div></div>', unsafe_allow_html=True)

    st.markdown("<div style='height:.7rem'></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-kicker'>QUICK ACTIONS</div>", unsafe_allow_html=True)
    q1, q2, q3 = st.columns(3)
    if q1.button("✦  Scan a scale photo", use_container_width=True, type="primary"):
        ss.page_nav = "Scan scale (Gemini)"
        st.rerun()
    if q2.button("＋  Add manual reading", use_container_width=True):
        ss.page_nav = "Readings"
        st.rerun()
    if q3.button("◉  Open virtual bench", use_container_width=True):
        ss.page_nav = "Simulation"
        st.rerun()

    st.markdown("<div class='section-kicker'>THE PHYSICS</div>", unsafe_allow_html=True)
    st.subheader("From minimum deviation to refractive index")
    formula_col, note_col = st.columns([1.15, 1])
    with formula_col:
        with st.container(border=True):
            st.latex(r"\\mu=\\frac{\\sin\\left(\\frac{A+D_m}{2}\\right)}{\\sin\\left(\\frac{A}{2}\\right)}")
            st.latex(r"\\omega=\\frac{\\mu_{short}-\\mu_{long}}{\\mu_{mean}-1}")
    with note_col:
        with st.container(border=True):
            st.markdown("**Minimum deviation method**")
            st.caption("At minimum deviation, the light path through the prism is symmetric. The measured deviation and prism angle reveal the refractive index.")
            st.markdown("**A colourful result**")
            st.caption("In normal dispersion, violet light typically bends more than red light because its refractive index is higher.")
    with st.expander("🎓  Viva quick answers"):
        for q, a in [("Why minimum deviation?", "The ray passes symmetrically, so the standard μ formula holds."),
                     ("Vernier least count?", "One main-scale division divided by the number of vernier divisions."),
                     ("Why does violet bend more?", "μ rises as wavelength falls (normal dispersion)."),
                     ("Why a collimator?", "It sends a parallel beam into the prism."),
                     ("Main sources of error?", "Parallax, backlash, prism not levelled, off-centre prism table.")]:
            st.markdown(f"**{q}**  {a}")

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
