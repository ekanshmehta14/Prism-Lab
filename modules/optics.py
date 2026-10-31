import math
from modules.calculations import cauchy_prism_model


def symmetric_prism_deviation(prism_angle=60.0, refractive_index=1.52):
    if refractive_index <= 1 or not 0 < prism_angle < 180:
        raise ValueError("Invalid prism angle or refractive index")
    arg = refractive_index * math.sin(math.radians(prism_angle/2))
    if arg >= 1:
        raise ValueError("Prism configuration does not transmit this wavelength")
    return 2 * math.degrees(math.asin(arg)) - prism_angle


def line_target_angle(wavelength_nm, side="Right", order=1, prism_angle=60.0, offset=0.0):
    n, D = cauchy_prism_model(wavelength_nm, prism_angle)
    side_sign = 1 if side == "Right" else -1
    return (D * (1 + 0.18*(order-1)) * side_sign) + side_sign*offset


def snell_normal_incidence(n1, n2, incidence_deg):
    # n1 sin(i) = n2 sin(r)
    arg = n1 / n2 * math.sin(math.radians(incidence_deg))
    if abs(arg) > 1:
        raise ValueError("Total internal reflection or invalid ray direction")
    return math.degrees(math.asin(arg))
