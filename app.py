import streamlit as st
import pandas as pd
import json
import hashlib
from PIL import Image
import io

from modules.spectrum import MERCURY_LINES
from modules.calculations import normalize_angle, convert_vernier_reading, refractive_index, dispersive_power
from modules.observations import add_observation, observations_frame, validate_import_payload
from modules.image_reader import extract_reading, read_scale_crop
from modules.gemini_reader import read_spectrometer_scale
from modules.visualization import refractive_index_plot, deviation_plot, calibration_plot
from modules.report import csv_bytes, json_bytes, pdf_bytes
from modules.optics import line_target_angle
from components.telescope import telescope
from ui import inject_theme, brand, hero, eyepiece, spectrum_strip

st.set_page_config(page_title="Prism Spectrometer Lab", page_icon="🔬", layout="wide")
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode="dark"

inject_theme(st.session_state.theme_mode)

if "observations" not in st.session_state:
    st.session_state.observations=[]
if "telescope_angle" not in st.session_state or st.session_state.get("telescope_default_version") != 2:
    st.session_state.telescope_angle=180.0
    st.session_state.telescope_default_version=2
if "prism_angle" not in st.session_state:
    st.session_state.prism_angle=60.0
if "least_count" not in st.session_state:
    st.session_state.least_count=1/60
if "scanner_results" not in st.session_state:
    st.session_state.scanner_results=[]
if "controls_visible" not in st.session_state:
    st.session_state.controls_visible=True
if "mercury_source_origin" not in st.session_state:
    st.session_state.mercury_source_origin=0.0

state={"observations":st.session_state.observations,"prism_angle":st.session_state.prism_angle,"least_count":st.session_state.least_count}

theme_action = "☀️ Light mode" if st.session_state.theme_mode == "dark" else "🌙 Dark mode"
if st.sidebar.button(theme_action, use_container_width=True, key="theme_toggle"):
    st.session_state.theme_mode = "light" if st.session_state.theme_mode == "dark" else "dark"
    st.rerun()

brand()
page=st.sidebar.radio("Navigate",["Experiment Overview","Virtual Spectrometer","Image Reading Scanner","Observation Table","Calculations and Results","Graphs and Analysis","Lab Report and Export","Theory and Viva Questions"])

if page=="Experiment Overview":
    hero("Refractive Index & Dispersive Power of a Prism","Virtual spectrometer practical: rotate the telescope, locate mercury lines on both sides, record readings from images or by hand, and calculate results.",[("Hg lamp","ref"),("Orders 1 & 2 only","ok"),("Local OCR","ocr"),("Simulated data labelled","sim")])
    c1,c2,c3=st.columns(3)
    c1.metric("Prism angle",f"{st.session_state.prism_angle:.1f}°")
    c2.metric("Observations",len(st.session_state.observations))
    c3.metric("Verified",sum(1 for x in st.session_state.observations if x.get("verified")))
    tabs=st.tabs(["Aim & Apparatus","Theory","Procedure","Safety & Errors"])
    with tabs[0]:
        st.markdown("**Aim:** To determine the refractive index and dispersive power of prism material for prominent mercury spectral lines.")
        st.write("**Apparatus:** Spectrometer, prism, mercury lamp, prism table, collimator, telescope, reading lens and vernier scales.")
    with tabs[1]:
        st.latex(r"\mu=\frac{\sin[(A+D_m)/2]}{\sin(A/2)}")
        st.latex(r"\omega=\frac{\mu_v-\mu_r}{\mu_y-1}")
        st.info("The Mercury source has been simplified into the seven visible VIBGYOR bands: Violet, Indigo, Blue, Green, Yellow, Orange and Red. No Blue-violet or Yellow companion categories are used.")
    with tabs[2]:
        st.markdown("1. Level and calibrate the spectrometer.\n2. Set and measure the prism angle.\n3. Obtain direct and deviated readings on left and right sides.\n4. Locate lines by order, moving the telescope rather than the eye.\n5. Record and verify readings.\n6. Calculate minimum deviation, refractive index and dispersive power.")
    with tabs[3]:
        st.write("Avoid touching optical surfaces. Verify zero calibration. Common errors include backlash, parallax, poor collimation, incorrect vernier use, and misidentified orders.")

