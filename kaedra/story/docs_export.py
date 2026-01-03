"""
Google Docs Screenplay Export
Exports formatted screenplay drafts to Google Docs with industry-standard formatting.
"""
import os
from pathlib import Path
from typing import Optional, List
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Paths
ROOT = Path(__file__).parent.parent  # kaedra_proper/kaedra
CONFIG_DIR = ROOT / "config"
TOKEN_FILE = CONFIG_DIR / "google_token.json"

# SJSU Screenplay Format Constants
SCREENPLAY_FONT = "Courier New"
SCREENPLAY_FONT_SIZE = 12  # points

# Margins in points (72 points = 1 inch)
MARGINS = {
    "top": 72,        # 1 inch
    "bottom": 72,     # 1 inch
    "left": 108,      # 1.5 inches
    "right": 72,      # 1 inch
}

# Veil Verse Folder Structure
VEIL_VERSE_STRUCTURE = {
    "root": "Veil Verse",
    "subfolders": [
        "Scripts",       # Screenplay drafts, treatments
        "References",    # Research, inspiration docs
        "Assets",        # Photos, images, visual references
        "Lore",          # World-building, character bibles
        "Archive",       # Old versions, backups
    ]
}

# Google Drive for Desktop Local Mount (I: drive)
DRIVE_LOCAL_PATH = Path("I:/My Drive/Veil Verse")
DRIVE_MOUNTED = DRIVE_LOCAL_PATH.exists()


def get_credentials() -> Optional[Credentials]:
    """Load saved Google OAuth credentials."""
    if not TOKEN_FILE.exists():
        print(f"❌ No token file found: {TOKEN_FILE}")
        print("   Run: python tools/google_auth.py")
        return None
    
    from google.auth.transport.requests import Request
    
    # Use scopes matching existing token from google_auth.py
    scopes = [
        'https://www.googleapis.com/auth/documents',
        'https://www.googleapis.com/auth/drive',  # Match existing token
    ]
    creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), scopes)
    
    # Refresh and SAVE the refreshed token
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
        print("🔄 Token refreshed and saved.")
    
    return creds


