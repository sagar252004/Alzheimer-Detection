from fastapi import FastAPI, UploadFile, File, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import subprocess
import traceback

from main import predict   # NOW THIS WILL WORK

FFMPEG_PATH = r"C:\Users\Sagar\Downloads\ffmpeg-8.0.1-essentials_build\ffmpeg-8.0.1-essentials_build\bin\ffmpeg.exe"
# FFMPEG_PATH = r"C:\Users\Sagar\Downloads\ffmpeg-8.0.1-essentials_build\bin\ffmpeg.exe"
FFPLAY_PATH = r"C:\Users\Sagar\Downloads\ffmpeg-8.0.1-essentials_build\ffmpeg-8.0.1-essentials_build\bin\ffplay.exe"
FFPROBE_PATH = r"C:\Users\Sagar\Downloads\ffmpeg-8.0.1-essentials_build\ffmpeg-8.0.1-essentials_build\bin\ffprobe.exe"
app = FastAPI()

app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
templates = Jinja2Templates(directory="frontend/templates")

TEMP_DIR = "temp_audio"
os.makedirs(TEMP_DIR, exist_ok=True)

LAST_RESULT = {}


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/audio", response_class=HTMLResponse)
def audio(request: Request):
    return templates.TemplateResponse("audio.html", {"request": request})


@app.post("/predict")
async def predict_audio(file: UploadFile = File(...)):
    try:
        print("==== PREDICT STARTED ====")

        input_path = os.path.join(TEMP_DIR, file.filename)
        output_path = os.path.join(TEMP_DIR, "converted.wav")

        print("Input path:", input_path)
        print("Output path:", output_path)
        print("FFMPEG PATH:", FFMPEG_PATH)

        # Save uploaded file
        with open(input_path, "wb") as f:
            f.write(await file.read())

        print("File saved. Exists?", os.path.exists(input_path))

        # Run ffmpeg
        subprocess.run(
            [
                FFMPEG_PATH,
                "-y",
                "-i", input_path,
                "-ar", "16000",
                "-ac", "1",
                output_path
            ],
            check=True
        )

        print("FFmpeg done. Output exists?", os.path.exists(output_path))

        # Run ML
        result = predict(output_path)
        print("Prediction result:", result)

        LAST_RESULT.update(result)

        return JSONResponse({"status": "ok"})

    except Exception as e:
        print("==== ERROR IN /predict ====")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/result", response_class=HTMLResponse)
def result(request: Request):
    return templates.TemplateResponse(
        "result.html",
        {
            "request": request,
            "result": LAST_RESULT
        }
    )

