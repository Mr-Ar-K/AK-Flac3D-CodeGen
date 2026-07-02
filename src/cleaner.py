from shapely.geometry import Polygon
from shapely.ops import polygonize, unary_union
from config.settings import GEOM_TOLERANCE

class GeometryCleaner:
    """Cleans up messy linear networks and joins them into logical closed regions."""
    
    @staticmethod
    def assemble_regions(lines: list) -> list:
        if not lines:
            return []
        unified_lines = unary_union(lines)
        polygons = list(polygonize(unified_lines))
        return polygons