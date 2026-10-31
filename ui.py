"""UI helpers: theme injection and HTML widgets. Pure presentation; no physics here."""
from pathlib import Path

_CSS = Path(__file__).parent / "assets" / "theme.css"
_DARK = dict(bg="#0A0F1E", side="#0D1326", card="rgba(20,28,50,.72)", card2="rgba(30,27,75,.55)", border="rgba(139,92,246,.24)",
             text="#E8ECF8", muted="#94A3B8", accent="#8B5CF6", accent2="#6366F1", glow="rgba(139,92,246,.28)",
             hover="rgba(139,92,246,.10)", input="rgba(15,23,42,.85)")
_LIGHT = dict(bg="#F3F5FB", side="#E9EDF7", card="#FFFFFF", card2="#EEF0FF", border="#D6DCEB",
              text="#0F172A", muted="#5B6478", accent="#7C3AED", accent2="#4F46E5", glow="rgba(124,58,237,.18)",
              hover="rgba(124,58,237,.08)", input="#FFFFFF")

def theme_css(mode: str = "dark") -> str:
    v = _LIGHT if mode == "light" else _DARK
    root = ":root{" + ";".join(f"--{k}:{x}" for k, x in v.items()) + "}"
    return root + (_CSS.read_text(encoding="utf-8") if _CSS.exists() else "")

def inject_theme(mode: str = "dark") -> None:
    import streamlit as st
    st.markdown(f"<style>{theme_css(mode)}</style>", unsafe_allow_html=True)

def brand() -> None:
    import streamlit as st
    st.sidebar.markdown("<div class='brand'><div class='logo'>🔬</div><div><b>Prism Lab</b><small>Spectrometer practical</small></div></div>", unsafe_allow_html=True)

def hero_html(title: str, subtitle: str = "", chips=()) -> str:
    cs = "".join(f"<span class='chip {c[1] if isinstance(c, tuple) else ''}'>{c[0] if isinstance(c, tuple) else c}</span>" for c in chips)
    return f"<div class='hero'><h1>{title}</h1><p>{subtitle}</p><div class='chips'>{cs}</div></div>"

def hero(title, subtitle="", chips=()) -> None:
    import streamlit as st
    st.markdown(hero_html(title, subtitle, chips), unsafe_allow_html=True)

def eyepiece_html(color: str = "#64748B", title: str = "Rotate telescope", status: str = "NO MERCURY LINE IN FIELD", aligned: bool = False) -> str:
    w = 10 if aligned else 2
    glow = f"box-shadow:0 0 {26 if aligned else 0}px {color},0 0 60px {color}66" if aligned else ""
    return (f"<div class='eyepiece-wrap'><div class='eyepiece'><div class='h'></div><div class='v'></div>"
            f"<div class='slit' style='width:{w}px;background:{color};{glow}'></div></div>"
            f"<div class='eyepiece-label'><b>{title}</b><small>{status}</small></div></div>")

def eyepiece(*a, **k) -> None:
    import streamlit as st
    st.markdown(eyepiece_html(*a, **k), unsafe_allow_html=True)

def spectrum_strip_html(lines, lo: float = 380, hi: float = 700) -> str:
    marks = ""
    for l in lines:
        nm = l.get("wavelength", l.get("nm")); col = l.get("color", "#fff")
        if nm is None or not lo <= nm <= hi: continue
        marks += f"<i style='left:{(nm-lo)/(hi-lo)*100:.1f}%;color:{col};background:{col}'><span>{nm:g}</span></i>"
    return f"<div class='strip'>{marks}</div><div class='scale'><span>{lo:g} nm</span><span>Illustrative VIBGYOR background · markers = line wavelengths</span><span>{hi:g} nm</span></div>"

def spectrum_strip(lines) -> None:
    import streamlit as st
    st.markdown(spectrum_strip_html(lines), unsafe_allow_html=True)
