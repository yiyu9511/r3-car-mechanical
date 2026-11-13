"""Derive the open wiring review frame from the source native frame."""
from pathlib import Path
from sc_mcp import Client

root=Path(__file__).resolve().parents[2]
with Client(root) as client:
    if client.call('inspect_design',{'measure':False,'sketches':False}).get('dirty'):
        raise RuntimeError('Save the open design before rebuilding the frame.')
    client.call('open',{'path':str(root/'cad_solidcraft/lidar_frame.sc')})
    state=client.call('inspect_design',{'measure':False,'sketches':False})
    prefixes=('Elevated side tie','Integral U rim','Continuous U front corner','Rectangular keyed interface slot','M3 anti-lift bolt access below slots')
    client.execute('timeline.delete',features=[item['id'] for item in state['timeline'] if item['name'].startswith(prefixes)])
    client.call('save',{'path':str(root/'cad_solidcraft/lidar_frame_open.sc')})
    client.call('export',{'path':str(root/'cad_solidcraft/review/lidar_frame_open.step'),'bodies':['LidarFrame']})
