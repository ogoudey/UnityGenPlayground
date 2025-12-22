import random
import json
import numpy as np
from tqdm import tqdm
from pathlib import Path

from logger import log

default_grid = """0 0 0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 2 0 0 0 0 0 0
0 0 0 0 0 3 0 0 0 0 0 0
0 0 0 0 0 6 0 0 0 0 0 0
0 0 0 0 0 8 0 0 0 0 0 0
0 0 0 0 0 10 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0 0 0"""

mini_grid = """1 1 1
1 2 1
1 1 1"""

pad = 100

def make_quads(matrix, x, y, obj_str, visited=[]):
    x_per_row = len(matrix)
    new_line = f"f {y*x_per_row + x + 1} {(y+1)*x_per_row + x + 1} {(y+1)*x_per_row + x + 2} {y*x_per_row + x + 2}\n"
    #print(new_line)
    obj_str += new_line
    visited.append((x, y))
    if x + 1 < len(matrix[0]):
        if not (x+1, y) in visited:
            new_obj_str_seg, visited = make_quads(matrix, x+1, y, obj_str, visited)
            new_line += new_obj_str_seg
    if y + 1 < len(matrix):
        if not (x, y+1) in visited:
            new_obj_str_seg, visited = make_quads(matrix, x, y+1, obj_str, visited)
            new_line += new_obj_str_seg
    if x + 1 < len(matrix[0]) and y + 1 < len(matrix):
        if not (x+1, y+1) in visited:
            new_obj_str_seg, visited = make_quads(matrix, x+1, y+1, obj_str, visited) 
            new_line += new_obj_str_seg

    return new_line, visited

def facify(matrix, scene_name_for_logging="facifier"):
    lines = ""
    log("Getting row size...", scene_name_for_logging)
    row_size = len(matrix)
    
    visited = []
    log("Constructing faces for each row...", scene_name_for_logging)
    for y in range(0, len(matrix) -1):
        for x in range(0, len(matrix[y]) -1):    
                if not (x, y) in visited:
                    visited.append((x, y))
                    lines += f"f {y*row_size + x + 1}/{y*row_size + x + 1} {(y+1)*row_size + x + 1}/{(y+1)*row_size + x + 1} {(y+1)*row_size + x + 2}/{(y+1)*row_size + x + 2} {y*row_size + x + 2}/{y*row_size + x + 2}\n"
 
    log("Returning...", scene_name_for_logging)
    return lines, visited
