from fastapi import FastAPI
from pydantic import BaseModel
from .ensemble_gender import ensemble_gender

app = FastAPI(title="Gender Detection Service")

class GenderRequest(BaseModel):
    text: str
    character: str

@app.post("/detect-gender/")
def detect_gender(req: GenderRequest):
    gender, confidence = ensemble_gender(req.text, req.character)

    return {
        "gender": gender,
        "confidence": confidence
    }

