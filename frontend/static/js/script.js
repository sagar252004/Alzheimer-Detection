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

        const response = await 
            fetch("https://sagarrv252004-alzheimer-detection-api.hf.space/predict", {
            // fetch("https://sagarrv252004-alzheimer-detection-api.hf.space/gradio_api/predict", {
                method: "POST",
                body: formData
            }
        );

        const data = await response.json();

        document.getElementById("result").innerText =
            "Classification: " + data.classification +
            " | MMSE Score: " + data.mmse_score;

    } catch (error) {
        document.getElementById("result").innerText = "Error connecting to API";
        console.error(error);
    }
}
