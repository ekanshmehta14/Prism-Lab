import pandas as pd
import plotly.graph_objects as go


def refractive_index_plot(rows):
    fig = go.Figure()
    if rows:
        df = pd.DataFrame(rows)
        fig.add_trace(go.Scatter(x=df["wavelength_nm"], y=df["refractive_index"], mode="lines+markers", name="Calculated μ"))
    fig.update_layout(template="plotly_dark", xaxis_title="Wavelength (nm)", yaxis_title="Refractive index μ", height=380)
    return fig


def deviation_plot(rows):
    fig = go.Figure()
    if rows:
        df = pd.DataFrame(rows)
        fig.add_trace(go.Scatter(x=df["wavelength_nm"], y=df["minimum_deviation"], mode="lines+markers", name="Measured deviation"))
    fig.update_layout(template="plotly_dark", xaxis_title="Wavelength (nm)", yaxis_title="Minimum deviation (degrees)", height=380)
    return fig


def calibration_plot(points, estimated=None):
    fig = go.Figure()
    if points:
        fig.add_trace(go.Scatter(x=[p[1] for p in points], y=[p[0] for p in points], mode="markers+lines", name="Calibration points"))
    if estimated is not None:
        fig.add_trace(go.Scatter(x=[estimated[0]], y=[estimated[1]], mode="markers", name="Estimated", marker=dict(size=12, color="#7C4DFF")))
    fig.update_layout(template="plotly_dark", xaxis_title="Measured value", yaxis_title="Wavelength (nm)", height=380)
    return fig
