"""
Gmail to Notion Integration for Dav1d
Auto-save important emails to Notion with AI categorization
"""

import os
import base64
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Google Auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Notion
from notion_client import Client as NotionClient

# Gemini for categorization
from google import genai
from google.genai import types

load_dotenv()

# Configuration
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
GMAIL_INBOX_DB = os.getenv("NOTION_GMAIL_DB_ID")  # Notion database for emails
PROJECT_ID = os.getenv("PROJECT_ID", "gen-lang-client-0285887798")
LOCATION = os.getenv("LOCATION", "us-east4")

# Gmail API Scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

if not NOTION_TOKEN:
    raise RuntimeError("NOTION_TOKEN not set in .env")

# Initialize clients
notion = NotionClient(auth=NOTION_TOKEN)
gemini_client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)


# ──────────────────────────────────────────────────────────────
# GMAIL AUTHENTICATION
# ──────────────────────────────────────────────────────────────

def get_gmail_service():
    """Authenticate with Gmail API using OAuth 2.0."""
    creds = None
    token_path = 'token_gmail.json'
    creds_path = 'credentials_gmail.json'
    
    # Load existing token
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    # Refresh or get new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(creds_path):
                raise FileNotFoundError(
                    f"Missing {creds_path}. Download from Google Cloud Console:\n"
                    "https://console.cloud.google.com/apis/credentials"
                )
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save token
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
    
    return build('gmail', 'v1', credentials=creds)


# ──────────────────────────────────────────────────────────────
# EMAIL PROCESSING
# ──────────────────────────────────────────────────────────────

def get_recent_emails(service, max_results: int = 10, query: str = "is:unread") -> List[Dict]:
    """Fetch recent emails from Gmail."""
    results = service.users().messages().list(
        userId='me',
        q=query,
        maxResults=max_results
    ).execute()
    
    messages = results.get('messages', [])
    emails = []
    
    for msg in messages:
        # Get full message
        message = service.users().messages().get(
            userId='me',
            id=msg['id'],
            format='full'
        ).execute()
        
        # Extract headers
        headers = {h['name']: h['value'] for h in message['payload']['headers']}
        
        # Extract body
        body = ""
        if 'parts' in message['payload']:
            for part in message['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    body_data = part['body'].get('data', '')
                    if body_data:
                        body = base64.urlsafe_b64decode(body_data).decode('utf-8')
                        break
        else:
            body_data = message['payload']['body'].get('data', '')
            if body_data:
                body = base64.urlsafe_b64decode(body_data).decode('utf-8')
        
        emails.append({
            'id': msg['id'],
            'thread_id': message['threadId'],
            'subject': headers.get('Subject', 'No Subject'),
            'from': headers.get('From', 'Unknown'),
            'to': headers.get('To', ''),
            'date': headers.get('Date', ''),
            'body': body[:5000]  # First 5000 chars
        })
    
    return emails


# ──────────────────────────────────────────────────────────────
# AI CATEGORIZATION
# ──────────────────────────────────────────────────────────────

async def categorize_email_with_gemini(email: Dict) -> Dict:
    """Use Gemini to categorize and extract insights from email."""
    
    prompt = f"""Analyze this email and provide structured insights.

Subject: {email['subject']}
From: {email['from']}
Date: {email['date']}

Body:
{email['body']}

Provide:
1. Category (work/personal/newsletter/spam/urgent)
2. Priority (low/medium/high/urgent)
3. Action required (yes/no)
4. Key points (3-5 bullets)
5. Suggested tags

Format as JSON:
{{
    "category": "work",
    "priority": "medium",
    "action_required": true,
    "key_points": ["point 1", "point 2"],
    "tags": ["tag1", "tag2"],
    "summary": "One sentence summary"
}}
"""
    
    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json"
            )
        )
        
        import json
        return json.loads(response.text)
    
    except Exception as e:
        print(f"❌ Gemini categorization failed: {e}")
        return {
            "category": "uncategorized",
            "priority": "low",
            "action_required": False,
            "key_points": [],
            "tags": [],
            "summary": email['subject']
        }