def get_or_create_folder(name: str) -> Optional[str]:
    """Get folder ID by name, or create it if it doesn't exist."""
    creds = get_credentials()
    if not creds:
        return None
    
    try:
        service = build('drive', 'v3', credentials=creds)
        
        # Search for existing folder
        q = f"mimeType='application/vnd.google-apps.folder' and trashed=false and name='{name}'"
        results = service.files().list(q=q, fields="files(id, name)").execute()
        files = results.get('files', [])
        
        if files:
            folder_id = files[0]['id']
            print(f"📁 Found folder: {name} (ID: {folder_id})")
            return folder_id
        
        # Create folder if not found
        folder_metadata = {
            'name': name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = service.files().create(body=folder_metadata, fields='id').execute()
        folder_id = folder['id']
        print(f"📁 Created folder: {name} (ID: {folder_id})")
        return folder_id
        
    except Exception as e:
        print(f"❌ Folder operation failed: {e}")
        return None


def setup_veil_verse_structure() -> dict:
    """
    Create the full Veil Verse folder structure in Google Drive.
    Returns dict of {subfolder_name: folder_id}.
    """
    creds = get_credentials()
    if not creds:
        return {}
    
    try:
        service = build('drive', 'v3', credentials=creds)
        
        # Get or create root folder
        root_id = get_or_create_folder(VEIL_VERSE_STRUCTURE["root"])
        if not root_id:
            return {}
        
        folder_ids = {"root": root_id}
        
        # Create subfolders inside root
        for subfolder_name in VEIL_VERSE_STRUCTURE["subfolders"]:
            # Search for existing subfolder
            q = (
                f"mimeType='application/vnd.google-apps.folder' "
                f"and trashed=false "
                f"and name='{subfolder_name}' "
                f"and '{root_id}' in parents"
            )
            results = service.files().list(q=q, fields="files(id, name)").execute()
            files = results.get('files', [])
            
            if files:
                folder_ids[subfolder_name] = files[0]['id']
                print(f"  📁 Found: {subfolder_name}")
            else:
                # Create subfolder
                metadata = {
                    'name': subfolder_name,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [root_id]
                }
                folder = service.files().create(body=metadata, fields='id').execute()
                folder_ids[subfolder_name] = folder['id']
                print(f"  📁 Created: {subfolder_name}")
        
        return folder_ids
        
    except Exception as e:
        print(f"❌ Structure setup failed: {e}")
        return {}


def get_scripts_folder() -> Optional[str]:
    """Get the Scripts subfolder ID (creates structure if needed)."""
    folders = setup_veil_verse_structure()
    return folders.get("Scripts")


def create_screenplay_doc(title: str, content: str, folder_id: Optional[str] = None) -> Optional[str]:
    """
    Create a new Google Doc with screenplay formatting.
    
    Args:
        title: Document title
        content: Screenplay text content
        folder_id: Optional Google Drive folder ID
    
    Returns:
        Document URL if successful, None otherwise
    """
    creds = get_credentials()
    if not creds:
        return None
    
    try:
        docs_service = build('docs', 'v1', credentials=creds)
        drive_service = build('drive', 'v3', credentials=creds)
        
        # Create blank document
        doc = docs_service.documents().create(body={'title': title}).execute()
        doc_id = doc['documentId']
        print(f"📄 Created document: {title} (ID: {doc_id})")
        
        # Insert content
        requests = [
            {
                'insertText': {
                    'location': {'index': 1},
                    'text': content
                }
            }
        ]
        
        # Apply Courier New font to all content
        content_length = len(content)
        if content_length > 0:
            requests.append({
                'updateTextStyle': {
                    'range': {
                        'startIndex': 1,
                        'endIndex': 1 + content_length
                    },
                    'textStyle': {
                        'weightedFontFamily': {
                            'fontFamily': SCREENPLAY_FONT
                        },
                        'fontSize': {
                            'magnitude': SCREENPLAY_FONT_SIZE,
                            'unit': 'PT'
                        }
                    },
                    'fields': 'weightedFontFamily,fontSize'
                }
            })
        
        # Execute all requests
        docs_service.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': requests}
        ).execute()
        
        # Update page margins
        docs_service.documents().batchUpdate(
            documentId=doc_id,
            body={
                'requests': [{
                    'updateDocumentStyle': {
                        'documentStyle': {
                            'marginTop': {'magnitude': MARGINS['top'], 'unit': 'PT'},
                            'marginBottom': {'magnitude': MARGINS['bottom'], 'unit': 'PT'},
                            'marginLeft': {'magnitude': MARGINS['left'], 'unit': 'PT'},
                            'marginRight': {'magnitude': MARGINS['right'], 'unit': 'PT'},
                        },
                        'fields': 'marginTop,marginBottom,marginLeft,marginRight'
                    }
                }]
            }
        ).execute()
        
        # Move to folder if specified (true move, not add parent)
        if folder_id:
            # Get current parents to remove them
            file = drive_service.files().get(fileId=doc_id, fields="parents").execute()
            previous_parents = ",".join(file.get("parents", []))
            
            drive_service.files().update(
                fileId=doc_id,
                addParents=folder_id,
                removeParents=previous_parents,
                fields="id, parents"
            ).execute()
            print(f"📁 Moved to folder: {folder_id}")
        
        doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
        print(f"🔗 Document URL: {doc_url}")
        
        return doc_url
        
    except Exception as e:
        print(f"❌ Failed to create document: {e}")
        return None


def append_to_doc(doc_id: str, content: str) -> bool:
    """
    Append content to an existing Google Doc.
    
    Args:
        doc_id: Google Doc ID
        content: Text to append
    
    Returns:
        True if successful
    """
    creds = get_credentials()
    if not creds:
        return False
    
    try:
        service = build('docs', 'v1', credentials=creds)
        
        # Get current document end index
        doc = service.documents().get(documentId=doc_id).execute()
        end_index = doc['body']['content'][-1]['endIndex'] - 1
        
        # Insert content at end
        append_text = f"\n\n{content}"
        append_length = len(append_text)
        
        requests = [
            {
                'insertText': {
                    'location': {'index': end_index},
                    'text': append_text
                }
            },
            # Apply Courier 12pt to appended text
            {
                'updateTextStyle': {
                    'range': {
                        'startIndex': end_index,
                        'endIndex': end_index + append_length
                    },
                    'textStyle': {
                        'weightedFontFamily': {
                            'fontFamily': SCREENPLAY_FONT
                        },
                        'fontSize': {
                            'magnitude': SCREENPLAY_FONT_SIZE,
                            'unit': 'PT'
                        }
                    },
                    'fields': 'weightedFontFamily,fontSize'
                }
            }
        ]
        
        service.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': requests}
        ).execute()
        
        print(f"✅ Appended {len(content)} characters to document")
        return True
        
    except Exception as e:
        print(f"❌ Failed to append: {e}")
        return False


