"""
Google Workspace Service for Kaedra
Handles Gmail, Calendar, and other Workspace APIs.
"""
import os
import json
from pathlib import Path
from typing import Optional, List, Dict
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta

class GoogleWorkspaceService:
    def __init__(self, token_path: Optional[Path] = None):
        self.root = Path(__file__).parent.parent.parent
        self.token_path = token_path or (self.root / "kaedra" / "config" / "google_token.json")
        self.creds = None
        self.services = {}
        
        if self.token_path.exists():
            try:
                self.creds = Credentials.from_authorized_user_file(str(self.token_path))
            except Exception as e:
                print(f"[!] Failed to load Google credentials: {e}")

    def _get_service(self, name: str, version: str):
        if not self.creds:
            return None
        key = f"{name}_{version}"
        if key not in self.services:
            self.services[key] = build(name, version, credentials=self.creds)
        return self.services[key]

    def list_emails(self, max_results: int = 5) -> list:
        """Fetch news emails from inbox."""
        service = self._get_service('gmail', 'v1')
        if not service: return []
        
        results = service.users().messages().list(userId='me', labelIds=['INBOX'], maxResults=max_results).execute()
        messages = results.get('messages', [])
        
        emails = []
        for msg in messages:
            m = service.users().messages().get(userId='me', id=msg['id'], format='metadata', metadataHeaders=['Subject', 'From', 'Date']).execute()
            headers = m.get('payload', {}).get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown')
            emails.append({
                "id": msg['id'],
                "subject": subject,
                "from": sender,
                "date": date,
                "snippet": m.get('snippet', '')
            })
        return emails

    def list_events(self, days: int = 1) -> list:
        """Fetch calendar events for the next X days."""
        service = self._get_service('calendar', 'v3')
        if not service: return []
        
        now = datetime.utcnow().isoformat() + 'Z'
        end = (datetime.utcnow() + timedelta(days=days)).isoformat() + 'Z'
        
        events_result = service.events().list(
            calendarId='primary', timeMin=now, timeMax=end,
            singleEvents=True, orderBy='startTime'
        ).execute()
        
        return events_result.get('items', [])

    def list_tasks(self, max_results: int = 10) -> list:
        """Fetch tasks from the primary task list."""
        service = self._get_service('tasks', 'v1')
        if not service: return []
        
        results = service.tasklists().list(maxResults=1).execute()
        tasklists = results.get('items', [])
        if not tasklists: return []
        
        list_id = tasklists[0]['id']
        tasks_result = service.tasks().list(tasklist=list_id, maxResults=max_results).execute()
        return tasks_result.get('items', [])

    def list_channel_videos(self, channel_handle: str, max_results: int = 50) -> List[Dict]:
        """Fetch videos from a channel using YouTube Data API."""
        service = self._get_service('youtube', 'v3')
        if not service: return []

        # 1. Resolve handle to channel ID (if starts with @)
        search_res = service.search().list(
            q=channel_handle,
            type='channel',
            part='id,snippet',
            maxResults=1
        ).execute()
        
        items = search_res.get('items', [])
        if not items: return []
        
        channel_id = items[0]['id']['channelId']
        
        # 2. List videos
        videos_res = service.search().list(
            channelId=channel_id,
            part='id,snippet',
            order='date',
            type='video',
            maxResults=max_results
        ).execute()
        
        videos = []
        for v in videos_res.get('items', []):
            videos.append({
                "id": v['id']['videoId'],
                "title": v['snippet']['title'],
                "url": f"https://www.youtube.com/watch?v={v['id']['videoId']}"
            })
        return videos
