let mediaRecorder;
let audioChunks = [];

const startBtn = document.getElementById("start");
const stopBtn = document.getElementById("stop");
const statusText = document.getElementById("status");
const MIN_SECONDS = 30;

let timerInterval;
let secondsElapsed = 0;

const timerText = document.getElementById("timer");

function startTimer() {
  secondsElapsed = 0;
  timerText.innerText = "00:00";

  stopBtn.disabled = true; // ⛔ disable Stop initially

  timerInterval = setInterval(() => {
    secondsElapsed++;
    const mins = String(Math.floor(secondsElapsed / 60)).padStart(2, "0");
    const secs = String(secondsElapsed % 60).padStart(2, "0");
    timerText.innerText = `${mins}:${secs}`;

    // ✅ Enable Stop after 30 sec
    if (secondsElapsed === MIN_SECONDS) {
      stopBtn.disabled = false;
      statusText.innerText = "✅ You can stop recording now";
    }
  }, 1000);
}

function stopTimer() {
  clearInterval(timerInterval);
}

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
  // stopTimer();
  // const audioBlob = new Blob(audioChunks, { type: "audio/webm" });

  stopTimer();

  // ⛔ Minimum 30-second validation
  if (secondsElapsed < MIN_SECONDS) {
    statusText.innerText =
      `Recording too short ❌ Please record at least ${MIN_SECONDS} seconds.`;

    audioChunks = [];          // discard audio
    startBtn.disabled = false; // allow retry
    stopBtn.disabled = true;
    return;                    // ❌ DO NOT PROCESS
  }

  // ✅ Continue normally if >= 30 sec
  const audioBlob = new Blob(audioChunks, { type: "audio/webm" });

  const formData = new FormData();
  formData.append("file", audioBlob, "sample.webm");

  statusText.innerText = "Processing audio...";

  // fetch("/predict", {
  //   method: "POST",
  //   body: formData
  // })
  //   .then(async (res) => {
  //     console.log("Predict response status:", res.status);

  //     const text = await res.text(); // 🔥 FORCE READ RESPONSE
  //     console.log("Raw response:", text);

  //     const data = JSON.parse(text);

  //     if (data.status === "ok") {
  //       sessionStorage.setItem("result", JSON.stringify(data.result));
  //       window.location.href = "/result";
  //     } else {
  //       statusText.innerText = "Prediction failed";
  //     }
  //   // })
//   fetch("https://sagarrv252004-alzheimer-detection-api.hf.space/predict", {
//   // fetch("https://sagarrv252004-alzheimer-detection-api.hf.space/gradio_api/predict", {
//   method: "POST",
//   body: formData
// })
  fetch("/predict", {
    method: "POST",
    body: formData
})
.then(async (res) => {

  const data = await res.json();

  console.log("Prediction response:", data);

  if (data.status !== "ok") {
    statusText.innerText = "Prediction failed. Please try again.";
    return;
  }

  // store prediction
  sessionStorage.setItem("prediction", data.prediction);

  // store audio URL from backend (Cloudinary)
  sessionStorage.setItem("voice_file", data.voice_file);

  window.location.href = "/result";
})
.catch(err => {
  console.error(err);
  statusText.innerText = "Server error while processing audio.";
});

      // .catch((err) => {
      //   console.error("Predict error:", err);
      //   statusText.innerText = "Server error";
      // });
};

    mediaRecorder.start();
    startTimer();

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