"""
def obj_from_grid(obj_path: Path, grid: str = default_grid, scale=5.0):
    location = {"x": 0.0, "y": 0.0, "z": 0.0}
    scale = 5
    matrix = []
    obj_str = ""
    lines = grid.split("\n")

    dimension = scale*len(lines) - scale
    #print(grid)
    
    print("\nVVVVVVVVV\n")
    for y in range(0, len(lines)):
        line = lines[y].split(" ")
        row = []
        
        for x in range(0, len(line)):
            row.append(float(line[x]))
            try:
                obj_str += f"v {-float(x)*scale} {float(line[x])} {dimension - float(y)*scale}\n"  
            except Exception:
                print(line[x], "is an arifact of the grid. Ignoring...")
        #print(line)
        

            
        matrix.append(row)
    #print("\nVVVVVVVVV\n")
    #print(matrix) 


    for y in range(0, len(lines)):
        line = lines[y].split(" ")
        for x in range(0, len(line)):
            try:
                u = x / (len(line) - 1) * scale*scale
                v = y / (len(lines) - 1) * scale*scale
                obj_str += f"vt {u:.6f} {v:.6f}\n"
                
            except Exception:
                print("Could not add vt")         
                
                

    obj_str1 = obj_str
    face_data, visits = facify(matrix, scene_name_for_logging)
    obj_str1 += face_data
    print("File contains", len(face_data.split("\n")), "faces.")
    
    
    out_file = "ground" + str(random.randint(100, 999)) + ".obj"
    out_path1 = obj_path / out_file
    with open(out_path1, "w") as f:
        f.write(obj_str1)
    print("Ground obj written to", out_path1)
    out_path = out_path1
    
    return out_path, matrix
    # Generate faces
"""
def obj_from_grid_procedural(manifest_path: Path, grid: str = default_grid, scale=5.0, scene_name_for_logging:str=""):
    log(f"Starting to build ground in Manifest {manifest_path}", scene_name_for_logging)
    location = {"x": 0.0, "y": 0.0, "z": 0.0}
    obj_str = ""
    log(f"Splitting...", scene_name_for_logging)
    log(f"Grid: {grid}", scene_name_for_logging)
    lines = grid.split("\n")



    line = lines[0].split(" ")
    dimension = scale*len(lines) - scale
    print(grid)
    log(f"Lines split into lines", scene_name_for_logging)
    big_world = []
    small_world = []

    if not len(lines) == len(line):
        log(f"Height {len(lines)} does not equal width {len(line)}", scene_name_for_logging)
        print(f"Height {len(lines)} does not equal width {len(line)}")
        raise AssertionError(f"Agent did not generate square ground. It was {len(lines)} by {len(line)}. Try a smaller resolution.")
    log(f"Section I", scene_name_for_logging)
    # Section I
    for y in range(0, pad):
        row = []
        for x in range(0, pad + len(line) + pad):
            row.append(0.0)
            obj_str += f"v {float(pad - x)*scale} {0.0} {float(pad + len(lines) - y - 1)*scale}\n"
        big_world.append(row)
        #print(pad + len(lines) - y - 1, ": ",row)
    #print("-----------")
    log(f"Section II", scene_name_for_logging)
    # Section II
    for y in range(0, len(lines)):
        line = lines[y].split(" ")
        row = []
        for x in range(0, pad):
            obj_str += f"v {float(pad - x)*scale} {0.0} {dimension - float(y)*scale}\n"
            row.append(0.0)

        small_world_row = []
        for x in range(0, len(line)):
            try:
                small_world_row.append(float(line[x]))
                row.append(float(line[x]))
                obj_str += f"v {-float(x)*scale} {float(line[x])} {dimension - float(y)*scale}\n"  
            except Exception:
                print(line[x], "is an arifact of the grid. Ignoring...")
        small_world.append(small_world_row)
        
        for x in range(0, pad):
            obj_str += f"v {float(-len(line) - x)*scale} {0.0} {dimension - float(y)*scale}\n"
            row.append(0.0)
        big_world.append(row)
        #print((dimension - float(y)*scale)/scale, ": ",row)
    #print("-----------")
    log(f"Section III", scene_name_for_logging)
    # Section III
    for y in range(0, pad):
        row = []
        for x in range(0, pad + len(line) + pad):
            row.append(0.0)
            obj_str += f"v {float(pad - x)*scale} {0.0} {float(- y - 1)*scale}\n"
        big_world.append(row)
        #print(- y - 1, ": ",row)

    
    log(f"Adding texture UVs", scene_name_for_logging)
    # Textures
    for y in range(0, len(big_world)):
        for x in range(0, len(big_world[y])):
            try:
                u = x / (len(big_world[0]) - 1) * scale*scale
                v = y / (len(big_world) - 1) * scale*scale
                obj_str += f"vt {u:.6f} {v:.6f}\n"
                
            except Exception:
                log(f"Could not add texture UV", scene_name_for_logging)
                print("Could not add vt")    
    

    try:
        obj_str1 = obj_str
        log(f"Creating faces", scene_name_for_logging)
        face_data, visits = facify(big_world, scene_name_for_logging)
        log(f"Adding faces to file", scene_name_for_logging)
        obj_str1 += face_data
        log(f"File contains {len(face_data.split('\n'))} faces.", scene_name_for_logging)
        
        
        out_file = f"ground_pro{str(random.randint(100, 999))}.obj"
        log(f"Outfile: {out_file}", scene_name_for_logging)
        out_path1 = manifest_path / out_file
        log(f"Making directory if it doesn't already exist: {out_path1}", scene_name_for_logging)
        manifest_path.resolve()
        log(f"Making directory if it doesn't already exist (resolved): {out_path1}", scene_name_for_logging)
        manifest_path.mkdir(parents=True, exist_ok=True)
        log(f"Attempting to write to {out_path1}", scene_name_for_logging)
        #log(f"Writing {obj_str1}", scene_name_for_logging)
        with open(out_path1, "w") as f:
            f.write(obj_str1)
        log(f"Written to {out_path1}", scene_name_for_logging)
        print("Ground obj written to", out_path1)
        out_path = out_path1
    except Exception as e:
        log(str(e), scene_name_for_logging)
        log("Wjat else??", scene_name_for_logging)
        out_path = "BAd path"
    return out_path, small_world