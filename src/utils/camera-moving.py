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
CAMERA_NAME = "Camera"

### TODO: Set the frame ####
FRAME_START = 1
FRAME_END = 282

### TODO: Set the hemisphere angles ####
THETA_START = 0.0       # in degrees
THETA_END = 360.0
PHI_START = 30.0              # fixed vertical angle (just an example) 
PHI_END = 70.0
RADIUS = 8.0

# Convert angles to radians
theta_range = THETA_END - THETA_START
phi_range = PHI_END - PHI_START

# Get the camera object
camera = bpy.data.objects.get(CAMERA_NAME)
if camera is None:
    raise ValueError(f"Camera object named '{CAMERA_NAME}' not found in the scene.")

frame_count = FRAME_END - FRAME_START + 1
for i, frame in enumerate(range(FRAME_START, FRAME_END + 1)):
    # Progress from 0 to 1 through frames
    t = i / (frame_count - 1)
    
    # Current angle in radians
    theta_current = math.radians(THETA_START + t * theta_range)
    phi_current = math.radians(PHI_START + t * phi_range)
    
    # Spherical coordinates:
    x = RADIUS * math.sin(phi_current) * math.cos(theta_current)
    y = RADIUS * math.sin(phi_current) * math.sin(theta_current)
    z = RADIUS * math.cos(phi_current)
    
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
bpy.context.scene.FRAME_START = FRAME_START
bpy.context.scene.FRAME_END = FRAME_END

print("Camera moving setup ended")
