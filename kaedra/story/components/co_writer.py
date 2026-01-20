
"""
✍️ CoWriter Component
Integrates 'Rhea Noir' (Co-Author) into the StoryEngine via her Cloud Run endpoint.
"""

import requests
import time
from typing import Optional, Dict, List
from rich.console import Console

console = Console()

class CoWriter:
    """Interface for the Rhea Noir co-writing agent."""
    
    BASE_URL = "https://rhea-noir-145241643240.us-central1.run.app"
    MODEL = "rhea-noir"
    
    # Cold start handling
    TIMEOUT = 90
    MAX_RETRIES = 3
    RETRY_DELAY = 5
    
    _PROTOCOL_CACHE = None
    _LAST_LOAD = 0
    CACHE_TTL = 3600 # 1 hour
    
    def __init__(self, warmup: bool = False):
        self.session_id = None
        self.last_response = None
        self._warmed_up = False
        
        if warmup:
            self.warmup()
    
    def warmup(self) -> bool:
        """Warm up using /health/detailed endpoint."""
        if self._warmed_up:
            return True
            
        console.print("[dim]🔥 Warming up Rhea...[/]")
        try:
            resp = requests.get(f"{self.BASE_URL}/health/detailed", timeout=60)
            if resp.status_code == 200:
                data = resp.json()
                console.print(f"[dim green]✅ Rhea online: {data.get('status', 'ready')}[/]")
                self._warmed_up = True
                return True
            return False
        except Exception as e:
            console.print(f"[dim yellow]⚠️ Warmup: {e}[/]")
            return False
    
    def consult(self, prompt: str, context: Optional[str] = None, thinking_level: str = "low") -> str:
        """Send a prompt to Rhea and get her response."""
        url = f"{self.BASE_URL}/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        
        # Load protocol with caching
        now = time.time()
        if not CoWriter._PROTOCOL_CACHE or (now - CoWriter._LAST_LOAD > CoWriter.CACHE_TTL):
            try:
                with open("lore/co_writing_protocol.md", "r", encoding="utf-8") as f:
                    CoWriter._PROTOCOL_CACHE = f.read()
                CoWriter._LAST_LOAD = now
            except:
                CoWriter._PROTOCOL_CACHE = "You are Rhea Noir, a co-author and narrative consultant."

        system_content = CoWriter._PROTOCOL_CACHE
        if context:
            system_content += f"\n\nCONTEXT:\n{context}"
            
        payload = {
            "messages": [
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "thinking_level": thinking_level
        }

        
        return self._request_with_retry("POST", url, payload)
    
    def cowrite(self, prompt: str, context: Optional[str] = None, mode: str = "prose", thinking_level: str = "low") -> str:
        """Dedicated cowrite endpoint call to Rhea."""
        url = f"{self.BASE_URL}/cowrite"
        payload = {
            "prompt": prompt,
            "context": context,
            "mode": mode,
            "thinking_level": thinking_level
        }
        return self._request_with_retry("POST", url, payload)
    
    def _request_with_retry(self, method: str, url: str, payload: Dict) -> str:
        """Make request with retry logic for cold starts."""
        headers = {"Content-Type": "application/json"}
        last_error = None
        
        for attempt in range(self.MAX_RETRIES):
            try:
                if attempt > 0:
                    delay = self.RETRY_DELAY * (2 ** (attempt - 1))
                    console.print(f"[dim yellow]⏳ Retry {attempt + 1}/{self.MAX_RETRIES} in {delay}s...[/]")
                    time.sleep(delay)
                
                if method == "POST":
                    resp = requests.post(url, json=payload, headers=headers, timeout=self.TIMEOUT)
                else:
                    resp = requests.get(url, params=payload, headers=headers, timeout=self.TIMEOUT)
                
                if resp.status_code == 200:
                    data = resp.json()
                    # Handle OpenAI-compatible response format
                    content = data.get("choices", [{}])[0].get("message", {}).get("content")
                    if not content:
                        # Try other response formats
                        content = data.get("content") or data.get("text") or data.get("response") or str(data)
                    self.last_response = content
                    self._warmed_up = True
                    return content
                else:
                    last_error = f"Status {resp.status_code}: {resp.text[:200]}"
                    console.print(f"[dim red]⚠️ API error: {last_error}[/]")
                    
            except requests.exceptions.Timeout:
                last_error = "Request timed out"
                console.print(f"[dim yellow]⏱️ Timeout on attempt {attempt + 1}[/]")
            except Exception as e:
                last_error = str(e)
        
        return f"[!] Rhea unavailable after {self.MAX_RETRIES} attempts: {last_error}"
    
    def critique(self, scene_text: str) -> str:
        """Ask Rhea to critique a scene."""
        return self.consult(
            f"Critique this scene. Focus on pacing, dialogue, character voice.\n\nSCENE:\n{scene_text}"
        )
    
    def brainstorm(self, topic: str) -> str:
        """Brainstorm ideas."""
        return self.consult(f"Brainstorm ideas for: {topic}. Give 3 distinct options.")
    
    def write_dialogue(self, setup: str, characters: List[str]) -> str:
        """Generate dialogue."""
        return self.consult(
            f"Write dialogue for this scene:\n{setup}\nCharacters: {', '.join(characters)}"
        )
    
    def health_check(self) -> Dict:
        """Detailed health check."""
        try:
            start = time.perf_counter()
            resp = requests.get(f"{self.BASE_URL}/health/detailed", timeout=30)
            latency = time.perf_counter() - start
            
            if resp.status_code == 200:
                data = resp.json()
                data["latency_ms"] = round(latency * 1000, 2)
                data["warmed_up"] = self._warmed_up
                return data
            return {"status": "degraded", "code": resp.status_code}
        except Exception as e:
            return {"status": "offline", "error": str(e)}
