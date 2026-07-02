import sys
import ezdxf
from shapely.geometry import LineString
from config.settings import SUPPORTED_ENTITIES

class DXFParser:
    """Handles loading and extracting basic line geometries from DXF files."""
    
    @staticmethod
    def extract_lines(dxf_path: str) -> list:
        try:
            doc = ezdxf.readfile(dxf_path)
        except IOError:
            print(f"Error: Unable to open or locate file at '{dxf_path}'")
            sys.exit(1)
        except ezdxf.DXFStructureError:
            print(f"Error: Corrupted or invalid DXF file structure structure.")
            sys.exit(1)

        msp = doc.modelspace()
        lines = []

        # Extract basic LINE structures
        if 'LINE' in SUPPORTED_ENTITIES:
            for e in msp.query('LINE'):
                start = (e.dxf.start.x, e.dxf.start.y)
                end = (e.dxf.end.x, e.dxf.end.y)
                if start != end:
                    lines.append(LineString([start, end]))

        # Extract standard closed/open polylines
        if 'LWPOLYLINE' in SUPPORTED_ENTITIES or 'POLYLINE' in SUPPORTED_ENTITIES:
            for e in msp.query('LWPOLYLINE POLYLINE'):
                points = [(pt[0], pt[1]) for pt in e.points()]
                if len(points) >= 2:
                    lines.append(LineString(points))

        return lines