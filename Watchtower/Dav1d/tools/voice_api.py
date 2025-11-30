#!/usr/bin/env python3
"""
Cloud Speech & Text-to-Speech Integration for DAV1D
Enables voice interaction capabilities
"""

import os
from typing import Optional, Dict, Any
from google.cloud import texttospeech, speech
from pathlib import Path

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "gen-lang-client-0285887798")


def text_to_speech(
    text: str,
    output_file: str = "output.mp3",
    voice_name: str = "en-US-Journey-D",
    speaking_rate: float = 1.0,
    pitch: float = 0.0
) -> Dict[str, Any]:
    """
    Convert text to speech and save as audio file.
    
    Args:
        text: Text to convert to speech
        output_file: Output audio file path (default: "output.mp3")
        voice_name: Voice to use. Options:
            - "en-US-Journey-D" (default) - Premium male voice
            - "en-US-Journey-F" - Premium female voice
            - "en-US-Neural2-D" - Neural male voice
            - "en-US-Neural2-F" - Neural female voice
            - "en-US-Standard-D" - Standard male voice
        speaking_rate: Speed (0.25-4.0, default: 1.0)
        pitch: Pitch adjustment (-20.0 to 20.0, default: 0.0)
        
    Returns:
        dict with success status and output file path
        
    Example:
        text_to_speech("Hello, I am Dav1d", voice_name="en-US-Journey-D")
    """
    try:
        client = texttospeech.TextToSpeechClient()
        
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name=voice_name
        )
        
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=speaking_rate,
            pitch=pitch
        )
        
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        # Save audio file
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'wb') as out:
            out.write(response.audio_content)
        
        return {
            'success': True,
            'text': text[:100] + ('...' if len(text) > 100 else ''),
            'voice': voice_name,
            'output_file': str(output_path.absolute()),
            'size_bytes': len(response.audio_content)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def speech_to_text(
    audio_file: str,
    language_code: str = "en-US",
    enable_automatic_punctuation: bool = True
) -> Dict[str, Any]:
    """
    Convert speech audio file to text.
    
    Args:
        audio_file: Path to audio file (WAV, FLAC, or MP3)
        language_code: Language of the audio (default: "en-US")
        enable_automatic_punctuation: Add punctuation automatically
        
    Returns:
        dict with transcribed text and confidence scores
        
    Example:
        speech_to_text("recording.wav")
    """
    try:
        client = speech.SpeechClient()
        
        # Read audio file
        audio_path = Path(audio_file)
        if not audio_path.exists():
            return {
                'success': False,
                'error': f'Audio file not found: {audio_file}'
            }
        
        with open(audio_path, 'rb') as audio:
            content = audio.read()
        
        audio = speech.RecognitionAudio(content=content)
        
        # Detect encoding from file extension
        ext = audio_path.suffix.lower()
        if ext == '.wav':
            encoding = speech.RecognitionConfig.AudioEncoding.LINEAR16
        elif ext == '.flac':
            encoding = speech.RecognitionConfig.AudioEncoding.FLAC
        elif ext == '.mp3':
            encoding = speech.RecognitionConfig.AudioEncoding.MP3
        else:
            encoding = speech.RecognitionConfig.AudioEncoding.ENCODING_UNSPECIFIED
        
        config = speech.RecognitionConfig(
            encoding=encoding,
            language_code=language_code,
            enable_automatic_punctuation=enable_automatic_punctuation,
            model="default"
        )
        
        response = client.recognize(config=config, audio=audio)
        
        if not response.results:
            return {
                'success': False,
                'error': 'No speech detected in audio file'
            }
        
        # Get all transcripts
        transcripts = []
        for result in response.results:
            alternative = result.alternatives[0]
            transcripts.append({
                'text': alternative.transcript,
                'confidence': alternative.confidence
            })
        
        # Combine all transcripts
        full_transcript = ' '.join([t['text'] for t in transcripts])
        avg_confidence = sum([t['confidence'] for t in transcripts]) / len(transcripts)
        
        return {
            'success': True,
            'audio_file': str(audio_path.absolute()),
            'transcript': full_transcript,
            'confidence': round(avg_confidence, 3),
            'segments': transcripts,
            'language': language_code
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def speech_to_text_streaming(
    audio_file: str,
    language_code: str = "en-US"
) -> Dict[str, Any]:
    """
    Convert speech to text with streaming (for real-time transcription).
    
    Args:
        audio_file: Path to audio file
        language_code: Language of the audio (default: "en-US")
        
    Returns:
        dict with streaming transcription results
    """
    try:
        client = speech.SpeechClient()
        
        audio_path = Path(audio_file)
        if not audio_path.exists():
            return {
                'success': False,
                'error': f'Audio file not found: {audio_file}'
            }
        
        with open(audio_path, 'rb') as audio:
            content = audio.read()
        
        # Create streaming request generator
        def request_generator():
            # First request with config
            config = speech.StreamingRecognitionConfig(
                config=speech.RecognitionConfig(
                    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                    language_code=language_code,
                    enable_automatic_punctuation=True
                ),
                interim_results=True
            )
            
            yield speech.StreamingRecognizeRequest(streaming_config=config)
            
            # Send audio in chunks
            chunk_size = 1024
            for i in range(0, len(content), chunk_size):
                chunk = content[i:i + chunk_size]
                yield speech.StreamingRecognizeRequest(audio_content=chunk)
        
        responses = client.streaming_recognize(request_generator())
        
        transcripts = []
        for response in responses:
            for result in response.results:
                if result.is_final:
                    transcripts.append({
                        'text': result.alternatives[0].transcript,
                        'confidence': result.alternatives[0].confidence,
                        'is_final': True
                    })
        
        full_transcript = ' '.join([t['text'] for t in transcripts])
        
        return {
            'success': True,
            'audio_file': str(audio_path.absolute()),
            'transcript': full_transcript,
            'segments': transcripts,
            'language': language_code
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def list_available_voices(language_code: str = "en-US") -> Dict[str, Any]:
    """
    List all available Text-to-Speech voices for a language.
    
    Args:
        language_code: Language code (default: "en-US")
        
    Returns:
        dict with list of available voices
    """
    try:
        client = texttospeech.TextToSpeechClient()
        
        voices = client.list_voices(language_code=language_code)
        
        voice_list = []
        for voice in voices.voices:
            # Filter to only the requested language
            if language_code in voice.language_codes:
                voice_list.append({
                    'name': voice.name,
                    'gender': texttospeech.SsmlVoiceGender(voice.ssml_gender).name,
                    'languages': list(voice.language_codes),
                    'natural_sample_rate': voice.natural_sample_rate_hertz
                })
        
        return {
            'success': True,
            'language': language_code,
            'voices': voice_list,
            'count': len(voice_list)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
