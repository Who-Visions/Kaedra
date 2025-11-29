#!/usr/bin/env python3
"""
YouTube Data API v3 Integration for DAV1D
Enables video search, playlist management, and content analysis
"""

import os
from typing import Optional, List, Dict, Any
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "gen-lang-client-0285887798")


def search_youtube_videos(
    query: str,
    max_results: int = 5,
    order: str = "relevance"
) -> Dict[str, Any]:
    """
    Search YouTube for videos matching a query.
    
    Args:
        query: Search query (e.g., "AI with Dav3", "Next.js tutorial")
        max_results: Maximum number of results to return (default: 5, max: 50)
        order: Sort order - "relevance", "date", "rating", "viewCount", "title"
        
    Returns:
        dict with search results including video IDs, titles, descriptions, and URLs
        
    Example:
        search_youtube_videos("Gemini AI tutorial", max_results=3)
    """
    try:
        # YouTube API requires an API key
        api_key = os.getenv("YOUTUBE_API_KEY")
        if not api_key:
            return {
                "success": False,
                "error": "YOUTUBE_API_KEY not set in environment. Get one from Google Cloud Console."
            }
        
        youtube = build('youtube', 'v3', developerKey=api_key)
        
        request = youtube.search().list(
            q=query,
            part='snippet',
            type='video',
            maxResults=min(max_results, 50),
            order=order,
            relevanceLanguage='en'
        )
        
        response = request.execute()
        
        videos = []
        for item in response.get('items', []):
            video_id = item['id']['videoId']
            snippet = item['snippet']
            
            videos.append({
                'video_id': video_id,
                'title': snippet['title'],
                'description': snippet['description'],
                'channel': snippet['channelTitle'],
                'published_at': snippet['publishedAt'],
                'url': f'https://www.youtube.com/watch?v={video_id}',
                'thumbnail': snippet['thumbnails']['high']['url'] if 'high' in snippet['thumbnails'] else snippet['thumbnails']['default']['url']
            })
        
        return {
            'success': True,
            'query': query,
            'total_results': response.get('pageInfo', {}).get('totalResults', 0),
            'videos': videos,
            'count': len(videos)
        }
        
    except HttpError as e:
        return {
            'success': False,
            'error': f'YouTube API error: {e.error_details}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def get_video_details(video_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific YouTube video.
    
    Args:
        video_id: YouTube video ID (e.g., "dQw4w9WgXcQ")
        
    Returns:
        dict with video details including statistics, content details, and metadata
    """
    try:
        api_key = os.getenv("YOUTUBE_API_KEY")
        if not api_key:
            return {
                "success": False,
                "error": "YOUTUBE_API_KEY not set"
            }
        
        youtube = build('youtube', 'v3', developerKey=api_key)
        
        request = youtube.videos().list(
            part='snippet,contentDetails,statistics',
            id=video_id
        )
        
        response = request.execute()
        
        if not response.get('items'):
            return {
                'success': False,
                'error': f'Video not found: {video_id}'
            }
        
        item = response['items'][0]
        snippet = item['snippet']
        stats = item.get('statistics', {})
        
        return {
            'success': True,
            'video_id': video_id,
            'title': snippet['title'],
            'description': snippet['description'],
            'channel': snippet['channelTitle'],
            'published_at': snippet['publishedAt'],
            'duration': item['contentDetails']['duration'],
            'views': int(stats.get('viewCount', 0)),
            'likes': int(stats.get('likeCount', 0)),
            'comments': int(stats.get('commentCount', 0)),
            'url': f'https://www.youtube.com/watch?v={video_id}',
            'tags': snippet.get('tags', [])
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def get_channel_info(channel_id: str) -> Dict[str, Any]:
    """
    Get information about a YouTube channel.
    
    Args:
        channel_id: YouTube channel ID
        
    Returns:
        dict with channel details including statistics and metadata
    """
    try:
        api_key = os.getenv("YOUTUBE_API_KEY")
        if not api_key:
            return {
                "success": False,
                "error": "YOUTUBE_API_KEY not set"
            }
        
        youtube = build('youtube', 'v3', developerKey=api_key)
        
        request = youtube.channels().list(
            part='snippet,statistics',
            id=channel_id
        )
        
        response = request.execute()
        
        if not response.get('items'):
            return {
                'success': False,
                'error': f'Channel not found: {channel_id}'
            }
        
        item = response['items'][0]
        snippet = item['snippet']
        stats = item.get('statistics', {})
        
        return {
            'success': True,
            'channel_id': channel_id,
            'title': snippet['title'],
            'description': snippet['description'],
            'subscribers': int(stats.get('subscriberCount', 0)),
            'total_videos': int(stats.get('videoCount', 0)),
            'total_views': int(stats.get('viewCount', 0)),
            'url': f'https://www.youtube.com/channel/{channel_id}',
            'thumbnail': snippet['thumbnails']['high']['url'] if 'high' in snippet['thumbnails'] else snippet['thumbnails']['default']['url']
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
