import os
import base64
from typing import List, Dict, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Gmail API Scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

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
            # Try Application Default Credentials (ADC) as fallback
            try:
                import google.auth
                print("Attempting to load Application Default Credentials...")
                default_creds, _ = google.auth.default(scopes=SCOPES)
                creds = default_creds
            except Exception as e:
                print(f"ADC load failed: {e}")

            # If ADC failed or wasn't sufficient, check for local credentials file
            if not creds and os.path.exists(creds_path):
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                    creds = flow.run_local_server(port=0)
                    # Save token only if we did the flow
                    with open(token_path, 'w') as token:
                        token.write(creds.to_json())
                except Exception as flow_error:
                    print(f"OAuth flow failed: {flow_error}")
            
            if not creds:
                return None  # Indicate failure to find credentials
    
    return build('gmail', 'v1', credentials=creds)

def list_emails(max_results: int = 5, query: str = "is:unread") -> Dict:
    """
    List recent emails from Gmail.
    
    Args:
        max_results: Number of emails to return (default: 5)
        query: Gmail search query (default: "is:unread")
        
    Returns:
        Dict containing list of emails or error message.
    """
    try:
        service = get_gmail_service()
        if not service:
            return {
                "success": False, 
                "error": "Gmail credentials not found. Please ensure 'credentials_gmail.json' or 'token_gmail.json' is in the root directory."
            }
        
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=max_results
        ).execute()
        
        messages = results.get('messages', [])
        emails = []
        
        for msg in messages:
            try:
                # Get full message
                message = service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='full'
                ).execute()
                
                # Extract headers
                headers = {h['name']: h['value'] for h in message['payload']['headers']}
                
                # Extract body snippet
                snippet = message.get('snippet', '')
                
                emails.append({
                    'from': headers.get('From', 'Unknown'),
                    'subject': headers.get('Subject', 'No Subject'),
                    'date': headers.get('Date', ''),
                    'snippet': snippet
                })
            except Exception as e:
                print(f"Error processing message {msg['id']}: {e}")
                continue
        
        return {
            "success": True,
            "count": len(emails),
            "emails": emails
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}