elif page=="Virtual Spectrometer":
    st.title("Interactive Virtual Spectrometer")
    left,right=st.columns([1.15,1])
    with left:
        st.session_state.prism_angle=st.slider("Prism angle A (°)",30.0,75.0,float(st.session_state.prism_angle),0.5)
        sensitivity=st.slider("Fine adjustment sensitivity (°)",0.1,5.0,1.0,0.1)
        angle=telescope(st.session_state.telescope_angle,key="telescope",theme=st.session_state.theme_mode)
        if angle is not None:
            st.session_state.telescope_angle=float(angle)
        c1,c2,c3,c4=st.columns(4)
        if c1.button("−1°"):
            st.session_state.telescope_angle=normalize_angle(st.session_state.telescope_angle-sensitivity)
        if c2.button("+1°"):
            st.session_state.telescope_angle=normalize_angle(st.session_state.telescope_angle+sensitivity)
        st.caption("Both Order 1 spectra start at 180°: Right side advances clockwise and Left side counter-clockwise by 4° between colours.")
    with right:
        st.subheader("Telescope eyepiece")
        line_targets=[]
        source_origin=st.session_state.mercury_source_origin
        telescope_angle=normalize_angle(st.session_state.telescope_angle)
        if telescope_angle < 180:
            active_side="Left"
        elif telescope_angle > 180:
            active_side="Right"
        else:
            active_side="Origin"

        sectors=[("Right",1,0),("Left",1,0),("Right",2,110),("Left",2,-70)]
        if active_side == "Origin":
            line_targets.append((0.0,"Origin",1,MERCURY_LINES[0],180.0))
        for sector_side,sector_order,dispersion_offset in sectors:
            if active_side == "Origin" or sector_side != active_side:
                continue
            for index,candidate in enumerate(MERCURY_LINES):
                direction=1 if sector_side=="Right" else -1
                if sector_order==1:
                    target=normalize_angle(180+direction*index*4)
                else:
                    target=normalize_angle(source_origin+dispersion_offset+direction*index*4)
                delta=st.session_state.telescope_angle-target
                if delta > 180: delta -= 360
                elif delta < -180: delta += 360
                line_targets.append((abs(delta),sector_side,sector_order,candidate,target))
        error,side,order,line,target=min(line_targets,key=lambda item:item[0])
        aligned=error<=max(1.5,0.8*sensitivity)
        if aligned:
            eyepiece_color=line["color"]
            line_text=f"{line['name']} | {line['wavelength']} nm"
            status=f"{side.upper()} SIDE • ORDER {order}"
            line_width=12
        else:
            side=None; order=None; line=None
            eyepiece_color="#64748B"
            line_text="Rotate telescope"
            status="NO MERCURY LINE IN FIELD"
            line_width=2
        eyepiece(eyepiece_color,line_text,status,aligned)
        spectrum_strip([{'wavelength':x['wavelength'],'color':x['color']} for x in MERCURY_LINES])
        st.metric("Current angle",f"{st.session_state.telescope_angle:.1f}°")
        st.metric("Nearest line angle error",f"{error:.1f}°")
        if c3.button("Align nearest line"):
            st.session_state.telescope_angle=target
        if c4.button("Record observed reading",disabled=not aligned):
            ms=int(st.session_state.telescope_angle)
            vc=int(round((st.session_state.telescope_angle-ms)*60/st.session_state.least_count))
            add_observation(state,{"side":side,"order":order,"spectral_colour":line["name"],"spectral_line":line["name"],"wavelength_nm":line["wavelength"],"main_scale":ms,"vernier":vc,"least_count":st.session_state.least_count,"final_reading":convert_vernier_reading(ms,vc,st.session_state.least_count),"minimum_deviation":None,"source":"simulated","verified":False})
            st.session_state.observations=state["observations"]
            st.success("Simulated observation recorded. It remains labelled as simulated until verified.")

