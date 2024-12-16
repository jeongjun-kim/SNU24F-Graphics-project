'''
2024 Graphics Programming Final Project
Animating an object from single monocular video

name: graph-distance-filtering.py
description: Filters vertices in each bone's vertex group based on graph distance to the highest-weight vertex.
Vertices that exceed a specified edge distance threshold from the highest-weight vertex will have their weight set to 0.

how to use:
    1. Open the Blender file.
    2. Open the Python Console in Blender.
    3. Load this script into the Python Console.
    4. Adjust the parameters:
        - `EDGE_THRESHOLD`: Maximum allowed edge distance from the highest-weight vertex.
        - `OBJECT_NAME`: Name of the mesh object to process.
    5. Run the script.
'''

import bpy
import bmesh
from mathutils import Vector
import time

EDGE_THRESHOLD = 100 
OBJECT_NAME = "standup" 

obj = bpy.data.objects.get(OBJECT_NAME)
if not obj:
    raise ValueError(f"Mesh object '{OBJECT_NAME}' not found!")

bpy.ops.object.mode_set(mode='OBJECT')

# Access the mesh data
mesh = obj.data
bm = bmesh.new()
bm.from_mesh(mesh)

# Create graph representation of mesh edges
edges = {v.index: [] for v in mesh.vertices}
for edge in bm.edges:
    v1, v2 = edge.verts[0].index, edge.verts[1].index
    edges[v1].append(v2)
    edges[v2].append(v1)

print("Graph created for edge connections.")

# BFS for shortest edge distance
def calculate_distances_from_vertex(start_vertex):
    """Returns a dictionary of shortest distances from start_vertex to all other vertices."""
    visited = set()
    queue = [(start_vertex, 0)]
    distances = {start_vertex: 0}

    while queue:
        current, distance = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)

        for neighbor in edges[current]:
            if neighbor not in distances:
                distances[neighbor] = distance + 1
                queue.append((neighbor, distance + 1))
    
    return distances

# Process a single vertex group
def process_vertex_group(vgroup):
    start_time = time.time()
    print(f"Processing vertex group: {vgroup.name}")

    # Extract weights for all vertices in the vertex group
    weights = []
    for vert in mesh.vertices:
        weight = next((g.weight for g in vert.groups if g.group == vgroup.index), 0.0)
        if weight > 0:
            weights.append((vert.index, weight))

    if not weights:
        print(f"  - No vertices with weight > 0 in group '{vgroup.name}'.")
        return

    # Find the vertex with the highest weight
    weights.sort(key=lambda x: x[1], reverse=True)
    highest_weight_vertex = weights[0][0]  # Index of the vertex with the highest weight
    print(f"  - Highest weight vertex: {highest_weight_vertex}")

    # Calculate distances from the highest weight vertex
    distances = calculate_distances_from_vertex(highest_weight_vertex)

    # Filter vertices based on distance
    filtered_count = 0
    for vert_index, weight in weights:
        if distances.get(vert_index, float('inf')) > EDGE_THRESHOLD:
            vgroup.add([vert_index], 0.0, 'REPLACE')
            filtered_count += 1

    elapsed = time.time() - start_time
    print(f"Vertex group '{vgroup.name}' processed. Filtered {filtered_count} vertices. Time: {elapsed:.2f}s")

# Process all vertex groups
start_time = time.time()
for vgroup in obj.vertex_groups:
    process_vertex_group(vgroup)

elapsed = time.time() - start_time
print(f"Weight filtering completed for all vertex groups. Total time: {elapsed:.2f}s")

bm.free()
mesh.update()
