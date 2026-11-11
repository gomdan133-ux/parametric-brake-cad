"""Parametric caliper mounting bracket (simplified, flat plate type).

All dimensions in millimeters.
"""
from __future__ import annotations

from dataclasses import dataclass

import cadquery as cq


@dataclass
class BracketSpec:
    length: float = 190.0          # overall length, across the rotor
    width: float = 45.0
    thickness: float = 16.0
    knuckle_hole_spacing: float = 100.0   # bolts to the steering knuckle
    knuckle_hole_d: float = 12.5          # clearance for M12
    caliper_hole_spacing: float = 150.0   # caliper slide pin bolts
    caliper_hole_d: float = 8.5           # tapped M10 shown as pilot size
    corner_r: float = 10.0
    edge_fillet: float = 1.5

    def check(self) -> None:
        if self.caliper_hole_spacing + self.caliper_hole_d >= self.length:
            raise ValueError("caliper holes too close to the ends")
        if self.knuckle_hole_spacing >= self.caliper_hole_spacing:
            raise ValueError("knuckle holes should sit inside the caliper holes")
        if self.corner_r * 2 >= self.width:
            raise ValueError("corner radius too large")


def build_bracket(spec: BracketSpec | None = None) -> cq.Workplane:
    s = spec or BracketSpec()
    s.check()
    plate = (cq.Workplane("XY").rect(s.length, s.width).extrude(s.thickness)
             .edges("|Z").fillet(s.corner_r))
    knuckle = [(-s.knuckle_hole_spacing / 2, 0), (s.knuckle_hole_spacing / 2, 0)]
    caliper = [(-s.caliper_hole_spacing / 2, 0), (s.caliper_hole_spacing / 2, 0)]
    plate = (plate.faces(">Z").workplane().pushPoints(knuckle).hole(s.knuckle_hole_d)
             .faces(">Z").workplane().pushPoints(caliper).hole(s.caliper_hole_d))
    # Lightening pocket between the knuckle holes
    pocket_len = s.knuckle_hole_spacing - 2 * s.knuckle_hole_d
    plate = (plate.faces(">Z").workplane().rect(pocket_len, s.width * 0.45)
             .cutBlind(-s.thickness / 2))
    return plate.edges(">Z or <Z").fillet(s.edge_fillet)
