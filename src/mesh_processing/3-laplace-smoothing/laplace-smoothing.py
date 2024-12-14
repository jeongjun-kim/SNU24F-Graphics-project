import bpy
import bmesh
from mathutils import Vector

def laplace_smooth(obj, iterations=1, lambda_factor=0.5, preservation_method='none'):
    """
    Perform Laplace smoothing with optional volume preservation.

    :param obj: The mesh object to smooth.
    :param iterations: Number of smoothing iterations.
    :param lambda_factor: Smoothing factor (0 < lambda_factor < 1).
    :param preservation_method: Preservation method ('none', 'centroid', 'local_volume', 'tangential').
    """
    if obj.type != 'MESH':
        print(f"{obj.name} is not a mesh object!")
        return

    bm = bmesh.new()
    bm.from_mesh(obj.data)

    for _ in range(iterations):
        # Store original vertex positions
        vertex_positions = {v: v.co.copy() for v in bm.verts}

        if preservation_method == 'centroid':
            # Compute the centroid of the mesh
            centroid = sum((v.co for v in bm.verts), Vector()) / len(bm.verts)

        for v in bm.verts:
            if not v.is_boundary:  # Skip boundary vertices
                # Calculate the average position of neighboring vertices
                neighbors = [e.other_vert(v) for e in v.link_edges]
                if len(neighbors) == 0:
                    continue

                avg_position = sum((vertex_positions[n] for n in neighbors), Vector()) / len(neighbors)

                # Apply Laplace smoothing
                smoothed_position = (1 - lambda_factor) * v.co + lambda_factor * avg_position

                if preservation_method == 'centroid':
                    # Adjust for global centroid-based volume preservation
                    v.co = smoothed_position + (v.co - centroid) * (1 - lambda_factor) *0.001
                elif preservation_method == 'local_volume':
                    # Calculate local volume before smoothing
                    initial_volume = calculate_local_volume(v, neighbors)

                    # Apply smoothing and calculate new volume
                    v.co = smoothed_position
                    new_volume = calculate_local_volume(v, neighbors)

                    # Adjust to maintain local volume
                    volume_ratio = initial_volume / new_volume if new_volume != 0 else 1
                    v.co = v.co.lerp(smoothed_position, volume_ratio)
                elif preservation_method == 'tangential':
                    # Restrict movement to the tangential plane
                    normal = v.normal
                    movement_vector = smoothed_position - v.co
                    tangential_movement = movement_vector - movement_vector.dot(normal) * normal
                    v.co += tangential_movement
                else:
                    # No preservation, standard Laplace smoothing
                    v.co = smoothed_position

    bm.to_mesh(obj.data)
    bm.free()
    print(f"Laplace smoothing with {preservation_method} preservation applied to {obj.name} for {iterations} iterations.")

def calculate_local_volume(vertex, neighbors):
    """
    Calculate the local volume (or area in 2D) around a vertex.

    :param vertex: The vertex being smoothed.
    :param neighbors: List of neighboring vertices.
    :return: Local volume.
    """
    volume = 0.0
    for n in neighbors:
        volume += (vertex.co - n.co).length
    return volume

obj = bpy.context.active_object

if obj:
    # Example usage: change the preservation_method as needed
    laplace_smooth(obj, iterations=10, lambda_factor=0.5, preservation_method='local_volume')
else:
    print("No active object selected!")
