"""
🌍 WorldForge v9.1 - Reverse Engineering Context
Splits transcripts, extracts cited facts, and builds structured "World Bibles".
"""
import json
import os
import math
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from google import genai
from google.genai import types
from kaedra.core.config import PROJECT_ID
from kaedra.story.config import PRO_MODEL, FLASH_MODEL

@dataclass
class TranscriptChunk:
    chunk_id: str
    start_s: float
    end_s: float
    text: str

class TranscriptChunker:
    """Splits raw transcript into citation-ready chunks."""
    
    def __init__(self, target_tokens: int = 2000):
        self.target_tokens = target_tokens

    def load_and_chunk(self, json_path: str) -> List[TranscriptChunk]:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        full_transcript = data.get("transcript", [])
        if not full_transcript:
            return []
            
        chunks = []
        current_text = []
        current_start = full_transcript[0].get("start_s", 0)
        current_tokens = 0
        chunk_idx = 1
        
        for seg in full_transcript:
            text = seg.get("text", "")
            start = seg.get("start_s", 0)
            end = seg.get("end_s", 0)
            tokens = len(text.split()) # Approx
            
            current_text.append(text)
            current_tokens += tokens
            
            if current_tokens >= self.target_tokens:
                # Seal chunk
                chunk_id = f"c{chunk_idx:03d}"
                joined_text = " ".join(current_text)
                chunks.append(TranscriptChunk(chunk_id, current_start, end, joined_text))
                
                # Reset
                chunk_idx += 1
                current_text = []
                current_start = end # Roughly
                current_tokens = 0
                
        # Final flush
        if current_text:
             chunk_id = f"c{chunk_idx:03d}"
             joined_text = " ".join(current_text)
             chunks.append(TranscriptChunk(chunk_id, current_start, full_transcript[-1].get("end_s", 0), joined_text))
             
        return chunks

class WorldExtractor:
    """Wraps LLM calls to extract structured facts with citations."""
    
    def __init__(self, client: genai.Client):
        self.client = client
        
    def extract_claims(self, chunks: List[TranscriptChunk]) -> dict:
        """Extract purely cited claims (Canon)."""
        prompt = """
        Analyze these transcript chunks. Extract PROVEN FACTS covering:
        - Factions, Locations, Entities, Items, History, Rules/Laws.
        
        CRITICAL: 
        1. Every claim MUST include 'evidence': ["c###"] referencing the exact source chunk.
        2. If a fact is implied but not stated, omit it here. Canon only.
        
        Return JSON structure:
        {
          "claims": [
            {
              "id": "claim_001", 
              "type": "faction|location|event|item|rule", 
              "summary": "...", 
              "evidence": ["c001"]
            }
          ]
        }
        """
        
        # Batch chunks for context window
        context_str = "\n\n".join([f"[{c.chunk_id} ({c.start_s:.0f}s-{c.end_s:.0f}s)] {c.text}" for c in chunks])
        
        try:
            # Check total length to avoid context overflow (defensive)
            # Gemini 1.5 Pro has 1-2M window, so this is rarely an issue for transcripts.
            resp = self.client.models.generate_content(
                model=PRO_MODEL,
                contents=prompt + "\n\nTRANSCRIPT DATA:\n" + context_str,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.0
                )
            )
            return json.loads(resp.text)
        except Exception as e:
            print(f"Extraction Error: {e}")
            return {"claims": []}

    def build_world_model(self, claims: dict, chunks: List[TranscriptChunk]) -> dict:
        """Synthesize structured entities from claims."""
        prompt = """
        Using these verified claims, build a structured World Model.
        Synthesize disparate claims into coherent entities.
        
        Return JSON matching this schema:
        {
          "locations": [{"id":"", "name":"", "type":"", "geography":{}, "evidence":["c..."]}],
          "factions": [{"id":"", "name":"", "ideology":"", "evidence":["c..."]}],
          "items": [{"id":"", "name":"", "type":"", "evidence":["c..."]}],
          "timeline": [{"id":"", "name":"", "when":{}, "evidence":["c..."]}]
        }
        """
        claims_str = json.dumps(claims)
        
        try:
            resp = self.client.models.generate_content(
                model=PRO_MODEL, # Reasoning model best for synthesis
                contents=prompt + "\n\nCLAIMS DATA:\n" + claims_str,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )
            return json.loads(resp.text)
        except Exception as e:
             print(f"Synthesis Error: {e}")
             return {}

    def generate_expansion(self, world_model: dict) -> dict:
        """Creative pass: generate NPCs, hooks, and subplots."""
        prompt = """
        Based on this World Model, generate CREATIVE EXPANSIONS.
        Invent content that fits the tone but fills the gaps.
        
        Return JSON:
        {
          "generated_npcs": [{"name":"", "role":"", "hook":"", "anchored_to_canon": "ref_id"}],
          "quest_hooks": [{"title":"", "description":"", "anchored_to_canon": "ref_id"}]
        }
        """
        model_str = json.dumps(world_model)
        
        try:
            resp = self.client.models.generate_content(
                model=FLASH_MODEL, # Flash is fine for creative storming
                contents=prompt + "\n\nWORLD MODEL:\n" + model_str,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.7
                )
            )
            return json.loads(resp.text)
        except Exception as e:
            return {}

class WorldForge:
    """Pipeline Orchestrator."""
    
    def __init__(self):
        self.client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")
        self.chunker = TranscriptChunker()
        self.extractor = WorldExtractor(self.client)
        
    def forge(self, video_id: str, ingest_path: str) -> str:
        """Run full pipeline: Ingest -> Chunk -> Extract -> Synthesize -> Save."""
        
        # 1. Output Setup
        out_dir = Path("lore/worlds") / video_id
        out_dir.mkdir(parents=True, exist_ok=True)
        
        # 2. Chunking
        print(f"[WorldForge] Chunking transcript from {ingest_path}...")
        chunks = self.chunker.load_and_chunk(ingest_path)
        
        # Save chunks
        chunks_data = [c.__dict__ for c in chunks]
        with open(out_dir / "chunks.json", "w") as f:
            json.dump(chunks_data, f, indent=2)
            
        if not chunks:
            return f"Error: No transcript found in {ingest_path}"
            
        # 3. Extraction (Canon)
        print(f"[WorldForge] Extracting canon claims ({len(chunks)} chunks)...")
        canon_data = self.extractor.extract_claims(chunks)
        with open(out_dir / "canon.json", "w") as f:
            json.dump(canon_data, f, indent=2)
            
        # 4. Synthesis (World Model)
        print("[WorldForge] Building structured World Model...")
        world_model = self.extractor.build_world_model(canon_data, chunks)
        with open(out_dir / "world_model.json", "w") as f:
            json.dump(world_model, f, indent=2)
            
        # 5. Expansion (Creative)
        print("[WorldForge] Generating creative expansion...")
        expansion = self.extractor.generate_expansion(world_model)
        with open(out_dir / "expansion.json", "w") as f:
            json.dump(expansion, f, indent=2)
            
        # 6. Final Bible Assembly
        bible = {
            "source": {"video_id": video_id, "ingested_file": ingest_path},
            "canon": canon_data,
            "world_model": world_model,
            "expansion": expansion
        }
        bible_path = out_dir / "world_bible.json"
        with open(bible_path, "w") as f:
            json.dump(bible, f, indent=2)
            
        return str(bible_path)

