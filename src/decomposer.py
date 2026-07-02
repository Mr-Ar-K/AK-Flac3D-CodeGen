from shapely.geometry import Polygon, box, MultiPolygon
from shapely.ops import unary_union
from config.settings import GEOM_TOLERANCE

class GeometricDecomposer:
    """Decomposes complex closed polygon structures into primitive shapes."""

    def __init__(self):
        self.tolerance = GEOM_TOLERANCE

    def process_polygon(self, polygon: Polygon) -> list:
        elements = []
        exterior_coords = list(polygon.exterior.coords)
        sloped_triangles = []
        orthogonal_pieces = polygon
        
        # 1. Identify and cut out sloped corners (Right Triangles)
        for i in range(len(exterior_coords) - 1):
            p1 = exterior_coords[i]
            p2 = exterior_coords[i+1]
            
            # If line segment is diagonal/sloped
            if abs(p1[0] - p2[0]) > self.tolerance and abs(p1[1] - p2[1]) > self.tolerance:
                v1 = (p1[0], p2[1])
                v2 = (p2[0], p1[1])
                
                for corner in [v1, v2]:
                    tri = Polygon([p1, p2, corner])
                    if polygon.contains(tri.buffer(-self.tolerance)):
                        sloped_triangles.append(tri)
                        orthogonal_pieces = orthogonal_pieces.difference(tri)
                        break

        # 2. Segment remaining axis-aligned geometries
        if orthogonal_pieces.is_empty:
            orthogonal_polys = []
        elif isinstance(orthogonal_pieces, MultiPolygon):
            orthogonal_polys = list(orthogonal_pieces.geoms)
        else:
            orthogonal_polys = [orthogonal_pieces]

        rectangles_and_squares = []
        
        for poly in orthogonal_polys:
            x_lines = sorted(list(set([round(pt[0], 5) for pt in poly.exterior.coords])))
            y_lines = sorted(list(set([round(pt[1], 5) for pt in poly.exterior.coords])))
            
            raw_cells = []
            for i in range(len(x_lines) - 1):
                for j in range(len(y_lines) - 1):
                    cell = box(x_lines[i], y_lines[j], x_lines[i+1], y_lines[j+1])
                    if poly.contains(cell.buffer(-self.tolerance)):
                        raw_cells.append(cell)
            
            merged_rects = self._merge_cells(raw_cells)
            rectangles_and_squares.extend(merged_rects)

        # 3. Format Rectangles and Squares
        for rect in rectangles_and_squares:
            minx, miny, maxx, maxy = rect.bounds
            w, h = maxx - minx, maxy - miny
            el_type = "Square" if abs(w - h) < self.tolerance else "Rectangle"
            
            coords = [(minx, miny), (maxx, miny), (maxx, maxy), (minx, maxy)]
            elements.append({"type": el_type, "coordinates": coords})
            
        # 4. Format Triangles
        for tri in sloped_triangles:
            coords = list(tri.exterior.coords)[:-1]
            elements.append({"type": "Right Triangle", "coordinates": coords})

        return elements

    def _merge_cells(self, cells):
        unprocessed = list(cells)
        merged = []
        
        while unprocessed:
            current = unprocessed.pop(0)
            extended = True
            while extended:
                extended = False
                minx, miny, maxx, maxy = current.bounds
                w, h = maxx - minx, maxy - miny
                
                r_neighbor = box(maxx, miny, maxx + w, maxy)
                match = [c for c in unprocessed if c.equals(r_neighbor)]
                if match:
                    current = unary_union([current, match[0]])
                    unprocessed.remove(match[0])
                    extended = True
                    continue
                    
                u_neighbor = box(minx, maxy, maxx, maxy + h)
                match = [c for c in unprocessed if c.equals(u_neighbor)]
                if match:
                    current = unary_union([current, match[0]])
                    unprocessed.remove(match[0])
                    extended = True
            merged.append(current)
        return merged