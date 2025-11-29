#!/usr/bin/env python3
"""
Veo 3 Video Generation for DAV1D
Google's most advanced video generation model
Cost: ~$3.13 per 4K video (excellent for burning credits!)
"""

import os
from typing import Optional, Dict, Any
from pathlib import Path
from google import genai
from google.genai.types import GenerateVideosConfig
from datetime import datetime
from zoneinfo import ZoneInfo

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "gen-lang-client-0285887798")
LOCATION = "us-central1"  # Veo is only available in us-central1
TIMEZONE = ZoneInfo("US/Eastern")

# Available Veo models
VEO_MODELS = {
    "veo-3.1": "veo-3.1-generate-preview",           # Latest, high quality, with audio
    "veo-3.1-fast": "veo-3.1-fast-generate-preview", # Fast version of 3.1
    "veo-3": "veo-3.0-generate-001",                 # Stable, high quality, with audio
    "veo-3-fast": "veo-3.0-fast-generate-001",       # Fast version of 3.0
    "veo-2": "veo-2.0-generate-001"                  # Older, silent (no audio)
}


def generate_video(
    prompt: str,
    duration: int = 8,
    resolution: str = "1080p",
    model: str = "veo-3.1-fast",
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a video using Veo.
    
    Args:
        prompt: Text description of the video to generate
        duration: Video duration in seconds (default: 8, max supported by Veo 3.1)
        resolution: "4K" or "1080p" (default: 1080p for testing, ~$1.88 vs $3.13)
        model: Which Veo model to use:
            - "veo-3.1" (latest, best quality, with audio)
            - "veo-3.1-fast" (default - faster generation, with audio)
            - "veo-3" (stable, high quality, with audio)
            - "veo-3-fast" (stable + fast, with audio)
            - "veo-2" (older, NO audio) 
        output_file: Optional output filename (auto-generated if not provided)
        
    Returns:
        dict with video file path and metadata
        
    Cost:
        - 4K: ~$3.13 per video
        - 1080p: ~$1.88 per video
        
    Example:
        generate_video(
            "A cyberpunk cityscape with neon lights and flying cars",
            duration=5,
            resolution="4K"
        )
    """
    try:
        client = genai.Client(
            vertexai=True,
            project=PROJECT_ID,
            location=LOCATION
        )
        
        # Determine resolution setting
        if resolution.upper() == "4K":
            aspect_ratio = "16:9"
            quality = "high"
            est_cost = 3.13
        else:  # 1080p
            aspect_ratio = "16:9"
            quality = "standard"
            est_cost = 1.88
        
        print(f"🎬 Generating {resolution} video...")
        print(f"   Model: {model}")
        print(f"   Prompt: {prompt[:80]}...")
        print(f"   Duration: {duration}s")
        print(f"   Est. cost: ${est_cost:.2f}")
        
        # Get model name
        model_name = VEO_MODELS.get(model, VEO_MODELS["veo-3.1-fast"])
        
        # Generate video (returns an async operation)
        operation = client.models.generate_videos(
            model=model_name,
            prompt=prompt,
            config=GenerateVideosConfig(
                number_of_videos=1
            )
        )
        
        print(f"⏳ Video generation started (takes 3-5 minutes)...")
        
        # Poll the operation status until the video is ready (official method)
        import time
        while not operation.done:
            print("   Waiting for video generation to complete...")
            time.sleep(10)
            operation = client.operations.get(operation)
        
        # Download the generated video
        if not operation.response or not operation.response.generated_videos:
            return {
                'success': False,
                'error': 'No videos generated in response'
            }
        
        generated_video = operation.response.generated_videos[0]
        
        # CLOUD-FIRST: Save to GCS, then cache locally
        videos_dir = Path("videos")
        videos_dir.mkdir(exist_ok=True)
        
        # Generate filename if not provided
        if not output_file:
            timestamp = datetime.now(TIMEZONE).strftime("%Y%m%d_%H%M%S")
            safe_prompt = "".join(c if c.isalnum() else "_" for c in prompt[:30])
            output_file = f"veo3_{resolution.lower()}_{timestamp}_{safe_prompt}.mp4"
        
        local_path = videos_dir / output_file
        gcs_url = None
        
        # For Vertex AI, the video is already a GCS URI
        video_uri = generated_video.video
        
        # Download from GCS
        try:
            from google.cloud import storage
            gcs_client = storage.Client(project=PROJECT_ID)
            
            # Parse GCS URI: gs://bucket/path
            if video_uri.startswith('gs://'):
                gcs_path = video_uri[5:]  # Remove 'gs://'
                bucket_name, blob_path = gcs_path.split('/', 1)
                
                bucket = gcs_client.bucket(bucket_name)
                blob = bucket.blob(blob_path)
                
                # Download to local
                blob.download_to_filename(str(local_path))
                
                # Copy to our bucket for permanent storage
                dest_bucket = gcs_client.bucket("dav1d-veo-videos")
                dest_blob = dest_bucket.blob(f"veo3/{output_file}")
                
                # Copy blob
                source_bucket = gcs_client.bucket(bucket_name)
                source_blob = source_bucket.blob(blob_path)
                dest_bucket.copy_blob(source_blob, dest_bucket, dest_blob.name)
                
                gcs_url = f"gs://dav1d-veo-videos/veo3/{output_file}"
                print(f"☁️  Saved to GCS: {gcs_url}")
            else:
                # Fallback: direct bytes if available
                with open(local_path, 'wb') as f:
                    f.write(generated_video.video_bytes)
            
        except Exception as e:
            print(f"⚠️  Download error: {e}")
            return {
                'success': False,
                'error': f'Failed to download video: {e}'
            }
        
        # Get file size
        size_mb = local_path.stat().st_size / (1024 * 1024)
        
        # Upload to GCS (cloud-first)
        try:
            from google.cloud import storage
            gcs_client = storage.Client(project=PROJECT_ID)
            bucket_name = "dav1d-veo-videos"
            bucket = gcs_client.bucket(bucket_name)
            
            gcs_path = f"veo3/{output_file}"
            blob = bucket.blob(gcs_path)
            blob.upload_from_filename(str(local_path), content_type='video/mp4')
            
            gcs_url = f"gs://{bucket_name}/{gcs_path}"
            print(f"☁️  Uploaded to GCS: {gcs_url}")
            
        except Exception as gcs_error:
            print(f"⚠️  GCS upload failed: {gcs_error}")
        
        print(f"✅ Video generated!")
        if gcs_url:
            print(f"   ☁️  Cloud: {gcs_url}")
        print(f"   💾 Local: {local_path}")
        print(f"   📊 Size: {size_mb:.2f} MB | Duration: {duration}s | Cost: ${est_cost:.2f}")
        
        return {
            'success': True,
            'video_path': str(local_path.absolute()),
            'gcs_url': gcs_url,
            'size_mb': round(size_mb, 2),
            'duration': duration,
            'resolution': resolution,
            'cost': est_cost,
            'prompt': prompt
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def generate_video_batch(
    prompts: list,
    duration: int = 8,
    resolution: str = "1080p",
    model: str = "veo-3.1-fast"
) -> Dict[str, Any]:
    """
    Generate multiple videos in batch.
    
    Args:
        prompts: List of text prompts
        duration: Video duration in seconds
        resolution: "4K" or "1080p"
        model: Which Veo model to use (default: veo-3.1-fast)
        
    Returns:
        dict with list of generated videos and total cost
        
    Example:
        generate_video_batch([
            "A serene ocean sunset",
            "A bustling city street at night",
            "A futuristic robot in a lab"
        ], resolution="4K")
    """
    results = []
    total_cost = 0.0
    
    print(f"\n🎬 Batch Video Generation")
    print(f"   Videos: {len(prompts)}")
    print(f"   Resolution: {resolution}")
    print(f"   Est. total cost: ${3.13 * len(prompts) if resolution.upper() == '4K' else 1.88 * len(prompts):.2f}")
    print()
    
    for i, prompt in enumerate(prompts, 1):
        print(f"[{i}/{len(prompts)}] ", end="")
        result = generate_video(prompt, duration, resolution, model)
        results.append(result)
        
        if result['success']:
            total_cost += result['cost']
        
        print()
    
    print(f"\n✅ Batch complete!")
    print(f"   Videos created: {sum(1 for r in results if r['success'])}/{len(prompts)}")
    print(f"   Total cost: ${total_cost:.2f}")
    
    return {
        'success': True,
        'videos': results,
        'total_cost': total_cost,
        'count': len(results)
    }


# Preset video prompts for credit burning
VIDEO_BURN_PROMPTS = [
    "A cyberpunk cityscape at night with neon lights and flying cars",
    "A futuristic AI data center with glowing servers and holographic displays",
    "A serene ocean sunset with waves gently crashing on a beach",
    "A bustling Tokyo street at night with vibrant signs and crowds",
    "A sleek sports car driving through a mountain road at golden hour",
    "A modern office workspace with large windows overlooking a city",
    "A cozy coffee shop interior with morning sunlight streaming through windows",
    "A high-tech laboratory with scientists working on advanced robotics",
    "A peaceful forest path with sunlight filtering through the trees",
    "A dramatic thunderstorm over an open field with lightning strikes"
]


def burn_credits_with_videos(target_spend: float = 12.50, resolution: str = "4K"):
    """
    Burn credits by generating multiple 4K videos.
    
    Args:
        target_spend: How much to spend (default: $12.50 = 4 videos)
        resolution: "4K" or "1080p"
        
    Example:
        burn_credits_with_videos(12.50, "4K")  # Generate 4 videos
    """
    cost_per_video = 3.13 if resolution.upper() == "4K" else 1.88
    videos_needed = int(target_spend / cost_per_video)
    
    print(f"""
    ╔══════════════════════════════════════════════════════════╗
    ║  🎬 VEO 3 VIDEO CREDIT BURNER                            ║
    ║  Resolution: {resolution}                                         ║
    ║  Videos: {videos_needed}                                           ║
    ║  Cost: ${target_spend:.2f}                                         ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    prompts = VIDEO_BURN_PROMPTS[:videos_needed]
    return generate_video_batch(prompts, duration=5, resolution=resolution)


if __name__ == "__main__":
    # Test video generation
    print("Testing Veo 3 video generation...")
    
    result = generate_video(
        "A futuristic cityscape with flying cars and neon lights",
        duration=8,
        resolution="4K"
    )
    
    if result['success']:
        print(f"\n✅ Success! Video: {result['video_path']}")
    else:
        print(f"\n❌ Error: {result['error']}")
