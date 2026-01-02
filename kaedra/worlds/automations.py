from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, List, Dict

from .store import WORLD_ROOT, touch_last_played

class UniverseAutomations:
    """
    Automated logic for VeilVerse Universe database consistency.
    Operates on the JSON files within a World container.
    """

    def __init__(self, world_id: str):
        self.world_id = world_id
        self.path = WORLD_ROOT / world_id
        self._load_data()
        self.logs: List[str] = []

    def _load_data(self):
        self.bible_path = self.path / "world_bible.json"
        self.canon_path = self.path / "canon.json"
        self.timeline_path = self.path / "timeline.json"

        self.bible = json.loads(self.bible_path.read_text("utf-8")) if self.bible_path.exists() else {"sections": {}}
        self.canon = json.loads(self.canon_path.read_text("utf-8")) if self.canon_path.exists() else {"canon": []}
        self.timeline = json.loads(self.timeline_path.read_text("utf-8")) if self.timeline_path.exists() else {"events": []}

    def _save_data(self):
        self.bible_path.write_text(json.dumps(self.bible, indent=2), "utf-8")
        self.canon_path.write_text(json.dumps(self.canon, indent=2), "utf-8")
        self.timeline_path.write_text(json.dumps(self.timeline, indent=2), "utf-8")

    def log(self, msg: str):
        self.logs.append(msg)

    # 1. Canon Status Promotion Pipeline
    def run_canon_promotion(self):
        """
        Trigger: Canon Status set to Canon
        Action: Set Production Status to 'In Development', Update Last Updated.
        """
        count = 0
        # Iterate over Bible entries (assuming Flattened list or Sections)
        # Structure: bible['sections']['Characters'] = [ {name:..., props:...} ]
        
        for section, entries in self.bible.get("sections", {}).items():
            for entry in entries:
                props = entry.get("properties", {})
                
                if props.get("Canon Status") == "Canon":
                    changes = False
                    
                    # Auto-promote Production Status
                    if props.get("Production Status") == "Concept":
                        props["Production Status"] = "In Development"
                        self.log(f"✅ Promoted '{entry['name']}' to In Development")
                        changes = True
                    
                    # Update Timestamp
                    today = datetime.now().strftime("%Y-%m-%d")
                    if props.get("Last Updated") != today:
                        props["Last Updated"] = today
                        changes = True
                        
                    if changes:
                        count += 1
                        
        if count > 0:
            self.log(f"Processed canon promotion for {count} entries.")

    # 2. Retcon Safety Net
    def check_retcons(self):
        """
        Trigger: Canon Status set to Retconned
        Action: Set Status to Inactive, Add [RETCONNED] prefix.
        """
        for section, entries in self.bible.get("sections", {}).items():
            for entry in entries:
                props = entry.get("properties", {})
                
                if props.get("Canon Status") == "Retconned":
                    name = entry.get("name", "Unknown")
                    
                    if not name.startswith("[RETCONNED]"):
                        entry["name"] = f"[RETCONNED] {name}"
                        props["Status"] = "Inactive"
                        self.log(f"🚫 Retconned '{name}' -> Marked Inactive")

    # 5. Timeline Validator
    def validate_timeline(self):
        """
        Trigger: Timeline Year edited
        Action: Set Universe Era.
        """
        # Iterate timeline events
        events = self.timeline.get("events", [])
        for event in events:
            year_val = event.get("year")
            if year_val is None:
                continue
                
            try:
                year = int(str(year_val).replace("AD", "").replace("CE", "").strip())
                era = "Unknown"
                
                if year < 0:
                    era = "Ancient Era"
                elif 0 <= year <= 2000:
                    era = "Classical Era"
                elif 2001 <= year <= 2100:
                    era = "Modern Era" # VeilVerse Core
                elif year > 2100:
                    era = "Future Era"
                    
                if event.get("era") != era:
                    event["era"] = era
                    self.log(f"⏳ Timeline Fix: {event.get('name')} ({year}) -> {era}")

            except ValueError:
                pass

    # 6. Character Power Tracking
    def calculate_power_scores(self):
        """
        Trigger: Category=Character AND Power Level set
        Action: Calculate Importance Score.
        """
        chars = self.bible.get("sections", {}).get("Characters", [])
        for char in chars:
            props = char.get("properties", {})
            power = props.get("Power Level", "").lower()
            
            score = 0
            if "god" in power or "cosmic" in power or "planetesimal" in power:
                score = 95
            elif "high" in power or "omega" in power:
                score = 80
            elif "mid" in power or "alpha" in power:
                score = 60
            elif "low" in power or "street" in power:
                score = 40
                
            if score > 0 and props.get("Importance Score") != score:
                props["Importance Score"] = score
                self.log(f"⚡ Power Calc: {char['name']} ({power}) -> Score {score}")

    # 3. Production Status Auto-Advancement
    def run_production_advancement(self):
        for section, entries in self.bible.get("sections", {}).items():
            for entry in entries:
                props = entry.get("properties", {})
                if props.get("Production Status") == "Released":
                    if props.get("Status") != "Completed":
                        props["Status"] = "Completed"
                        props["Last Updated"] = datetime.now().strftime("%Y-%m-%d")
                        
                        # Add Phase 1 tag
                        appears = props.get("Appears In", [])
                        if isinstance(appears, str): appears = [appears] # normalize
                        if "Phase 1" not in appears:
                            appears.append("Phase 1")
                            props["Appears In"] = appears
                            
                        self.log(f"🎬 Production Release: '{entry['name']}' -> Completed & Phase 1")

    # 4. Weekly Concept Review
    def run_concept_review(self):
        # Trigger: Every Monday 9am (Simulated: Just run check and notify if day matches)
        now = datetime.now()
        if now.weekday() == 0: # Monday
             concepts = []
             for section, entries in self.bible.get("sections", {}).items():
                for entry in entries:
                    props = entry.get("properties", {})
                    if props.get("Production Status") == "Concept" and props.get("Canon Status") == "Canon":
                        concepts.append(entry["name"])
             
             if concepts:
                 self.notify(f"📋 Weekly Concept Review: {len(concepts)} items need dev work ({', '.join(concepts[:3])}...)")

    # 7. Auto Link Major Characters
    def auto_link_major_characters(self):
        chars = self.bible.get("sections", {}).get("Characters", [])
        major_chars = [c for c in chars if c.get("properties", {}).get("Importance") == "Major"]
        
        for char in major_chars:
            # Setup connections list if missing
            if "Connections" not in char:
                char["Connections"] = []
                
            # If newly Major (we don't track state change perfectly here without a delta log, but we can checks empty connections)
            if not char["Connections"] and len(major_chars) > 1:
                # Naive suggestion: just notify to review
                 self.notify(f"🔗 Major Character '{char['name']}': Review connections to existing Majors.")

    # 8. Event to Character Linking
    def queue_event_links(self):
        events = self.bible.get("sections", {}).get("Events", [])
        pending = self.bible.get("sections", {}).get("Pending Links", [])
        
        for evt in events:
            # logic: if event exists but has no character links?
            # User trigger: Category=Event.
            # We just ensure it's tracked in pending if brand new? 
            # Or simplified: Check if linked.
            pass # Implementation ambiguous without specific property, skipping to avoid noise.

    # 9. Media Release Notification
    def notify_media_release(self):
        media = self.bible.get("sections", {}).get("Media", [])
        for item in media:
            props = item.get("properties", {})
            if props.get("Production Status") == "Released":
                # Check if notification already sent? We use a "Notified" flag convention
                if not props.get("_meta_release_notified"):
                    self.notify(f"🚀 Media Release: '{item['name']}'. Social scheduler pinged.")
                    props["_meta_release_notified"] = True
                    
                    if props.get("Canon Status") == "Semi-Canon":
                        props["Canon Status"] = "Canon"
                        self.log(f"  -> Upgraded '{item['name']}' to Canon")

    # 10. Shadow Dweller Saga Tracker
    def track_shadow_dweller(self):
        for section, entries in self.bible.get("sections", {}).items():
            for entry in entries:
                props = entry.get("properties", {})
                franchise = props.get("Series/Franchise", [])
                if isinstance(franchise, str): franchise = [franchise]
                
                if any("Shadow Dweller" in f for f in franchise):
                    appears = props.get("Appears In", [])
                    if isinstance(appears, str): appears = [appears]
                    
                    changes = False
                    if "Shadow Dweller" not in appears:
                        appears.append("Shadow Dweller")
                        changes = True
                    if "Phase 1" not in appears:
                        appears.append("Phase 1")
                        changes = True
                        
                    if changes:
                        props["Appears In"] = appears
                        self.log(f"🌑 Shadow Dweller tagged: '{entry['name']}'")

    # 11. Ingestion to Canon
    def ingest_approved_items(self):
        ingest_path = self.path / "ingestion.json"
        if not ingest_path.exists():
            return
            
        ingestion = json.loads(ingest_path.read_text("utf-8"))
        items = ingestion.get("items", [])
        
        processed_count = 0
        for item in items:
            if item.get("status") == "Approved":
                # Create in Bible
                section = item.get("category", "General")
                if "sections" not in self.bible: self.bible["sections"] = {}
                if section not in self.bible["sections"]: self.bible["sections"][section] = []
                
                new_entry = {
                    "name": item.get("title", "Untitled"),
                    "properties": item.get("properties", {})
                }
                # Copy relevant props...
                
                self.bible["sections"][section].append(new_entry)
                
                item["status"] = "Imported"
                processed_count += 1
                self.log(f"📥 Ingested: '{new_entry['name']}' from Approved queue.")
                
        if processed_count > 0:
            ingestion["items"] = items
            ingest_path.write_text(json.dumps(ingestion, indent=2), "utf-8")

    def notify(self, message: str):
        """Append to notifications.md and log"""
        note_path = self.path / "notifications.md"
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        with open(note_path, "a", encoding="utf-8") as f:
            f.write(f"- [{ts}] {message}\n")
        self.log(f"🔔 {message}")

    # Main Execution
    def run_all(self) -> List[str]:
        self.run_canon_promotion()
        self.check_retcons()
        self.validate_timeline()
        self.calculate_power_scores()
        
        # New Automations
        self.run_production_advancement()
        self.run_concept_review()
        self.auto_link_major_characters()
        self.notify_media_release()
        self.track_shadow_dweller()
        self.ingest_approved_items()
        
        self._save_data()
        return self.logs

def run_automations_on_world(world_id: str) -> List[str]:
    auto = UniverseAutomations(world_id)
    return auto.run_all()
