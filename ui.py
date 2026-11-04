"""Visual layer for Prism Lab: theme CSS and small HTML components."""
import pandas as pd
import streamlit as st
import physics as P

LO, HI = 380.0, 720.0
TITLES = {
    "Overview": ("Prism spectrometer lab", "Find the refractive index and dispersive power of a prism from your vernier readings."),
    "Scan scale (Gemini)": ("Scan a scale photo", "Upload a close-up of the main scale and vernier. Gemini reads it, then you confirm the values before saving."),
    "Readings": ("Readings", "Enter vernier readings for both verniers, or import them from a CSV."),
    "Results": ("Results", "Refractive index at each spectral line, then the dispersive power of the prism."),
    "Simulation": ("Simulation", "Turn the telescope onto each spectral line and record both vernier readings."),
    "Export": ("Export", "Download your readings, or the whole experiment as JSON."),
}
PLOT = dict(template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#FBFCFC",
            font=dict(family="Hanken Grotesk, system-ui, sans-serif", color="#16212B"),
            margin=dict(l=10, r=10, t=20, b=10))

CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@400;500;600;700&family=Newsreader:opsz,wght@6..72,400;6..72,500;6..72,600&display=swap');
:root{--bench:#EDF0F2;--paper:#FBFCFC;--ink:#16212B;--slate:#566673;--rule:#D3DAE0;--enamel:#11161C;--brass:#8A5F17;--brass-lt:#D9A441}
html,body,button,input,textarea{font-family:'Hanken Grotesk',system-ui,sans-serif}
[data-testid="stIconMaterial"],.material-symbols-rounded,.material-symbols-outlined{
 font-family:'Material Symbols Rounded'!important;font-weight:normal!important;font-style:normal!important;
 font-size:24px;line-height:1;letter-spacing:normal;text-transform:none;display:inline-block;white-space:nowrap;
 word-wrap:normal;direction:ltr;-webkit-font-feature-settings:'liga';-webkit-font-smoothing:antialiased}
[data-testid=stFileUploader] [data-testid=stIconMaterial]{display:initial!important}
[data-testid="stAppViewContainer"]{background-color:var(--bench);color:var(--ink);
 background-image:linear-gradient(rgba(22,33,43,.045) 1px,transparent 1px),linear-gradient(90deg,rgba(22,33,43,.045) 1px,transparent 1px);
 background-size:32px 32px}
[data-testid="stHeader"]{background:transparent}
.block-container{max-width:1180px;padding-top:3.2rem;padding-bottom:4rem}
h1,h2,h3{font-family:'Newsreader',Georgia,serif!important;color:var(--ink)!important;font-weight:500!important;letter-spacing:-.015em!important}
h2{font-size:1.7rem!important} h3{font-size:1.35rem!important}
h5{font-family:'Hanken Grotesk',sans-serif!important;font-size:.95rem!important;font-weight:700!important;margin:.2rem 0 .4rem!important}
p,li{line-height:1.6}
[data-testid="stCaptionContainer"]{color:var(--slate)!important}
:focus-visible{outline:2px solid var(--brass);outline-offset:2px}
@media(prefers-reduced-motion:reduce){*{transition:none!important}}
/* page header + wavelength ruler */
.ph-row{display:flex;justify-content:space-between;gap:1rem;flex-wrap:wrap}
.crumb{font-size:.86rem;color:var(--slate)}
.ph-title{font-family:'Newsreader',Georgia,serif;font-size:clamp(2.2rem,4vw,3.1rem);line-height:1.05;font-weight:500;
 letter-spacing:-.02em;margin:.3rem 0 .5rem;padding:0;color:var(--ink)}
.ph-lede{max-width:62ch;color:var(--slate);font-size:1.05rem;margin:0 0 1.5rem}
.ruler{position:relative;height:2.2rem;margin:0 0 1.8rem}
.ruler-bar{height:8px;border-radius:2px;margin-top:4px;
 background:linear-gradient(90deg,#4B2A8C 0%,#3A47C9 10%,#1C8FE0 24%,#14B8A6 38%,#2FBF5B 46%,#E6D325 58%,#F29A1D 70%,#E0431C 84%,#8A1710 100%)}
.ruler-tick{position:absolute;top:14px;width:1px;height:6px;background:var(--slate)}
.ruler-lab{position:absolute;top:20px;transform:translateX(-50%);font-size:.72rem;color:var(--slate);font-variant-numeric:tabular-nums}
.ruler-mk{position:absolute;top:1px;width:14px;height:14px;margin-left:-7px;border-radius:50%;border:2px solid var(--ink);background:var(--paper);box-sizing:border-box}
.ruler-mk.on{background:var(--ink)}
/* sidebar */
[data-testid="stSidebar"]{background:var(--enamel);border-right:1px solid #232C36}
[data-testid="stSidebar"] label,[data-testid="stSidebar"] p,[data-testid="stSidebar"] h5,[data-testid="stSidebar"] [data-testid="stCaptionContainer"]{color:#C9D3DB!important}
[data-testid="stSidebar"] input{background:#1B232C!important;color:#EEF2F4!important}
[data-testid="stSidebar"] hr{border-color:#232C36}
.brand{font-family:'Newsreader',Georgia,serif;font-size:1.9rem;color:#F4F1E8;line-height:1.1}
.brand-sub{font-size:.82rem;color:#8C99A5;margin:.15rem 0 .7rem}
.brand-bar{height:4px;border-radius:2px;margin-bottom:1.1rem;
 background:linear-gradient(90deg,#8B5CF6,#3B82F6,#22C55E,#EAB308,#F97316,#EF4444)}
[data-testid="stSidebar"] [data-baseweb=radio]>div:first-child{display:none}
[data-testid="stSidebar"] [data-testid=stRadio] label{padding:.5rem .8rem;border-left:3px solid transparent;border-radius:0 6px 6px 0;width:100%}
[data-testid="stSidebar"] [data-testid=stRadio] label:has(input:checked){border-left-color:var(--brass-lt);background:#1B232C}
[data-testid="stSidebar"] [data-testid=stRadio] label:has(input:checked) p{color:#fff!important;font-weight:600}
[data-testid="stSidebar"] label:has(input:focus-visible){outline:2px solid var(--brass-lt)}
.sb-stat{padding:.6rem .8rem;border:1px solid #2A3540;border-radius:6px;color:#C9D3DB;font-size:.88rem;margin-top:.8rem}
.sb-stat b{color:#F4F1E8;font-variant-numeric:tabular-nums}
/* controls */
[data-testid=stMetric]{background:var(--paper);border:1px solid var(--rule);border-radius:8px;padding:16px 18px}
[data-testid=stMetricLabel]{color:var(--slate)!important;font-weight:600}
[data-testid=stMetricValue]{font-family:'Newsreader',Georgia,serif;font-size:2.1rem;font-variant-numeric:tabular-nums}
.stButton>button,.stDownloadButton>button{border-radius:6px;border:1px solid var(--ink);background:var(--paper);color:var(--ink);
 font-weight:600;min-height:2.6rem;transition:border-color .15s,color .15s,background .15s}
.stButton>button:hover,.stDownloadButton>button:hover{border-color:var(--brass);color:var(--brass);background:var(--paper)}
.stButton>button[kind="primary"]{background:var(--ink);border-color:var(--ink);color:#fff}
.stButton>button[kind="primary"]:hover{background:#2B3B4A;color:#fff;border-color:#2B3B4A}
.stButton>button:disabled{opacity:.45}
[data-testid=stVerticalBlockBorderWrapper],[data-testid=stExpander]{border-color:var(--rule)!important;border-radius:8px;background:var(--paper)}
[data-testid=stFileUploader]{background:var(--paper);border:1px dashed #9AA8B3;border-radius:8px;padding:.6rem}
[data-testid=stDataFrame],[data-testid=stTable]{border:1px solid var(--rule);border-radius:8px;overflow:hidden}
[data-testid=stAlert]{border-radius:8px}
iframe{border-radius:10px}
/* overview */
.hero{display:grid;grid-template-columns:1.1fr 1fr;border:1px solid var(--rule);border-radius:10px;overflow:hidden;background:var(--paper);margin-bottom:1.5rem}
.hero-copy{padding:2.2rem}
.hero-h{font-family:'Newsreader',Georgia,serif;font-size:clamp(1.8rem,3.2vw,2.6rem);line-height:1.1;font-weight:500;letter-spacing:-.015em;margin-bottom:.8rem}
.hero-p{color:var(--slate);max-width:46ch;margin:0}
.hero-plate{background:var(--enamel)}
.flow{display:grid;grid-template-columns:repeat(4,1fr);border:1px solid var(--rule);border-radius:8px;background:var(--paper);margin:.4rem 0 1.6rem}
.flow>div{padding:1rem 1.1rem;border-left:1px solid var(--rule)}
.flow>div:first-child{border-left:0}
.dot{display:inline-grid;place-items:center;width:1.6rem;height:1.6rem;border-radius:50%;border:1.5px solid var(--slate);font-size:.8rem;font-weight:700;color:var(--slate)}
.flow .done .dot{background:var(--brass);border-color:var(--brass);color:#fff}
.flow-t{font-weight:700;margin:.55rem 0 .2rem}
.flow-c{font-size:.88rem;color:var(--slate);line-height:1.5}
.flow-s{font-size:.8rem;font-weight:600;margin-top:.6rem;color:var(--slate)}
.flow .done .flow-s{color:var(--brass)}
/* simulation readouts */
.vern{display:grid;grid-template-columns:1fr 1fr;gap:.75rem;margin-bottom:.75rem}
.vern>div{background:var(--enamel);border-radius:8px;padding:.7rem 1rem;border-left:3px solid var(--brass-lt)}
.vern .k{color:#C8B07A;font-size:.82rem;font-weight:600}
.vern .v{font-family:'Newsreader',Georgia,serif;font-size:1.9rem;color:#F4F1E8;font-variant-numeric:tabular-nums}
@media(max-width:820px){.hero,.flow{grid-template-columns:1fr}.flow>div{border-left:0;border-top:1px solid var(--rule)}.flow>div:first-child{border-top:0}.hero-copy{padding:1.4rem}}
</style>"""


def inject():
    st.markdown(CSS, unsafe_allow_html=True)


def _logged(obs):
    out = set()
    if obs is None or obs.empty:
        return out
    for _, r in obs.iterrows():
        line = str(r.get("Line", ""))
        if line and line.upper() != "UDR" and (pd.notna(r.get("Right reading (°)")) or pd.notna(r.get("Left reading (°)"))):
            out.add(line)
    return out


def _pct(w):
    return (w - LO) / (HI - LO) * 100


def brand():
    st.markdown('<div class="brand">Prism Lab</div><div class="brand-sub">Prism spectrometer practical</div><div class="brand-bar"></div>',
                unsafe_allow_html=True)


def sidebar_status(n):
    st.markdown(f'<div class="sb-stat"><b>{n}</b> observation{"" if n == 1 else "s"} saved</div>', unsafe_allow_html=True)


def page_header(page, obs):
    title, lede = TITLES[page]
    logged = _logged(obs)
    marks = "".join(
        f'<span class="ruler-mk{" on" if n in logged else ""}" style="left:{_pct(w):.2f}%" '
        f'title="{n}, {w:.0f} nm: {"logged" if n in logged else "not logged"}"></span>' for n, w, _ in P.LINES)
    ticks = "".join(
        f'<span class="ruler-tick" style="left:{_pct(w):.2f}%"></span><span class="ruler-lab" style="left:{_pct(w):.2f}%">{w}</span>'
        for w in range(400, 701, 50))
    st.markdown(
        f'<div class="ph-row"><span class="crumb">Prism Lab / {page.split(" (")[0]}</span>'
        f'<span class="crumb">{len(logged)} of {len(P.LINES)} spectral lines logged</span></div>'
        f'<h1 class="ph-title">{title}</h1><p class="ph-lede">{lede}</p>'
        f'<div class="ruler" role="img" aria-label="Visible spectrum, 380 to 720 nanometres. Filled markers are spectral lines with readings.">'
        f'<div class="ruler-bar"></div>{marks}{ticks}</div>', unsafe_allow_html=True)


def _prism_svg():
    rays = "".join(
        f'<line x1="290" y1="158" x2="440" y2="{275 - i * 83 / 6:.1f}" stroke="{c}" stroke-width="3.5" stroke-linecap="round"/>'
        for i, (_, _, c) in enumerate(P.LINES))
    return ('<svg viewBox="0 0 520 330" role="img" aria-label="White light enters a prism and fans out into seven colours; violet bends most" '
            'style="display:block;width:100%;height:100%;min-height:260px">'
            '<polygon points="250,80 170,225 330,225" fill="rgba(255,255,255,.07)" stroke="#9FB3C2" stroke-width="1.5"/>'
            '<line x1="20" y1="186" x2="210" y2="152" stroke="#F4F1E8" stroke-width="3.5" stroke-linecap="round"/>'
            '<line x1="210" y1="152" x2="290" y2="158" stroke="#F4F1E8" stroke-opacity=".45" stroke-width="2"/>'
            '<line x1="290" y1="158" x2="440" y2="158" stroke="#8A98A5" stroke-dasharray="5 5"/>' + rays +
            '<text x="448" y="162" fill="#8A98A5" font-size="13">direct ray</text>'
            f'<text x="448" y="279" fill="{P.LINES[0][2]}" font-size="13">Violet</text>'
            f'<text x="448" y="196" fill="{P.LINES[-1][2]}" font-size="13">Red</text></svg>')


def hero():
    st.markdown(
        '<section class="hero"><div class="hero-copy"><div class="hero-h">Measure how glass bends each colour.</div>'
        '<p class="hero-p">Log vernier readings at the direct ray and at each spectral line. Prism Lab turns the deviations into a '
        'refractive index μ for every colour and the dispersive power ω of the prism.</p></div>'
        f'<div class="hero-plate">{_prism_svg()}</div></section>', unsafe_allow_html=True)


def workflow(ss):
    lines = _logged(ss.obs)
    has_udr = (not ss.obs.empty and bool((ss.obs["Line"].astype(str).str.upper() == "UDR").any())) or abs(float(ss.direct) - 180.0) > 1e-9
    steps = [
        ("Record the direct ray", "Set the telescope on the undeviated slit image and note both verniers.", has_udr, "Done", "To do"),
        ("Log spectral lines", "Scan a vernier photo, type readings, or use the virtual bench.", len(lines) >= 1, "Done", "To do"),
        ("Cover three colours", "Three lines give a dispersive power. More lines improve the Cauchy fit.", len(lines) >= 3, "Done", "To do"),
        ("Export", "Download the readings as CSV or the whole experiment as JSON.", not ss.obs.empty, "Ready", "Nothing to export yet"),
    ]
    cells = "".join(
        f'<div class="{"done" if d else ""}"><span class="dot">{"✓" if d else i + 1}</span><div class="flow-t">{t}</div>'
        f'<div class="flow-c">{c}</div><div class="flow-s">{a if d else b}</div></div>' for i, (t, c, d, a, b) in enumerate(steps))
    st.markdown(f'<div class="flow">{cells}</div>', unsafe_allow_html=True)


def vernier_readouts(v1, v2):
    st.markdown(f'<div class="vern"><div><div class="k">Vernier V1</div><div class="v">{v1:.2f}°</div></div>'
                f'<div><div class="k">Vernier V2</div><div class="v">{v2:.2f}°</div></div></div>', unsafe_allow_html=True)


def eyepiece(offset, color):
    x = 150 + max(-85, min(85, offset * 0.6))
    st.markdown(
        '<svg viewBox="0 0 300 220" width="100%" role="img" aria-label="Eyepiece view of the spectral line against the cross-wire">'
        '<defs><clipPath id="fov"><circle cx="150" cy="110" r="100"/></clipPath><filter id="glow"><feGaussianBlur stdDeviation="3"/></filter></defs>'
        '<circle cx="150" cy="110" r="104" fill="#05070B" stroke="#3A4651" stroke-width="6"/><g clip-path="url(#fov)">'
        f'<line x1="{x:.1f}" y1="0" x2="{x:.1f}" y2="220" stroke="{color}" stroke-width="10" opacity=".55" filter="url(#glow)"/>'
        f'<line x1="{x:.1f}" y1="0" x2="{x:.1f}" y2="220" stroke="{color}" stroke-width="3"/>'
        '<line x1="150" y1="0" x2="150" y2="220" stroke="#DDE4EA" stroke-width="1"/>'
        '<line x1="0" y1="110" x2="300" y2="110" stroke="#DDE4EA" stroke-width="1"/></g></svg>', unsafe_allow_html=True)
