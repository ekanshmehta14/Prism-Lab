import hashlib, json, os
import numpy as np, pandas as pd, plotly.graph_objects as go, streamlit as st
from PIL import Image
import physics as P
import simulation
import ui
from gemini_reader import read_scale, DEFAULT_MODEL

st.set_page_config(page_title="Prism Lab", page_icon="🔬", layout="wide")

ui.inject()

ss = st.session_state
READING_COLUMNS = [
    "S.No", "Line", "Vernier", "Right reading (°)", "Left reading (°)", "Difference (°)",
    "Deviation (°)", "Source"
]
ss.setdefault("obs", pd.DataFrame(columns=READING_COLUMNS))
ss.setdefault("direct", 180.0)
ss.setdefault("prism", 60.0)
ss.setdefault("scans", {})


def api_key():
    try:
        k = st.secrets["GEMINI_API_KEY"]
    except Exception:
        k = None
    return k or os.getenv("GEMINI_API_KEY")


def collapse_duplicate_vernier_rows():
    if ss.obs.empty:
        return
    collapsed = pd.DataFrame(columns=READING_COLUMNS)
    for _, row in ss.obs.iterrows():
        matches = collapsed[
            (collapsed["Line"].astype(str) == str(row["Line"]))
            & (collapsed["Vernier"].astype(str) == str(row["Vernier"]))
        ]
        if matches.empty:
            collapsed.loc[len(collapsed)] = row.reindex(READING_COLUMNS).fillna(None)
        else:
            idx = matches.index[0]
            for column in ("Right reading (°)", "Left reading (°)"):
                if pd.notna(row.get(column)):
                    collapsed.at[idx, column] = row[column]
    collapsed["S.No"] = range(1, len(collapsed) + 1)
    ss.obs = collapsed


def update_reading_calculations():
    if ss.obs.empty:
        return
    ss.obs["S.No"] = range(1, len(ss.obs) + 1)
    for idx, row in ss.obs.iterrows():
        if str(row["Line"]).upper() == "UDR":
            ss.obs.at[idx, "Difference (°)"] = None
            ss.obs.at[idx, "Deviation (°)"] = None
            continue
        right_reading = row.get("Right reading (°)")
        left_reading = row.get("Left reading (°)")
        if pd.notna(right_reading) and pd.notna(left_reading):
            difference = P.angle_diff(float(right_reading), float(left_reading))
            ss.obs.at[idx, "Difference (°)"] = round(difference, 4)
            ss.obs.at[idx, "Deviation (°)"] = round(difference / 2, 4)
        else:
            ss.obs.at[idx, "Difference (°)"] = None
            ss.obs.at[idx, "Deviation (°)"] = None


def normalize_observations():
    old = ss.obs.copy()
    if list(old.columns) == READING_COLUMNS:
        collapse_duplicate_vernier_rows()
        update_reading_calculations()
        return

    normalized = pd.DataFrame(columns=READING_COLUMNS)
    if not old.empty:
        for i, row in old.iterrows():
            side = row.get("Side", "")
            imported_reading = row.get("Reading (°)", row.get("Total (°)", row.get("Right reading (°)")))
            normalized.loc[len(normalized)] = {
                "S.No": len(normalized) + 1,
                "Line": row.get("Line", ""),
                "Vernier": "V1" if side == "Left" else "V2" if side == "Right" else "",
                "Right reading (°)": imported_reading if side != "Left" else row.get("Right reading (°)"),
                "Left reading (°)": imported_reading if side == "Left" else row.get("Left reading (°)"),
                "Difference (°)": None,
                "Deviation (°)": None,
                "Source": row.get("Source", "Imported"),
            }
    ss.obs = normalized
    collapse_duplicate_vernier_rows()
    update_reading_calculations()


def add_obs(line, side, reading, source, vernier=None):
    normalize_observations()
    side = str(side).strip()
    if vernier:
        vernier_name = vernier
    else:
        vernier_name = "V1" if side == "Left" else "V2" if side == "Right" else side

    matches = ss.obs[
        (ss.obs["Line"].astype(str) == str(line))
        & (ss.obs["Vernier"].astype(str) == vernier_name)
    ]
    column = "Right reading (°)" if side == "Right" else "Left reading (°)" if side == "Left" else None
    if column is not None and not matches.empty:
        idx = matches.index[0]
        ss.obs.at[idx, column] = round(reading, 4)
        ss.obs.at[idx, "Source"] = source
    else:
        row = pd.DataFrame([{
            "S.No": len(ss.obs) + 1,
            "Line": line,
            "Vernier": vernier_name,
            "Right reading (°)": round(reading, 4) if side == "Right" else None,
            "Left reading (°)": round(reading, 4) if side == "Left" else None,
            "Difference (°)": None,
            "Deviation (°)": None,
            "Source": source,
        }])
        ss.obs = pd.concat([ss.obs, row], ignore_index=True)

    update_reading_calculations()


