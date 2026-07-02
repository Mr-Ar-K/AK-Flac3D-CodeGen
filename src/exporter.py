from config.settings import Y_DEPTH, GRID_SIZE

def point3(x, y, z):
    return f"({x:.4f}, {y:.4f}, {z:.4f})"

def export_to_fish(rects, tris, output_file="mesh.f3dat"):
    out = ["model new", "model largestrain off", "", "; --- Block Definitions ---"]
    b_id, w_id = 1, 1
    ny = max(1, round(Y_DEPTH / GRID_SIZE))
    
    # Process Rectangles (Bricks)
    for r in rects:
        pts = list(r.exterior.coords)
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        xmin, xmax, zmin, zmax = min(xs), max(xs), min(ys), max(ys)
        nx, nz = max(1, round((xmax - xmin) / GRID_SIZE)), max(1, round((zmax - zmin) / GRID_SIZE))
        
        out.append("zone create brick ...")
        out.append(f"    point 0 {point3(xmin, 0, zmin)} ...")
        out.append(f"    point 1 {point3(xmax, 0, zmin)} ...")
        out.append(f"    point 2 {point3(xmin, Y_DEPTH, zmin)} ...")
        out.append(f"    point 3 {point3(xmin, 0, zmax)} ...")
        out.append(f"    size ({nx},{ny},{nz}) group 'brick_{b_id}'\n")
        b_id += 1

    # Process Triangles (Uniform Wedges)
    for t in tris:
        pts = list(t.exterior.coords)[:-1]
        
        # 1. Find the corner closest to 90 degrees to act as P0 (Origin)
        # uniform-wedge strictly expects P0 to be the right-angle corner
        best_corner = 0
        min_dot = float('inf')
        
        for i in range(3):
            p_curr = pts[i]
            p_next = pts[(i+1)%3]
            p_prev = pts[(i-1)%3]
            
            # Vectors from current point
            v1 = (p_next[0] - p_curr[0], p_next[1] - p_curr[1])
            v2 = (p_prev[0] - p_curr[0], p_prev[1] - p_curr[1])
            
            # Normalize to find the angle (dot product)
            l1 = (v1[0]**2 + v1[1]**2)**0.5
            l2 = (v2[0]**2 + v2[1]**2)**0.5
            if l1 == 0 or l2 == 0: continue
            
            dot = abs((v1[0]*v2[0] + v1[1]*v2[1]) / (l1 * l2))
            if dot < min_dot:
                min_dot = dot
                best_corner = i
                
        # 2. Reorder points so P0 is the 90-degree corner
        P0_2d = pts[best_corner]
        P1_2d = pts[(best_corner + 1) % 3]
        P3_2d = pts[(best_corner + 2) % 3]
        
        # 3. Enforce Counter-Clockwise (CCW) orientation for valid FLAC3D volumes
        cross = (P1_2d[0] - P0_2d[0]) * (P3_2d[1] - P0_2d[1]) - (P1_2d[1] - P0_2d[1]) * (P3_2d[0] - P0_2d[0])
        if cross < 0:
            P1_2d, P3_2d = P3_2d, P1_2d

        # 4. Map to FLAC3D uniform-wedge axes 
        P0 = (P0_2d[0], 0, P0_2d[1])                 # Origin Corner
        P1 = (P1_2d[0], 0, P1_2d[1])                 # S1 Axis Leg
        P2 = (P0_2d[0], Y_DEPTH, P0_2d[1])           # S2 Axis (Depth Extrusion)
        P3 = (P3_2d[0], 0, P3_2d[1])                 # S3 Axis Leg
        P4 = (P1_2d[0], Y_DEPTH, P1_2d[1])           # Extrusion of P1
        P5 = (P3_2d[0], Y_DEPTH, P3_2d[1])           # Extrusion of P3
        
        # Determine logical subdivision grid sizing for the wedge sides
        n1 = max(1, round(((P1_2d[0]-P0_2d[0])**2 + (P1_2d[1]-P0_2d[1])**2)**0.5 / GRID_SIZE))
        n3 = max(1, round(((P3_2d[0]-P0_2d[0])**2 + (P3_2d[1]-P0_2d[1])**2)**0.5 / GRID_SIZE))

        # 5. Output strictly as uniform-wedge
        out.append("zone create uniform-wedge ...")
        out.append(f"    point 0 {point3(*P0)} ...")
        out.append(f"    point 1 {point3(*P1)} ...")
        out.append(f"    point 2 {point3(*P2)} ...")
        out.append(f"    point 3 {point3(*P3)} ...")
        out.append(f"    point 4 {point3(*P4)} ...")
        out.append(f"    point 5 {point3(*P5)} ...")
        out.append(f"    size ({n1},{ny},{n3}) group 'slope_{w_id}'\n")
        w_id += 1

    out.append("; --- Unify and Merge Nodes ---")
    out.append("zone gridpoint merge")
    
    with open(output_file, "w") as f:
        f.write("\n".join(out))
    
    return b_id - 1, w_id - 1