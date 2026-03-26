import os
import base64
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from sarvamai import SarvamAI
from sarvamai.core.api_error import ApiError
from dotenv import load_dotenv
from fastapi import UploadFile, File

load_dotenv()

API_KEY = os.getenv("SARVAM_API_KEY")
if not API_KEY:
    raise ValueError("Please set SARVAM_API_KEY environment variable")

client = SarvamAI(api_subscription_key=API_KEY)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# 🎤 STT using sample.wav
# -------------------------

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

        transcript = response.transcript

        # PRINT IN TERMINAL
        print("\n🎤 STT RESULT:", transcript)
        print("Language:", response.language_code)
        print("Confidence:", response.language_probability)

        return {
            "transcript": transcript,
            "language": response.language_code,
            "confidence": response.language_probability
        }

    except ApiError as e:
        return {"error": str(e.body)}

# -------------------------
# 🔊 TEXT TO SPEECH
# -------------------------

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
            
# Available Options:

# unknown: Use when the language is not known; the API will auto-detect.
# hi-IN: Hindi
# bn-IN: Bengali
# kn-IN: Kannada
# ml-IN: Malayalam
# mr-IN: Marathi
# od-IN: Odia
# pa-IN: Punjabi
# ta-IN: Tamil
# te-IN: Telugu
# en-IN: English
# gu-IN: Gujarati
# Additional Options (saaras:v3 only):

# as-IN: Assamese
# ur-IN: Urdu
# ne-IN: Nepali
# kok-IN: Konkani
# ks-IN: Kashmiri
# sd-IN: Sindhi
# sa-IN: Sanskrit
# sat-IN: Santali
# mni-IN: Manipuri
# brx-IN: Bodo
# mai-IN: Maithili
# doi-IN: Dogri


## STT Modes (Saaras v3)

# | Mode | Description |
# |------|-------------|
# | `transcribe` | Standard transcription with formatting and normalization (default) |
# | `translate` | Direct speech-to-English translation |
# | `verbatim` | Exact word-for-word transcription |
# | `translit` | Romanization to Latin script |
# | `codemix` | Mixed script (English words in English, Indic in native script) |