elif page=="Image Reading Scanner":
    st.title("Image Reading Scanner")
    uploads=st.file_uploader("Upload JPG, JPEG, PNG or WebP",type=["jpg","jpeg","png","webp"],accept_multiple_files=True)
    if uploads:
        for upload in uploads:
            image=Image.open(upload).convert("RGB")
            upload_id=hashlib.sha256(upload.getvalue()).hexdigest()[:12]
            st.subheader(upload.name)
            c1,c2=st.columns(2)
            with c1: st.image(image,use_container_width=True,caption="Original image")
            processed=image
            with c2: st.image(processed,use_container_width=True,caption="Enhanced review area")
            result=extract_reading(processed,upload.name)
            st.caption("Reading extracted directly from the uploaded image. Locally detected values can be corrected below.")
            if result["text"]: st.code(result["text"][:1000])
            if not result["numbers"]:
                st.info("No reliable two-value scale reading was detected. Enter the reading manually from the image.")
            with st.expander("Scale Reading Tool — select and zoom the scale"):
                st.caption("Drag the area controls to isolate the main scale or vernier, then read the enlarged crop.")
                left=st.slider("Crop left (%)",0,80,8,key=upload_id+"crop-left")
                top=st.slider("Crop top (%)",0,80,15,key=upload_id+"crop-top")
                crop_width=st.slider("Crop width (%)",10,100,50,key=upload_id+"crop-width")
                crop_height=st.slider("Crop height (%)",10,100,55,key=upload_id+"crop-height")
                iw,ih=image.size
                x1=int(iw*left/100)
                y1=int(ih*top/100)
                x2=min(iw,int(iw*(left+crop_width)/100))
                y2=min(ih,int(ih*(top+crop_height)/100))
                scale_crop=image.crop((x1,y1,x2,y2))
                zoomed=scale_crop.resize((max(scale_crop.width*3,900),max(scale_crop.height*3,900)),resample=Image.Resampling.LANCZOS)
                st.image(zoomed,use_container_width=True,caption="Selected scale area enlarged 3x")
                if st.button("Read with Gemini",key=upload_id+"read-gemini"):
                    cloud_result=read_spectrometer_scale(scale_crop)
                    st.session_state[upload_id+"gemini-result"]=cloud_result
                    if cloud_result["ok"]:
                        st.success(f"Gemini confidence: {cloud_result['confidence']:.0%}")
                    else:
                        st.error(cloud_result["error"])
                cloud_result=st.session_state.get(upload_id+"gemini-result")
                if cloud_result and cloud_result["ok"]:
                    gc1,gc2,gc3=st.columns(3)
                    if cloud_result["main_scale"] is not None:
                        gc1.metric("Gemini main scale",f"{cloud_result['main_scale']:.3f}")
                        if gc1.button("Apply Gemini main scale",key=upload_id+"apply-gemini-main"):
                            st.session_state[upload_id+"-ms"]=float(cloud_result["main_scale"])
                            st.rerun()
                    if cloud_result["vernier"] is not None:
                        gc2.metric("Gemini vernier",f"{cloud_result['vernier']:.3f}")
                        if gc2.button("Apply Gemini vernier",key=upload_id+"apply-gemini-vernier"):
                            st.session_state[upload_id+"-vc"]=float(cloud_result["vernier"])
                            st.rerun()
                if st.button("Read selected scale area",key=upload_id+"read-crop"):
                    crop_result=read_scale_crop(scale_crop,upload.name)
                    st.session_state[upload_id+"crop-text"]=crop_result["text"]
                    st.session_state[upload_id+"main-options"]=crop_result["main_candidates"]
                    st.session_state[upload_id+"vernier-options"]=crop_result["vernier_candidates"]
                crop_text=st.session_state.get(upload_id+"crop-text","")
                if crop_text: st.code(crop_text[:1200])
                main_options=st.session_state.get(upload_id+"main-options",[])
                vernier_options=st.session_state.get(upload_id+"vernier-options",[])
                tc1,tc2=st.columns(2)
                if main_options:
                    chosen_main=tc1.selectbox("Detected main-scale value",main_options,key=upload_id+"main-choice")
                    if tc1.button("Apply main scale",key=upload_id+"apply-main"):
                        st.session_state[upload_id+"-ms"]=float(chosen_main)
                        st.rerun()
                if vernier_options:
                    chosen_vernier=tc2.selectbox("Detected vernier value",vernier_options,key=upload_id+"vernier-choice")
                    if tc2.button("Apply vernier",key=upload_id+"apply-vernier"):
                        st.session_state[upload_id+"-vc"]=float(chosen_vernier)
                        st.rerun()
            r1,r2,r3,r4,r5=st.columns(5)
            side=r1.selectbox("Side",["Left","Right"],key=upload.name+"side")
            order=int(r2.selectbox("Order",[1,2],key=upload.name+"order"))
            line_name=r3.selectbox("Line",[x["name"] for x in MERCURY_LINES],key=upload.name+"line")
            ms=r4.number_input("Main scale",value=float(result["main_scale"] or 0),format="%.3f",key=upload_id+"-ms")
            vc=r5.number_input("Vernier",value=float(result["vernier"] or 0),format="%.3f",key=upload_id+"-vc")
            confidence=st.progress(result["confidence"],text=f"OCR confidence: {result['confidence']:.0%}")
            if st.button("Confirm and save reading",key=upload.name+"save"):
                line=next(x for x in MERCURY_LINES if x["name"]==line_name)
                add_observation(state,{"side":side,"order":order,"spectral_colour":line_name,"spectral_line":line_name,"wavelength_nm":line["wavelength"],"main_scale":ms,"vernier":vc,"least_count":st.session_state.least_count,"final_reading":convert_vernier_reading(ms,vc,st.session_state.least_count),"minimum_deviation":None,"source":"OCR-extracted","verified":True})
                st.session_state.observations=state["observations"]
                st.success("Confirmed reading saved")

