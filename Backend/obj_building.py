import random
import json

default_grid = """0 0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 2 0 0 0 0 0
0 0 0 0 0 3 0 0 0 0 0
0 0 0 0 0 6 0 0 0 0 0
0 0 0 0 0 8 0 0 0 0 0
0 0 0 0 0 10 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0 0"""

pad = 1000

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

def facify(matrix, extended_to_big=True):
    lines = ""
    x_per_row = len(matrix)
    print(x_per_row)
    index_offset = 6 if extended_to_big else 0
    if extended_to_big:
        lines += f"f 1/1 5/5 6/6 2/2\n"
        lines += f"f 2/2 6/6 {5 + x_per_row}/{5 + x_per_row} 3/3\n"
        lines += f"f 3/3 {5 + x_per_row}/{5 + x_per_row} {6 + x_per_row}/{6 + x_per_row} 4/4\n"
        lines += f"f 5/5 {7 + x_per_row * (x_per_row - 1)}/{7 + x_per_row * (x_per_row - 1)} {8 + x_per_row * (x_per_row - 1)}/{8 + x_per_row * (x_per_row - 1)} 6/6\n"
        lines += f"f {5 + x_per_row}/{5 + x_per_row} {7 + x_per_row * x_per_row}/{7 + x_per_row * x_per_row} {8 + x_per_row * x_per_row}/{8 + x_per_row * x_per_row} {6 + x_per_row}/{6 + x_per_row}\n"
        lines += f"f {7 + x_per_row * (x_per_row - 1)}/{7 + x_per_row * (x_per_row - 1)} {9 + x_per_row * x_per_row}/{9 + x_per_row * x_per_row} {10 + x_per_row * x_per_row}/{10 + x_per_row * x_per_row} {8 + x_per_row * (x_per_row - 1)}/{8 + x_per_row * (x_per_row - 1)}\n"
        lines += f"f {8 + x_per_row * (x_per_row - 1)}/{8 + x_per_row * (x_per_row - 1)} {10 + x_per_row * x_per_row}/{10 + x_per_row * x_per_row} {11 + x_per_row * x_per_row}/{11 + x_per_row * x_per_row} {7 + x_per_row * x_per_row}/{7 + x_per_row * x_per_row}\n"
        lines += f"f {7 + x_per_row * x_per_row}/{7 + x_per_row * x_per_row} {11 + x_per_row * x_per_row}/{11 + x_per_row * x_per_row} {12 + x_per_row * x_per_row}/{12 + x_per_row * x_per_row} {8 + x_per_row * x_per_row}/{8 + x_per_row * x_per_row}\n"
    visited = []
    
    for x in range(0, len(matrix[0]) -1):    
        if not (x, 0) in visited:
            visited.append((x, 0))
            lines += f"f {0 + x + index_offset}/{0 + x + index_offset} {x_per_row + 1 + x + index_offset}/{x_per_row + 1 + x + index_offset} {x_per_row + 2 + x + index_offset}/{x_per_row + 2 + x + index_offset} {1 + x + index_offset}/{1 + x + index_offset}\n"
    index_offset = 7 if extended_to_big else 0
    for y in range(1, len(matrix) -2):
        for x in range(0, len(matrix[y]) -1):    
                if not (x, y) in visited:
                    visited.append((x, y))
                    lines += f"f {y*x_per_row + x + index_offset}/{y*x_per_row + x + index_offset} {(y+1)*x_per_row + x + index_offset}/{(y+1)*x_per_row + x + index_offset} {(y+1)*x_per_row + x + 1 + index_offset}/{(y+1)*x_per_row + x + 1 + index_offset} {y*x_per_row + x + 1 + index_offset}/{y*x_per_row + x + 1 + index_offset}\n"
    index_offset = 6 if extended_to_big else 0
    y = len(matrix) - 2
    for x in range(1, len(matrix[-1])):    
        if not (x, y) in visited:
            visited.append((x, y))
            lines += f"f {y*x_per_row + x + index_offset}/{y*x_per_row + x + index_offset} {(y+1)*x_per_row + x + 1 + index_offset}/{(y+1)*x_per_row + x + 1 + index_offset} {(y+1)*x_per_row + x + 2 + index_offset}/{(y+1)*x_per_row + x + 2 + index_offset} {y*x_per_row + x + 1 + index_offset}/{y*x_per_row + x + 1 + index_offset}\n"

    
    
    return lines, visited