def add_simulation_readings(line, side, v1_reading, v2_reading):
    normalize_observations()
    side = str(side).strip()
    column = "Right reading (°)" if side == "Right" else "Left reading (°)" if side == "Left" else None
    if column is None:
        return

    for vernier, reading in (("V1", v1_reading), ("V2", v2_reading)):
        matches = ss.obs[
            (ss.obs["Line"].astype(str) == str(line))
            & (ss.obs["Vernier"].astype(str) == vernier)
        ]
        if matches.empty:
            ss.obs = pd.concat(
                [ss.obs, pd.DataFrame([{
                    "S.No": len(ss.obs) + 1,
                    "Line": line,
                    "Vernier": vernier,
                    "Right reading (°)": None,
                    "Left reading (°)": None,
                    "Difference (°)": None,
                    "Deviation (°)": None,
                    "Source": "Simulated telescope",
                }])],
                ignore_index=True,
            )
            matches = ss.obs[
                (ss.obs["Line"].astype(str) == str(line))
                & (ss.obs["Vernier"].astype(str) == vernier)
            ]

        ss.obs.at[matches.index[0], column] = round(float(reading), 4)
        ss.obs.at[matches.index[0], "Source"] = "Simulated telescope"

    collapse_duplicate_vernier_rows()
    update_reading_calculations()


def import_readings_csv(uploaded_file):
    imported = pd.read_csv(uploaded_file)
    if imported.empty:
        raise ValueError("The CSV file is empty.")

    aliases = {
        "Line": ["Line", "Colour", "Color", "Line / colour"],
        "Vernier": ["Vernier", "Vernier No", "Vernier number"],
        "Right reading (°)": ["Right reading (°)", "Right reading", "Right", "Total (°)", "Total"],
        "Left reading (°)": ["Left reading (°)", "Left reading", "Left", "Reading (°)", "Reading"],
        "Source": ["Source", "Reading Source"],
    }

    def find_value(row, column):
        for alias in aliases[column]:
            if alias in imported.columns and pd.notna(row.get(alias)):
                return row[alias]
        return None

    normalized = pd.DataFrame(columns=READING_COLUMNS)
    side_aliases = ("Reading side", "Reading Side", "Side")
    for _, row in imported.iterrows():
        line = find_value(row, "Line")
        vernier = find_value(row, "Vernier")
        if pd.isna(line) or str(line).strip() == "":
            continue

        line = str(line).strip()
        vernier_value = str(vernier).strip().upper() if pd.notna(vernier) else ""
        if vernier_value not in ("V1", "V2"):
            continue

        right_reading = find_value(row, "Right reading (°)")
        left_reading = find_value(row, "Left reading (°)")
        side = next((row[column] for column in side_aliases if column in imported.columns and pd.notna(row[column])), None)
        reading = row.get("Reading (°)", row.get("Reading", row.get("Total (°)", row.get("Total"))))

        if pd.isna(right_reading) and pd.isna(left_reading) and pd.notna(reading):
            if str(side).strip().lower() == "left":
                left_reading = reading
            else:
                right_reading = reading

        normalized.loc[len(normalized)] = {
            "S.No": len(normalized) + 1,
            "Line": line,
            "Vernier": vernier_value,
            "Right reading (°)": pd.to_numeric(pd.Series([right_reading]), errors="coerce").iloc[0] if pd.notna(right_reading) else None,
            "Left reading (°)": pd.to_numeric(pd.Series([left_reading]), errors="coerce").iloc[0] if pd.notna(left_reading) else None,
            "Difference (°)": None,
            "Deviation (°)": None,
            "Source": "Imported CSV" if pd.isna(find_value(row, "Source")) else str(find_value(row, "Source")),
        }

    if normalized.empty:
        raise ValueError("No valid rows found. The CSV must contain Line and Vernier (V1 or V2) columns.")

    return normalized


def row_reading(row):
    for column in ("Right reading (°)", "Left reading (°)"):
        if column in row.index and pd.notna(row[column]):
            return float(row[column])
    return None


def navigate_to(target_page):
    ss.page_nav = target_page


