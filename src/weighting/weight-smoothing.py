'''
2024 Graphics Programming Final Project
Animating an object from single monocular video

name: weight-smoothing.py
description: processing graph-distance-filtering.py makes weight flow discrete due to clamping by graph distance.
             This script smooths those weights. It iteratively adjusts the weights of each vertex by averaging them with the weights 
             of neighboring vertices, creating a smoother transition between vertex weights. 

how to use:
    1. Open the Blender file.
    2. Open the Python Console in Blender.
    3. Load this script into the Python Console.
    4. Adjust the parameters:
        - `SMOOTHING_ITERATIONS`: Number of smoothing iterations (recommended 3)
        - `OBJECT_NAME`: Name of the mesh object to process.
    5. Run the script.
'''

import bpy
import bmesh
import time


SMOOTHING_ITERATIONS = 3  # Number of smoothing iterations
OBJECT_NAME = "" 

obj = bpy.data.objects.get(OBJECT_NAME)
if not obj:
    raise ValueError(f"Mesh object '{OBJECT_NAME}' not found!")

bpy.ops.object.mode_set(mode='OBJECT')

mesh = obj.data
bm = bmesh.new()
bm.from_mesh(mesh)

edges = {v.index: [] for v in mesh.vertices}
for edge in bm.edges:
    v1, v2 = edge.verts[0].index, edge.verts[1].index
    edges[v1].append(v2)
    edges[v2].append(v1)

print("Graph created for edge connections.")

# Smoothing function
def smooth_vertex_group_weights(vgroup, edges, iterations):
    for _ in range(iterations):
        # Store new weights temporarily
        new_weights = {vert.index: 0.0 for vert in mesh.vertices}
        for vert in mesh.vertices:
            weight = next((g.weight for g in vert.groups if g.group == vgroup.index), 0.0)
            neighbor_weights = [
                next((g.weight for g in mesh.vertices[neighbor].groups if g.group == vgroup.index), 0.0)
                for neighbor in edges[vert.index]
            ]
            
            if neighbor_weights:
                new_weights[vert.index] = (weight + sum(neighbor_weights)) / (1 + len(neighbor_weights))
            else:
                new_weights[vert.index] = weight
        
        for vert_index, smoothed_weight in new_weights.items():
            vgroup.add([vert_index], smoothed_weight, 'REPLACE')

start_time = time.time()
for vgroup in obj.vertex_groups:
    print(f"Smoothing vertex group: {vgroup.name}")
    smooth_vertex_group_weights(vgroup, edges, SMOOTHING_ITERATIONS)

elapsed = time.time() - start_time
print(f"Weight smoothing completed for all vertex groups. Total time: {elapsed:.2f}s")

bm.free()
mesh.update()