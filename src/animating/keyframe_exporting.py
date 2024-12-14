import bpy
import json


OUTPUT_PATH = ""

def export_keyframe_animation(filepath):
    obj = bpy.context.object
    if obj.type != 'ARMATURE':
        print("Selected object is not an armature!")
        return
    
    animation_data = []
    
    # Get the action associated with the armature
    action = obj.animation_data.action
    if not action:
        print("No action found for the selected armature!")
        return
    
    # Extract keyframe points
    keyframes = set()
    for fcurve in action.fcurves:
        for keyframe_point in fcurve.keyframe_points:
            keyframes.add(keyframe_point.co[0])  # Keyframe time (frame number)
    
    keyframes = sorted(list(keyframes))  # Sort keyframes in ascending order
    
    for frame in keyframes:
        bpy.context.scene.frame_set(int(frame))  # Set the frame to extract pose
        frame_data = {"frame": int(frame), "bones": []}
        
        for bone in obj.pose.bones:
            bone_data = {
                "name": bone.name,
                "location": list(bone.location),
                "rotation_quaternion": list(bone.rotation_quaternion),
                "scale": list(bone.scale),
            }
            frame_data["bones"].append(bone_data)
        
        animation_data.append(frame_data)
    
    # Write data to JSON file
    with open(filepath, 'w') as f:
        json.dump(animation_data, f, indent=4)
    
    print(f"Keyframe animation exported to {filepath}")
    
export_keyframe_animation(OUTPUT_PATH)
