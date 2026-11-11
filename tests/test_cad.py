import pytest

from cad import BracketSpec, RotorSpec, build_bracket, build_rotor, mass_properties


@pytest.fixture(scope="module")
def rotor():
    return build_rotor()


def test_rotor_is_one_valid_solid(rotor):
    assert rotor.val().isValid()
    assert len(rotor.solids().vals()) == 1


def test_rotor_size(rotor):
    s = RotorSpec()
    bb = rotor.val().BoundingBox()
    assert bb.xlen == pytest.approx(s.outer_d, abs=0.5)
    assert bb.zlen == pytest.approx(s.total_t + s.hat_height, abs=0.5)


def test_rotor_mass_is_realistic(rotor):
    # A 300 mm vented cast iron rotor typically weighs about 7 to 11 kg
    m = mass_properties(rotor)["mass_kg"]
    assert 7.0 < m < 11.0


def test_rotor_is_balanced(rotor):
    x, y, _ = mass_properties(rotor)["center_of_mass_mm"]
    assert abs(x) < 0.01 and abs(y) < 0.01


def test_thicker_plates_add_mass():
    thin = mass_properties(build_rotor(RotorSpec(plate_t=8)))["mass_kg"]
    thick = mass_properties(build_rotor(RotorSpec(plate_t=10)))["mass_kg"]
    assert thick > thin


def test_aluminum_lighter_than_iron(rotor):
    assert (mass_properties(rotor, "aluminum_6061")["mass_kg"]
            < mass_properties(rotor, "gray_cast_iron")["mass_kg"])


def test_bracket_valid_and_mass():
    b = build_bracket()
    assert b.val().isValid()
    m = mass_properties(b, "steel_1020")["mass_kg"]
    assert 0.5 < m < 1.5


@pytest.mark.parametrize("spec", [
    RotorSpec(lug_pcd=60),                 # lug holes hit the center bore
    RotorSpec(hat_d=200),                  # hat bigger than the friction ring
    RotorSpec(vane_count=2),
])
def test_bad_rotor_specs_rejected(spec):
    with pytest.raises(ValueError):
        build_rotor(spec)


def test_bad_bracket_spec_rejected():
    with pytest.raises(ValueError):
        build_bracket(BracketSpec(caliper_hole_spacing=200))


def test_unknown_material(rotor):
    with pytest.raises(ValueError):
        mass_properties(rotor, "unobtainium")
