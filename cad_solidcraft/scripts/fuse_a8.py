import build123d as bd
from build123d import import_step
sh = import_step(r"E:\car_projects\cad_solidcraft\exports\battery_cradle_a8.step")
solids = list(sh.solids())
fused = solids[0].fuse(*solids[1:])
out = bd.Compound([fused])
out.label = "battery_cradle_a8"
out.color = "#d9822b"
bd.export_step(out, r"E:\car_projects\cad_solidcraft\exports\battery_cradle_a8.step")
print("fused solids:", len(fused.solids()), "vol:", round(fused.volume))
