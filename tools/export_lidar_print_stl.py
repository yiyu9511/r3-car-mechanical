"""Export compact binary STL and verify four assembly rods are one printable part."""
import json, math, struct
from cad_common import Part, ROOT, V
import Mesh, MeshPart

B = ROOT / 'cad_solidcraft'
spec = json.loads((B / 'checks/lidar_cable_rods_spec.json').read_text())
rods = []
for entry in spec['rods']:
    shape = Part.read(str(B / 'review' / (entry['name'] + '.step')))
    shape.translate(-V(*entry['head_base']))
    shape.rotate(V(), V(0, 0, 1), math.degrees(math.atan2(entry['axis'][0], entry['axis'][1])))
    rods.append(shape)
differences = [rods[0].cut(s).Volume + s.cut(rods[0]).Volume for s in rods]
assert max(differences) < .001, differences
# Stop head on Z=0; this is an initial orientation, not a slicing approval.
rod = rods[0].copy()
rod.rotate(V(), V(1, 0, 0), 90)
rod.translate(V(0, 0, -rod.optimalBoundingBox().ZMin))
report = {'rod_symmetric_difference_mm3': differences, 'parts': {},
          'limitations': ['Rod orientation is initial only; slicing and physical fit not verified',
                          'Nominal neighboring screw-head relief has no added fit allowance']}
for name, shape, count in [
    ('lidar_frame_flat', Part.read(str(B / 'review/lidar_frame_flat_print.step')), 1),
    ('lidar_locator_sleeve', Part.read(str(B / 'review/lidar_locator_sleeve_print.step')), 2),
    ('lidar_cable_rod', rod, 4),
]:
    assert shape.isValid() and len(shape.Solids) == 1
    mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=.005 if name == "lidar_cable_rod" else .03, AngularDeflection=.10 if name == "lidar_cable_rod" else .15)
    path = B / 'exports' / (name + '.stl')
    with path.open('wb') as out:
        out.write(b'R3 LiDAR binary STL; units mm'.ljust(80, b' '))
        out.write(struct.pack('<I', mesh.CountFacets))
        for facet in mesh.Facets:
            values = list(facet.Normal)
            for point in facet.Points:
                values.extend(point)
            out.write(struct.pack('<12fH', *values, 0))
    read = Mesh.Mesh(str(path))
    error = abs(abs(read.Volume) - shape.Volume) / shape.Volume
    assert read.isSolid() and error < .003, (name, read.isSolid(), error, mesh.isSolid(), mesh.Volume, shape.Volume)
    assert abs(read.BoundBox.ZMin) < .001
    report['parts'][name] = {'quantity': count, 'bytes': path.stat().st_size,
                           'triangles': read.CountFacets, 'closed': read.isSolid(),
                           'relative_volume_error': error}
(B / 'checks/lidar_print_stl.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
