// script.js

const video = document.getElementById("video");
const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");
const startCameraBtn = document.getElementById("startCamera");
const runDetectionBtn = document.getElementById("runDetection");
const captureImageBtn = document.getElementById("captureImage");
const uploadInput = document.getElementById("uploadInput");
const uploadButton = document.getElementById("uploadButton");
const extractedText = document.getElementById("extractedText");
const questionInput = document.getElementById("questionInput");
const askButton = document.getElementById("askButton");
const responseDiv = document.getElementById("response");
const responseText = document.getElementById("responseText");
const loading = document.getElementById("loading");

let stream;
let detectionInterval;

// Start camera
startCameraBtn.addEventListener("click", async () => {
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: true });
    video.srcObject = stream;
    runDetectionBtn.disabled = false;
    captureImageBtn.disabled = false;
  } catch (err) {
    alert("Error accessing camera: " + err.message);
  }
});

// Run YOLO detection on live stream
runDetectionBtn.addEventListener("click", () => {
  if (detectionInterval) {
    clearInterval(detectionInterval);
    detectionInterval = null;
    runDetectionBtn.textContent = "Run YOLO Detection";
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    canvas.style.display = "none";
  } else {
    runDetectionBtn.textContent = "Stop Detection";
    canvas.style.display = "block";
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    detectionInterval = setInterval(detectObjects, 1000); // Detect every second
  }
});

// Detect objects in current frame
async function detectObjects() {
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  ctx.drawImage(video, 0, 0);

  canvas.toBlob(async (blob) => {
    const formData = new FormData();
    formData.append("file", blob, "frame.jpg");

    try {
      const response = await fetch("/detect", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      drawDetections(data.detections);
    } catch (err) {
      console.error("Detection error:", err);
    }
  });
}

// Draw bounding boxes
function drawDetections(detections) {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.drawImage(video, 0, 0);

  ctx.strokeStyle = "red";
  ctx.lineWidth = 2;
  ctx.font = "16px Arial";
  ctx.fillStyle = "red";

  detections.forEach((det) => {
    ctx.strokeRect(det.x1, det.y1, det.x2 - det.x1, det.y2 - det.y1);
    ctx.fillText(
      `${det.name} (${det.confidence.toFixed(2)})`,
      det.x1,
      det.y1 - 5,
    );
  });
}

// Capture image
captureImageBtn.addEventListener("click", async () => {
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  ctx.drawImage(video, 0, 0);

  canvas.toBlob(async (blob) => {
    loading.style.display = "block";
    const formData = new FormData();
    formData.append("file", blob, "capture.jpg");

    try {
      const response = await fetch("/capture", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      extractedText.value = data.text;
    } catch (err) {
      alert("Error capturing image: " + err.message);
    } finally {
      loading.style.display = "none";
    }
  });
});

// Upload image
uploadButton.addEventListener("click", async () => {
  const file = uploadInput.files[0];
  if (!file) {
    alert("Please select an image file.");
    return;
  }

  loading.style.display = "block";
  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch("/upload", {
      method: "POST",
      body: formData,
    });
    const data = await response.json();
    extractedText.value = data.text;
  } catch (err) {
    alert("Error uploading image: " + err.message);
  } finally {
    loading.style.display = "none";
  }
});

// Ask question
askButton.addEventListener("click", async () => {
  const text = extractedText.value;
  const question = questionInput.value;

  if (!text || !question) {
    alert("Please provide both extracted text and a question.");
    return;
  }

  loading.style.display = "block";
  const formData = new FormData();
  formData.append("text", text);
  formData.append("question", question);

  try {
    const response = await fetch("/ask", {
      method: "POST",
      body: formData,
    });
    const data = await response.json();
    responseText.textContent = data.answer;
    responseDiv.style.display = "block";
  } catch (err) {
    alert("Error asking question: " + err.message);
  } finally {
    loading.style.display = "none";
  }
});

let recorder;
let audioChunks = [];

async function startRecording() {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

    recorder = new MediaRecorder(stream);
    audioChunks = [];

    recorder.ondataavailable = e => audioChunks.push(e.data);

    recorder.start();

    setTimeout(() => stopRecording(), 4000); // auto stop after 4 sec
}

async function stopRecording() {
    recorder.stop();

    recorder.onstop = async () => {
        let blob = new Blob(audioChunks, { type: "audio/wav" });

        let formData = new FormData();
        formData.append("file", blob, "speech.wav");

        let response = await fetch("/stt", {
            method: "POST",
            body: formData
        });

        let data = await response.json();

        document.getElementById("questionInput").value = data.transcript;
    };
}

let ws = new WebSocket("ws://localhost:8000/tts");

ws.onmessage = function(event) {
    let audioBase64 = event.data;

    let binary = atob(audioBase64);
    let bytes = new Uint8Array(binary.length);

    for (let i = 0; i < binary.length; i++) {
        bytes[i] = binary.charCodeAt(i);
    }

    let blob = new Blob([bytes], { type: "audio/webm" });
    let url = URL.createObjectURL(blob);

    let audio = new Audio(url);
    audio.play();
};

function playTTS() {
    let text = document.getElementById("responseText").innerText;

    ws.send(JSON.stringify({
        text: text,
        language: "en-IN"
    }));
}