elif page=="Observation Table":
    st.title("Observation Table")
    with st.expander("Add a manual observation",expanded=False):
        m1,m2,m3,m4=st.columns(4)
        side=m1.selectbox("Side",["Left","Right"])
        order=int(m2.selectbox("Order",[1,2]))
        line_name=m3.selectbox("Spectral line",[x["name"] for x in MERCURY_LINES])
        minimum=m4.number_input("Minimum deviation (°)",0.0,180.0,0.0)
        n1,n2,n3,n4=st.columns(4)
        ms=n1.number_input("Main scale",0.0,359.999)
        vc=n2.number_input("Vernier division",0.0)
        lc=n3.number_input("Least count",0.000001,1.0,float(st.session_state.least_count),format="%.6f")
        source=n4.selectbox("Data source",["manually entered","OCR-extracted","simulated","reference"])
        if st.button("Add observation"):
            line=next(x for x in MERCURY_LINES if x["name"]==line_name)
            add_observation(state,{"side":side,"order":order,"spectral_colour":line_name,"spectral_line":line_name,"wavelength_nm":line["wavelength"],"main_scale":ms,"vernier":vc,"least_count":lc,"final_reading":convert_vernier_reading(ms,vc,lc),"minimum_deviation":minimum if minimum>0 else None,"source":source,"verified":False})
            st.session_state.observations=state["observations"]
            st.rerun()
    df=observations_frame(state)
    st.dataframe(df,use_container_width=True)
    c1,c2,c3=st.columns(3)
    delete_id=c1.number_input("Observation ID to delete",min_value=0,step=1)
    if c2.button("Delete") and delete_id>0:
        st.session_state.observations=[x for x in st.session_state.observations if x["id"]!=delete_id]
        st.rerun()
    verify_id=c3.number_input("ID to verify",min_value=0,step=1,key="verifyid")
    if st.button("Mark verified"):
        for x in st.session_state.observations:
            if x["id"]==verify_id: x["verified"]=True
        st.rerun()
    uploaded=st.file_uploader("Import experiment JSON",type=["json"])
    if uploaded:
        try:
            payload=validate_import_payload(json.load(uploaded)); st.session_state.observations=payload["observations"]
            st.session_state.prism_angle=float(payload.get("prism_angle",60)); st.success("Experiment imported")
        except Exception as exc: st.error(str(exc))

elif page=="Calculations and Results":
    st.title("Calculations and Results")
    st.session_state.prism_angle=st.number_input("Prism angle A (°)",1.0,179.0,float(st.session_state.prism_angle))
    st.subheader("Refractive index by wavelength")
    results=[]
    for line in MERCURY_LINES:
        rows=[x for x in st.session_state.observations if x.get("wavelength_nm")==line["wavelength"] and x.get("minimum_deviation") not in (None,0)]
        if rows:
            D=sum(float(x["minimum_deviation"] ) for x in rows)/len(rows)
            try:
                mu=refractive_index(st.session_state.prism_angle,D)
                results.append({"line":line["name"],"wavelength_nm":line["wavelength"],"minimum_deviation":D,"refractive_index":mu})
                st.write(f"**{line['name']} ({line['wavelength']} nm):** μ = {mu:.5f}")
            except ValueError as exc: st.warning(str(exc))
        else: st.write(f"**{line['name']} ({line['wavelength']} nm):** Insufficient measurements")
    st.subheader("Dispersive power")
    by_w={r["wavelength_nm"]:r["refractive_index"] for r in results}
    yellow=max((x for x in by_w if 570<=x<=580),key=by_w.get,default=None)
    violet=max((x for x in by_w if x<440),key=by_w.get,default=None)
    red=max((x for x in by_w if x>=620),key=by_w.get,default=None)
    missing=[]
    if violet: mv=by_w[violet]
    else: missing.append("violet")
    if red: mr=by_w[red]
    else:
        # Documented fallback: mercury has no red reference line in this data set.
        mr=None; missing.append("mercury red line")
    if yellow: my=by_w[yellow]
    else: missing.append("yellow")
    if missing:
        st.warning("Missing observations: "+", ".join(missing)+". Dispersive power not calculated.")
    else:
        st.write(f"ω = ({mv:.5f} − {mr:.5f}) / ({my:.5f} − 1) = **{dispersive_power(mv,my,mr):.5f}**")
    st.session_state.result_rows=results

