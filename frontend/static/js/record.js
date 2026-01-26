let mediaRecorder;
let audioChunks = [];

const startBtn = document.getElementById("start");
const stopBtn = document.getElementById("stop");
const statusText = document.getElementById("status");

startBtn.onclick = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

    // IMPORTANT: do NOT force wav here
    mediaRecorder = new MediaRecorder(stream, {
      mimeType: "audio/webm"
    });

    audioChunks = [];

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunks.push(event.data);
      }
    };

    mediaRecorder.onstop = async () => {
      // Browser gives WEBM, not WAV
      const audioBlob = new Blob(audioChunks, { type: "audio/webm" });

      const formData = new FormData();
      formData.append("file", audioBlob, "sample.webm");

      // statusText.innerText = "Processing audio...";

      // await fetch("/predict", {
      //   method: "POST",
      //   body: formData
      // });

      // window.location.href = "/result";
      
      statusText.innerText = "Processing audio...";

      fetch("/predict", {
        method: "POST",
        body: formData
      })
      .then(res => {
        if (!res.ok) throw new Error("Prediction failed");
        return res.json();
      })
      .then(() => {
        window.location.href = "/result";
      })
      .catch(err => {
        console.error(err);
        statusText.innerText = "Prediction failed. Try again.";
      });

    };

    mediaRecorder.start();
    statusText.innerText = "Recording...";
    startBtn.disabled = true;
    stopBtn.disabled = false;

  } catch (err) {
    alert("Microphone access denied");
    console.error(err);
  }
};

stopBtn.onclick = () => {
  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    mediaRecorder.stop();
    stopBtn.disabled = true;
  }
};
