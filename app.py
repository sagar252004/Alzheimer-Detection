from fastapi import FastAPI, UploadFile, File, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import subprocess
import traceback

from main import predict

FFMPEG_PATH = "ffmpeg"

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
        input_path = os.path.join(TEMP_DIR, file.filename)
        output_path = os.path.join(TEMP_DIR, "converted.wav")

        with open(input_path, "wb") as f:
            f.write(await file.read())

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

        result = predict(output_path)
        LAST_RESULT.clear()
        LAST_RESULT.update(result)

        return JSONResponse({"status": "ok"})

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/result", response_class=HTMLResponse)
def result(request: Request):
    if not LAST_RESULT:
        return templates.TemplateResponse(
            "result.html",
            {
                "request": request,
                "result": None,
                "message": "No prediction yet. Please upload audio first."
            }
        )

    return templates.TemplateResponse(
        "result.html",
        {
            "request": request,
            "result": LAST_RESULT,
            "message": None
        }
    )
