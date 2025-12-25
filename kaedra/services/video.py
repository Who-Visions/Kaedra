"""
KAEDRA v0.0.6 - Video Generation Service
Handles video generation with Google Veo models via Gemini API.
"""

import os
import time
from typing import Optional, List, Dict, Any, Union
from pathlib import Path
from dataclasses import dataclass

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

from ..core.config import VIDEO_DIR, VEO_MODELS, DEFAULT_VEO_MODEL


@dataclass
class VideoResult:
    """Result from a video generation."""
    file_path: Path
    model: str
    duration_seconds: float
    prompt: str
    operation_id: Optional[str] = None
    metadata: Optional[Dict] = None


class VideoService:
    """
    Manages video generation via Google Veo models.
    
    Features:
    - Multiple Veo model support (3.1, 3.0, 2.0)
    - Text-to-video generation
    - Image-to-video generation
    - Reference image support (asset mode)
    - Video interpolation (first + last frame)
    - Video extension (extend existing video)
    - Async operation polling
    - Automatic file management
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 model_key: str = DEFAULT_VEO_MODEL):
        """
        Initialize the video service.
        
        Args:
            api_key: Google AI API key (defaults to env var)
            model_key: Veo model key from VEO_MODELS dict
        """
        if genai is None:
            raise ImportError(
                "google-genai package not installed. "
                "Install with: pip install google-genai"
            )
        
        api_key = api_key or os.getenv("GOOGLE_AI_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "Google AI API key required. Set GOOGLE_AI_API_KEY or GEMINI_API_KEY env var."
            )
        
        self.client = genai.Client(api_key=api_key)
        self.model = VEO_MODELS.get(model_key, VEO_MODELS[DEFAULT_VEO_MODEL])
        self.model_key = model_key
    
    def generate_image(self, prompt: str) -> Any:
        """
        Generate an image using Gemini 3 Pro Image Preview.
        
        Args:
            prompt: Text description of the image
            
        Returns:
            Generated image object
        """
        try:
            result = self.client.models.generate_content(
                model="gemini-3-pro-image-preview",
                contents=prompt,
                config={"response_modalities": ['IMAGE']}
            )
            return result.parts[0].as_image()
        except Exception as e:
            raise RuntimeError(f"Failed to generate image: {e}")
    
    def generate_video(self,
                      prompt: str,
                      image: Optional[Any] = None,
                      reference_images: Optional[List[Dict[str, Any]]] = None,
                      first_frame: Optional[Any] = None,
                      last_frame: Optional[Any] = None,
                      input_video: Optional[Any] = None,
                      resolution: str = "720p",
                      number_of_videos: int = 1,
                      poll_interval: int = 10,
                      output_filename: Optional[str] = None) -> VideoResult:
        """
        Generate a video using Veo.
        
        Args:
            prompt: Text description of the video (max 1024 tokens)
            image: Optional starting image (generated separately)
            reference_images: Optional list of reference images with metadata
                            Format: [{"image": image_obj, "reference_type": "asset"}, ...]
            first_frame: Optional first frame image (for interpolation)
            last_frame: Optional last frame image (for interpolation)
            input_video: Optional input video file (for extension)
            resolution: Output resolution ("720p", "1080p")
            number_of_videos: Number of videos to generate (default 1)
            poll_interval: Seconds between status checks (default 10)
            output_filename: Optional custom filename (auto-generated if None)
            
        Returns:
            VideoResult with file path and metadata
        """
        start_time = time.time()
        
        # Build config
        config_params = {
            "number_of_videos": number_of_videos,
            "resolution": resolution
        }
        
        # Add reference images if provided
        if reference_images:
            if types:
                ref_images = [
                    types.VideoGenerationReferenceImage(
                        image=ref["image"],
                        reference_type=ref.get("reference_type", "asset")
                    )
                    for ref in reference_images
                ]
                config_params["reference_images"] = ref_images
            else:
                # Fallback: pass as-is if types not available
                config_params["reference_images"] = reference_images
        
        # Add interpolation frames if provided
        if last_frame:
            config_params["last_frame"] = last_frame
        
        # Build config if types module available
        if types:
            config = types.GenerateVideosConfig(**config_params)
        else:
            config = config_params  # Fallback to dict if types not available
        
        # Start generation
        try:
            if input_video:
                # Video extension mode
                operation = self.client.models.generate_videos(
                    model=self.model,
                    video=input_video,
                    prompt=prompt,
                    config=config
                )
            elif first_frame and last_frame:
                # Interpolation mode
                operation = self.client.models.generate_videos(
                    model=self.model,
                    prompt=prompt,
                    image=first_frame,
                    config=config
                )
            elif image:
                # Image-to-video mode
                operation = self.client.models.generate_videos(
                    model=self.model,
                    prompt=prompt,
                    image=image,
                    config=config
                )
            else:
                # Text-to-video mode
                operation = self.client.models.generate_videos(
                    model=self.model,
                    prompt=prompt,
                    config=config
                )
        except Exception as e:
            raise RuntimeError(f"Failed to start video generation: {e}")
        
        # Poll for completion
        operation_id = getattr(operation, 'name', None)
        
        while not operation.done:
            time.sleep(poll_interval)
            try:
                operation = self.client.operations.get(operation)
            except Exception as e:
                raise RuntimeError(f"Failed to check operation status: {e}")
        
        # Download video
        try:
            video = operation.response.generated_videos[0]
            self.client.files.download(file=video.video)
            
            # Generate filename if not provided
            if not output_filename:
                timestamp = int(time.time())
                output_filename = f"veo_{self.model_key}_{timestamp}.mp4"
            
            output_path = VIDEO_DIR / output_filename
            
            # Save video
            video.video.save(str(output_path))
            
            duration = time.time() - start_time
            
            return VideoResult(
                file_path=output_path,
                model=self.model,
                duration_seconds=duration,
                prompt=prompt,
                operation_id=operation_id,
                metadata={
                    "resolution": resolution,
                    "number_of_videos": number_of_videos
                }
            )
        except Exception as e:
            raise RuntimeError(f"Failed to download/save video: {e}")
    
    def generate_video_with_image(self,
                                  prompt: str,
                                  image_prompt: Optional[str] = None,
                                  output_filename: Optional[str] = None) -> VideoResult:
        """
        Convenience method: Generate image first, then video.
        
        Args:
            prompt: Video description
            image_prompt: Optional separate image description (uses video prompt if None)
            output_filename: Optional custom filename
            
        Returns:
            VideoResult
        """
        image_prompt = image_prompt or prompt
        image = self.generate_image(image_prompt)
        return self.generate_video(prompt, image=image, output_filename=output_filename)
    
    def extend_video(self,
                    video_path: Union[str, Path],
                    prompt: str,
                    output_filename: Optional[str] = None) -> VideoResult:
        """
        Extend an existing video.
        
        Args:
            video_path: Path to existing video file
            prompt: Description of the extension
            output_filename: Optional custom filename
            
        Returns:
            VideoResult
        """
        # Load video file
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        # Upload video (simplified - may need adjustment based on API)
        try:
            video_file = self.client.files.upload(path=str(video_path))
        except Exception as e:
            raise RuntimeError(f"Failed to upload video: {e}")
        
        return self.generate_video(
            prompt=prompt,
            input_video=video_file,
            output_filename=output_filename
        )
    
    def set_model(self, model_key: str):
        """Change the Veo model."""
        if model_key not in VEO_MODELS:
            raise ValueError(f"Unknown model key: {model_key}. Available: {list(VEO_MODELS.keys())}")
        self.model = VEO_MODELS[model_key]
        self.model_key = model_key

