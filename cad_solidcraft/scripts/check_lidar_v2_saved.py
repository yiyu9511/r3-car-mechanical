"""Read saved V2 native models in isolation without changing the visible UI."""
import json,os
from pathlib import Path
from sc_mcp import Client
R=Path(__file__).resolve().parents[2]
os.environ.pop('SOLIDCRAFT_CONNECT',None)
os.environ['SOLIDCRAFT_HEADLESS']='1'
report={}
with Client(R,timeout=300) as c:
    for name in ['lidar_cable_rods','lidar_print_layout']:
        c.call('open',{'path':str(R/f'cad_solidcraft/{name}.sc')})
        state=c.call('inspect_design',{'measure':False,'sketches':False})
        errors=[f['name'] for f in state['timeline'] if f.get('error')]
        report[name]={'body_count':len(state['bodies']),'errors':errors}
        assert len(state['bodies'])==7 and not errors
report['lidar_print_layout']['purpose']='Separate frame, two sleeves, four rods; rod orientation for viewing only'
(R/'cad_solidcraft/checks/lidar_cable_rods_saved.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
