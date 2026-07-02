from shapely.geometry import box, Polygon
from config.settings import TOLERANCE

def decompose_shape(poly):
    """
    Slices the polygon using a dense orthogonal grid.
    Uses Template Matching to explicitly force all partial cells into 
    perfect 90-degree Right Triangles locked to the grid corners.
    This guarantees 100% conformal meshes with zero T-junction errors in FLAC3D.
    """
    poly = poly.buffer(0) # Clean any self-intersections from CAD
    
    # 1. Collect all initial X and Y vertices
    coords = list(poly.exterior.coords)
    for interior in poly.interiors:
        coords.extend(list(interior.coords))

    xs = set([round(p[0], 5) for p in coords])
    ys = set([round(p[1], 5) for p in coords])

    # 2. Extract sloped line segments
    sloped_lines = []
    for i in range(len(coords)-1):
        p1, p2 = coords[i], coords[i+1]
        if abs(p1[0]-p2[0]) > TOLERANCE and abs(p1[1]-p2[1]) > TOLERANCE:
            sloped_lines.append((p1, p2))

    # 3. Dense Grid Generation
    changed = True
    while changed:
        changed = False
        new_xs, new_ys = set(), set()

        for p1, p2 in sloped_lines:
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            m = dy / dx
            c = p1[1] - m * p1[0]

            for x in xs:
                if min(p1[0], p2[0]) + TOLERANCE < x < max(p1[0], p2[0]) - TOLERANCE:
                    y = round(m * x + c, 5)
                    if y not in ys and y not in new_ys:
                        new_ys.add(y)
            
            for y in ys:
                if min(p1[1], p2[1]) + TOLERANCE < y < max(p1[1], p2[1]) - TOLERANCE:
                    x = round((y - c) / m, 5)
                    if x not in xs and x not in new_xs:
                        new_xs.add(x)
                        
        if new_xs or new_ys:
            xs.update(new_xs)
            ys.update(new_ys)
            changed = True

    x_list = sorted(list(xs))
    y_list = sorted(list(ys))

    small_rects = []
    small_tris = []

    # 4. Template-Matching Cell Extraction
    for i in range(len(x_list)-1):
        for j in range(len(y_list)-1):
            x1, x2 = x_list[i], x_list[i+1]
            y1, y2 = y_list[j], y_list[j+1]
            
            # Skip invalid/tiny grid cells
            if x2 - x1 < TOLERANCE or y2 - y1 < TOLERANCE:
                continue

            cell = box(x1, y1, x2, y2)
            inter_area = poly.intersection(cell).area

            if inter_area < 1e-7:
                continue

            # If it perfectly fills the cell, it is a pure Rectangle
            if inter_area > 0.99 * cell.area:
                small_rects.append(cell)
            
            # If partially filled, we FORCE it to be one of 4 exact Right Triangles
            else:
                BL, BR = (x1, y1), (x2, y1)
                TR, TL = (x2, y2), (x1, y2)
                
                # The 4 mathematically perfect 90-degree right triangles for this cell
                T1 = Polygon([BL, BR, TR]) # Bottom-Right half
                T2 = Polygon([BL, TL, TR]) # Top-Left half
                T3 = Polygon([BL, BR, TL]) # Bottom-Left half
                T4 = Polygon([BR, TR, TL]) # Top-Right half
                
                best_T = None
                max_inter = 0
                
                # Find which perfect triangle actually represents the CAD geometry
                for T in [T1, T2, T3, T4]:
                    a = poly.intersection(T).area
                    if a > max_inter:
                        max_inter = a
                        best_T = T
                        
                # Append the mathematically perfect triangle, sidestepping floating point anomalies
                if best_T and max_inter > 0.90 * best_T.area:
                    small_tris.append(best_T)

    # Return the perfectly aligned small blocks without merging them
    return small_rects, small_tris