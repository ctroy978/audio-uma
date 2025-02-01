import uvicorn
from fastapi import FastAPI, HTTPException, Form, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from kokoro import KPipeline
import soundfile as sf
import io
import os
import tempfile

app = FastAPI()

# CORS setup for allowing cross-origin requests if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Kokoro Pipeline
pipeline = KPipeline(lang_code='a')

@app.post("/generate_tts/")
async def generate_tts(
    text: str = Form(...),  # Changed to explicitly accept form data
    voice: str = Form("af_heart"),  # Default voice, can be changed
    speed: float = Form(1.0),       # Default speed
    format: str = Form("mp3")       # Default format, can be mp3, wav, etc.
):
    try:
        # Generate audio
        generator = pipeline(text, voice=voice, speed=speed, split_pattern=r'\n+')
        
        # Use BytesIO for in-memory file handling for better performance
        with io.BytesIO() as audio_buffer:
            for _, _, audio in generator:
                # Write audio data to buffer
                sf.write(audio_buffer, audio, 24000, format=format)
                # Reset the buffer position to the start for subsequent writes
                audio_buffer.seek(0, os.SEEK_END)
            
            # Reset buffer position to start for reading
            audio_buffer.seek(0)

            # Streaming the response to avoid loading the entire file into memory
            return StreamingResponse(
                iter([audio_buffer.getvalue()]),
                media_type=f"audio/{format}",
                headers={"Content-Disposition": f"attachment; filename=tts_output.{format}"}
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)