# ──────────────────────────────────────────────────────────────
# NOTION INTEGRATION
# ──────────────────────────────────────────────────────────────

async def save_email_to_notion(email: Dict, analysis: Dict) -> str:
    """Save email to Notion database with AI analysis."""
    
    if not GMAIL_INBOX_DB:
        print("⚠️  NOTION_GMAIL_DB_ID not set. Skipping Notion save.")
        return None
    
    try:
        # Create page properties
        properties = {
            "Subject": {
                "title": [
                    {"text": {"content": email['subject'][:2000]}}
                ]
            },
            "From": {
                "rich_text": [
                    {"text": {"content": email['from'][:2000]}}
                ]
            },
            "Category": {
                "select": {"name": analysis.get('category', 'uncategorized').capitalize()}
            },
            "Priority": {
                "select": {"name": analysis.get('priority', 'low').capitalize()}
            },
            "Action Required": {
                "checkbox": analysis.get('action_required', False)
            },
            "Date": {
                "date": {"start": datetime.now().isoformat()}
            }
        }
        
        # Add tags if multi_select exists
        if analysis.get('tags'):
            properties["Tags"] = {
                "multi_select": [{"name": tag} for tag in analysis['tags'][:5]]
            }
        
        # Create page content with email body and analysis
        children = [
            {
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [
                        {"text": {"content": f"🤖 {analysis.get('summary', '')}"}}
                    ],
                    "icon": {"emoji": "📧"},
                    "color": "blue_background"
                }
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "Key Points"}}]
                }
            }
        ]
        
        # Add key points
        for point in analysis.get('key_points', []):
            children.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"text": {"content": point[:2000]}}]
                }
            })
        
        # Add email body
        children.extend([
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "Email Body"}}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"text": {"content": email['body'][:2000]}}]
                }
            }
        ])
        
        # Create Notion page
        page = notion.pages.create(
            parent={"database_id": GMAIL_INBOX_DB},
            properties=properties,
            children=children
        )
        
        print(f"✅ Saved to Notion: {email['subject'][:50]}")
        return page['id']
    
    except Exception as e:
        print(f"❌ Failed to save to Notion: {e}")
        import traceback
        traceback.print_exc()
        return None


# ──────────────────────────────────────────────────────────────
# MAIN SYNC FUNCTION
# ──────────────────────────────────────────────────────────────

async def sync_gmail_to_notion(max_emails: int = 10, query: str = "is:unread"):
    """
    Main sync function:
    1. Fetch unread emails from Gmail
    2. Analyze with Gemini
    3. Save to Notion
    """
    
    print(f"📧 Syncing Gmail to Notion...")
    print(f"Query: {query} | Max: {max_emails}")
    
    try:
        # Get Gmail service
        service = get_gmail_service()
        
        # Fetch emails
        emails = get_recent_emails(service, max_results=max_emails, query=query)
        print(f"📬 Found {len(emails)} emails")
        
        if not emails:
            print("✅ No emails to process")
            return
        
        # Process each email
        for i, email in enumerate(emails, 1):
            print(f"\n[{i}/{len(emails)}] Processing: {email['subject'][:50]}")
            
            # Analyze with Gemini
            analysis = await categorize_email_with_gemini(email)
            print(f"   Category: {analysis.get('category')} | Priority: {analysis.get('priority')}")
            
            # Save to Notion
            page_id = await save_email_to_notion(email, analysis)
            
            if page_id:
                print(f"   ✅ Notion page: {page_id[:8]}")
        
        print(f"\n✅ Sync complete! Processed {len(emails)} emails")
    
    except Exception as e:
        print(f"❌ Sync failed: {e}")
        import traceback
        traceback.print_exc()


# ──────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import asyncio
    import argparse
    
    parser = argparse.ArgumentParser(description="Sync Gmail to Notion")
    parser.add_argument("--max", type=int, default=10, help="Max emails to process")
    parser.add_argument("--query", type=str, default="is:unread", help="Gmail search query")
    
    args = parser.parse_args()
    
    print("🚀 Gmail to Notion Sync - Dav1d")
    print("=" * 50)
    
    asyncio.run(sync_gmail_to_notion(max_emails=args.max, query=args.query))
