"""
KAEDRA v0.0.6 - Web Service
Web fetching, scraping, and search capabilities.
"""

import requests
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger("kaedra.services.web")


@dataclass
class WebPage:
    """Represents a fetched web page."""
    url: str
    title: str
    content: str
    status_code: int
    headers: Dict[str, str]


class WebService:
    """
    Web fetching and scraping service.
    
    Features:
    - Fetch URLs and extract content
    - Clean HTML to readable text
    - Extract metadata (title, description)
    - Handle errors gracefully
    """
    
    def __init__(self, timeout: int = 10, user_agent: str = None):
        self.timeout = timeout
        self.user_agent = user_agent or "KAEDRA/0.0.6 (Who Visions LLC)"
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})
    
    def fetch(self, url: str) -> WebPage:
        """
        Fetch a URL and return cleaned content.
        
        Args:
            url: URL to fetch
            
        Returns:
            WebPage object with title and content
        """
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            title = soup.title.string if soup.title else url
            
            # Remove script and style elements
            for element in soup(['script', 'style', 'nav', 'footer', 'iframe']):
                element.decompose()
            
            # Get text content
            text = soup.get_text(separator='\n', strip=True)
            
            # Clean up whitespace
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            content = '\n'.join(lines)
            
            logger.info(f"Successfully fetched: {url}")
            
            return WebPage(
                url=url,
                title=title,
                content=content[:10000],  # Limit to 10k chars
                status_code=response.status_code,
                headers=dict(response.headers)
            )
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return WebPage(
                url=url,
                title="Error",
                content=f"Failed to fetch URL: {e}",
                status_code=0,
                headers={}
            )
    
    def search_web(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """
        Perform web search (placeholder - requires search API).
        
        Note: This is a stub. In production, integrate with:
        - Google Custom Search API
        - Bing Search API
        - DuckDuckGo API
        - Or use Vertex AI's built-in grounding
        
        Args:
            query: Search query
            num_results: Number of results to return
            
        Returns:
            List of search results
        """
        # For now, return a message explaining to use Vertex AI grounding
        return [{
            "title": "Web Search via Vertex AI",
            "url": "built-in",
            "snippet": "KAEDRA uses Vertex AI's Google Search grounding for web searches. "
                      "Just ask your question naturally, and I'll search for you automatically."
        }]
    
    def extract_metadata(self, url: str) -> Dict[str, Any]:
        """Extract metadata from a webpage."""
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            metadata = {
                "url": url,
                "title": soup.title.string if soup.title else None,
                "description": None,
                "og_title": None,
                "og_description": None,
                "og_image": None,
            }
            
            # Meta description
            desc_tag = soup.find('meta', attrs={'name': 'description'})
            if desc_tag:
                metadata["description"] = desc_tag.get('content')
            
            # Open Graph tags
            og_title = soup.find('meta', attrs={'property': 'og:title'})
            if og_title:
                metadata["og_title"] = og_title.get('content')
            
            og_desc = soup.find('meta', attrs={'property': 'og:description'})
            if og_desc:
                metadata["og_description"] = og_desc.get('content')
            
            og_img = soup.find('meta', attrs={'property': 'og:image'})
            if og_img:
                metadata["og_image"] = og_img.get('content')
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to extract metadata from {url}: {e}")
            return {"url": url, "error": str(e)}
    
    def close(self):
        """Close the session."""
        self.session.close()
