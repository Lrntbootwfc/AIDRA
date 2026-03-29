from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from main import run_research # Aapka modular engine call karega

app = FastAPI(title="AIDRA Pharmaceutical Intelligence API")

# ✅ CORS Settings: Taaki Vercel frontend se connection block na ho
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Model
class ResearchRequest(BaseModel):
    molecule: str
    disease: str

@app.get("/")
def health_check():
    return {"status": "Active", "engine": "Llama-3.3-70b-versatile"}

@app.post("/api/research")
async def start_research(request: ResearchRequest):
    """
    Frontend se jab 'Start Research' button dabega, ye trigger hoga.
    """
    try:
        # 1. Engine Run (main.py ka logic call ho raha hai)
        # Note: Llama-3.3-70b versatile quota refill check zaroori hai
        report_output = run_research(request.molecule, request.disease)
        
        # 2. Response Structure for Dashboard
        # Full report string return karega jo Markdown support karta hai
        return {
            "success": True,
            "molecule": request.molecule,
            "disease": request.disease,
            "report_markdown": str(report_output),
            "status": "Completed"
        }
        
    except Exception as e:
        # Agar Groq Rate Limit (429) de, toh frontend ko bata dega
        error_msg = str(e)
        if "429" in error_msg:
            raise HTTPException(status_code=429, detail="Groq Quota Exhausted. Try again in some time.")
        raise HTTPException(status_code=500, detail=error_msg)

# ✅ PDF Download Endpoint (Dashboard ke 'Download' icon ke liye)
@app.get("/api/download-report")
async def download_report(molecule: str):
    # Future: Ismein 'FPDF' library use karke Markdown ko PDF bana sakte hain
    return {"message": f"Generating PDF for {molecule}... Check back in 10 seconds."}

if __name__ == "__main__":
    import uvicorn
    # Local testing ke liye: python app.py
    uvicorn.run(app, host="0.0.0.0", port=8000)