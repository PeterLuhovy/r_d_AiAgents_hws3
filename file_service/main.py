

import os
import time

from pathlib import Path
from fastapi import FastAPI, HTTPException
from typing import Dict, Any, List
import base64
from pdf2image import convert_from_path # type: ignore
from io import BytesIO
from PIL import Image


app = FastAPI(title="PDF File Manager", version="1.0.0")

# Cesta k zložke s PDF súbormi (bude mount z Docker)
ENV_FILES_PATH = os.getenv("ENV_FILES_PATH", "/app/files")
FILES_PATH = Path(ENV_FILES_PATH)

@app.get("/")
async def root():
    return {"message": "PDF File Manager API"}

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    files_exist = FILES_PATH.exists()
    return {
        "timestamp": time.time(),
        "status": "healthy",
        "service": "PDF File Manager",
        "version": "0.1.0",
        "files_path": str(FILES_PATH),
        "files_path_exists": files_exist
    }

@app.get("/files")
async def list_files() -> Dict[str, Any]:
    """Zoznam všetkých súborov v zložke"""
    try:
        if not FILES_PATH.exists():
            raise HTTPException(status_code=404, detail="Files directory not found")
        
        files = [f.name for f in FILES_PATH.iterdir() if f.is_file()]
        return {"files": files, "count": len(files)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/process-file")
async def process_next_pdf():
    """Zoberie prvý PDF súbor (bez raw_ prefixu), skonvertuje na JPG a premenuje pôvodný"""
    try:
        if not FILES_PATH.exists():
            raise HTTPException(status_code=404, detail="Files directory not found")
        
        # Nájdi prvý PDF súbor bez raw_ prefixu
        files: List[Path] = [f for f in FILES_PATH.iterdir() if f.is_file() and f.name.lower().endswith('.pdf') and not f.name.startswith('raw_')]
        
        if not files:
            return {"message": "no files to process"}
        
        # Zoradí a vezmi prvý
        file = sorted(files)[0]
        original_name = file.name
 
        # Konverzia PDF na JPG
        images: List[Any] = convert_from_path(str(file))

        if not images:
            raise HTTPException(status_code=500, detail="Could not convert PDF to image")

        # Spoj všetky stránky do jedného obrázka (vertikálne)
        if len(images) > 1:
            # Spočítaj celkovú výšku a najväčšiu šírku
            total_height = sum(img.height for img in images)
            max_width = max(img.width for img in images)

            # Vytvor nový obrázok
            combined = Image.new('RGB', (max_width, total_height), 'white')

            # Vlož stránky pod seba
            y_offset = 0
            for img in images:
                combined.paste(img, (0, y_offset))
                y_offset += img.height

            final_image = combined
        else:
            # Iba jedna stránka
            final_image = images[0]
        
        # Konverzia na base64
        buffer = BytesIO()
        final_image.save(buffer, format='JPEG', quality=95)
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        # Premenuj pôvodný PDF s prefixom raw_
        raw_filename = f"raw_{original_name}"
        raw_path = FILES_PATH / raw_filename
        file.rename(raw_path)
        
        return {
            "original_filename": original_name,
            "raw_filename": raw_filename,
            "base64": img_base64,
            "format": "jpeg"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))