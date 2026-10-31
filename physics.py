"""Optics and vernier helpers for the prism spectrometer experiment."""
import math
import numpy as np

# VIBGYOR visible spectrum colours (representative wavelengths in nm)
LINES = [
    ("Violet", 400.0, "#8B5CF6"),
    ("Indigo", 445.0, "#6366F1"),
    ("Blue", 470.0, "#3B82F6"),
    ("Green", 530.0, "#22C55E"),
    ("Yellow", 580.0, "#EAB308"),
    ("Orange", 610.0, "#F97316"),
    ("Red", 700.0, "#EF4444"),
]
LINE_NAMES = [l[0] for l in LINES]
WAVELENGTH = {l[0]: l[1] for l in LINES}
COLOUR = {l[0]: l[2] for l in LINES}


def vernier_reading(main_deg, vernier_div, least_count_deg):
    """Total reading in degrees = main scale + coinciding division x least count."""
    return (main_deg + vernier_div * least_count_deg) % 360


def angle_diff(a, b):
    """Smallest absolute angular difference (handles the 360/0 wrap)."""
    d = abs(a - b) % 360
    return min(d, 360 - d)


def refractive_index(prism_deg, dmin_deg):
    return math.sin(math.radians((prism_deg + dmin_deg) / 2)) / math.sin(math.radians(prism_deg / 2))


def dispersive_power(mu_short, mu_long, mu_mean):
    return (mu_short - mu_long) / (mu_mean - 1)


def cauchy_n(wl_nm, a=1.600, b=15000.0):
    return a + b / wl_nm ** 2


def min_deviation(prism_deg, n):
    A = math.radians(prism_deg)
    return math.degrees(2 * math.asin(n * math.sin(A / 2)) - A)


def cauchy_fit(wavelengths, mus):
    if len(wavelengths) < 2:
        return None
    x = 1 / np.square(np.asarray(wavelengths, float))
    B, A = np.polyfit(x, np.asarray(mus, float), 1)
    return A, B
