'''
2024 Graphics Programming Final Project
Animating an object from single monocular video

name: dual-quaternion-skinning.py
description: Perform Dual Quaternion Skinning (DQS) on a mesh object using an armature
Run this script AFTER ASSIGNING WEIGHTS to the mesh object
reference: https://team.inria.fr/imagine/files/2014/10/skinning_dual_quaternions.pdf

how to use:
    1. Open Blender file
    2. Open the Python Console
    3. Open the script file on the Python Console
    4. *** Change object_name and armature_name in the script ***
    5. Run the script
'''

import bpy
import bmesh
from mathutils import Vector, Quaternion
import numpy as np

class DualQuaternion:
    """A helper class to represent dual quaternions."""
    def __init__(self, real=Quaternion((1, 0, 0, 0)), dual=Quaternion((0, 0, 0, 0))):
        self.real = real
        self.dual = dual

    def normalize(self):
        """Normalize the dual quaternion."""
        magnitude = self.real.magnitude
        if magnitude > 0:
            self.real = self.real * (1.0 / magnitude)
            self.dual = self.dual * (1.0 / magnitude)

    def extract_components(self):
        """Extract normalized components of the dual quaternion."""
        self.normalize()
        # Real (rotation) components
        w0, x0, y0, z0 = self.real
        # Dual (translation) components
        wε, xε, yε, zε = self.dual
        return (w0, x0, y0, z0), (wε, xε, yε, zε)

    def to_transformation_matrix(self):
        """Convert the dual quaternion to a transformation matrix."""
        (w0, x0, y0, z0), (wε, xε, yε, zε) = self.extract_components()

        # Compute translation components t0, t1, t2
        t0 = 2 * (-wε * x0 + xε * w0 - yε * z0 + zε * y0)
        t1 = 2 * (-wε * y0 + xε * z0 + yε * w0 - zε * x0)
        t2 = 2 * (-wε * z0 - xε * y0 + yε * x0 + zε * w0)

        # Construct the transformation matrix M
        matrix = np.array([
            [1 - 2 * (y0**2 + z0**2), 2 * (x0 * y0 - w0 * z0), 2 * (x0 * z0 + w0 * y0), t0],
            [2 * (x0 * y0 + w0 * z0), 1 - 2 * (x0**2 + z0**2), 2 * (y0 * z0 - w0 * x0), t1],
            [2 * (x0 * z0 - w0 * y0), 2 * (y0 * z0 + w0 * x0), 1 - 2 * (x0**2 + y0**2), t2],
            [0, 0, 0, 1]
        ])
        return matrix


def matrix_to_dual_quaternion(matrix):
    """Convert a transformation matrix to a dual quaternion."""
    real = matrix.to_quaternion()
    translation = matrix.translation
    dual = 0.5 * Quaternion((0, translation.x, translation.y, translation.z)) @ real
    return DualQuaternion(real, dual)


object_name = "jumpingjacks"
armature_name = "metarig"

# Access the objects
obj = bpy.data.objects.get(object_name)
armature = bpy.data.objects.get(armature_name)
if not obj or not armature:
    raise ValueError("Object or armature not found.")

print(f"Using object: {object_name}, armature: {armature_name}")

# Ensure we're in Object Mode
bpy.ops.object.mode_set(mode='OBJECT')

# Access the mesh data
mesh = obj.data
bm = bmesh.new()
bm.from_mesh(mesh)

# Step 1: Normalize weights
for vert in mesh.vertices:
    total_weight = sum(group.weight for group in vert.groups)
    if total_weight > 0:
        for group in vert.groups:
            vgroup = obj.vertex_groups[group.group]
            normalized_weight = group.weight / total_weight
            vgroup.add([vert.index], normalized_weight, 'REPLACE')
print("Weights normalized!")

# Step 2: Precompute dual quaternions for each bone
dual_quaternions = {}
for bone in armature.pose.bones:
    bone_name = bone.name
    rest_matrix = armature.matrix_world @ bone.bone.matrix_local
    pose_matrix = armature.matrix_world @ bone.matrix
    transform_matrix = pose_matrix @ rest_matrix.inverted()

    # Convert to dual quaternion
    dual_quaternions[bone_name] = matrix_to_dual_quaternion(transform_matrix)

print("Dual quaternions computed for all bones.")

# Step 3: Perform Dual Quaternion Skinning (DQS)
# Transform vertex positions and normals
for vert in mesh.vertices:
    # Initialize blended dual quaternion
    blended_dual_quat = DualQuaternion(Quaternion((0, 0, 0, 0)), Quaternion((0, 0, 0, 0)))
    total_weight = 0.0

    # Blend dual quaternions for all influencing bones
    for group in vert.groups:
        vgroup = obj.vertex_groups[group.group]
        bone_name = vgroup.name
        weight = group.weight
        if weight > 0 and bone_name in dual_quaternions:
            dq = dual_quaternions[bone_name]
            blended_dual_quat.real += dq.real * weight
            blended_dual_quat.dual += dq.dual * weight
            total_weight += weight

    if total_weight > 0:
        blended_dual_quat.normalize()
        transformation_matrix = blended_dual_quat.to_transformation_matrix()

        # Transform vertex position
        vertex_position = np.array([vert.co.x, vert.co.y, vert.co.z, 1.0])  # Homogeneous coordinates
        transformed_position = transformation_matrix @ vertex_position

        # Update vertex position
        vert.co = Vector(transformed_position[:3])

# Recalculate normals for the entire mesh
bm.normal_update()  # Updates the vertex and face normals based on geometry changes
mesh.update()

print("Vertex positions and normals updated successfully!")
print("Dual Quaternion Skinning applied!")
