'''
2024 Graphics Programming Final Project
Animating an object from single monocular video

name: plane-threshold-selecting.py
description: Select objects whose vertices are under a plane

how to use:
    1. Open Blender file
    2. Open the Python Console
    3. Open the script file on the Python Console
    4. *** Change parameters in the script ***
    6. Run the script
'''

import bpy
import mathutils

### TODO: Set Plane equation coefficients
a = 1.0  # Coefficient for x
b = 1.0  # Coefficient for y
c = 0.0  # Constant

# Function to check if a vertex is under the plane
def is_vertex_under_plane(vertex, a, b, c):
    x, y, z = vertex
    z_plane = a * x + b * y + c
    return z < z_plane

# Deselect all objects first
bpy.ops.object.select_all(action='DESELECT')

# Iterate through all mesh objects
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        # Get the object's world matrix
        world_matrix = obj.matrix_world
        
        # Get the object's mesh data
        mesh = obj.data
        
        # Iterate through all vertices of the mesh
        under_plane = False
        for vertex in mesh.vertices:
            # Transform vertex to world coordinates
            world_vertex = world_matrix @ vertex.co
            
            # Check if the vertex is under the plane
            if is_vertex_under_plane(world_vertex, a, b, c):
                under_plane = True
                break
        
        # Select the object if any vertex is under the plane
        if under_plane:
            obj.select_set(True)
