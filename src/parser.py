import ezdxf
from shapely.geometry import LineString
from config.settings import SUPPORTED_ENTITIES

class DXFParser:
    @staticmethod
    def extract_lines(dxf_path: str) -> list:
        try:
            doc = ezdxf.readfile(dxf_path)
        except Exception as e:
            raise ValueError(f"Corrupted or invalid DXF file: {str(e)}")

        msp = doc.modelspace()
        lines = []

        if 'LINE' in SUPPORTED_ENTITIES:
            for e in msp.query('LINE'):
                start = (e.dxf.start.x, e.dxf.start.y)
                end = (e.dxf.end.x, e.dxf.end.y)
                if start != end:
                    lines.append(LineString([start, end]))

        if 'LWPOLYLINE' in SUPPORTED_ENTITIES or 'POLYLINE' in SUPPORTED_ENTITIES:
            for e in msp.query('LWPOLYLINE POLYLINE'):
                points = [(pt[0], pt[1]) for pt in e.points()]
                if len(points) >= 2:
                    lines.append(LineString(points))

        return lines