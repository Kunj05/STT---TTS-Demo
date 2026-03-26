from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import cv2
import numpy as np
from PIL import Image
import io
from ultralytics import YOLO
from paddleocr import PaddleOCR
import google.generativeai as genai
import os

from fastapi import WebSocket
from fastapi.middleware.cors import CORSMiddleware
from sarvamai import SarvamAI
from sarvamai.core.api_error import ApiError
from dotenv import load_dotenv
import base64

load_dotenv()
API_KEY = os.getenv("SARVAM_API_KEY")
gemini_api_key=os.getenv("gemini_API_KEY")
client = SarvamAI(api_subscription_key=API_KEY)


# Initialize OCR
ocr = PaddleOCR(use_angle_cls=False, lang="en")

# Initialize YOLO model
# model = YOLO('yolov8n.pt')  # Using YOLOv8 nano model for object detection
yolo_model = YOLO('yolov8n.pt').to('cuda')
# Configure Gemini API
genai.configure(api_key=gemini_api_key)
app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Templates
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# @app.post("/detect")
# async def detect_objects(file: UploadFile = File(...)):
#     # Read image from upload
#     contents = await file.read()
#     nparr = np.frombuffer(contents, np.uint8)
#     img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

#     # Run YOLO detection
#     results = model(img)
#     detections = []
#     for result in results:
#         for box in result.boxes:
#             x1, y1, x2, y2 = box.xyxy[0].tolist()
#             conf = box.conf[0].item()
#             cls = int(box.cls[0].item())
#             name = model.names[cls]
#             detections.append({
#                 "x1": x1, "y1": y1, "x2": x2, "y2": y2,
#                 "confidence": conf, "name": name
#             })

#     return JSONResponse(content={"detections": detections})
@app.post("/detect")
async def detect_objects(file: UploadFile = File(...)):
    # Read image
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # 🔥 Resize (BIG speed boost)
    img = cv2.resize(img, (640, 480))

    # 🔥 YOLO inference (optimized)
    results = yolo_model(img, imgsz=416, device=0, conf=0.4)

    detections = []

    # 🔥 Faster parsing
    r = results[0]
    if r.boxes is not None:
        boxes = r.boxes.xyxy.cpu().numpy()
        confs = r.boxes.conf.cpu().numpy()
        classes = r.boxes.cls.cpu().numpy().astype(int)

        for i in range(len(boxes)):
            x1, y1, x2, y2 = boxes[i]
            detections.append({
                "x1": float(x1),
                "y1": float(y1),
                "x2": float(x2),
                "y2": float(y2),
                "confidence": float(confs[i]),
                "name": yolo_model.names[classes[i]]
            })

    return {"detections": detections}

@app.post("/capture")
async def capture_image(file: UploadFile = File(...)):
    # Read image from upload
    contents = await file.read()
    image = Image.open(io.BytesIO(contents))

    # Convert to numpy array
    img_np = np.array(image)

    # Handle RGBA images
    if img_np.shape[2] == 4:
        img_np = cv2.cvtColor(img_np, cv2.COLOR_RGBA2RGB)

    # Run OCR
    result = ocr.ocr(img_np, cls=False)
    text = "\n".join([line[1][0] for line in result[0]]) if result and result[0] else ""

    return JSONResponse(content={"text": text})

@app.post("/ask")
async def ask_question(text: str = Form(...), question: str = Form(...)):
    # Create prompt for Gemini
    prompt = f"""You are analyzing a text.

 text:
{text}

Answer the user's question and give short answer.

Question:
{question}"""

    # Generate response using Gemini
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content(prompt)
    answer = response.text

    return JSONResponse(content={"answer": answer})

@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    # Same logic as capture
    contents = await file.read()
    image = Image.open(io.BytesIO(contents))
    img_np = np.array(image)
    if img_np.shape[2] == 4:
        img_np = cv2.cvtColor(img_np, cv2.COLOR_RGBA2RGB)

    result = ocr.ocr(img_np, cls=False)
    text = "\n".join([line[1][0] for line in result[0]]) if result and result[0] else ""

    return JSONResponse(content={"text": text})

@app.post("/stt")
async def speech_to_text(file: UploadFile = File(...)):
    try:
        audio_bytes = await file.read()

        response = client.speech_to_text.transcribe(
            file=audio_bytes,
            model="saaras:v3",
            mode="codemix",
            language_code="unknown"
        )

        return {
            "transcript": response.transcript
        }

    except ApiError as e:
        return {"error": str(e.body)}
    


@app.websocket("/tts")
async def text_to_speech(ws: WebSocket):
    await ws.accept()

    while True:
        data = await ws.receive_json()

        text = data.get("text")
        language = data.get("language", "en-IN")

        try:
            response = client.text_to_speech.convert(
                text=text,
                model="bulbul:v3",
                target_language_code=language,
                pace=1.0,
                speech_sample_rate=24000
            )

            audio_base64 = "".join(response.audios)
            await ws.send_text(audio_base64)

        except ApiError as e:
            await ws.send_json({"error": str(e.body)})