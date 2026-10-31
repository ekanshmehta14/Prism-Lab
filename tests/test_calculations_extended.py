import pytest
from modules.calculations import estimate_wavelength


def test_calibration_interpolation():
    wavelength, extrapolated, residual=estimate_wavelength([(404.7,44),(546.1,38),(579.1,37)],40)
    assert 404.7 <= wavelength <= 579.1
    assert extrapolated is False


def test_calibration_requires_points():
    with pytest.raises(ValueError): estimate_wavelength([(546.1,38)],38)