def obj_from_grid(obj_path: str, grid: str = default_grid, scale=5.0, extend_to_big=True):
    location = {"x": 0.0, "y": 0.0, "z": 0.0}
    matrix = []
    obj_str = ""
    lines = grid.split("\n")
    dimension = scale*len(lines) - scale
    print(grid)
    
    

    # regions 1-3
    obj_str += f"v {pad} {0.0} {pad + dimension}\n" 
    obj_str += f"v {0.0} {0.0} {pad + dimension}\n"
    obj_str += f"v {-dimension} {0.0} {pad + dimension}\n"
    obj_str += f"v {-(pad + dimension)} {0.0} {pad + dimension}\n" 

    
    #obj_str += f"v {0.0} {0.0} {dimension}\n"
    #obj_str += f"v {dimension} {0.0} {dimension}\n"
    

    

    print("\nVVVVVVVVV\n")
    obj_str += f"v {pad} {0.0} {dimension}\n"
    line = lines[0].split(" ")
    row = []
    
    for x in range(0, len(line)):
        try:
            row.append(float(line[x]))
            obj_str += f"v {-float(x)*scale} {float(line[x])} {dimension}\n"  
        except Exception:
            print(line[x], "is an arifact of the grid. Ignoring...")
    print(line)
    obj_str += f"v {-(pad + dimension)} {0.0} {dimension}\n"
    matrix.append(row)
    for y in range(1, len(lines) -1):
        line = lines[y].split(" ")
        row = []
        
        for x in range(0, len(line)):
            try:
                row.append(float(line[x]))
                obj_str += f"v {-float(x)*scale} {float(line[x])} {dimension - float(y)*scale}\n"  
            except Exception:
                print(line[x], "is an arifact of the grid. Ignoring...")
        print(line)

            
        matrix.append(row)

    obj_str += f"v {pad} {0.0} {0.0}\n"
    line = lines[-1].split(" ")
    row = []
    for x in range(0, len(line)):
        try:
            row.append(float(line[x]))
            obj_str += f"v {-float(x)*scale} {float(line[x])} {0.0}\n"  
        except Exception:
            print(line[x], "is an arifact of the grid. Ignoring...")
    print(line)
    matrix.append(row)
    
    #obj_str += f"v {0.0} {0.0} {0.0}\n"
    #obj_str += f"v {dimension} {0.0} {0.0}\n"
    obj_str += f"v {-(pad + dimension)} {0.0} {0.0}\n"

    obj_str += f"v {pad} {0.0} {-pad}\n"
    obj_str += f"v {0.0} {0.0} {-pad}\n"
    obj_str += f"v {-dimension} {0.0} {-pad}\n"
    obj_str += f"v {-(pad + dimension)} {0.0} {-pad}\n"


    print("\nVVVVVVVVV\n")
    local_matrix = matrix.copy()
    print(local_matrix) 


    uniform_uv = x / (len(line) - 1) * scale*scale
    big_square_uv = uniform_uv * pad
    sliver_uv = uniform_uv * dimension
    obj_str += f"vt {big_square_uv:.6f} {big_square_uv:.6f}\n"
    obj_str += f"vt {sliver_uv:.6f} {big_square_uv:.6f}\n"
    obj_str += f"vt {big_square_uv:.6f} {big_square_uv:.6f}\n"
    
    

    line = lines[0].split(" ")
    for x in range(0, len(line)):
        u = x / (len(line) - 1) * scale*scale
        v = y / (len(lines) - 1) * scale*scale
        obj_str += f"vt {u:.6f} {v:.6f}\n"
    
    obj_str += f"vt {big_square_uv:.6f} {sliver_uv:.6f}\n"

    for y in range(1, len(lines) -1):
        line = lines[y].split(" ")
        for x in range(0, len(line)):
            try:
                u = x / (len(line) - 1) * scale*scale
                v = y / (len(lines) - 1) * scale*scale
                obj_str += f"vt {u:.6f} {v:.6f}\n"
                
            except Exception:
                print("Could not add vt")    
    
    obj_str += f"vt {big_square_uv:.6f} {sliver_uv:.6f}\n"

    line = lines[-1].split(" ")
    for x in range(0, len(line)):
        u = x / (len(line) - 1) * scale*scale
        v = y / (len(lines) - 1) * scale*scale
        obj_str += f"vt {u:.6f} {v:.6f}\n"

    obj_str += f"vt {big_square_uv:.6f} {big_square_uv:.6f}\n"
    obj_str += f"vt {sliver_uv:.6f} {big_square_uv:.6f}\n"
    obj_str += f"vt {big_square_uv:.6f} {big_square_uv:.6f}\n"


    obj_str1 = obj_str
    face_data, visits = facify(matrix, extended_to_big=extend_to_big)

    obj_str1 += face_data
    print("File contains", len(face_data.split("\n")), "faces.")
    
    if extend_to_big:
        print("\nVVVV extending to inf. VVVV\n")



    
    out_file = "ground"
    out_path1 = obj_path + "/" + out_file + str(random.randint(100, 999)) + ".obj"
    with open(out_path1, "w") as f:
        f.write(obj_str1)
    print("Ground obj written to", out_path1)
    out_path = out_path1
    
    return out_path, local_matrix