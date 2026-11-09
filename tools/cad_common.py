"""Shared source geometry and millimetre measurements for the current project."""
import os
from pathlib import Path
import sys

if os.environ.get('PATH_TO_FREECAD_LIBDIR'):
    sys.path.insert(0, os.environ['PATH_TO_FREECAD_LIBDIR'])
import FreeCAD as App
import Part

ROOT = Path(__file__).resolve().parents[1]
V = App.Vector


def bounds(shape):
    b = shape.BoundBox
    return [b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax]


def horizontal_faces(shape, min_area=0):
    return [f for f in shape.Faces if isinstance(f.Surface, Part.Plane)
            and f.BoundBox.ZLength < 1e-5 and f.Area > min_area]


def cat_shells():
    """Extract the two metal shells, turn upright, and set the underside at Z=0.

    The vendor STEP also contains PCB/electronics and detached components.
    Only the two largest solids are the upper/lower metal shells. Bounds and
    the lower face's 8 vents + 6 screw holes guard against a changed source.
    """
    imported = Part.read(str(ROOT/'models/LubanCat 5-外壳3D文件-20240911.STEP'))
    shells = [s.copy() for s in sorted(imported.Solids, key=lambda s: s.Volume, reverse=True)[:2]]
    for s in shells:
        s.rotate(V(), V(1, 0, 0), 90)
    floor = min(s.BoundBox.ZMin for s in shells)
    for s in shells:
        s.translate(V(0, 0, -floor))
    lower = min(shells, key=lambda s: s.BoundBox.ZMin)
    face = max([f for f in horizontal_faces(lower) if abs(f.CenterOfMass.z) < 1e-5], key=lambda f: f.Area)
    assert len(face.Wires) == 15
    assert abs(lower.BoundBox.XLength - 135.3256) < .01
    assert abs(lower.BoundBox.YLength - 80.5) < .01
    return shells, face
