from fastapi import FastAPI, UploadFile, File, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.concurrency import run_in_threadpool
from functools import partial
from database.db import patients_collection
from datetime import datetime

import os
import subprocess
import traceback
import uuid

import cloudinary
import cloudinary.uploader

import os
from dotenv import load_dotenv

load_dotenv()

FFMPEG_PATH = "ffmpeg"

app = FastAPI()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)
# -------------------- FOLDERS --------------------

UPLOAD_DIR = "uploads"
TEMP_DIR = "temp_audio"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# -------------------- STATIC --------------------

app.mount(
    "/static",
    StaticFiles(directory="frontend/static", html=True),
    name="static"
)

# serve saved audio files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

templates = Jinja2Templates(directory="frontend/templates")

# -------------------- ROUTES --------------------

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/audio", response_class=HTMLResponse)
def audio(request: Request):
    return templates.TemplateResponse("audio.html", {"request": request})


# -------------------- SAVE PATIENT --------------------

@app.post("/save_patient")
async def save_patient_api(request: Request):

    data = await request.json()

    patient = {
        "name": data.get("name"),
        "age": data.get("age"),
        "prediction": data.get("prediction"),
        "voice_file": data.get("voice_file"),
        "created_at": datetime.utcnow()
    }

    patients_collection.insert_one(patient)

    return JSONResponse({
        "status": "success",
        "message": "Patient saved successfully"
    })

@app.get("/patients", response_class=HTMLResponse)
def patients_page(request: Request):

    patients = list(patients_collection.find().sort("created_at", -1))

    return templates.TemplateResponse(
        "patients.html",
        {
            "request": request,
            "patients": patients
        }
    )

# -------------------- PREDICT AUDIO --------------------

@app.post("/predict")
async def predict_audio(file: UploadFile = File(...)):

    try:
        uid = str(uuid.uuid4())

        input_path = os.path.join(TEMP_DIR, f"{uid}.webm")
        temp_wav = os.path.join(TEMP_DIR, f"{uid}.wav")

        # save uploaded audio
        with open(input_path, "wb") as f:
            f.write(await file.read())

        # convert webm → wav
        ffmpeg_cmd = [
            FFMPEG_PATH,
            "-y",
            "-i", input_path,
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            temp_wav
        ]

        await run_in_threadpool(
            partial(
                subprocess.run,
                ffmpeg_cmd,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        )

        print("Converted WAV size:", os.path.getsize(temp_wav))

        # --------------------------
        # SEND TO ML MODEL
        # --------------------------
        import requests

        with open(temp_wav, "rb") as audio_file:
            response = requests.post(
                "https://sagarrv252004-alzheimer-detection-api.hf.space/predict",
                files={"file": audio_file}
            )

        model_result = response.json()

        prediction_text = (
            "Classification: " + model_result["classification"] +
            " | MMSE Score: " + str(model_result["mmse_score"])
        )

        # --------------------------
        # UPLOAD TO CLOUDINARY
        # --------------------------
        upload_result = cloudinary.uploader.upload(
            temp_wav,
            resource_type="auto"
        )

        audio_url = upload_result["secure_url"]

        # cleanup
        os.remove(input_path)
        os.remove(temp_wav)

        return JSONResponse({
            "status": "ok",
            "prediction": prediction_text,
            "voice_file": audio_url
        })

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
# -------------------- RESULT PAGE --------------------

@app.get("/result", response_class=HTMLResponse)
def result(request: Request):
    return templates.TemplateResponse(
        "result.html",
        {"request": request}
    )


# -------------------- SERVER --------------------

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)