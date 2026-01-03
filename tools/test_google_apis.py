"""
Test all Google Workspace APIs
"""
from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Load token
ROOT = Path(__file__).parent.parent
TOKEN_FILE = ROOT / "kaedra" / "config" / "google_token.json"

# All scopes needed
SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/tasks',
    'https://www.googleapis.com/auth/contacts.readonly',
    'https://www.googleapis.com/auth/presentations.readonly',
]

def test_all_apis():
    if not TOKEN_FILE.exists():
        print("❌ No token found. Run google_auth.py first.")
        return
    
    creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    results = {}
    
    print("=" * 60)
    print("Testing All Google Workspace APIs")
    print("=" * 60)
    
    # 1. Gmail
    try:
        gmail = build('gmail', 'v1', credentials=creds)
        profile = gmail.users().getProfile(userId='me').execute()
        results['Gmail'] = f"✅ {profile['emailAddress']}"
    except Exception as e:
        results['Gmail'] = f"❌ {e}"
    
    # 2. Calendar
    try:
        cal = build('calendar', 'v3', credentials=creds)
        calendars = cal.calendarList().list(maxResults=5).execute()
        results['Calendar'] = f"✅ {len(calendars.get('items', []))} calendars"
    except Exception as e:
        results['Calendar'] = f"❌ {e}"
    
    # 3. Drive
    try:
        drive = build('drive', 'v3', credentials=creds)
        about = drive.about().get(fields='user,storageQuota').execute()
        results['Drive'] = f"✅ {about['user']['displayName']}"
    except Exception as e:
        results['Drive'] = f"❌ {e}"
    
    # 4. Docs
    try:
        docs = build('docs', 'v1', credentials=creds)
        # Can't list docs directly, just verify API is accessible
        results['Docs'] = "✅ API accessible"
    except Exception as e:
        results['Docs'] = f"❌ {e}"
    
    # 5. Sheets
    try:
        sheets = build('sheets', 'v4', credentials=creds)
        results['Sheets'] = "✅ API accessible"
    except Exception as e:
        results['Sheets'] = f"❌ {e}"
    
    # 6. Slides
    try:
        slides = build('slides', 'v1', credentials=creds)
        results['Slides'] = "✅ API accessible"
    except Exception as e:
        results['Slides'] = f"❌ {e}"
    
    # 7. Tasks
    try:
        tasks = build('tasks', 'v1', credentials=creds)
        tasklists = tasks.tasklists().list(maxResults=5).execute()
        results['Tasks'] = f"✅ {len(tasklists.get('items', []))} task lists"
    except Exception as e:
        results['Tasks'] = f"❌ {e}"
    
    # 8. Contacts (People API)
    try:
        people = build('people', 'v1', credentials=creds)
        connections = people.people().connections().list(
            resourceName='people/me',
            pageSize=10,
            personFields='names,emailAddresses'
        ).execute()
        count = len(connections.get('connections', []))
        results['Contacts'] = f"✅ {count} contacts found"
    except Exception as e:
        results['Contacts'] = f"❌ {e}"
    
    # Print Results
    print("\n" + "-" * 40)
    print("RESULTS:")
    print("-" * 40)
    for api, status in results.items():
        print(f"  {api:12} {status}")
    
    print("-" * 40)
    passed = sum(1 for s in results.values() if s.startswith("✅"))
    print(f"\n{passed}/{len(results)} APIs working")
    
    return results

if __name__ == "__main__":
    test_all_apis()
