'''
2024 Graphics Programming Final Project
Animating an object from single monocular video

name: catmull-clark-subdiv-all.py
description: Subdivides all faces of a mesh using the Catmull-Clark algorithm with color interpolation.

how to use:
    1. Open Blender file
    2. Open the Python Console
    3. Open the script file on the Python Console
    4. Select the object you want to subdivide
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

obj = bpy.context.active_object
if obj is None or obj.type != 'MESH':
    raise ValueError("Active object must be a mesh")

bpy.ops.object.mode_set(mode='OBJECT')
mesh = obj.data

# -------- Fill your color Attribute -------- #
color_layer_name = 'Attribute'
# ------------------------------------------- #

bm = bmesh.new()
bm.from_mesh(mesh)
bm.verts.ensure_lookup_table()
bm.edges.ensure_lookup_table()
bm.faces.ensure_lookup_table()

original_vert_coords = [v.co.copy() for v in bm.verts]
original_vert_colors = [None]*len(bm.verts)

# Read vertex colors if available
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

original_faces_indices = []
for f in bm.faces:
    face_vert_indices = [v.index for v in f.verts]
    original_faces_indices.append(face_vert_indices)

vert_faces_map = [[] for _ in bm.verts]
for f_i, f_verts in enumerate(original_faces_indices):
    for vi in f_verts:
        vert_faces_map[vi].append(f_i)

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

unique_edges = list(edge_lookup.items())
original_edges_data = []
edge_of_vertex = [[] for _ in bm.verts]
for ei, (vs, fs) in enumerate(unique_edges):
    verts_list = list(vs)
    v1_i, v2_i = verts_list
    original_edges_data.append((v1_i, v2_i, fs))
    edge_of_vertex[v1_i].append(ei)
    edge_of_vertex[v2_i].append(ei)

vert_edges_map = edge_of_vertex

# Clear and rebuild
bm.clear()

# Compute face points
face_points = []
face_colors = []
for f_i, f_verts in enumerate(original_faces_indices):
    coords = [original_vert_coords[vi] for vi in f_verts]
    fp = sum(coords, Vector()) / len(coords)
    face_points.append(fp)

    f_cols = [original_vert_colors[vi] for vi in f_verts]
    f_c = interpolate_colors(f_cols, [1.0]*len(f_cols))
    face_colors.append(f_c)

# Compute edge points
edge_points = []
edge_colors = []
for (v1_i, v2_i, f_list) in original_edges_data:
    v1_co = original_vert_coords[v1_i]
    v2_co = original_vert_coords[v2_i]
    v1_col = original_vert_colors[v1_i]
    v2_col = original_vert_colors[v2_i]

    if is_hole_edge(f_list):
        ep = (v1_co + v2_co) / 2.0
        ep_col = interpolate_colors([v1_col, v2_col],[1.0,1.0])
    else:
        if len(f_list) == 2:
            F1, F2 = f_list
            ep = (v1_co + v2_co + face_points[F1] + face_points[F2]) / 4.0
            ep_col = interpolate_colors([v1_col, v2_col, face_colors[F1], face_colors[F2]],
                                        [1.0,1.0,1.0,1.0])
        elif len(f_list) == 1:
            F = f_list[0]
            ep = (v1_co + v2_co + face_points[F]) / 3.0
            ep_col = interpolate_colors([v1_col, v2_col, face_colors[F]],
                                        [1.0,1.0,1.0])
        else:
            ep = (v1_co + v2_co)/2.0
            ep_col = interpolate_colors([v1_col, v2_col],[1.0,1.0])

    edge_points.append(ep)
    edge_colors.append(ep_col)

# Compute new vertex positions/colors
new_vertex_positions = []
new_vertex_colors = []
for vi, P in enumerate(original_vert_coords):
    adj_faces = vert_faces_map[vi]
    adj_edges = vert_edges_map[vi]
    n = len(adj_faces)
    V_col = original_vert_colors[vi]

    if is_hole_vertex(len(adj_edges), len(adj_faces)):
        avg_midpoints = Vector((0,0,0))
        avg_mid_col_list = []
        hole_edge_count = 0
        for ei in adj_edges:
            v1_i, v2_i, f_list = original_edges_data[ei]
            if is_hole_edge(f_list):
                m = (original_vert_coords[v1_i] + original_vert_coords[v2_i])/2.0
                avg_midpoints += m
                m_col = interpolate_colors([original_vert_colors[v1_i],
                                            original_vert_colors[v2_i]], [1.0,1.0])
                avg_mid_col_list.append(m_col)
                hole_edge_count += 1
        if hole_edge_count > 0:
            V_new = (avg_midpoints + P)/(hole_edge_count+1)
            V_new_col = interpolate_colors([V_col]+avg_mid_col_list, [1.0]*(hole_edge_count+1))
        else:
            V_new = P
            V_new_col = V_col
    else:
        if n == 0:
            V_new = P
            V_new_col = V_col
        else:
            F_avg = sum((face_points[fi] for fi in adj_faces), Vector())/n
            F_cols = [face_colors[fi] for fi in adj_faces]
            F_avg_col = interpolate_colors(F_cols, [1.0]*len(F_cols))

            edge_midpoints = []
            edge_mid_col_list = []
            for ei in adj_edges:
                v1_i, v2_i, _ = original_edges_data[ei]
                midpoint_pos = (original_vert_coords[v1_i] + original_vert_coords[v2_i])/2.0
                edge_midpoints.append(midpoint_pos)
                midpoint_col = interpolate_colors([original_vert_colors[v1_i],
                                                   original_vert_colors[v2_i]], [1.0,1.0])
                edge_mid_col_list.append(midpoint_col)

            R_avg = sum(edge_midpoints, Vector())/len(edge_midpoints)
            R_avg_col = interpolate_colors(edge_mid_col_list, [1.0]*len(edge_mid_col_list))

            V_new = (F_avg + 2*R_avg + (n-3)*P)/n

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
                V_new_col = interpolate_colors(color_list, weight_list)
            else:
                V_new_col = V_col

    new_vertex_positions.append(V_new)
    new_vertex_colors.append(V_new_col)

# Build the new subdivided mesh in BMesh
# First original verts
v_bm_verts = [bm.verts.new(co) for co in new_vertex_positions]
# Then face points
f_bm_verts = [bm.verts.new(fp) for fp in face_points]
# Then edge points
e_bm_verts = [bm.verts.new(ep) for ep in edge_points]

bm.verts.index_update()

edge_map = {}
for ei, (v1_i, v2_i, f_list) in enumerate(original_edges_data):
    edge_map[frozenset({v1_i,v2_i})] = ei

# Create faces in BM
new_face_list = []
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

        f_new = bm.faces.new([V_i, EP_current, Fv, EP_prev])
        new_face_list.append(f_new)

bm.faces.index_update()
bm.verts.index_update()

# Convert BMesh to Mesh
new_mesh = bpy.data.meshes.new("SubdividedMesh")
bm.to_mesh(new_mesh)
new_mesh.update()
bm.free()

obj.data = new_mesh

# Now assign colors to a CORNER domain attribute after we have a final mesh
col_attr = new_mesh.color_attributes.new(name="Attribute", type='FLOAT_COLOR', domain='CORNER')
col_data = col_attr.data

all_new_vertices = new_vertex_positions + face_points + edge_points
all_new_colors = new_vertex_colors + face_colors + edge_colors
default_color = Vector((1,1,1,1))

# Assign loop colors based on loop vertex index
# Each loop references a vertex in new_mesh.loops[].vertex_index
for poly in new_mesh.polygons:
    for li in range(poly.loop_start, poly.loop_start+poly.loop_total):
        v_i = new_mesh.loops[li].vertex_index
        c = all_new_colors[v_i]
        if c is None:
            c = default_color
        col_data[li].color = c
        # print(c[0], c[1], c[2], c[3])

bpy.ops.object.mode_set(mode='EDIT')
print("Catmull-Clark subdivision complete")
