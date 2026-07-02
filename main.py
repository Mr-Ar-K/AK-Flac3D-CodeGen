import os
import sys
from src.parser import DXFParser
from src.cleaner import GeometryCleaner
from src.decomposer import GeometricDecomposer

def main():
    # Looks for a file named "input.dxf" in the current active working directory
    dxf_filename = "input.dxf"
    
    if not os.path.exists(dxf_filename):
        print(f"Error: '{dxf_filename}' not found in root workspace direction.")
        print("Please place your target drawing file here or modify main.py.")
        sys.exit(1)
        
    print(f"Parsing drawing profile data from: {dxf_filename}")
    raw_lines = DXFParser.extract_lines(dxf_filename)
    
    regions = GeometryCleaner.assemble_regions(raw_lines)
    if not regions:
        print("Processing stopped: No valid closed shapes could be mapped.")
        return

    decomposer = GeometricDecomposer()
    element_global_id = 1

    print(f"Discovered {len(regions)} closed geometric profiles.\n")

    for region_idx, region_poly in enumerate(regions, start=1):
        elements = decomposer.process_polygon(region_poly)
        
        for element in elements:
            # Custom clean text formatting: bracket-less presentation style
            print(f"Element {element_global_id}")
            print(f"Type: {element['type']}")
            print("Coordinates:")
            for x, y in element['coordinates']:
                print(f"  {round(x, 4)} {round(y, 4)}")
            print("-" * 30)
            element_global_id += 1

if __name__ == "__main__":
    main()