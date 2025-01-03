'''
2024 Graphics Programming Final Project
Animating an object from single monocular video

name: keyframe_importing.py
description: This script performs importing of demo animation keyframes.

how to use:
    1. Open Blender file
    2. Open the Python Console
    3. Open the script file on the Python Console
    4. Select a rig(Aramature) object in the 3D Viewport, Object mode before running the script
    5. fill the PATH with provided json file(exported from mixamo by utils/keyframe_exporting.py)
    6. Run the script
'''

import bpy
import json

PATH = "../../resource/animation/demo_ani_hand.json"

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
                continue
            
            bone = obj.pose.bones[bone_name]
            
            bone.location = bone_data["location"]
            bone.keyframe_insert(data_path="location", frame=frame)
            
            bone.rotation_quaternion = bone_data["rotation_quaternion"]
            bone.keyframe_insert(data_path="rotation_quaternion", frame=frame)
            
            bone.scale = bone_data["scale"]
            bone.keyframe_insert(data_path="scale", frame=frame)
    
    print(f"Animation imported from {filepath}")


if __name__ == "__main__":
    import_animation(PATH)
