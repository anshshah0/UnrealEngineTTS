from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from transformers import pipeline
import numpy as np
import scipy.io.wavfile as wavfile
import torch
import uuid, os

app = FastAPI()

UE_AUDIO_DIR = os.path.abspath("Saved/tts_audio")
os.makedirs(UE_AUDIO_DIR, exist_ok=True)

tts = pipeline("text-to-speech", model="facebook/mms-tts-eng")  # or set device=0 for GPU

class TTSRequest(BaseModel):
    text: str

def _to_int16_pcm(wave: np.ndarray) -> np.ndarray:
    """Ensure mono float -> int16 PCM in [-32768, 32767]."""
    if wave.ndim > 1:
        wave = np.mean(wave, axis=1)
    wave = wave.astype(np.float64, copy=False)
    wave = np.clip(wave, -1.0, 1.0)
    return (wave * 32767.0).astype(np.int16)

@app.post("/tts/")
async def tts_endpoint(req: TTSRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    out = tts(req.text)

    audio = out["audio"]
    sr = int(out["sampling_rate"])

    if isinstance(audio, torch.Tensor):
        audio = audio.detach().cpu().numpy()

    if not isinstance(audio, np.ndarray):
        audio = np.array(audio)

    pcm16 = _to_int16_pcm(audio)

    file_id = str(uuid.uuid4())
    file_path = os.path.join(UE_AUDIO_DIR, f"{file_id}.wav")
    wavfile.write(file_path, sr, pcm16)

    if not (os.path.exists(file_path) and os.path.getsize(file_path) > 44):
        raise HTTPException(status_code=500, detail="Failed to write WAV file.")

    return {
        "file_id": file_id,
        "path": file_path.replace("\\", "/"),
        "download_url": f"/tts/{file_id}"
    }

@app.get("/tts/{file_id}")
async def get_tts(file_id: str):
    path = os.path.join(UE_AUDIO_DIR, f"{file_id}.wav")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(path, media_type="audio/wav", filename=f"{file_id}.wav")

# cd OneDrive/tts/my_tts_api
# python -m uvicorn tts_api:app --reload
# http://127.0.0.1:8000/docs