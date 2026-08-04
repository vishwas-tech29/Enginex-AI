import os
import tempfile

import cadquery as cq
from cadquery import exporters


def _shape_of(workplane_or_shape: "cq.Workplane | cq.Shape") -> cq.Shape:
    return workplane_or_shape.val() if isinstance(workplane_or_shape, cq.Workplane) else workplane_or_shape


def export_step(workplane: cq.Workplane) -> bytes:
    """Real ISO 10303-21 STEP export via OCCT — not a hand-written string
    template, so it's valid enough for other real CAD tools to open."""
    with tempfile.NamedTemporaryFile(suffix=".step", delete=False) as tmp:
        path = tmp.name
    try:
        exporters.export(workplane, path, exportType="STEP")
        with open(path, "rb") as f:
            return f.read()
    finally:
        os.unlink(path)


def export_stl(workplane: cq.Workplane, binary: bool = True, tolerance: float = 0.1) -> bytes:
    suffix = ".stl"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        path = tmp.name
    try:
        exporters.export(
            workplane, path, exportType="STL", tolerance=tolerance,
            opt={"ascii": not binary},
        )
        mode = "rb" if binary else "r"
        with open(path, mode) as f:
            content = f.read()
        return content if binary else content.encode("utf-8")
    finally:
        os.unlink(path)


def export_obj(workplane: cq.Workplane, tolerance: float = 0.1) -> str:
    """CadQuery has no built-in OBJ writer, so this walks the same real
    tessellation used for STL/mesh (`Shape.tessellate`) and writes vertices
    + faces by hand — the geometry is real, only the file writer is ours."""
    shape = _shape_of(workplane)
    vertices, triangles = shape.tessellate(tolerance)

    lines = ["# Exported from Enginex AI CAD engine (app/cad/export/exporters.py)"]
    for v in vertices:
        lines.append(f"v {v.x:.6f} {v.y:.6f} {v.z:.6f}")
    for tri in triangles:
        lines.append(f"f {tri[0] + 1} {tri[1] + 1} {tri[2] + 1}")  # OBJ is 1-indexed
    return "\n".join(lines) + "\n"


def get_mesh(workplane: cq.Workplane, tolerance: float = 0.1) -> dict:
    """Triangle mesh for the frontend 3D viewport: real OCCT tessellation,
    not a placeholder cube."""
    shape = _shape_of(workplane)
    vertices, triangles = shape.tessellate(tolerance)
    bbox = shape.BoundingBox()
    return {
        "vertices": [[v.x, v.y, v.z] for v in vertices],
        "triangles": [list(t) for t in triangles],
        "bounding_box": {
            "min": [bbox.xmin, bbox.ymin, bbox.zmin],
            "max": [bbox.xmax, bbox.ymax, bbox.zmax],
        },
        "volume": shape.Volume(),
        "surface_area": shape.Area(),
    }
