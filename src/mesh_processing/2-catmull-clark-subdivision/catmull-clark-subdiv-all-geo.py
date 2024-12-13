'''
2024 Graphics Programming Final Project
Animating an object from single monocular video

name: catmull-clark-subdiv-all-geo.py
description: Subdivides all faces of a mesh using the Catmull-Clark algorithm (geometry only).

how to use:
    1. Open Blender file
    2. Open the Python Console
    3. Open the script file on the Python Console
    4. Select the object you want to subdivide
    5. Run the script
'''

import bpy
import bmesh
from mathutils import Vector

def is_hole_edge(edge_faces):
    return len(edge_faces) == 1

def is_hole_vertex(num_edges, num_faces):
    return num_edges != num_faces

obj = bpy.context.active_object
if obj is None or obj.type != 'MESH':
    raise ValueError("Active object must be a mesh")

# Ensure we start in Object Mode
bpy.ops.object.mode_set(mode='OBJECT')

mesh = obj.data

bm = bmesh.new()
bm.from_mesh(mesh)
bm.verts.ensure_lookup_table()
bm.edges.ensure_lookup_table()
bm.faces.ensure_lookup_table()

# Store original vertex coordinates
original_vert_coords = [v.co.copy() for v in bm.verts]

# Build face list
original_faces_indices = []
for f in bm.faces:
    face_vert_indices = [v.index for v in f.verts]
    original_faces_indices.append(face_vert_indices)

# Build adjacency maps
vert_faces_map = [[] for _ in bm.verts]
for f_i, f_verts in enumerate(original_faces_indices):
    for vi in f_verts:
        vert_faces_map[vi].append(f_i)

# Build edges and their face connectivity
edge_lookup = {}
for f_i, f_verts in enumerate(original_faces_indices):
    f_len = len(f_verts)
    for i in range(f_len):
        v1_i = f_verts[i]
        v2_i = f_verts[(i+1)%f_len]
        key = frozenset((v1_i, v2_i))
        if key not in edge_lookup:
            edge_lookup[key] = []
        edge_lookup[key].append(f_i)

unique_edges = list(edge_lookup.items()) # [(frozenset({v1,v2}), [face_i, ...]), ...]
original_edges_data = []
edge_of_vertex = [[] for _ in bm.verts]
for ei, (vs, fs) in enumerate(unique_edges):
    verts_list = list(vs)
    v1_i, v2_i = verts_list
    original_edges_data.append((v1_i, v2_i, fs))
    edge_of_vertex[v1_i].append(ei)
    edge_of_vertex[v2_i].append(ei)

vert_edges_map = edge_of_vertex

bm.clear()  # We'll rebuild from scratch

def midpoint(co1, co2):
    return (co1 + co2) / 2.0

# Compute face points
face_points = []
for f_i, f_verts in enumerate(original_faces_indices):
    coords = [original_vert_coords[vi] for vi in f_verts]
    fp = sum(coords, Vector()) / len(coords)
    face_points.append(fp)

# Compute edge points
edge_points = []
for (v1_i, v2_i, f_list) in original_edges_data:
    v1_co = original_vert_coords[v1_i]
    v2_co = original_vert_coords[v2_i]

    if is_hole_edge(f_list):
        ep = midpoint(v1_co, v2_co)
    else:
        if len(f_list) == 2:
            F1, F2 = f_list
            ep = (v1_co + v2_co + face_points[F1] + face_points[F2]) / 4.0
        elif len(f_list) == 1:
            F = f_list[0]
            ep = (v1_co + v2_co + face_points[F]) / 3.0
        else:
            ep = midpoint(v1_co, v2_co)

    edge_points.append(ep)

# Compute new vertex positions
new_vertex_positions = []
for vi, P in enumerate(original_vert_coords):
    adj_faces = vert_faces_map[vi]
    adj_edges = vert_edges_map[vi]
    n = len(adj_faces)

    if is_hole_vertex(len(adj_edges), len(adj_faces)):
        # Hole vertex
        avg_midpoints = Vector((0,0,0))
        hole_edge_count = 0
        for ei in adj_edges:
            v1_i, v2_i, f_list = original_edges_data[ei]
            if is_hole_edge(f_list):
                m = midpoint(original_vert_coords[v1_i], original_vert_coords[v2_i])
                avg_midpoints += m
                hole_edge_count += 1
        if hole_edge_count > 0:
            V_new = (avg_midpoints + P)/(hole_edge_count+1)
        else:
            V_new = P
    else:
        # Normal vertex
        if n == 0:
            # Isolated vertex
            V_new = P
        else:
            F_avg = sum((face_points[fi] for fi in adj_faces), Vector())/n
            edge_midpoints = []
            for ei in adj_edges:
                v1_i, v2_i, _ = original_edges_data[ei]
                edge_midpoints.append(midpoint(original_vert_coords[v1_i], original_vert_coords[v2_i]))
            R_avg = sum(edge_midpoints, Vector())/len(edge_midpoints)
            V_new = (F_avg + 2*R_avg + (n-3)*P)/n

    new_vertex_positions.append(V_new)

# Rebuild the mesh
bm = bmesh.new()

v_bm_verts = [bm.verts.new(co) for co in new_vertex_positions]
f_bm_verts = [bm.verts.new(fp) for fp in face_points]
e_bm_verts = [bm.verts.new(ep) for ep in edge_points]

bm.verts.index_update()

edge_map = {}
for ei, (v1_i, v2_i, f_list) in enumerate(original_edges_data):
    edge_map[frozenset({v1_i,v2_i})] = ei

# Create new faces
for fi, face_verts in enumerate(original_faces_indices):
    Fv = f_bm_verts[fi]
    f_len = len(face_verts)
    for i in range(f_len):
        v_curr_i = face_verts[i]
        v_next_i = face_verts[(i+1)%f_len]
        v_prev_i = face_verts[(i-1)%f_len]

        ei_current = edge_map[frozenset({v_curr_i, v_next_i})]
        ei_prev = edge_map[frozenset({v_prev_i, v_curr_i})]

        V_i = v_bm_verts[v_curr_i]
        EP_current = e_bm_verts[ei_current]
        EP_prev = e_bm_verts[ei_prev]

        bm.faces.new([V_i, EP_current, Fv, EP_prev])

bm.faces.index_update()
bm.verts.index_update()

# Write mesh back
new_mesh = bpy.data.meshes.new("SubdividedMesh")
bm.to_mesh(new_mesh)
new_mesh.update()
bm.free()

# Assign the new mesh to the object
obj.data = new_mesh

# Switch to Edit Mode to see the result
bpy.ops.object.mode_set(mode='EDIT')

print("Catmull-Clark subdivision complete (geometry only)")
