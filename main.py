import os
import tempfile
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from src.parser import DXFParser
from src.cleaner import GeometryCleaner
from src.decomposer import GeometricDecomposer
import uvicorn

app = FastAPI(title="FLAC3D DXF Compiler API")

# Mount the static folder to serve the frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    with open("static/index.html", "r") as f:
        return f.read()

@app.post("/api/process-dxf")
async def process_dxf(file: UploadFile = File(...)):
    # Save the uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as temp_file:
        temp_file.write(await file.read())
        temp_path = temp_file.name

    try:
        # Parse and process
        raw_lines = DXFParser.extract_lines(temp_path)
        regions = GeometryCleaner.assemble_regions(raw_lines)
        
        if not regions:
            return {"error": "No valid closed geometric profiles mapped."}

        decomposer = GeometricDecomposer()
        all_elements = []

        for region_poly in regions:
            elements = decomposer.process_polygon(region_poly)
            all_elements.extend(elements)
            
        return {"elements": all_elements}
    
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)

if __name__ == "__main__":
    print("Starting server at http://127.0.0.1:8000")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)