with st.sidebar:
    ui.brand()
    page = st.radio("Workspace", ["Overview", "Scan scale (Gemini)", "Readings", "Results", "Simulation", "Export"],
                    key="page_nav", label_visibility="collapsed")
    ui.sidebar_status(len(ss.obs))
    st.divider()
    st.markdown("##### Experiment setup")
    ss.prism = st.number_input("Prism angle A (°)", 10.0, 90.0, float(ss.prism), 0.1)
    d = st.number_input("Direct ray reading (°)", 0.0, 360.0, float(ss.direct), 0.01, format="%.4f")
    ss.direct = d if d else ss.direct
    st.caption("Set the reference values before analysing observations.")
    st.divider()
    st.markdown("##### Checklist")
    st.caption("✓ Prism angle configured")
    st.caption("✓ Gemini scanner available" if api_key() else "○ Gemini key not configured")
    st.caption("✓ Direct ray recorded" if ss.direct else "○ Direct ray not recorded")

ui.page_header(page, ss.obs)

# ---------------------------------------------------------------- Overview
if page == "Overview":
    n = len(ss.obs)
    ui.hero()

    c1, c2, c3 = st.columns(3)
    c1.metric("Prism angle", f"{ss.prism:.1f}°", help="Configured prism angle A")
    c2.metric("Direct reading", f"{ss.direct:.3f}°" if ss.direct else "Not set", help="Reference reading before inserting the prism")
    c3.metric("Readings logged", n, help="Saved manual, scanned, and simulated readings")

    st.subheader("Your workflow")
    ui.workflow(ss)

    st.markdown("<div style='height:.7rem'></div>", unsafe_allow_html=True)
    q1, q2, q3 = st.columns(3)
    q1.button("Scan a scale photo", use_container_width=True, type="primary",
              on_click=navigate_to, args=("Scan scale (Gemini)",))
    q2.button("Add a manual reading", use_container_width=True,
              on_click=navigate_to, args=("Readings",))
    q3.button("Open the virtual bench", use_container_width=True,
              on_click=navigate_to, args=("Simulation",))

    st.subheader("From minimum deviation to refractive index")
    formula_col, note_col = st.columns([1.15, 1])
    with formula_col:
        with st.container(border=True):
            st.latex(r"\mu=\frac{\sin\left(\frac{A+D_m}{2}\right)}{\sin\left(\frac{A}{2}\right)}")
            st.latex(r"\omega=\frac{\mu_{\mathrm{short}}-\mu_{\mathrm{long}}}{\mu_{\mathrm{mean}}-1}")
    with note_col:
        with st.container(border=True):
            st.markdown("**Minimum deviation method**")
            st.caption("At minimum deviation, the light path through the prism is symmetric. The measured deviation and prism angle reveal the refractive index.")
            st.markdown("**A colourful result**")
            st.caption("In normal dispersion, violet light typically bends more than red light because its refractive index is higher.")
    with st.expander("Viva quick answers"):
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
                d1, d2, d3 = st.columns([1.2, 1, 1])
                line = d1.selectbox("Line / direct ray", ["UDR"] + P.LINE_NAMES, key=f"ln{uid}")
                side = d2.selectbox("Side", ["Left", "Right"], key=f"sd{uid}")
                st.metric(f"{side} reading", f"{total:.4f}°")
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
    st.subheader("Add observations for both verniers")
    line_options = ["UDR"] + P.LINE_NAMES

    with st.expander("Import readings from CSV", expanded=False):
        template = pd.DataFrame([{
            "S.No": 1,
            "Line": "Green",
            "Vernier": "V1",
            "Right reading (°)": 218.16,
            "Left reading (°)": 321.83,
            "Difference (°)": 103.67,
            "Deviation (°)": 51.835,
            "Source": "Imported CSV",
        }])
        st.download_button(
            "Download CSV template",
            template.to_csv(index=False),
            file_name="prism_lab_readings_template.csv",
            mime="text/csv",
        )
        imported_file = st.file_uploader(
            "Select readings CSV",
            type=["csv"],
            key="readings_csv_import",
        )
        import_mode = st.radio(
            "Import mode",
            ["Append to existing readings", "Replace existing readings"],
            horizontal=True,
            key="readings_import_mode",
        )
        if st.button("Import CSV", type="primary", disabled=imported_file is None):
            try:
                imported_rows = import_readings_csv(imported_file)
                if import_mode == "Replace existing readings":
                    ss.obs = imported_rows.copy()
                else:
                    ss.obs = pd.concat([ss.obs, imported_rows], ignore_index=True)
                collapse_duplicate_vernier_rows()
                update_reading_calculations()
                st.success(f"Imported {len(imported_rows)} reading rows successfully.")
                st.rerun()
            except Exception as exc:
                st.error(f"Could not import CSV: {exc}")

    l = st.selectbox("Line / colour", line_options, key="manual_line")
    reading_side = st.selectbox("Reading side", ["Right", "Left"], key="manual_reading_side")
    lc = st.number_input("Least count (°)", 0.00001, 1.0, 1 / 60, 0.00001, format="%.5f",
                         key="manual_least_count")
    v1, v2 = st.columns(2)
    v1_main = v1.number_input("V1 main scale (°)", 0.0, 360.0, 0.0, 0.01,
                              format="%.4f", key="manual_v1_main")
    v1_vernier = v1.number_input("V1 vernier division", 0.0, 60.0, 0.0, 1.0,
                                 format="%.1f", key="manual_v1_vernier")
    v2_main = v2.number_input("V2 main scale (°)", 0.0, 360.0, 0.0, 0.01,
                              format="%.4f", key="manual_v2_main")
    v2_vernier = v2.number_input("V2 vernier division", 0.0, 60.0, 0.0, 1.0,
                                 format="%.1f", key="manual_v2_vernier")

    if st.button("Add both vernier readings", type="primary"):
        for vernier, main, vernier_div in (
            ("V1", v1_main, v1_vernier),
            ("V2", v2_main, v2_vernier),
        ):
            total = P.vernier_reading(main, vernier_div, lc)
            add_obs(l, reading_side, total, "Manual", vernier)
        st.rerun()

    if ss.obs.empty:
        st.info("No readings yet. Scan a photo or add one by hand.")
    else:
        ss.obs = st.data_editor(ss.obs, num_rows="dynamic", use_container_width=True, hide_index=True,
                                column_config={
                                    "Line": st.column_config.SelectboxColumn(options=["UDR"] + P.LINE_NAMES),
                                    "Vernier": st.column_config.SelectboxColumn(options=["V1", "V2"]),
                                    "S.No": st.column_config.NumberColumn(disabled=True),
                                    "Difference (°)": st.column_config.NumberColumn(disabled=True, format="%.4f"),
                                    "Deviation (°)": st.column_config.NumberColumn(disabled=True, format="%.4f"),
                                })
        update_reading_calculations()

