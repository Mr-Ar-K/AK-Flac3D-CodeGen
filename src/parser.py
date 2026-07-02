import ezdxf
from shapely.geometry import LineString
from shapely.ops import unary_union, polygonize
from config.settings import SUPPORTED_ENTITIES

def extract_polygons(dxf_path):
    """Extracts raw lines from DXF and assembles them into closed polygons."""
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()
    lines = []
    
    for e in msp.query('LINE'):
        lines.append(LineString([(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]))
    
    if any(ent in SUPPORTED_ENTITIES for ent in ['LWPOLYLINE', 'POLYLINE']):
        for e in msp.query('LWPOLYLINE POLYLINE'):
            pts = [(p[0], p[1]) for p in e.points()]
            if len(pts) > 1:
                lines.append(LineString(pts))
                
    merged = unary_union(lines)
    return list(polygonize(merged))