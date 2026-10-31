import pytest
from modules.calculations import normalize_angle, angular_difference, convert_vernier_reading, refractive_index, dispersive_power
from modules.observations import validate_observation
from modules.optics import snell_normal_incidence


def test_prism_refractive_index():
    mu=refractive_index(60,38)
    assert abs(mu-1.5096)<0.01


def test_invalid_prism_angle():
    with pytest.raises(ValueError): refractive_index(181,30)


def test_wraparound():
    assert normalize_angle(361)==1
    assert angular_difference(359,1)==-2


def test_vernier_reading():
    assert abs(convert_vernier_reading(30,12,1/60)-30.2)<0.001


def test_dispersive_power():
    assert dispersive_power(1.53,1.52,1.51)>0


def test_second_order_allowed_only():
    assert validate_observation({"side":"Left","order":1,"spectral_colour":"Green"})
    assert validate_observation({"side":"Right","order":2,"spectral_line":"Green"})
    with pytest.raises(ValueError): validate_observation({"side":"Left","order":3,"spectral_line":"Green"})


def test_snell_normal_incidence():
    assert abs(snell_normal_incidence(1,1.5,30)-19.471)<0.01
