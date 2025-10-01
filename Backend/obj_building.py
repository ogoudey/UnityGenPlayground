import random
import json

default_grid = """0.2 0.3 0.5 0.7 1.0 1.0 0.7 0.5 0.3 0.2
0.3 0.6 0.9 1.3 1.7 1.7 1.3 0.9 0.6 0.3
0.5 0.9 1.5 2.0 2.5 2.5 2.0 1.5 0.9 0.5
0.7 1.3 2.0 2.8 3.3 3.3 2.8 2.0 1.3 0.7
1.0 1.7 2.5 3.3 4.0 4.0 3.3 2.5 1.7 1.0
1.0 1.7 2.5 3.3 4.0 4.0 3.3 2.5 1.7 1.0
0.7 1.3 2.0 2.8 3.3 3.3 2.8 2.0 1.3 0.7
0.5 0.9 1.5 2.0 2.5 2.5 2.0 1.5 0.9 0.5
0.3 0.6 0.9 1.3 1.7 1.7 1.3 0.9 0.6 0.3
0.2 0.3 0.5 0.7 1.0 1.0 0.7 0.5 0.3 0.2"""

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

def facify(matrix):
    lines = ""
    visited = []
    x_per_row = len(matrix)
    for x in range(0, len(matrix) -1):
        for y in range(0, len(matrix[x]) -1):    
                if not (x, y) in visited:
                    visited.append((x, y))
                    lines += f"f {y*x_per_row + x + 1}/{y*x_per_row + x + 1} {(y+1)*x_per_row + x + 1}/{(y+1)*x_per_row + x + 1} {(y+1)*x_per_row + x + 2}/{(y+1)*x_per_row + x + 2} {y*x_per_row + x + 2}/{y*x_per_row + x + 2}\n"
    return lines, visited

def obj_from_grid(grid: str = default_grid):
    location = {"x": 0.0, "y": 0.0, "z": 0.0}
    scale = 5
    matrix = []
    obj_str = ""
    lines = grid.split("\n")
    print(grid)
    
    
    for y in range(len(lines)-1, -1, -1):
        line = lines[y].split(" ")
        row = []
        for x in range(len(line) - 1, -1, -1):
            row.append(float(line[x]))
            try:
                obj_str += f"v {float(x)*scale} {float(line[x])} {float(y)*scale}\n"  
            except Exception:
                print(line[x], "is an arifact of the grid. Ignoring...")
        matrix.append(row)
    print(matrix) 


    for y in range(0, len(lines)):
        line = lines[y].split(" ")
        for x in range(0, len(line)):
            try:
                u = x / (len(line) - 1) * scale*scale
                v = y / (len(lines) - 1) * scale*scale
                obj_str += f"vt {u:.6f} {v:.6f}\n"
                
            except Exception:
                print("Could not add vt")         
                
                
    """ 1st pass """
    obj_str1 = obj_str
    face_data, visits = facify(matrix)
    obj_str1 += face_data
    print("File contains", len(face_data.split("\n")), "faces.")
    
    
    out_file = "ground_built"
    out_path1 = "../Assets/" + out_file + str(random.randint(100, 999)) + ".obj"
    with open(out_path1, "w") as f:
        f.write(obj_str1)
    print("Ground obj written to", out_path1)
    out_path = out_path1
    
    """
    # 2nd pass
    face_data, visits = make_quads(matrix, 0, 0, obj_str)
    obj_str += face_data
    print("File contains", len(face_data.split("\n")), "faces.")
    
    out_file = "ground_built"
    out_path = "../Assets/" + out_file + str(random.randint(100, 999)) + ".obj"
    with open(out_path, "w") as f:
        
        f.write(obj_str)
    print("Ground obj written to", out_path)
    
    """
    
    
    return out_path, matrix
    # Generate faces
            
    
