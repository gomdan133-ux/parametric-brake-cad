"""Build every model and export STEP, STL, SVG drawings, PNG renders and a mass report.

Run from the repo root:  python scripts/build_all.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import cadquery as cq  # noqa: E402
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # noqa: E402

from cad import (BracketSpec, RotorSpec, build_bracket, build_rotor,  # noqa: E402
                 mass_properties)

OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)


def render_png(part, path, elev=35, azim=-60, base=(0.62, 0.66, 0.70)):
    import numpy as np
    verts, tris = part.val().tessellate(0.2, 0.15)
    pts = np.array([(v.x, v.y, v.z) for v in verts])
    tri = np.array(tris)
    faces = pts[tri]
    # Simple diffuse shading from a light above and to the side of the viewer
    n = np.cross(faces[:, 1] - faces[:, 0], faces[:, 2] - faces[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    light = np.array([0.4, -0.6, 0.7])
    light /= np.linalg.norm(light)
    shade = 0.35 + 0.65 * np.abs(n @ light)
    colors = np.clip(np.outer(shade, base), 0, 1)
    fig = plt.figure(figsize=(6, 5), dpi=150)
    ax = fig.add_subplot(111, projection="3d")
    ax.add_collection3d(Poly3DCollection(faces, facecolors=colors, edgecolor="none"))
    pts = [tuple(p) for p in pts]
    xs, ys, zs = zip(*pts)
    span = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)) / 2
    cx, cy, cz = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2, (max(zs) + min(zs)) / 2
    ax.set_xlim(cx - span, cx + span)
    ax.set_ylim(cy - span, cy + span)
    ax.set_zlim(cz - span, cz + span)
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(path, transparent=False, facecolor="white")
    plt.close(fig)


def export_all(name, part, material, drawing_dir):
    cq.exporters.export(part, str(OUT / f"{name}.step"))
    cq.exporters.export(part, str(OUT / f"{name}.stl"), tolerance=0.1, angularTolerance=0.2)
    # Orthographic drawing views with hidden lines
    for view, d in {"top": (0, 0, 1), "front": (0, -1, 0), "iso": (1, -1, 1)}.items():
        cq.exporters.export(part, str(OUT / f"{name}_{view}.svg"), opt={
            "projectionDir": d, "showHidden": True, "width": 600, "height": 450,
            "marginLeft": 20, "marginTop": 20, "strokeWidth": 0.4})
    render_png(part, OUT / f"{name}.png")
    props = mass_properties(part, material)
    return props


def main():
    rs, bs = RotorSpec(), BracketSpec()
    report = {
        "rotor": {"spec": rs.__dict__, **export_all("rotor", build_rotor(rs), "gray_cast_iron", OUT)},
        "bracket": {"spec": bs.__dict__, **export_all("bracket", build_bracket(bs), "steel_1020", OUT)},
    }
    # Design study: rotor mass vs friction plate thickness
    study = []
    for t in (7.0, 8.0, 9.0, 10.0, 11.0):
        s = RotorSpec(plate_t=t)
        study.append({"plate_t_mm": t, "mass_kg": round(mass_properties(build_rotor(s))["mass_kg"], 2)})
    report["rotor_plate_thickness_study"] = study
    (OUT / "mass_report.json").write_text(json.dumps(report, indent=2))
    for k in ("rotor", "bracket"):
        p = report[k]
        print(f"{k:8s} {p['material']:15s} mass {p['mass_kg']:.2f} kg  "
              f"volume {p['volume_mm3'] / 1000:.0f} cm^3  "
              f"COM z {p['center_of_mass_mm'][2]:.1f} mm  bbox {tuple(round(x, 1) for x in p['bounding_box_mm'])}")
    print("plate thickness study:", ", ".join(f"{r['plate_t_mm']:.0f} mm -> {r['mass_kg']} kg" for r in study))


if __name__ == "__main__":
    main()
