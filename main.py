import os
from src.parser import extract_polygons
from src.mesher import decompose_shape
from src.exporter import export_to_fish

def main():
    dxf_file = "input.dxf"
    
    if not os.path.exists(dxf_file):
        print(f"Error: {dxf_file} not found.")
        return

    print("Parsing DXF...")
    polygons = extract_polygons(dxf_file)
    
    all_rects = []
    all_tris = []
    
    print("Decomposing mesh and mapping constraints...")
    for poly in polygons:
        rects, tris = decompose_shape(poly)
        all_rects.extend(rects)
        all_tris.extend(tris)

    print("Writing FISH data file...")
    bricks, wedges = export_to_fish(all_rects, all_tris)
    
    print(f"Success! Generated mesh.f3dat with {bricks} bricks and {wedges} wedges.")

if __name__ == "__main__":
    main()