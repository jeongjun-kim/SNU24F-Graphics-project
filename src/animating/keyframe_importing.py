import bpy
import json


OUTPUT_PATH = ""
    
# Import Animation
def import_animation(filepath):
    obj = bpy.context.object
    if obj.type != 'ARMATURE':
        print("Selected object is not an armature!")
        return
    
    # Read data from JSON file
    with open(filepath, 'r') as f:
        animation_data = json.load(f)
    
    # Create a new action
    action = bpy.data.actions.new(name="Imported Animation")
    obj.animation_data_create()
    obj.animation_data.action = action
    
    for frame_data in animation_data:
        frame = frame_data["frame"]
        for bone_data in frame_data["bones"]:
            bone_name = bone_data["name"]
            if bone_name not in obj.pose.bones:
                print(f"Bone {bone_name} not found in the armature!")
                continue
            
            bone = obj.pose.bones[bone_name]
            
            # Apply location
            bone.location = bone_data["location"]
            bone.keyframe_insert(data_path="location", frame=frame)
            
            # Apply rotation
            bone.rotation_quaternion = bone_data["rotation_quaternion"]
            bone.keyframe_insert(data_path="rotation_quaternion", frame=frame)
            
            # Apply scale
            bone.scale = bone_data["scale"]
            bone.keyframe_insert(data_path="scale", frame=frame)
    
    print(f"Animation imported from {filepath}")



import_animation(OUTPUT_PATH)
