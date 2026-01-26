from fastapi.concurrency import run_in_threadpool

@app.post("/predict")
async def predict_audio(file: UploadFile = File(...)):
    try:
        input_path = os.path.join(TEMP_DIR, "sample.webm")
        output_path = os.path.join(TEMP_DIR, "converted.wav")

        # Save uploaded file (async-safe)
        with open(input_path, "wb") as f:
            f.write(await file.read())

        # ⬇️ Run FFmpeg in threadpool
        await run_in_threadpool(
            subprocess.run,
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

        # ⬇️ Run ML inference in threadpool
        result = await run_in_threadpool(predict, output_path)

        return JSONResponse({
            "status": "ok",
            "result": result
        })

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
