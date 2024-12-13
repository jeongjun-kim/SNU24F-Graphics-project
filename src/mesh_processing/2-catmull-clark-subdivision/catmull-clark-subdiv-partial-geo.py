'''
2024 Graphics Programming Final Project
Animating an object from single monocular video

name: catmull-clark-subdiv-partial-geo.py
description: Subdivides selected faces of a mesh using the Catmull-Clark algorithm (geometry only).

how to use:
    1. Open Blender file
    2. Open the Python Console
    3. Open the script file on the Python Console
    4. Select the faces you want to subdivide in Edit Mode
    5. Run the script
'''

import bpy
import bmesh
from mathutils import Vector

def is_hole_edge(edge_faces):
    return len(edge_faces) == 1

def is_hole_vertex(num_edges, num_faces):
    return num_edges != num_faces

def midpoint(co1, co2):
    return (co1 + co2) / 2.0

# Switch to object mode to access the BMesh
bpy.ops.object.mode_set(mode='OBJECT')
obj = bpy.context.active_object
if obj is None or obj.type != 'MESH':
    raise ValueError("Active object must be a mesh")

mesh = obj.data
bm = bmesh.new()
bm.from_mesh(mesh)
bm.verts.ensure_lookup_table()
bm.edges.ensure_lookup_table()
bm.faces.ensure_lookup_table()

# The user must have selected faces in Edit Mode beforehand
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_mode(type='FACE')
bpy.ops.object.mode_set(mode='OBJECT')

bm.clear()
bm.from_mesh(mesh)
bm.verts.ensure_lookup_table()
bm.edges.ensure_lookup_table()
bm.faces.ensure_lookup_table()

# Identify selected faces
selected_faces = [f for f in bm.faces if f.select]
if not selected_faces:
    bm.free()
    raise ValueError("No faces selected. Exiting.")

# Extract sub-mesh (faces, edges, verts) from selected faces
selected_faces_indices = []
for f in selected_faces:
    selected_faces_indices.append([v.index for v in f.verts])

sub_vert_indices = set()
sub_edge_set = set()
for face_verts in selected_faces_indices:
    for v_i in face_verts:
        sub_vert_indices.add(v_i)
    # Collect edges from these faces
    f_len = len(face_verts)
    for i in range(f_len):
        e_key = frozenset({face_verts[i], face_verts[(i+1)%f_len]})
        sub_edge_set.add(e_key)

sub_vert_indices = list(sub_vert_indices)
old_to_new_vert = {v_i: i for i, v_i in enumerate(sub_vert_indices)}

sub_vert_coords = [bm.verts[v_i].co.copy() for v_i in sub_vert_indices]

sub_faces = []
for f_verts in selected_faces_indices:
    sub_faces.append([old_to_new_vert[v_i] for v_i in f_verts])

# Build adjacency
vert_faces_map = [[] for _ in sub_vert_coords]
for f_i, f_verts in enumerate(sub_faces):
    for v_i in f_verts:
        vert_faces_map[v_i].append(f_i)

edge_map = {}
for f_i, f_verts in enumerate(sub_faces):
    f_len = len(f_verts)
    for i in range(f_len):
        key = frozenset({f_verts[i], f_verts[(i+1)%f_len]})
        if key not in edge_map:
            edge_map[key] = []
        edge_map[key].append(f_i)

original_edges_data = []
vert_edges_map = [[] for _ in sub_vert_coords]
for ei, (vs, flist) in enumerate(edge_map.items()):
    vs_l = list(vs)
    v1_i, v2_i = vs_l
    original_edges_data.append((v1_i, v2_i, flist))
    vert_edges_map[v1_i].append(ei)
    vert_edges_map[v2_i].append(ei)

# Catmull-Clark on sub-mesh
# Face points
face_points = []
for f_i, f_verts in enumerate(sub_faces):
    coords = [sub_vert_coords[v_i] for v_i in f_verts]
    fp = sum(coords, Vector()) / len(coords)
    face_points.append(fp)

# Edge points
edge_points = []
for (v1_i, v2_i, f_list) in original_edges_data:
    v1_co = sub_vert_coords[v1_i]
    v2_co = sub_vert_coords[v2_i]
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

