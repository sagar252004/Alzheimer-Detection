async function sendAudio() {

    const fileInput = document.getElementById("audioFile");
    const file = fileInput.files[0];

    if (!file) {
        alert("Please upload an audio file");
        return;
    }

    const formData = new FormData();
    formData.append("file", file);

    document.getElementById("result").innerText = "Analyzing speech...";

    try {

        // call YOUR backend instead of HuggingFace
        const response = await fetch("/predict", {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        if (data.status !== "ok") {
            document.getElementById("result").innerText = "Prediction failed.";
            return;
        }

        const predictionText = data.prediction;

        // show result
        document.getElementById("result").innerText = predictionText;

        // store values for result page + database
        sessionStorage.setItem("prediction", predictionText);
        sessionStorage.setItem("voice_file", data.voice_file);

        console.log("Stored values:", {
            prediction: sessionStorage.getItem("prediction"),
            voice_file: sessionStorage.getItem("voice_file")
        });

    } catch (error) {

        document.getElementById("result").innerText = "Error connecting to server";
        console.error(error);

    }
}