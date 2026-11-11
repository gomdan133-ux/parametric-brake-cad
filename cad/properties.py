"""Mass properties from a CadQuery solid, like SOLIDWORKS Mass Properties."""
import cadquery as cq

DENSITY_KG_M3 = {
    "gray_cast_iron": 7200.0,
    "steel_1020": 7900.0,
    "aluminum_6061": 2700.0,
}


def mass_properties(part: cq.Workplane, material: str = "gray_cast_iron") -> dict:
    """Volume (mm^3), mass (kg) and center of mass (mm) of a solid."""
    if material not in DENSITY_KG_M3:
        raise ValueError(f"unknown material {material!r}")
    solid = part.val()
    vol_mm3 = solid.Volume()
    com = cq.Shape.centerOfMass(solid)
    mass = vol_mm3 * 1e-9 * DENSITY_KG_M3[material]
    bb = solid.BoundingBox()
    return {
        "volume_mm3": vol_mm3,
        "mass_kg": mass,
        "center_of_mass_mm": (com.x, com.y, com.z),
        "bounding_box_mm": (bb.xlen, bb.ylen, bb.zlen),
        "material": material,
    }
