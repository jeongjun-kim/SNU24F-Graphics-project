'''
2024 Graphics Programming Final Project
Animating an object from single monocular video

name: mesh_logging_by_cpp.py
description: This script integrates Blender with a custom C++ library to process and clean up 3D mesh data. 
             Specifically, it uses the library to merge duplicate vertices within a given distance threshold, 
             optimizing the mesh structure for further operations. The script demonstrates how to combine Python, 
             C++ for efficient mesh processing.

how to use:
    1. Open the Blender file.
    2. Open the Python Console in Blender.
    3. Load this script into the Python Console.
    4. Adjust the parameters:
        - `THRESHOLD`: Maximum distance between vertices to be considered duplicates (default 0.003).
    5. Go to ./cpp/src
    6. $ g++ -shared -fPIC -o ../build/mesh_processing.so mesh_processing.cpp ../includes/glad/glad.c -I../includes -lGL -lglfw -ldl
    7. Ensure the compiled C++ library is located in the specified path (`./cpp/build/mesh_processing.so`).
    8. Run the script.
'''

THRESHOLD = 0.001

import bpy
import ctypes
import numpy as np
import gpu
from gpu.types import GPUOffScreen

lib = ctypes.CDLL('./cpp/build/mesh_processing.so')

lib.init_glad.argtypes = []
lib.init_glad.restype = ctypes.c_bool

lib.process_vertices.argtypes = [
    ctypes.POINTER(ctypes.c_float),  # vertices
    ctypes.c_int,                   # num_vertices
    ctypes.POINTER(ctypes.c_int),   # edges
    ctypes.c_int,                   # num_edges
    ctypes.c_float                  # threshold
]
lib.process_vertices.restype = None

def merge_duplicate_vertices(obj, threshold=0.001):
    if not obj or obj.type != 'MESH':
        print("Please select a valid mesh object.")
        return

    mesh = obj.data
    vertices = np.array([v.co for v in mesh.vertices], dtype=np.float32).flatten()
    edges = np.array([[e.vertices[0], e.vertices[1]] for e in mesh.edges], dtype=np.int32).flatten()

    vertices_ptr = vertices.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
    edges_ptr = edges.ctypes.data_as(ctypes.POINTER(ctypes.c_int))


    if not lib.init_glad():
        print("Failed to initialize GLAD in Blender script.")
        return

    lib.process_vertices(vertices_ptr, len(mesh.vertices), edges_ptr, len(mesh.edges), threshold)

    reshaped_vertices = vertices.reshape(-1, 3)
    for i, v in enumerate(mesh.vertices):
        v.co = reshaped_vertices[i]


    print(f"Merged duplicate vertices with threshold {threshold} using C++ and OpenGL.")

obj = bpy.context.active_object
merge_duplicate_vertices(obj, THRESHOLD)