def list_screenplay_docs(max_results: int = 10) -> List[dict]:
    """List recent docs with 'screenplay' in the name."""
    creds = get_credentials()
    if not creds:
        return []
    
    try:
        service = build('drive', 'v3', credentials=creds)
        
        # Exclude trashed files
        q = (
            "mimeType='application/vnd.google-apps.document' "
            "and trashed=false "
            "and name contains 'screenplay'"
        )
        
        results = service.files().list(
            q=q,
            pageSize=max_results,
            fields="files(id, name, modifiedTime)"
        ).execute()
        
        return results.get('files', [])
        
    except Exception as e:
        print(f"❌ Failed to list docs: {e}")
        return []


# ============================================================
# VEIL VERSE INTEGRATION HELPERS
# ============================================================

def get_folder_id(name: str) -> Optional[str]:
    """Get cached folder ID by name, setup structure if needed."""
    folders = setup_veil_verse_structure()
    return folders.get(name)


def upload_asset(file_path: str, category: str = None) -> Optional[str]:
    """
    Upload a file to Assets folder (or subfolder if category specified).
    Returns file URL.
    """
    creds = get_credentials()
    if not creds:
        return None
    
    from pathlib import Path as FilePath
    import mimetypes
    
    try:
        service = build('drive', 'v3', credentials=creds)
        
        # Get Assets folder
        assets_id = get_folder_id("Assets")
        if not assets_id:
            return None
        
        # Create category subfolder if specified
        target_folder = assets_id
        if category:
            target_folder = get_or_create_folder(category)
            # Move subfolder into Assets
            file_meta = service.files().get(fileId=target_folder, fields="parents").execute()
            prev_parents = ",".join(file_meta.get("parents", []))
            service.files().update(
                fileId=target_folder,
                addParents=assets_id,
                removeParents=prev_parents,
                fields="id, parents"
            ).execute()
        
        # Upload file
        file_path = FilePath(file_path)
        mime_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        
        from googleapiclient.http import MediaFileUpload
        
        file_metadata = {
            "name": file_path.name,
            "parents": [target_folder]
        }
        media = MediaFileUpload(str(file_path), mimetype=mime_type)
        
        uploaded = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id, webViewLink"
        ).execute()
        
        url = uploaded.get("webViewLink", f"https://drive.google.com/file/d/{uploaded['id']}/view")
        print(f"📤 Uploaded: {file_path.name} → Assets/{category or ''}")
        return url
        
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return None


def copy_doc(doc_id: str, new_title: str, folder_id: str = None) -> Optional[str]:
    """Copy a Google Doc to a new location."""
    creds = get_credentials()
    if not creds:
        return None
    
    try:
        service = build('drive', 'v3', credentials=creds)
        
        copy_metadata = {"name": new_title}
        if folder_id:
            copy_metadata["parents"] = [folder_id]
        
        copied = service.files().copy(
            fileId=doc_id,
            body=copy_metadata,
            fields="id, webViewLink"
        ).execute()
        
        url = copied.get("webViewLink", f"https://docs.google.com/document/d/{copied['id']}/edit")
        print(f"📋 Copied to: {new_title}")
        return url
        
    except Exception as e:
        print(f"❌ Copy failed: {e}")
        return None


def archive_doc(doc_id: str, version: str = None) -> Optional[str]:
    """Archive a doc to Archive folder with version stamp."""
    from datetime import datetime
    
    creds = get_credentials()
    if not creds:
        return None
    
    try:
        service = build('drive', 'v3', credentials=creds)
        
        # Get original doc title
        doc = service.files().get(fileId=doc_id, fields="name").execute()
        original_title = doc.get("name", "Untitled")
        
        # Generate version stamp
        version = version or datetime.now().strftime("%Y-%m-%d_%H%M")
        archive_title = f"{original_title}_v{version}"
        
        # Get archive folder
        archive_id = get_folder_id("Archive")
        
        return copy_doc(doc_id, archive_title, archive_id)
        
    except Exception as e:
        print(f"❌ Archive failed: {e}")
        return None


