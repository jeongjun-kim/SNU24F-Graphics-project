import bpy
import bmesh

def laplace_smooth(obj, iterations=1, lambda_factor=0.5):
    if obj.type != 'MESH':
        print(f"{obj.name} is not a mesh object!")
        return

    bm = bmesh.new()
    bm.from_mesh(obj.data)

    for _ in range(iterations):
        vertex_positions = {v: v.co.copy() for v in bm.verts}

        for v in bm.verts:
            if not v.is_boundary:  # Skip boundary vertices
                neighbors = [e.other_vert(v) for e in v.link_edges]
                avg_position = sum((vertex_positions[n] for n in neighbors), v.co) / (len(neighbors) + 1)
                v.co = (1 - lambda_factor) * v.co + lambda_factor * avg_position

    bm.to_mesh(obj.data)
    bm.free()
    print(f"Laplace smoothing applied to {obj.name} for {iterations} iterations.")

obj = bpy.context.active_object

if obj:
    laplace_smooth(obj, iterations=10, lambda_factor=0.5)
else:
    print("No active object selected!")
