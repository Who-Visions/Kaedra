"""
KAEDRA v0.0.6 - Google Cloud Tools Module
Google API integrations for NYX and BLADE
"""

from typing import Dict, Any, Optional
import os


class GoogleCloudTools:
    """Google Cloud API integrations using your enabled services"""
    
    def __init__(self):
        """Initialize with Google Cloud credentials from environment"""
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "who-visions-app")
        self.api_key = os.getenv("GOOGLE_API_KEY", "")
    
    # ============================================
    # CUSTOM SEARCH API (Free: 100/day)
    # ============================================
    
    def custom_search(self, query: str, num_results: int = 5) -> Dict[str, Any]:
        """
        Search the web using Google Custom Search API
        
        Args:
            query: Search query
            num_results: Number of results to return (max 10)
            
        Returns:
            Search results with titles, URLs, snippets
        """
        try:
            import requests
            
            if not self.api_key:
                return {"status": "error", "message": "GOOGLE_API_KEY not set"}
            
            # Custom Search API endpoint
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": self.api_key,
                "cx": os.getenv("GOOGLE_CSE_ID", ""),  # Custom Search Engine ID
                "q": query,
                "num": min(num_results, 10)
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                for item in data.get("items", []):
                    results.append({
                        "title": item.get("title", ""),
                        "link": item.get("link", ""),
                        "snippet": item.get("snippet", ""),
                        "displayLink": item.get("displayLink", "")
                    })
                
                return {
                    "query": query,
                    "results": results,
                    "totalResults": data.get("searchInformation", {}).get("totalResults", "0"),
                    "status": "success"
                }
            else:
                return {
                    "status": "error",
                    "message": f"API error: {response.status_code}"
                }
                
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    # ============================================
    # GOOGLE NEWS (Free via RSS)
    # ============================================
    
    def google_news(self, topic: str = "technology", num_results: int = 5) -> Dict[str, Any]:
        """
        Fetch news from Google News RSS (100% free, no API key)
        
        Args:
            topic: News topic/search term
            num_results: Number of articles to return
            
        Returns:
            News articles with titles, links, dates
        """
        try:
            import requests
            import xml.etree.ElementTree as ET
            from datetime import datetime
            
            # Google News RSS feed (no API key needed!)
            url = f"https://news.google.com/rss/search?q={topic}&hl=en-US&gl=US&ceid=US:en"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                articles = []
                
                for item in root.findall(".//item")[:num_results]:
                    title = item.find("title")
                    link = item.find("link")
                    pub_date = item.find("pubDate")
                    source = item.find("source")
                    
                    articles.append({
                        "title": title.text if title is not None else "",
                        "link": link.text if link is not None else "",
                        "published": pub_date.text if pub_date is not None else "",
                        "source": source.text if source is not None else ""
                    })
                
                return {
                    "topic": topic,
                    "articles": articles,
                    "count": len(articles),
                    "timestamp": datetime.now().isoformat(),
                    "status": "success"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Request failed: {response.status_code}"
                }
                
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    # ============================================
    # YOUTUBE DATA API (Free: 10K quota/day)
    # ============================================
    
    def youtube_search(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Search YouTube videos using YouTube Data API v3
        
        Args:
            query: Search query
            max_results: Number of results (max 50)
            
        Returns:
            Video results with titles, IDs, thumbnails
        """
        try:
            import requests
            
            if not self.api_key:
                return {"status": "error", "message": "GOOGLE_API_KEY not set"}
            
            url = "https://www.googleapis.com/youtube/v3/search"
            params = {
                "key": self.api_key,
                "q": query,
                "part": "snippet",
                "type": "video",
                "maxResults": min(max_results, 50),
                "order": "relevance"
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                videos = []
                
                for item in data.get("items", []):
                    snippet = item.get("snippet", {})
                    videos.append({
                        "videoId": item["id"]["videoId"],
                        "title": snippet.get("title", ""),
                        "description": snippet.get("description", ""),
                        "channelTitle": snippet.get("channelTitle", ""),
                        "publishedAt": snippet.get("publishedAt", ""),
                        "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
                        "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}"
                    })
                
                return {
                    "query": query,
                    "videos": videos,
                    "count": len(videos),
                    "status": "success"
                }
            else:
                return {
                    "status": "error",
                    "message": f"API error: {response.status_code}"
                }
                
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    # ============================================
    # YOUTUBE TRENDING (Free: 10K quota/day)
    # ============================================
    
    def youtube_trending(self, category: str = "0", max_results: int = 10) -> Dict[str, Any]:
        """
        Get trending YouTube videos
        
        Args:
            category: Video category ID (0=All, 28=Science & Tech)
            max_results: Number of results
            
        Returns:
            Trending videos list
        """
        try:
            import requests
            
            if not self.api_key:
                return {"status": "error", "message": "GOOGLE_API_KEY not set"}
            
            url = "https://www.googleapis.com/youtube/v3/videos"
            params = {
                "key": self.api_key,
                "part": "snippet,statistics",
                "chart": "mostPopular",
                "regionCode": "US",
                "videoCategoryId": category,
                "maxResults": min(max_results, 50)
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                videos = []
                
                for item in data.get("items", []):
                    snippet = item.get("snippet", {})
                    stats = item.get("statistics", {})
                    
                    videos.append({
                        "videoId": item["id"],
                        "title": snippet.get("title", ""),
                        "channelTitle": snippet.get("channelTitle", ""),
                        "viewCount": stats.get("viewCount", "0"),
                        "likeCount": stats.get("likeCount", "0"),
                        "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
                        "url": f"https://www.youtube.com/watch?v={item['id']}"
                    })
                
                return {
                    "category": category,
                    "videos": videos,
                    "count": len(videos),
                    "status": "success"
                }
            else:
                return {
                    "status": "error",
                    "message": f"API error: {response.status_code}"
                }
                
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    # ============================================
    # GOOGLE TRENDS (Via Serpapi or similar)
    # ============================================
    
    def google_trends_topics(self) -> Dict[str, Any]:
        """
        Get current trending topics (uses Google Trends RSS)
        100% free, no API key
        """
        try:
            import requests
            import xml.etree.ElementTree as ET
            
            url = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=US"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                trends = []
                
                for item in root.findall(".//item")[:10]:
                    title = item.find("title")
                    traffic = item.find("{http://www.google.com/trends/}approx_traffic")
                    
                    trends.append({
                        "topic": title.text if title is not None else "",
                        "traffic": traffic.text if traffic is not None else "Unknown"
                    })
                
                return {
                    "trends": trends,
                    "count": len(trends),
                    "status": "success"
                }
            else:
                return {"status": "error", "message": f"Request failed: {response.status_code}"}
                
        except Exception as e:
            return {"status": "error", "message": str(e)}


# ============================================
# Export Google Tools Registry
# ============================================

def create_google_tools() -> Dict[str, Any]:
    """Create and return Google Cloud tools registry"""
    google = GoogleCloudTools()
    
    return {
        # Search & Discovery
        "google_search": google.custom_search,
        "google_news": google.google_news,
        "google_trends": google.google_trends_topics,
        
        # YouTube
        "youtube_search": google.youtube_search,
        "youtube_trending": google.youtube_trending,
    }


# Initialize on import
GOOGLE_TOOLS = create_google_tools()

__all__ = ['GoogleCloudTools', 'GOOGLE_TOOLS']