elif page=="Graphs and Analysis":
    st.title("Graphs and Analysis")
    rows=getattr(st.session_state,"result_rows",[])
    c1,c2=st.columns(2)
    c1.plotly_chart(refractive_index_plot(rows),use_container_width=True)
    c2.plotly_chart(deviation_plot(rows),use_container_width=True)
    st.subheader("Calibration data")
    calibration=[]
    raw=st.text_area("Calibration pairs (wavelength_nm, measured_deviation), one per line")
    for line in raw.splitlines():
        try:
            a,b=(float(x.strip()) for x in line.split(",")); calibration.append((a,b))
        except Exception: pass
    measured=st.number_input("Unknown measured deviation (°)",0.0,180.0,0.0)
    if len(calibration)>=2:
        wavelengths=sorted(calibration)
        # Simple interpolation of measured value against recorded deviation.
        xs=sorted([p[1] for p in wavelengths]); ys=sorted([p[0] for p in wavelengths])
        if  min(xs)<=measured<=max(xs): estimated=float(pd.Series(ys).interpolate().iloc[0]) if False else float(__import__('numpy').interp(measured,xs,ys))
        else: estimated=None
        if estimated is not None: st.success(f"Estimated wavelength: {estimated:.1f} nm (interpolation within calibration range)")
        else: st.warning("Measured value is outside the calibration range; no wavelength estimate shown.")
        st.plotly_chart(calibration_plot(calibration,[measured,estimated] if estimated else None),use_container_width=True)
    else: st.info("No calibration data. Reference wavelengths are shown separately and are not independent measured values.")

elif page=="Lab Report and Export":
    st.title("Lab Report and Export")
    st.write("The report labels simulated, reference and experimentally measured results separately. Incomplete data remains explicitly missing.")
    state["prism_angle"]=st.session_state.prism_angle
    c1,c2,c3=st.columns(3)
    c1.download_button("Download CSV",csv_bytes(state),"prism_observations.csv","text/csv")
    c2.download_button("Download JSON",json_bytes(state),"prism_experiment.json","application/json")
    c3.download_button("Download PDF",pdf_bytes(state),"prism_report.pdf","application/pdf")

else:
    st.title("Theory and Viva Questions")
    questions=[
        ("What is refractive index?","The ratio of the speed of light in vacuum to that in the medium, also n=sin i/sin r."),
        ("What is dispersive power?","The relative separation of violet and red refractive indices for a representative mean refractive index."),
        ("What is minimum deviation?","The smallest angular deviation for a given prism and wavelength, occurring at symmetric ray passage."),
        ("Principle of a spectrometer?","Collimation, dispersion/refraction and telescope observation permit precise angular measurement."),
        ("Function of the collimator?","Produces a parallel beam from the slit for the prism."),
        ("Function of the telescope?","Collects and magnifies the emergent rays so spectral lines can be aligned and read."),
        ("Purpose of the prism table?","Supports and rotates the prism for alignment and measurement."),
        ("Reflection vs refraction?","Reflection returns light to the incident medium; refraction bends it while crossing media."),
        ("State Snell's law.","n₁ sin i=n₂ sin r."),
        ("What is prism angle?","The angle between the two refracting faces."),
        ("What is angular deviation?","The change in direction between incident and emergent rays."),
        ("What is vernier least count?","The smallest readable difference between main-scale and vernier divisions."),
        ("Sources of experimental error?","Parallax, backlash, calibration offset, slit width, prism placement and reading uncertainty."),
        ("Why mercury lines?","Mercury vapour emits characteristic discrete visible wavelengths rather than a continuous rainbow."),
        ("How does wavelength relate to refractive index?","Normally refractive index and deviation decrease across the visible spectrum as wavelength increases, with material dispersion."),
        ("Why do colours deviate differently?","They refract differently because the material refractive index depends on wavelength."),
        ("Why can reference and experimental wavelengths differ?","Reference data are known line identities; experimental uncertainty, calibration and apparatus conditions affect measured association."),
        ("Why locate minimum deviation?","A symmetric minimum-deviation geometry allows the standard μ formula to be applied reliably."),
        ("What are first and second orders?","Angular diffraction/spectral observation groups; this educational prism simulation limits collection to orders 1 and 2."),
        ("How is the vernier reading converted?","MSR plus coincident vernier division multiplied by least count, with configured calibration offset if used."),
    ]
    for i,(q,a) in enumerate(questions,1):
        with st.expander(f"Q{i}. {q}"): st.write(a)
