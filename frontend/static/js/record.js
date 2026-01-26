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

mediaRecorder.onstop = () => {
  const audioBlob = new Blob(audioChunks, { type: "audio/webm" });

  const formData = new FormData();
  formData.append("file", audioBlob, "sample.webm");

  statusText.innerText = "Processing audio...";

  fetch("/predict", {
    method: "POST",
    body: formData
  })
    .then(async (res) => {
      console.log("Predict response status:", res.status);

      const text = await res.text(); // 🔥 FORCE READ RESPONSE
      console.log("Raw response:", text);

      const data = JSON.parse(text);

      if (data.status === "ok") {
        sessionStorage.setItem("result", JSON.stringify(data.result));
        window.location.href = "/result";
      } else {
        statusText.innerText = "Prediction failed";
      }
    })
    .catch((err) => {
      console.error("Predict error:", err);
      statusText.innerText = "Server error";
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
