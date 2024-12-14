'''
2024 Graphics Programming Final Project
Animating an object from single monocular video

name: distance-based-weighting.py
description: Assign weights to vertices based on the distance to bones
ex) linear, sigmoid, exponential, noise

how to use:
    1. Open Blender file
    2. Open the Python Console
    3. Open the script file on the Python Console
    4. *** Change weight function and corresponding parameters in the script ***
    6. Run the script
'''

import bpy
import bmesh
from mathutils import Vector
import math

### ------------ TODO: Set up the parameters ------------- ###
# mesh object, armature
object_name = "jumpingjacks"
armature_name = "metarig"

# Method: ["linear", "sigmoid", "exponential", "noise", "cluster"]
skinning_method = "exponential"

# Parameters
influence_radius = 0.2  # Maximum influence radius for bones
factor = 1.2

# Sigmoid weight function
weight_sharpness = 10.0
# Exponential weight function
decay_factor = 30.0

# Bone-specific factors for weighting
bone_weight_factors = {  
    "Hips": 2.0,
    "Spine": 1.5,
    "Spine1": 1.5,
    "Spine2": 1.2,
    "LeftLeg": 1.0,
    "RightLeg": 1.0,
    "LeftArm": 1.0,
    "RightArm": 1.0,
    "LeftForeArm": 0.8,
    "RightForeArm": 0.8,
}
### ------------ TODO: Set up the parameters ------------- ###

min_weight_threshold = 0.0

# Access the objects
obj = bpy.data.objects.get(object_name)
armature = bpy.data.objects.get(armature_name)
if obj:
    print('mesh is right')
if armature:
    print('armature is right')

# Ensure we're in Object Mode
bpy.ops.object.mode_set(mode='OBJECT')

# Access the mesh data
mesh = obj.data
bm = bmesh.new()
bm.from_mesh(mesh)

# Ensure vertex groups exist for each bone
for bone in armature.pose.bones:
    if bone.name not in obj.vertex_groups:
        obj.vertex_groups.new(name=bone.name)
print(f"Vertex groups created for {len(armature.pose.bones)} bones")

# Assign weights
for bone in armature.pose.bones:
    print(f"Processing bone: {bone.name}")
    bone_head = armature.matrix_world @ bone.head
    bone_tail = armature.matrix_world @ bone.tail
    bone_vec = bone_tail - bone_head
    
    vgroup = obj.vertex_groups[bone.name]
    for vert in mesh.vertices:
        vertex_pos = obj.matrix_world @ Vector(vert.co)
        
        proj = (vertex_pos - bone_head).project(bone_vec)
        closest_point_on_bone = bone_head + proj
        
        if proj.dot(bone_vec) < 0:
            closest_point_on_bone = bone_head
        elif proj.length > bone_vec.length:
            closest_point_on_bone = bone_tail
        
        dist = (vertex_pos - closest_point_on_bone).length
        
        # Get the bone-specific weighting factor
        factor = bone_weight_factors.get(bone.name, 1.0)*4
        
        weight : float = 0.0
        # Weight functions
        if skinning_method == "linear":
            weight = max(min_weight_threshold, (1.0 - (dist / influence_radius)) * factor)
        elif skinning_method == "sigmoid":
            weight = 1 / (1 + math.exp(weight_sharpness * (dist - influence_radius / 2)))
            weight = max(min_weight_threshold, weight * factor)
        elif skinning_method == "exponential":
            weight = max(min_weight_threshold, math.exp(-decay_factor * dist) * factor)
        elif skinning_method == "noise":
            import random
            noise_intensity = 0.5  # Maximum noise variation (0 to 1)
            random.seed(42)
            base_weight = max(min_weight_threshold, (1.0 - (dist / influence_radius)))
            # Add noise
            noise = random.uniform(-noise_intensity, noise_intensity)
            weight = max(min_weight_threshold, base_weight + noise)
        
        # Assign weight
        vgroup.add([vert.index], weight, 'REPLACE')
            
bm.free()
mesh.update()

print(f"{skinning_method.capitalize()}-based weights assigned!")