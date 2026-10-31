MERCURY_LINES = [
    {"name":"Violet", "wavelength":404.7, "color":"#7C4DFF", "relative_brightness":0.75},
    {"name":"Indigo", "wavelength":445.0, "color":"#4B0082", "relative_brightness":0.72},
    {"name":"Blue", "wavelength":480.0, "color":"#2196F3", "relative_brightness":0.78},
    {"name":"Green", "wavelength":530.0, "color":"#00E676", "relative_brightness":1.00},
    {"name":"Yellow", "wavelength":580.0, "color":"#FFEA00", "relative_brightness":0.95},
    {"name":"Orange", "wavelength":610.0, "color":"#FF9800", "relative_brightness":0.85},
    {"name":"Red", "wavelength":650.0, "color":"#F44336", "relative_brightness":0.82},
]

def get_line(name):
    return next((x for x in MERCURY_LINES if x["name"] == name), None)

def wavelength_to_css(wavelength):
    if wavelength < 440: return "#7C4DFF"
    if wavelength < 490: return "#536DFE"
    if wavelength < 510: return "#2196F3"
    if wavelength < 575: return "#00E676"
    if wavelength < 590: return "#FFEA00"
    if wavelength < 620: return "#FF9800"
    return "#F44336"
