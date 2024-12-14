'''
2024 Graphics Programming Final Project
Animating an object from single monocular video

name: camera_moving.py
description: Set up the camera to move in a circular path around the origin for rendering

how to use:
    1. Open Blender file
    2. Open the Python Console
    3. Open the script file on the Python Console
    4. *** Change parameters in the script ***
    6. Run the script
'''

import bpy
import math
from mathutils import Euler, Vector

# Parameters
camera_name = "Camera"

### TODO: Set the frame ####
frame_start = 1
frame_end = 282


### TODO: Set the hemisphere angles ####
theta_start = 0.0       # in degrees
theta_end = 360.0
phi_start = 30.0              # fixed vertical angle (just an example) 
phi_end = 70.0
radius = 8.0

# Convert angles to radians
theta_range = theta_end - theta_start
phi_range = phi_end - phi_start

# Get the camera object
camera = bpy.data.objects.get(camera_name)
if camera is None:
    raise ValueError(f"Camera object named '{camera_name}' not found in the scene.")

frame_count = frame_end - frame_start + 1
for i, frame in enumerate(range(frame_start, frame_end + 1)):
    # Progress from 0 to 1 through frames
    t = i / (frame_count - 1)
    
    # Current angle in radians
    theta_current = math.radians(theta_start + t * theta_range)
    phi_current = math.radians(phi_start + t * phi_range)
    
    # Spherical coordinates:
    x = radius * math.sin(phi_current) * math.cos(theta_current)
    y = radius * math.sin(phi_current) * math.sin(theta_current)
    z = radius * math.cos(phi_current)
    
    # Set the camera location
    camera.location = (x, y, z)
    
    # Make the camera point towards the origin (0,0,0)
    # Direction vector from camera to target:
    direction = - Vector((0.0, 0.0, 0.0)) + camera.location
    # Point the camera along direction vector:
    camera.rotation_euler = direction.to_track_quat('Z', 'Y').to_euler()
    
    # Insert keyframes for location and rotation
    camera.keyframe_insert(data_path="location", frame=frame)
    camera.keyframe_insert(data_path="rotation_euler", frame=frame)

# Optionally, you can set the scene frame range
bpy.context.scene.frame_start = frame_start
bpy.context.scene.frame_end = frame_end

print("Camera moving setup ended")
