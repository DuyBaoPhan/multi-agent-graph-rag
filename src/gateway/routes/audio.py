"""
Audio Routes — Module C3
=========================
Text-to-Speech endpoint using gTTS.
"""

import io
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from gtts import gTTS
from loguru import logger

router = APIRouter()

@router.get("/tts")
async def text_to_speech(text: str, lang: str = "vi"):
    """Convert text to speech and return as MP3 stream."""
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")
    
    try:
        # Create gTTS object
        tts = gTTS(text=text, lang=lang)
        
        # Write to memory buffer
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        
        return StreamingResponse(
            audio_buffer, 
            media_type="audio/mpeg",
            headers={"Content-Disposition": "inline; filename=speech.mp3"}
        )
    except Exception as e:
        logger.error(f"TTS Failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
