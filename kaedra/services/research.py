"""
KAEDRA v0.0.6 - Research Service
Orchestrates deep research by combining Search, Scraping, and Synthesis.
"""

import asyncio
import uuid
import logging
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from ..core.google_tools import GOOGLE_TOOLS
from .web import WebService
from .prompt import PromptService

logger = logging.getLogger("kaedra.services.research")

@dataclass
class ResearchTask:
    id: str
    query: str
    status: str  # pending, researching, synthesizing, completed, failed
    created_at: float
    updated_at: float
    results: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

class ResearchService:
    """
    Orchestrates Deep Research tasks.
    """
    
    def __init__(self, prompt_service: PromptService):
        self.prompt_service = prompt_service
        self.web_service = WebService()
        self._tasks: Dict[str, ResearchTask] = {}
        
    def create_task(self, query: str) -> str:
        """Create a new research task and return its ID."""
        task_id = str(uuid.uuid4())
        now = time.time()
        
        task = ResearchTask(
            id=task_id,
            query=query,
            status="pending",
            created_at=now,
            updated_at=now
        )
        self._tasks[task_id] = task
        
        # Start background task
        asyncio.create_task(self._process_research(task_id))
        
        return task_id
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status and results."""
        task = self._tasks.get(task_id)
        if not task:
            return None
            
        return {
            "id": task.id,
            "query": task.query,
            "status": task.status,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
            "results": task.results,
            "error": task.error
        }
        
    async def _process_research(self, task_id: str):
        """Execute the research pipeline."""
        task = self._tasks[task_id]
        task.status = "researching"
        task.updated_at = time.time()
        
        try:
            # 1. Search
            logger.info(f"Researching: {task.query}")
            search_results = GOOGLE_TOOLS["google_search"](task.query, num_results=5)
            
            if search_results.get("status") == "error":
                raise Exception(f"Search failed: {search_results.get('message')}")
                
            urls = [item['link'] for item in search_results.get('results', [])[:3]]
            
            # 2. Scrape (Concurrent)
            scraped_data = []
            for url in urls:
                try:
                    # Note: synchronous calls in asyncio for now, ideally make web_service async
                    page = self.web_service.fetch(url)
                    if page.status_code == 200:
                        scraped_data.append(f"SOURCE: {page.url}\nTITLE: {page.title}\nCONTENT:\n{page.content[:5000]}")
                except Exception as e:
                    logger.warning(f"Failed to scrape {url}: {e}")
            
            combined_context = "\n\n---\n\n".join(scraped_data)
            
            # 3. Synthesize
            task.status = "synthesizing"
            task.updated_at = time.time()
            
            prompt = f"""
            You are conducting DEEP RESEARCH on: "{task.query}"
            
            Synthesize the following gathered information into a comprehensive report.
            Focus on facts, dates, key figures, and technical details.
            
            SOURCES:
            {combined_context}
            
            REPORT FORMAT:
            # Executive Summary
            # Key Findings
            # Detailed Analysis
            # Sources
            """
            
            # Use Gemini 3 Pro for synthesis if available
            result = await self.prompt_service.generate_async(
                prompt=prompt,
                model_key="pro",
                system_instruction="You are an expert research analyst."
            )
            
            task.results = {
                "report": result.text,
                "sources": urls,
                "model": result.model
            }
            task.status = "completed"
            
        except Exception as e:
            logger.error(f"Research failed for {task_id}: {e}")
            task.status = "failed"
            task.error = str(e)
        finally:
            task.updated_at = time.time()
