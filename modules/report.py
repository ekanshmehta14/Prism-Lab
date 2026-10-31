import csv, io, json
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet


def csv_bytes(state):
    output = io.StringIO()
    obs = state["observations"]
    if obs:
        writer = csv.DictWriter(output, fieldnames=sorted(set().union(*(row.keys() for row in obs))))
        writer.writeheader(); writer.writerows(obs)
    else:
        output.write("No observations recorded\n")
    return output.getvalue().encode("utf-8")


def json_bytes(state):
    return json.dumps(state, indent=2, default=str).encode("utf-8")


def pdf_bytes(state):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet(); story=[]
    story += [Paragraph("Prism Spectrometer Practical Report", styles["Title"]), Spacer(1,12),
              Paragraph("Aim: Determine refractive index and dispersive power of prism material.", styles["BodyText"]), Spacer(1,12)]
    data = [["Side","Order","Line","λ nm","Source","Verified"]]
    for r in state["observations"]:
        data.append([str(r.get("side","")), str(r.get("order","")), str(r.get("spectral_line",r.get("spectral_colour",""))), str(r.get("wavelength_nm","—")), str(r.get("source","")), str(r.get("verified",False))])
    if len(data)==1: data.append(["—","—","No observations","—","—","—"])
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#1E293B")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),0.5,colors.grey)]))
    story += [table, Spacer(1,12), Paragraph("Missing data is not fabricated. Simulated results are explicitly labeled.", styles["Italic"])]
    doc.build(story)
    return buf.getvalue()
