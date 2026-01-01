
import asyncio
import json
import logging
import base64
import os
import websockets
from datetime import datetime
import numpy as np

logger = logging.getLogger("WisprCloud")
logger.setLevel(logging.INFO)

class WisprCloudService:
    """
    WebSocket Client for Wispr Flow Cloud API.
    Stream raw audio -> Received Transcribed Text.
    """
    ENDPOINT = "wss://platform-api.wisprflow.ai/api/v1/dash/ws"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("WISPR_FLOW_API_KEY")
        if not self.api_key:
            logger.error("WISPR_FLOW_API_KEY not found!")
            
        self.running = False
        self.ws = None
        self.packet_counter = 0
        self.audio_buffer = bytearray()
        
        # Callbacks
        self.on_commit = None
        self.on_partial = None
        
        # Audio Config (Required by Wispr: 16kHz, 16bit PCM)
        self.target_rate = 16000
        self.chunk_size_bytes = 32000 # ~1 second of 16k/16bit/mono

    def start(self, on_commit, on_partial=None):
        self.on_commit = on_commit
        self.on_partial = on_partial
        self.running = True
        asyncio.create_task(self._process_loop())
        logger.info("Wispr Cloud Service Started.")

    def stop(self):
        self.running = False
        if self.ws:
            asyncio.create_task(self.ws.close())
        logger.info("Wispr Cloud Service Stopped.")

    def add_audio(self, audio_chunk: np.ndarray):
        """
        Add raw float32 audio (from sounddevice).
        Convert to int16 PCM and buffer.
        """
        # 1. Convert float32 [-1, 1] to int16
        audio_int16 = (audio_chunk * 32767).astype(np.int16)
        
        # 2. Append bytes
        self.audio_buffer.extend(audio_int16.tobytes())

    async def _process_loop(self):
        url = f"{self.ENDPOINT}?api_key=Bearer%20{self.api_key}"
        
        while self.running:
            try:
                async with websockets.connect(url) as ws:
                    self.ws = ws
                    logger.info("Connected to Wispr Cloud.")
                    
                    # 1. Send START message
                    await ws.send(json.dumps({"type": "start"}))
                    
                    # 2. Parallel Tasks: Send Audio & Receive Text
                    send_task = asyncio.create_task(self._sender(ws))
                    recv_task = asyncio.create_task(self._receiver(ws))
                    
                    await asyncio.gather(send_task, recv_task)
                    
            except websockets.exceptions.ConnectionClosed:
                logger.warning("Wispr Connection Closed. Reconnecting...")
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Wispr Error: {e}")
                await asyncio.sleep(2)

    async def _sender(self, ws):
        """Send audio chunks every ~1s"""
        while self.running:
            if len(self.audio_buffer) >= self.chunk_size_bytes:
                # Pop chunk
                chunk = self.audio_buffer[:self.chunk_size_bytes]
                self.audio_buffer = self.audio_buffer[self.chunk_size_bytes:]
                
                # Base64 Encode
                b64_audio = base64.b64encode(chunk).decode('utf-8')
                
                # Send 'append'
                msg = {
                    "type": "append",
                    "audio": b64_audio,
                    "position": self.packet_counter
                }
                await ws.send(json.dumps(msg))
                self.packet_counter += 1
            else:
                await asyncio.sleep(0.1)

    async def _receiver(self, ws):
        """Listen for transcription events"""
        async for message in ws:
            try:
                data = json.loads(message)
                # Event types might be 'transcript', 'partial', 'final', etc.
                # Documentation wasn't explicit on response schema, so inferring or logging first.
                
                # Handling assumed structure based on reverse engineering standard speech APIs
                # Usually: { type: "transcription", text: "...", is_final: bool }
                
                msg_type = data.get("type")
                text = data.get("text", "")
                
                if msg_type == "transcription":
                     # Check if final?
                     # Wispr docs mentioned "streaming response".
                     # Let's dump the first few to learn the schema if needed.
                     pass 
                
                # For now, simplistic handling (assuming 'text' field exists)
                if text:
                    if self.on_partial: self.on_partial(text)
                    
                    # If this is a final commit (logic depends on API specifics)
                    # Often "is_final": true
                    if data.get("is_final") or data.get("final"):
                        if self.on_commit: self.on_commit(text)
                        
            except Exception as e:
                logger.error(f"Receiver Error: {e}")