# ---------------------------------------------------------------- Results
elif page == "Results":
    normalize_observations()
    df = ss.obs.dropna(subset=["Line"]).copy()
    df = df[df.apply(row_reading, axis=1).notna()].copy()
    udr = df[df["Line"].astype(str).str.upper() == "UDR"]
    spectral = df[df["Line"].astype(str).str.upper() != "UDR"].copy()

    if spectral.empty:
        st.info("Log at least one spectral-line reading. UDR readings are shown only in the Readings table and excluded from wavelength calculations.")
    elif udr.empty and not ss.direct:
        st.info("Add UDR readings for V1 and V2, or set the direct-ray reading in the sidebar.")
    else:
        spectral["D (°)"] = np.nan
        for idx, row in spectral.iterrows():
            table_deviation = row.get("Deviation (°)")
            if pd.notna(table_deviation):
                spectral.at[idx, "D (°)"] = round(float(table_deviation), 4)
                continue

            vernier_udr = udr[udr["Vernier"] == row["Vernier"]] if not udr.empty else pd.DataFrame()
            side_deviations = []
            if not vernier_udr.empty:
                direct_row = vernier_udr.iloc[0]
                for column in ("Right reading (°)", "Left reading (°)"):
                    if pd.notna(row.get(column)) and pd.notna(direct_row.get(column)):
                        side_deviations.append(
                            P.angle_diff(float(row[column]), float(direct_row[column]))
                        )
            if not side_deviations and ss.direct:
                for column in ("Right reading (°)", "Left reading (°)"):
                    if pd.notna(row.get(column)):
                        side_deviations.append(
                            P.angle_diff(float(row[column]), float(ss.direct))
                        )
            if side_deviations:
                spectral.at[idx, "D (°)"] = round(sum(side_deviations) / len(side_deviations), 4)

        df = spectral
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
        fig.update_layout(**ui.PLOT,
                          xaxis_title="Wavelength (nm)", yaxis_title="Refractive index μ", height=420)
        st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------- Virtual bench
elif page == "Simulation":
    simulation.render(ss, add_obs, add_simulation_readings)

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
