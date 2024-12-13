import bmesh
import bpy
import time
from mathutils import Vector

def get_mesh_stats():
    """Get the count of vertices, edges, and faces in the active object."""
    bm = bmesh.from_edit_mesh(bpy.context.edit_object.data)
    return len(bm.verts), len(bm.edges), len(bm.faces)

def log_stats_change(start_stats, end_stats, process_name, elapsed_time):
    """Log the changes in mesh statistics."""
    verts_diff = end_stats[0] - start_stats[0]
    edges_diff = end_stats[1] - start_stats[1]
    faces_diff = end_stats[2] - start_stats[2]
    print(f"{process_name}: \n    Vertices: {verts_diff:+}, Edges: {edges_diff:+}, Faces: {faces_diff:+}, Time: {elapsed_time:.4f} seconds")

def custom_fill(obj):
    """
    Detect and fill holes (non-manifold edges) in the selected mesh object.
    """
    if obj.type != 'MESH':
        print("Selected object is not a mesh!")
        return

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)

    # Deselect all vertices, edges, and faces
    for elem in bm.verts:
        elem.select = False
    for elem in bm.edges:
        elem.select = False
    for elem in bm.faces:
        elem.select = False

    non_manifold_edges = [e for e in bm.edges if not e.is_manifold]
    for edge in non_manifold_edges:
        edge.select = True

    bmesh.update_edit_mesh(obj.data)

    if non_manifold_edges:
        bpy.ops.mesh.fill()  # Fill selected edges
        print(f"Filled {len(non_manifold_edges)} non-manifold edges.")

    bpy.ops.object.mode_set(mode='OBJECT')

def clean_non_manifold(threshold=0.0001, sides=0):
    """
    Cleanup non-manifold issues such as loose elements, duplicate vertices, and holes.
    
    :param threshold: Minimum distance between elements to merge.
    :param sides: Number of sides in hole required to fill (0 fills all holes).
    """
    # Ensure in Edit Mode
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_mode(type="VERT")
    bpy.ops.mesh.reveal()

    # Initial stats
    initial_stats = get_mesh_stats()

    # Delete loose elements
    start_time = time.time()
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.delete_loose(use_verts=True, use_edges=True, use_faces=True)
    elapsed_time = time.time() - start_time
    log_stats_change(initial_stats, get_mesh_stats(), "Delete Loose Elements", elapsed_time)

    # Delete interior faces
    start_stats = get_mesh_stats()
    start_time = time.time()
    bpy.ops.mesh.select_all(action="DESELECT")
    bpy.ops.mesh.select_interior_faces()
    bpy.ops.mesh.delete(type="FACE")
    elapsed_time = time.time() - start_time
    log_stats_change(start_stats, get_mesh_stats(), "Delete Interior Faces", elapsed_time)

    # Remove duplicate vertices
    start_stats = get_mesh_stats()
    start_time = time.time()
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.remove_doubles(threshold=threshold)
    elapsed_time = time.time() - start_time
    log_stats_change(start_stats, get_mesh_stats(), "Remove Duplicate Vertices", elapsed_time)

    # Dissolve degenerate faces and edges
    start_stats = get_mesh_stats()
    start_time = time.time()
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.dissolve_degenerate(threshold=threshold)
    elapsed_time = time.time() - start_time
    log_stats_change(start_stats, get_mesh_stats(), "Dissolve Degenerate Elements", elapsed_time)

    # Fix non-manifold geometry
    start_stats = get_mesh_stats()
    start_time = time.time()
    bpy.ops.mesh.select_non_manifold(extend=False, use_wire=True, use_boundary=True, use_multi_face=True, use_non_contiguous=True, use_verts=True)
    bpy.ops.mesh.fill_holes(sides=sides)
    elapsed_time = time.time() - start_time
    log_stats_change(start_stats, get_mesh_stats(), "Fix Non-Manifold Geometry", elapsed_time)

    # Ensure normals are consistent
    start_stats = get_mesh_stats()
    start_time = time.time()
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent()
    elapsed_time = time.time() - start_time
    log_stats_change(start_stats, get_mesh_stats(), "Ensure Consistent Normals", elapsed_time)

# Example usage
if __name__ == "__main__":
    obj = bpy.context.active_object
    if obj:
        print("Running custom fill...")
        custom_fill(obj)
        
        ########################
        # TODO : Find threshold
        threshold = 0.001
        ########################
        print("Running clean non-manifold...")
        clean_non_manifold(threshold=threshold, sides=4)
    else:
        print("No active object selected!")

