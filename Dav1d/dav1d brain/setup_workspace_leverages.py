"""
Quick Setup Assistant for Workspace Leverages
Helps configure OAuth credentials and Notion databases
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv, set_key

load_dotenv()

ENV_FILE = Path(".env")
CREDENTIALS_DIR = Path(".")

def print_header(text):
    """Print formatted header."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")


def check_file_exists(filepath: Path, description: str) -> bool:
    """Check if file exists and report status."""
    if filepath.exists():
        print(f"✅ {description}: {filepath.name}")
        return True
    else:
        print(f"❌ {description}: {filepath.name} (MISSING)")
        return False


def check_env_var(var_name: str) -> bool:
    """Check if environment variable is set."""
    value = os.getenv(var_name)
    if value:
        print(f"✅ {var_name}: Set")
        return True
    else:
        print(f"❌ {var_name}: Not set")
        return False


def setup_oauth_credentials():
    """Guide user through OAuth credential setup."""
    print_header("OAuth Credentials Setup")
    
    print("📥 You need to download OAuth credentials from Google Cloud Console:\n")
    print("1. Go to: https://console.cloud.google.com/apis/credentials")
    print("2. Select project: gen-lang-client-0285887798")
    print("3. Click '+ CREATE CREDENTIALS' → 'OAuth client ID'")
    print("4. Application type: 'Desktop app'")
    print("5. Name it 'Dav1d Gmail Integration' (or similar)")
    print("6. Click 'CREATE'")
    print("7. Download JSON file\n")
    
    print("You'll need TWO credential files:")
    print("  • credentials_gmail.json  (for Gmail API)")
    print("  • credentials_tasks.json  (for Tasks API)\n")
    
    print("💡 TIP: You can use the SAME credential file for both!")
    print("   Just copy it to both filenames.\n")
    
    # Check if files exist
    gmail_creds = CREDENTIALS_DIR / "credentials_gmail.json"
    tasks_creds = CREDENTIALS_DIR / "credentials_tasks.json"
    
    has_gmail = check_file_exists(gmail_creds, "Gmail credentials")
    has_tasks = check_file_exists(tasks_creds, "Tasks credentials")
    
    if not has_gmail or not has_tasks:
        print("\n⚠️  Missing credential files!")
        print(f"   Place them in: {CREDENTIALS_DIR.absolute()}\n")
        return False
    
    return True


def setup_notion_databases():
    """Guide user through Notion database setup."""
    print_header("Notion Databases Setup")
    
    print("📊 You need to create 3 Notion databases:\n")
    
    databases = [
        {
            "name": "Gmail Inbox",
            "env_var": "NOTION_GMAIL_DB_ID",
            "properties": [
                "Subject (Title)",
                "From (Text)",
                "Category (Select: Work, Personal, Newsletter, Spam, Urgent)",
                "Priority (Select: Low, Medium, High, Urgent)",
                "Action Required (Checkbox)",
                "Date (Date)",
                "Tags (Multi-select)"
            ]
        },
        {
            "name": "Tasks",
            "env_var": "NOTION_TASKS_DB_ID",
            "properties": [
                "Name (Title)",
                "Status (Select: To Do, In Progress, Done)",
                "Priority (Select: Low, Medium, High, Urgent)",
                "Due Date (Date)",
                "Tags (Multi-select)"
            ]
        },
        {
            "name": "Workflows",
            "env_var": "NOTION_WORKFLOWS_DB_ID",
            "properties": [
                "Workflow (Title)",
                "Timestamp (Date)",
                "Status (Select: Completed, Failed)"
            ]
        }
    ]
    
    for i, db in enumerate(databases, 1):
        print(f"{i}. CREATE: '{db['name']}' Database")
        print("   Required properties:")
        for prop in db['properties']:
            print(f"     - {prop}")
        print("")
    
    print("After creating each database:")
    print("  1. Share it with your 'Dav1d AI' Notion integration")
    print("  2. Get database ID from URL (32-char hex string)")
    print("  3. Add to .env file\n")
    
    # Check environment variables
    all_set = True
    for db in databases:
        if not check_env_var(db['env_var']):
            all_set = False
    
    if not all_set:
        print("\n⚠️  Missing Notion database IDs!")
        print(f"   Add them to: {ENV_FILE.absolute()}\n")
        
        print("Example .env entries:")
        for db in databases:
            print(f"  {db['env_var']}=your_database_id_here")
        print("")
        return False
    
    return True


def setup_google_apis():
    """Guide user through API enablement."""
    print_header("Google APIs Setup")
    
    print("🔧 You need to enable these Google APIs:\n")
    
    apis = [
        ("Gmail API", "gmail.googleapis.com"),
        ("Tasks API", "tasks.googleapis.com"),
        ("Drive API", "drive.googleapis.com"),
        ("Calendar API", "calendar-json.googleapis.com")
    ]
    
    print("Run these commands:\n")
    for name, api in apis:
        print(f"gcloud services enable {api} --project=gen-lang-client-0285887798")
    
    print("\nOr enable via console:")
    print("https://console.cloud.google.com/apis/library\n")


def install_dependencies():
    """Install Python dependencies."""
    print_header("Install Dependencies")
    
    print("📦 Installing required Python packages...\n")
    
    import subprocess
    
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=True
        )
        print("\n✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("\n❌ Failed to install dependencies")
        print("   Try manually: pip install -r requirements.txt\n")
        return False


def run_setup():
    """Run the complete setup process."""
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║     🚀 DAV1D WORKSPACE LEVERAGES SETUP ASSISTANT 🚀     ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    # Check existing setup
    print_header("Current Status")
    
    checks = {
        "Notion Token": check_env_var("NOTION_TOKEN"),
        "Project ID": check_env_var("PROJECT_ID"),
        "Location": check_env_var("LOCATION")
    }
    
    # Run setup steps
    steps = [
        ("Install Dependencies", install_dependencies),
        ("OAuth Credentials", setup_oauth_credentials),
        ("Notion Databases", setup_notion_databases),
        ("Google APIs", lambda: (setup_google_apis(), True)[1])
    ]
    
    results = {}
    for step_name, step_func in steps:
        try:
            results[step_name] = step_func()
        except Exception as e:
            print(f"\n❌ Error in {step_name}: {e}\n")
            results[step_name] = False
    
    # Summary
    print_header("Setup Summary")
    
    all_good = True
    for step_name, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {step_name}")
        if not success:
            all_good = False
    
    if all_good:
        print("\n🎉 Setup complete! You're ready to use Workspace Leverages!")
        print("\n📚 Next steps:")
        print("  1. Run: python gmail_to_notion.py --max 5")
        print("  2. Run: python tasks_notion_sync.py --direction google-to-notion")
        print("  3. Run: python workflow_automation.py")
        print("\nSee WORKSPACE_LEVERAGES_GUIDE.md for details.\n")
    else:
        print("\n⚠️  Setup incomplete. Please fix the issues above.")
        print("   See WORKSPACE_LEVERAGES_GUIDE.md for help.\n")


if __name__ == "__main__":
    run_setup()
