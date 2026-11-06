"""Anchor-hole candidate analysis: extract every steel-plate hole and match
the three adapter footprints against it. Decision-support only; no hole is
confirmed usable until the user approves it."""
import io
import json
import math
import os
import sys
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from cad_common import App, Part, ROOT, V, battery_cradle, bounds

OUT = ROOT / 'output/two_layer'


def global_shape(obj):
    s = obj.Shape.copy()
    s.Placement = obj.getGlobalPlacement().multiply(obj.Placement.inverse()).multiply(s.Placement)
    return s


baseline = App.openDocument(str(ROOT / 'assemblies/c30d_on_chassis.FCStd'))
chassis = global_shape(baseline.getObject('Chassis_R3mini'))
App.closeDocument(baseline.Name)
steel = max([s for s in chassis.Solids if s.BoundBox.ZLength < 2], key=lambda s: s.Volume).copy()

# --- full hole inventory of the steel plate -------------------------------
holes = {}
for f in steel.Faces:
    if isinstance(f.Surface, Part.Cylinder) and abs(f.Surface.Axis.z) > .999:
        c = f.Surface.Center
        key = (round(c.x, 4), round(c.y, 4), round(f.Surface.Radius, 4))
        if key not in holes or f.Area > holes[key]['area']:
            holes[key] = {'x': c.x, 'y': c.y, 'r': f.Surface.Radius, 'area': f.Area,
                          'zmin': f.BoundBox.ZMin, 'zmax': f.BoundBox.ZMax}
hole_list = [{'x': h['x'], 'y': h['y'], 'd': round(2 * h['r'], 3),
              'through': abs(h['zmax'] - h['zmin'] - steel.BoundBox.ZLength) < 1e-3}
             for h in holes.values()]
hole_list.sort(key=lambda h: (h['y'], h['x']))

# --- battery cradle: extract its own Ø3.4 holes and map to global ---------
cradle = battery_cradle()
bholes = {}
for f in cradle.Faces:
    if isinstance(f.Surface, Part.Cylinder) and abs(f.Surface.Axis.z) > .999:
        c = f.Surface.Center
        bholes[(round(c.x, 3), round(c.y, 3))] = (c.x, c.y, f.Surface.Radius)
# group placement: Rz90 then translate (0,-84,1.5) -> local (x,y)->(-y,x)
battery_holes_global = []
for (lx, ly), (cx, cy, r) in sorted(bholes.items()):
    gx, gy = -cy, cx
    battery_holes_global.append({'local': [cx, cy], 'global': [round(gx, 3), round(gy, 3)],
                                 'd': round(2 * r, 3)})
gx = [p['global'] for p in battery_holes_global]
battery_pitch = {'x': round(max(p[0] for p in gx) - min(p[0] for p in gx), 3),
                 'y': round(max(p[1] for p in gx) - min(p[1] for p in gx), 3)}


def nearest_holes(pts, limit=6.0):
    out = []
    for p in pts:
        cands = sorted(hole_list, key=lambda h: math.hypot(h['x'] - p[0], h['y'] - p[1]))[:3]
        best = [{'d': round(math.hypot(h['x'] - p[0], h['y'] - p[1]), 3), 'hole': h} for h in cands]
        out.append({'point': list(p), 'nearest': best})
    return out


# --- CAT feet: group base y=-50; local foot centers (±56, ±30) ------------
cat_feet = [(sx * 56, sy * 30 + (-50)) for sx in (-1, 1) for sy in (-1, 1)]
# --- lidar mount feet: group base y=55; local (±26, ±28) ------------------
lidar_feet = [(x, y + 55) for x in (-26, 26) for y in (-28, 28)]
# --- camera mount base: local y in [-14,0], x in [-22,22], group y=104 ----
camera_zone_center = [(x, 97) for x in (-15, 0, 15)]

report = {
    'status': 'decision_support_only_no_hole_confirmed',
    'plate_hole_count': len(hole_list),
    'plate_holes': hole_list,
    'battery_cradle_holes_global': {'holes': battery_holes_global, 'pitch_mm': battery_pitch,
                                    'note': 'cradle rotated 90 deg, long side along X; original Ø3.4 kept',
                                    'nearest_plate_holes': nearest_holes(gx)},
    'cat_feet_centers_global': {'points': cat_feet, 'foot_d_mm': 10,
                                'nearest_plate_holes': nearest_holes(cat_feet)},
    'lidar_foot_centers_global': {'points': lidar_feet, 'foot_d_mm': 10,
                                  'nearest_plate_holes': nearest_holes(lidar_feet)},
    'camera_base_probe_points_global': {'points': camera_zone_center,
                                        'nearest_plate_holes': nearest_holes(camera_zone_center)},
    'nut_space_note': 'plate is 1.5 mm; any screw needs a nut or standoff on the far side; '
                      'for the lower plate that means protrusion below z=0 (ground side), '
                      'for the upper plate into the layer-1 space above C30D/battery.',
}
with open(OUT / 'anchor_candidates.json', 'w', encoding='utf-8') as fh:
    fh.write(json.dumps(report, ensure_ascii=False, indent=2))
print(json.dumps({'plate_hole_count': len(hole_list),
                  'battery_pitch': battery_pitch,
                  'battery_global_holes': gx,
                  'cat_nearest': [[n['nearest'][0]['d'], n['nearest'][0]['hole']['d']]
                                  for n in report['cat_feet_centers_global']['nearest_plate_holes']],
                  'lidar_nearest': [[n['nearest'][0]['d'], n['nearest'][0]['hole']['d']]
                                    for n in report['lidar_foot_centers_global']['nearest_plate_holes']],
                  'camera_nearest': [[n['nearest'][0]['d'], n['nearest'][0]['hole']['d']]
                                     for n in report['camera_base_probe_points_global']['nearest_plate_holes']]},
                 ensure_ascii=False, indent=1), flush=True)