def save_research(topic: str, content: str) -> Optional[str]:
    """Save research summary to References folder."""
    from datetime import datetime
    
    folder_id = get_folder_id("References")
    if not folder_id:
        return None
    
    title = f"Research - {topic} ({datetime.now().strftime('%Y-%m-%d')})"
    return create_screenplay_doc(title, content, folder_id)


def get_references_folder() -> Optional[str]:
    """Get the References subfolder ID."""
    return get_folder_id("References")


def get_assets_folder() -> Optional[str]:
    """Get the Assets subfolder ID."""
    return get_folder_id("Assets")


def get_lore_folder() -> Optional[str]:
    """Get the Lore subfolder ID."""
    return get_folder_id("Lore")


def get_archive_folder() -> Optional[str]:
    """Get the Archive subfolder ID."""
    return get_folder_id("Archive")


# ============================================================
# LOCAL DRIVE FUNCTIONS (Fast - uses mounted I: drive)
# ============================================================

def local_upload_asset(file_path: str, category: str = None) -> Optional[str]:
    """
    Fast upload using local Drive mount (I: drive).
    Falls back to API if drive not mounted.
    """
    import shutil
    from pathlib import Path as FilePath
    
    source = FilePath(file_path)
    if not source.exists():
        print(f"❌ File not found: {file_path}")
        return None
    
    # Check if Drive is mounted
    if not DRIVE_MOUNTED:
        print("⚠️ Drive not mounted, falling back to API...")
        return upload_asset(file_path, category)
    
    try:
        # Build destination path
        if category:
            dest_folder = DRIVE_LOCAL_PATH / "Assets" / category
        else:
            dest_folder = DRIVE_LOCAL_PATH / "Assets"
        
        # Create folder if needed
        dest_folder.mkdir(parents=True, exist_ok=True)
        
        # Copy file
        dest_path = dest_folder / source.name
        shutil.copy2(str(source), str(dest_path))
        
        print(f"📤 Local upload: {source.name} → {dest_path.relative_to(DRIVE_LOCAL_PATH)}")
        return str(dest_path)
        
    except Exception as e:
        print(f"❌ Local upload failed: {e}")
        return None


def batch_upload_assets(file_paths: list, category: str = None, progress: bool = True) -> list:
    """
    Batch upload multiple files using local Drive mount.
    Much faster than API for large batches.
    """
    results = []
    total = len(file_paths)
    
    for i, path in enumerate(file_paths):
        if progress:
            print(f"[{i+1}/{total}] ", end="")
        
        result = local_upload_asset(path, category)
        results.append({"path": path, "result": result, "success": result is not None})
    
    success_count = sum(1 for r in results if r["success"])
    print(f"\n✅ Uploaded {success_count}/{total} files to Assets/{category or ''}")
    
    return results


def get_local_path(folder: str) -> Optional[Path]:
    """Get local path for a Veil Verse subfolder."""
    if not DRIVE_MOUNTED:
        return None
    return DRIVE_LOCAL_PATH / folder


def get_file_link(name: str) -> Optional[str]:
    """Search for a file by name and return its webViewLink."""
    creds = get_credentials()
    if not creds:
        return None
    
    try:
        service = build('drive', 'v3', credentials=creds)
        
        # Search for file
        q = f"name='{name}' and trashed=false"
        results = service.files().list(q=q, fields="files(id, name, webViewLink)").execute()
        files = results.get('files', [])
        
        if files:
            url = files[0].get('webViewLink')
            print(f"🔗 Resolved: {name} -> {url}")
            return url
        
        return None
        
    except Exception as e:
        print(f"❌ Failed to resolve link: {e}")
        return None


if __name__ == "__main__":
    print("=== Google Docs Screenplay Export Test ===")
    
    test_content = """INT. VOID CHAMBER - NIGHT

KRONOS
(stern)
The council has spoken. Your narrative lacks coherence.

KAEDRA crosses to the shadows, her presence flickering.

KAEDRA
(whispering)
Then let the shadows write it for me.

                         (She vanishes into darkness)

FADE OUT.
"""
    
    url = create_screenplay_doc("Kaedra Screenplay Draft", test_content)
    if url:
        print(f"\n✅ Test successful! Open: {url}")
    else:
        print("\n❌ Test failed. Check authentication.")
