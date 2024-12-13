'''
2024 Graphics Programming Final Project
Animating an object from single monocular video

name: catmull-clark-subdiv-partial.py
description: Subdivides selected faces of a mesh using the Catmull-Clark algorithm with color interpolation.

how to use:
    1. Open Blender file
    2. Open the Python Console
    3. Open the script file on the Python Console
    4. Select the faces you want to subdivide in Edit Mode
    5. *** Change the color_layer_name variable to the name of the color attribute you want to interpolate
    6. Run the script
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

def interpolate_colors(colors, weights):
    if all(c is None for c in colors):
        return None

    default_color = Vector((1.0, 1.0, 1.0, 1.0))
    weighted_sum = Vector((0.0, 0.0, 0.0, 0.0))
    total_weight = 0.0

    for color, weight in zip(colors, weights):
        if color is None:
            color = default_color
        weighted_sum += color * weight
        total_weight += weight

    if total_weight > 0:
        return weighted_sum / total_weight
    else:
        return default_color

# Ensure an active mesh is selected
obj = bpy.context.active_object
if obj is None or obj.type != 'MESH':
    raise ValueError("Active object must be a mesh")

bpy.ops.object.mode_set(mode='OBJECT')
mesh = obj.data

# -------- Define color attribute -------- #
color_layer_name = 'Attribute'  # Replace with your color attribute name
# ----------------------------------------- #

bm = bmesh.new()
bm.from_mesh(mesh)
bm.verts.ensure_lookup_table()
bm.edges.ensure_lookup_table()
bm.faces.ensure_lookup_table()

# Access vertex colors
original_vert_colors = [None] * len(bm.verts)

if color_layer_name is not None:
    try:
        color_layer = mesh.color_attributes[color_layer_name]
        print(f"Color attribute domain: {color_layer.domain}")
        if color_layer.domain == 'CORNER':
            # Loop-domain colors
            loop_vert_map = [[] for _ in bm.verts]
            for poly in mesh.polygons:
                for li, vi in zip(poly.loop_indices, poly.vertices):
                    c = color_layer.data[li].color
                    loop_vert_map[vi].append(c)
            for i, loops in enumerate(loop_vert_map):
                if loops:
                    avg_col = Vector((0.0, 0.0, 0.0, 0.0))
                    for c in loops:
                        avg_col += Vector(c)
                    avg_col /= len(loops)
                    original_vert_colors[i] = avg_col
                else:
                    original_vert_colors[i] = Vector((1.0, 1.0, 1.0, 1.0))
        elif color_layer.domain == 'POINT':
            # Vertex-domain colors
            for i in range(len(bm.verts)):
                c = color_layer.data[i].color
                original_vert_colors[i] = Vector(c)
        else:
            print(f"Color attribute domain '{color_layer.domain}' not supported. No color interpolation.")
            original_vert_colors = [None]*len(bm.verts)
    except KeyError:
        print("Could not access color attribute. No color interpolation.")
        original_vert_colors = [None]*len(bm.verts)
else:
    original_vert_colors = [None]*len(bm.verts)

# Switch back to Edit Mode to ensure face selection
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

# Extract sub-mesh
selected_faces_indices = []
for f in selected_faces:
    selected_faces_indices.append([v.index for v in f.verts])

sub_vert_indices = set()
sub_edge_set = set()
for face_verts in selected_faces_indices:
    for v_i in face_verts:
        sub_vert_indices.add(v_i)
    for i in range(len(face_verts)):
        e_key = frozenset({face_verts[i], face_verts[(i + 1) % len(face_verts)]})
        sub_edge_set.add(e_key)

sub_vert_indices = list(sub_vert_indices)
old_to_new_vert = {v_i: i for i, v_i in enumerate(sub_vert_indices)}

sub_vert_coords = [bm.verts[v_i].co.copy() for v_i in sub_vert_indices]
sub_vert_colors = [original_vert_colors[v_i] for v_i in sub_vert_indices]

sub_faces = []
for f_verts in selected_faces_indices:
    sub_faces.append([old_to_new_vert[v_i] for v_i in f_verts])

# Adjacency maps
vert_faces_map = [[] for _ in sub_vert_coords]
for f_i, f_verts in enumerate(sub_faces):
    for v_i in f_verts:
        vert_faces_map[v_i].append(f_i)

edge_map = {}
for f_i, f_verts in enumerate(sub_faces):
    f_len = len(f_verts)
    for i in range(f_len):
        key = frozenset({f_verts[i], f_verts[(i + 1) % f_len]})
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

# Face points
face_points = []
face_colors = []
for f_i, f_verts in enumerate(sub_faces):
    coords = [sub_vert_coords[v_i] for v_i in f_verts]
    colors = [sub_vert_colors[v_i] for v_i in f_verts]
    fp = sum(coords, Vector()) / len(coords)
    fc = interpolate_colors(colors, [1.0] * len(colors))
    face_points.append(fp)
    face_colors.append(fc)

# Edge points
edge_points = []
edge_colors = []
for (v1_i, v2_i, f_list) in original_edges_data:
    v1_co = sub_vert_coords[v1_i]
    v2_co = sub_vert_coords[v2_i]
    v1_col = sub_vert_colors[v1_i]
    v2_col = sub_vert_colors[v2_i]

    if is_hole_edge(f_list):
        ep = midpoint(v1_co, v2_co)
        ec = interpolate_colors([v1_col, v2_col], [1.0, 1.0])
    else:
        if len(f_list) == 2:
            F1, F2 = f_list
            ep = (v1_co + v2_co + face_points[F1] + face_points[F2]) / 4.0
            ec = interpolate_colors([v1_col, v2_col, face_colors[F1], face_colors[F2]], [1.0, 1.0, 1.0, 1.0])
        elif len(f_list) == 1:
            F = f_list[0]
            ep = (v1_co + v2_co + face_points[F]) / 3.0
            ec = interpolate_colors([v1_col, v2_col, face_colors[F]], [1.0, 1.0, 1.0])
        else:
            ep = midpoint(v1_co, v2_co)
            ec = interpolate_colors([v1_col, v2_col], [1.0, 1.0])
    edge_points.append(ep)
    edge_colors.append(ec)

# Vertex points
new_vertex_positions = []
new_vertex_colors = []
for vi, P in enumerate(sub_vert_coords):
    adj_faces = vert_faces_map[vi]
    adj_edges = vert_edges_map[vi]
    n = len(adj_faces)
    V_col = sub_vert_colors[vi]

    if is_hole_vertex(len(adj_edges), len(adj_faces)):
        avg_midpoints = Vector((0, 0, 0))
        avg_colors = []
        hole_edge_count = 0
        for ei in adj_edges:
            v1_i, v2_i, flist = original_edges_data[ei]
            if is_hole_edge(flist):
                m = midpoint(sub_vert_coords[v1_i], sub_vert_coords[v2_i])
                avg_midpoints += m
                avg_colors.append(interpolate_colors([sub_vert_colors[v1_i], sub_vert_colors[v2_i]], [1.0, 1.0]))
                hole_edge_count += 1
        if hole_edge_count > 0:
            V_new = (avg_midpoints + P) / (hole_edge_count + 1)
            V_new_col = interpolate_colors([V_col] + avg_colors, [1.0] * (hole_edge_count + 1))
        else:
            V_new = P
            V_new_col = V_col
    else:
        if n == 0:
            V_new = P
            V_new_col = V_col
        else:
            F_avg = sum((face_points[f] for f in adj_faces), Vector()) / n
            F_cols = [face_colors[f] for f in adj_faces]
            F_avg_col = interpolate_colors(F_cols, [1.0] * len(F_cols))

            edge_midpoints = []
            edge_mid_col_list = []
            for ei in adj_edges:
                v1_i, v2_i, _ = original_edges_data[ei]
                edge_midpoints.append(midpoint(sub_vert_coords[v1_i], sub_vert_coords[v2_i]))
                edge_mid_col_list.append(interpolate_colors([sub_vert_colors[v1_i], sub_vert_colors[v2_i]], [1.0, 1.0]))

            R_avg = sum(edge_midpoints, Vector()) / len(edge_midpoints)
            R_avg_col = interpolate_colors(edge_mid_col_list, [1.0] * len(edge_mid_col_list))

            V_new = (F_avg + 2 * R_avg + (n - 3) * P) / n
            
            color_list = []
            weight_list = []
            if F_avg_col is not None:
                color_list.append(F_avg_col)
                weight_list.append(1.0)
            if R_avg_col is not None:
                color_list.append(R_avg_col)
                weight_list.append(2.0)
            if V_col is not None:
                if (n-3) != 0:
                    color_list.append(V_col)
                    weight_list.append(n-3)
                else:
                    if not color_list:
                        color_list.append(V_col)
                        weight_list.append(1.0)
            
            if color_list and sum(weight_list) != 0:
                V_new_col
            else:
                V_new_col = V_col
            
    new_vertex_positions.append(V_new)
    new_vertex_colors.append(V_new_col)

# Reconstruct subdivided faces
edge_lookup = {}
for ei, (v1_i, v2_i, flist) in enumerate(original_edges_data):
    edge_lookup[frozenset({v1_i, v2_i})] = ei
    
# Create new geometry
subdiv_verts = new_vertex_positions + face_points + edge_points
subdiv_colors = new_vertex_colors + face_colors + edge_colors
default_color = Vector((1.0, 1.0, 1.0, 1.0))
# Add faces
v_count_original = len(new_vertex_positions)
v_count_face = len(face_points)
v_count_edge = len(edge_points)

new_faces = []
for fi, f_verts in enumerate(sub_faces):
    Fv_i = v_count_original + fi
    f_len = len(f_verts)
    for i in range(f_len):
        v_curr_i = f_verts[i]
        v_next_i = f_verts[(i + 1) % f_len]
        v_prev_i = f_verts[(i - 1) % f_len]

        ei_current = edge_lookup[frozenset({v_curr_i, v_next_i})]
        ei_prev = edge_lookup[frozenset({v_prev_i, v_curr_i})]

        EP_current_i = v_count_original + v_count_face + ei_current
        EP_prev_i = v_count_original + v_count_face + ei_prev

        new_faces.append([v_curr_i, EP_current_i, Fv_i, EP_prev_i])

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
#Map subdiv mesh indices to BMVert
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

# Map between old index and new index after bm.verts.index_update()
new_to_old_index_map = {vert.index: old_index for old_index, vert in subdiv_to_bmvert.items()}
key_list = list(new_to_old_index_map.keys())

bm.to_mesh(mesh)
mesh.update()

# Assign vertex colors
col_attr = mesh.color_attributes[color_layer_name]
col_data = col_attr.data


# Assign loop colors based on loop vertex index
for poly in mesh.polygons:
    for li in range(poly.loop_start, poly.loop_start + poly.loop_total):
        v_i = mesh.loops[li].vertex_index
        if v_i not in new_to_old_index_map:
            continue
        else:
            old_v_i = new_to_old_index_map[v_i]
            # print(f"v_i: {v_i}, new_v_i: {old_v_i}")
            c = subdiv_colors[old_v_i]
            if c is None:
                c = default_color
            col_data[li].color = c


# Delete the edges that are not connected to any face
# Reload the mesh

# Get the active object
obj = bpy.context.active_object
if obj is None or obj.type != 'MESH':
    raise ValueError("Active object must be a mesh")

# Switch to object mode
bpy.ops.object.mode_set(mode='OBJECT')
mesh = obj.data

# Load BMesh and ensure lookup tables are updated
bm = bmesh.new()
bm.from_mesh(mesh)
bm.verts.ensure_lookup_table()
bm.edges.ensure_lookup_table()
bm.faces.ensure_lookup_table()

# Find and delete loose edges (edges not connected to any face)
loose_edges = [e for e in bm.edges if len(e.link_faces) == 0]
for edge in loose_edges:
    bm.edges.remove(edge)

# Ensure vertex color attributes are preserved
if len(mesh.color_attributes) > 0:
    color_layer = mesh.color_attributes.active
    if color_layer and color_layer.domain == 'POINT':
        # Collect vertex colors before writing the updated mesh
        vertex_colors = [color_layer.data[i].color for i in range(len(mesh.vertices))]
    else:
        vertex_colors = None
else:
    vertex_colors = None

# Write changes back to the mesh
bm.to_mesh(mesh)
mesh.update()
bm.free()

# Reapply vertex colors if they exist
if vertex_colors:
    color_layer = mesh.color_attributes.active
    if color_layer and color_layer.domain == 'POINT':
        for i, color in enumerate(vertex_colors):
            color_layer.data[i].color = color

# Switch back to edit mode to see the changes
bpy.ops.object.mode_set(mode='EDIT')

print("Unconnected edges removed")
print("Partial Catmull-Clark subdivision with color interpolation complete")

