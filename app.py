from fastapi import FastAPI, UploadFile, File, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.concurrency import run_in_threadpool
from functools import partial
import os
import subprocess
import traceback
import uuid
import requests
FFMPEG_PATH = "ffmpeg"

app = FastAPI()

# Static & templates
# app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
app.mount(
    "/static",
    StaticFiles(directory="frontend/static", html=True),
    name="static"
)

templates = Jinja2Templates(directory="frontend/templates")

# Temp directory
TEMP_DIR = "temp_audio"
os.makedirs(TEMP_DIR, exist_ok=True)


# -------------------- ROUTES --------------------

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/audio", response_class=HTMLResponse)
def audio(request: Request):
    return templates.TemplateResponse("audio.html", {"request": request})


#@app.post("/predict")
# async def predict_audio(file: UploadFile = File(...)):
#     try:
#         # input_path = os.path.join(TEMP_DIR, "sample.webm")
#         # output_path = os.path.join(TEMP_DIR, "converted.wav")
#         uid = str(uuid.uuid4())
#         input_path = os.path.join(TEMP_DIR, f"{uid}.webm")
#         output_path = os.path.join(TEMP_DIR, f"{uid}.wav")
#         with open(input_path, "wb") as f:
#             f.write(await file.read())

#         # ✅ FIXED: use partial for kwargs
#         # ffmpeg_cmd = [
#         #     FFMPEG_PATH,
#         #     "-y",
#         #     "-i", input_path,
#         #     "-ar", "16000",
#         #     "-ac", "1",
#         #     output_path
#         # ]
#         ffmpeg_cmd = [
#             FFMPEG_PATH,
#             "-y",
#             "-i", input_path,

#             # 🔥 force PCM
#             "-acodec", "pcm_s16le",
#             "-ar", "16000",
#             "-ac", "1",

#             # 🔥 loudness normalize to speech level
#             "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",

#             output_path
# ]
#         # await run_in_threadpool(
#         #     partial(subprocess.run, ffmpeg_cmd, check=True)
#         # )
#         await run_in_threadpool(
#             partial(
#                 subprocess.run,
#                 ffmpeg_cmd,
#                 check=True,
#                 stdout=subprocess.DEVNULL,
#                 stderr=subprocess.DEVNULL
#             )
#         )
#         print("Converted WAV size:", os.path.getsize(output_path))

#         # ✅ FIXED: ML inference also wrapped correctly
#         result = await run_in_threadpool(
#             partial(predict, output_path)
#         )
#         # 🧹 cleanup temp files
#         if os.path.exists(input_path):
#             os.remove(input_path)

#         if os.path.exists(output_path):
#             os.remove(output_path)

#         return JSONResponse({
#             "status": "ok",
#             "result": result
#         })

#     except Exception as e:
#         traceback.print_exc()
#         raise HTTPException(status_code=500, detail=str(e))

GCP_SERVER = "http://YOUR_GCP_EXTERNAL_IP:8000/predict"

@app.post("/predict")
async def predict_audio(file: UploadFile = File(...)):
    try:
        uid = str(uuid.uuid4())
        input_path = os.path.join(TEMP_DIR, f"{uid}.webm")
        output_path = os.path.join(TEMP_DIR, f"{uid}.wav")

        # save uploaded audio
        with open(input_path, "wb") as f:
            f.write(await file.read())

        # convert webm → wav (this part is SAFE on Render)
        ffmpeg_cmd = [
            FFMPEG_PATH,
            "-y",
            "-i", input_path,
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            output_path
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
        print("Converted WAV size:", os.path.getsize(output_path))
        # 🔥 send WAV to GCP ML server instead of predicting locally
        with open(output_path, "rb") as audio_file:
            response = requests.post(
            GCP_SERVER,
            files={"file": ("audio.wav", audio_file, "audio/wav")},
            timeout=300
            )
        result = response.json()["prediction"]
        os.remove(input_path)
        os.remove(output_path)

        return JSONResponse({
            "status": "ok",
            "result": result
        })

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/result", response_class=HTMLResponse)
def result(request: Request):
    """
    Result page.
    Data is rendered via JS using sessionStorage.
    """
    return templates.TemplateResponse(
        "result.html",
        {"request": request}
    )
# -------------------- SERVER --------------------

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)