# Vertex points
new_vertex_positions = []
for vi, P in enumerate(sub_vert_coords):
    adj_faces = vert_faces_map[vi]
    adj_edges = vert_edges_map[vi]
    n = len(adj_faces)

    if is_hole_vertex(len(adj_edges), len(adj_faces)):
        avg_midpoints = Vector((0,0,0))
        hole_edge_count = 0
        for ei in adj_edges:
            v1_i, v2_i, flist = original_edges_data[ei]
            if is_hole_edge(flist):
                m = midpoint(sub_vert_coords[v1_i], sub_vert_coords[v2_i])
                avg_midpoints += m
                hole_edge_count += 1
        if hole_edge_count > 0:
            V_new = (avg_midpoints + P) / (hole_edge_count + 1)
        else:
            V_new = P
    else:
        if n == 0:
            V_new = P
        else:
            F_avg = sum((face_points[f_i] for f_i in adj_faces), Vector()) / n
            edge_midpoints = []
            for ei in adj_edges:
                v1_i, v2_i, _ = original_edges_data[ei]
                edge_midpoints.append(midpoint(sub_vert_coords[v1_i], sub_vert_coords[v2_i]))
            R_avg = sum(edge_midpoints, Vector()) / len(edge_midpoints)
            V_new = (F_avg + 2*R_avg + (n-3)*P) / n

    new_vertex_positions.append(V_new)

# Reconstruct subdivided faces
edge_lookup = {}
for ei, (v1_i, v2_i, flist) in enumerate(original_edges_data):
    edge_lookup[frozenset({v1_i,v2_i})] = ei

subdiv_verts = new_vertex_positions + face_points + edge_points
v_count_original = len(new_vertex_positions)
v_count_face = len(face_points)
v_count_edge = len(edge_points)

new_faces = []
for fi, f_verts in enumerate(sub_faces):
    Fv_i = v_count_original + fi
    f_len = len(f_verts)
    for i in range(f_len):
        v_curr_i = f_verts[i]
        v_next_i = f_verts[(i+1)%f_len]
        v_prev_i = f_verts[(i-1)%f_len]

        ei_current = edge_lookup[frozenset({v_curr_i, v_next_i})]
        ei_prev = edge_lookup[frozenset({v_prev_i, v_curr_i})]

        EP_current_i = v_count_original + v_count_face + ei_current
        EP_prev_i = v_count_original + v_count_face + ei_prev

        new_faces.append([v_curr_i, EP_current_i, Fv_i, EP_prev_i])

# Replace original selected faces with subdivided faces
bm.clear()
bm.from_mesh(mesh)
bm.verts.ensure_lookup_table()
bm.edges.ensure_lookup_table()
bm.faces.ensure_lookup_table()

# Remove selected faces
for f in bm.faces[:]:
    if f.select:
        bm.faces.remove(f)

bm.verts.ensure_lookup_table()
# Map subdiv mesh indices to BMVert
subdiv_to_bmvert = {}

# Original vertices (reuse)
for i, old_vi in enumerate(sub_vert_indices):
    subdiv_to_bmvert[i] = bm.verts[old_vi]

# Create new BMVerts for face points
for i in range(v_count_face):
    co = face_points[i]
    subdiv_to_bmvert[v_count_original + i] = bm.verts.new(co)

# Create new BMVerts for edge points
for i in range(v_count_edge):
    co = edge_points[i]
    subdiv_to_bmvert[v_count_original + v_count_face + i] = bm.verts.new(co)

bm.verts.index_update()
# Create new faces
for nf in new_faces:
    face_verts = [subdiv_to_bmvert[idx] for idx in nf]
    bm.faces.new(face_verts)

bm.faces.index_update()
bm.verts.index_update()
bm.edges.index_update()

# bm.to_mesh(mesh)
# mesh.update()

# Delete the unconnected edges
bpy.ops.object.mode_set(mode='OBJECT')

# Ensure lookup tables are up-to-date
bm.verts.ensure_lookup_table()
bm.edges.ensure_lookup_table()
bm.faces.ensure_lookup_table()

# Identify edges that are not connected to any faces
edges_to_remove = [e for e in bm.edges if len(e.link_faces) == 0]

print("Removing {} unconnected edges...".format(len(edges_to_remove)))
# Remove the edges
for edge in edges_to_remove:
    bm.edges.remove(edge)

# Write back to the mesh
bm.to_mesh(mesh)
mesh.update()

# Clean up the BMesh
bm.free()

# Switch back to Edit Mode to visualize the result
bpy.ops.object.mode_set(mode='EDIT')

print("Unconnected edges removed")
print("Partial Catmull-Clark subdivision complete (geometry-only)")
