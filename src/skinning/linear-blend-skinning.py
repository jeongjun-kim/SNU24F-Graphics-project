'''
2024 Graphics Programming Final Project
Animating an object from single monocular video

name: linear-blend-skinning.py
description: Perform Linear Blend Skinning (LBS) on a mesh object using an armature
Run this script AFTER ASSIGNING WEIGHTS to the mesh object

how to use:
    1. Open Blender file
    2. Open the Python Console
    3. Open the script file on the Python Console
    4. *** Change OBJECT_NAME and ARMATURE_NAME in the script ***
    6. Run the script
'''

import bpy
import bmesh
from mathutils import Vector, Matrix

OBJECT_NAME = "jumpingjacks"
ARMATURE_NAME = "metarig"

# Access the objects
obj = bpy.data.objects.get(OBJECT_NAME)
armature = bpy.data.objects.get(ARMATURE_NAME)
if not obj or not armature:
    raise ValueError("Object or armature not found.")

print(f"Using object: {OBJECT_NAME}, armature: {ARMATURE_NAME}")

# Ensure we're in Object Mode
bpy.ops.object.mode_set(mode='OBJECT')

# Access the mesh data
mesh = obj.data
bm = bmesh.new()
bm.from_mesh(mesh)

# Step 1: Normalize weights
# Normalize weights across all bones for each vertex
for vert in mesh.vertices:
    total_weight = 0.0
    weights = []
    for group in vert.groups:
        vgroup = obj.vertex_groups[group.group]
        weight = group.weight
        total_weight += weight
        weights.append((vgroup, weight))
    
    # Normalize weights
    if total_weight > 0:
        for vgroup, weight in weights:
            normalized_weight = weight / total_weight
            vgroup.add([vert.index], normalized_weight, 'REPLACE')
print("Weights normalized!")

# Step 2: Perform Linear Blend Skinning (LBS)
rest_pose_matrices = {bone.name: armature.matrix_world @ bone.bone.matrix_local for bone in armature.pose.bones}
for vert in mesh.vertices:
    blended_position = Vector((0, 0, 0))
    for group in vert.groups:
        vgroup = obj.vertex_groups[group.group]
        bone_name = vgroup.name
        weight = group.weight
        if weight > 0:
            pose_bone = armature.pose.bones.get(bone_name)
            if pose_bone:
                bone_matrix = (armature.matrix_world @ pose_bone.matrix) @ rest_pose_matrices[bone_name].inverted()
                transformed_vertex = bone_matrix @ vert.co
                blended_position += weight * transformed_vertex
    vert.co = blended_position


bm.free()
mesh.update()
print("Linear Blend Skinning applied!")