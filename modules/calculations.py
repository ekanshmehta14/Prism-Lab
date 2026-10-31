import math
import numpy as np


def normalize_angle(angle):
    return float(angle) % 360.0


def angular_difference(a, b, signed=True):
    d = normalize_angle(a - b)
    if signed and d > 180:
        d -= 360
    return abs(d) if not signed else d


def convert_vernier_reading(main_scale, vernier_coincidence, least_count=1/60, calibration_offset=0.0):
    value = float(main_scale) + float(vernier_coincidence) * float(least_count) + float(calibration_offset)
    return normalize_angle(value)


def refractive_index(prism_angle, minimum_deviation):
    A, D = float(prism_angle), float(minimum_deviation)
    if not 0 < A < 180:
        raise ValueError("Prism angle must be between 0° and 180°.")
    if D < 0 or A + D >= 180:
        raise ValueError("Minimum deviation is physically invalid for the prism angle.")
    return math.sin(math.radians((A + D) / 2)) / math.sin(math.radians(A / 2))


def dispersive_power(mu_violet, mu_yellow, mu_red):
    mu = list(map(float, (mu_violet, mu_yellow, mu_red)))
    if any(x <= 1 for x in mu):
        raise ValueError("Refractive indices must be greater than 1.")
    return (mu[0] - mu[2]) / (mu[1] - 1)


def cauchy_prism_model(wavelength_nm, A=60.0, index_at_546=1.52, b=12000):
    # Explicit educational model: n(lambda)=n0+b/lambda^2 at the reference wavelength.
    n = index_at_546 + b * (1/(wavelength_nm*wavelength_nm) - 1/(546.1*546.1))
    D = 2 * math.degrees(math.asin(n * math.sin(math.radians(A/2)))) - A
    return n, D


def estimate_wavelength(calibration_points, measured_value, based_on="deviation"):
    if len(calibration_points) < 2:
        raise ValueError("At least two calibration points are required.")
    pts = sorted(calibration_points, key=lambda p: p[0])
    wavelengths = np.array([p[0] for p in pts], dtype=float)
    values = np.array([p[1] for p in pts], dtype=float)
    if based_on == "inverse_squared":
        x = 1/(wavelengths*wavelengths)
    else:
        x = wavelengths
    coeff = np.polyfit(x, values, min(2, len(pts)-1))
    poly = np.poly1d(coeff)
    measured = float(measured_value)
    roots = (np.polynomial.polynomial.polyroots([c for c in (np.poly1d(coeff).coef[::-1])]) if False else np.roots(coeff))
    # For inverse-square and angular/deviation calibration, interpolate linearly when no unique root is safely supported.
    if len(pts) >= 2:
        pairs = sorted(zip(values, wavelengths), key=lambda pair: pair[0])
        sorted_values = np.array([pair[0] for pair in pairs])
        sorted_wavelengths = np.array([pair[1] for pair in pairs])
        estimated = np.interp(measured, sorted_values, sorted_wavelengths)
    else:
        estimated = float(wavelengths[0])
    extrapolated = estimated < min(wavelengths) or estimated > max(wavelengths)
    residual = float(np.sqrt(np.mean((poly(x) - values)**2)))
    return float(estimated), bool(extrapolated), residual
