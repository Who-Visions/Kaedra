import sqlite3
import time
import os
import asyncio
import re
from typing import Optional, Callable, Awaitable, List, Dict, Any
from datetime import datetime

class WisprService:
    def __init__(self, db_path: str = None, callback: Callable[[str], Awaitable[None]] = None, wake_word_required: bool = True):
        if db_path is None:
            # Default path for Windows user
            db_path = os.path.expandvars(r"%APPDATA%\Wispr Flow\flow.sqlite")
        
        self.db_path = db_path
        self.callback = callback
        self.wake_word_required = wake_word_required
        self.running = False
        self.last_processed_timestamp = None
        self._polling_task = None

    # --- Active Query Methods (The Brain) ---

    def get_recent_transcripts(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Active Recall: Get the last N transcripts."""
        conn = self._get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            query = """
            SELECT asrText, formattedText, timestamp, status 
            FROM History 
            ORDER BY timestamp DESC 
            LIMIT ?
            """
            cursor.execute(query, (limit,))
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                results.append({
                    "text": row[1] or row[0], # formatted or asr
                    "timestamp": row[2],
                    "status": row[3]
                })
            return results
        finally:
            conn.close()

    def search_transcripts(self, query_text: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Active Recall: Search transcripts for keywords."""
        conn = self._get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            # SQLite safe LIKE search
            sql = """
            SELECT asrText, formattedText, timestamp, status 
            FROM History 
            WHERE formattedText LIKE ? OR asrText LIKE ?
            ORDER BY timestamp DESC 
            LIMIT ?
            """
            search_pattern = f"%{query_text}%"
            cursor.execute(sql, (search_pattern, search_pattern, limit))
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                results.append({
                    "text": row[1] or row[0],
                    "timestamp": row[2],
                    "status": row[3]
                })
            return results
        finally:
            conn.close()

    def get_all_transcripts(self) -> List[Dict[str, Any]]:
        """Active Recall: Get ALL transcripts for ingestion."""
        conn = self._get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            query = """
            SELECT asrText, formattedText, timestamp, status 
            FROM History 
            WHERE (formattedText IS NOT NULL AND formattedText != '') 
               OR (asrText IS NOT NULL AND asrText != '')
            ORDER BY timestamp ASC
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                results.append({
                    "text": row[1] or row[0], # formatted or asr
                    "timestamp": row[2],
                    "status": row[3]
                })
            return results
        finally:
            conn.close()

    # --- Passive Monitoring Methods (The Ear) ---

    async def start(self, on_commit=None, on_partial=None):
        """Starts the monitoring loop."""
        # Update callback if provided (UnifiedFlowEngine pattern)
        if on_commit:
            self.callback = on_commit
            
        if self.running:
            return
        
        print(f"[*] Starting Wispr Monitor on: {self.db_path}")
        if not os.path.exists(self.db_path):
             print(f"[!] Wispr DB not found at {self.db_path}. Monitoring aborted.")
             return

        self.running = True
        latest = self._get_latest_transcript_entry()
        if latest:
            self.last_processed_timestamp = latest.get('timestamp')
            txt_preview = (latest.get('formattedText') or latest.get('asrText') or "")[:50]
            print(f"[*] Wispr Connected. Last Context: '{txt_preview}...'")
        else:
            print("[*] Wispr Connected. Waiting for new dictation...")
        
        self._polling_task = asyncio.create_task(self._poll_loop())

    async def stop(self):
        """Stops the monitoring loop."""
        self.running = False
        if self._polling_task:
            self._polling_task.cancel()
            try:
                await self._polling_task
            except asyncio.CancelledError:
                pass
        print("[*] Wispr Monitor stopped.")

    async def _poll_loop(self):
        """Main polling loop."""
        while self.running:
            try:
                # We reuse the active method logic or query specifically for ONE
                entry = self._get_latest_transcript_entry()
                if entry:
                    timestamp = entry.get('timestamp')
                    text = entry.get('formattedText') or entry.get('asrText') or ""
                    
                    # Process if NEW timestamp OR (Same timestamp but text changed - unlikely for immutable logs but safe)
                    # Actually, let's stick to timestamp to avoid duplicate processing of the same static row.
                    # If Wispr updates row in place, we might need to track text hash. 
                    # For now, faster polling is the key.
                    
                    if timestamp and timestamp != self.last_processed_timestamp:
                        self.last_processed_timestamp = timestamp
                        await self._process_text(text)
                
                await asyncio.sleep(0.2) # 5x faster polling
            except Exception as e:
                print(f"[!] Error in Wispr poll loop: {e}")
                await asyncio.sleep(1)

    def _get_connection(self):
        """Helper for DB connection."""
        try:
            return sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
        except Exception as e:
            # print(f"[!] DB Connection Error: {e}") 
            return None

    def _get_latest_transcript_entry(self) -> Optional[dict]:
        """Synchronously reads the latest ONE row."""
        conn = self._get_connection()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT asrText, formattedText, timestamp FROM History ORDER BY timestamp DESC LIMIT 1")
            row = cursor.fetchone()
            if row:
                return {"asrText": row[0], "formattedText": row[1], "timestamp": row[2]}
            return None
        finally:
            conn.close()

    async def _process_text(self, text: str):
        """Analyzes text for wake word or emits all if streaming."""
        if not text:
            return
        
        # Mode 1: Continuous Stream (No Wake Word)
        if not self.wake_word_required:
            print(f"[Wispr] New Transcript: '{text[:50]}...'")
            if self.callback:
                if asyncio.iscoroutinefunction(self.callback):
                    await self.callback(text)
                else:
                    self.callback(text)
            return

        # Mode 2: Wake Word Only
        lower_text = text.lower()
        if "hey kaedra" in lower_text:
            print(f"[Wispr] Wake word detected in: '{text}'")
            parts = re.split(r"hey\s+kaedra", lower_text, flags=re.IGNORECASE)
            if len(parts) > 1:
                command = parts[-1].strip()
                if command and self.callback:
                    print(f"[Wispr] Command extracted: '{command}'")
                    if asyncio.iscoroutinefunction(self.callback):
                        await self.callback(command)
                    else:
                        self.callback(command)

# Alias for backward compatibility if needed, though we should update callers
WisprMonitor = WisprService
