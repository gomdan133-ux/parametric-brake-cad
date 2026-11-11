"""Parametric vented brake rotor.

All dimensions in millimeters. Change RotorSpec values to model a different rotor.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import cadquery as cq


@dataclass
class RotorSpec:
    outer_d: float = 300.0          # rotor outside diameter
    friction_inner_d: float = 180.0 # inside diameter of the friction ring
    plate_t: float = 9.0            # thickness of each friction plate
    vane_gap: float = 10.0          # air gap between plates (vane height)
    vane_count: int = 36            # straight radial cooling vanes
    vane_t: float = 4.0             # vane width
    hat_d: float = 165.0            # outside diameter of the hat
    hat_height: float = 45.0        # hat height above the friction ring
    hat_wall: float = 6.0
    hub_face_t: float = 8.0         # thickness of the mounting face
    center_bore_d: float = 64.1     # hub pilot bore
    lug_count: int = 5
    lug_pcd: float = 114.3          # bolt circle diameter (5 x 114.3)
    lug_hole_d: float = 14.0

    @property
    def total_t(self) -> float:
        return 2 * self.plate_t + self.vane_gap

    def check(self) -> None:
        if not self.center_bore_d < self.lug_pcd - self.lug_hole_d:
            raise ValueError("lug holes overlap the center bore")
        if not self.lug_pcd + self.lug_hole_d < self.hat_d - 2 * self.hat_wall:
            raise ValueError("lug holes do not fit inside the hat")
        if not self.hat_d < self.friction_inner_d < self.outer_d:
            raise ValueError("diameters must go hat < friction inner < outer")
        if self.vane_count < 3 or self.vane_t <= 0:
            raise ValueError("need at least 3 vanes with positive width")


def build_rotor(spec: RotorSpec | None = None) -> cq.Workplane:
    """Build the rotor solid. Friction ring sits on Z=0, hat rises in +Z."""
    s = spec or RotorSpec()
    s.check()
    ro, ri = s.outer_d / 2, s.friction_inner_d / 2

    # Two friction plates
    inboard = cq.Workplane("XY").circle(ro).circle(ri).extrude(s.plate_t)
    outboard = (cq.Workplane("XY").workplane(offset=s.plate_t + s.vane_gap)
                .circle(ro).circle(ri).extrude(s.plate_t))
    rotor = inboard.union(outboard)

    # Radial vanes between the plates
    vane_len = ro - ri
    for i in range(s.vane_count):
        ang = 360.0 * i / s.vane_count
        vane = (cq.Workplane("XY").workplane(offset=s.plate_t)
                .center((ri + ro) / 2, 0).rect(vane_len, s.vane_t).extrude(s.vane_gap)
                .rotate((0, 0, 0), (0, 0, 1), ang))
        rotor = rotor.union(vane)

    # Hat: connects outboard plate inner edge up to the mounting face
    z_top = s.total_t
    hat_wall = (cq.Workplane("XY").workplane(offset=z_top - s.plate_t)
                .circle(ri).circle(s.hat_d / 2 - s.hat_wall).extrude(s.plate_t))
    hat_cyl = (cq.Workplane("XY").workplane(offset=z_top)
               .circle(s.hat_d / 2).circle(s.hat_d / 2 - s.hat_wall)
               .extrude(s.hat_height - s.hub_face_t))
    hub_face = (cq.Workplane("XY").workplane(offset=z_top + s.hat_height - s.hub_face_t)
                .circle(s.hat_d / 2).extrude(s.hub_face_t))
    rotor = rotor.union(hat_wall).union(hat_cyl).union(hub_face)

    # Center bore and lug holes through the mounting face
    pts = [(s.lug_pcd / 2 * math.cos(2 * math.pi * k / s.lug_count),
            s.lug_pcd / 2 * math.sin(2 * math.pi * k / s.lug_count)) for k in range(s.lug_count)]
    cutter = (cq.Workplane("XY").workplane(offset=z_top + s.hat_height - s.hub_face_t - 1)
              .circle(s.center_bore_d / 2).extrude(s.hub_face_t + 2))
    holes = (cq.Workplane("XY").workplane(offset=z_top + s.hat_height - s.hub_face_t - 1)
             .pushPoints(pts).circle(s.lug_hole_d / 2).extrude(s.hub_face_t + 2))
    return rotor.cut(cutter).cut(holes)
