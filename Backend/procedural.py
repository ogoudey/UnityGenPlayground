from noise import pnoise2
import numpy as np

import obj_building

def populate(asset_path_list, unity):
    ground_matrix, ground_scale = unity.ground_matrix, unity.ground_scale
    dimension = len(ground_matrix)*ground_scale - ground_scale

    def in_no_pose_zone(point):
        if point[0] < ground_scale * (len(ground_matrix[0]) - 1) and point[0] > 0:
            if point[1] < ground_scale * (len(ground_matrix) - 1) and point[1] > 0:
                return True
            
    for asset in asset_path_list:
        world_pad = obj_building.pad
        x_range = (-world_pad, int(world_pad + dimension))
        y_range = (-world_pad, int(world_pad + dimension))
        # noise

        p_noise_list = perlin_points_2d(x_range, y_range, n_points=100, scale=0.1, threshold=0.0)
        for point in p_noise_list:
            if not in_no_pose_zone(point):
                print("Adding prefab")
                unity.add_prefab(asset, {"x": point[0], "y": 0, "z": point[1]}, {"x": 0, "y": 0, "z": 0})
    

def perlin_points_2d(x_range, y_range, n_points, scale=0.1, threshold=0.0, seed=None):
    """
    Generate points in a 2D plane using Perlin noise.

    Args:
        x_range: tuple (xmin, xmax)
        y_range: tuple (ymin, ymax)
        n_points: number of candidate grid points to sample
        scale: frequency scaling of Perlin noise (smaller = smoother)
        threshold: minimum noise value to keep a point
        seed: optional integer for reproducibility

    Returns:
        List of (x, y) points
    """
    if seed is not None:
        np.random.seed(seed)

    points = []
    for _ in range(n_points * 5):  # oversample and filter by threshold
        x = np.random.uniform(*x_range)
        y = np.random.uniform(*y_range)
        n = pnoise2(x * scale, y * scale, octaves=4)
        if n > threshold:
            points.append([x, y])
        if len(points) >= n_points:
            break
    return points