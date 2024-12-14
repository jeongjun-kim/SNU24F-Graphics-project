import bpy
import bmesh
from mathutils import Vector, Matrix

def main(object_name="jumpingjacks", armature_name="metarig", influence_radius=0.2):
    # Access the objects
    obj = bpy.data.objects.get(object_name)
    armature = bpy.data.objects.get(armature_name)
    if not obj or not armature:
        print("Object or armature not found.")
        return

    print(f"Using object: {object_name}, armature: {armature_name}")

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

    # Step 1: Assign weights
#    for bone in armature.pose.bones:
#        print(f"Processing bone: {bone.name}")
#        bone_head = armature.matrix_world @ bone.head
#        bone_tail = armature.matrix_world @ bone.tail
#        bone_vec = bone_tail - bone_head
#        
#        vgroup = obj.vertex_groups[bone.name]

#        for vert in mesh.vertices:
#            vertex_pos = obj.matrix_world @ Vector(vert.co)
#            proj = (vertex_pos - bone_head).project(bone_vec)
#            closest_point_on_bone = bone_head + proj

#            if proj.dot(bone_vec) < 0:
#                closest_point_on_bone = bone_head
#            elif proj.length > bone_vec.length:
#                closest_point_on_bone = bone_tail

#            dist = (vertex_pos - closest_point_on_bone).length

#            weight = 0.0
#            if dist < influence_radius:
#                weight = (1.0 - (dist / influence_radius))
#            
#            # Assign weight
#            vgroup.add([vert.index], weight, 'REPLACE')

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

if __name__ == "__main__":
    # Object and armature names
    object_name = "jumpingjacks"
    armature_name = "Armature"

    # Parameters
    influence_radius = 0.2  # Maximum influence radius for bones

    main(object_name=object_name, armature_name=armature_name, influence_radius=influence_radius)
